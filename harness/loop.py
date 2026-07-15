"""Optional research loop: a small state machine over persistent files.

    READ_STATE -> SELECT_ONE_QUESTION -> PROPOSE_ONE_EXPERIMENT -> RUN
    -> EVALUATE -> UPDATE_EVIDENCE -> COMMIT_AND_HAND_OFF

The loop DISPATCHES experiments; it does not invent them. Humans (or a Claude
session) enqueue planned experiments — each with a config + contract — in
EXPERIMENTS.json; the loop verifies the baseline, runs exactly one planned
experiment through the harness, records the evidence, and commits. All state
lives in files (RESEARCH_STATE.md, EXPERIMENTS.json, runs/) — never in
conversation history.

Rules enforced here:
  - baseline (smoke-test) must pass before any experiment runs;
  - one experiment per iteration;
  - a crash marks the ledger entry failed and adds an uncertainty note —
    it is never recorded as negative evidence;
  - evidence lines carry the verdict, run id, and strength stamp verbatim
    from the deterministic evaluation;
  - commit is skipped (with a warning) if the worktree was already dirty.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from .cli import cmd_smoke_test, do_run
from .contract import ContractError
from .cli import load_config

EVIDENCE_HEADER = "## Established evidence"
UNCERTAINTY_HEADER = "## Unresolved uncertainties"


class Loop:
    def __init__(
        self,
        repo_root: Path,
        runs_root: Path,
        state_md: Optional[Path] = None,
        ledger_path: Optional[Path] = None,
    ):
        self.repo_root = Path(repo_root)
        self.runs_root = Path(runs_root)
        self.state_md = state_md or self.repo_root / "RESEARCH_STATE.md"
        self.ledger_path = ledger_path or self.repo_root / "EXPERIMENTS.json"

    # -- state files ---------------------------------------------------------
    def _read_ledger(self) -> dict:
        return json.loads(self.ledger_path.read_text(encoding="utf-8"))

    def _write_ledger(self, ledger: dict) -> None:
        self.ledger_path.write_text(
            json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def _append_to_section(self, header: str, line: str) -> None:
        text = self.state_md.read_text(encoding="utf-8")
        if header not in text:
            raise ContractError(f"{self.state_md} missing section {header!r}")
        idx = text.index(header) + len(header)
        nxt = text.find("\n## ", idx)
        insert_at = nxt if nxt != -1 else len(text)
        block = text[idx:insert_at].rstrip() + f"\n- {line}\n"
        self.state_md.write_text(
            text[:idx] + block + ("\n" + text[insert_at:].lstrip("\n") if nxt != -1 else ""),
            encoding="utf-8",
        )

    # -- steps -----------------------------------------------------------------
    def step(self, commit: bool = True, skip_baseline: bool = False) -> int:
        # READ_STATE
        for f in (self.state_md, self.ledger_path):
            if not f.exists():
                print(f"[loop] missing {f} — create it before running the loop",
                      file=sys.stderr)
                return 2
        ledger = self._read_ledger()
        dirty_before = self._git_dirty()

        # verify the baseline still works
        if skip_baseline:
            print("[loop] baseline check SKIPPED (--skip-baseline)")
        else:
            print("[loop] verifying baseline (smoke-test) ...")
            if cmd_smoke_test(None) != 0:
                print("[loop] baseline smoke-test FAILED — fix the baseline before "
                      "running new experiments", file=sys.stderr)
                return 1

        # SELECT_ONE_QUESTION
        item = next((e for e in ledger["experiments"] if e["status"] == "planned"), None)
        if item is None:
            print("[loop] no planned experiments in EXPERIMENTS.json — add one "
                  "(question + config with contract) and re-run")
            return 0
        print(f"[loop] selected {item['id']}: {item['question']}")

        # PROPOSE_ONE_EXPERIMENT (validate config + contract before running)
        config_path = self.repo_root / item["config"]
        try:
            load_config(config_path)
        except (ContractError, FileNotFoundError, OSError) as e:
            print(f"[loop] {item['id']} has an invalid config/contract: {e}",
                  file=sys.stderr)
            return 2
        item["status"] = "running"
        item["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        self._write_ledger(ledger)

        # RUN + EVALUATE (one experiment, cheapest already chosen by planner)
        date = time.strftime("%Y-%m-%d")
        try:
            run = do_run(config_path, self.runs_root, with_eval=True)
        except BaseException as e:
            item["status"] = "failed"
            item["note"] = f"crashed: {type(e).__name__}: {str(e)[:200]}"
            self._write_ledger(ledger)
            self._append_to_section(
                UNCERTAINTY_HEADER,
                f"[{date}] {item['id']} crashed during execution "
                f"(see runs/*/failure.json) — crash is NOT negative evidence; "
                f"diagnose and resume.",
            )
            print(f"[loop] {item['id']} crashed — ledger updated, no evidence recorded",
                  file=sys.stderr)
            return 3

        ev = run.eval_result()

        # UPDATE_EVIDENCE
        item.update(
            status="complete",
            run=run.id,
            verdict=ev["verdict"],
            confirmed=ev["confirmed"],
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self._write_ledger(ledger)
        relation = {
            "success": "SUPPORTS",
            "failure": "CONTRADICTS",
            "inconclusive": "INCONCLUSIVE for",
        }[ev["verdict"]]
        detail = ev["checks"]["success_metric"]["detail"]
        self._append_to_section(
            EVIDENCE_HEADER,
            f"[{date}] {item['id']} (run {run.id}): {relation} — "
            f"{item['question']} | {detail} | strength: {ev['evidence_strength']}",
        )
        if ev["verdict"] == "inconclusive":
            self._append_to_section(
                UNCERTAINTY_HEADER,
                f"[{date}] {item['id']} was inconclusive "
                f"(missing: {ev['missing_diagnostics'] or 'criteria unmet both ways'}) "
                f"— refine the contract or design a sharper experiment.",
            )
        print(f"[loop] {item['id']} -> {ev['verdict']} (run {run.id}); evidence recorded")

        # COMMIT_AND_HAND_OFF
        if commit:
            if dirty_before:
                print("[loop] worktree was dirty before this iteration — commit "
                      "skipped; commit your changes and re-run, or use --no-commit")
            else:
                self._commit(item, ev)
        nxt = next((e for e in ledger["experiments"] if e["status"] == "planned"), None)
        print(f"[loop] next planned: {nxt['id'] if nxt else '(none — plan the next experiment)'}")
        return 0

    def _git_dirty(self) -> bool:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=self.repo_root,
            capture_output=True, text=True,
        )
        return bool(out.stdout.strip())

    def _commit(self, item: dict, ev: dict) -> None:
        rel_runs = self.runs_root
        try:
            rel_runs = self.runs_root.relative_to(self.repo_root)
        except ValueError:
            pass
        subprocess.run(
            ["git", "add", str(self.state_md), str(self.ledger_path),
             str(rel_runs), item["config"]],
            cwd=self.repo_root, check=True,
        )
        msg = (f"loop({item['id']}): {ev['verdict']} — {item['question']}\n\n"
               f"run: {item.get('run')}  strength: {ev['evidence_strength']}\n\n"
               f"Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>")
        subprocess.run(["git", "commit", "-m", msg], cwd=self.repo_root, check=True)
        print("[loop] committed")

    # -- status -------------------------------------------------------------------
    def print_status(self) -> None:
        if not self.ledger_path.exists():
            print("[loop] no EXPERIMENTS.json yet")
            return
        ledger = self._read_ledger()
        counts: dict = {}
        for e in ledger["experiments"]:
            counts[e["status"]] = counts.get(e["status"], 0) + 1
        print(f"[loop] ledger: {counts}")
        for e in ledger["experiments"]:
            verdict = f" verdict={e.get('verdict')}" if e.get("verdict") else ""
            run = f" run={e.get('run')}" if e.get("run") else ""
            print(f"  {e['id']:<10} {e['status']:<9}{verdict}{run}  {e['question']}")

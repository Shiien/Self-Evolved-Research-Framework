"""TTT skill-evolution experiment, migrated onto the harness.

Consolidates the two legacy drivers in experiments/tic_tac_toe/run_cycle.py
(batch mode and online-evolve mode) into one parameterized runner whose
artifacts live entirely inside the run directory. Scientific code is imported
unchanged: game rules, minimax grading, G2 writing, and the evolve CLI are the
exact legacy implementations.

Params (config `params:` block, defaults in DEFAULTS):
    mode: "online-evolve" | "batch"
        online-evolve: N self-play games; after EACH game write G2, run the
            evolve backward pass, and apply the proposal if valid.
        batch: eval games vs minimax (before), one evolve pass, eval (after).
    games: int                  self-play games (online-evolve mode)
    games_per_side: int         eval games per side (batch mode / confirmation)
    confirm_games_per_side: int held-out confirmation games vs minimax with the
                                FINAL spec (0 = skip). These populate confirm.*
                                metrics and are never used as training signal.
    evolve_enabled: bool        false = pure evaluation run (control/baseline)
    engine: "claude-cli" | "scripted-first-legal"
    evolve_engine: "cli" | "none"   ("none" = deterministic shim backward pass)
    model, timeout:             claude-cli engine settings
    sandbox: bool               true  = copy skill + fresh feedback-log into the
                                        run dir (self-contained, repo untouched)
                                false = legacy live mode: evolve the repo's
                                        skills/play-tic-tac-toe/SKILL.md in place

Behavioral difference vs legacy (deliberate, tested): a proposed spec is only
applied if it looks like a valid SKILL.md (YAML frontmatter, no shim
"<<EVOLVE NOTE" placeholder text). The legacy driver applied shim placeholders
verbatim, which corrupted the live skill during cycle-005.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from .. import REPO_ROOT
from ..contract import Contract, evaluate_contract
from ..rundir import RunDir

# Make legacy packages importable exactly the way they import themselves.
for p in (REPO_ROOT / "experiments", REPO_ROOT / "skills" / "td-nl"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tic_tac_toe.arena import (  # noqa: E402
    GameRecord,
    grade_game,
    minimax_agent,
    play_one_game,
    skill_agent,
)
from tic_tac_toe.g2_writer import (  # noqa: E402
    SKILL_NAME,
    write_batch,
    write_selfplay_batch,
)
from tic_tac_toe.logging_engine import LoggingEngine  # noqa: E402
from tic_tac_toe.run_cycle import (  # noqa: E402  (pure helpers, single-sourced)
    extract_last_proposal,
    extract_proposal_spec,
    games_to_jsonl,
    summarize,
    summarize_selfplay,
)
from textgrad_backend.engines import ClaudeCodeCLIEngine  # noqa: E402

EVOLVE_SCRIPT = REPO_ROOT / "scripts" / "evolve_textgrad.py"
LIVE_SKILL = REPO_ROOT / "skills" / SKILL_NAME / "SKILL.md"
LIVE_TDNL = REPO_ROOT / "skills" / "td-nl"

DEFAULTS = {
    "mode": "online-evolve",
    "games": 4,
    "games_per_side": 1,
    "confirm_games_per_side": 0,
    "evolve_enabled": True,
    "engine": "claude-cli",
    "evolve_engine": "cli",
    "model": "haiku",
    "timeout": 180.0,
    "sandbox": True,
}

FEEDBACK_LOG_SKELETON = """# Skill Feedback Log (sandboxed run copy)

## Pending Feedback

## Pending Proposals

## Processed Feedback
"""

_LEGAL_RE = re.compile(r"Legal cells:\s*([0-9,\s]+)")


class ScriptedFirstLegalEngine:
    """Deterministic offline stand-in for the LLM engine: always plays the
    lowest-numbered legal cell (parsed from the prompt). Test/smoke only."""

    def __call__(self, prompt: str, system_prompt: Optional[str] = None, **kw) -> str:
        m = _LEGAL_RE.search(prompt)
        if not m:
            return "5"
        return m.group(1).split(",")[0].strip()

    def generate(self, content: str, system_prompt: Optional[str] = None, **kw) -> str:
        return self.__call__(content, system_prompt=system_prompt, **kw)


def _resolve_params(params: dict) -> dict:
    p = dict(DEFAULTS)
    p.update(params or {})
    unknown = set(p) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"ttt_cycle: unknown params {sorted(unknown)}")
    if p["mode"] not in ("online-evolve", "batch"):
        raise ValueError(f"ttt_cycle: bad mode {p['mode']!r}")
    return p


def resolve_params(params: dict) -> dict:
    """Public alias used by the CLI to resolve+validate params before a run."""
    return _resolve_params(params)


def _setup_paths(p: dict, run: RunDir) -> dict:
    """Return the file layout the run operates on (sandboxed or live)."""
    if p["sandbox"]:
        sb = run.artifacts / "sandbox"
        skills_root = sb / "skills"
        skill_dir = skills_root / SKILL_NAME
        skill_dir.mkdir(parents=True)
        shutil.copy2(LIVE_SKILL, skill_dir / "SKILL.md")
        feedback_log = sb / "feedback-log.md"
        feedback_log.write_text(FEEDBACK_LOG_SKELETON, encoding="utf-8")
        skill_values = sb / "skill-values"
        skill_values.mkdir()
        value_function = sb / "value-function.md"
        live_vf = LIVE_TDNL / "value-function.md"
        if live_vf.exists():
            shutil.copy2(live_vf, value_function)
        return {
            "skill_path": skill_dir / "SKILL.md",
            "feedback_log": feedback_log,
            "skills_root": skills_root,
            "skill_values_dir": skill_values,
            "value_function": value_function,
        }
    return {
        "skill_path": LIVE_SKILL,
        "feedback_log": LIVE_TDNL / "feedback-log.md",
        "skills_root": REPO_ROOT / "skills",
        "skill_values_dir": LIVE_TDNL / "skill-values",
        "value_function": LIVE_TDNL / "value-function.md",
    }


def _make_engine(p: dict, run: RunDir) -> LoggingEngine:
    if p["engine"] == "scripted-first-legal":
        raw = ScriptedFirstLegalEngine()
    elif p["engine"] == "claude-cli":
        raw = ClaudeCodeCLIEngine(model=p["model"], timeout=p["timeout"])
    else:
        raise ValueError(f"ttt_cycle: unknown engine {p['engine']!r}")
    return LoggingEngine(raw, log_path=run.logs / "engine-calls.jsonl", label="arena")


def _run_evolve(p: dict, paths: dict, run: RunDir, tag: str) -> Optional[dict]:
    """Run the legacy evolve CLI against this run's state. Returns the parsed
    TD JSON summary (or None on parse failure; raw output is always saved)."""
    cmd = [
        sys.executable, str(EVOLVE_SCRIPT), "--apply-proposal", "--json",
        "--feedback-log", str(paths["feedback_log"]),
        "--skills-root", str(paths["skills_root"]),
        "--skill-values-dir", str(paths["skill_values_dir"]),
        "--value-function", str(paths["value_function"]),
    ]
    if p["evolve_engine"] == "none":
        cmd.append("--no-engine")
    else:
        cmd += ["--engine-model", p["model"]]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600
    )
    (run.logs / f"evolve-{tag}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (run.logs / f"evolve-{tag}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode not in (0, 1):  # 1 = "no pending feedback" (benign)
        raise RuntimeError(
            f"evolve_textgrad failed rc={proc.returncode}: {proc.stderr[:500]}"
        )
    # The proposal block is printed before the JSON summary; the summary is
    # the last line-start "{" (same parse as the legacy driver).
    try:
        jstart = proc.stdout.rfind("\n{")
        jstart = (jstart + 1) if jstart != -1 else proc.stdout.find("{")
        if jstart == -1:
            return None
        td = json.loads(proc.stdout[jstart:])
        (run.logs / f"evolve-{tag}.td.json").write_text(
            json.dumps(td, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return td
    except (ValueError, json.JSONDecodeError):
        return None


def _spec_is_valid(text: str) -> bool:
    """Guardrail: only apply specs that look like a real SKILL.md."""
    return text.startswith("---") and "<<EVOLVE NOTE" not in text


def _apply_proposal(paths: dict, run: RunDir, tag: str) -> dict:
    """If the latest proposal targets our skill and is a valid spec, apply it
    (archiving the previous version to checkpoints/)."""
    proposal = extract_last_proposal(paths["feedback_log"])
    out = {"applied": False, "rejected_invalid": False}
    if not proposal or f"target:{SKILL_NAME}" not in proposal:
        return out
    (run.logs / f"proposal-{tag}.md").write_text(proposal, encoding="utf-8")
    before = paths["skill_path"].read_text(encoding="utf-8")
    new_spec = extract_proposal_spec(proposal)
    if not new_spec or new_spec == before:
        return out
    if not _spec_is_valid(new_spec):
        out["rejected_invalid"] = True
        (run.logs / f"rejected-spec-{tag}.md").write_text(new_spec, encoding="utf-8")
        return out
    paths["skill_path"].write_text(new_spec, encoding="utf-8")
    out["applied"] = True
    return out


def _play_selfplay(engine, skill_path: Path, n: int) -> List[Tuple[GameRecord, dict]]:
    out = []
    for _ in range(n):
        x = skill_agent(engine, skill_path, name="skill-X")
        o = skill_agent(engine, skill_path, name="skill-O")
        rec = play_one_game(x, o)
        out.append((rec, grade_game(rec)))
    return out


def _play_vs_minimax(engine, skill_path: Path, games_per_side: int):
    mm = minimax_agent(name="minimax")
    out: List[Tuple[GameRecord, str]] = []
    for _ in range(games_per_side):
        sk = skill_agent(engine, skill_path, name="skill")
        out.append((play_one_game(sk, mm), "X"))
    for _ in range(games_per_side):
        sk = skill_agent(engine, skill_path, name="skill")
        out.append((play_one_game(mm, sk), "O"))
    return out


def _append_jsonl(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def execute(params: dict, run: RunDir) -> dict:
    p = _resolve_params(params)
    paths = _setup_paths(p, run)
    engine = _make_engine(p, run)
    t0 = time.time()

    # v0 snapshot
    run.checkpoints.joinpath("spec-initial.md").write_text(
        paths["skill_path"].read_text(encoding="utf-8"), encoding="utf-8"
    )

    result: dict = {"mode": p["mode"], "params": p, "edits_applied": 0,
                    "apply_rejected_invalid": 0}
    games_file = run.artifacts / "games.jsonl"

    if p["mode"] == "online-evolve":
        all_graded: List[Tuple[GameRecord, dict]] = []
        for i in range(1, p["games"] + 1):
            graded = _play_selfplay(engine, paths["skill_path"], 1)
            rec, grading = graded[0]
            all_graded.append((rec, grading))
            d = rec.to_dict()
            d.update(grading=grading, game_idx=i)
            _append_jsonl(games_file, d)
            run.append_metric({
                "game": i,
                "terminal": rec.terminal,
                "winner": rec.winner,
                "mistakes": grading["X_mistakes"] + grading["O_mistakes"],
            })
            if p["evolve_enabled"]:
                session_id = f"ttt-{run.id}-g{i:02d}"
                write_selfplay_batch(paths["feedback_log"], graded, session_id=session_id)
                _run_evolve(p, paths, run, tag=f"g{i:02d}")
                apply_info = _apply_proposal(paths, run, tag=f"g{i:02d}")
                result["edits_applied"] += int(apply_info["applied"])
                result["apply_rejected_invalid"] += int(apply_info["rejected_invalid"])
            run.checkpoints.joinpath(f"spec-after-game-{i:02d}.md").write_text(
                paths["skill_path"].read_text(encoding="utf-8"), encoding="utf-8"
            )
        result["dev"] = summarize_selfplay(all_graded)

    else:  # batch
        records_before = _play_vs_minimax(engine, paths["skill_path"], p["games_per_side"])
        (run.artifacts / "games-before.jsonl").write_text(
            games_to_jsonl(records_before), encoding="utf-8"
        )
        result["dev"] = summarize(records_before)
        if p["evolve_enabled"]:
            session_id = f"ttt-{run.id}"
            write_batch(paths["feedback_log"], records_before, session_id=session_id)
            _run_evolve(p, paths, run, tag="batch")
            apply_info = _apply_proposal(paths, run, tag="batch")
            result["edits_applied"] += int(apply_info["applied"])
            result["apply_rejected_invalid"] += int(apply_info["rejected_invalid"])
            records_after = _play_vs_minimax(
                engine, paths["skill_path"], p["games_per_side"]
            )
            (run.artifacts / "games-after.jsonl").write_text(
                games_to_jsonl(records_after), encoding="utf-8"
            )
            result["dev_after"] = summarize(records_after)
        run.checkpoints.joinpath("spec-after-batch.md").write_text(
            paths["skill_path"].read_text(encoding="utf-8"), encoding="utf-8"
        )

    # Held-out confirmation with the FINAL spec (never a training signal).
    if p["confirm_games_per_side"] > 0:
        confirm_records = _play_vs_minimax(
            engine, paths["skill_path"], p["confirm_games_per_side"]
        )
        (run.artifacts / "games-confirm.jsonl").write_text(
            games_to_jsonl(confirm_records), encoding="utf-8"
        )
        result["confirm"] = summarize(confirm_records)

    result["final_spec_valid"] = _spec_is_valid(
        paths["skill_path"].read_text(encoding="utf-8")
    )
    calls_file = run.logs / "engine-calls.jsonl"
    n_calls = (
        sum(1 for _ in calls_file.open(encoding="utf-8")) if calls_file.exists() else 0
    )
    result["engine_calls"] = n_calls
    # only real LLM calls count against the LLM budget (scripted engine is free)
    result["llm_calls"] = n_calls if p["engine"] == "claude-cli" else 0
    result["wall_seconds"] = round(time.time() - t0, 2)
    return result


def flatten_metrics(result: dict) -> dict:
    """Flatten execute() output into the dotted metric names contracts use."""
    m: dict = {
        "edits_applied": result.get("edits_applied", 0),
        "apply_rejected_invalid": result.get("apply_rejected_invalid", 0),
        "final_spec_valid": result.get("final_spec_valid"),
        "engine_calls": result.get("engine_calls", 0),
        "llm_calls": result.get("llm_calls", 0),
        "wall_seconds": result.get("wall_seconds"),
    }
    for prefix in ("dev", "dev_after", "confirm"):
        block = result.get(prefix)
        if isinstance(block, dict):
            for k, v in block.items():
                if isinstance(v, (int, float, bool)):
                    m[f"{prefix}.{k}"] = v
    return m


def evaluate(params: dict, run: RunDir, contract: Contract) -> dict:
    from .. import RUNS_ROOT

    result = run.result()
    metrics = flatten_metrics(result)
    ev = evaluate_contract(contract, metrics, run.root, RUNS_ROOT)

    budget = contract.budget
    over = {}
    if "max_llm_calls" in budget and metrics["llm_calls"] > budget["max_llm_calls"]:
        over["llm_calls"] = {"used": metrics["llm_calls"], "budget": budget["max_llm_calls"]}
    if "max_engine_calls" in budget and metrics["engine_calls"] > budget["max_engine_calls"]:
        over["engine_calls"] = {"used": metrics["engine_calls"],
                                "budget": budget["max_engine_calls"]}
    if "max_minutes" in budget and metrics.get("wall_seconds", 0) > 60 * float(budget["max_minutes"]):
        over["minutes"] = {"used": round(metrics["wall_seconds"] / 60, 2),
                           "budget": budget["max_minutes"]}
    ev["budget_exceeded"] = over or False
    return ev

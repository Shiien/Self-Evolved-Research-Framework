"""Self-contained run directory.

runs/<id>/
    config.yaml        resolved configuration (experiment, seed, params, contract)
    contract.yaml      the contract alone (hashed into meta.json at creation)
    meta.json          seed, git sha/dirty, python, platform, argv, timestamps
    status.json        created -> running -> executed -> evaluated | failed
    metrics.jsonl      one JSON object per line, appended during execution
    logs/              stage logs (engine-calls.jsonl, evolve stdout/stderr, ...)
    artifacts/         experiment-specific outputs (games, sandboxed state, ...)
    checkpoints/       spec snapshots per step
    eval/result.json   deterministic evaluation against the contract
    failure.json       traceback + stage, only on failure
    summary.md         concise human-readable run summary
"""
from __future__ import annotations

import getpass
import json
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .contract import Contract

STATES = ("created", "running", "executed", "evaluated", "failed")


def _git_info(repo_root: Path) -> dict:
    def _run(*args: str) -> Optional[str]:
        try:
            out = subprocess.run(
                ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=10
            )
            return out.stdout.strip() if out.returncode == 0 else None
        except Exception:
            return None

    sha = _run("rev-parse", "HEAD")
    status = _run("status", "--porcelain")
    return {"sha": sha, "dirty": bool(status) if status is not None else None}


class RunDir:
    def __init__(self, root: Path):
        self.root = Path(root)

    # -- paths ------------------------------------------------------------
    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def checkpoints(self) -> Path:
        return self.root / "checkpoints"

    @property
    def eval_dir(self) -> Path:
        return self.root / "eval"

    @property
    def id(self) -> str:
        return self.root.name

    # -- creation / loading -------------------------------------------------
    @classmethod
    def create(
        cls,
        runs_root: Path,
        name: str,
        config: Dict[str, Any],
        contract: Contract,
        repo_root: Path,
        seed: int = 0,
    ) -> "RunDir":
        runs_root.mkdir(parents=True, exist_ok=True)
        run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{name}"
        root = runs_root / run_id
        n = 1
        while root.exists():
            n += 1
            root = runs_root / f"{run_id}-{n}"
        run = cls(root)
        for d in (run.root, run.logs, run.artifacts, run.checkpoints, run.eval_dir):
            d.mkdir(parents=True)

        (run.root / "config.yaml").write_text(
            yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        (run.root / "contract.yaml").write_text(
            yaml.safe_dump(contract.raw, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        meta = {
            "run_id": run.id,
            "experiment": config.get("experiment"),
            "seed": seed,
            "contract_sha256": contract.sha256(),
            "git": _git_info(repo_root),
            "python": sys.version,
            "platform": platform.platform(),
            "hostname": platform.node(),
            "user": getpass.getuser(),
            "argv": sys.argv,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        (run.root / "meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (run.root / "metrics.jsonl").write_text("", encoding="utf-8")
        run._write_status({"state": "created", "history": []})
        return run

    @classmethod
    def load(cls, path: Path) -> "RunDir":
        run = cls(path)
        if not (run.root / "status.json").exists():
            raise FileNotFoundError(f"{path} is not a run directory (no status.json)")
        return run

    # -- state ----------------------------------------------------------------
    def _write_status(self, status: dict) -> None:
        (self.root / "status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )

    def status(self) -> dict:
        return json.loads((self.root / "status.json").read_text(encoding="utf-8"))

    def set_state(self, state: str, **extra: Any) -> None:
        assert state in STATES, state
        s = self.status()
        s["history"].append(
            {"state": s["state"], "until": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        )
        s["state"] = state
        s.update(extra)
        self._write_status(s)

    def meta(self) -> dict:
        return json.loads((self.root / "meta.json").read_text(encoding="utf-8"))

    def config(self) -> dict:
        return yaml.safe_load((self.root / "config.yaml").read_text(encoding="utf-8"))

    def contract(self) -> Contract:
        return Contract.from_dict(
            yaml.safe_load((self.root / "contract.yaml").read_text(encoding="utf-8"))
        )

    def contract_unchanged(self) -> bool:
        return self.contract().sha256() == self.meta()["contract_sha256"]

    # -- recording ------------------------------------------------------------
    def append_metric(self, entry: Dict[str, Any]) -> None:
        with (self.root / "metrics.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def record_failure(self, stage: str, exc: BaseException) -> None:
        (self.root / "failure.json").write_text(
            json.dumps(
                {
                    "stage": stage,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.set_state("failed", failed_stage=stage)

    def write_result(self, result: Dict[str, Any]) -> None:
        (self.artifacts / "result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def result(self) -> dict:
        return json.loads(
            (self.artifacts / "result.json").read_text(encoding="utf-8")
        )

    def write_eval(self, result: Dict[str, Any]) -> None:
        (self.eval_dir / "result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def eval_result(self) -> Optional[dict]:
        f = self.eval_dir / "result.json"
        if not f.exists():
            return None
        return json.loads(f.read_text(encoding="utf-8"))

    def write_summary(self, text: str) -> None:
        (self.root / "summary.md").write_text(text, encoding="utf-8")

    # -- resume support ---------------------------------------------------------
    def archive_attempt(self) -> Path:
        """Move the mutable outputs of a failed/partial attempt aside so the
        run can be re-executed in place (same id, fresh artifacts)."""
        attempts = self.root / "attempts"
        attempts.mkdir(exist_ok=True)
        n = 1 + sum(1 for _ in attempts.iterdir())
        dest = attempts / f"attempt-{n}"
        dest.mkdir()
        for name in ("artifacts", "checkpoints", "eval", "logs", "failure.json",
                     "metrics.jsonl", "summary.md"):
            src = self.root / name
            if src.exists():
                src.rename(dest / name)
        for d in (self.logs, self.artifacts, self.checkpoints, self.eval_dir):
            d.mkdir()
        (self.root / "metrics.jsonl").write_text("", encoding="utf-8")
        return dest

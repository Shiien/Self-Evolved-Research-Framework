"""Experiment contract: a small structured commitment made BEFORE a run.

The contract is stored (and hashed) in the run directory at creation time;
evaluation refuses to run if the stored contract no longer matches the hash,
so criteria cannot be edited after observing results.

Criteria are deterministic comparisons over the flattened metrics dict the
experiment's execute() returns. `dev.*` metrics are development signals;
`confirm.*` metrics are held-out confirmation signals.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_FIELDS = [
    "hypothesis",
    "change",
    "controls",
    "success_metric",
    "failure_condition",
    "required_diagnostics",
    "budget",
]

_OPS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


class ContractError(ValueError):
    pass


@dataclass
class Criterion:
    metric: str
    op: str
    value: Optional[float] = None
    baseline_run: Optional[str] = None  # run id/path to pull the metric from
    margin: float = 0.0  # added to the baseline value before comparing

    @staticmethod
    def from_dict(d: dict, name: str) -> "Criterion":
        if not isinstance(d, dict):
            raise ContractError(f"{name} must be a mapping, got {type(d).__name__}")
        missing = [k for k in ("metric", "op") if k not in d]
        if missing:
            raise ContractError(f"{name} missing fields: {missing}")
        if d["op"] not in _OPS:
            raise ContractError(f"{name}.op must be one of {sorted(_OPS)}")
        if ("value" in d) == ("baseline_run" in d):
            raise ContractError(
                f"{name} needs exactly one of 'value' or 'baseline_run'"
            )
        return Criterion(
            metric=d["metric"],
            op=d["op"],
            value=d.get("value"),
            baseline_run=d.get("baseline_run"),
            margin=float(d.get("margin", 0.0)),
        )

    def reference_value(self, runs_root: Path) -> float:
        """Resolve the comparison reference (literal or from a baseline run)."""
        if self.baseline_run is None:
            return float(self.value)
        base = resolve_run_path(runs_root, self.baseline_run)
        result_file = base / "eval" / "result.json"
        if not result_file.exists():
            raise ContractError(
                f"baseline run {self.baseline_run} has no eval/result.json "
                "(baselines must be evaluated runs)"
            )
        metrics = json.loads(result_file.read_text(encoding="utf-8"))["metrics"]
        if self.metric not in metrics:
            raise ContractError(
                f"baseline run {self.baseline_run} lacks metric {self.metric!r}"
            )
        return float(metrics[self.metric]) + self.margin

    def check(self, metrics: Dict[str, Any], runs_root: Path) -> dict:
        """Returns {passed: bool|None, detail: str}. passed=None when the
        metric is missing (inconclusive, never silently pass/fail)."""
        if self.metric not in metrics:
            return {"passed": None, "detail": f"metric {self.metric!r} missing"}
        observed = metrics[self.metric]
        ref = self.reference_value(runs_root)
        passed = bool(_OPS[self.op](observed, ref))
        src = f"baseline {self.baseline_run}{self.margin:+g}" if self.baseline_run else "literal"
        return {
            "passed": passed,
            "detail": f"{self.metric}={observed} {self.op} {ref} ({src}) -> {passed}",
        }


@dataclass
class Contract:
    hypothesis: str
    change: str
    controls: Any
    success_metric: Criterion
    failure_condition: Criterion
    required_diagnostics: List[str]
    budget: Dict[str, Any]
    confirmation: Optional[Criterion] = None  # held-out confirmation, optional
    raw: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict) -> "Contract":
        if not isinstance(d, dict):
            raise ContractError("contract must be a mapping")
        missing = [k for k in REQUIRED_FIELDS if k not in d or d[k] in (None, "")]
        if missing:
            raise ContractError(f"contract missing required fields: {missing}")
        if not isinstance(d["required_diagnostics"], list):
            raise ContractError("required_diagnostics must be a list of filenames")
        budget = d["budget"]
        if not isinstance(budget, dict) or not budget:
            raise ContractError("budget must be a non-empty mapping")
        confirmation = None
        if d.get("confirmation") is not None:
            confirmation = Criterion.from_dict(d["confirmation"], "confirmation")
        return Contract(
            hypothesis=str(d["hypothesis"]),
            change=str(d["change"]),
            controls=d["controls"],
            success_metric=Criterion.from_dict(d["success_metric"], "success_metric"),
            failure_condition=Criterion.from_dict(
                d["failure_condition"], "failure_condition"
            ),
            required_diagnostics=[str(x) for x in d["required_diagnostics"]],
            budget=budget,
            confirmation=confirmation,
            raw=d,
        )

    def sha256(self) -> str:
        canonical = json.dumps(self.raw, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_run_path(runs_root: Path, ref: str) -> Path:
    """Resolve a run reference: absolute/relative path, exact id, or unique
    id suffix under runs_root."""
    p = Path(ref)
    if p.is_dir() and (p / "status.json").exists():
        return p
    exact = runs_root / ref
    if exact.is_dir():
        return exact
    if runs_root.is_dir():
        matches = [
            d for d in runs_root.iterdir() if d.is_dir() and d.name.endswith(ref)
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ContractError(f"run ref {ref!r} is ambiguous: {[m.name for m in matches]}")
    raise ContractError(f"run {ref!r} not found under {runs_root}")


def evaluate_contract(
    contract: Contract, metrics: Dict[str, Any], run_dir: Path, runs_root: Path
) -> dict:
    """Deterministic verdict for one run. Crash handling lives in the caller —
    this is only called after a successful execute()."""
    missing_diags = [
        name
        for name in contract.required_diagnostics
        if not list(run_dir.rglob(name))
    ]
    failure = contract.failure_condition.check(metrics, runs_root)
    success = contract.success_metric.check(metrics, runs_root)
    confirmation = (
        contract.confirmation.check(metrics, runs_root)
        if contract.confirmation
        else None
    )

    if missing_diags:
        verdict = "inconclusive"
    elif failure["passed"] is True:
        verdict = "failure"
    elif success["passed"] is True:
        verdict = "success"
    elif success["passed"] is False:
        verdict = "failure" if failure["passed"] is False else "inconclusive"
    else:
        verdict = "inconclusive"

    n_runs = int(metrics.get("n_runs", 1))
    result = {
        "verdict": verdict,
        "confirmed": None if confirmation is None else confirmation["passed"],
        "checks": {
            "success_metric": success,
            "failure_condition": failure,
            "confirmation": confirmation,
        },
        "missing_diagnostics": missing_diags,
        "evidence_strength": "weak (n=1 run)" if n_runs <= 1 else f"n={n_runs} runs",
        "metrics": metrics,
    }
    return result

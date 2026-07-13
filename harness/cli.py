"""Harness CLI.

    python -m harness setup
    python -m harness smoke-test
    python -m harness status
    python -m harness run configs/<exp>.yaml [--no-eval] [--runs-root DIR]
    python -m harness evaluate <run>
    python -m harness resume <run>
    python -m harness compare <run> <run> [...]
    python -m harness loop step [--no-commit] [--skip-baseline] | loop status
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from . import REPO_ROOT, RUNS_ROOT
from .contract import Contract, ContractError, resolve_run_path
from .experiments import EXPERIMENTS
from .rundir import RunDir

SMOKE_TEST_PATHS = [
    "tests",
    "experiments/tic_tac_toe/test_game.py",
    "skills/td-nl/textgrad_backend/test_smoke.py",
]


# --------------------------------------------------------------------------
# core run pipeline (also used by the loop)
# --------------------------------------------------------------------------
def load_config(config_path: Path) -> tuple[dict, Contract]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ContractError(f"{config_path}: config must be a YAML mapping")
    exp_name = cfg.get("experiment")
    if exp_name not in EXPERIMENTS:
        raise ContractError(
            f"{config_path}: unknown experiment {exp_name!r} "
            f"(available: {sorted(EXPERIMENTS)})"
        )
    if "contract" not in cfg:
        raise ContractError(
            f"{config_path}: missing 'contract' block — an experiment may not "
            "run without a contract (hypothesis/success_metric/... defined "
            "before execution)"
        )
    contract = Contract.from_dict(cfg["contract"])
    module = EXPERIMENTS[exp_name]
    cfg["params"] = module.resolve_params(cfg.get("params") or {})
    return cfg, contract


def do_run(
    config_path: Path,
    runs_root: Path = RUNS_ROOT,
    with_eval: bool = True,
) -> RunDir:
    cfg, contract = load_config(config_path)
    module = EXPERIMENTS[cfg["experiment"]]
    name = cfg.get("name") or config_path.stem
    run = RunDir.create(
        runs_root, name, cfg, contract, REPO_ROOT, seed=int(cfg.get("seed", 0))
    )
    print(f"[harness] run {run.id} -> {run.root}")

    run.set_state("running")
    try:
        result = module.execute(cfg["params"], run)
    except BaseException as e:
        run.record_failure("execute", e)
        run.write_summary(_summary_md(run, cfg, contract, None, failed=True))
        print(f"[harness] EXECUTE FAILED: {e} (see {run.root / 'failure.json'})",
              file=sys.stderr)
        raise
    run.write_result(result)
    run.set_state("executed")

    if with_eval:
        do_evaluate(run)
    else:
        run.write_summary(_summary_md(run, cfg, contract, None))
        print("[harness] executed; evaluation pending "
              f"(run: python -m harness evaluate {run.id})")
    return run


def do_evaluate(run: RunDir) -> dict:
    cfg = run.config()
    contract = run.contract()
    if not run.contract_unchanged():
        raise ContractError(
            f"{run.id}: contract.yaml was modified after run creation — "
            "refusing to evaluate against post-hoc criteria"
        )
    if run.status()["state"] not in ("executed", "evaluated"):
        raise ContractError(
            f"{run.id}: state={run.status()['state']} — evaluation requires a "
            "completed execution (a crash is a failure, not evidence)"
        )
    module = EXPERIMENTS[cfg["experiment"]]
    try:
        ev = module.evaluate(cfg["params"], run, contract)
    except BaseException as e:
        run.record_failure("evaluate", e)
        raise
    run.write_eval(ev)
    run.set_state("evaluated")
    run.write_summary(_summary_md(run, cfg, contract, ev))
    print(f"[harness] verdict={ev['verdict']} confirmed={ev['confirmed']} "
          f"({ev['evidence_strength']})")
    return ev


def _summary_md(run: RunDir, cfg: dict, contract: Contract,
                ev: Optional[dict], failed: bool = False) -> str:
    lines = [
        f"# Run {run.id}",
        "",
        f"- experiment: `{cfg['experiment']}`  seed: {cfg.get('seed', 0)}",
        f"- hypothesis: {contract.hypothesis}",
        f"- change: {contract.change}",
        f"- state: {run.status()['state']}",
    ]
    if failed:
        lines += ["", "## FAILED", "",
                  "Execution crashed — see `failure.json`. A crash is recorded "
                  "as a failure, **not** as negative evidence for the hypothesis."]
    elif ev is None:
        lines += ["", "Evaluation pending — the experiment is NOT complete "
                  "until its evaluation has run."]
    else:
        lines += [
            "",
            f"## Verdict: **{ev['verdict']}**"
            + (f" (confirmation: {ev['confirmed']})" if ev["confirmed"] is not None else ""),
            f"- evidence strength: {ev['evidence_strength']}",
            f"- budget exceeded: {ev['budget_exceeded']}",
            "",
            "### Checks",
        ]
        for name, chk in ev["checks"].items():
            if chk is not None:
                lines.append(f"- {name}: {chk['detail']}")
        if ev["missing_diagnostics"]:
            lines.append(f"- missing diagnostics: {ev['missing_diagnostics']}")
        lines += ["", "### Metrics", "```json",
                  json.dumps(ev["metrics"], indent=2), "```"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------
def cmd_setup(_args) -> int:
    ok = True
    checks = []
    checks.append(("python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0]))
    try:
        import yaml as _y  # noqa: F401
        checks.append(("PyYAML", True, _y.__version__))
    except ImportError:
        checks.append(("PyYAML", False, "pip install pyyaml"))
    checks.append(("git", shutil.which("git") is not None, shutil.which("git") or "-"))
    checks.append(("pytest", shutil.which("pytest") is not None or _has_pytest(),
                   "needed for smoke-test"))
    claude = shutil.which("claude") is not None
    checks.append(("claude CLI (optional)", claude,
                   "real-engine runs unavailable without it" if not claude else "ok"))
    RUNS_ROOT.mkdir(exist_ok=True)
    checks.append(("runs/", True, str(RUNS_ROOT)))
    for name, passed, detail in checks:
        mark = "ok " if passed else "MISSING"
        print(f"  [{mark}] {name:<24} {detail}")
        if not passed and "optional" not in name:
            ok = False
    return 0 if ok else 1


def _has_pytest() -> bool:
    try:
        import pytest  # noqa: F401
        return True
    except ImportError:
        return False


def cmd_smoke_test(_args) -> int:
    import os
    env = dict(os.environ, SER_TDNL_DISABLE_ENGINE="1")
    paths = [str(REPO_ROOT / p) for p in SMOKE_TEST_PATHS if (REPO_ROOT / p).exists()]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *paths], cwd=str(REPO_ROOT), env=env
    )
    return proc.returncode


def cmd_run(args) -> int:
    try:
        do_run(Path(args.config), Path(args.runs_root), with_eval=not args.no_eval)
    except ContractError as e:
        print(f"[harness] contract error: {e}", file=sys.stderr)
        return 2
    except BaseException:
        return 3
    return 0


def cmd_evaluate(args) -> int:
    run = RunDir.load(resolve_run_path(Path(args.runs_root), args.run))
    try:
        do_evaluate(run)
    except ContractError as e:
        print(f"[harness] {e}", file=sys.stderr)
        return 2
    return 0


def cmd_resume(args) -> int:
    run = RunDir.load(resolve_run_path(Path(args.runs_root), args.run))
    state = run.status()["state"]
    cfg = run.config()
    module = EXPERIMENTS[cfg["experiment"]]
    if state == "evaluated":
        print(f"[harness] {run.id} already evaluated — nothing to resume")
        return 0
    if state == "executed":
        do_evaluate(run)
        return 0
    # created / running / failed: archive the partial attempt, re-execute in place
    dest = run.archive_attempt()
    print(f"[harness] {run.id}: prior attempt archived to {dest}; re-executing")
    run.set_state("running")
    try:
        result = module.execute(cfg["params"], run)
    except BaseException as e:
        run.record_failure("execute", e)
        print(f"[harness] EXECUTE FAILED again: {e}", file=sys.stderr)
        return 3
    run.write_result(result)
    run.set_state("executed")
    do_evaluate(run)
    return 0


def cmd_compare(args) -> int:
    rows = []
    keys: List[str] = []
    for ref in args.runs:
        run = RunDir.load(resolve_run_path(Path(args.runs_root), ref))
        ev = run.eval_result()
        row = {"run": run.id,
               "experiment": run.config().get("experiment"),
               "state": run.status()["state"],
               "verdict": ev["verdict"] if ev else "-",
               "confirmed": (ev or {}).get("confirmed")}
        for k, v in ((ev or {}).get("metrics") or {}).items():
            row[k] = v
            if k not in keys:
                keys.append(k)
        rows.append(row)
    cols = ["run", "experiment", "state", "verdict", "confirmed"] + keys
    widths = {c: max(len(c), *(len(_fmt(r.get(c))) for r in rows)) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    for r in rows:
        print("  ".join(_fmt(r.get(c)).ljust(widths[c]) for c in cols))
    return 0


def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def cmd_status(args) -> int:
    from .status import print_status

    print_status(REPO_ROOT, Path(args.runs_root))
    return 0


def cmd_ext_status(args) -> int:
    from .ext_status import print_ext_status

    print_ext_status(REPO_ROOT, ssh=args.ssh, include_all=args.all)
    return 0


def cmd_loop(args) -> int:
    from .loop import Loop

    loop = Loop(REPO_ROOT, Path(args.runs_root))
    if args.action == "status":
        loop.print_status()
        return 0
    return loop.step(commit=not args.no_commit, skip_baseline=args.skip_baseline)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="harness", description=__doc__)
    ap.add_argument("--runs-root", default=str(RUNS_ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup").set_defaults(fn=cmd_setup)
    sub.add_parser("smoke-test").set_defaults(fn=cmd_smoke_test)
    sub.add_parser("status").set_defaults(fn=cmd_status)

    p = sub.add_parser("ext-status")
    p.add_argument("--ssh", action="store_true",
                   help="check remote PIDs / tail remote logs via ssh")
    p.add_argument("--all", action="store_true",
                   help="include completed/failed records, not just active ones")
    p.set_defaults(fn=cmd_ext_status)

    p = sub.add_parser("run")
    p.add_argument("config")
    p.add_argument("--no-eval", action="store_true",
                   help="execute only; evaluation can be run later")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("evaluate")
    p.add_argument("run")
    p.set_defaults(fn=cmd_evaluate)

    p = sub.add_parser("resume")
    p.add_argument("run")
    p.set_defaults(fn=cmd_resume)

    p = sub.add_parser("compare")
    p.add_argument("runs", nargs="+")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("loop")
    p.add_argument("action", choices=["step", "status"])
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--skip-baseline", action="store_true",
                   help="skip the baseline smoke-test check (tests only)")
    p.set_defaults(fn=cmd_loop)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

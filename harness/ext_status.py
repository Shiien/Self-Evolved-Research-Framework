"""`python -m harness ext-status` — deterministic polling of external GPU
runs recorded in logs/experiments/*.yaml.

Migrated from the experiment-monitor skill's mechanical core: liveness
checks, log tailing, and error-pattern detection. Read-only: interpreting
results and updating the yaml records stays with the skill/user, mirroring
the status-vs-checklist split.

Liveness is checked locally when the record's machine is this host; with
--ssh, remote PIDs and log tails are fetched via `ssh {user}@{ip}` (fails
soft per record — an unreachable host reports "unreachable", never crashes
the report).
"""
from __future__ import annotations

import platform
import re
import subprocess
from pathlib import Path
from typing import List, Optional

import yaml

ACTIVE_STATES = ("launched", "running")
ERROR_PATTERNS = [
    (re.compile(r"CUDA out of memory|OutOfMemoryError", re.I), "OOM"),
    (re.compile(r"\bnan\b.*loss|loss.*\bnan\b", re.I), "NaN-loss"),
    (re.compile(r"Traceback \(most recent call last\)"), "traceback"),
    (re.compile(r"Segmentation fault|core dumped", re.I), "segfault"),
]
_METRIC_RE = re.compile(r"loss|reward|acc|epoch|step", re.I)


def _run(cmd: List[str], timeout: float = 15.0) -> Optional[str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout if p.returncode == 0 else None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _is_local(machine: str) -> bool:
    host = platform.node()
    return machine in ("local", "localhost", host)


def check_record(record: dict, ssh: bool = False, tail_lines: int = 20) -> dict:
    """Poll one experiment record. Returns a report dict; never raises."""
    out = {
        "exp_id": record.get("exp_id", "?"),
        "machine": record.get("machine", "?"),
        "recorded_status": record.get("status", "?"),
        "pid_alive": None,       # True/False/None(unchecked)/"unreachable"
        "errors": [],
        "last_metric_line": None,
        "log_tail": None,
    }
    pid = record.get("pid")
    ip = record.get("ip")
    user = record.get("ssh_user", "hsshi")
    log_file = record.get("log_file")
    local = _is_local(out["machine"])

    if pid:
        if local:
            out["pid_alive"] = _run(["ps", "-p", str(pid), "-o", "pid="]) is not None
        elif ssh and ip:
            res = _run(["ssh", "-o", "ConnectTimeout=5", f"{user}@{ip}",
                        f"ps -p {pid} -o pid= 2>/dev/null"])
            out["pid_alive"] = "unreachable" if res is None else bool(res.strip())

    tail = None
    if log_file:
        if local and Path(log_file).exists():
            tail = "\n".join(
                Path(log_file).read_text(encoding="utf-8", errors="replace")
                .splitlines()[-tail_lines:]
            )
        elif ssh and ip:
            tail = _run(["ssh", "-o", "ConnectTimeout=5", f"{user}@{ip}",
                         f"tail -{tail_lines} {log_file} 2>/dev/null"])
    if tail:
        out["log_tail"] = tail
        for pattern, label in ERROR_PATTERNS:
            if pattern.search(tail):
                out["errors"].append(label)
        metric_lines = [ln for ln in tail.splitlines() if _METRIC_RE.search(ln)]
        if metric_lines:
            out["last_metric_line"] = metric_lines[-1].strip()[:160]
    return out


def load_active(experiments_log_dir: Path, include_all: bool = False) -> List[dict]:
    records = []
    if not experiments_log_dir.is_dir():
        return records
    for f in sorted(experiments_log_dir.glob("*.yaml")):
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if include_all or d.get("status") in ACTIVE_STATES:
            d.setdefault("exp_id", f.stem)
            records.append(d)
    return records


def print_ext_status(repo_root: Path, ssh: bool = False, include_all: bool = False) -> None:
    records = load_active(repo_root / "logs" / "experiments", include_all=include_all)
    if not records:
        print("[EXT] no active external runs in logs/experiments/ "
              "(use --all to include finished ones)")
        return
    print(f"[EXT] {len(records)} external run(s)"
          + ("" if ssh else "  (local checks only — pass --ssh for remote liveness)"))
    for rec in records:
        r = check_record(rec, ssh=ssh)
        alive = {True: "alive", False: "DEAD", None: "unchecked",
                 "unreachable": "unreachable"}[r["pid_alive"]]
        errs = f"  errors={','.join(r['errors'])}" if r["errors"] else ""
        print(f"  {r['exp_id']}  {r['recorded_status']}  on {r['machine']}  pid={alive}{errs}")
        if r["last_metric_line"]:
            print(f"    last metric: {r['last_metric_line']}")
        if r["errors"] and r["log_tail"]:
            print("    tail: " + r["log_tail"].splitlines()[-1][:150])
        if not rec.get("contract"):
            print("    [!] record has NO CONTRACT — evaluation criteria were not pre-registered")

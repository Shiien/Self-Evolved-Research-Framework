"""`python -m harness ext-launch` — contract-gated launcher for external GPU
runs (other repos / remote machines), migrated from the experiment-run
skill's dispatch mechanics.

Refuses to launch without a valid 7-field experiment contract; writes the
run record (contract embedded, criteria frozen at launch) to
logs/experiments/{exp_id}.yaml; launches via nohup locally or over ssh and
captures the PID. GPU selection and environment verification remain the
experiment-run skill's judgment — this module only executes and records.
"""
from __future__ import annotations

import platform
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional

import yaml

from .contract import Contract, ContractError


def load_contract_file(path: Path) -> Contract:
    """Accept either a bare contract mapping or a config file with a
    `contract:` block."""
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise ContractError(f"{path}: not a YAML mapping")
    if "contract" in d and isinstance(d["contract"], dict):
        d = d["contract"]
    return Contract.from_dict(d)


def next_exp_id(experiments_log_dir: Path) -> str:
    date = time.strftime("%Y%m%d")
    n = 1
    while (experiments_log_dir / f"exp-{date}-{n:03d}.yaml").exists():
        n += 1
    return f"exp-{date}-{n:03d}"


def build_launch(
    command: str,
    workdir: str,
    gpu: str,
    log_file: str,
    machine: str,
    ip: Optional[str],
    ssh_user: str,
) -> list:
    """Return the argv that launches the run and echoes the PID."""
    inner = (
        f"cd {shlex.quote(workdir)} && "
        f"CUDA_VISIBLE_DEVICES={gpu} nohup {command} "
        f"> {shlex.quote(log_file)} 2>&1 & echo $!"
    )
    if machine in ("local", "localhost", platform.node()):
        return ["bash", "-c", inner]
    if not ip:
        raise ContractError(f"remote machine {machine!r} needs --ip")
    return ["ssh", "-o", "ConnectTimeout=10", f"{ssh_user}@{ip}", inner]


def launch(
    repo_root: Path,
    command: str,
    machine: str,
    gpu: str,
    workdir: str,
    contract_path: Path,
    ip: Optional[str] = None,
    ssh_user: str = "hsshi",
    exp_id: Optional[str] = None,
    log_file: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Validate the contract, launch, and write the run record.
    Returns the record dict. Raises ContractError before any side effect
    when the contract is missing/invalid — no contract, no launch."""
    contract = load_contract_file(contract_path)  # gate FIRST

    log_dir = repo_root / "logs" / "experiments"
    log_dir.mkdir(parents=True, exist_ok=True)
    exp_id = exp_id or next_exp_id(log_dir)
    log_file = log_file or f"/tmp/{exp_id}.log"
    argv = build_launch(command, workdir, gpu, log_file, machine, ip, ssh_user)

    record = {
        "exp_id": exp_id,
        "command": command,
        "machine": machine,
        "ip": ip,
        "gpu": str(gpu),
        "pid": None,
        "ssh_user": ssh_user,
        "working_dir": workdir,
        "log_file": log_file,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "launched",
        "ended": None,
        "last_checked": None,
        "latest_metrics": {},
        "final_metrics": {},
        "error_summary": None,
        "contract": contract.raw,
    }

    if dry_run:
        print("[ext-launch] DRY RUN — would execute:")
        print("  " + " ".join(shlex.quote(a) for a in argv))
        print("[ext-launch] would write record:")
        print(yaml.safe_dump(record, sort_keys=False, allow_unicode=True))
        return record

    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(
            f"launch failed rc={proc.returncode}: {proc.stderr.strip()[:400]}"
        )
    pid_str = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    record["pid"] = int(pid_str) if pid_str.isdigit() else None

    record_path = log_dir / f"{exp_id}.yaml"
    record_path.write_text(
        yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[ext-launch] {exp_id} launched on {machine} gpu={gpu} pid={record['pid']}")
    print(f"[ext-launch] record: {record_path}  log: {log_file}")
    print("[ext-launch] monitor: python -m harness ext-status --ssh")
    return record

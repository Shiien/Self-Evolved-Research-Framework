"""harness ext-launch: contract gate, dry-run, local launch + record."""
import platform
import time

import pytest
import yaml

from harness.contract import ContractError
from harness.ext_launch import build_launch, launch, load_contract_file, next_exp_id

CONTRACT = {
    "hypothesis": "h",
    "change": "c",
    "controls": "ctrl",
    "success_metric": {"metric": "confirm.x", "op": ">=", "value": 1},
    "failure_condition": {"metric": "dev.y", "op": ">", "value": 5},
    "required_diagnostics": ["log"],
    "budget": {"max_minutes": 1},
}


def test_refuses_without_valid_contract(tmp_path):
    bad = tmp_path / "c.yaml"
    bad.write_text("hypothesis: h\n", encoding="utf-8")  # missing 6 fields
    with pytest.raises(ContractError):
        launch(tmp_path, command="echo hi", machine="local", gpu="0",
               workdir=str(tmp_path), contract_path=bad, dry_run=True)
    assert not (tmp_path / "logs").exists()  # gate fired before side effects


def test_contract_block_in_config_accepted(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml.safe_dump({"experiment": "x", "contract": CONTRACT}),
                   encoding="utf-8")
    assert load_contract_file(cfg).hypothesis == "h"


def test_dry_run_writes_nothing(tmp_path, capsys):
    c = tmp_path / "c.yaml"
    c.write_text(yaml.safe_dump(CONTRACT), encoding="utf-8")
    rec = launch(tmp_path, command="echo hi", machine="local", gpu="0",
                 workdir=str(tmp_path), contract_path=c, dry_run=True)
    assert rec["status"] == "launched" and rec["pid"] is None
    assert "DRY RUN" in capsys.readouterr().out
    assert not (tmp_path / "logs" / "experiments").exists() or \
        not list((tmp_path / "logs" / "experiments").glob("*.yaml"))


def test_remote_without_ip_refused(tmp_path):
    with pytest.raises(ContractError, match="--ip"):
        build_launch("echo", str(tmp_path), "0", "/tmp/x.log", "remote-13",
                     None, "hsshi")


def test_local_launch_writes_record_and_runs(tmp_path):
    c = tmp_path / "c.yaml"
    c.write_text(yaml.safe_dump(CONTRACT), encoding="utf-8")
    log = tmp_path / "run.log"
    rec = launch(tmp_path, command="echo launched-ok", machine=platform.node(),
                 gpu="0", workdir=str(tmp_path), contract_path=c,
                 exp_id="exp-test-001", log_file=str(log))
    record_file = tmp_path / "logs" / "experiments" / "exp-test-001.yaml"
    assert record_file.exists()
    stored = yaml.safe_load(record_file.read_text(encoding="utf-8"))
    assert stored["contract"]["hypothesis"] == "h"  # criteria frozen at launch
    assert stored["status"] == "launched"
    assert isinstance(rec["pid"], int)
    for _ in range(20):  # nohup'd echo finishes quickly
        if log.exists() and "launched-ok" in log.read_text(encoding="utf-8"):
            break
        time.sleep(0.05)
    assert "launched-ok" in log.read_text(encoding="utf-8")


def test_next_exp_id_sequential(tmp_path):
    d = tmp_path / "logs" / "experiments"
    d.mkdir(parents=True)
    first = next_exp_id(d)
    (d / f"{first}.yaml").write_text("", encoding="utf-8")
    assert next_exp_id(d) != first

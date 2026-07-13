"""Run directory lifecycle: creation, state, failure recording, resume."""
import pytest

from harness.contract import Contract
from harness.rundir import RunDir
from tests.test_contract import VALID


@pytest.fixture
def run(tmp_path):
    contract = Contract.from_dict(dict(VALID))
    return RunDir.create(
        tmp_path / "runs", "unit", {"experiment": "x", "seed": 3},
        contract, tmp_path, seed=3,
    )


def test_create_writes_required_files(run):
    for name in ("config.yaml", "contract.yaml", "meta.json", "status.json",
                 "metrics.jsonl"):
        assert (run.root / name).exists(), name
    for d in (run.logs, run.artifacts, run.checkpoints, run.eval_dir):
        assert d.is_dir()
    assert run.status()["state"] == "created"
    assert run.meta()["seed"] == 3
    assert run.meta()["contract_sha256"] == run.contract().sha256()
    assert run.contract_unchanged()


def test_state_transitions_keep_history(run):
    run.set_state("running")
    run.set_state("executed")
    s = run.status()
    assert s["state"] == "executed"
    assert [h["state"] for h in s["history"]] == ["created", "running"]


def test_failure_recording(run):
    run.set_state("running")
    try:
        raise ValueError("boom")
    except ValueError as e:
        run.record_failure("execute", e)
    assert run.status()["state"] == "failed"
    assert run.status()["failed_stage"] == "execute"
    fail = (run.root / "failure.json").read_text(encoding="utf-8")
    assert "boom" in fail and "Traceback" in fail


def test_contract_tamper_detected(run):
    f = run.root / "contract.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "hypothesis: h", "hypothesis: tampered"), encoding="utf-8")
    assert not run.contract_unchanged()


def test_archive_attempt_resets_outputs(run):
    (run.artifacts / "junk.txt").write_text("x", encoding="utf-8")
    run.append_metric({"a": 1})
    try:
        raise RuntimeError("crash")
    except RuntimeError as e:
        run.record_failure("execute", e)
    dest = run.archive_attempt()
    assert (dest / "artifacts" / "junk.txt").exists()
    assert (dest / "failure.json").exists()
    assert not (run.root / "failure.json").exists()
    assert (run.root / "metrics.jsonl").read_text(encoding="utf-8") == ""
    assert run.artifacts.is_dir() and not list(run.artifacts.iterdir())


def test_load_rejects_non_run_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        RunDir.load(tmp_path)

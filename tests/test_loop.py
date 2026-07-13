"""Loop state machine over temporary state files (never the repo's own)."""
import json

import pytest

from harness import REPO_ROOT
from harness.loop import Loop

STATE_MD = """# Research State

## Current research question
q

## Active hypotheses
- h

## Established evidence

## Unresolved uncertainties

## Next recommended experiments
"""


@pytest.fixture
def loop_env(tmp_path):
    state = tmp_path / "RESEARCH_STATE.md"
    state.write_text(STATE_MD, encoding="utf-8")
    ledger = tmp_path / "EXPERIMENTS.json"
    ledger.write_text(json.dumps({
        "experiments": [{
            "id": "exp-t1",
            "question": "does the smoke pipeline hold?",
            "config": "configs/ttt_smoke.yaml",
            "status": "planned", "run": None, "verdict": None,
        }]
    }), encoding="utf-8")
    return Loop(REPO_ROOT, tmp_path / "runs", state_md=state, ledger_path=ledger)


def test_step_runs_one_experiment_and_records_evidence(loop_env):
    rc = loop_env.step(commit=False, skip_baseline=True)
    assert rc == 0
    ledger = json.loads(loop_env.ledger_path.read_text(encoding="utf-8"))
    item = ledger["experiments"][0]
    assert item["status"] == "complete"
    assert item["verdict"] == "success"
    assert item["run"]
    assert (loop_env.runs_root / item["run"] / "eval" / "result.json").exists()
    state = loop_env.state_md.read_text(encoding="utf-8")
    assert "exp-t1" in state and "SUPPORTS" in state
    assert "weak" in state  # strength stamp propagated verbatim


def test_step_with_nothing_planned_is_a_noop(loop_env):
    loop_env.step(commit=False, skip_baseline=True)
    before = loop_env.state_md.read_text(encoding="utf-8")
    assert loop_env.step(commit=False, skip_baseline=True) == 0
    assert loop_env.state_md.read_text(encoding="utf-8") == before


def test_invalid_config_blocks_run(loop_env, tmp_path):
    ledger = json.loads(loop_env.ledger_path.read_text(encoding="utf-8"))
    ledger["experiments"][0]["config"] = "configs/does-not-exist.yaml"
    loop_env.ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    assert loop_env.step(commit=False, skip_baseline=True) == 2
    ledger = json.loads(loop_env.ledger_path.read_text(encoding="utf-8"))
    assert ledger["experiments"][0]["status"] == "planned"  # untouched


def test_missing_state_files_refuse(tmp_path):
    loop = Loop(REPO_ROOT, tmp_path / "runs",
                state_md=tmp_path / "nope.md", ledger_path=tmp_path / "nope.json")
    assert loop.step(commit=False, skip_baseline=True) == 2

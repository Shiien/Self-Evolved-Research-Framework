"""Deterministic end-to-end harness run of the migrated TTT experiment:
scripted engine, shim evolve, sandboxed state. No LLM, no cost, and it must
leave the live repo state (SKILL.md, feedback-log.md) untouched."""
import hashlib
import json
from pathlib import Path

import pytest

from harness import REPO_ROOT
from harness.cli import do_run, main as cli_main

SMOKE_CONFIG = REPO_ROOT / "configs" / "ttt_smoke.yaml"
LIVE_SKILL = REPO_ROOT / "skills" / "play-tic-tac-toe" / "SKILL.md"
LIVE_LOG = REPO_ROOT / "skills" / "td-nl" / "feedback-log.md"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def smoke_run(tmp_path_factory):
    runs_root = tmp_path_factory.mktemp("runs")
    before = (_sha(LIVE_SKILL), _sha(LIVE_LOG))
    run = do_run(SMOKE_CONFIG, runs_root, with_eval=True)
    after = (_sha(LIVE_SKILL), _sha(LIVE_LOG))
    assert before == after, "sandboxed run mutated live repo state"
    return run


def test_run_directory_is_self_contained(smoke_run):
    r = smoke_run.root
    for name in ("config.yaml", "contract.yaml", "meta.json", "status.json",
                 "metrics.jsonl", "summary.md"):
        assert (r / name).exists(), name
    assert (r / "artifacts" / "games.jsonl").exists()
    assert (r / "artifacts" / "result.json").exists()
    assert (r / "artifacts" / "sandbox" / "feedback-log.md").exists()
    assert (r / "logs" / "engine-calls.jsonl").exists()
    assert (r / "eval" / "result.json").exists()
    assert (r / "checkpoints" / "spec-initial.md").exists()
    assert (r / "checkpoints" / "spec-after-game-02.md").exists()
    assert smoke_run.status()["state"] == "evaluated"


def test_games_are_deterministic(smoke_run):
    lines = (smoke_run.artifacts / "games.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lines) == 2
    games = [json.loads(l) for l in lines]
    # scripted first-legal engine: X plays 1,3,5,7 -> wins on diagonal 3-5-7
    for g in games:
        assert g["terminal"] == "win" and g["winner"] == "X"
        assert [m["cell"] for m in g["moves"]] == [1, 2, 3, 4, 5, 6, 7]
    # metrics.jsonl mirrors the games
    metrics = [json.loads(l) for l in
               (smoke_run.root / "metrics.jsonl").read_text().splitlines()]
    assert [m["game"] for m in metrics] == [1, 2]


def test_evolve_ran_and_apply_was_guarded(smoke_run):
    result = smoke_run.result()
    # shim evolve ran per game (stdout logs exist)
    assert (smoke_run.logs / "evolve-g01.stdout.txt").exists()
    assert (smoke_run.logs / "evolve-g02.stdout.txt").exists()
    # the validity guard must never let a shim placeholder become the spec
    assert result["edits_applied"] == 0
    assert result["final_spec_valid"] is True
    spec = (smoke_run.artifacts / "sandbox" / "skills" / "play-tic-tac-toe"
            / "SKILL.md").read_text(encoding="utf-8")
    assert "<<EVOLVE NOTE" not in spec


def test_evaluation_verdict(smoke_run):
    ev = smoke_run.eval_result()
    assert ev["verdict"] == "success"
    assert ev["confirmed"] is True
    assert ev["metrics"]["dev.forfeits"] == 0
    assert ev["metrics"]["confirm.forfeit_rate"] == 0.0
    assert ev["metrics"]["llm_calls"] == 0
    assert "weak" in ev["evidence_strength"]  # single run stays labeled weak


def test_evaluate_refuses_tampered_contract(smoke_run):
    f = smoke_run.root / "contract.yaml"
    original = f.read_text(encoding="utf-8")
    try:
        f.write_text(original.replace("value: 0", "value: 99"), encoding="utf-8")
        rc = cli_main(["--runs-root", str(smoke_run.root.parent),
                       "evaluate", smoke_run.id])
        assert rc == 2
    finally:
        f.write_text(original, encoding="utf-8")


def test_compare_and_resume_cli(smoke_run, capsys):
    runs_root = str(smoke_run.root.parent)
    assert cli_main(["--runs-root", runs_root, "compare", smoke_run.id]) == 0
    out = capsys.readouterr().out
    assert "success" in out
    # resume on an evaluated run is a no-op
    assert cli_main(["--runs-root", runs_root, "resume", smoke_run.id]) == 0

"""End-to-end resume: a run that crashes mid-execute is re-executed in place
(same run id, prior attempt archived) and completes through evaluation."""
import pytest

from harness import REPO_ROOT
from harness.cli import do_run, main as cli_main
from harness.experiments import ttt_cycle

SMOKE_CONFIG = REPO_ROOT / "configs" / "ttt_smoke.yaml"


def test_failed_run_resumes_in_place(tmp_path, monkeypatch):
    runs_root = tmp_path / "runs"
    real_execute = ttt_cycle.execute

    def crash(params, run):
        raise RuntimeError("injected mid-execute crash")

    monkeypatch.setattr(ttt_cycle, "execute", crash)
    with pytest.raises(RuntimeError, match="injected"):
        do_run(SMOKE_CONFIG, runs_root, with_eval=True)

    run_dir = next(runs_root.iterdir())
    assert (run_dir / "failure.json").exists()
    assert "injected" in (run_dir / "failure.json").read_text(encoding="utf-8")
    summary = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "not** as negative evidence" in summary

    monkeypatch.setattr(ttt_cycle, "execute", real_execute)
    rc = cli_main(["--runs-root", str(runs_root), "resume", run_dir.name])
    assert rc == 0
    # same run id, prior attempt archived, evaluation complete
    assert (run_dir / "attempts" / "attempt-1" / "failure.json").exists()
    assert not (run_dir / "failure.json").exists()
    assert (run_dir / "eval" / "result.json").exists()
    import json
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "evaluated"

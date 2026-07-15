"""harness ext-status: record loading, error detection, local liveness."""
import os

from harness.ext_status import check_record, load_active


def _write(dirpath, name, text):
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / name).write_text(text, encoding="utf-8")


def test_load_active_filters_by_status(tmp_path):
    d = tmp_path / "logs" / "experiments"
    _write(d, "a.yaml", "exp_id: a\nstatus: running\n")
    _write(d, "b.yaml", "exp_id: b\nstatus: completed\n")
    _write(d, "c.yaml", "exp_id: c\nstatus: launched\n")
    assert [r["exp_id"] for r in load_active(d)] == ["a", "c"]
    assert len(load_active(d, include_all=True)) == 3


def test_check_record_detects_errors_in_local_log(tmp_path):
    log = tmp_path / "exp.log"
    log.write_text(
        "step 100 loss=0.52\nstep 200 loss=nan\n"
        "Traceback (most recent call last):\n  ...\n"
        "torch.cuda.OutOfMemoryError: CUDA out of memory\n",
        encoding="utf-8",
    )
    import platform
    rec = {"exp_id": "x", "machine": platform.node(),
           "status": "running", "log_file": str(log)}
    r = check_record(rec)
    assert set(r["errors"]) == {"OOM", "NaN-loss", "traceback"}
    assert "loss=nan" in r["last_metric_line"]


def test_check_record_local_pid_liveness(tmp_path):
    import platform
    rec = {"exp_id": "x", "machine": platform.node(),
           "status": "running", "pid": os.getpid()}
    assert check_record(rec)["pid_alive"] is True
    rec["pid"] = 2 ** 22 + 12345  # near-certainly nonexistent
    assert check_record(rec)["pid_alive"] is False


def test_check_record_never_raises_on_garbage():
    r = check_record({})
    assert r["exp_id"] == "?" and r["pid_alive"] is None and r["errors"] == []

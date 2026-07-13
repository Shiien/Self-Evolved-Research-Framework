"""harness status: deterministic aggregation over fixture state files."""
import json

from harness.status import (
    checklist_summary,
    external_summary,
    ledger_summary,
    runs_summary,
)


def test_ledger_summary(tmp_path):
    assert ledger_summary(tmp_path / "nope.json") is None
    (tmp_path / "EXPERIMENTS.json").write_text(json.dumps({
        "experiments": [
            {"id": "a", "status": "complete", "question": "q1"},
            {"id": "b", "status": "planned", "question": "q2"},
            {"id": "c", "status": "failed", "question": "q3"},
        ]
    }), encoding="utf-8")
    led = ledger_summary(tmp_path / "EXPERIMENTS.json")
    assert led["counts"] == {"complete": 1, "planned": 1, "failed": 1}
    assert led["planned"][0]["id"] == "b"
    assert led["failed"][0]["id"] == "c"


def test_runs_summary(tmp_path):
    r = tmp_path / "runs" / "20260101-000000-x"
    (r / "eval").mkdir(parents=True)
    (r / "status.json").write_text(json.dumps({"state": "evaluated"}))
    (r / "eval" / "result.json").write_text(json.dumps(
        {"verdict": "success", "evidence_strength": "weak (n=1 run)"}))
    (tmp_path / "runs" / "not-a-run").mkdir()  # ignored: no status.json
    out = runs_summary(tmp_path / "runs")
    assert len(out) == 1
    assert out[0]["state"] == "evaluated"
    assert "success" in out[0]["verdict"]


def test_external_summary_flags_missing_contract(tmp_path):
    d = tmp_path / "logs" / "experiments"
    d.mkdir(parents=True)
    (d / "exp-1.yaml").write_text(
        "exp_id: exp-1\nstatus: running\nmachine: remote-13\n"
        "contract:\n  hypothesis: h\n", encoding="utf-8")
    (d / "exp-2.yaml").write_text(
        "exp_id: exp-2\nstatus: launched\nmachine: remote-3\n", encoding="utf-8")
    out = external_summary(d)
    assert [e["has_contract"] for e in out] == [True, False]


def test_checklist_summary_counts_fresh_ignoring_stale_caches(tmp_path):
    ck = tmp_path / "checklists"
    (ck / "short-term").mkdir(parents=True)
    # stale branch cache [0/9] must be ignored; children counted directly
    (ck / "short-term.md").write_text(
        "# Short\n- [x] leaf done\n- [ ] leaf todo\n"
        "- [0/9] branch → checklists/short-term/x.md\n", encoding="utf-8")
    (ck / "short-term" / "x.md").write_text(
        "- [v] verified child\n- [U] signed off\n- [ ] open child\n",
        encoding="utf-8")
    terms = checklist_summary(tmp_path)
    st = terms["short-term"]
    assert st == {"done": 3, "total": 5, "blocked_signoff": 1,
                  "verified": 1, "todo": 2}
    assert terms["mid-term"]["total"] == 0

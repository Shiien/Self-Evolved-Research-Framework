"""Contract parsing, validation, criteria evaluation, and hashing."""
import pytest

from harness.contract import Contract, ContractError, Criterion, evaluate_contract

VALID = {
    "hypothesis": "h",
    "change": "c",
    "controls": "ctrl",
    "success_metric": {"metric": "dev.x", "op": "<=", "value": 1},
    "failure_condition": {"metric": "dev.y", "op": ">", "value": 5},
    "required_diagnostics": [],
    "budget": {"max_minutes": 1},
}


def test_valid_contract_parses():
    c = Contract.from_dict(dict(VALID))
    assert c.hypothesis == "h"
    assert c.confirmation is None


def test_missing_field_rejected():
    for field in ("hypothesis", "success_metric", "budget"):
        d = dict(VALID)
        del d[field]
        with pytest.raises(ContractError):
            Contract.from_dict(d)


def test_criterion_needs_exactly_one_reference():
    with pytest.raises(ContractError):
        Criterion.from_dict({"metric": "m", "op": "<"}, "x")
    with pytest.raises(ContractError):
        Criterion.from_dict(
            {"metric": "m", "op": "<", "value": 1, "baseline_run": "r"}, "x"
        )


def test_bad_op_rejected():
    with pytest.raises(ContractError):
        Criterion.from_dict({"metric": "m", "op": "~", "value": 1}, "x")


def test_hash_stable_under_key_order():
    a = Contract.from_dict(dict(VALID))
    b = Contract.from_dict(dict(reversed(list(VALID.items()))))
    assert a.sha256() == b.sha256()
    changed = dict(VALID, hypothesis="different")
    assert Contract.from_dict(changed).sha256() != a.sha256()


def test_evaluate_contract_verdicts(tmp_path):
    c = Contract.from_dict(dict(VALID))
    # success: dev.x <= 1, failure condition not met
    ev = evaluate_contract(c, {"dev.x": 0.5, "dev.y": 0}, tmp_path, tmp_path)
    assert ev["verdict"] == "success"
    # failure condition dominates
    ev = evaluate_contract(c, {"dev.x": 0.5, "dev.y": 10}, tmp_path, tmp_path)
    assert ev["verdict"] == "failure"
    # missing metric -> inconclusive, never a silent pass
    ev = evaluate_contract(c, {"dev.y": 0}, tmp_path, tmp_path)
    assert ev["verdict"] == "inconclusive"
    # single run is stamped weak
    assert "weak" in ev["evidence_strength"]


def test_missing_diagnostic_is_inconclusive(tmp_path):
    d = dict(VALID, required_diagnostics=["nonexistent.jsonl"])
    c = Contract.from_dict(d)
    ev = evaluate_contract(c, {"dev.x": 0.0, "dev.y": 0}, tmp_path, tmp_path)
    assert ev["verdict"] == "inconclusive"
    assert ev["missing_diagnostics"] == ["nonexistent.jsonl"]

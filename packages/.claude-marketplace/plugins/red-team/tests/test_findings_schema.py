"""Unit tests for findings_schema.validate — pure deterministic transform."""

from findings_schema import validate


def _valid_finding():
    return {
        "id": "X-1",
        "severity": "BLOCK",
        "location": "file.py:1",
        "title": "t",
        "detail": "d",
        "evidence": "e",
        "fix": "f",
    }


def test_valid_object_passes():
    assert validate({"specialist": "x", "findings": [_valid_finding()]}) == []


def test_empty_findings_list_passes_schema():
    # The verdict function (separate) handles the empty case per FM-3.
    assert validate({"specialist": "x", "findings": []}) == []


def test_missing_required_field_fails():
    f = _valid_finding()
    del f["evidence"]
    errs = validate({"findings": [f]})
    assert any("evidence" in e for e in errs)


def test_invalid_severity_fails():
    f = _valid_finding()
    f["severity"] = "CRITICAL"
    errs = validate({"findings": [f]})
    assert any("severity" in e for e in errs)


def test_invalid_claim_type_fails():
    f = _valid_finding()
    f["claim_type"] = "guess"
    errs = validate({"findings": [f]})
    assert any("claim_type" in e for e in errs)


def test_non_dict_input_fails():
    assert validate("not a dict") == ["findings object is not a dict"]


def test_missing_findings_key_fails():
    assert validate({"specialist": "x"}) == ["missing 'findings' list"]

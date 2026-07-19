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


def _valid_obj(findings=None):
    """Construct a minimally-valid findings object with both required top-level fields."""
    return {"specialist": "x", "writer_session": "s1", "findings": findings or [_valid_finding()]}


def test_valid_object_passes():
    assert validate(_valid_obj()) == []


def test_empty_findings_list_passes_schema():
    # The verdict function (separate) handles the empty case per FM-3.
    assert validate(_valid_obj(findings=[])) == []


def test_missing_required_field_fails():
    f = _valid_finding()
    del f["evidence"]
    errs = validate(_valid_obj(findings=[f]))
    assert any("evidence" in e for e in errs)


def test_invalid_severity_fails():
    f = _valid_finding()
    f["severity"] = "CRITICAL"
    errs = validate(_valid_obj(findings=[f]))
    assert any("severity" in e for e in errs)


def test_invalid_claim_type_fails():
    f = _valid_finding()
    f["claim_type"] = "guess"
    errs = validate(_valid_obj(findings=[f]))
    assert any("claim_type" in e for e in errs)


def test_non_dict_input_fails():
    assert validate("not a dict") == ["findings object is not a dict"]


def test_missing_findings_key_fails():
    errs = validate({"specialist": "x", "writer_session": "s1"})
    assert any("missing 'findings' list" in e for e in errs)


def test_missing_top_level_writer_session_fails():
    """writer_session is the staleness guard — without it, a file cannot be bound
    to the run that produced it, and FM-4 cannot distinguish a fresh write from
    a leftover from a prior run. The schema must reject its absence."""
    obj = {"specialist": "x", "findings": []}
    errs = validate(obj)
    assert any("writer_session" in e and "top-level" in e for e in errs)


def test_missing_top_level_specialist_fails():
    """specialist identifies which agent wrote the file; required for the critic's
    per-specialist dedupe and the dispatch manifest's DISPATCHED/DEFERRED labels."""
    obj = {"writer_session": "s1", "findings": []}
    errs = validate(obj)
    assert any("specialist" in e and "top-level" in e for e in errs)

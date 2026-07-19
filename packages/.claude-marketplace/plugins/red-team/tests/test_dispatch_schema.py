"""Unit tests for dispatch_schema — pure deterministic transform."""

import sys
from pathlib import Path

# Add __lib to path (same pattern as test_findings_schema.py)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "__lib"))

from dispatch_schema import validate, dispatched_paths  # noqa: E402


def _valid_manifest():
    return {
        "run_id": "20260719-133433",
        "session_id": "s1",
        "specialists": [
            {"name": "failure-modes", "status": "DISPATCHED", "path": "/run/failure-modes.json"},
            {"name": "logic", "status": "DEFERRED", "reason": "timeout", "path": None},
        ],
    }


def test_valid_manifest_passes():
    assert validate(_valid_manifest()) == []


def test_empty_specialists_list_passes():
    """An empty specialists list is structurally valid — FM-3 (empty input)
    handles the semantic 'no work to do' case at the verdict layer."""
    m = _valid_manifest()
    m["specialists"] = []
    assert validate(m) == []


def test_missing_top_level_field_fails():
    m = _valid_manifest()
    del m["run_id"]
    errs = validate(m)
    assert any("run_id" in e and "top-level" in e for e in errs)


def test_specialist_missing_required_field_fails():
    m = _valid_manifest()
    del m["specialists"][0]["status"]
    errs = validate(m)
    assert any("specialist[0]" in e and "status" in e for e in errs)


def test_invalid_status_fails():
    m = _valid_manifest()
    m["specialists"][0]["status"] = "PENDING"
    errs = validate(m)
    assert any("status 'PENDING'" in e for e in errs)


def test_dispatched_without_path_fails():
    """DISPATCHED must carry a non-empty path — otherwise the critic has nothing to Read."""
    m = _valid_manifest()
    m["specialists"][0]["path"] = None
    errs = validate(m)
    assert any("DISPATCHED requires a non-empty 'path'" in e for e in errs)


def test_dispatched_with_empty_path_fails():
    m = _valid_manifest()
    m["specialists"][0]["path"] = ""
    errs = validate(m)
    assert any("DISPATCHED requires a non-empty 'path'" in e for e in errs)


def test_deferred_with_null_path_passes():
    """DEFERRED entries may have path=null (no file expected)."""
    m = _valid_manifest()
    m["specialists"][1]["path"] = None
    assert validate(m) == []


def test_deferred_with_late_write_path_passes():
    """DEFERRED entries with a path represent late writes the critic must IGNORE
    per the manifest contract. The path is preserved for forensics but the
    critic filters by status=DISPATCHED, not by file existence."""
    m = _valid_manifest()
    m["specialists"][1] = {
        "name": "logic", "status": "DEFERRED", "reason": "timeout",
        "path": "/run/logic.json",  # late write — must be ignored by critic
    }
    assert validate(m) == []


def test_duplicate_specialist_name_fails():
    """Each specialist appears at most once — duplicates would let a DEFERRED
    entry shadow a DISPATCHED entry or vice versa."""
    m = _valid_manifest()
    m["specialists"].append({
        "name": "failure-modes", "status": "DEFERRED", "reason": "dup", "path": None,
    })
    errs = validate(m)
    assert any("duplicate name 'failure-modes'" in e for e in errs)


def test_non_dict_input_fails():
    assert validate("not a dict") == ["manifest object is not a dict"]


def test_missing_specialists_key_fails():
    errs = validate({"run_id": "r", "session_id": "s"})
    assert any("missing 'specialists' list" in e for e in errs)


# dispatched_paths() helper tests


def test_dispatched_paths_returns_only_dispatched_in_order():
    m = _valid_manifest()
    # Add a second DISPATCHED entry to test ordering
    m["specialists"].insert(0, {
        "name": "gate-reviewer", "status": "DISPATCHED", "path": "/run/gate-reviewer.json",
    })
    paths = dispatched_paths(m)
    assert paths == ["/run/gate-reviewer.json", "/run/failure-modes.json"]


def test_dispatched_paths_excludes_deferred_with_late_write():
    """The race-closing guarantee: a DEFERRED specialist whose file exists on
    disk (late write) is NOT returned by dispatched_paths()."""
    m = {
        "run_id": "r", "session_id": "s",
        "specialists": [
            {"name": "a", "status": "DISPATCHED", "path": "/run/a.json"},
            {"name": "b", "status": "DEFERRED", "reason": "timeout", "path": "/run/b.json"},
        ],
    }
    assert dispatched_paths(m) == ["/run/a.json"]


def test_dispatched_paths_empty_when_all_deferred():
    """FM-3 trigger: no DISPATCHED specialists means no work for the critic."""
    m = {
        "run_id": "r", "session_id": "s",
        "specialists": [
            {"name": "a", "status": "DEFERRED", "reason": "timeout", "path": None},
        ],
    }
    assert dispatched_paths(m) == []


def test_dispatched_paths_empty_for_invalid_manifest():
    """Helper is defensive — returns [] rather than raising on bad input."""
    assert dispatched_paths("not a dict") == []
    assert dispatched_paths({}) == []
    assert dispatched_paths({"specialists": "not a list"}) == []

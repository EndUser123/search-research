"""Tests for ``output_validator.py`` — packet and verifier-output validation.

Evidence classification: CONTRACT_MODEL_TESTED

Tests construct intentionally-broken packet dicts to confirm the validator
catches each error class, plus a known-good packet to confirm it accepts.
"""

import pytest

import output_validator as ov
import event_model as m
from output_validator import ValidationError


def _good_packet() -> dict:
    """Minimal structurally-valid packet dict."""
    return {
        "schema_version": m.PACKET_SCHEMA_VERSION,
        "producer": "check.preprocessor",
        "produced_at": "2026-07-18T00:00:00+00:00",
        "source": {
            "path": "x.jsonl",
            "status": "SOURCE_COMPLETE",
            "session_id": None,
            "line_count": 1,
            "has_timestamps": False,
        },
        "parse_stats": {
            "total_lines": 1,
            "parsed_events": 1,
            "skipped_blank": 0,
            "skipped_malformed": 0,
            "by_role": {"system": 1},
            "synthetic_user_messages": 0,
            "real_user_messages": 0,
            "tool_calls_total": 0,
            "tool_calls_with_parse_error": 0,
            "tool_results_orphaned": 0,
            "unknown_role_lines": 0,
            "has_timestamps": False,
            "warnings": [],
        },
        "signal_counts": {name: 0 for name in (
            "file_edits", "command_executions", "test_runs",
            "verification_tool_calls", "claim_verbs", "failures",
            "todo_state_changes", "scope_files", "subagent_spawns",
            "unverified_claim_candidates",
        )},
        "signals": {name: [] for name in (
            "file_edits", "command_executions", "test_runs",
            "verification_tool_calls", "claim_verbs", "failures",
            "todo_state_changes", "scope_files", "subagent_spawns",
            "unverified_claim_candidates",
        )},
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Packet validation — happy path
# ---------------------------------------------------------------------------


def test_good_packet_validates():
    errs = ov.validate_packet(_good_packet())
    assert errs.ok
    assert errs.errors == []


def test_assert_valid_packet_accepts_good():
    ov.assert_valid_packet(_good_packet())  # no raise


# ---------------------------------------------------------------------------
# Packet validation — structural failures
# ---------------------------------------------------------------------------


def test_missing_top_level_key_flagged():
    p = _good_packet()
    del p["produced_at"]
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("produced_at" in e or "missing" in e for e in errs.errors)


def test_unknown_schema_version_flagged():
    p = _good_packet()
    p["schema_version"] = "99.0"
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("unknown schema_version" in e for e in errs.errors)


def test_bad_source_status_flagged():
    p = _good_packet()
    p["source"]["status"] = "SOURCE_BOGUS"
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("source.status" in e for e in errs.errors)


def test_unreconciled_parse_stats_flagged():
    p = _good_packet()
    p["parse_stats"]["parsed_events"] = 5  # mismatch with total_lines=1
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("reconcile" in e for e in errs.errors)


def test_signal_count_mismatch_flagged():
    p = _good_packet()
    p["signal_counts"]["file_edits"] = 99
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("file_edits" in e and "!=" in e for e in errs.errors)


def test_signal_with_empty_event_indices_flagged():
    p = _good_packet()
    p["signals"]["file_edits"] = [
        {"kind": "file_edits", "event_indices": [], "summary": "x", "detail": {}, "confidence": "OBSERVED"}
    ]
    p["signal_counts"]["file_edits"] = 1
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("event_indices" in e and "non-empty" in e for e in errs.errors)


def test_signal_event_index_out_of_range_flagged():
    p = _good_packet()
    p["signals"]["file_edits"] = [
        {"kind": "file_edits", "event_indices": [99], "summary": "x", "detail": {}, "confidence": "OBSERVED"}
    ]
    p["signal_counts"]["file_edits"] = 1
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("out of range" in e for e in errs.errors)


def test_signal_kind_mismatch_with_bucket_flagged():
    p = _good_packet()
    p["signals"]["file_edits"] = [
        {"kind": "claim_verbs", "event_indices": [0], "summary": "x", "detail": {}, "confidence": "OBSERVED"}
    ]
    p["signal_counts"]["file_edits"] = 1
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any(".kind=" in e for e in errs.errors)


def test_signal_bad_confidence_flagged():
    p = _good_packet()
    p["signals"]["file_edits"] = [
        {"kind": "file_edits", "event_indices": [0], "summary": "x", "detail": {}, "confidence": "GUESS"}
    ]
    p["signal_counts"]["file_edits"] = 1
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("confidence" in e for e in errs.errors)


def test_missing_detector_bucket_flagged():
    p = _good_packet()
    del p["signals"]["subagent_spawns"]
    errs = ov.validate_packet(p)
    assert not errs.ok
    assert any("subagent_spawns" in e for e in errs.errors)


def test_assert_valid_packet_raises_with_all_errors():
    p = _good_packet()
    p["schema_version"] = "0.0"
    with pytest.raises(ValidationError) as exc_info:
        ov.assert_valid_packet(p)
    assert "schema_version" in str(exc_info.value)


def test_non_dict_packet_flagged():
    errs = ov.validate_packet(["not", "a", "dict"])  # type: ignore[arg-type]
    assert not errs.ok


# ---------------------------------------------------------------------------
# Verifier-output validation
# ---------------------------------------------------------------------------


def test_verifier_pass_with_no_issues_ok():
    errs = ov.validate_verifier_output({"verdict": "PASS", "issues": []})
    assert errs.ok


def test_verifier_fail_with_no_issues_rejected():
    errs = ov.validate_verifier_output({"verdict": "FAIL", "issues": []})
    assert not errs.ok
    assert any("FAIL" in e and "zero" in e for e in errs.errors)


def test_verifier_pass_with_bug_issue_rejected():
    errs = ov.validate_verifier_output({
        "verdict": "PASS",
        "issues": [{"severity": "bug", "description": "x", "evidence": "y", "suggestion": "z"}],
    })
    assert not errs.ok
    assert any("contradicts PASS" in e for e in errs.errors)


def test_verifier_pass_with_suggestion_warns_but_ok():
    errs = ov.validate_verifier_output({
        "verdict": "PASS",
        "issues": [{"severity": "suggestion", "description": "x", "evidence": "y", "suggestion": "z"}],
    })
    assert errs.ok
    assert len(errs.warnings) >= 1


def test_verifier_bad_verdict_rejected():
    errs = ov.validate_verifier_output({"verdict": "MAYBE", "issues": []})
    assert not errs.ok


def test_verifier_bad_severity_rejected():
    errs = ov.validate_verifier_output({
        "verdict": "FAIL",
        "issues": [{"severity": "critical", "description": "x", "evidence": "y", "suggestion": "z"}],
    })
    assert not errs.ok
    assert any("severity" in e for e in errs.errors)


def test_verifier_issue_missing_field_rejected():
    errs = ov.validate_verifier_output({
        "verdict": "FAIL",
        "issues": [{"severity": "bug", "description": "x"}],  # missing evidence, suggestion
    })
    assert not errs.ok
    assert any("missing" in e for e in errs.errors)


def test_verifier_fail_with_complete_issue_ok():
    errs = ov.validate_verifier_output({
        "verdict": "FAIL",
        "issues": [{"severity": "bug", "description": "x", "evidence": "y", "suggestion": "z"}],
    })
    assert errs.ok

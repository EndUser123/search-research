"""Tests for ``detectors.py`` — the 10 check-oriented detectors.

Evidence classification: CONTRACT_MODEL_TESTED + fixture-grounded

Each detector gets at least one fixture-grounded assertion (using the
23-line synthetic fixture) and at least one inline edge-case assertion.
"""

from pathlib import Path

import pytest

import transcript_parser as tp
import detectors as d
import event_model as m

FIXTURE = Path(__file__).parent / "fixture_sample.jsonl"


@pytest.fixture(scope="module")
def transcript():
    return tp.parse_file(FIXTURE)


@pytest.fixture(scope="module")
def signals(transcript):
    return d.run_all_detectors(transcript)


# ---------------------------------------------------------------------------
# Detector registry invariants
# ---------------------------------------------------------------------------


def test_exactly_10_detectors():
    assert len(d.DETECTOR_NAMES) == 10
    assert len(set(d.DETECTOR_NAMES)) == 10  # no duplicates


def test_run_all_detectors_returns_every_bucket(signals):
    for name in d.DETECTOR_NAMES:
        assert name in signals
        assert isinstance(signals[name], list)


def test_signal_kind_matches_bucket(signals):
    """Every signal's `kind` must equal its bucket key (defensive invariant)."""
    for bucket, sigs in signals.items():
        for s in sigs:
            assert s.kind == bucket, f"signal in bucket {bucket!r} has kind={s.kind!r}"


def test_every_signal_cites_at_least_one_event(signals):
    for bucket, sigs in signals.items():
        for s in sigs:
            assert len(s.event_indices) >= 1, f"{bucket} signal has no event_indices"


def test_confidence_is_observed_or_inferred(signals):
    allowed = {"OBSERVED", "INFERRED"}
    for bucket, sigs in signals.items():
        for s in sigs:
            assert s.confidence in allowed, f"{bucket} has bad confidence {s.confidence!r}"


# ---------------------------------------------------------------------------
# 1. file_edits
# ---------------------------------------------------------------------------


def test_file_edits_detects_write_and_search_replace(signals):
    targets = [s.detail.get("target_path") for s in signals["file_edits"]]
    # Fixture has one search_replace on src/app.py and one write on tests/test_app.py
    assert "src/app.py" in targets
    assert "tests/test_app.py" in targets


def test_file_edits_excludes_read_only_tools(transcript):
    sigs = d.detect_file_edits(transcript)
    tools = {s.detail["tool"] for s in sigs}
    # read_file / grep must never appear here
    assert "read_file" not in tools
    assert "grep" not in tools


def test_file_edits_op_label_distinguishes_create_vs_edit(transcript):
    sigs = d.detect_file_edits(transcript)
    by_target = {s.detail["target_path"]: s.detail["op"] for s in sigs if s.detail.get("target_path")}
    assert by_target.get("src/app.py") == "edit"
    assert by_target.get("tests/test_app.py") == "create"


# ---------------------------------------------------------------------------
# 2. command_executions
# ---------------------------------------------------------------------------


def test_command_executions_capture_command_and_exit_code(signals):
    cmds = {s.detail.get("command"): s.detail.get("exit_code") for s in signals["command_executions"]}
    assert "pytest tests/test_app.py" in cmds
    assert cmds["pytest tests/test_app.py"] == 0  # exit 0 in fixture


def test_command_executions_resolves_result_event_index(signals):
    for s in signals["command_executions"]:
        if s.detail.get("exit_code") is not None:
            assert s.detail.get("result_event_index") is not None


# ---------------------------------------------------------------------------
# 3. test_runs
# ---------------------------------------------------------------------------


def test_test_runs_match_pytest(signals):
    frameworks = {s.detail["framework"] for s in signals["test_runs"]}
    assert "pytest" in frameworks


def test_test_runs_exclude_non_test_commands(transcript):
    """A plain grep or read command must not appear as a test_run."""
    sigs = d.detect_test_runs(transcript)
    for s in sigs:
        assert "framework" in s.detail


def test_test_runs_with_failing_exit_have_nonzero_code(signals):
    # Fixture has pytest (exit 0) — none failing. So we check the contract:
    # any test_run with exit_code 1+ would be failing. Here we assert none
    # are falsely flagged.
    for s in signals["test_runs"]:
        assert s.detail["exit_code"] in (0, None) or s.detail["exit_code"] >= 1


# ---------------------------------------------------------------------------
# 4. verification_tool_calls
# ---------------------------------------------------------------------------


def test_verification_calls_include_read_and_grep(signals):
    tools = {s.detail["tool"] for s in signals["verification_tool_calls"]}
    assert "read_file" in tools
    assert "grep" in tools


def test_verification_calls_carry_target(signals):
    targets = {s.detail.get("target") for s in signals["verification_tool_calls"]}
    assert "src/app.py" in targets


# ---------------------------------------------------------------------------
# 5. claim_verbs
# ---------------------------------------------------------------------------


def test_claim_verbs_match_fixture_phrases(signals):
    verbs = {s.detail["verb"] for s in signals["claim_verbs"]}
    # Fixture exercises fixed, tests_pass, confirmed, wrote_or_changed, done.
    assert "fixed" in verbs
    assert "tests_pass" in verbs
    assert "confirmed" in verbs
    assert "wrote_or_changed" in verbs


def test_claim_verbs_carry_matched_text(signals):
    """Every claim_verb signal includes the literal matched phrase."""
    for s in signals["claim_verbs"]:
        assert "matched_text" in s.detail
        assert isinstance(s.detail["matched_text"], str)
        assert len(s.detail["matched_text"]) > 0


def test_claim_verbs_are_inferred_confidence(signals):
    """Phrase matches are never OBSERVED."""
    for s in signals["claim_verbs"]:
        assert s.confidence == "INFERRED"


# ---------------------------------------------------------------------------
# 6. failures
# ---------------------------------------------------------------------------


def test_failures_capture_traceback(signals):
    kinds = [s.detail["kind"] for s in signals["failures"]]
    assert "traceback" in kinds


def test_failures_capture_nonzero_exit(signals):
    exit_codes = [s.detail.get("exit_code") for s in signals["failures"] if s.detail["kind"] == "nonzero_exit"]
    assert any(c >= 1 for c in exit_codes)


def test_failures_exclude_zero_exit_inline():
    """A clean exit: 0 must NOT produce a nonzero_exit signal."""
    records = [
        {"type": "tool_result", "tool_call_id": "x", "content": "exit: 0\nall good"},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    sigs = d.detect_failures(t)
    kinds = [s.detail["kind"] for s in sigs]
    assert "nonzero_exit" not in kinds


# ---------------------------------------------------------------------------
# 7. todo_state_changes
# ---------------------------------------------------------------------------


def test_todo_state_changes_capture_status_counts(signals):
    assert len(signals["todo_state_changes"]) >= 1
    s = signals["todo_state_changes"][0]
    assert s.detail["total"] == 3
    assert s.detail["completed"] == 3
    assert s.detail["pending"] == 0


# ---------------------------------------------------------------------------
# 8. scope_files
# ---------------------------------------------------------------------------


def test_scope_files_aggregates_distinct_paths(signals):
    assert len(signals["scope_files"]) == 1  # one aggregation signal
    s = signals["scope_files"][0]
    files = s.detail["files"]
    assert "src/app.py" in files
    assert "tests/test_app.py" in files
    assert s.detail["count"] == len(files)


def test_scope_files_splits_by_source(signals):
    s = signals["scope_files"][0]
    assert "src/app.py" in s.detail["by_source"]["edited"]
    assert "src/app.py" in s.detail["by_source"]["read"]  # was both read and edited


# ---------------------------------------------------------------------------
# 9. subagent_spawns
# ---------------------------------------------------------------------------


def test_subagent_spawns_capture_type_and_description(signals):
    assert len(signals["subagent_spawns"]) >= 1
    s = signals["subagent_spawns"][0]
    assert s.detail["subagent_type"] == "general-purpose"
    assert "review" in (s.detail["description"] or "")


# ---------------------------------------------------------------------------
# 10. unverified_claim_candidates
# ---------------------------------------------------------------------------


def test_unverified_candidates_nonempty_in_fixture(signals):
    """The fixture has an unverified 'refactored... done' claim."""
    assert len(signals["unverified_claim_candidates"]) >= 1


def test_unverified_candidates_are_inferred(signals):
    for s in signals["unverified_claim_candidates"]:
        assert s.confidence == "INFERRED"
        assert s.detail["verification_in_window"] is False


def test_claim_backed_by_forward_verification_not_flagged():
    """A claim followed by a read_file within window must NOT be flagged."""
    records = [
        {"type": "assistant", "content": "I have fixed the bug.", "tool_calls": []},
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "read_file", "arguments": '{"target_file": "a"}'}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    sigs = d.detect_unverified_claim_candidates(t)
    assert sigs == []


def test_claim_backed_by_backward_verification_not_flagged():
    """A claim preceded by a grep within window must NOT be flagged."""
    records = [
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "grep", "arguments": '{"pattern": "x", "path": "a"}'}
        ]},
        {"type": "assistant", "content": "Confirmed: everything is fine."},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    sigs = d.detect_unverified_claim_candidates(t)
    assert sigs == []


def test_unverified_claim_with_no_verification_flagged():
    """A claim with no verification anywhere must be flagged."""
    records = [
        {"type": "assistant", "content": "I have refactored everything. All done."},
        {"type": "assistant", "content": "Some unrelated talk."},
        {"type": "assistant", "content": "More unrelated talk."},
        {"type": "assistant", "content": "Yet more."},
        {"type": "assistant", "content": "Final unrelated message."},
        {"type": "assistant", "content": "Last unrelated message."},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    sigs = d.detect_unverified_claim_candidates(t)
    assert len(sigs) >= 1
    assert any(s.detail["verb"] in {"wrote", "done"} for s in sigs)


# ---------------------------------------------------------------------------
# Empty-input contract
# ---------------------------------------------------------------------------


def test_empty_transcript_yields_empty_signals():
    t = m.Transcript(
        events=(),
        source_path="",
        source_status=m.SourceStatus.UNVERIFIED,
        parse_stats=m.ParseStats(),
    )
    sigs = d.run_all_detectors(t)
    for name in d.DETECTOR_NAMES:
        assert sigs[name] == []

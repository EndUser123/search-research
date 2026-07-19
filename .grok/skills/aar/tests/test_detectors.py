"""Tests for the deterministic signal detectors.

Evidence classification: CONTRACT_MODEL_TESTED

Each detector gets a positive test (the pattern is present → signal fires)
and a negative test (the pattern is absent → no signal). Every signal must
carry a non-empty falsifier (the anti-overclaim contract).

Fixtures are real ``Event`` tuples built inline (anti-mock: no mocking of
the parser; the detector runs on its real input type).
"""

from __future__ import annotations

import pytest

from detectors import (
    ALL_DETECTORS,
    Signal,
    SignalKind,
    SignalSeverity,
    detect_assistant_self_corrections,
    detect_empty_tool_results,
    detect_file_edit_reversals,
    detect_long_tool_chains,
    detect_orphaned_tool_results,
    detect_repeated_file_edits,
    detect_repeated_identical_tool_calls,
    detect_repeated_tool_name_windows,
    detect_tool_arg_parse_failures,
    detect_tool_result_errors,
    detect_unanswered_user_questions,
    detect_unexpected_role_order,
    detect_user_corrections,
    run_all_detectors,
)
from event_model import Event, Role, ToolCall

FIXTURE_SAMPLE = True  # placeholder — module-level marker for readers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assistant(
    index: int,
    text: str | None = "",
    tool_calls: tuple[ToolCall, ...] = (),
) -> Event:
    return Event(index=index, role=Role.ASSISTANT, text=text, tool_calls=tool_calls)


def _tc(name: str, arguments: dict, call_id: str = "c1", raw: str | None = None) -> ToolCall:
    return ToolCall(
        id=call_id,
        name=name,
        arguments=arguments,
        arguments_raw=raw if raw is not None else "irrelevant",
    )


def _user(index: int, text: str, synthetic: bool = False) -> Event:
    return Event(
        index=index,
        role=Role.USER,
        text=text,
        synthetic_reason="compaction_meta" if synthetic else None,
    )


def _tool_result(index: int, text: str | None, call_id: str = "c1") -> Event:
    return Event(index=index, role=Role.TOOL_RESULT, text=text, tool_call_id=call_id)


def _assert_falsifier_present(sig: Signal) -> None:
    assert sig.falsifier and sig.falsifier.strip(), (
        f"signal {sig.kind.value!r} missing falsifier (anti-overclaim violation)"
    )


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------


def test_all_detectors_are_callables():
    for det in ALL_DETECTORS:
        assert callable(det)


def test_run_all_detectors_returns_signals_with_falsifiers():
    """Every emitted signal must carry a non-empty falsifier."""
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "a.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("write", {"file_path": "a.py"}, "c2"),)),
        _assistant(2, tool_calls=(_tc("write", {"file_path": "a.py"}, "c3"),)),
    ]
    sigs = run_all_detectors(events)
    assert len(sigs) > 0
    for s in sigs:
        _assert_falsifier_present(s)


def test_run_all_detectors_is_deterministic():
    events = [_assistant(0, tool_calls=(_tc("read_file", {"target_file": "x"}, "c1"),))]
    a = run_all_detectors(events)
    b = run_all_detectors(events)
    assert [(s.kind, s.event_indices, s.detail) for s in a] == [
        (s.kind, s.event_indices, s.detail) for s in b
    ]


# ---------------------------------------------------------------------------
# detect_repeated_identical_tool_calls
# ---------------------------------------------------------------------------


def test_repeated_identical_tool_calls_fires():
    events = [
        _assistant(0, tool_calls=(_tc("run_terminal_command", {"command": "pytest"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("run_terminal_command", {"command": "pytest"}, "c2"),)),
    ]
    sigs = detect_repeated_identical_tool_calls(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.REPEATED_IDENTICAL_TOOL_CALL
    assert set(sigs[0].event_indices) == {0, 1}
    _assert_falsifier_present(sigs[0])


def test_repeated_identical_tool_calls_different_args_no_fire():
    events = [
        _assistant(0, tool_calls=(_tc("run_terminal_command", {"command": "pytest a"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("run_terminal_command", {"command": "pytest b"}, "c2"),)),
    ]
    assert detect_repeated_identical_tool_calls(events) == []


# ---------------------------------------------------------------------------
# detect_repeated_tool_name_windows
# ---------------------------------------------------------------------------


def test_repeated_tool_name_window_fires_for_mutating_tools():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "a.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("write", {"file_path": "b.py"}, "c2"),)),
        _assistant(2, tool_calls=(_tc("write", {"file_path": "c.py"}, "c3"),)),
    ]
    sigs = detect_repeated_tool_name_windows(events)
    assert len(sigs) >= 1
    assert sigs[0].kind is SignalKind.REPEATED_TOOL_NAME_WINDOW


def test_repeated_tool_name_window_does_not_fire_for_read_tools():
    """read-only tools repeating is normal exploratory behaviour."""
    events = [
        _assistant(0, tool_calls=(_tc("read_file", {"target_file": "a.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("read_file", {"target_file": "b.py"}, "c2"),)),
        _assistant(2, tool_calls=(_tc("read_file", {"target_file": "c.py"}, "c3"),)),
    ]
    assert detect_repeated_tool_name_windows(events) == []


# ---------------------------------------------------------------------------
# detect_tool_result_errors
# ---------------------------------------------------------------------------


def test_tool_result_error_fires_on_explicit_marker():
    events = [_tool_result(0, "Error: something failed\nTraceback (most recent call last):")]
    sigs = detect_tool_result_errors(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.TOOL_RESULT_ERROR


def test_tool_result_error_fires_on_nonzero_exit_code():
    events = [_tool_result(0, "Exit Code: 1\nsome output")]
    sigs = detect_tool_result_errors(events)
    assert len(sigs) == 1


def test_tool_result_error_does_not_fire_on_discussion_of_failure():
    """Bare 'fail' in test output must not match (discussion-of-failure)."""
    events = [_tool_result(0, "This test should fail fast. The failure mode is documented.")]
    assert detect_tool_result_errors(events) == []


# ---------------------------------------------------------------------------
# detect_empty_tool_results
# ---------------------------------------------------------------------------


def test_empty_tool_result_fires():
    events = [_tool_result(0, ""), _tool_result(1, "   "), _tool_result(2, None)]
    sigs = detect_empty_tool_results(events)
    assert len(sigs) == 3


def test_nonempty_tool_result_does_not_fire():
    events = [_tool_result(0, "real output")]
    assert detect_empty_tool_results(events) == []


# ---------------------------------------------------------------------------
# detect_repeated_file_edits
# ---------------------------------------------------------------------------


def test_repeated_file_edit_fires_at_three_writes_same_turn():
    """Three writes to the same path in ONE turn is genuine thrashing."""
    events = [
        _assistant(
            0,
            tool_calls=(
                _tc("write", {"file_path": "a.py"}, "c1"),
                _tc("write", {"file_path": "a.py"}, "c2"),
                _tc("write", {"file_path": "a.py"}, "c3"),
            ),
        )
    ]
    sigs = detect_repeated_file_edits(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.REPEATED_FILE_EDIT


def test_repeated_file_edit_does_not_fire_at_two_writes():
    """Two writes is allowed (legitimate write-then-small-fix)."""
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "a.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("write", {"file_path": "a.py"}, "c2"),)),
    ]
    assert detect_repeated_file_edits(events) == []


def test_repeated_file_edit_recognises_target_file_key():
    """Different tools use different arg keys (file_path, target_file, path)."""
    events = [
        _assistant(0, tool_calls=(_tc("edit", {"target_file": "b.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("edit", {"target_file": "b.py"}, "c2"),)),
        _assistant(2, tool_calls=(_tc("edit", {"target_file": "b.py"}, "c3"),)),
    ]
    sigs = detect_repeated_file_edits(events)
    assert len(sigs) == 1


# ---------------------------------------------------------------------------
# detect_file_edit_reversals
# ---------------------------------------------------------------------------


def test_file_edit_reversal_fires_on_explicit_path_match():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "src/feature.py"}, "c1"),)),
        _assistant(
            1,
            tool_calls=(
                _tc("run_terminal_command", {"command": "git checkout -- src/feature.py"}, "c2"),
            ),
        ),
    ]
    sigs = detect_file_edit_reversals(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.FILE_EDIT_REVERSAL
    assert sigs[0].severity is SignalSeverity.HIGH


def test_file_edit_reversal_does_not_fire_on_different_file():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "src/feature.py"}, "c1"),)),
        _assistant(
            1,
            tool_calls=(
                _tc("run_terminal_command", {"command": "git checkout -- src/other.py"}, "c2"),
            ),
        ),
    ]
    assert detect_file_edit_reversals(events) == []


def test_file_edit_reversal_does_not_fire_on_non_git_command():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "src/feature.py"}, "c1"),)),
        _assistant(
            1,
            tool_calls=(_tc("run_terminal_command", {"command": "ls src/feature.py"}, "c2"),),
        ),
    ]
    assert detect_file_edit_reversals(events) == []


def test_file_edit_reversal_consolidates_per_path():
    """Multiple reverts of the same path produce one signal, not N."""
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "src/x.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("run_terminal_command", {"command": "git checkout -- src/x.py"}, "c2"),)),
        _assistant(2, tool_calls=(_tc("run_terminal_command", {"command": "git checkout -- src/x.py"}, "c3"),)),
    ]
    sigs = detect_file_edit_reversals(events)
    assert len(sigs) == 1


# ---------------------------------------------------------------------------
# detect_assistant_self_corrections
# ---------------------------------------------------------------------------


def test_assistant_self_correction_fires():
    events = [_assistant(0, "Wait, actually, let me reconsider. I was wrong.")]
    sigs = detect_assistant_self_corrections(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.ASSISTANT_SELF_CORRECTION


def test_assistant_self_correction_does_not_fire_on_normal_text():
    events = [_assistant(0, "The test passed. Moving on.")]
    assert detect_assistant_self_corrections(events) == []


# ---------------------------------------------------------------------------
# detect_user_corrections
# ---------------------------------------------------------------------------


def test_user_correction_fires_after_assistant():
    events = [_assistant(0, "Done."), _user(1, "No, that's wrong. Revert it.")]
    sigs = detect_user_corrections(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.USER_CORRECTION
    assert sigs[0].severity is SignalSeverity.HIGH


def test_synthetic_user_message_does_not_fire_correction():
    """Harness-injected messages (compaction_meta) are not user corrections."""
    events = [_assistant(0, "Done."), _user(1, "No, stop", synthetic=True)]
    assert detect_user_corrections(events) == []


def test_user_correction_before_any_assistant_does_not_fire():
    events = [_user(0, "No, that's wrong")]
    assert detect_user_corrections(events) == []


# ---------------------------------------------------------------------------
# detect_unanswered_user_questions
# ---------------------------------------------------------------------------


def test_unanswered_user_question_fires():
    events = [_user(0, "What does this do?"), _user(1, "Never mind, next thing.")]
    sigs = detect_unanswered_user_questions(events)
    assert len(sigs) == 1
    assert sigs[0].event_indices == (0,)


def test_answered_user_question_does_not_fire():
    events = [_user(0, "What does this do?"), _assistant(1, "It parses JSON.")]
    assert detect_unanswered_user_questions(events) == []


def test_rhetorical_question_marked_unanswered_still_flags():
    """Conservative: a '?' with no answer is flagged even if rhetorical.

    The LLM decides whether it was rhetorical; the detector only reports the
    mechanical pattern.
    """
    events = [_user(0, "Is this right?")]
    sigs = detect_unanswered_user_questions(events)
    assert len(sigs) == 1
    _assert_falsifier_present(sigs[0])


# ---------------------------------------------------------------------------
# detect_long_tool_chains
# ---------------------------------------------------------------------------


def test_long_tool_chain_fires_at_eight():
    calls = tuple(_tc("write", {"file_path": f"f{i}.py"}, f"c{i}") for i in range(8))
    events = [_assistant(0, tool_calls=calls)]
    sigs = detect_long_tool_chains(events)
    assert len(sigs) == 1
    assert sigs[0].severity is SignalSeverity.INFO


def test_long_tool_chain_does_not_fire_below_threshold():
    calls = tuple(_tc("write", {"file_path": f"f{i}.py"}, f"c{i}") for i in range(7))
    events = [_assistant(0, tool_calls=calls)]
    assert detect_long_tool_chains(events) == []


# ---------------------------------------------------------------------------
# detect_unexpected_role_order & detect_orphaned_tool_results
# ---------------------------------------------------------------------------


def test_unexpected_role_order_fires_on_orphaned_tool_result():
    events = [_tool_result(0, "x", call_id="nonexistent")]
    sigs = detect_unexpected_role_order(events)
    assert any(s.kind is SignalKind.UNEXPECTED_ROLE_ORDER for s in sigs)


def test_orphaned_tool_result_downgraded_when_source_lacks_tool_calls():
    """When no assistant event has tool_calls (e.g. Markdown-converted),
    orphan signals are LOW, not HIGH — the linkage is unknowable."""
    events = [_tool_result(0, "x", call_id="nonexistent")]
    sigs = detect_orphaned_tool_results(events)
    assert len(sigs) == 1
    assert sigs[0].severity is SignalSeverity.LOW
    assert "linkage unavailable" in sigs[0].detail


def test_orphaned_tool_result_high_when_tool_calls_exist_but_result_orphaned():
    """When tool_calls DO exist (proving the format supports linkage),
    a genuinely orphaned result is HIGH."""
    events = [
        _assistant(0, tool_calls=(_tc("read_file", {"target_file": "x"}, "c1"),)),
        _tool_result(1, "x", call_id="nonexistent"),  # no matching call
    ]
    sigs = detect_orphaned_tool_results(events)
    assert len(sigs) == 1
    assert sigs[0].severity is SignalSeverity.HIGH


def test_orphaned_tool_result_does_not_fire_when_call_exists():
    events = [
        _assistant(0, tool_calls=(_tc("read_file", {"target_file": "x"}, "c1"),)),
        _tool_result(1, "x", call_id="c1"),
    ]
    assert detect_orphaned_tool_results(events) == []


def test_orphaned_tool_result_mixed_source_only_observable_linkage_supports_high():
    """Mixed-source transcript: SOME tool_calls exist (linkage IS available
    in the source representation), so the unmatched results are genuine
    orphans and earn HIGH — but matched results still produce nothing.
    Required source-fidelity case: only observable linkage supports HIGH."""
    events = [
        # one matched pair: linkage proven, no signal
        _assistant(0, tool_calls=(_tc("read_file", {"target_file": "a"}, "c1"),)),
        _tool_result(1, "a", call_id="c1"),
        # one orphan: linkage available (c2 absent while other calls exist),
        # so this is a structurally-proven orphan → HIGH
        _assistant(2, tool_calls=(_tc("read_file", {"target_file": "b"}, "c3"),)),
        _tool_result(3, "b", call_id="c2-missing"),
        _tool_result(4, "b", call_id="c3"),  # matched, no signal
    ]
    sigs = detect_orphaned_tool_results(events)
    orphan_sigs = [s for s in sigs if s.severity is SignalSeverity.HIGH]
    assert len(orphan_sigs) == 1
    assert orphan_sigs[0].event_indices == (3,)
    # Detail must NOT mention "linkage unavailable" — linkage WAS available
    assert "linkage unavailable" not in orphan_sigs[0].detail.lower()


def test_orphaned_tool_result_detail_falsifier_distinguish_linkage_modes():
    """Required source-fidelity case: detail and falsifier must explicitly
    distinguish 'linkage unavailable' (LOW branch) from 'orphan proven'
    (HIGH branch). The two branches carry distinct vocabulary so a downstream
    consumer cannot mistake representation-artifact for structural-failure."""
    # LOW branch — linkage unavailable
    low_events = [_tool_result(0, "x", call_id="any")]
    low_sigs = detect_orphaned_tool_results(low_events)
    assert len(low_sigs) == 1 and low_sigs[0].severity is SignalSeverity.LOW
    assert "linkage unavailable" in low_sigs[0].detail
    assert "lost in conversion" in low_sigs[0].falsifier or \
           "does not preserve" in low_sigs[0].falsifier

    # HIGH branch — orphan proven (linkage available)
    high_events = [
        _assistant(0, tool_calls=(_tc("read_file", {"target_file": "y"}, "present"),)),
        _tool_result(1, "y", call_id="absent"),
    ]
    high_sigs = detect_orphaned_tool_results(high_events)
    assert len(high_sigs) == 1 and high_sigs[0].severity is SignalSeverity.HIGH
    assert "no producing tool_call" in high_sigs[0].detail
    assert "linkage unavailable" not in high_sigs[0].detail.lower()
    # HIGH falsifier must point to a real structural explanation
    # (compaction / excluded event), not to a representation artifact
    assert "compacted" in high_sigs[0].falsifier or \
           "excluded" in high_sigs[0].falsifier


# ---------------------------------------------------------------------------
# detect_tool_arg_parse_failures
# ---------------------------------------------------------------------------


def test_tool_arg_parse_failure_fires():
    events = [
        _assistant(
            0,
            tool_calls=(
                ToolCall(id="c1", name="bad", arguments={}, arguments_raw="{bad", parse_error="arg parse failed"),
            ),
        )
    ]
    sigs = detect_tool_arg_parse_failures(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.TOOL_ARG_PARSE_FAILURE


def test_tool_arg_parse_failure_no_fire_on_clean_call():
    events = [_assistant(0, tool_calls=(_tc("write", {"file_path": "x"}, "c1"),))]
    assert detect_tool_arg_parse_failures(events) == []

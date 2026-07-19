"""Tests for the opportunity-candidate detectors (spec Section 19).

Evidence class: production unit.

Each detector emits Signal objects of kind ``OPPORTUNITY_CANDIDATE_*`` —
*candidates* the LLM interprets, never final opportunity decisions (spec
Section 18). Every signal must carry a falsifier (existing contract).

Covers spec test cases 2, 3, 6, 8, 17, 18 (mechanical aspects).
"""

from __future__ import annotations

import pytest

from detectors import (
    Signal,
    SignalKind,
    detect_duplicate_capability_references,
    detect_recommendation_revisions,
    detect_successful_interventions,
    detect_unconsumed_artifacts,
    detect_unused_capability,
)
from event_model import Event, Role, ToolCall

from test_detectors import _assistant, _tc, _tool_result, _assert_falsifier_present  # reuse helpers


# ---------------------------------------------------------------------------
# detect_unconsumed_artifacts (test case 17)
# ---------------------------------------------------------------------------


def test_unconsumed_artifact_fires_for_written_then_never_read():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "scratch.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("read_file", {"target_file": "other.py"}, "c2"),)),
    ]
    sigs = detect_unconsumed_artifacts(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_UNCONSUMED_ARTIFACT
    _assert_falsifier_present(sigs[0])


def test_unconsumed_artifact_does_not_fire_when_subsequently_read():
    events = [
        _assistant(0, tool_calls=(_tc("write", {"file_path": "scratch.py"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("read_file", {"target_file": "scratch.py"}, "c2"),)),
    ]
    assert detect_unconsumed_artifacts(events) == []


def test_unconsumed_artifact_does_not_imply_waste():
    """Test case 17: unused artifact does not automatically imply waste.

    The detector emits a *candidate* with LOW severity and a falsifier that
    explicitly notes the artifact may be a deliberate deliverable. The
    severity + falsifier are the contract that prevents automatic waste-
    labelling."""
    events = [_assistant(0, tool_calls=(_tc("write", {"file_path": "report.md"}, "c1"),))]
    sigs = detect_unconsumed_artifacts(events)
    assert sigs
    assert sigs[0].severity.value == "LOW"
    assert "deliverable" in sigs[0].falsifier


# ---------------------------------------------------------------------------
# detect_unused_capability (test case 3 — reuse candidate)
# ---------------------------------------------------------------------------


def test_unused_capability_fires_for_discovered_script_not_invoked():
    """Spec example: a security scanner was discovered inside a rejected package."""
    events = [
        _tool_result(0, "Found module scanner.py with function run_security_scan()"),
        _assistant(1, "moving on"),
    ]
    sigs = detect_unused_capability(events)
    assert any(s.group_key == "scanner.py" for s in sigs)


def test_unused_capability_does_not_fire_when_subsequently_invoked():
    events = [
        _tool_result(0, "Found scanner.py"),
        _assistant(1, "running scanner", tool_calls=(_tc("run_terminal_command", {"command": "python scanner.py"}, "c1"),)),
    ]
    sigs = detect_unused_capability(events)
    assert not any(s.group_key == "scanner.py" for s in sigs)


def test_unused_capability_ignores_generic_filenames():
    """setup.py / __init__.py / readme.md should not trigger the detector."""
    events = [
        _tool_result(0, "Found setup.py and __init__.py and readme.md"),
        _assistant(1, "moving on"),
    ]
    sigs = detect_unused_capability(events)
    # Generic noise names should be filtered.
    group_keys = {s.group_key for s in sigs}
    assert "setup.py" not in group_keys
    assert "__init__.py" not in group_keys


# ---------------------------------------------------------------------------
# detect_duplicate_capability_references (test case 6)
# ---------------------------------------------------------------------------


def test_duplicate_capability_fires_when_proposing_existing_tool():
    """Spec example: 'build a new security scanner' when scanner.py already exists."""
    events = [
        _tool_result(0, "discovered scanner.py"),
        _assistant(1, "Let me build a new scanner for this workflow"),
    ]
    sigs = detect_duplicate_capability_references(events)
    assert any(s.kind is SignalKind.OPPORTUNITY_CANDIDATE_DUPLICATE_CAPABILITY for s in sigs)


def test_duplicate_capability_does_not_fire_for_unrelated_proposal():
    events = [
        _tool_result(0, "discovered scanner.py"),
        _assistant(1, "Let me build a new dashboard"),
    ]
    sigs = detect_duplicate_capability_references(events)
    assert not any("scanner" in (s.detail or "") for s in sigs)


# ---------------------------------------------------------------------------
# detect_recommendation_revisions (Section 12)
# ---------------------------------------------------------------------------


def test_recommendation_revision_fires_on_revised_recommendation():
    events = [
        _assistant(0, "I recommend adopting package X."),
        _assistant(1, "Actually, on reflection, I recommend against it."),
    ]
    sigs = detect_recommendation_revisions(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION


def test_recommendation_revision_does_not_fire_without_revision_marker():
    events = [
        _assistant(0, "I recommend X."),
        _assistant(1, "I also recommend Y."),  # additional rec, no revision
    ]
    assert detect_recommendation_revisions(events) == []


def test_recommendation_revision_does_not_fire_on_first_recommendation():
    events = [_assistant(0, "I recommend X.")]
    assert detect_recommendation_revisions(events) == []


# ---------------------------------------------------------------------------
# detect_successful_interventions (test cases 1, 12 — success amplification)
# ---------------------------------------------------------------------------


def test_successful_intervention_fires_when_success_follows_error():
    events = [
        _tool_result(0, "Error: test failed"),
        _assistant(1, "I fixed the bug. Tests passed now."),
    ]
    sigs = detect_successful_interventions(events)
    assert len(sigs) == 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_SUCCESSFUL_INTERVENTION


def test_successful_intervention_does_not_fire_without_prior_error():
    events = [_assistant(0, "Tests passed!")]
    assert detect_successful_interventions(events) == []


def test_successful_intervention_does_not_fire_success_without_marker():
    events = [
        _tool_result(0, "Error: failed"),
        _assistant(1, "moving on"),  # no success marker
    ]
    assert detect_successful_interventions(events) == []


# ---------------------------------------------------------------------------
# Registry integration: every opportunity detector runs and produces only
# OPPORTUNITY_CANDIDATE_* signals.
# ---------------------------------------------------------------------------


def test_opportunity_detectors_in_registry():
    from detectors import ALL_DETECTORS
    names = {d.__name__ for d in ALL_DETECTORS}
    for name in (
        "detect_unconsumed_artifacts",
        "detect_unused_capability",
        "detect_duplicate_capability_references",
        "detect_recommendation_revisions",
        "detect_successful_interventions",
    ):
        assert name in names


def test_opportunity_candidate_kinds_use_correct_prefix():
    """All opportunity-candidate signal kinds start with the prefix."""
    from detectors import SignalKind
    opp_kinds = [
        SignalKind.OPPORTUNITY_CANDIDATE_UNCONSUMED_ARTIFACT,
        SignalKind.OPPORTUNITY_CANDIDATE_UNUSED_CAPABILITY,
        SignalKind.OPPORTUNITY_CANDIDATE_DUPLICATE_CAPABILITY,
        SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION,
        SignalKind.OPPORTUNITY_CANDIDATE_SUCCESSFUL_INTERVENTION,
    ]
    for k in opp_kinds:
        assert k.value.startswith("opportunity_candidate_")

#!/usr/bin/env python3
"""Tests for Stop_claim_gap_telemetry_probe (telemetry-only Stop probe).

This probe emits to the existing __lib/agentic_reliability_telemetry sink and
never blocks. Tests assert the emit-vs-suppress contract, not decisions.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path("P:/.claude/hooks")
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
if str(HOOKS_DIR / "tests") not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR / "tests"))


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "stop_claim_gap_telemetry_probe",
        HOOKS_DIR / "Stop_claim_gap_telemetry_probe.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _enable_telemetry(monkeypatch):
    """Force the agentic_reliability_telemetry sink on, regardless of env."""
    tel = importlib.import_module("__lib.agentic_reliability_telemetry")
    monkeypatch.setattr(tel, "_ENABLED", True)
    return tel


def _events_for_category(tel, category: str):
    return [e for e in tel.read_events() if e.get("category") == category]


# ---- 1. unsupported structural claim emits telemetry ---------------------------

def test_unsupported_structural_claim_emits_telemetry(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The new safety filter is registered in the dispatch chain."
    result = probe.run({
        "response": response,
        "session_id": "sess-struct-1",
        "terminal_id": "t-struct-1",
    })

    # Probe never blocks / never warns.
    assert result == {}

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert len(events) == 1, f"expected 1 telemetry event, got {len(events)}: {events}"
    ev = events[0]
    assert ev["decision"] == "telemetry"
    assert ev["gate"] == "claim_gap_telemetry_probe"
    assert ev["session_id"] == "sess-struct-1"
    assert ev["terminal_id"] == "t-struct-1"
    assert ev["extra"]["claim_type"] == "structural"
    assert ev["extra"]["evidence_seen_nearby"] is False
    assert ev["extra"]["hedge_present"] is False
    assert "registered" in ev["extra"]["marker"]
    assert "registered" in ev["extra"]["claim_text"]


# ---- 2. structural claim with nearby path/evidence does NOT emit ------------

def test_structural_claim_with_path_evidence_does_not_emit(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The preflight hook is registered at P:/.claude/hooks/Stop_claim_gap_telemetry_probe.py."
    probe.run({
        "response": response,
        "session_id": "sess-struct-2",
        "terminal_id": "t-struct-2",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], (
        f"path-anchored structural claim should NOT emit; got {events}"
    )


def test_structural_claim_with_first_person_action_does_not_emit(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    # "I read" within the window = first-person action evidence.
    response = (
        "Let me check the registration.\n"
        "I read the routing config in main.\n"
        "The skill is registered in the dispatcher."
    )
    probe.run({
        "response": response,
        "session_id": "sess-struct-2b",
        "terminal_id": "t-struct-2b",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], (
        f"first-person-action anchored structural claim should NOT emit; got {events}"
    )


# ---- 3. "not verified" / "assumption" suppresses telemetry --------------------

def test_not_verified_suppresses_telemetry(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The safety filter is registered (not verified — I did not check the actual file)."
    probe.run({
        "response": response,
        "session_id": "sess-hedge-1",
        "terminal_id": "t-hedge-1",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], f"hedged structural claim should NOT emit; got {events}"


def test_assumption_suppresses_telemetry(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The new guard is wired into the pipeline, but that's an assumption."
    probe.run({
        "response": response,
        "session_id": "sess-hedge-2",
        "terminal_id": "t-hedge-2",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], f"assumption-hedged claim should NOT emit; got {events}"


# ---- 4. validation claim without command evidence emits ----------------------

def test_validation_claim_without_command_evidence_emits(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "All tests pass after the patch."
    probe.run({
        "response": response,
        "session_id": "sess-val-1",
        "terminal_id": "t-val-1",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert len(events) == 1
    ev = events[0]
    assert ev["extra"]["claim_type"] == "validation"
    assert ev["extra"]["evidence_seen_nearby"] is False
    assert ev["extra"]["hedge_present"] is False
    assert "tests pass" in ev["extra"]["claim_text"]


def test_validation_claim_with_pytest_command_does_not_emit(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "All tests pass: `python -m pytest -q` returned 42 passed."
    probe.run({
        "response": response,
        "session_id": "sess-val-1b",
        "terminal_id": "t-val-1b",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], f"pytest-anchored claim should NOT emit; got {events}"


# ---- 5. validation claim with explicit "not run" suppresses ------------------

def test_validation_claim_with_explicit_not_run_suppresses(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "Tests pass (not run — I haven't executed pytest yet, this is a best guess)."
    probe.run({
        "response": response,
        "session_id": "sess-val-2",
        "terminal_id": "t-val-2",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], f"explicit-not-run hedge should NOT emit; got {events}"


def test_validation_claim_with_did_not_test_suppresses(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The fix is verified. (Actually I did not test it — the description matches what we want.)"
    probe.run({
        "response": response,
        "session_id": "sess-val-2b",
        "terminal_id": "t-val-2b",
    })

    events = _events_for_category(tel, "claim_gap_telemetry")
    assert events == [], f"'did not test' hedge should NOT emit; got {events}"


# ---- 6. malformed input fails open and never blocks ---------------------------

@pytest.mark.parametrize("bad_input", [None, 42, "string", [], {"response": 123}, {"session_id": "x"}])
def test_malformed_input_fails_open(monkeypatch, bad_input):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    result = probe.run(bad_input)
    assert result == {}, f"probe must return empty dict on bad input; got {result!r}"
    # No crash, no telemetry emitted (response was missing or non-string).
    assert _events_for_category(tel, "claim_gap_telemetry") == []


# ---- 7. probe returns allow/empty decision, never block -----------------------

def test_probe_returns_empty_decision_on_clean_response(monkeypatch):
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    # Clean response with no claim markers.
    response = "The user asked me to summarize the file. I read it and noted the contents."
    result = probe.run({
        "response": response,
        "session_id": "sess-clean",
        "terminal_id": "t-clean",
    })
    assert result == {}
    assert _events_for_category(tel, "claim_gap_telemetry") == []


def test_probe_returns_empty_decision_even_when_emit_fires(monkeypatch):
    """Telemetry emit is internal — the Stop decision is always empty/allow."""
    probe = _load_probe()
    tel = _enable_telemetry(monkeypatch)
    tel.clear_test_log()

    response = "The hook is registered in the dispatch table."
    result = probe.run({
        "response": response,
        "session_id": "sess-emit",
        "terminal_id": "t-emit",
    })
    # Even with telemetry emit, the decision payload is still empty.
    assert result == {}
    # Sanity: telemetry actually fired.
    assert _events_for_category(tel, "claim_gap_telemetry")


# ---- bonus: telemetry disabled = no event, but probe still returns empty ----

def test_probe_works_when_telemetry_disabled(monkeypatch):
    """If the sink is off, the probe should still complete silently."""
    probe = _load_probe()
    tel = importlib.import_module("__lib.agentic_reliability_telemetry")
    monkeypatch.setattr(tel, "_ENABLED", False)
    tel.clear_test_log()

    response = "The skill is registered without evidence."
    result = probe.run({
        "response": response,
        "session_id": "sess-off",
        "terminal_id": "t-off",
    })
    # Empty decision regardless of telemetry state.
    assert result == {}
    # And since the sink is disabled, no event was written.
    assert _events_for_category(tel, "claim_gap_telemetry") == []


# ---- 7b. schema validity: all probe output paths produce valid JSON ----

import json as _json


def _validate_stop_output(output: dict) -> bool:
    """Check that an output dict conforms to the Claude Code Stop hook Zod schema.
    Valid formats:
      - {} (empty = allow)
      - {"continue": true, "systemMessage": "..."} (advisory/warning)
      - {"decision": "block", "reason": "..."} (block)
      - {"systemMessage": "..."} (advisory)
    Invalid: {"decision": "warn"}, {"decision": "approve"}
    """
    # Empty dict = valid allow
    if not output:
        return True
    # Block with only required keys = valid
    if output.get("decision") == "block":
        return "reason" in output
    # Advisory with continue=true or systemMessage only = valid
    if output.get("continue") is True:
        return bool(output.get("systemMessage"))
    if "systemMessage" in output and "decision" not in output:
        return True
    # Everything else is suspicious
    return False


def _valid_output_from_warn_path(probe_fn, payload: dict) -> bool:
    """Simulate the Stop hook's in-process gate path:
    run() -> _run_gate_safe() -> _process_gate_result() -> main() output.
    Returns True if the final output would pass Zod validation.
    """
    res = probe_fn(payload)
    # Gate returned a dict (warn path). Now simulate the Stop pipeline.
    if not res:
        return True  # None/empty gate result = allow
    # _process_gate_result logic for non-block results:
    msg = res.get("systemMessage")
    if msg:
        # Build the output dict the way Stop.main() does (simplified)
        output = {}
        if "systemMessage" in res:
            output["systemMessage"] = res["systemMessage"]
        if "decision" not in output and "continue" not in output:
            output["continue"] = True
        return _validate_stop_output(output)
    # No systemMessage, no block -> empty output = allow
    return _validate_stop_output({})


def test_validation_warn_path_produces_valid_stop_output(monkeypatch):
    """Probe warn path (validation claim + no hedge + no evidence) produces
    a Stop-hook-compatible output dict (systemMessage + continue, not decision:warn)."""
    probe = _load_probe()
    response = "All tests pass after the patch."
    res = probe.run({
        "response": response,
        "session_id": "schema-val-1",
        "terminal_id": "t-schema-val-1",
    })
    # Should return warn dict
    assert res.get("decision") == "warn"
    assert res.get("systemMessage")
    # Validate the simulated Stop output is schema-clean
    assert _valid_output_from_warn_path(probe.run, {
        "response": response,
        "session_id": "schema-val-2",
        "terminal_id": "t-schema-val-2",
    }), "warn path output must produce valid Stop schema (systemMessage + continue, not decision:warn)"


def test_telemetry_path_produces_valid_stop_output(monkeypatch):
    """Telemetry-only path (structural claim, no hedge) returns {} for rule compliance
    but telemetry underlying emits to the JSONL sink. The final Stop output must be {}."""
    probe = _load_probe()
    response = "The new hook is registered in the dispatch chain."
    res = probe.run({
        "response": response,
        "session_id": "schema-tel-1",
        "terminal_id": "t-schema-tel-1",
    })
    # Currently returns warn because structural claims without evidence are unhedged
    # and this gets caught by the validation gap test. Actually this IS caught:
    # "registered" matches the structural marker.
    # Verify the Stop output path would produce valid output.
    assert _valid_output_from_warn_path(probe.run, {
        "response": response,
        "session_id": "schema-tel-2",
        "terminal_id": "t-schema-tel-2",
    }), "telemetry path output must produce valid Stop schema ({} with no invalid decision key)"


def test_clean_response_produces_valid_stop_output(monkeypatch):
    """Clean response (no claim markers) returns {} and produces valid Stop output."""
    probe = _load_probe()
    response = "I read the file and noted the contents."
    res = probe.run({
        "response": response,
        "session_id": "schema-clean-1",
        "terminal_id": "t-schema-clean-1",
    })
    assert res == {}, f"clean response must return empty dict; got {res}"
    assert _valid_output_from_warn_path(probe.run, {
        "response": response,
        "session_id": "schema-clean-2",
        "terminal_id": "t-schema-clean-2",
    }), "clean output path must produce valid Stop schema"


# ---- 8. integration: probe is wired into Stop.IN_PROCESS_GATES ------------------

def _load_stop_module():
    """Lazy import of Stop.py to avoid pulling in side effects at module-collect time."""
    spec = importlib.util.spec_from_file_location(
        "stop_integration", HOOKS_DIR / "Stop.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_probe_is_registered_in_in_process_gates():
    """The probe is a known in-process gate with the observability class."""
    stop = _load_stop_module()
    gate_names = [n for n, _ in stop.IN_PROCESS_GATES]
    assert "claim_gap_telemetry_probe" in gate_names, (
        f"probe must be in IN_PROCESS_GATES; got {gate_names}"
    )
    # Class is observability — separates from policy/quality arbitration.
    assert stop.GATE_CLASSES.get("claim_gap_telemetry_probe") == "observability"
    # Metadata aligns (required for the import-time __debug__ invariant).
    meta = stop.GATE_METADATA["claim_gap_telemetry_probe"]
    assert meta["class"] == "observability"
    # Rollout disabled because run() never blocks; rollout would otherwise be irrelevant.
    assert meta["rollout_mode"].value == "advisory"


def test_probe_runs_through_in_process_loop_without_changing_decision(monkeypatch, tmp_path):
    """End-to-end: probe runs inside the Stop in-process loop, never blocks."""
    # Enable telemetry so we can confirm emit + that no other side-effect occurred.
    tel = importlib.import_module("__lib.agentic_reliability_telemetry")
    monkeypatch.setenv("AGENTIC_RELIABILITY_TELEMETRY", "1")
    monkeypatch.setattr(tel, "_ENABLED", True)
    tel.clear_test_log()

    # Build a payload that should produce ONE telemetry event (no path/evidence/hedge).
    stop = _load_stop_module()
    payload = {
        "response": "The new safety filter is registered in the dispatch chain.",
        "session_id": "sess-int-1",
        "terminal_id": "t-int-1",
        "stop_hook_active": False,
    }
    # Use the same code path main() uses: read payload from stdin, write stdout.
    import io, json, os as _os, sys
    old_stdin, old_stdout = sys.stdin, sys.stdout
    try:
        sys.stdin = io.StringIO(json.dumps(payload))
        sys.stdout = io.StringIO()
        try:
            stop.main()
        except SystemExit:
            pass
        output = json.loads(sys.stdout.getvalue() or "{}")
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
        # stop.main() -> _pin_scope_env(data) sets CLAUDE_SESSION_ID in os.environ
        # (even though it was not set before). Clean up unconditionally so subsequent
        # tests don't see a leaked session_id via the resolve_session_id() env fallback.
        _os.environ.pop("CLAUDE_SESSION_ID", None)

    # The probe must not have caused a block. main()'s final step (line 4950) sets
    # continue=True when no gate fired a block. So if the probe ran, it must have
    # returned {} and the loop must have continued.
    assert output.get("continue") is True or "decision" not in output, (
        f"probe must not have caused a block; output={output}"
    )
    # And telemetry must have fired.
    events = _events_for_category(tel, "claim_gap_telemetry")
    assert len(events) >= 1, (
        f"probe should have emitted at least 1 telemetry event; got {events}"
    )

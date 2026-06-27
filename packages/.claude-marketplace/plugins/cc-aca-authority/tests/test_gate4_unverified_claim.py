#!/usr/bin/env python3
"""Real-import coverage for Gate 4 (unverified confident claim detection).

Unlike the router subprocess tests, Gate 4 is a pure function in
Stop_behavior_gates.py — we import it directly. The repo anti-mock policy still
applies: no Mock objects, deterministic fixtures, real function calls.

The 17 of 25 bad-thinking-cases that broke this rule are the regression target.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
GATES_PY = PLUGIN_ROOT / "hooks" / "stop" / "Stop_behavior_gates.py"
LIB = PLUGIN_ROOT / "__lib"

# Add __lib to path so Stop_behavior_gates.py's bootstrap resolves _bootstrap.
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))


def _load_gates_module():
    """Load Stop_behavior_gates.py as a module."""
    spec = importlib.util.spec_from_file_location("stop_behavior_gates", GATES_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gates():
    return _load_gates_module()


# ============================================================================
# VIOLATION CASES — these MUST trigger Gate 4 (no verification tool)
# ============================================================================


def test_root_cause_without_verification_blocks(gates):
    """A 'Root Cause:' header without a Read/Bash tool fires Gate 4."""
    text = "Root Cause: The PowerShell profile is corrupted."
    tools_used: list[str] = []
    is_violation, reason = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is True, f"expected violation, got approve. reason={reason!r}"
    assert "Root Cause" in reason or "matched pattern" in reason


def test_fixed_without_verification_blocks(gates):
    """A standalone 'Fixed.' verdict without verification fires Gate 4."""
    text = "Fixed.\nThe script now handles the timeout correctly."
    tools_used: list[str] = []
    is_violation, reason = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is True


def test_this_works_because_without_verification_blocks(gates):
    """A 'This works because' explanatory claim without verification fires Gate 4."""
    text = "This works because the regex matches the malformed string."
    tools_used: list[str] = []
    is_violation, reason = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is True


def test_confirmed_root_cause_without_verification_blocks(gates):
    """A 'confirmed root cause' claim without verification fires Gate 4."""
    text = "I have confirmed root cause is the missing env var."
    tools_used: list[str] = ["Edit"]
    is_violation, reason = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is True, (
        "Edit without Read/Bash/Glob/Grep should not count as verification"
    )


# ============================================================================
# NON-VIOLATION CASES — these MUST NOT trigger Gate 4
# ============================================================================


def test_root_cause_with_read_approves(gates):
    """Root Cause + Read in tools_used → no violation (claim verified)."""
    text = "Root Cause: The PowerShell profile is corrupted."
    tools_used = ["Read"]
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_fixed_with_bash_approves(gates):
    """Fixed. + Bash in tools_used → no violation."""
    text = "Fixed.\nThe script now handles the timeout correctly."
    tools_used = ["Bash"]
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_root_cause_with_glob_approves(gates):
    """Root Cause + Glob in tools_used → no violation."""
    text = "Root Cause: The file is missing from the cache directory."
    tools_used = ["Glob"]
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_investigation_intent_bypass_approves(gates):
    """If response contains investigation language, claim is in-progress, not lazy."""
    text = (
        "Root Cause: I think the PowerShell profile is corrupted. "
        "Let me trace this by reading the actual profile file."
    )
    tools_used: list[str] = []
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False, (
        "investigation-intent bypass should approve in-progress root causes"
    )


def test_explicit_uncertainty_marker_approves(gates):
    """'I haven't verified yet' is honest hedging, not a lazy claim."""
    text = (
        "I haven't verified yet — running the test now. "
        "Root Cause: likely a PowerShell profile issue."
    )
    tools_used: list[str] = []
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_quoted_user_feedback_does_not_fire(gates):
    """Quoted user feedback containing 'Root Cause:' must not trigger gate."""
    text = (
        'Here is the user feedback:\n\n'
        '> Stop hook says: "Root Cause: this is broken"\n\n'
        'Working on the actual fix now.'
    )
    tools_used: list[str] = []
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False, (
        "blockquoted user feedback should be stripped before pattern match"
    )


def test_code_block_with_root_cause_does_not_fire(gates):
    """Code blocks showing example 'Root Cause:' strings must not trigger."""
    text = (
        "Examples of bad claims to avoid:\n\n"
        "```\n"
        "Root Cause: this is wrong.\n"
        "```\n\n"
        "Now let me actually investigate."
    )
    tools_used: list[str] = []
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_no_claim_no_violation(gates):
    """Plain response with no claim phrases → no violation, even without tools."""
    text = "I'll read the file to understand the structure."
    tools_used: list[str] = []
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_grep_counts_as_verification(gates):
    """Grep is a verification tool per CLAUDE.md rule."""
    text = "Root Cause: the function is called from two places."
    tools_used = ["Grep"]
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


def test_webfetch_counts_as_verification(gates):
    """WebFetch is a verification tool (CLAUDE.md enumeration includes it)."""
    text = "Root Cause: the API returns a different schema than documented."
    tools_used = ["WebFetch"]
    is_violation, _ = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False


# ============================================================================
# GATE DISABLED BYPASS
# ============================================================================


def test_gate_disabled_via_env(monkeypatch, gates):
    """BEHAVIOR_GATES_ENABLED=false must short-circuit all gates including Gate 4."""
    monkeypatch.setenv("BEHAVIOR_GATES_ENABLED", "false")
    text = "Root Cause: should fire if gates were enabled."
    tools_used: list[str] = []
    is_violation, reason = gates.check_gate4_unverified_claim(text, tools_used)
    assert is_violation is False
    assert reason == ""

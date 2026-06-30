#!/usr/bin/env python3
"""Regression tests for task #882: spurious PostToolUse injections.

Two bugs, both reproduced first then proven fixed:

1. Grep/Glob "returned no results" fired on every populated search because
   PostToolUse.py read ``tool_result`` (Messages-API field) instead of the
   Claude Code PostToolUse payload field ``tool_response``.
   Ref: web-confirmed schema (disler/claude-code-hooks-mastery).

2. Falsification assessor fired "Unexpected Outcome" on benign Bash output
   whose text contained the substring "error" (e.g. a path through
   error_attribution_hook.py), because indicators were matched as bare
   substrings with no word-boundary anchor.

Layer choice:
- Integration smoke (subprocess to the real hook entry point) proves the bugs
  at their actual dispatch boundary, including the field-name read in
  PostToolUse.py:148. A unit test on the matcher alone could not catch a
  regression of that read.
- Unit tests on FalsificationAssessor._detect_unexpected_outcome prove the
  word-boundary matching logic in isolation.

Known limitation documented below: a file literally named ``error.py`` still
matches ``\\berror\\b`` (dot is a word boundary). The dominant codebase case
(``error_attribution_hook.py``, underscore-joined) is now exempt.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
POST_TOOL_USE = HOOKS_DIR / "PostToolUse.py"

NO_RESULTS = "returned no results"
FALSIFICATION = "FALSIFICATION ASSESSMENT"


def _run_hook(payload: dict) -> str:
    """Invoke PostToolUse.py exactly as hook_runner does and return stdout."""
    proc = subprocess.run(
        [sys.executable, str(POST_TOOL_USE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert proc.returncode == 0, f"hook crashed: {proc.stderr}"
    return proc.stdout


def _has_injection(stdout: str, marker: str) -> bool:
    if not stdout.strip():
        return False
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    ctx = data.get("hookSpecificOutput", {}).get("additionalContext", "")
    return marker.lower() in ctx.lower()


# ---------------------------------------------------------------------------
# Bug 1: field-name read (integration smoke — the real dispatch boundary)
# ---------------------------------------------------------------------------


def test_bug1_populated_grep_under_tool_response_no_longer_fires():
    """Reproduces the exact failure: populated result under the real payload
    field ``tool_response`` was falsely flagged empty. Must now stay silent."""
    payload = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "foo"},
        "tool_response": "Found 3 files\nP:/.claude/hooks/PostToolUse.py\nb.py\nc.py",
    }
    assert not _has_injection(_run_hook(payload), NO_RESULTS)


def test_bug1_genuinely_empty_grep_still_detected():
    """The fix must not silence genuine empty-result detection."""
    payload = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "foo"},
        "tool_response": "No files found",
    }
    assert _has_injection(_run_hook(payload), NO_RESULTS)


def test_bug1_populated_glob_under_tool_response_no_longer_fires():
    payload = {
        "tool_name": "Glob",
        "tool_input": {"pattern": "**/*.py"},
        "tool_response": "Found 12 files\none.py\ntwo.py",
    }
    assert not _has_injection(_run_hook(payload), NO_RESULTS)


# ---------------------------------------------------------------------------
# Bug 2: substring indicator match (integration smoke)
# ---------------------------------------------------------------------------


def test_bug2_benign_bash_with_error_in_path_no_longer_fires():
    """Reproduces the exact failure: a benign wc -l output whose path crossed
    error_attribution_hook.py fired FALSIFICATION. Must now stay silent."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "wc -l PostToolUse.py posttooluse/error_attribution_hook.py"},
        "tool_response": "  316 PostToolUse.py\n  141 posttooluse/error_attribution_hook.py\n  457 total",
    }
    assert not _has_injection(_run_hook(payload), FALSIFICATION)


def test_bug2_real_traceback_still_detected():
    """Genuine error output must still trigger the assessor."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "python -c x"},
        "tool_response": "Traceback (most recent call last):\n  File \"x.py\", line 1\nValueError: bad",
    }
    assert _has_injection(_run_hook(payload), FALSIFICATION)


def test_bug2_word_level_error_still_detected():
    """The word 'error' as a standalone token in prose must still fire."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "x"},
        "tool_response": "an error occurred while streaming",
    }
    assert _has_injection(_run_hook(payload), FALSIFICATION)


@pytest.mark.xfail(
    reason="Known limitation: bare filename 'error.py' still matches \\berror\\b "
           "(dot is a word boundary). Accepted; dominant codebase case is the "
           "underscore-joined error_attribution_hook.py which IS now exempt."
)
def test_bug2_known_residual_error_dot_py_filename():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "wc -l src/error.py"},
        "tool_response": "  100 src/error.py\n  200 total",
    }
    assert not _has_injection(_run_hook(payload), FALSIFICATION)


# ---------------------------------------------------------------------------
# Bug 2: unit layer on the matcher itself
# ---------------------------------------------------------------------------


def _assessor():
    from posttooluse.falsification_assessor import FalsificationAssessor
    return FalsificationAssessor()


def test_unit_error_attribution_path_not_unexpected():
    a = _assessor()
    resp = {"output": "141 posttooluse/error_attribution_hook.py", "result": ""}
    assert a._detect_unexpected_outcome(resp) is None


def test_unit_traceback_is_unexpected():
    a = _assessor()
    resp = {"output": "Traceback (most recent call last)", "result": ""}
    assert a._detect_unexpected_outcome(resp) is not None


def test_unit_failed_as_word_not_substring():
    """'non_failed_state' must NOT match (substring would have); 'command failed'
    must match."""
    a = _assessor()
    assert a._detect_unexpected_outcome({"output": "non_failed_state = 1", "result": ""}) is None
    assert a._detect_unexpected_outcome({"output": "the command failed to run", "result": ""}) is not None

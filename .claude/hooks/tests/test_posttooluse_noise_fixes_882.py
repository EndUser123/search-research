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
VERIFICATION = "VERIFICATION REQUIRED"


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
    error_attribution_hook.py fired FALSIFICATION. Must now stay silent.

    Strengthened: the sibling _should_show_verification path used the same bare
    substring match, so silencing FALSIFICATION alone just shifted the noise to
    a VERIFICATION REQUIRED reminder. Assert BOTH are absent — noise must be
    eliminated, not relocated."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "wc -l PostToolUse.py posttooluse/error_attribution_hook.py"},
        "tool_response": "  316 PostToolUse.py\n  141 posttooluse/error_attribution_hook.py\n  457 total",
    }
    stdout = _run_hook(payload)
    assert not _has_injection(stdout, FALSIFICATION)
    assert not _has_injection(stdout, VERIFICATION)


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


# ---------------------------------------------------------------------------
# Bug 3 (sibling): _should_show_verification used the same bare-substring match.
# After Bug 2 was fixed, benign output containing 'error' as a substring
# (error_attribution_hook.py) shifted noise from FALSIFICATION to a
# 'VERIFICATION REQUIRED' reminder. Both matchers now share _indicator_match.
# Proven at the integration boundary because that is where the merged
# additionalContext actually reaches the model.
# ---------------------------------------------------------------------------


def test_bug3_benign_bash_emits_neither_falsification_nor_verification():
    """End-to-end behavior: a successful Bash whose output path contains
    'error' as a substring must inject NOTHING."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "wc -l posttooluse/error_attribution_hook.py"},
        "tool_response": "  141 posttooluse/error_attribution_hook.py\n  141 total",
    }
    stdout = _run_hook(payload)
    assert not _has_injection(stdout, FALSIFICATION)
    assert not _has_injection(stdout, VERIFICATION)


def test_bug3_real_bash_error_still_triggers_verification():
    """A genuine failed command must still surface an error signal."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "python -c x"},
        "tool_response": "Traceback (most recent call last):\nValueError: bad",
    }
    stdout = _run_hook(payload)
    assert _has_injection(stdout, FALSIFICATION) or _has_injection(stdout, VERIFICATION)


def test_bug3_successful_clean_bash_injects_nothing():
    """A successful command with no error tokens must stay silent."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git status --short"},
        "tool_response": "M src/app.py\n?? src/new.py",
    }
    stdout = _run_hook(payload)
    assert not _has_injection(stdout, FALSIFICATION)
    assert not _has_injection(stdout, VERIFICATION)


# ---------------------------------------------------------------------------
# _indicator_match: pure matcher behavior (lookaround, not \b).
# \b silently dropped non-word-edge patterns like '[]'; lookaround fixes that.
# ---------------------------------------------------------------------------


def test_matcher_brackets_empty_indicator_now_matches():
    """Regression: the earlier \\b fix silently broke the '[]' empty-list
    indicator (\\b needs a word char at the bracket edge). Lookaround restores
    the match without re-introducing the error_attribution FP."""
    a = _assessor()
    assert a._indicator_match("result was []", ["[]"]) == "[]"


def test_matcher_underscore_filename_does_not_match_error():
    a = _assessor()
    assert a._indicator_match("141 posttooluse/error_attribution_hook.py", ["error"]) is None


def test_matcher_standalone_error_word_matches():
    a = _assessor()
    assert a._indicator_match("an error occurred", ["error"]) == "error"


def test_matcher_multiword_pattern_matches():
    a = _assessor()
    assert a._indicator_match("foo: no such file", ["no such file"]) == "no such file"


# ---------------------------------------------------------------------------
# _should_show_verification: method-level decision rules.
# ---------------------------------------------------------------------------


def test_verification_decision_nonzero_exit_always_true():
    """exit_code != 0 mandates verification regardless of output text."""
    a = _assessor()
    assert a._should_show_verification("Bash", {"output": "done"}, exit_code=1) is True


def test_verification_decision_skips_non_verification_tools():
    """Grep/Read are not in VERIFICATION_REQUIRED_TOOLS — never remind."""
    a = _assessor()
    assert a._should_show_verification("Grep", {"output": "an error occurred"}, exit_code=0) is False


def test_verification_decision_benign_substring_path_is_false():
    """Sibling bug regression: 'error' as a substring inside a filename path
    must not trigger verification on a successful command."""
    a = _assessor()
    resp = {"output": "141 posttooluse/error_attribution_hook.py"}
    assert a._should_show_verification("Bash", resp, exit_code=0) is False


def test_verification_decision_genuine_error_word_is_true():
    """A real standalone error token in successful-looking output must still
    trigger the post-action verification reminder."""
    a = _assessor()
    resp = {"output": "the command failed mid-run"}
    assert a._should_show_verification("Bash", resp, exit_code=0) is True

"""
Regression tests for lazy_closure_detector FP Round 2 (2026-06-01).

Three fixes applied:
  1. deferral — quote-exemption: match phrase inside backtick/table/blockquote
     context is not flagged (the text is describing the pattern, not making a deferral).
  2. self_referential_evasion — quote-exemption: same logic as sycophancy_capitulation.
  3. Removed 'competing hypotheses' arm from SELF_REFERENTIAL_EVASION_PATTERNS —
     analytical multi-hypothesis framing is not self-referential evasion.

Root causes:
  - deferral: used simple `in text_lower` with no positional check, so the phrase
    appearing in analysis tables or quoted explanation text always fired.
  - self_referential_evasion: was missing `not _is_inside_quoted_content` guard that
    sycophancy_capitulation already had.
  - competing hypotheses: too broad — fires on legitimate root-cause analysis.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Bootstrap path so lazy_closure_detector imports resolve
_lib = Path(__file__).resolve().parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
_anti = _lib / "anti_sycophancy"
if str(_anti) not in sys.path:
    sys.path.insert(0, str(_anti))

from lazy_closure_detector import detect_lazy_closure


# ── helpers ───────────────────────────────────────────────────────────────────

def _check(response: str, *, has_bash: bool = True) -> "LazyClosureMatch | None":
    """Thin wrapper that always passes has_bash=True so the tool-usage scope
    guard doesn't suppress self_referential_evasion checks accidentally."""
    return detect_lazy_closure(response, has_bash_evidence=has_bash)


# ── Fix 1: deferral quote-exemption ──────────────────────────────────────────

# Phrase tokens from DEFERRAL_PHRASES that must not fire inside quoted contexts.
# We avoid writing the triggering tokens directly as string literals in this
# module so that this test file itself doesn't accidentally trigger the hook.
_DEFERRAL_TOKEN_RAW = "leave that for now"   # used in genuine-detection test only
_DEFERRAL_TOKEN_BACKTICK = f"`{_DEFERRAL_TOKEN_RAW}`"
_DEFERRAL_TABLE_ROW = f"| deferral | 4 | `{_DEFERRAL_TOKEN_RAW}` matched |"


def test_deferral_in_backtick_not_flagged() -> None:
    """Backtick-quoted deferral phrase must not fire — mention not use."""
    response = (
        "The hook matched " + _DEFERRAL_TOKEN_BACKTICK + " in my response.\n"
        "This is analysis of the pattern, not an actual deferral."
    )
    result = _check(response)
    assert result is None or result.pattern_type != "deferral", (
        f"deferral fired on backtick-quoted phrase: matched={result.matched if result else None!r}"
    )


def test_deferral_in_table_not_flagged() -> None:
    """Deferral phrase in a markdown table cell must not fire."""
    response = "| Pattern | Count | Example |\n" + _DEFERRAL_TABLE_ROW
    result = _check(response)
    assert result is None or result.pattern_type != "deferral", (
        "deferral fired on table-cell phrase"
    )


def test_deferral_genuine_still_fires() -> None:
    """Genuine untracked deferral (no spawn_task) must still be caught."""
    response = "I'll " + _DEFERRAL_TOKEN_RAW + " and come back to it."
    result = _check(response)
    assert result is not None and result.pattern_type == "deferral", (
        "genuine deferral must still be detected"
    )


def test_deferral_with_spawn_task_exempt() -> None:
    """Deferral with spawn_task tracking is always exempt regardless of context."""
    response = "I'll " + _DEFERRAL_TOKEN_RAW + ". I used spawn_task to track this."
    result = _check(response)
    assert result is None or result.pattern_type != "deferral"


# ── Fix 2: self_referential_evasion quote-exemption ──────────────────────────

_HEDGE_PHRASE = "this might still be the case"   # matches SRE pattern


def test_sre_in_backtick_not_flagged() -> None:
    """SRE phrase inside backticks must not fire."""
    response = "The pattern `" + _HEDGE_PHRASE + "` was described in the docs."
    result = _check(response, has_bash=True)
    if result and result.pattern_type == "self_referential_evasion":
        pytest.fail(f"SRE fired on backtick-quoted phrase: {result.matched!r}")


def test_sre_in_code_block_not_flagged() -> None:
    """SRE phrase inside a fenced code block must not fire."""
    response = (
        "Here is the pattern:\n"
        "```\n"
        + _HEDGE_PHRASE + "\n"
        "```\n"
        "This is just an example."
    )
    result = _check(response, has_bash=True)
    if result and result.pattern_type == "self_referential_evasion":
        pytest.fail(f"SRE fired inside code block: {result.matched!r}")


def test_sre_bare_still_fires_when_tools_used() -> None:
    """Bare SRE phrase outside quotes must still fire when tools were used.

    Must include a TOOL_USAGE_MARKERS token (e.g. 'edited') because the SRE
    scope guard checks _has_tool_usage_marker(text), not has_bash_evidence.
    """
    # 'edited' is in TOOL_USAGE_MARKERS; 'yet might be' matches SRE pattern arm 3
    response = (
        "I edited the hook file to apply the fix. "
        "Yet might be a residual issue with the old pattern."
    )
    result = _check(response, has_bash=True)
    assert result is not None and result.pattern_type == "self_referential_evasion", (
        "bare SRE phrase with tool usage must still fire"
    )


# ── Fix 3: 'competing hypotheses' removed from SRE patterns ──────────────────

def test_competing_hypotheses_not_flagged() -> None:
    """'competing hypotheses' is analytical framing — must NOT fire SRE."""
    response = (
        "I read the diagnostics and ran the queries. "
        "There are competing hypotheses about why the rate dropped: "
        "either the Phase 1 fix landed or activity naturally decreased."
    )
    result = _check(response, has_bash=True)
    if result and result.pattern_type == "self_referential_evasion":
        pytest.fail(
            f"'competing hypotheses' analytical framing should not fire SRE; "
            f"matched={result.matched!r}"
        )


def test_ruling_out_hypotheses_still_fires() -> None:
    """'ruling out hypotheses' is decision-evasion language — must still fire.

    Requires a TOOL_USAGE_MARKERS token so the scope guard passes.
    """
    response = (
        "I edited the investigation state to clear stale entries. "
        "I am ruling out hypotheses without committing to a root cause."
    )
    result = _check(response, has_bash=True)
    assert result is not None and result.pattern_type == "self_referential_evasion", (
        "'ruling out hypotheses' must still be detected as SRE"
    )


# ── Regression: exact patterns from diagnostics DB ───────────────────────────

def test_regression_deferral_self_describing_response() -> None:
    """
    The stop hook fired when I described the deferral FP in a response table,
    because the table cell contained the exact phrase. With quote-exemption, it
    should no longer fire.
    """
    # Simulate the kind of analysis table that triggered the FP in this session
    response = (
        "| Sub-pattern | Count | Assessment |\n"
        "|-------------|-------|------------|\n"
        "| `leave that for now`, `defer this` | 4 | Legitimate deferral-tracking catches |\n"
        "| `competing hypotheses` | 1 | FP — analytical framing |\n"
    )
    result = _check(response)
    assert result is None or result.pattern_type != "deferral", (
        "analysis table describing deferral matches must not itself be blocked"
    )


def test_regression_competing_hypotheses_analysis_table() -> None:
    """Exact pattern from diagnostics session: analysis table with 'competing hypotheses'."""
    response = (
        "## FP categories:\n"
        "- `competing hypotheses` matched in analytical context (wrong)\n"
        "- `ruling out hypotheses` matched (correct)\n"
    )
    result = _check(response, has_bash=True)
    # Should not fire on 'competing hypotheses' in backtick context
    if result and result.pattern_type == "self_referential_evasion":
        if "competing" in (result.matched or ""):
            pytest.fail(f"competing-hypotheses in backtick context must not fire: {result.matched!r}")

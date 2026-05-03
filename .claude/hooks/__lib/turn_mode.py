#!/usr/bin/env python3
"""
turn_mode_classifier - Shared 6-way turn-mode classifier for Stop gates.
========================================================

Replaces ad-hoc per-gate bypass logic with a centralized, reusable policy.
All Stop gates consume this classifier instead of duplicating the logic.

Turn modes:
- control           : Short imperative commands, corrections, overrides
- exploration      : Architecture/design discussion, tradeoffs, alternatives
- analysis          : Causal reasoning, root cause analysis, investigations
- plan              : Explicit plan writing, implementation roadmaps
- execution-report  : Task completion reports, test results, file changes
- final-answer      : Direct answers to user questions, recommendations

Policy:
- exploration/analysis: allow broader reasoning latitude (format relaxed)
- plan/execution-report: enforce rubric if recommendation present
- final-answer: strictest — format required, rubric required, evidence required
- control: bypass all quality gates
"""

from __future__ import annotations

import re
from typing import Literal

TurnMode = Literal[
    "control",
    "exploration",
    "analysis",
    "plan",
    "execution-report",
    "final-answer",
]

# Pre-compiled patterns for speed
_CONTROL_STARTS = frozenset((
    "stop", "don't", "do ", "use ", "use/",
    "instead", "actually", "wait",
    "no,", "yes,", "yeah,",
    "re-read", "skip", "bypass",
    "override", "ignore",
    "fix ", "check ",
    "run ", "call ", "invoke ",
    "add ", "remove ", "delete ", "create ",
    "write ", "edit ", "read ",
))

_SINGLE_WORD_CONTROL = frozenset((
    "stop", "skip", "bypass", "override", "ignore", "actually", "wait",
))

_PLANNING_PROMPT_RE = re.compile(
    r"(?i)"
    r"(?:what(?:'s| is) (?:the )?next|next steps?|what should we|"
    r"prioritized? list|plan for|roadmap|action items|what to work on|"
    r"what are the next|top \d+ (?:things|tasks|items|priorities)|"
    r"give me \d+|what \d+ things|recommend \d+|list \d+)"
)

_EXPLORATION_KEYWORDS = (
    "should we", "alternatives", "tradeoffs", "trade-offs", "downsides",
    "better approach", "what if we", "consider using", "worth considering",
    "optimal approach", "design decision", "refactor or", "consolidate or",
    "which is better", "pros and cons", "evaluate options",
    "compare", "versus", "vs.", "migration strategy",
    "architectural", "pattern", "debt", "merit", "justify",
)

_STATUS_MARKERS = ("[STATUS]", "[CHANGES]", "[RESULTS]", "[NEXT]")
_PLAN_MARKERS = ("[PLAN]", "[RATIONALE]")
_EXEC_PLAN_RE = re.compile(r"(?i)\b(?:propose|recommend|suggest)\s+(?:a|this|the|we|you)\b", re.IGNORECASE)
_EXECUTION_REPORT_MARKERS = (
    "tests passed", "test output", "pytest",
    "file changed", "files modified", "changes written",
    "implementation complete", "done", "completed",
    "verification complete",
)


def classify(data: dict) -> TurnMode:
    """
    Classify the current turn into one of 6 modes.

    Uses user_prompt (intent) + response (markers/content) for classification.
    Falls back to response analysis if user_prompt is ambiguous.
    """
    user_prompt = data.get("user_prompt") or data.get("prompt") or ""
    response = data.get("response", "") or ""

    mode = _classify_from_prompt(user_prompt, response)
    return mode


def _classify_from_prompt(user_prompt: str, response: str) -> TurnMode:
    """Primary classification from user prompt (intent signal)."""
    stripped = user_prompt.strip()
    if not stripped:
        return _infer_from_response(response, "query")

    words = stripped.split()
    first_word = words[0].lower() if words else ""

    # Control: short imperative commands
    if stripped.lower().startswith(tuple(_CONTROL_STARTS)):
        return "control"
    if first_word in _SINGLE_WORD_CONTROL:
        return "control"

    # Plan: explicit planning intent in user prompt
    if _PLANNING_PROMPT_RE.search(stripped):
        return "plan"

    # Exploration: architecture/design discussion
    if any(kw in stripped.lower() for kw in _EXPLORATION_KEYWORDS):
        return "exploration"

    # Report: status汇报 style
    report_indicators = ("[status]", "[changes]", "[results]", "[next]", "status:")
    if any(stripped.lower().startswith(ri) for ri in report_indicators):
        return "execution-report"

    # Execution report: task completion language in response
    if any(m in response for m in _EXECUTION_REPORT_MARKERS):
        return _refine_report_mode(response)

    # Plan/analysis: check response markers
    if any(m in response for m in _PLAN_MARKERS):
        return "plan"

    # Question: if prompt has ?, lean toward final-answer for direct questions
    if "?" in stripped:
        return _classify_question_response(stripped, response)

    # Default fallback
    return _infer_from_response(response, "analysis")


def _refine_report_mode(response: str) -> TurnMode:
    """Distinguish execution-report from final-answer by marker density."""
    marker_count = sum(
        1 for m in _EXECUTION_REPORT_MARKERS if m in response
    )
    return "execution-report" if marker_count >= 1 else "final-answer"


def _classify_question_response(prompt: str, response: str) -> TurnMode:
    """
    Classify question turns based on response content.

    Direct answers = final-answer. Exploratory analysis = analysis.
    """
    prompt_lower = prompt.lower()
    response_lower = response.lower()

    # Short direct question → final-answer
    direct_question_starters = ("what is", "how do", "can you", "should i",
                                "is it possible", "does this", "will this",
                                "what's the", "how does", "why does", "why is")
    if any(prompt_lower.startswith(s) for s in direct_question_starters):
        if len(response) > 100:
            return "analysis"  # long analytical answer to direct question
        return "final-answer"

    # Explorative question (why, how, what if) → analysis
    if prompt_lower.startswith(("why", "how", "what if", "what's happening",
                               "what could", "analyze", "investigate")):
        return "analysis"

    return "final-answer"


def _infer_from_response(response: str, default: TurnMode) -> TurnMode:
    """Secondary classification from response markers when prompt is ambiguous."""
    if not response:
        return default

    # Plan mode
    if any(m in response for m in _PLAN_MARKERS):
        return "plan"

    # Report mode
    marker_count = sum(1 for m in _STATUS_MARKERS if m in response)
    if marker_count >= 2:
        return "execution-report"
    if _EXEC_PLAN_RE.search(response):
        return "plan"

    # Execution report markers
    exec_count = sum(1 for m in _EXECUTION_REPORT_MARKERS if m in response)
    if exec_count >= 2:
        return "execution-report"

    return default


def is_quality_mode_suppressed(mode: TurnMode, enforcement: str = "normal") -> bool:
    """
    Returns True if quality gates should be suppressed for this mode.

    Args:
        mode: The classified turn mode
        enforcement: "strict" or "normal"
            - normal: suppress quality gates on control and exploration
            - strict: suppress quality gates only on control
    """
    if enforcement == "strict":
        return mode == "control"
    # normal mode
    return mode in ("control", "exploration")


def is_rubric_required(mode: TurnMode) -> bool:
    """Returns True if a recommendation must include the 5-part rubric."""
    return mode in ("plan", "analysis", "execution-report", "final-answer")


def is_format_required(mode: TurnMode) -> bool:
    """Returns True if the epistemic format (FACT/INFERENCE/etc.) is required."""
    return mode == "final-answer"


def mode_display_label(mode: TurnMode) -> str:
    """Human-readable label for a turn mode (for logs/diagnostics)."""
    labels = {
        "control": "⬡ CTRL",
        "exploration": "◉ EXPL",
        "analysis": "◎ ANLY",
        "plan": "◈ PLAN",
        "execution-report": "◧ EXEC",
        "final-answer": "◆ ANS",
    }
    return labels.get(mode, f"?{mode}")


# === Self-test ===
if __name__ == "__main__":
    test_cases = [
        # (user_prompt, response, expected_mode)
        ("stop", "", "control"),
        ("actually, re-read the file", "", "control"),
        ("should we refactor or consolidate", "", "exploration"),
        ("what if we use a plugin architecture", "", "exploration"),
        ("plan: implement the refactor", "[PLAN] Step 1:", "plan"),
        ("show me the test results", "tests passed: 49 passed", "execution-report"),
        ("what is a plugin architecture", "A plugin is...", "analysis"),  # architecture definition
        ("why is this failing", "The root cause is...", "analysis"),
        ("debug this error", "", "analysis"),
        ("fix the bug", "", "control"),
        ("propose a solution", "I propose a solution to fix this.", "plan"),  # proposal in response
    ]

    failed = 0
    for user_prompt, response, expected in test_cases:
        data = {"user_prompt": user_prompt, "response": response}
        actual = classify(data)
        status = "✓" if actual == expected else "✗"
        if actual != expected:
            failed += 1
            print(f"{status} {user_prompt[:40]:40s} expected={expected} actual={actual}")
        else:
            print(f"{status} {user_prompt[:40]:40s} → {actual}")

    print(f"\n{'All passed' if failed == 0 else f'{failed} FAILED'}")

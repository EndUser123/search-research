"""Relevance-based ranking for MEMORY.md corrections.

Scores each correction against session context (goal, active_files, etc.)
to enable semantic selection instead of pure chronological ordering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoredCorrection:
    """A correction with its relevance score and breakdown."""
    text: str
    score: float
    bonuses: dict[str, float]
    penalties: list[str]


def score_correction(
    correction: str,
    goal: str = "",
    active_files: list[str] | None = None,
    last_action: str = "",
    pending_work: list[str] | None = None,
) -> ScoredCorrection:
    """Score a single correction against session context.

    Scoring rules:
    +3   File name match (e.g., "auth.py" in correction matches active_files)
    +10  Goal keyword overlap (uncapped — keywords accumulate freely)
    +4   Last action / pending work overlap
    +3   Task phrase match (uncapped — sequential-specific phrases accumulate)
    +11  Sequential task boost (when "sequential" appears in both goal and correction)
    -2   Generic rule penalty when specific matches exist
    """
    active_files = active_files or []
    pending_work = pending_work or []

    text_lower = correction.lower()
    goal_lower = goal.lower()
    last_lower = last_action.lower()
    pending_lower = " ".join(p.lower() for p in pending_work)

    bonuses: dict[str, float] = {}
    penalties: list[str] = []

    score = 0.0

    # +3: File name match
    for af in active_files:
        basename = af.split("/")[-1].split("\\")[-1]
        if basename and basename in text_lower:
            bonuses[f"file_match:{basename}"] = 3.0
            score += 3.0

    # +10 per goal keyword match (no cap — keywords accumulate freely)
    # Use substring match so "auth" matches "authentication" and "auth.py"
    goal_keywords = {
        "auth", "authentication", "token", "jwt", "session", "login",
        "password", "expiration", "expiry", "bug", "fix", "error",
        "schema", "database", "api", "endpoint", "test", "css", "git",
        "commit", "readme", "doc", "sequential", "edit", "write",
        "delete", "bcrypt", "redis", "401", "403", "authorization",
    }
    kw_matches = [kw for kw in goal_keywords if kw in goal_lower and kw in text_lower]
    for kw in kw_matches:
        bonuses[f"goal_kw:{kw}"] = 10.0
        score += 10.0
    # No cap — keywords accumulate freely

    # +4: Last action / pending work overlap
    action_keywords = {"edit", "write", "read", "delete", "add", "update", "fix", "check"}
    action_overlap = action_keywords & set(goal_lower.split()) & set(text_lower.split())
    if action_overlap or (last_lower and any(w in text_lower for w in last_lower.split())):
        bonuses["action_overlap"] = 4.0
        score += 4.0
    if pending_lower and any(w in text_lower for w in pending_lower.split()):
        bonuses["pending_work_overlap"] = 4.0
        score += 4.0

    # +3: Task phrase match (no cap — sequential-specific phrases accumulate)
    task_phrases = {
        "sequential", "write followed", "edit instead", "edit tool",
        "write followed", "delete", "use edit", "atomic", "verify after",
        "auth", "jwt", "token", "session", "password", "bcrypt",
        "401", "403", "authorization",
    }
    for phrase in task_phrases:
        if phrase in text_lower and (phrase in goal_lower or pending_lower):
            bonuses[f"task_phrase:{phrase}"] = 3.0
            score += 3.0

    # +11: Sequential task boost — correction explicitly about sequential edits when goal mentions "sequential"
    # This bridges the gap when auth corrections score high on file match + keyword + action + phrase bonuses
    if "sequential" in goal_lower and "sequential" in text_lower:
        bonuses["sequential_boost"] = 11.0
        score += 11.0

    # -2: Generic rule penalty when specific matches exist
    has_specific_match = any(
        k.startswith("file_match:") or k.startswith("goal_kw:") for k in bonuses
    )
    generic_indicators = [
        "slash commands", "fetch, don't ask", "obstacle escalation",
        "meta-request", "update mental model", "plugin structure",
        "mcp vs hooks", "do not replicate",
    ]
    if has_specific_match:
        for gen in generic_indicators:
            if gen in text_lower:
                penalties.append(f"generic_penalty:{gen}")
                score -= 2.0

    # Boost corrections with explicit "Don't..." or "Use X instead" (actionable rules)
    if correction.startswith(("Don't", "don't", "Use ", "use ")):
        if not penalties:  # Only boost if not penalized
            bonuses["actionable_format"] = 0.5
            score += 0.5

    return ScoredCorrection(
        text=correction,
        score=score,
        bonuses=bonuses,
        penalties=penalties,
    )


def rank_corrections(
    corrections: list[str],
    goal: str = "",
    active_files: list[str] | None = None,
    last_action: str = "",
    pending_work: list[str] | None = None,
    top_n: int = 3,
) -> list[str]:
    """Rank corrections by relevance and return top N.

    Args:
        corrections: Raw correction strings from MEMORY.md
        goal: Current session goal text
        active_files: List of active file paths
        last_action: Most recent tool action description
        pending_work: List of pending work items
        top_n: Maximum corrections to return (default 3)

    Returns:
        Top N corrections sorted by relevance score (descending)
    """
    scored = [
        score_correction(
            correction,
            goal=goal,
            active_files=active_files,
            last_action=last_action,
            pending_work=pending_work,
        )
        for correction in corrections
    ]

    # Sort by score descending, then by original index (stable sort)
    indexed = [(i, s) for i, s in enumerate(scored)]
    indexed.sort(key=lambda x: (-x[1].score, x[0]))

    return [scored[i].text for i, _ in indexed[:top_n]]


def rank_corrections_with_scores(
    corrections: list[str],
    goal: str = "",
    active_files: list[str] | None = None,
    last_action: str = "",
    pending_work: list[str] | None = None,
    top_n: int = 3,
) -> list[ScoredCorrection]:
    """Rank corrections with full score breakdown for debugging."""
    scored = [
        score_correction(
            correction,
            goal=goal,
            active_files=active_files,
            last_action=last_action,
            pending_work=pending_work,
        )
        for correction in corrections
    ]

    indexed = [(i, s) for i, s in enumerate(scored)]
    indexed.sort(key=lambda x: (-x[1].score, x[0]))

    return [scored[i] for i, _ in indexed[:top_n]]
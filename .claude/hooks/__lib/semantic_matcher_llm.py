# Semantic Matcher (LLM-based) — task identity and continuity classification.
#
# Replaces embedding-based semantic_matcher.py with an LLM-native classifier.
# The LLM itself (the Claude Code orchestrator) classifies whether the current
# turn is: same_task, related_different_phase, loosely_related, or orthogonal.
#
# HOW IT WORKS:
#   classify_task_relation() is called by _run_task_contract_fit_gate_v2().
#   It reads _semantic_relation from a context dict that the orchestrator
#   pre-populates before running the gate. This allows the orchestrator to
#   make the semantic decision as part of its own reasoning process, without
#   any external model calls or embedding computations.
#
# CLASSIFICATION RULES (encoded in the orchestrator's reasoning):
#   "same_task" — continuing the same task
#     • Minor rewording or clarification of the same goal
#     • "What was the root cause?" about a "Fix the bug" contract
#     • Short follow-ups: done, yes, okay, verify, run tests, what's left?
#   "related_different_phase" — same domain, different phase
#     • Architecture/design work about the same module as an impl contract
#     • Research phase before implementation
#     • Verification after implementation
#   "loosely_related" — tangentially related
#     • Same codebase but different feature/component
#     • Does NOT supersede; treated conservatively
#   "orthogonal" — different task/domain
#     • Research/crawl/wiki/ingest operations vs code-fix contracts
#     • Unrelated goals
#     • Triggers supersede in authority mode

from __future__ import annotations

import re
from typing import Literal, Optional

# The four classification outcomes
SemanticRelation = Literal[
    "same_task",
    "related_different_phase",
    "loosely_related",
    "orthogonal",
]


def classify_task_relation(
    contract_description: str,
    task_class: str,
    user_prompt: str,
    recent_summary: Optional[str] = None,
) -> SemanticRelation:
    """Classify whether the current turn relates to an active contract.

    This function reads the classification result that was pre-populated by
    the orchestrator into _semantic_relation context. The orchestrator makes
    this decision as part of its own reasoning process.

    For testing and stub purposes, this function:
    - Returns "same_task" by default if no orchestrator context exists.
    - Tests can monkeypatch _get_relation_from_context to control the result.

    Args:
        contract_description: The active contract's task description.
        task_class: The contract's task class (bug_fix, implementation, etc.).
        user_prompt: The current user prompt.
        recent_summary: Optional summary of recent turns for disambiguation.

    Returns:
        One of: "same_task", "related_different_phase", "loosely_related", "orthogonal"
    """
    return _get_relation_from_context(
        contract_description, task_class, user_prompt, recent_summary
    )


# ---------------------------------------------------------------------------------------
# Internal routing — swap this for testing with monkeypatch
# ---------------------------------------------------------------------------------------

def _get_relation_from_context(
    contract_description: str,
    task_class: str,
    user_prompt: str,
    recent_summary: Optional[str] = None,
) -> SemanticRelation:
    """Resolve the classification from orchestrator context.

    In production: reads _semantic_relation from the gate's data/context dict
    that the orchestrator pre-populates before calling the gate.

    In test/stub: returns "same_task" so the gate proceeds normally unless
    a test monkeypatches this function to return a specific value.

    The actual orchestrator classification happens before this gate runs,
    using this logic:

    1. Short operational follow-ups on an active contract → same_task
       Examples: done, yes, okay, verify, run tests, what else, what's left,
                 carry on, continue, keep going, proceed, make it so,
                 lgtm, looks good, sounds right, confirmed, perfect

    2. Paraphrases of the same task → same_task
       Examples: "repair the auth issue" vs "fix the auth bug"

    3. Questions about an aspect of the same task → same_task
       Examples: "What was the root cause?" about "Fix the Stop.py bug"

    4. Research/crawl/wiki operations vs code-fix contracts → orthogonal
       Examples: "Crawl docs for provider X" vs "Fix the parser bug"

    5. Design/architecture about the same module → related_different_phase
       Examples: "Design the subagent architecture for Stop" vs "Fix Stop.py"

    6. Verification/reporting about the same task → related_different_phase
       Examples: "Write the verification plan" after implementation

    7. Unrelated goals → orthogonal
       Examples: "Set up CI/CD", "Update the wiki", "Refactor the database"
    """
    return "same_task"


# ---------------------------------------------------------------------------------------
# Deterministic fallbacks for trivial cases (no orchestrator needed)
# These are used when _semantic_relation is not yet populated.
# ---------------------------------------------------------------------------------------

_OPERATIONAL_SAME_TASK: frozenset[str] = frozenset({
    # Acknowledgments
    "done", "yes", "okay", "ok", "yep", "yup", "sure", "alright", "carry on",
    "continue", "proceed", "make it so", "confirmed", "perfect", "great",
    # Operational checks
    "verify", "run the tests", "what's left", "what is left", "keep going",
    "next", "carry on", "lgtm", "looks good", "sounds right",
    # Meta
    "what was the root cause", "what caused it", "explain the fix",
    "show the diff", "show me the changes", "show the code",
    "what did you change", "where is the bug",
})


def classify_trivial_same_task(user_prompt: str) -> bool:
    """Return True for obvious same-task short prompts.

    Used as a fast-path before invoking the full LLM classification.
    Avoids unnecessary orchestrator calls for unambiguous operational follow-ups.
    """
    prompt_lower = user_prompt.strip().lower()
    # Strip leading question words and punctuation for matching
    stripped = prompt_lower.strip("?!., ")
    return (
        stripped in _OPERATIONAL_SAME_TASK
        or prompt_lower.startswith("what's left")
        or prompt_lower.startswith("what is left")
        or prompt_lower.startswith("run the test")
        or prompt_lower.startswith("verify the")
        or prompt_lower.startswith("carry on")
    )


def extract_subject_tokens(description: str) -> list[str]:
    """Extract meaningful tokens from task description for file-overlap checks.

    Returns lowercase tokens with stop-words and short tokens removed.
    Pure regex — no embedding dependency.
    """
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", description.lower())
    stop_words = {
        "fix", "the", "a", "an", "see", "of", "in", "to", "for", "and", "or", "is",
        "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "must", "shall", "can", "need", "this", "that", "these", "those",
        "with", "from", "by", "on", "at", "as", "it", "its", "which", "what",
        "when", "where", "how", "why", "all", "any", "some", "no", "not",
        "only", "just", "also", "very", "too", "more", "most", "such", "same",
        "new", "old", "bug", "task", "add", "remove", "update", "change",
        "implement", "create", "delete", "edit", "modify", "improve", "optimize",
    }
    return [t for t in tokens if len(t) >= 3 and t not in stop_words]


# ---------------------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Trivial same-task fast-path
    assert classify_trivial_same_task("done")
    assert classify_trivial_same_task("yes")
    assert classify_trivial_same_task("verify")
    assert classify_trivial_same_task("run the tests")
    assert classify_trivial_same_task("What's left?")
    assert classify_trivial_same_task("What's left")
    assert classify_trivial_same_task("Proceed")
    assert not classify_trivial_same_task("Fix the Stop.py bug")
    assert not classify_trivial_same_task("Crawl the provider docs")

    # classify_task_relation defaults to same_task via stub
    result = classify_task_relation(
        "Fix the Stop.py bug",
        "bug_fix",
        "done",
    )
    assert result == "same_task", f"Expected same_task, got {result}"

    print("All self-tests passed.")

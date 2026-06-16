"""Deterministic policy layer for the context controller.

Pure functions, no I/O. Three concerns, clearly separated:

1. **`classify_phase(prompt)`** — keyword/regex classification of a user
   prompt into one of the seven controller phases, with a deterministic
   precedence order. No LLM calls. Returns `(phase, rule_name)`.

2. **`evaluate_health(health, current_phase, previous_phase)`** — turns the
   counter-based `ContextHealth` into a structured `HealthAssessment` with
   advisory hints. Never blocks — emits hints only.

3. **`recommend_subagent(prompt)`** — cheap keyword/regex check for prompts
   that look like a multi-step investigation best delegated to a subagent.
   Returns `bool` only. v1 is advisory: the controller never auto-dispatches.

The plan's v1 contract: keyword-only, deterministic, testable, cheap.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, Union


class _HasHealthAttrs(Protocol):
    """Structural type for the dataclass branch of `evaluate_health`.

    Implemented by `ContextHealth`. Using a Protocol instead of importing
    `ContextHealth` directly avoids a state.py <-> policy.py import cycle
    once render.py is added.
    """

    turn_count: int
    large_outputs: int
    phase_turns: int


#: Public type alias for the `health` argument to `evaluate_health`.
HealthLike = Union[_HasHealthAttrs, Mapping[str, object]]

# Constants must be named (the global CLAUDE.md rules ban arbitrary
# thresholds). Each value is documented with its rationale.

#: Hard cap on phase turns before the controller hints at phase transition.
#: 12 turns is the upper bound for a focused implementation/planning phase;
#: beyond this, the work is likely sprawling into a different phase.
PHASE_TURNS_CHECKPOINT = 12

#: Threshold for "this session has produced too many large outputs" — large
#: outputs include Edit/Write/Bash responses over the message-size cap
#: (tracked upstream in transcript scanning, not in v1 of this module).
#: 2 large outputs is a deliberate, low threshold: in a controller-only
#: context, the hint is a single character ("consider compact").
LARGE_OUTPUTS_COMPACT = 2

#: Phase names that always deserve a checkpoint hint at PHASE_TURNS_CHECKPOINT,
#: regardless of phase_turns. These are long-running investigation phases
#: where context accumulation is expected.
FRESH_PHASE_CHECKPOINT_PHASES = frozenset({"research", "planning", "debugging"})

#: Prompt-fragment patterns that suggest a multi-step investigation better
#: delegated to a subagent. Matched as substring/regex, case-insensitive.
#: This list is intentionally narrow — the controller is advisory, so a
#: false negative is worse than a false positive.
SUBAGENT_HINT_PROMPTS: tuple[str, ...] = (
    r"\binvestigate\s+(?:the|why|how)\b",
    r"\btrace\s+(?:the|through|back)\b",
    r"\bdebug\s+(?:the|this|why)\b",
    r"\bfind\s+all\s+(?:uses?|references?|calls?|invocations?)\b",
    r"\bmap\s+(?:the\s+)?(?:call\s+graph|dependency|module\s+structure)\b",
    r"\bcompare\s+(?:across|every|the\s+last)\b",
    r"\brefactor\s+(?:the|this)\s+\w+\s+to\b",
)

# Compiled once. re.IGNORECASE is the only flag used so behavior is
# deterministic across locales and Unicode case-fold.
_SUBAGENT_HINT_RE = re.compile(
    "|".join(SUBAGENT_HINT_PROMPTS),
    re.IGNORECASE,
)


# ---- Phase classification --------------------------------------------------


#: Per-phase keyword patterns, ordered by precedence (most specific first).
#: Each phase gets a `_rule_name` so the renderer can show *why* a phase was
#: chosen, and tests can pin behavior without depending on regex internals.
#:
#: Precedence order (top to bottom) is the contract:
#: 1. handoff       — explicit "hand off", "continue from"
#: 2. debugging     — bug/fix/error/stack-trace verbs
#: 3. review        — review/audit/critique verbs
#: 4. implementation — "implement", "add", "build" without prior "plan"
#: 5. planning      — "plan", "design", "architect" (incl. "let's plan")
#: 6. research      — "research", "investigate" (lowercase keyword only;
#:                    "investigate" doubles as a subagent hint)
#: 7. general       — fallback
_PHASE_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "handoff",
        "handoff_keyword",
        re.compile(
            r"\b(?:hand\s*off|handoff|continue\s+from\s+(?:previous|last))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "debugging",
        "debug_verb",
        re.compile(
            r"\b(?:debug|fix\s+the\s+bug|stack\s*trace|traceback|why\s+(?:is|does|did)|"
            r"repro(?:duce)?\s+(?:the|this))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "review",
        "review_verb",
        re.compile(
            r"\b(?:review|audit|critique|examine|assess|evaluate)\s+(?:the|this|my|our)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "implementation",
        "implement_verb",
        re.compile(
            r"\b(?:implement|build|create|write|add|introduce|wire\s+up)\s+"
            r"(?:a\s+|the\s+)?(?:\w+\s+){0,3}(?:function|class|module|hook|"
            r"endpoint|test|method|component|script|file)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "planning",
        "plan_verb",
        re.compile(
            r"\b(?:plan|design|architect|sketch|outline)\s+(?:the|this|out|a\s+)?\b|"
            r"\blet['']?s\s+plan\b",
            re.IGNORECASE,
        ),
    ),
    (
        "research",
        "research_verb",
        re.compile(
            r"\b(?:research|survey|explore|investigate)\s+(?:the|how|why|what|"
            r"existing|current)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class PhaseClassification:
    """Result of `classify_phase`. Frozen for hashability (tests)."""

    phase: str
    rule_name: str
    matched_text: str


def classify_phase(prompt: str) -> PhaseClassification:
    """Classify a user prompt into a controller phase.

    Returns the highest-precedence matching phase. Falls back to
    `("general", "fallback", "")` when no rule matches.

    Determinism: the rule list is a tuple, the patterns are pre-compiled,
    and `re.search` is anchored on the raw prompt. Two runs with the same
    input always produce the same `(phase, rule_name, matched_text)`.

    Empty/None prompts return the fallback. The function never raises.
    """
    if not prompt or not prompt.strip():
        return PhaseClassification(phase="general", rule_name="fallback", matched_text="")

    for phase, rule_name, pattern in _PHASE_RULES:
        m = pattern.search(prompt)
        if m:
            return PhaseClassification(
                phase=phase,
                rule_name=rule_name,
                matched_text=m.group(0),
            )

    return PhaseClassification(phase="general", rule_name="fallback", matched_text="")


# ---- Health evaluation -----------------------------------------------------


@dataclass(frozen=True)
class HealthAssessment:
    """Structured output of `evaluate_health`.

    `should_compact` and `should_start_fresh` mirror the booleans on
    `ContextHealth`; `hints` is a list of human-readable advisory lines
    suitable for the renderer to embed in the compact packet.
    """

    should_compact: bool
    should_start_fresh: bool
    hints: tuple[str, ...]


def evaluate_health(
    health: HealthLike,
    current_phase: str,
    previous_phase: str | None,
) -> HealthAssessment:
    """Evaluate context-health counters and emit advisory hints.

    Args:
        health: a `ContextHealth` dataclass, or a duck-typed mapping with
            the same keys (for callers that already have a dict).
        current_phase: the controller's current phase.
        previous_phase: the previous phase, or `None` on a fresh session.
            A phase change is itself a hint that the user has pivoted.

    Returns:
        `HealthAssessment` with booleans + ordered, deduped hint lines.

    Decision rules (deterministic, in order):
        1. `should_compact` ← `health.large_outputs >= LARGE_OUTPUTS_COMPACT`.
        2. `should_start_fresh` ← phase change AND `health.phase_turns`
           was nonzero before reset.
        3. Hint: phase-turns checkpoint if `phase_turns >= PHASE_TURNS_CHECKPOINT`
           OR `current_phase in FRESH_PHASE_CHECKPOINT_PHASES` after a change.
        4. Hint: large-output count when nonzero but below compact threshold.
    """
    # Accept either dataclass (Protocol) or Mapping[str, object]. The
    # `isinstance(health, Mapping)` check narrows the type so Pyright
    # accepts the `.get` access.
    if isinstance(health, Mapping):
        # Mapping fallback (e.g. raw policy.json['context_health'] dict)
        turn_count = int(health.get("turn_count", 0))  # type: ignore[arg-type]
        large_outputs = int(health.get("large_outputs", 0))  # type: ignore[arg-type]
        phase_turns = int(health.get("phase_turns", 0))  # type: ignore[arg-type]
    else:
        # Dataclass branch (Protocol-typed)
        turn_count = int(getattr(health, "turn_count", 0))
        large_outputs = int(getattr(health, "large_outputs", 0))
        phase_turns = int(getattr(health, "phase_turns", 0))

    hints: list[str] = []

    should_compact = large_outputs >= LARGE_OUTPUTS_COMPACT
    if should_compact:
        hints.append(
            f"{large_outputs} large outputs observed (>= {LARGE_OUTPUTS_COMPACT}); "
            "consider compact."
        )
    elif large_outputs > 0:
        hints.append(
            f"{large_outputs} large output(s) this phase; "
            f"compact advisory at {LARGE_OUTPUTS_COMPACT}."
        )

    phase_changed = previous_phase is not None and previous_phase != current_phase
    # Heuristic: if the previous phase was set AND the new phase_turns is 0
    # (just reset by `update_policy_state`), AND we crossed phases, the user
    # pivoted mid-flight — that's a fresh-start signal.
    should_start_fresh = phase_changed and phase_turns == 0 and turn_count > 0
    if should_start_fresh:
        hints.append(
            f"Phase changed from '{previous_phase}' to '{current_phase}'; "
            "consider starting fresh on the new phase."
        )

    if phase_turns >= PHASE_TURNS_CHECKPOINT:
        hints.append(
            f"Phase '{current_phase}' has run {phase_turns} turns "
            f"(>= {PHASE_TURNS_CHECKPOINT}); consider transitioning."
        )
    elif (
        phase_turns > 0
        and current_phase in FRESH_PHASE_CHECKPOINT_PHASES
    ):
        hints.append(
            f"Long-running phase '{current_phase}' ({phase_turns} turns); "
            "checkpoint progress soon."
        )

    # Dedupe while preserving order (cheap, deterministic)
    seen: set[str] = set()
    deduped: list[str] = []
    for h in hints:
        if h not in seen:
            seen.add(h)
            deduped.append(h)

    return HealthAssessment(
        should_compact=should_compact,
        should_start_fresh=should_start_fresh,
        hints=tuple(deduped),
    )


# ---- Subagent recommendation ----------------------------------------------


def recommend_subagent(prompt: str) -> bool:
    """Return True if the prompt looks like a multi-step investigation.

    v1 contract: pure regex match against `SUBAGENT_HINT_PROMPTS`. No LLM.
    Returns False for empty/None prompts. The result is advisory only —
    the controller never auto-dispatches, and no follow-up action file is
    written (per the v1 guardrail).
    """
    if not prompt or not prompt.strip():
        return False
    return _SUBAGENT_HINT_RE.search(prompt) is not None


# ---- Re-exports -----------------------------------------------------------

__all__ = [
    "FRESH_PHASE_CHECKPOINT_PHASES",
    "HealthAssessment",
    "HealthLike",
    "LARGE_OUTPUTS_COMPACT",
    "PHASE_TURNS_CHECKPOINT",
    "PhaseClassification",
    "SUBAGENT_HINT_PROMPTS",
    "classify_phase",
    "evaluate_health",
    "recommend_subagent",
]

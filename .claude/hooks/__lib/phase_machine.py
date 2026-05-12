# Phase State Machine — explicit development lifecycle phase tracking.
from __future__ import annotations

from typing import Optional

from __lib.v2_config import (
    CONTENT_MARKER_WEIGHT,
    EVIDENCE_WEIGHT,
    TURN_MODE_WEIGHT,
)

# Valid phase labels
VALID_PHASES = frozenset({
    "exploration",
    "design",
    "implementation",
    "verification",
    "reporting",
    "complete",
    "superseded",
})

# Permitted transitions from each phase
VALID_TRANSITIONS: dict[str, list[str]] = {
    "exploration": ["design", "implementation", "exploration", "superseded"],
    "design": ["implementation", "exploration", "design", "superseded"],
    "implementation": ["verification", "implementation", "design", "superseded"],
    "verification": ["reporting", "verification", "implementation", "superseded"],
    "reporting": ["complete", "verification", "reporting", "superseded"],
    "complete": [],
    "superseded": [],
}

# Design-signal phrases that indicate design-phase content
_DESIGN_SIGNALS = frozenset({
    "architecture",
    "design tradeoff",
    "approach would be",
    "high-level",
    "structure should",
    "layered design",
    "component diagram",
    "adrs",
    "architecture decision",
})

# Code-signal fragments that indicate implementation-phase content
_CODE_SIGNALS = frozenset({
    "def ",
    "class ",
    "async def",
    "if __name__",
    "import ",
    "```python",
    "```py",
})

# Turn modes that map to exploration/control
_EXPLORATION_MODES = frozenset({"control", "exploration"})
_ANALYSIS_MODES = frozenset({"analysis", "final-answer"})


def can_transition(current_phase: str, next_phase: str) -> bool:
    """Return True if transitioning from current_phase to next_phase is valid."""
    if current_phase == next_phase:
        return True  # No-op is always valid
    return next_phase in VALID_TRANSITIONS.get(current_phase, [])


def is_terminal(phase: str) -> bool:
    """Return True if phase is terminal (no further transitions allowed)."""
    return phase in ("complete", "superseded")


def should_enforce_outputs(phase: str, task_class: str) -> bool:
    """Return True if required outputs should be enforced in this phase.

    Rules:
    - exploration/design: never enforce
    - implementation: enforce fix+tests for bug_fix/implementation/refactor
    - verification: enforce verification_commands
    - reporting: enforce all required outputs
    - architecture_recommendation: only enforce in reporting phase
    """
    if phase in ("exploration", "design", "complete", "superseded"):
        return False

    implementation_classes = frozenset({
        "bug_fix", "implementation", "refactor", "bug_diagnosis",
    })

    if phase == "implementation":
        return task_class in implementation_classes

    if phase == "verification":
        return task_class in implementation_classes

    # reporting: enforce all task classes
    return True


def infer_phase_from_context(
    context: dict,
    evidence: dict,
    current_phase: Optional[str] = None,
) -> str:
    """Infer the current development phase from context, evidence, and turn mode.

    Priority (highest to lowest):
    1. Evidence (files modified → implementation; tests run → verification)
    2. Turn mode (control/exploration → exploration; analysis/final-answer → reporting)
    3. Content markers (design keywords → design; code → implementation)

    Args:
        context: Dict with keys: response, turn_mode, user_prompt
        evidence: Evidence dict with keys: files_modified, tests_run, etc.
        current_phase: Optional current phase for tie-breaking

    Returns:
        Inferred phase string.
    """
    # --- Layer 1: Evidence (strongest signal) ---
    files_modified = evidence.get("files_modified", [])
    tests_run = evidence.get("tests_run", [])
    verification_commands = evidence.get("verification_commands_executed", [])
    code_generated = evidence.get("code_generated", False)
    design_artifacts = evidence.get("design_artifacts", [])

    if files_modified or code_generated:
        return "implementation"

    if tests_run or verification_commands:
        return "verification"

    if design_artifacts:
        return "design"

    # --- Layer 2: Turn mode (second priority) ---
    turn_mode = context.get("turn_mode", "")
    if turn_mode in _EXPLORATION_MODES:
        return "exploration"

    if turn_mode in _ANALYSIS_MODES:
        return "reporting"

    # --- Layer 3: Content markers (last resort) ---
    response = context.get("response", "").lower()
    prompt = context.get("user_prompt", "").lower()
    combined = response + " " + prompt

    if any(signal in combined for signal in _DESIGN_SIGNALS):
        return "design"

    if any(signal in combined for signal in _CODE_SIGNALS):
        return "implementation"

    # --- Fallback ---
    # Prefer implementation over design for migrated contracts (conservative)
    if current_phase and current_phase not in ("exploration", "design"):
        return current_phase
    return "exploration"


def format_phase_history(history: list[dict]) -> str:
    """Format phase history as a readable string for telemetry/debug."""
    lines = []
    for entry in history:
        phase = entry.get("phase", "?")
        entered = entry.get("entered_at", "")
        exited = entry.get("exited_at", "now")
        turns = entry.get("turns", 0)
        lines.append(f"  {phase}: {entered} → {exited} ({turns} turns)")
    return "\n".join(lines) if lines else "  (no history)"


# ---------------------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Test valid transitions
    assert can_transition("exploration", "design")
    assert can_transition("design", "implementation")
    assert can_transition("implementation", "verification")
    assert can_transition("verification", "reporting")
    assert can_transition("reporting", "complete")
    assert can_transition("exploration", "exploration")  # no-op

    # Test invalid transitions
    assert not can_transition("reporting", "exploration")
    assert not can_transition("complete", "exploration")
    assert not can_transition("complete", "reporting")

    # Test enforcement rules
    assert not should_enforce_outputs("exploration", "bug_fix")
    assert not should_enforce_outputs("design", "bug_fix")
    assert should_enforce_outputs("implementation", "bug_fix")
    assert should_enforce_outputs("reporting", "architecture_recommendation")
    assert not should_enforce_outputs("complete", "bug_fix")

    # Test phase inference
    ctx = {"response": "I fixed the bug", "turn_mode": "final-answer"}
    ev = {"files_modified": ["Stop.py"]}
    assert infer_phase_from_context(ctx, ev) == "implementation"

    ctx2 = {"response": "The architecture is...", "turn_mode": "exploration"}
    ev2 = {"design_artifacts": ["arch.md"]}
    assert infer_phase_from_context(ctx2, ev2) == "design"

    ctx3 = {"response": "Tests pass now", "turn_mode": "analysis"}
    ev3 = {"tests_run": ["test_task_contract.py"]}
    assert infer_phase_from_context(ctx3, ev3) == "verification"

    print("All phase_machine self-tests passed.")
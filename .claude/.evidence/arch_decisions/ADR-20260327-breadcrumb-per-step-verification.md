# ADR-20260327-breadcrumb-per-step-verification: Per-Step Breadcrumb Verification

**Status:** Implemented
**Date:** 2026-03-27
**Implementation Date:** 2026-03-28
**Context:** Breadcrumb trail verification only fires at Stop hook (end of workflow), missing mid-workflow enforcement opportunity

## Decision

**Don't register the orphan `StopHook_breadcrumb_verifier.py`. Instead, create a PreToolUse breadcrumb gate that verifies step completion before each tool execution.**

### Core Problem

`StopHook_breadcrumb_verifier.py` exists but is **NOT registered** in `Stop_router.py HOOK_SEQUENCE` — it's an orphan hook that never fires.

Even if registered, Stop verification is too late: by the time Stop fires, the model has already wasted tokens generating a response. PreToolUse verification blocks **before** the next tool, preventing wasted work.

## Architecture

| Component | Status | File | Purpose |
|-----------|--------|------|---------|
| PostToolUse auto-tracking | ✅ Active | `posttooluse/breadcrumb_tracker_hook.py` | Tracks steps after each tool |
| Breadcrumb infrastructure | ✅ Active | `skill_guard.breadcrumb` | Terminal-scoped state management |
| Stop verification | ❌ Orphan | `StopHook_breadcrumb_verifier.py` | Only checks at end (too late) |
| **PreToolUse verification** | **NEW** | **`PreToolUse_breadcrumb_gate.py`** | **Verifies before next tool** |

## Decision: Why PreToolUse Over Stop

| Aspect | Stop Hook | PreToolUse Gate |
|--------|----------|-----------------|
| Timing | End of workflow | Before each tool |
| Waste | Tokens already spent | Tokens preserved |
| Blocking | After prose generated | Before tool executes |
| Effectiveness | Catches incomplete at end | Prevents wrong sequence |

## Implementation

### New Hook: `PreToolUse_breadcrumb_gate.py`

**Location:** `P:/.claude/hooks/PreToolUse_breadcrumb_gate.py`

**Logic:**
1. Allow `Skill` tool always (workflow initiation)
2. Get current skill context from breadcrumb state
3. Get expected next step from workflow definition
4. Validate current tool is valid progression from last completed step
5. Block if invalid progression

### Key Interfaces (from `skill_guard.breadcrumb`)

```python
from skill_guard.breadcrumb import (
    get_breadcrumb_trail,      # Get current trail state
    get_expected_next_step,     # From workflow_steps definition
    is_valid_progression,       # Check tool/step compatibility
)

def run(data: dict) -> dict:
    tool_name = data.get("tool_name", "")

    # Always allow Skill tool (workflow initiation)
    if tool_name == "Skill":
        return {"continue": True}

    # Get current skill context
    skill = get_skill_from_intent()
    if not skill:
        return {"continue": True}

    # Get breadcrumb state
    trail = get_breadcrumb_trail(skill)
    completed = trail.get("completed_steps", [])
    expected_next = get_expected_next_step(skill, completed)

    # Check if current tool is valid next step
    if is_valid_progression(tool_name, expected_next):
        return {"continue": True}

    # Block - must complete expected step first
    return {
        "continue": False,
        "reason": f"Complete '{expected_next}' before using {tool_name}"
    }
```

## Multi-Terminal Safety

Uses terminal-scoped breadcrumb state (already implemented in `skill_guard.breadcrumb` via `detect_terminal_id()`). No cross-terminal contamination.

## Registration

Add to `PreToolUse.py` UNIVERSAL hooks list:
```python
from PreToolUse_breadcrumb_gate import run as breadcrumb_gate_run
```

## What to Delete

1. `StopHook_breadcrumb_verifier.py` — Orphan, provides no value (never registered) ✅ DELETED
2. Documentation of orphan in `P:/.claude/hooks/CLAUDE.md` — Not found, no action needed

## Implementation Notes

### PreToolUse_breadcrumb_gate.py

**Location:** `P:/.claude/hooks/PreToolUse_breadcrumb_gate.py`

**Key functions:**
- `_get_step_kind_from_tool()` - Maps tool names to step kinds (research, requirements, tdd, etc.)
- `_get_expected_next_step()` - Finds first incomplete step from workflow_steps
- `_is_valid_progression()` - Validates tool is appropriate for expected step
- `_get_skill_from_context()` - Gets current skill from breadcrumb trail state

**Logic:**
1. Allow `Skill` tool always (workflow initiation)
2. Get current skill context from breadcrumb state
3. Get expected next step from workflow_steps
4. Validate current tool is valid progression from last completed step
5. Block if invalid progression (advisory mode by default)

**Registration:** Added to PreToolUse.py UNIVERSAL hooks list (line 573)

**Configuration:**
- `BREADCRUMB_GATE_ENABLED` (default: true)
- `BREADCRUMB_GATE_MODE` (default: advisory) - advisory or block
- `BREADCRUMB_GATE_ADVISORY_ONLY_LIST` - comma-separated skills to always advisory

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Reliability | Prevents wasted work mid-workflow | Adds latency per tool (estimated <5ms) |
| Maintainability | Single verification point | New hook to test |
| Usability | Clearer step requirements | Potential blocking friction |

## Consequences

- **Positive:** Workflow enforcement happens at decision point, not after
- **Negative:** Model must follow declared workflow steps more strictly
- **Mitigation:** Advisory mode (warn, don't block) for initial deployment

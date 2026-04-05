# ADR-20260323: Reduce Hook Friction by Disabling Redundant Stop Bypass Detection

**Status:** Implemented
**Date:** 2026-03-23
**Context:** Three-layer skill-first enforcement is creating false positive friction. The Stop hook fires "SLASH COMMAND IGNORED" even when PreToolUse Layer 0 enforcement is already active and Skill was called correctly.

---

## Problem

The skill-first enforcement system has three independent layers:

| Layer | Hook | Mechanism |
|-------|------|-----------|
| Layer 1 | `skill_enforcer.py` (UserPromptSubmit) | Injects INSTRUCTION format |
| Layer 0 | `PreToolUse_skill_pattern_gate.py` | Blocks tools until Skill called |
| Layer 2 | `StopHook_skill_execution_gate.py` | Bypass detection post-response |

**Issue**: Stop hook bypass detection runs independently from PreToolUse. When PreToolUse Layer 0 enforcement is active (for skills with `workflow_steps`), the Stop check is **redundant** but still fires, causing false positive blocks.

**Evidence**: On 2026-03-23, `/arch` was invoked, `Skill("arch")` was called as the first tool, and the Stop hook still fired "SLASH COMMAND IGNORED."

---

## Decision

Modify `StopHook_skill_execution_gate.py` to skip bypass detection when `pending_command_intent` state exists for the skill (indicating PreToolUse Layer 0 enforcement was active).

---

## Rationale

PreToolUse Layer 0 already guarantees Skill-first for skills with `workflow_steps`. The Stop bypass detection is redundant for those cases and creates false positive friction without adding safety value.

The Stop hook's own documentation describes it as a "safety net for when PreToolUse failed to block." If PreToolUse succeeded (state exists), the safety net is not needed.

---

## Implementation

In `StopHook_skill_execution_gate.py`, before the bypass detection check in `_run_bypass_detection()`:

```python
# Check if PreToolUse Layer 0 enforcement was active for this skill
pending_intent = _read_pending_intent(terminal_id)
if pending_intent and pending_intent.get("skill") == slash_cmd:
    # PreToolUse already enforced Skill-first - skip redundant Stop bypass detection
    return None
```

---

## Multi-Terminal Safety

- `pending_command_intent` state is terminal-scoped via `terminal_id`
- No cross-terminal contamination

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Operational Excellence | Removes false positive friction | None |
| Reliability | Preserves genuine bypass detection | None |
| Complexity | Minimal (one conditional check) | None |

---

## Edge Cases

1. **Skills without `workflow_steps`**: Stop bypass detection still fires (needed, no PreToolUse enforcement for these)
2. **State file missing**: Falls through to existing bypass detection (correct behavior)
3. **Colon syntax** (`/skill:subskill`): May need separate handling; test after fix

---

## Consequences

- **Positive**: Eliminates false positive "SLASH COMMAND IGNORED" blocks for skills with `workflow_steps`
- **Negative**: Slight added coordination coupling between hooks (mitigated by using existing state file)

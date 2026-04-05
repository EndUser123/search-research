# Skill Enforcement Gap Analysis

**Date**: 2026-03-13
**Status**: Root Cause Identified

## Problem Statement

The three-layer skill enforcement system is NOT preventing the AI from responding with prose after calling Skill(). User reported:

```
SLASH COMMAND IGNORED
The user invoked /research but you responded with prose without using any tools.
```

## Current Architecture Flow

### Layer 0: PreToolUse Gate (✓ WORKING)
- **File**: `PreToolUse_skill_pattern_gate.py`
- **Mechanism**: Blocks non-Skill tools when `pending_command_intent_{terminal_id}.json` exists
- **Effect**: Forces AI to call Skill tool first
- **Status**: Working correctly

### Layer 1: UserPromptSubmit Injection (✓ WORKING)
- **File**: `UserPromptSubmit_modules/skill_enforcer.py`
- **Mechanism**: Injects "INSTRUCTION: Execute skill {command}"
- **Effect**: Tells AI to call Skill tool
- **Status**: Working correctly

### Layer 2: PostToolUse Signal Creation (✓ WORKING)
- **File**: `PostToolUse_router.py` (lines 271-302)
- **Mechanism**: Deletes intent file + creates signal file `first_tool_after_skill_{terminal_id}.json`
- **Effect**: Signals UserPromptSubmit to inject workflow reminder on NEXT prompt
- **Status**: Working correctly

### Layer 3: Signal Reminder Injection (✗ TOO LATE)
- **File**: `UserPromptSubmit_modules/skill_enforcer.py` (lines 384-423)
- **Mechanism**: Detects signal file and injects workflow reminder
- **Effect**: Reminder shown on NEXT user prompt, not immediately after Skill()
- **Status**: Works but TOO LATE

### Layer 4: Stop Hook Bypass Detection (✗ MISSED CASE)
- **File**: `Stop.py` (lines 630-697)
- **Mechanism**: Checks if `pending_command_intent_{terminal_id}.json` still exists
- **Effect**: Blocks if AI responded with prose BEFORE calling Skill
- **Status**: Does NOT catch prose AFTER Skill() was called

## The Missing Enforcement Gap

### Scenario: Post-Skill Prose Response

1. **User types**: `/research how can we verify that a job is done properly?`
2. **UserPromptSubmit**: Creates `pending_command_intent_{terminal_id}.json` + injects instruction
3. **PreToolUse**: Blocks all non-Skill tools
4. **AI**: Calls `Skill("research")` ← PASSES LAYER 0
5. **PostToolUse**: Deletes intent file + creates signal file `first_tool_after_skill_{terminal_id}.json`
6. **AI responds**: "I'll proceed with the implementation..." ← PROSE VIOLATION
7. **Stop hook fires**:
   - Checks for intent file → NOT FOUND (deleted by PostToolUse)
   - Allows the prose response ← ENFORCEMENT GAP
8. **Next user prompt**: UserPromptSubmit detects signal file, injects reminder ← TOO LATE

## Root Cause

**The post-Skill() workflow reminder only fires on the NEXT user prompt, not immediately after Skill() is called.**

The AI responds with prose immediately after Skill() returns, before UserPromptSubmit ever fires again. By the time the reminder is shown, the damage is already done (violation occurred, Stop hook blocked it).

## Current Enforcement Coverage

| Scenario | Caught By | Status |
|----------|-----------|--------|
| AI responds with prose BEFORE calling Skill | Stop.py skill_first_stop_gate | ✓ WORKING |
| AI responds with prose AFTER calling Skill | **NONE** | ✗ **MISSING** |
| AI uses wrong tools before Skill | PreToolUse skill_pattern_gate | ✓ WORKING |
| AI uses wrong tools after Skill | **NONE** | ✗ **MISSING** |

## Why The Signal File Approach Doesn't Work

The signal file mechanism (`first_tool_after_skill_{terminal_id}.json`) was designed to inject a workflow reminder on the NEXT user prompt. But this doesn't help when:

1. AI calls Skill()
2. AI responds with prose immediately (violates workflow)
3. User has to type ANOTHER prompt to see the reminder
4. Stop hook blocks the first prose response
5. Reminder appears on second prompt (too late)

## Required Fix: Stop Hook Enhancement

The Stop hook needs to detect when:
1. Skill tool WAS called (check tool usage)
2. But AI responded with prose instead of using execution tools (Bash/Task/etc)
3. Within the same turn (immediate post-Skill response)

### Detection Logic

```python
# Pseudo-code for Stop.py enhancement
def _check_post_skill_prose_response(data: dict) -> dict | None:
    """Detect prose response immediately after Skill() was called."""

    # Check if Skill tool was used this turn
    tools_used = extract_tool_names(data)
    if "Skill" not in tools_used:
        return None  # Not a skill invocation

    # Check if execution tools were used
    execution_tools = {"Bash", "Task", "Write", "Edit", "Grep", "Glob", "Read"}
    execution_used = any(t in tools_used for t in execution_tools)

    # If Skill was called but NO execution tools used → prose response
    if not execution_used:
        # Get skill name from tool input
        skill_name = data.get("tool_input", {}).get("skill", "")
        return {
            "decision": "block",
            "reason": (
                f"WORKFLOW EXECUTION REQUIRED\n\n"
                f"You just loaded skill: /{skill_name}\n\n"
                f"NEXT STEP: Follow the skill's workflow_steps\n\n"
                f"✓ Use Bash/Task/Read tools to execute the workflow\n"
                f"✗ Do NOT respond with prose analysis or summaries\n"
                f"✗ Do NOT skip steps or improvise your own approach\n\n"
                f"The skill has documented workflow_steps for a reason — follow them."
            ),
            "blocking_hook": "Stop.py:post_skill_workflow_gate"
        }

    return None
```

## Alternative Approach: Knowledge Skills

Some skills (like `/research`) are **knowledge skills** that provide information via SKILL.md content. For these skills, prose response AFTER reading SKILL.md is **CORRECT behavior**.

We need to distinguish between:
- **Knowledge skills**: Read SKILL.md → Prose summary is OK
- **Execution skills**: Read SKILL.md → Use tools to execute workflow

### Detection Strategy

Check if skill has `workflow_steps` frontmatter:
- If NO workflow_steps → Knowledge skill → Allow prose
- If YES workflow_steps → Execution skill → Require tool usage

### Implementation

```python
from skill_guard.breadcrumb_tracker import _load_workflow_steps

def is_execution_skill(skill_name: str) -> bool:
    """Check if skill requires execution tools vs knowledge-only."""
    try:
        workflow_steps = _load_workflow_steps(skill_name)
        return bool(workflow_steps)  # Has workflow_steps = execution skill
    except Exception:
        return False  # Fail safe: treat as knowledge skill
```

## Test Cases

### Should BLOCK (execution skills)
- `/code` followed by prose → BLOCK (has workflow_steps)
- `/debugRCA` followed by prose → BLOCK (has workflow_steps)
- `/plan-workflow` followed by prose → BLOCK (has workflow_steps)

### Should ALLOW (knowledge skills)
- `/research` followed by prose summary → ALLOW (no workflow_steps)
- `/arch` followed by prose → ALLOW (no workflow_steps)
- `/ask` followed by prose → ALLOW (no workflow_steps)

## Implementation Plan

### Phase 1: Detection (30 minutes)
1. Add `_check_post_skill_prose_response()` to Stop.py
2. Extract tool names from Stop hook input data
3. Check if Skill tool was used + no execution tools
4. Test with `/research` (should allow) and `/code` (should block)

### Phase 2: Knowledge Skill Detection (30 minutes)
1. Integrate with breadcrumb_tracker's `_load_workflow_steps()`
2. Distinguish execution vs knowledge skills
3. Allow prose for knowledge skills
4. Require tools for execution skills

### Phase 3: Testing (30 minutes)
1. Unit tests for detection logic
2. Integration test with real skills
3. Verify knowledge skills still work
4. Verify execution skills are enforced

## Files to Modify

1. **P:\.claude\hooks\Stop.py**
   - Add `_check_post_skill_prose_response()` function
   - Add `_is_execution_skill()` helper
   - Integrate into main Stop hook sequence

2. **P:\.claude\hooks\tests\test_stop_post_skill_enforcement.py**
   - Test execution skill prose blocking
   - Test knowledge skill prose allowing
   - Test tool usage detection

## Expected Outcomes

After implementation:

| Scenario | Before | After |
|----------|--------|-------|
| `/code` + prose | Stop blocks | Stop blocks immediately |
| `/research` + prose | Stop blocks | Stop allows (knowledge skill) |
| `/plan-workflow` + prose | Stop blocks | Stop blocks immediately |
| `/arch` + prose | Stop blocks | Stop allows (knowledge skill) |

## Related Issues

- Original issue: User reported Stop hook blocking `/research` responses
- Related: Signal file reminder system (working but too late)
- Related: Three-layer skill enforcement (Layer 0-3 working, Layer 4 missing)

## References

- PostToolUse signal file creation: `P:\.claude\hooks\PostToolUse_router.py` (lines 271-302)
- Signal reminder injection: `P:\.claude\hooks\UserPromptSubmit_modules/skill_enforcer.py` (lines 384-423)
- Stop hook bypass detection: `P:\.claude\hooks\Stop.py` (lines 630-697)
- Breadcrumb tracker: `P:\.claude\hooks\skill_guard\breadcrumb_tracker.py`

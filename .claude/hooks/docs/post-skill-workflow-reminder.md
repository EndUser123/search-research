# Post-Skill() Workflow Reminder Enhancement

**Implementation Date:** 2026-03-13
**Status:** Implemented and tested

## Problem

AI responds with prose after calling `Skill()` instead of following the skill's workflow_steps with Bash/Task/Read tools. The existing three-layer enforcement (Layer 0: PreToolUse block, Layer 1: UserPromptSubmit injection, Layer 2: Stop detection) all work correctly, but the AI forgets to execute workflows after reading skill documentation.

## Solution

Added **post-Skill() workflow reminder** that injects a clear directive on the FIRST prompt after `Skill()` is called.

### Architecture

```
User types: /plan-workflow review
    ↓
UserPromptSubmit: Store intent file + inject "INSTRUCTION: Execute skill"
    ↓
PreToolUse: Block tools until Skill() called
    ↓
AI calls: Skill("plan-workflow")
    ↓
PostToolUse: Clear intent file + WRITE SIGNAL FILE (first_tool_after_skill_{terminal}.json)
    ↓
User NEXT prompt: "Running verification..."
    ↓
UserPromptSubmit: DETECT SIGNAL FILE → Inject workflow reminder → DELETE SIGNAL FILE
    ↓
AI sees: "⚠️ WORKFLOW EXECUTION REQUIRED - Use Bash/Task/Read tools to execute workflow"
```

### Implementation

**File 1: PostToolUse_router.py** (lines 271-302)
- Modified `_clear_pending_skill_intent()` to write signal file when clearing intent
- Signal file contains: `{skill, timestamp, terminal_id}`
- Format: `first_tool_after_skill_{terminal_id}.json`

**File 2: skill_enforcer.py** (lines 367-440)
- Added signal file detection at start of `skill_enforcement_hook()`
- If signal found: inject workflow reminder + delete signal (one-time)
- Priority 0.5 (high) to ensure early visibility

### Reminder Text

```
═══════════════════════════════════════════════════════════════
⚠️  WORKFLOW EXECUTION REQUIRED
═══════════════════════════════════════════════════════════════

You just loaded skill: /{skill_name}

NEXT STEP: Follow the skill's workflow_steps (from SKILL.md)

✓ Use Bash/Task/Read tools to execute the workflow
✗ Do NOT respond with prose analysis or summaries
✗ Do NOT skip steps or improvise your own approach

The skill has documented workflow_steps for a reason — follow them.

═══════════════════════════════════════════════════════════════
```

### Signal File Lifecycle

1. **Created:** PostToolUse when Skill() succeeds and intent is cleared
2. **Detected:** UserPromptSubmit on next prompt (signal file exists)
3. **Deleted:** UserPromptSubmit after reading signal (one-time reminder)
4. **Fallback:** Temp directory if hooks/state unavailable

### Terminal Isolation

Signal files use terminal-scoped naming (same as intent files):
- `first_tool_after_skill_{terminal_id}.json`
- Prevents cross-talk between concurrent terminal sessions
- Auto-cleanup by session_data_retention.py

## Testing

All existing tests pass:
```bash
pytest P:/.claude/hooks/tests/test_skill_first_enforcement.py -v
# 13 passed in 0.44s
```

## Behavior Change

**Before:**
1. User types `/plan-workflow review`
2. AI calls `Skill("plan-workflow")`
3. AI responds: "I'll proceed with implementation..." ← PROSE VIOLATION
4. Stop hook catches and blocks

**After:**
1. User types `/plan-workflow review`
2. AI calls `Skill("plan-workflow")`
3. **PostToolUse writes signal file**
4. User types "Running verification..."
5. **UserPromptSubmit detects signal, injects reminder, deletes signal**
6. AI sees workflow reminder and uses tools

## Future Enhancements

**Option 2: Streak-Based Escalation** (not implemented)
Track repeated offenses and increase blocking severity:
- 1st offense: Advisory reminder (current)
- 2nd offense: Strong warning
- 3rd+ offense: Hard block until tool usage

**Option 3: Strip Prose Capability** (not implemented)
Temporarily disable prose generation after Skill() call until workflow tool usage detected.

## Related Files

- `P:/.claude/hooks/PostToolUse_router.py` - Signal file creation
- `P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py` - Signal detection + reminder injection
- `P:/.claude/hooks/PreToolUse.py` - Layer 0 enforcement (unchanged)
- `P:/.claude/hooks/Stop.py` - Layer 2 bypass detection (unchanged)

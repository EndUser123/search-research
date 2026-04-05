# Skill-First Gate Deadlock Fixes

**Date**: 2026-03-13
**Status**: ✅ Complete
**Related Issues**: pre-mortem deadlock, KNOWLEDGE_SKILLS drift

## Problem Summary

The `/pre-mortem` command was experiencing a deadlock where:
1. `Skill("pre-mortem")` was called successfully
2. Immediately followed by a Bash call that was blocked with:
   ```
   ⛔ SKILL-FIRST GATE: You typed /pre-mortem but haven't called Skill("pre-mortem") yet.
   ```

Three additional friction points were identified during investigation.

## Root Causes

1. **Fixes 1 & 2**: Already implemented in previous work
   - `PreToolUse_workflow_steps_gate.py` line 263: `skill_loaded` check
   - `PreToolUse_skill_pattern_gate.py` lines 522-545: Stateless gate validation

2. **Fix 3**: Classification conflict
   - `pre-mortem` was in `KNOWLEDGE_SKILLS` but has `workflow_steps` declared
   - The Stop hook enforces on `pre-mortem`, but PreToolUse exempted it
   - Inconsistent treatment across hooks

3. **Fix 4**: Maintenance hazard
   - `KNOWLEDGE_SKILLS` defined in 3 places with different contents
   - Every new knowledge skill required three separate edits
   - Definitions drifted over time

## Changes Made

### Fix 3: Remove pre-mortem from KNOWLEDGE_SKILLS

**File**: `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py`

**Change**: Removed `"pre-mortem"` from `KNOWLEDGE_SKILLS` set (line 177)

**Rationale**: `pre-mortem` declares `workflow_steps` in its SKILL.md frontmatter. The Stop hook already enforces it as an execution target. This makes PreToolUse consistent with Stop hook behavior.

### Fix 4: Centralize KNOWLEDGE_SKILLS

**New File**: `P:\.claude\hooks\__lib\hook_constants.py`

**Created centralized constants module** with:
```python
KNOWLEDGE_SKILLS = frozenset({
    "standards", "constraints", "techniques", "evidence-tiers",
    "constitutional-patterns", "cognitive-frameworks", "prompt_refiner",
    "library-first", "solo-dev-authority", "data-safety-vcs",
    "chs", "cks", "analyze", "discover", "ask",
    "reflect", "s",
})
```

**Note**: `pre-mortem` is explicitly NOT in this set (see module docstring for rationale).

**Updated three hooks to import centralized constants**:

1. **PreToolUse_skill_pattern_gate.py** (line 58)
   - Added: `from __lib.hook_constants import KNOWLEDGE_SKILLS`
   - Removed: Local KNOWLEDGE_SKILLS definition (lines 172-180)

2. **StopHook_skill_execution_gate.py** (line 66)
   - Added: `from __lib.hook_constants import KNOWLEDGE_SKILLS`
   - Removed: Local KNOWLEDGE_SKILLS definition (lines 298-302)

3. **PreToolUse_skill_first_gate.py** (lines 30-48)
   - Added: Import from `__lib.hook_constants`
   - Combined: BUILTIN_COMMANDS + LIGHTWEIGHT_COMMANDS + KNOWLEDGE_SKILLS
   - Removed: Duplicate knowledge skill definitions

## Verification

### Import Tests
All import tests pass:
```
Test 1: Importing hook_constants...
  ✓ KNOWLEDGE_SKILLS imported: 17 skills

Test 2: Verifying pre-mortem exclusion...
  ✓ pre-mortem correctly excluded from KNOWLEDGE_SKILLS

Test 3: Verifying key skills are included...
  ✓ All expected knowledge skills present
```

### Expected Behavior After Fixes

When user types `/pre-mortem`:
1. UserPromptSubmit stores pending_command_intent
2. Claude calls `Skill("pre-mortem")`
3. PreToolUse_workflow_steps_gate sets `skill_loaded=True`
4. PreToolUse_skill_pattern_gate sees `skill_loaded=True` and allows all tools
5. No deadlock occurs

## Testing Recommendations

1. **Manual Test**: Run `/pre-mortem` and verify it proceeds without deadlock
2. **Regression Test**: Verify other workflow skills (`/code`, `/verify`, `/trace`) still work
3. **Knowledge Skills**: Verify pure knowledge skills (`/standards`, `/constraints`) still prose-only

## Related Documentation

- `P:\.claude\hooks\CLAUDE.md` - Skill enforcement enhancement (Layer 0)
- `P:\.claude\arch_decisions\2026-03-12_skill-first-gate-efficiency.md` - Original stateless gate implementation

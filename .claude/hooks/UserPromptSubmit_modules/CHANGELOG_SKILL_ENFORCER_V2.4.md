# Skill Enforcer v2.4 - Revert to Directive-Only Enforcement

## Date
2026-03-11

## Summary
Reverted v2.3 pre-execution injection. Skill enforcer now forces actual Skill() tool calls via directive approach instead of injecting SKILL.md content directly.

## Problem
v2.3 implementation (2026-02-17) did BOTH:
1. Told AI: "You MUST call Skill() first"
2. BUT ALSO: Injected full SKILL.md content directly

This created a conflict - the AI was told to call Skill() but the content was already injected, so it might skip the actual tool call. This defeated the purpose of the Skill tool as a proper tool invocation mechanism.

**User feedback**: "We are supposed to see the claude skill tool being invoked."

## Solution
Removed pre-execution injection (lines 320-334). Now uses ONLY directive approach:
1. Injects EVALUATION_DIRECTIVE: "You MUST call Skill() first"
2. Injects SLASH_EXECUTION_LANE: Reinforces Skill() requirement
3. AI must explicitly call Skill tool to load skill content

## Behavior Change

**Before (v2.3)**:
```
User types: /gto
    ↓
skill_enforcer: "You MUST call Skill('gto') first"
    ↓
skill_enforcer ALSO: [injects full SKILL.md content]
    ↓
AI sees content already there, might skip Skill() call
```

**After (v2.4)**:
```
User types: /gto
    ↓
skill_enforcer (priority 1.0): "You MUST call Skill('gto') first"
    ↓
breadcrumb_init (priority 7.0): Shows "**🔧 Invoking Skill** /gto"
    ↓
AI calls: Skill("gto") ← Actual tool invocation
    ↓
Skill tool loads and executes /gto skill
```

## Changes Made

### File: `P:\.claude\hooks\UserPromptSubmit_modules\skill_enforcer.py`

**Removed**:
- `SKILL_INJECTION_TEMPLATE` constant (lines 39-47)
- Pre-execution injection logic (lines 320-334)
- Docstring reference to v2.3 approach

**Modified**:
- `build_command_context()` function now uses directive-only approach
- Updated docstring to reflect directive-only enforcement

**Kept**:
- `EVALUATION_DIRECTIVE` constant (lines 284-292)
- `SLASH_EXECUTION_LANE` constant (lines 24-37)

## Benefits
- **Proper tool invocation**: Skills are now invoked via Skill tool, not content injection
- **Observable behavior**: Users can see Skill("gto") in tool use list
- **Consistent architecture**: All skills use same invocation mechanism
- **No bypass**: AI cannot skip Skill tool call since content is not pre-injected

## Testing
Created test: `P:\.claude\hooks\tests\test_skill_enforcer_fix.py`

**Test results**:
```
✓ Contains EVALUATION_DIRECTIVE: True
✓ Contains SLASH_EXECUTION_LANE: True
✗ Contains pre-execution injection: False
✓ Forces Skill() tool call: True
```

## Backward Compatibility
This is a **behavioral change** that affects how skills are invoked:
- Skills will now be called via Skill tool explicitly
- This is the intended architecture (v2.3 was an experiment)
- No breaking changes to skill definitions or SKILL.md files

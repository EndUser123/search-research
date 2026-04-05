# Skill Pattern Gate: Architectural Fix

**Date**: 2026-03-06
**Issue**: False positive bug + architectural flaw
**Status**: ✅ FIXED

## Problem Statement

The skill pattern gate was blocking ALL bash commands when knowledge skills like "pre-mortem" were loaded, due to two architectural flaws:

1. **Brittle hardcoded classification**: Skills manually added to `KNOWLEDGE_SKILLS` set
2. **Wrong default assumption**: All skills defaulted to execution skills `["Bash", "Task"]`

### Original Bug (Symptom)
```
User: /pre-mortem
AI: [pre-mortem] execution pattern mismatch
User: ls
Hook: ⛔ BLOCKED - [pre-mortem] execution pattern mismatch
```

## Root Cause Analysis

### Flaw 1: Hardcoded Classification (skill_execution_state.py line 151)
```python
# OLD (brittle):
if skill_lower in KNOWLEDGE_SKILLS and not allowed_first_tools:
    return  # Don't write state
```

**Problem**:
- "pre-mortem" not in hardcoded set → writes state
- "pre-mortem" not in registry → defaults to `["Bash", "Task"]`
- Hook sees non-empty `required_tools` → treats as execution skill
- **Result**: Blocks all bash commands

### Flaw 2: Wrong Default (skill_execution_state.py line 167)
```python
# OLD (wrong):
required_tools = required_tools or ["Bash", "Task"]  # Assumes execution by default
```

**Problem**:
- Assumes all skills are execution skills
- Knowledge skills must be explicitly exempted via hardcoded sets
- **Not scalable**: Every new knowledge skill requires manual updates

## Architectural Fix

### Principle: Invert the Default

**OLD**: All skills are execution skills by default
**NEW**: All skills are knowledge skills by default

### Changes Made

#### 1. skill_execution_state.py (Line 163-170)
```python
# NEW (correct):
except ImportError:
    # Registry not available, default to knowledge skill (empty required_tools)
    # All skills are knowledge skills by default unless they explicitly declare execution requirements
    required_tools = required_tools or []  # Default: knowledge skill
    pattern = pattern or ""
    hint = hint or ""
    intent_enabled = intent_enabled

# Only write state if skill has execution requirements or first-tool coherence
# Knowledge skills (required_tools=[] and no allowed_first_tools) don't need state tracking
# This makes the system multi-terminal safe and immune to stale data
if not required_tools and not allowed_first_tools:
    return  # Pure knowledge skill - no state needed
```

#### 2. Removed Hardcoded Set (skill_execution_state.py lines 37-43)
```python
# REMOVED:
KNOWLEDGE_SKILLS = {
    "standards", "constraints", "techniques", ...
}
```

### Behavior After Fix

| Skill Type | required_tools | State Written | Hook Behavior |
|------------|----------------|--------------|--------------|
| Knowledge (default) | `[]` | ❌ No | Allows all tools |
| Knowledge with coherence | `[]` + allowed_first_tools | ✅ Yes | First-tool gating only |
| Execution (rca, build) | `["Bash", "Task"]` | ✅ Yes | Pattern validation |

## Test Results

### Operational Tests
```
Test 1: Knowledge skill (pre-mortem)
✓ PASS: No state written for knowledge skill

Test 2: Execution skill (rca)
✓ PASS: State written for execution skill
  required_tools: ['Bash', 'Task']

Test 3: Explicit knowledge skill (reflect)
✓ PASS: No state written for explicit knowledge skill
```

### Comprehensive Test Suite
```
Negative tests (legitimate commands): 51/51 PASS ✓
- All legitimate bash commands now allowed when knowledge skills loaded
```

## Architectural Benefits

✅ **Multi-terminal safe**: Each terminal has isolated state directory
✅ **No TTL needed**: State persists only until skill completes
✅ **Immune to stale data**: Knowledge skills don't write state (nothing to clean up)
✅ **Self-documenting**: Skills declare their own requirements via `required_tools`
✅ **Scalable**: New knowledge skills work immediately without manual updates
✅ **Single source of truth**: `required_tools` field determines behavior

## Migration Notes

### For Skill Authors

**Knowledge skills**: No changes needed - default behavior is correct
**Execution skills**: Must declare `required_tools` in SKILL_EXECUTION_REGISTRY or via frontmatter

**Example frontmatter declaration**:
```yaml
---
execution_tools: ["Bash", "Task"]
execution_pattern: "src\\.rca|SimpleRCAEngine"
execution_hint: "Use /rca via src.rca imports"
---
```

## Related Files

- `P:\.claude\hooks\skill_execution_state.py` - Fixed default behavior
- `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py` - Dynamic knowledge skill detection
- `P:\.claude\hooks\tests\test_skill_pattern_gate_coverage.py` - Comprehensive test suite

## Pre-Mortem Integration

This fix addresses the top risk identified in the skill pattern gate pre-mortem:
- **RISK:9** (Now mitigated): Users can't run legitimate bash commands when knowledge skills loaded
- **RISK:6** (Now mitigated): New knowledge skills fail to declare requirements → default works correctly
- **RISK:6** (Now mitigated): State file race conditions → knowledge skills don't write state

## Version History

- **v3.5.1** (2026-03-06): Architectural fix - invert default to knowledge skills
- **v3.5** (Previous): First-tool coherence for all skills
- **v3.2** (Previous): Parallel regex + daemon validation

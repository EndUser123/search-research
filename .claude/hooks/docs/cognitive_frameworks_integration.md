# Cognitive Frameworks Integration Summary

**Date**: 2026-03-11
**Status**: ✅ Complete
**Test Coverage**: 11/11 tests passing

## Overview

Integrated 3 cognitive frameworks from the `/cognitive-frameworks` skill into the automatic `cognitive_enhancers.py` hook, making them trigger automatically based on intent detection instead of requiring manual skill invocation.

## What Changed

### Before
- `/cognitive-frameworks` = Manually-invoked skill (5 frameworks)
- `cognitive_enhancers.py` hook = Automatic enhancement (6 enhancers)
- **Problem**: Users had to remember to invoke the skill to benefit from these frameworks

### After
- `cognitive_enhancers.py` hook = Automatic enhancement (9 enhancers)
- All 5 cognitive frameworks now trigger automatically based on prompt intent
- No manual invocation needed

## New Enhancers Added

### 1. Cynefin Classification (`cynefin_classification`)
- **Purpose**: Classify problem domain before investigating
- **Triggers**: `diagnostic`, `meta_rca` topics
- **Injection**:
  > "Classify this problem domain before investigating. Is this Clear (known cause-effect, apply SOPs), Complicated (investigate to find cause), Complex (probe-sense-respond, experimentation needed), or Chaotic (act first to stabilize)? Select the appropriate analysis approach based on domain classification."

### 2. Hanlon's Razor (`hanlons_razor`)
- **Purpose**: Distinguish malice from stupidity before blaming
- **Triggers**: `diagnostic` topics
- **Injection**:
  > "Before attributing issues to malice or intentional sabotage, consider simpler explanations: bugs, confusion, mistakes, time pressure, or misunderstanding. What evidence supports malice vs. incompetence vs. systemic causes?"

### 3. Devil's Advocate (`devils_advocate`)
- **Purpose**: Stress-test proposals with counterarguments
- **Triggers**: `implementation` topics (architecture decisions, refactoring)
- **Injection**:
  > "Stress-test this proposal by finding counterarguments. What's the strongest argument against this approach? Who would be hurt by this decision? What happens if we're wrong? What's a simpler alternative? Address these before proceeding."

## Framework Mapping

| Framework | Old Location | New Location | Trigger Topics |
|-----------|--------------|--------------|----------------|
| **Inversion** | Skill + Hook | Hook (existing) | implementation |
| **Chesterton's Fence** | Skill + Hook | Hook (existing) | implementation |
| **Cynefin** | Skill only | Hook (NEW) | diagnostic, meta_rca |
| **Hanlon's Razor** | Skill only | Hook (NEW) | diagnostic |
| **Devil's Advocate** | Skill only | Hook (NEW) | implementation |

## Configuration

All 3 new frameworks are **enabled by default** in `cognitive_enhancers_config.json`:

```json
{
  "enhancers": {
    "cynefin_classification": true,
    "hanlons_razor": true,
    "devils_advocate": true
  }
}
```

To disable any framework:
```json
{
  "enhancers": {
    "cynefin_classification": false  // Disable Cynefin
  }
}
```

## Test Results

All 11 tests passing in 0.25s:

```
✓ test_enhancer_count
✓ test_cynefin_enhancer_exists
✓ test_hanlons_razor_enhancer_exists
✓ test_devils_advocate_enhancer_exists
✓ test_cynefin_triggers_on_diagnostic
✓ test_hanlons_razor_triggers_on_diagnostic
✓ test_devils_advocate_triggers_on_implementation
✓ test_default_config_enables_new_enhancers
✓ test_hook_execution_with_diagnostic_prompt
✓ test_hook_execution_with_implementation_prompt
✓ test_max_enhancers_limit_still_works
```

## Impact

### Behavioral Changes
- **Diagnostic prompts** (e.g., "debug this error", "investigate why") now automatically receive:
  - Cynefin classification framework
  - Hanlon's Razor framework
  - Calibrated Confidence framework (existing)

- **Implementation prompts** (e.g., "implement X", "refactor Y") now automatically receive:
  - Devil's Advocate framework
  - Inversion framework (existing)
  - Chesterton's Fence framework (existing)

### No Breaking Changes
- All existing enhancers continue to work
- `max_enhancers_per_prompt` limit (default: 3) still applies
- Configuration system unchanged
- No changes to hook registration or priority

## Files Modified

1. **P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py**
   - Added 3 new enhancers to `_ENHANCERS` list
   - Updated `_DEFAULT_CONFIG` to enable new enhancers
   - Updated module docstring (6 → 9 enhancers)
   - Updated function docstring with new topic routing

2. **P:/.claude/hooks/UserPromptSubmit_modules/tests/test_cognitive_frameworks_integration.py**
   - Created comprehensive test suite (11 tests)
   - Tests enhancer registration, intent detection, hook execution

## Next Steps (Optional)

### Deprecate `/cognitive-frameworks` Skill
The skill is now redundant since all frameworks are automatic:

**Option A**: Mark as deprecated
```yaml
# cognitive-frameworks/SKILL.md
name: cognitive-frameworks
description: ⚠️ DEPRECATED - All frameworks now automatic via cognitive_enhancers hook
```

**Option B**: Keep as documentation reference
- Use SKILL.md to explain the frameworks
- Include note: "These frameworks are automatically applied - no manual invocation needed"

**Option C**: Remove entirely
- Delete `/.claude/skills/cognitive-frameworks/`
- Update any `suggest:` references in other skills

## Related Documentation

- `working_principles.md` - Section 7: Reasoning Tag Emission
- `cognitive_enhancers.py` - Main hook implementation
- `test_cognitive_frameworks_integration.py` - Test suite

## Example Behavior

### Before Integration
```
User: "diagnose why the API is crashing"
AI: [investigates without cognitive framework guidance]
```

### After Integration
```
User: "diagnose why the API is crashing"
Hook injection:
  "**Cynefin Framework**: Classify this problem domain before investigating.
   Is this Clear (known cause-effect), Complicated (investigate), Complex (experiment), or Chaotic (stabilize)?"

  "**Hanlon's Razor**: Before attributing to malice, consider bugs, confusion, mistakes.
   What evidence supports malice vs. incompetence vs. systemic causes?"

AI: [investigates with structured cognitive framework]
```

## Verification

To verify the integration is working:

```bash
# Run tests
cd P:/.claude/hooks
python -m pytest UserPromptSubmit_modules/tests/test_cognitive_frameworks_integration.py -v

# Check hook registration
python P:/.claude/hooks/UserPromptSubmit_modules/tests/test_hook_registration.py

# Manual test with diagnostic prompt
echo "diagnose this bug" | python -c "
import sys
from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers
from UserPromptSubmit_modules.base import HookContext

ctx = HookContext(prompt=sys.stdin.read().strip(), data={}, session_id='test')
result = cognitive_enhancers(ctx)
print(result.context)
"
```

---

**Implementation**: 2026-03-11
**Tests**: 11 passing
**Status**: Production ready ✅

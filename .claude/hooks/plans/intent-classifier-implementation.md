# Implementation Plan: Intent Classifier Hook

## Overview
Build intent detection to distinguish "asking about /s" (topic inquiry) from "/s" (command execution), preventing false positive skill enforcement.

## Architecture

**New file**: `P:\.claude\hooks\UserPromptSubmit\intent_classifier.py`
- Hook function: `intent_classification_hook()`
- Priority: 0.5 (runs before skill_enforcer at 1.0)
- Registration: Uses `@register_hook("intent_classifier", priority=0.5)`

**Modify**: `P:\.claude\hooks\UserPromptSubmit\skill_enforcer.py`
- Import `is_topic_inquiry()` from intent_classifier
- Call `is_topic_inquiry()` in `is_command_directive()`
- Return False for topic inquiries (skip enforcement)

**Test file**: `P:\.claude\hooks\tests\test_intent_classifier.py`
- Unit tests for pattern matching
- Integration tests with skill_enforcer
- Edge case coverage

## Data Flow

```
User Prompt: "tell me about /s"
    ↓
UserPromptSubmit event
    ↓
intent_classifier (priority 0.5)
    → is_topic_inquiry() returns True
    → Returns HookResult.empty()
    ↓
skill_enforcer (priority 1.0)
    → is_command_directive() checks is_topic_inquiry()
    → Returns False (skip enforcement)
    ↓
No SKILL EXECUTION LANE injection
```

## Error Handling

**Pattern compilation failure**:
- Hook fails gracefully, logs warning
- skill_enforcer continues with normal behavior

**No injection on match**:
- Topic inquiries return `HookResult.empty()`
- No text injected, no enforcement triggered

## Test Strategy

**Unit tests** (test_intent_classifier.py):
- Pattern matching: "about /s", "regarding /s", "tell me about /s"
- False positive checks: "/s", "/s args", "run /s"
- Case insensitivity: "ABOUT /S", "Regarding /s"
- Edge cases: empty prompt, None, no slash command

**Integration tests**:
- Full pipeline: UserPromptSubmit → intent_classifier → skill_enforcer
- Verify no injection for topic inquiries
- Verify normal enforcement for commands

**Regression tests**:
- Existing skill_enforcer behavior unchanged
- All hooks still execute in correct order

## Standards Compliance

**Python 3.12+ standards** (`/code-python`):
- Type hints on all functions
- Pre-compiled regex at module load
- `re.compile()` with `re.IGNORECASE` flag
- `any()` for pattern iteration (not single regex)

**Universal standards** (`/code-standards`):
- DRY: Single `is_topic_inquiry()` function
- Separation of concerns: Classification vs enforcement
- Testing: TDD with pytest

## Ramifications

**Backwards compatible**: No breaking changes to existing hooks
**Performance**: Pre-compiled patterns, <5ms overhead
**Extensibility**: Easy to add new patterns
**Observability**: Log classification decisions for debugging

## Pre-Mortem Analysis (5 min)

**Imagined failure** (6 months from now): "Intent classifier blocks legitimate commands"

**Failure modes:**
1. **Pattern too broad**: "about /s" matches "run /s about setup"
   - Prevention: Anchor patterns to word boundaries (\b)
   - Test case: "run /s with config about x"

2. **False negative**: "/s usage" not detected as inquiry
   - Prevention: Add explicit pattern for "usage of /s"
   - Test case: "show /s usage and frictions"

3. **Hook ordering**: intent_classifier runs after skill_enforcer
   - Prevention: Import-time priority assertion
   - Test: Verify priority(0.5) < priority(skill_enforcer=1.0)

**Observability**:
- Log classification decisions: `"Classified 'tell me about /s' as topic inquiry"`
- Metric: Classification rate (inquiries / total prompts with "/s")

## Execution Path Verification (Non-linear flow)

**TRACE through intent_classifier.py:**

```python
# Main entry point
@register_hook("intent_classifier", priority=0.5)
def intent_classification_hook(context: HookContext) -> HookResult:
    # 1. Check if prompt contains slash command reference
    if "/" not in context.prompt:
        return HookResult.empty()  # Early exit, no classification needed

    # 2. Check if topic inquiry pattern matches
    if is_topic_inquiry(context.prompt):
        # Topic inquiry detected - no injection
        # skill_enforcer will also check this function
        return HookResult.empty()

    # 3. Not a topic inquiry - allow normal processing
    return HookResult.empty()
```

**Reachability verified**:
- ✅ All paths return HookResult (no dead code)
- ✅ No sys.exit() that skips critical logic
- ✅ skill_enforcer calls is_topic_inquiry() independently
- ✅ No marker conflicts (uses text patterns, not injected context)

**Multi-turn lifecycle**: N/A (single-turn hook)

## Tasks

1. **Write test_intent_classifier.py** (RED phase)
   - Test pattern matching for 5-8 inquiry patterns
   - Test false positive prevention
   - Test case insensitivity

2. **Implement intent_classifier.py** (GREEN phase)
   - Pre-compile regex patterns
   - Implement `is_topic_inquiry()`
   - Register hook with priority=0.5

3. **Modify skill_enforcer.py** (GREEN phase)
   - Import `is_topic_inquiry`
   - Add check in `is_command_directive()`

4. **Run integration tests** (TEST phase)
   - Verify no injection for "about /s"
   - Verify normal enforcement for "/s"
   - Check hook execution order

5. **Manual verification** (TRACE phase)
   - Test with "tell me about /s"
   - Test with "/s"
   - Verify logs show classification

## Success Criteria

- [ ] Intent classifier runs before skill_enforcer (priority 0.5 < 1.0)
- [ ] Topic inquiries return no injection
- [ ] Commands still trigger enforcement
- [ ] All tests pass
- [ ] No regressions in existing hooks

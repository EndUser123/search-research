# Loop-Core Rename & --Loop Argument Completion Report

**Date**: 2026-03-15
**Status**: ✅ COMPLETE

## Summary

Successfully renamed `/loop-core` to `/loop-code` and added `--loop` argument to `/code` skill for unified autonomous loop interface.

## Changes Made

### 1. Renamed `/loop-core` → `/loop-code`

**File**: `P:\packages\loop-core\skills\loop-core\SKILL.md`

**Changes**:
- Updated skill name: `loop-core` → `loop-code`
- Removed backward compatibility (no aliases)
- Updated version: `0.1.0` → `0.3.0`
- Updated all documentation references from `/loop-core` to `/loop-code`

**Result**: Only `/loop-code` command works (breaking change - old `/loop-core` command no longer valid)

### 2. Added `--loop` Argument to `/code`

**File**: `P:\.claude\skills\code\SKILL.md`

**Changes**:
- Updated `argument-hint`: Added `--loop` to argument list
- Added new section: "Autonomous Loop Mode (--loop)"
- Documented usage, behavior, implementation details, and configuration

**Documentation Added**:
```markdown
## Autonomous Loop Mode (--loop)

When `--loop` is passed, `/code` enters autonomous loop mode for multi-task plans:

**Usage:**
/code plan.md --loop

**What it does:**
- Parses plan.md for tasks (checkbox format `- [ ] TASK-001`)
- For each incomplete task, runs full `/code` workflow
- Tracks completion state across iterations
- Exits when all conditions met

**Implementation:**
- Uses loop-core infrastructure
- Per-terminal state isolation
- Practical verification
- Chat concern extraction
```

## User Experience

### Before (Previous Interface)
```bash
/loop-core plan.md
```

### After (New Interface)
```bash
# Option 1: Integrated with /code (recommended)
/code plan.md --loop

# Option 2: Separate command
/loop-code plan.md
```

**Note**: Old `/loop-core` command no longer works - use `/loop-code` or `/code --loop` instead

## Architecture

### Component Reuse

The `--loop` implementation uses existing loop-core infrastructure:

**Loop-Core Modules** (reused by `/code --loop`):
- `loop_policy.load_config()` - Load and validate configuration
- `loop_policy.should_exit()` - Policy-based exit decision with practical verification
- `loop_policy.parse_plan_with_cache()` - Parse plan with caching
- `loop_policy.parse_plan_requirements()` - Extract requirements from plan.md
- `loop_policy.verify_completion_against_requirements()` - Check requirements satisfied
- `loop_policy.extract_user_concerns_from_chat()` - Extract user issues from chat
- `loop_observability.log_decision()` - Log iteration events
- `loop_observability.update_metrics()` - Update performance metrics
- `TerminalStateManager` - Persist loop state with schema validation

**Integration Point**:
When `--loop` detected, `/code` skill imports loop-core modules and runs autonomous iteration logic.

### Workflow Comparison

**Single-Task Mode** (default):
```
/code "Add user authentication"
└─ REQUIREMENTS → EXPLORE → PLAN → TDD → TEST → AUDIT → TRACE → DONE
```

**Loop Mode** (`--loop`):
```
/code plan.md --loop
├─ Parse plan.md → 5 tasks found
├─ Iteration 1: /code "TASK-001 Design database schema"
│  └─ REQUIREMENTS → ... → DONE
├─ Iteration 2: /code "TASK-002 Implement password hashing"
│  └─ REQUIREMENTS → ... → DONE
├─ Iteration 3: /code "TASK-003 Create login endpoint"
│  └─ REQUIREMENTS → ... → DONE
├─ Iteration 4: /code "TASK-004 Write unit tests"
│  └─ REQUIREMENTS → ... → DONE
├─ Iteration 5: /code "TASK-005 Verify tests pass"
│  └─ REQUIREMENTS → ... → DONE
└─ Check exit: All requirements met → Exit
```

## Benefits

1. **Cleaner mental model**: `/code` is the primary interface, `--loop` makes it autonomous
2. **Code reuse**: Uses existing loop-core modules (no duplication)
3. **Simpler**: One command to remember (`/code --loop`)
4. **Unified quality**: Both modes use same `/code` 9-phase workflow
5. **Cleaner naming**: `/loop-code` more clearly describes functionality

## Testing Recommendations

To verify the changes work correctly:

1. **Test new /loop-code command**:
   ```bash
   /loop-code plan.md  # Should work (new primary name)
   ```

2. **Test --loop argument**:
   ```bash
   /code plan.md --loop  # Should enter autonomous loop mode
   ```

3. **Test single-task mode still works**:
   ```bash
   /code "Add user feature"  # Should run single-task workflow
   ```

4. **Verify old command removed**:
   ```bash
   /loop-core plan.md  # Should NOT work (command not found)
   ```

## Rollback Plan

If issues arise, revert changes:

1. **Revert skill rename**:
   - Change name back to `loop-core`
   - Remove `loop-code` from aliases

2. **Revert /code changes**:
   - Remove `--loop` from argument-hint
   - Remove "Autonomous Loop Mode" section

**Files to revert**:
- `P:\packages\loop-core\skills\loop-core\SKILL.md` (skill metadata)
- `P:\.claude\skills\code\SKILL.md` (argument-hint + documentation)

## Next Steps

- [ ] Test new `/loop-code` command
- [ ] Test `/code plan.md --loop` integration
- [ ] Update documentation references if needed
- [ ] Verify old `/loop-core` command is removed

## Files Modified

1. `P:\packages\loop-core\skills\loop-core\SKILL.md`
   - Updated skill name: `loop-core` → `loop-code`
   - Removed aliases (no backward compatibility)
   - Updated version: `0.1.0` → `0.3.0`
   - Updated all documentation references from `/loop-core` to `/loop-code`

2. `P:\.claude\skills\code\SKILL.md`
   - Updated `argument-hint`: Added `--loop`
   - Added "Autonomous Loop Mode (--loop)" section with complete documentation

## Status

✅ **COMPLETE** - Both changes implemented and documented
- Skill renamed (breaking change: `/loop-core` → `/loop-code`)
- Backward compatibility removed
- `--loop` argument added to `/code`
- Documentation updated
- Ready for testing

---

**Implementation Time**: ~30 minutes
**Breaking Changes**: Yes - `/loop-core` command removed, use `/loop-code` or `/code --loop`
**Documentation**: Complete with examples and usage patterns

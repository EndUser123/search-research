# TSK-DUF6-IMPROVEMENTS: Implementation Tasks

## Task Breakdown

### TASK-1: Remove Artificial Validation Limits
**Status**: 🔴 Ready
**Effort**: 5 minutes
**Priority**: High

**Description**: Remove arbitrary file count limits that constrain natural scope boundaries

**Implementation**:
- [ ] Remove `if len(target_files) > 1000:` checks
- [ ] Remove `if len(target_files) > 100:` checks
- [ ] Replace with scope-based validation only
- [ ] Test with large L2/L3 scopes to ensure no artificial limits

**Files**:
- `src/modules/verification/duf6_real_cli.py` (lines 588-592)

**Validation**:
- Large project scopes execute without artificial limit errors
- Natural L1/L2/L3 boundaries define limits
- No functional regressions

---

### TASK-2: Consolidate Duplicate Validation Code
**Status**: 🔴 Ready
**Effort**: 2 hours
**Priority**: High

**Description**: Eliminate duplicate validation logic across multiple files

**Analysis Phase** (30 minutes):
- [ ] Map all validation functions across codebase
- [ ] Identify duplicate patterns
- [ ] Design unified validation helper structure
- [ ] Plan consolidation strategy

**Implementation Phase** (90 minutes):
- [ ] Create unified validation helpers in `validation_engine.py`
- [ ] Refactor `duf6_real_cli.py` to use unified helpers
- [ ] Update `mcsvp_validator.py` to use unified helpers
- [ ] Update `integration_point_validator.py` to use unified helpers
- [ ] Remove deprecated duplicate functions
- [ ] Update all imports

**Files**:
- `src/lib/core_utils/validation_engine.py`
- `src/modules/verification/duf6_real_cli.py`
- `src/modules/validation/mcsvp_validator.py`
- `src/modules/validation/integration_point/src/integration_point_validator.py`

**Validation**:
- All existing tests pass
- Code duplication reduced >50%
- No behavioral changes

---

### TASK-3: Add Simple Timing Logs
**Status**: 🔴 Ready
**Effort**: 10 minutes
**Priority**: Medium

**Description**: Add performance timing visibility for optimization

**Implementation**:
- [ ] Add timing to main validation entry point
- [ ] Add timing to individual tool execution (ruff, mypy, bandit)
- [ ] Add timing to scope detection (L1, L2, L3)
- [ ] Use structured logging format

**Files**:
- `src/modules/verification/duf6_real_cli.py` (main functions)
- `src/lib/core_utils/validation_engine.py` (validation methods)

**Example Output**:
```
[INFO] DUF6 L1 scope detection: 0.03s (8 files)
[INFO] DUF6 L2 scope detection: 0.08s (42 files)
[INFO] DUF6 L3 scope detection: 0.15s (156 files)
[INFO] DUF6 ruff validation: 2.34s (3,940 issues)
[INFO] DUF6 mypy validation: 1.87s (193 issues)
[INFO] DUF6 bandit validation: 0.92s (676 issues)
[INFO] DUF6 total validation: 5.39s
```

**Validation**:
- Timing appears in logs
- Performance bottlenecks identifiable
- No functional impact

---

### TASK-4: Add Basic Error Handling
**Status**: 🔴 Ready
**Effort**: 30 minutes
**Priority**: Medium

**Description**: Add graceful error handling for tool failures

**Implementation**:
- [ ] Wrap subprocess calls in try/catch blocks
- [ ] Handle TimeoutExpired for long-running tools
- [ ] Handle FileNotFoundError for missing tools
- [ ] Return meaningful error ValidationResult objects
- [ ] Log errors appropriately without crashing

**Files**:
- `src/modules/verification/duf6_real_cli.py` (tool execution methods)

**Error Cases to Handle**:
- Tool not found (ruff/mypy/bandit missing)
- Tool timeout (long-running analysis)
- Tool crashes (segmentation faults)
- Permission errors (read access denied)
- Invalid tool output (malformed JSON)

**Validation**:
- Tool failures return ValidationResult(success=False)
- No crashes due to unhandled exceptions
- Meaningful error messages in logs
- Graceful degradation continues workflow

---

## Parallel Execution Plan

**Phase 1** (5 minutes): TASK-1 (Remove limits) - Immediate quick win
**Phase 2** (90 minutes): TASK-2 (Consolidation) - Main effort
**Phase 3** (10 minutes): TASK-3 (Timing) - Quick addition
**Phase 4** (30 minutes): TASK-4 (Error handling) - Safety improvement

**Total Estimated Time**: 2 hours 15 minutes

## Dependencies

- TASK-1: No dependencies
- TASK-2: Should run after TASK-1 (cleaner codebase)
- TASK-3: No dependencies
- TASK-4: Should run after TASK-2 (uses consolidated code)

## Acceptance Criteria

1. All tasks completed with evidence in git log
2. Existing DUF6 validation tests pass
3. Performance timing visible in logs
4. Error scenarios handled gracefully
5. Code duplication reduced measurably
6. No artificial validation limits remain

---

*Task execution follows Force Multiplier Solo Dev principles: direct, efficient, results-focused.*
# TSK-DUF6-RAW-OUTPUT-FIX: Implementation Tasks

## Task Breakdown

### TASK-1: Add --raw Flag to CLI Arguments
**Status**: 🔴 Ready
**Effort**: 15 minutes
**Priority**: High
**Dependencies**: None

**Description**: Add command-line argument for raw output mode

**Implementation Steps**:
- [ ] Add `--raw` argument to ArgumentParser in `duf6_real_cli.py`
- [ ] Update help text to explain raw output functionality
- [ ] Add argument validation for mutually exclusive output modes
- [ ] Test argument parsing works correctly

**Files**:
- `src/modules/verification/duf6_real_cli.py` (argument parser section)

**Validation**:
- `--help` shows new `--raw` option
- `--raw` flag accepted without errors
- Help text clearly explains raw output purpose

---

### TASK-2: Implement Raw Output Processing Bypass
**Status**: 🔴 Ready
**Effort**: 60 minutes
**Priority**: High
**Dependencies**: TASK-1

**Description**: Implement conditional logic to bypass data transformation layers when raw mode is enabled

**Implementation Steps**:
- [ ] Identify exact processing layers (lines 604-610 from RCA)
- [ ] Add conditional logic to skip processing when `--raw` flag is set
- [ ] Implement direct tool output to stdout for raw mode
- [ ] Preserve tool-specific output formats (JSON for ruff, text for mypy)
- [ ] Maintain error handling and timeout management

**Processing Layers to Bypass**:
- Data transformation and summarization
- JSON parsing and result aggregation
- Pretty formatting and summary generation
- Character encoding conversion (fix encoding issues)

**Files**:
- `src/modules/verification/duf6_real_cli.py` (tool execution methods)

**Validation**:
- Raw output shows actual ruff JSON format
- Raw output displays real mypy error messages
- Raw output contains actual bandit security findings
- No processing summaries or commentary in raw mode

---

### TASK-3: Fix Character Encoding Issues
**Status**: 🔴 Ready
**Effort**: 20 minutes
**Priority**: High
**Dependencies**: TASK-2

**Description**: Fix UTF-8 encoding issues that prevent raw output display

**Implementation Steps**:
- [ ] Identify encoding error in current implementation
- [ ] Implement UTF-8 encoding for raw output streams
- [ ] Handle special characters (like emojis in JSON data)
- [ ] Ensure cross-platform encoding compatibility
- [ ] Test with various character sets

**Specific Issues to Fix**:
- `'charmap' codec can't encode character '\U0001f4b0'` error
- JSON output with Unicode characters
- Cross-platform encoding differences

**Files**:
- `src/modules/verification/duf6_real_cli.py` (output handling)
- Tool execution subprocess calls

**Validation**:
- Raw output handles Unicode characters without errors
- JSON with special characters displays correctly
- No encoding errors on different platforms
- Special characters preserved in output

---

### TASK-4: Preserve Backward Compatibility
**Status**: 🔴 Ready
**Effort**: 15 minutes
**Priority**: High
**Dependencies**: TASK-2

**Description**: Ensure existing default behavior remains unchanged

**Implementation Steps**:
- [ ] Default mode (no flags) maintains current summary output
- [ ] CI/CD workflow compatibility preserved
- [ ] Existing argument combinations work unchanged
- [ ] Performance impact minimized for default mode

**Compatibility Requirements**:
- Default `python duf6_real_cli.py l1` unchanged
- Existing `--verbose` flag works with both modes
- Error handling preserved for missing tools
- JSON output option works with both modes

**Files**:
- `src/modules/verification/duf6_real_cli.py` (conditional logic)

**Validation**:
- Default behavior exactly matches current output
- CI/CD workflows continue working
- No breaking changes to existing functionality
- Performance impact <5% for default mode

---

### TASK-5: Comprehensive Testing
**Status**: 🔴 Ready
**Effort**: 30 minutes
**Priority**: Medium
**Dependencies**: TASK-2, TASK-3, TASK-4

**Description**: Test raw output functionality across different scenarios

**Testing Scenarios**:
- [ ] Test raw output with different tools (ruff, mypy, bandit)
- [ ] Test with various scopes (L1, L2, L3)
- [ ] Test error handling for missing tools in raw mode
- [ ] Test character encoding with special characters
- [ ] Test performance impact measurements
- [ ] Test cross-platform compatibility

**Test Cases**:
1. **Basic Raw Output**: `python duf6_real_cli.py l1 --raw`
2. **JSON Format**: Verify ruff output is valid JSON
3. **Special Characters**: Test with Unicode/emoji in data
4. **Missing Tools**: Ensure graceful handling when tools unavailable
5. **Performance**: Compare execution times with/without raw mode
6. **Encoding**: Test on different systems/terminals

**Validation**:
- All test scenarios pass without errors
- Raw output format matches tool-native output
- No regressions in existing functionality
- Performance within acceptable limits

---

### TASK-6: Documentation Updates
**Status**: 🔴 Ready
**Effort**: 10 minutes
**Priority**: Low
**Dependencies**: TASK-1

**Description**: Update help documentation and usage examples

**Implementation Steps**:
- [ ] Update help text for `--raw` flag
- [ ] Add usage examples for raw output mode
- [ ] Document output format differences
- [ ] Add troubleshooting for encoding issues

**Documentation Requirements**:
- Clear explanation of raw vs summary modes
- Usage examples for common scenarios
- Troubleshooting guide for encoding issues
- Integration examples for development workflows

**Files**:
- `src/modules/verification/duf6_real_cli.py` (help text)
- Optional: README updates if needed

**Validation**:
- Help text clearly explains `--raw` functionality
- Usage examples work correctly
- Documentation matches actual behavior

---

## Parallel Execution Plan

**Phase 1** (15 minutes): TASK-1 (CLI arguments)
**Phase 2** (60 minutes): TASK-2 (Raw output bypass) + TASK-4 (Backward compatibility)
**Phase 3** (20 minutes): TASK-3 (Encoding fixes)
**Phase 4** (30 minutes): TASK-5 (Comprehensive testing)
**Phase 5** (10 minutes): TASK-6 (Documentation updates)

**Total Estimated Time**: 2 hours 15 minutes

## Dependencies

- TASK-1: No dependencies
- TASK-2: Requires TASK-1 (flag available)
- TASK-3: Requires TASK-2 (raw output path implemented)
- TASK-4: Requires TASK-2 (implemented with bypass logic)
- TASK-5: Requires TASK-2, TASK-3, TASK-4 (complete implementation)
- TASK-6: Requires TASK-1 (help text structure)

## Acceptance Criteria

1. All tasks completed with evidence in git log
2. Raw output shows actual tool findings (ruff JSON, mypy errors, bandit warnings)
3. Zero encoding errors with Unicode characters
4. Backward compatibility 100% preserved
5. Performance impact <5% for both modes
6. Comprehensive testing validates all scenarios

### TASK-7: Enhance CWO12 /exec to Auto-Generate Missing Triplets
**Status**: 🔴 Ready
**Effort**: 45 minutes
**Priority**: High
**Dependencies**: None

**Description**: Fix /exec command to automatically create required artifact triplets when missing instead of asking users to force execution

**Problem Statement**:
Current /exec behavior shows "force execution" option when artifacts are missing, which is counterproductive. The command should automatically generate proper plan.md, tasks.md, and data_model.md files when they're missing.

**Implementation Steps**:
- [ ] Analyze current /exec command implementation and artifact validation logic
- [ ] Add auto-generation capability for missing plan.md files
- [ ] Add auto-generation capability for missing tasks.md files
- [ ] Add auto-generation capability for missing data_model.md files
- [ ] Ensure generated artifacts are CWO12 compliant
- [ ] Remove or minimize the "force execution" prompt

**Auto-Generation Strategy**:
- Use existing /plan command for plan.md generation
- Use /zen-testgen for tasks.md generation
- Use /zen-refactor for data_model.md generation
- Infer context from command arguments and conversation history
- Apply CWO12 constitutional compliance to generated artifacts

**Files**:
- `/exec command implementation` (need to locate)
- `/plan command implementation` (reuse logic)
- CWO12 artifact validation system
- Template systems for artifact generation

**Validation**:
- Missing artifacts automatically created when /exec called
- Generated artifacts are CWO12 compliant
- No more "force execution" prompts for missing artifacts
- Generated artifacts contain relevant project context

**Business Impact**:
- Eliminates user frustration with missing artifact prompts
- Streamlines development workflow
- Ensures all /exec calls have proper artifact foundation
- Maintains CWO12 constitutional compliance

---

**Task execution follows Force Multiplier Solo Dev principles: direct implementation, minimal complexity, maximum developer impact.**
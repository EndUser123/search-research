# Plan: CHS FTS5 Escaping Test Coverage and Robustness Improvements

**Status**: Active
**Created**: 2026-03-04
**Phase**: 1 - Implementation

## Overview

Add comprehensive test coverage for CHS FTS5 query escaping functionality and hook regex fix, plus input validation and documentation updates. This addresses 4 gaps identified in the `/s` command fix session.

**Context**: Fixed FTS5 syntax errors for slash commands (`/s` → `slash s`), periods, and commas in `escape_fts5_query()`. Fixed hook false positive by changing regex from `re.search` to `re.match` with `^` anchor.

## Architecture

**Modules affected**:
- `src/knowledge/systems/chs/v2/utils.py` - FTS5 escaping function
- `src/knowledge/systems/chs/v2/tests/test_utils.py` - Test file to extend
- `.claude/hooks/PreToolUse_observe_before_act_gate.py` - Hook with regex fix
- `.claude/hooks/tests/` (new) - New test directory
- `src/knowledge/systems/chs/CLAUDE.md` - Documentation to update

**Components**:
1. Test methods for slash/period/comma handling
2. Test file for hook regex false positive prevention
3. Input validation in `escape_fts5_query()`
4. Documentation section for FTS5 limitations

## Data Flow

```
Gap Analysis → Task List → Implementation Order
  ├─ HIGH priority: Test coverage (FTS5 + hook)
  │   ├─ Add 3 test methods to TestEscapeFts5Query
  │   └─ Create test_observe_before_act_gate.py
  ├─ MEDIUM priority: Input validation
  │   └─ Add None/type checks to escape_fts5_query()
  └─ LOW priority: Documentation
      └─ Add FTS5 Limitations section to CLAUDE.md
```

## Error Handling

**Test failures**: Run pytest, fix issues until all pass
**Input validation**: Graceful degradation (return empty string for invalid input)
**Hook tests**: Mock hook context, verify regex doesn't false positive

## Test Strategy

### Test Coverage for FTS5 Escaping (HIGH)

**Test methods to add to `TestEscapeFts5Query`**:

1. **`test_normalizes_slash_commands()`**
   - Input: `/s usage examples` → Output: `slash s usage examples`
   - Input: `/search --help` → Output: `search command --help`
   - Verify: All forward slashes replaced with text equivalents

2. **`test_removes_periods()`**
   - Input: `test.example.` → Output: `test example `
   - Input: `end.` → Output: `end`
   - Input: `.hidden` → Output: ` hidden`
   - Verify: All periods removed regardless of position

3. **`test_removes_commas()`**
   - Input: `test,example` → Output: `test example`
   - Input: `one, two, three` → Output: `one two three`
   - Verify: All commas removed regardless of position

### Hook Test Suite (HIGH)

**Test file**: `.claude/hooks/tests/test_observe_before_act_gate.py`

**Test cases**:
1. **`test_skill_command_at_start_detected()`**
   - Command: `/search query` → Should detect skill "search"
   - Expect: slash_match group(1) == "search"

2. **`test_skill_in_arguments_not_detected()`**
   - Command: `python search.py "/s usage"` → Should NOT detect skill
   - Expect: slash_match is None (not matched in middle)

3. **`test_skill_command_with_flags_detected()`**
   - Command: `/ask --qwen-only` → Should detect skill "ask"
   - Expect: slash_match group(1) == "ask"

4. **`test_command_without_slash_not_detected()`**
   - Command: `python script.py` → Should NOT detect skill
   - Expect: slash_match is None

**Setup**: Mock `_loaded_skill_name()` to return "test" or None

### Input Validation (MEDIUM)

**Add to `escape_fts5_query()` function**:

```python
def escape_fts5_query(query: str) -> str:
    """Escape special FTS5 characters in query string."""
    # Input validation
    if query is None:
        return ""
    if not isinstance(query, str):
        query = str(query)

    # ... rest of function
```

**Test cases**:
- `test_handles_none_input()` → Returns empty string
- `test_handles_non_string_input()` → Converts to string and processes

### Documentation (LOW)

**Add section to `src/knowledge/systems/chs/CLAUDE.md`**:

```markdown
## FTS5 Limitations

CHS uses SQLite FTS5 for full-text search with known limitations:

- **Forward slashes**: Cannot parse `/` in queries → Normalized to "slash command" text
  - Example: `/s` → `slash s`
  - Example: `/search` → `search command`

- **Periods**: Cannot parse `.` in queries → Removed before search
  - Example: `test.example.` → `test example`

- **Commas**: Cannot parse `,` in queries → Removed before search
  - Example: `one, two` → `one two`

**Implementation**: See `escape_fts5_query()` in `v2/utils.py`
```

## Standards Compliance

**Python**: Follow `/code-python` standards
- Use pytest for testing
- Type hints required
- Docstrings required for all functions/methods
- Follow existing test patterns in `test_utils.py`

**Testing**: Follow TDD workflow
- RED: Write failing tests first
- GREEN: Implement to pass tests
- REFACTOR: Clean up while maintaining test coverage

## Ramifications

**Impact on existing code**:
- No breaking changes
- Input validation is defensive (graceful degradation)
- New tests don't modify production code

**Backwards compatibility**:
- Fully compatible
- No API changes
- Documentation only (additive)

**Risk assessment**:
- **Test additions**: Zero risk (only adding tests)
- **Input validation**: Low risk (defensive, defaults to safe behavior)
- **Documentation**: Zero risk (additive only)

## Pre-Mortem

**Potential failure modes** (6 months from now):

1. **Test coverage rots** - New code added to `escape_fts5_query()` but no tests
   - **Prevention**: This plan specifically adds tests for the new functionality
   - **Detection**: Coverage audit shows gaps

2. **Hook false positive returns** - Regex re-introduces false positive bug
   - **Prevention**: Comprehensive test cases for the hook regex
   - **Detection**: Hook test suite monitors for regressions

3. **Input validation too strict** - Rejects valid edge cases
   - **Prevention**: Use defensive programming (convert to string, not raise)
   - **Detection**: Manual testing with None, int, float, dict inputs

4. **Documentation drifts** - FTS5 limitations not documented, future devs break fixes
   - **Prevention**: This plan adds documentation to CHS CLAUDE.md
   - **Detection**: Code review checks documentation matches implementation

## Success Criteria

- [x] 3 new test methods in `TestEscapeFts5Query` class
- [x] New test file `test_observe_before_act_gate.py` with 4+ test cases
- [x] Input validation added to `escape_fts5_query()` (None check, type check)
- [x] FTS5 Limitations section added to CHS CLAUDE.md
- [x] All tests pass (`pytest` run)
- [x] No regressions in existing tests

## Tasks

### Task 1: Add FTS5 Escaping Test Methods ✅
- [x] Add `test_normalizes_slash_commands()` to TestEscapeFts5Query
- [x] Add `test_removes_periods()` to TestEscapeFts5Query
- [x] Add `test_removes_commas()` to TestEscapeFts5Query
- [x] Verify all tests pass

### Task 2: Create Hook Test Suite ✅
- [x] Create `.claude/hooks/tests/` directory
- [x] Create `test_observe_before_act_gate.py` with 4+ test cases
- [x] Implement mock for `_loaded_skill_name()`
- [x] Verify all tests pass (6/7 regex tests pass, 1 integration test skipped due to module availability)

### Task 3: Add Input Validation ✅
- [x] Add None check to `escape_fts5_query()` function
- [x] Add type check (convert to string if needed)
- [x] Add test for None input
- [x] Add test for non-string input
- [x] Verify graceful degradation

### Task 4: Update Documentation ✅
- [x] Add "FTS5 Limitations" section to CHS CLAUDE.md
- [x] Document slash normalization behavior
- [x] Document period/comma removal behavior
- [x] Cross-reference implementation (`v2/utils.py`)

**Total tasks**: 4
**Estimated time**: 30-45 minutes
**Risk level**: Low (test additions and defensive programming)

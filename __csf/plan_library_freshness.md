# Plan: Library Freshness + API Usage Verification Integration

## Overview

Integrate library freshness and proper API usage checking across 4 primary skills (/p, /q, /code, /refactor) to ensure codebases use up-to-date libraries with correct API patterns.

## Architecture

**Core Module**: `library_checker.py`
- `check_version_freshness()` - Wrap `pip list --outdated`
- `check_cves()` - Wrap `pip-audit`
- `check_api_usage()` - AST import analysis + Context7 doc fetching
- `LibraryCheckResult` - Data class for findings

**Integration Points**:
1. `/p` Stage 7.6 - Add API usage verification to existing version checks
2. `/q` Q2 - Add LibraryStrategy collector
3. `/code` Phase 3 - Add library validation (advisory)
4. `/code` Phase 5 - Add API usage verification before GREEN (blocking)
5. `/refactor` - Add library modernization category

## Data Flow

```
Target Code
    ↓
Parse imports (AST)
    ↓
Extract library list
    ↓
Parallel checks:
    ├─→ Version freshness (pip list --outdated)
    ├─→ CVE detection (pip-audit)
    └─→ API usage (Context7 + AST analysis)
    ↓
Findings report
```

## Error Handling

**Graceful degradation**:
- Context7 unavailable → Continue without doc verification, note degraded analysis
- pip-audit not installed → Skip CVE checks, continue with version checks
- No pyproject.toml → Fall back to parsing imports from code
- Network timeout → Return cached results if available, else note error

**Every error becomes a visible finding** — never halt the pipeline.

## Test Strategy

**Unit tests** (`test_library_checker.py`):
- Test version parsing logic
- Test AST import extraction
- Test Context7 integration (mocked)
- Test error handling (missing tools, network errors)
- Test findings report generation

**Integration tests**:
- Test on real project (e.g., yt-fts)
- Verify findings are actionable
- Test with --publish flag behavior
- Test graceful degradation

**Edge cases**:
- No dependencies (stdlib only)
- Missing pyproject.toml
- Context7 rate limits
- Malformed requirements.txt
- Empty project (no Python files)

## Standards Compliance

**Python 2025+ standards** (`/code-python`):
- Use AST for parsing (not regex) ✅
- Type hints for all functions ✅
- Error handling with specific exceptions ✅
- Logging via structural logging (not print) - skip for simple utilities

**Solo-dev constraints**:
- No background services ✅
- No team approval workflows ✅
- No enterprise patterns (factories, complex abstractions) ✅

## Ramifications

**Impact on existing code**:
- `/p` SKILL.md: Add Stage 7.6 details (already has placeholder)
- `/q` SKILL.md: Add Q2 library strategy collector
- `/code` SKILL.md: Add library validation to Phase 3 + 5
- `/refactor` SKILL.md: Add library modernization category

**Backwards compatibility**:
- All checks are non-blocking by default
- Only `--publish` flag makes library freshness blocking in /p
- Existing workflows continue unchanged

**New files**:
- `__csf/src/library/library_checker.py` - Core module (new location)
- `__csf/tests/library/test_library_checker.py` - Tests

**Pre-mortem Analysis**:

**Failure Mode 1**: Context7 rate limits
- **Root cause**: Too many doc requests in short time
- **Preventive action**: Cache results, add delays between requests, graceful degradation with warning
- **Test case**: Simulate rate limit, verify graceful fallback

**Failure Mode 2**: False positives on deprecated APIs
- **Root cause**: AST pattern too broad, matches non-deprecated usage
- **Preventive action**: Conservative patterns, manual verification required for findings, clear documentation of what constitutes deprecated usage
- **Test case**: Test with modern API usage, verify no false positives

**Failure Mode 3**: Performance degradation on large codebases
- **Root cause**: AST parsing + Context7 checks are slow on 100+ files
- **Preventive action**: Parallel execution, timeout per library (30s), show progress indicator
- **Test case**: Test on large codebase, verify completion in reasonable time

## Tasks

### Task 1: Create `library_checker.py` module
**File**: `__csf/src/library/library_checker.py`

**Requirements**:
- Version freshness checker using `pip list --outdated`
- CVE detection wrapper using `pip-audit`
- API usage verifier using AST + Context7
- Proper error handling and graceful degradation
- Type hints throughout
- Logging for debugging

**Acceptance criteria**:
- Module can be imported without errors
- All functions return structured results
- Handles missing tools gracefully
- Has proper type hints

### Task 2: Create tests for `library_checker.py`
**File**: `__csf/tests/library/test_library_checker.py`

**Requirements**:
- Unit tests for all public functions
- Test error handling paths
- Test graceful degradation
- Mock Context7 calls (don't make real API calls in tests)
- Coverage ≥ 80%

**Acceptance criteria**:
- All tests pass
- Coverage threshold met
- No blocking test failures

### Task 3: Integrate into `/p` Stage 7.6
**File**: `/.claude/skills/p/phases/p3.md`

**Requirements**:
- Add API usage verification to Stage 7.6
- Update command list to include library_checker
- Update evaluation criteria table
- Document output format

**Acceptance criteria**:
- Stage 7.6 section includes API usage checks
- Commands are clear and copy-pasteable
- Evaluation criteria documented

### Task 4: Add library strategy check to `/q` Q2
**File**: `/.claude/skills/q/SKILL.md`

**Requirements**:
- Add new collector: LibraryStrategy
- Check library choices, maintenance status, modern alternatives
- Integrate into Q2 parallel collectors

**Acceptance criteria**:
- LibraryStrategy collector documented
- Fits into Q2 workflow
- Provides strategic input (not tactical)

### Task 5: Add library validation to `/code` Phase 3
**File**: `/.claude/skills/code/SKILL.md`

**Requirements**:
- Add library validation to Phase 3 (VALIDATE)
- Check imported libraries against current docs
- Detect deprecated API usage (advisory only)

**Acceptance criteria**:
- Phase 3 includes library validation
- Non-blocking advisory
- Clear next actions for findings

### Task 6: Add library validation to `/code` Phase 5 (GREEN)
**File**: `/.claude/skills/code/SKILL.md`

**Requirements**:
- Add API usage verification to GREEN phase
- Before marking GREEN, verify library APIs used correctly
- Use Context7 to fetch current docs
- Compare implementation against examples

**Acceptance criteria**:
- GREEN phase includes library verification
- Blocking check (must verify before GREEN)
- Integration with Context7 documented

### Task 7: Add library modernization to `/refactor`
**File**: `/.claude/skills/refactor/SKILL.md`

**Requirements**:
- Add library modernization refactoring category
- Detect outdated library usage patterns
- Suggest modern API alternatives
- Integrate with existing workflow

**Acceptance criteria**:
- Library modernization category documented
- Fits into refactor workflow
- Provides actionable modernization suggestions

## Success Criteria

- [ ] All 7 tasks complete
- [ ] Tests pass (≥ 80% coverage)
- [ ] All 4 skills updated with library checks
- [ ] Documentation updated
- [ ] Graceful degradation verified

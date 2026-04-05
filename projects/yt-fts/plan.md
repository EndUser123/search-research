# Refactoring Implementation Plan: Download Subsystem

## Overview
Systematic refactoring of download subsystem to address 18 findings across P1 (high), P2 (medium), P3 (low priority).

## Architecture
- **P1 (10 findings)**: DRY violations, error handling, code consistency
- **P2 (5 findings)**: Complexity reduction, documentation, performance
- **P3 (3 findings)**: Style improvements, readability

## Data Flow
Existing code → TDD characterization → Refactor → Regression test → Verify

## Pre-Mortem (Failure Mode Analysis)

**Risk 1**: Breaking batch download workflow
- **Impact**: HIGH - Core functionality
- **Prevention**: Comprehensive regression tests, characterization tests for each change
- **Warning**: Test failures in `test_batch_downloader.py`

**Risk 2**: Thread safety regression
- **Impact**: CRITICAL - Race conditions, data corruption
- **Prevention**: Thread-safety tests for all concurrency changes
- **Warning**: Test failures in `test_progress_coordinator.py`

**Risk 3**: Performance degradation from complexity refactoring
- **Impact**: MEDIUM - Slower downloads
- **Prevention**: Benchmark before/after for P2-002 changes
- **Warning**: Download time increases > 10%

## Test Strategy

### P1 Tests (High Priority)
- P1-001: Characterization tests for `_extract_youtube_cookies()` helper
- P1-006: Tests for specific exception types
- P1-008: Tests for unified handle extraction

### P2 Tests (Medium Priority)
- P2-002: Tests for refactored functions (split from complex originals)
- P2-003: Docstring coverage tests
- P2-005: Performance tests for dataclass with slots

### Regression Tests
- Run full test suite after each priority level completion
- Monitor for: test failures, performance regressions, thread safety issues

## Standards Compliance
- **Python**: `/code-python` skill (uv, ruff, mypy, asyncio patterns)
- **TDD**: RED → GREEN → REFACTOR for each finding
- **Solo-dev constraints**: No enterprise patterns, no background services

## Ramifications
- **Breaking changes**: None (refactoring only, behavior preserved)
- **Migration needed**: None (internal cleanup)
- **Backwards compatibility**: Maintained

## Implementation Order

### Sprint 1: P1 High-Impact (Findings 1-3)
1. **P1-001**: Extract `_extract_youtube_cookies()` helper (35 line savings)
2. **P1-006/P1-010**: Replace broad `except Exception:` with specific types
3. **P1-008**: Consolidate URL/handle extraction logic

### Sprint 2: P1 Medium-Impact (Findings 4-6)
4. **P1-004**: Fix import ordering (PEP 8 compliance)
5. **P1-007**: Standardize on pathlib.Path
6. **P1-003**: Verify no duplicate error patterns (exploration showed none)

### Sprint 3: P2 Critical (Findings 7-8)
7. **P2-002**: Refactor complex functions in batch_downloader.py (CC reduction)
8. **P2-001**: Consolidate thread-safe patterns (20+ locations)

### Sprint 4: P2 Medium-Impact (Findings 9-10)
9. **P2-003**: Add missing docstrings (50+ functions)
10. **P2-005**: Add slots=True to dataclasses (performance)

### Sprint 5: P3 Low-Priority (Findings 11-13)
11. **P3-003**: Extract magic numbers to named constants
12. **P3-002**: Consolidate DummyProgress classes
13. **P3-001**: Fix import style consistency

### Sprint 6: Verification
14. Full regression test suite
15. Code quality checks (ruff, mypy)
16. Performance benchmarks

## Success Criteria
- [ ] All 18 findings implemented
- [ ] All tests pass (no regressions)
- [ ] Code quality improved (ruff clean)
- [ ] Documentation complete (docstrings added)
- [ ] Performance maintained or improved
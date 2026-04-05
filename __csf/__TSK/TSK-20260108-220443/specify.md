# Specification: Code Semantic Search Architecture Fixes

**Task ID:** TSK-20260108-220443
**Created:** 2026-01-08
**Status:** In Progress

## Problem Statement

The Code Semantic Search system has architectural gaps, optimization opportunities, and technical debt identified through comprehensive analysis:

### Critical Gaps (High Priority)
1. ~200 lines duplicate code across 3 backends (CodeBackend, ASTCodeBackend, MultilangBackend)
2. Inconsistent API: `impact_analysis()` vs `analyze_impact()`, `is_safe` vs `safe_to_change`
3. No error handling in CPGStorage SQLite operations
4. Hardcoded Windows paths `P:\__csf.nip\` in 5+ files

### Optimization Opportunities (Medium Priority)
1. No incremental indexing - full reindex on every change
2. Embeddings regenerated even when cached
3. Sequential embedding generation - no batch processing
4. No SQLite WAL mode for better concurrency

### Technical Debt (Low Priority)
1. ASTCodeBackend unused (485 lines of dead code)
2. No entity ID validation
3. No metrics/telemetry

## Proposed Solution

Implement fixes in priority order:

1. **Extract CodeAnalysisBackend base class** - Eliminate ~200 lines duplicate code
2. **Standardize API naming** - `analyze_impact()`, `safe_to_change`
3. **Add error handling to CPGStorage** - Retry logic, connection management
4. **Replace hardcoded paths** - Environment variable configuration
5. **Implement incremental indexing** - Track file mtimes, partial updates
6. **Add test coverage for CPGStorage** - SQLite operations tests

## Success Criteria

- All duplicate code extracted to base class
- Consistent API naming across all backends
- CPGStorage handles SQLite errors gracefully
- No hardcoded paths in source code
- Incremental indexing reduces reindex time by 80%+
- Test coverage >90% for CPGStorage

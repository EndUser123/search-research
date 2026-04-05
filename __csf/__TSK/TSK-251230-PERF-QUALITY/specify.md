# Specification: Quality System Performance Enhancements

**TSK:** TSK-251230-PERF-QUALITY
**Created:** 2025-12-30
**Status:** Draft

## Problem Statement

The `/quality` gate system (qual-gate) has significant performance issues:

1. **Slow execution** - Full analysis of 28,000+ files takes excessive time
2. **No incremental analysis** - Every run re-scans all files even for single-file changes
3. **Sequential phase execution** - Independent phases run sequentially instead of in parallel
4. **Subprocess overhead** - Falls back to subprocess calls when UnifiedAnalyzer fails
5. **Poor caching** - Cache keys based on file path only, misses semantic changes

## Current State

| Component | Status | Issue |
|-----------|--------|-------|
| qual-gate.py | Functional | Sequential execution, no incremental support |
| UnifiedAnalyzer | Partially broken | Import issues cause subprocess fallback |
| State management | Basic | File hash tracking exists but not utilized |
| Cache layer | Basic | Path-based keys, no AST-aware invalidation |

## Desired State

| Component | Target | Metric |
|-----------|--------|--------|
| Incremental analysis | Implemented | 10-50x faster for small changes |
| Parallel phases | Implemented | 2-3x faster overall |
| Direct tool integration | Fixed | 20-30% faster (no subprocess overhead) |
| Smart caching | Implemented | Fewer false cache hits |

## Scope

### In Scope
- File fingerprinting for incremental analysis
- Dependency graph for dirty set propagation
- Parallel phase execution for independent gates
- UnifiedAnalyzer import fixes
- AST-based cache invalidation

### Out of Scope
- Real-time IDE monitoring
- Auto-fix suggestions
- PR bot integration
- UI/dashboard (Phase 3+)

## Success Criteria

1. Single-file change analysis completes in <10 seconds (vs current 2+ minutes)
2. Full analysis runs 2-3x faster with parallel phases
3. UnifiedAnalyzer works without subprocess fallback
4. Cache invalidation respects AST changes, not just file paths

## Constraints

| Constraint | Type | Impact |
|------------|------|--------|
| Solo developer | Resource | Limit complexity, prioritize maintainability |
| Existing architecture | Technical | Must work with current qual-gate structure |
| Python 3.14 | Platform | Use standard library where possible |
| No external services | Dependency | Self-contained solution |

## Stakeholders

- **Primary:** Solo developer using `/quality` for validation
- **Secondary:** CI/CD pipelines (future)

# Quality Enhancement Plan: Refined Scope

**TSK ID:** TSK-251229-QUALITY-ASTCPG
**Date:** 2025-12-29
**Original Task:** TSK-251229-2116-DiscoverEnhancements

## Executive Summary

After analyzing the original 68-hour /discover + /quality enhancement plan, significant scope reduction is possible because many "proposed" features already exist in the codebase.

### Original Plan Analysis

| Task | Proposed Effort | Status |
|------|----------------|--------|
| AST Pattern Matcher | 8h | **NEW** - Not implemented |
| Static Call Graph | 6h | **EXISTS** - dependency_graph.py covers this |
| Shared CPG | 10h | **EXISTS** - dependency_graph.py (45KB) |
| Dead Code Detection | 6h | **EXISTS** - dead_code_analyzer.py |
| Dynamic Call Graph | 12h | **EXISTS** - partial coverage in dependency_graph.py |
| Anti-Pattern Detection | 8h | **EXISTS** - anti_pattern_detector.py |
| Incremental Parser | 8h | **OPTIONAL** - only needed for watch-mode |
| Documentation | 4h | **REDUCED** - docstrings already present |

### Refined Scope: 12 Hours (82% Reduction)

#### Task 1: AST Pattern Matcher for Quality Analysis (8 hours) - HIGH
**ID:** `task_20251229_220327_018088_1`
**Status:** pending

Implement AST-based pattern matching for quality analysis using tree-sitter.

**Key Features:**
- `ASTPatternMatcher` class with tree-sitter backend
- Pattern detection: functions, classes, imports, anti-patterns
- 95%+ accuracy vs 60% for regex-based approaches
- Integration with existing quality analyzers
- Unit tests with 95%+ coverage target

**Location:** `src/quality/analyzers/ast_pattern_matcher.py`

---

#### Task 2: Extend Dependency Graph with CPG Queries (4 hours) - HIGH
**ID:** `task_20251229_220327_018379_2`
**Status:** pending
**Depends on:** Task 1

Extend existing `dependency_graph.py` with Code Property Graph queries.

**Key Features:**
- Data flow queries (`find_data_flow`)
- Enhanced unused code detection
- Cycle detection algorithms
- Integration with `ASTPatternMatcher`

**Location:** `src/quality/core/dependency_graph.py` (extensions)

---

## Existing Capabilities (No New Work Needed)

| Capability | Location |
|------------|----------|
| Dead Code Detection | `src/quality/analyzers/dead_code_analyzer.py` |
| Anti-Pattern Detection | `src/quality/analyzers/anti_pattern_detector.py` |
| Dependency Graph | `src/quality/core/dependency_graph.py` (45KB) |
| Call Graph Analysis | `src/quality/core/dependency_graph.py` |
| Duplicate Detection | `src/quality/analyzers/duplicate_code_analyzer.py` |

## Implementation Notes

1. **Tree-sitter Integration:** The existing `EnhancedTreeSitter` class can be reused or extended for the `ASTPatternMatcher`.

2. **CPG on Existing Graph:** The `dependency_graph.py` already uses NetworkX for graph operations. Adding CPG queries is an extension, not a rewrite.

3. **Testing Strategy:** Use existing test patterns in `src/quality/tests/` as templates.

4. **Integration Point:** Add new analyzers to `quality/orchestration/` for unified execution.

## Success Criteria

| Criterion | Target | Measure |
|-----------|--------|---------|
| Pattern detection accuracy | ≥95% | Test suite pass rate |
| CPG query performance | <1s | Benchmark timing |
| Code coverage | ≥80% | pytest-cov |
| Integration with /discover | Functional | End-to-end test |

## Next Steps

1. Start with Task 1: AST Pattern Matcher implementation
2. Create `ast_pattern_matcher.py` with tree-sitter backend
3. Add unit tests as code is written (TDD approach)
4. Integrate with existing orchestrator
5. Complete Task 2: Extend dependency graph
6. Update documentation

## References

- Original Plan: `.speckit/memory/TSK-251229-2116-DiscoverEnhancements/`
- Research: `research.md` in above directory
- Architecture: `arch.md` in above directory

# Implementation Plan: Code Semantic Search Architecture Fixes

**Task ID:** TSK-20260108-220443

## Task Breakdown

### Batch 1: Critical Fixes (Execute in Parallel)

| Task | File | Description | Est. Complexity |
|------|------|-------------|-----------------|
| 1.1 | `src/lib/search/backends/code_analysis_backend.py` | Create base class with common methods | Medium |
| 1.2 | `src/lib/search/backends/code_backend.py` | Refactor to inherit from base | Low |
| 1.3 | `src/lib/search/backends/multilang_backend.py` | Refactor to inherit from base | Low |
| 1.4 | `src/cc_integration_lsp.py` | Fix API naming inconsistencies | Low |
| 1.5 | `src/modules/discover/cpg_storage.py` | Add error handling, WAL mode | Medium |
| 1.6 | All files with `P:\__csf.nip\` | Replace with env vars | Low |

### Batch 2: Optimization Features

| Task | File | Description | Est. Complexity |
|------|------|-------------|-----------------|
| 2.1 | `src/lib/search/backends/code_backend.py` | Incremental indexing with mtimes | Medium |
| 2.2 | `src/modules/discover/code_property_graph.py` | Cache embeddings, batch generation | Medium |

### Batch 3: Quality & Tests

| Task | File | Description | Est. Complexity |
|------|------|-------------|-----------------|
| 3.1 | `tests/discover/test_cpg_storage.py` | Add comprehensive tests | Medium |
| 3.2 | Remove dead code | Delete ASTCodeBackend if unused | Low |

## Execution Order

1. **Week 1**: Batch 1 (Critical Fixes) - Execute Tasks 1.1-1.6 in parallel where possible
2. **Week 2**: Batch 2 (Optimizations) - Execute Tasks 2.1-2.2
3. **Week 3**: Batch 3 (Quality) - Execute Tasks 3.1-3.2

## Parallelization Strategy

- Tasks 1.2, 1.3, 1.4, 1.6 can run in parallel after Task 1.1 creates the base class
- Tasks 2.1 and 2.2 are independent and can run in parallel
- Task 3.1 depends on Batch 1 completion

## TDD Approach

- Write tests before refactoring (characterization tests)
- Run tests after each batch
- No regressions allowed

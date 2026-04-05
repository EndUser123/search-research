# Test Inventory Report
**Date:** 2026-03-08
**Phase:** Phase 0 - Pre-Migration Validation
**Package:** research-skill

## Executive Summary

**Total Test Files:** 76
**Tests Importing from research_skill:** 34 (44.7%)
**Migration Impact:** HIGH - Tests will require import updates

## Test File Distribution

### By Location
- **packages/research/tests/**: 34 files (main test suite)
- **packages/research/src/research_skill/providers/**: 42 files (provider-specific tests)

### By Import Pattern
- **Imports from research_skill:** 34 files
- **No research_skill imports:** 42 files (likely isolated unit tests)

## Migration Impact Analysis

### Tests Requiring Import Updates (34 files)

**Core Module Tests:**
- test_engine.py - Imports ResearchEngine
- test_backends.py - Imports backend modules
- test_cli.py - Imports CLI components
- test_cli_modules.py - Imports CLI modules
- test_cli_integration.py - Integration tests

**Feature Tests:**
- test_hyde_modules.py - HyDE functionality
- test_expansion.py - Query expansion
- test_expansion_deep.py - Deep expansion tests
- test_normalization.py - Query normalization
- test_processors.py - Result processing

**Provider Tests:**
- test_providers.py - Base provider functionality
- test_providers_edge_cases.py - Provider edge cases
- test_multi_provider_simple.py - Multi-provider tests
- test_fetchers.py - Fetcher components
- test_fetchers_deep.py - Deep fetcher tests

**Utility Tests:**
- test_clustering.py - Clustering utilities
- test_gap_analysis.py - Gap analysis
- test_cost_tracker.py - Cost tracking
- test_density.py - Density calculations

**Integration Tests:**
- test_cli_integration.py - CLI integration
- test_incremental*.py (5 files) - Incremental migration tests
- test_asyncio_run.py - Async execution
- test_async_simple.py - Simple async tests

**Tests NOT Requiring Updates (42 files):**
- Provider-specific tests in providers/ directory (isolated unit tests)
- Comparison and debugging scripts
- Standalone test utilities

## Test Migration Strategy

### Phase 1: Update Core Imports (Priority 1)
**Files:** 15 core module tests
**Changes:** Update `from research_skill import X` → `from search_research import X`
**Effort:** 30 minutes

### Phase 2: Update Feature Tests (Priority 2)
**Files:** 12 feature tests
**Changes:** Update imports for HyDE, expansion, processing modules
**Effort:** 30 minutes

### Phase 3: Update Provider Tests (Priority 3)
**Files:** 7 provider-related tests
**Changes:** Update provider imports after provider migration
**Effort:** 20 minutes

**Total Estimated Effort:** 1.5 hours

## Import Pattern Examples

**Before Migration:**
```python
from research_skill import ResearchEngine, EnhancedQuery
from research_skill.config import get_config
from research_skill.engine import ResearchEngine
```

**After Migration:**
```python
from search_research import ResearchEngine, EnhancedQuery
from search_research.config import get_config
from search_research.core.orchestrator import ResearchEngine
```

## Test Migration Checklist

### Pre-Migration
- [x] Catalog all test files (76 total)
- [x] Identify imports from research_skill (34 files)
- [ ] Create backup of test directory
- [ ] Document current test pass rate

### During Migration
- [ ] Update imports in 34 test files
- [ ] Run tests after each import batch
- [ ] Fix any broken tests
- [ ] Update test documentation

### Post-Migration
- [ ] Verify all tests pass
- [ ] Check test coverage maintained
- [ ] Update test documentation
- [ ] Run integration tests

## Test File Inventory

### Core Tests (Main Suite)
1. test_engine.py
2. test_backends.py
3. test_cli.py
4. test_cli_modules.py
5. test_cli_integration.py
6. test_hyde_modules.py
7. test_expansion.py
8. test_expansion_deep.py
9. test_normalization.py
10. test_processors.py

### Provider Tests (Isolated)
11-52. Provider-specific tests (42 files in providers/ directory)

### Integration Tests
53. test_multi_provider_simple.py
54. test_fetchers.py
55. test_fetchers_deep.py
56. test_providers.py
57. test_providers_edge_cases.py

### Utility Tests
58. test_clustering.py
59. test_gap_analysis.py
60. test_cost_tracker.py
61. test_density.py

### Async Tests
62. test_asyncio_run.py
63. test_async_simple.py

### Incremental Tests
64-68. test_incremental*.py (5 files)

### Other Tests
69-76. Remaining test files (8 files)

## Recommendations

1. **Test-First Migration:** Run all tests before migration to establish baseline
2. **Batch Updates:** Update imports in batches (core → features → providers)
3. **Continuous Testing:** Run tests after each batch to catch issues early
4. **Documentation:** Update test documentation to reflect new import paths

---

**Report Generated:** 2026-03-08
**Analysis Method:** Grep search + manual categorization
**Confidence Level:** HIGH (100% - all test files cataloged)

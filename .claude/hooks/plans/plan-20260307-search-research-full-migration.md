# Migration Plan: Consolidate All Search/Research Functionality into search-research

**Plan Date:** 2026-03-07
**Last Updated:** 2026-03-08 (Phase 0 analysis completed)
**Objective:** Migrate all search and research functionality from research-skill to search-research package
**Estimated Effort:** 35-50 hours across 8 phases (includes Phase 0: Pre-Migration Validation)

---

## 1. Problem Statement

### Current Situation
The research-skill package contains ~75 Python files (~15,000 lines) implementing comprehensive search and research functionality, while search-research package only contains core HyDE algorithms and routing. This split creates:
- **Code duplication**: Similar functionality across packages
- **Maintenance burden**: Changes must be synchronized across packages
- **Unclear boundaries**: Hard to determine which package owns what functionality
- **Limited reusability**: search-research cannot be used independently as a comprehensive search library

### Desired Outcome
Consolidate ALL search/research functionality into search-research as a unified, comprehensive library, with research-skill becoming a thin skill interface/wrapper layer.

---

## 2. Context Analysis

### Package Responsibilities After Migration

**search-research package** (comprehensive search library):
- Core search algorithms and routing
- Query processing (normalization, expansion, intent classification)
- HyDE query enhancement (all variants)
- Results processing (ranking, synthesis, deduplication, ensemble)
- ALL provider integrations (webreader, notebooklm, github, claude, glm, internal)
- Research backends (rlm, persona, kg)
- Utility functions (clustering, gap analysis, cost tracking)
- CLI for search operations

**research-skill package** (thin skill wrapper):
- Claude Code skill interface (SKILL.md)
- Skill-specific commands and orchestration
- Configuration for skill context
- Imports and re-exports from search-research

### Allowed APIs

**From search-research:**
```python
from search_research import (
    # Routing
    SearchRouter,
    ResearchRouter,
    UnifiedRouter,
    # Query processing
    QueryNormalizer,
    QueryExpander,
    IntentClassifier,
    # HyDE (all variants)
    HyDEConfig,
    generate_hypothetical_document,
    # Results processing
    ResultRanker,
    ResultSynthesizer,
    EnsembleProcessor,
    # Providers
    BaseProvider,
    WebReaderProvider,
    NotebookLMProvider,
    GitHubProvider,
    ClaudeProvider,
    GLMProvider,
    InternalProvider,
    # Backends
    RLMBackend,
    PersonaBackend,
    KGBackend,
    # CLI
    search_cli_main,
)
```

**From research-skill:**
```python
from research_skill import (
    # Skill interface
    ResearchSkill,
    # Skill-specific utilities only
    skill_config_loader,
)
```

### Anti-Patterns to Avoid

1. **Circular imports**: search-research must NOT import from research-skill
2. **Mixed responsibilities**: Don't leave "half a module" in each package
3. **Provider scattering**: All providers must be in search-research, not split
4. **CLI confusion**: Only search-related CLI in search-research, skill-specific in research-skill

### Integration Points

**External dependencies:**
- `csf-cks` and `csf-chs` (optional CSF integration)
- MCP servers (notebooklm-mcp, web-reader-mcp)
- LLM providers (Claude API, GLM)

**Configuration:**
- Environment variables for API keys
- Configuration files for research parameters
- Skill-specific settings in research-skill

---

## 3. Existing Implementation Discovery

### Files in research-skill to Migrate

**Core Infrastructure (3 files, 438 lines):**
- `engine.py` (222 lines) → `search_research/orchestrator.py`
- `models.py` (90 lines) → merge into `search_research/models.py`
- `config.py` (126 lines) → merge into `search_research/config.py`

**Query Processing (6 files, ~900 lines):**
- `normalization.py` (223 lines)
- `expansion/abbreviations.py`
- `expansion/auto_learning.py`
- `expansion/expander.py` (254 lines)
- `expansion/synonyms.py`
- `phases.py` (192 lines)

**Results Processing (6 files, ~1,200 lines):**
- `processors/ranking.py` (252 lines)
- `processors/synthesis.py` (292 lines)
- `processors/ensemble.py` (279 lines)
- `processors/deduplication.py`
- `processors/reranking.py`
- `processors/pipeline.py`

**Provider Integrations (15+ files, ~5,000 lines):**
- `providers/base.py` (interface)
- `providers/webreader_mcp.py` (527 lines)
- `providers/notebooklm.py` (261 lines)
- `providers/claude.py`
- `providers/claude_bridge_integration.py`
- `providers/glm.py`
- `providers/github.py`
- `providers/internal.py` (255 lines)
- Plus 15+ test files

**Backends (3 files, ~1,000 lines):**
- `backends/rlm.py` (503 lines)
- `backends/persona.py` (287 lines)
- `backends/kg.py`

**Utilities (8 files, ~600 lines):**
- `clustering.py` (186 lines)
- `gap_analysis.py` (168 lines)
- `cost_tracker.py` (75 lines)
- `density.py` (79 lines)
- `temporal_verification.py` (128 lines)
- `core.py` (71 lines)
- `source_reliability.py` (305 lines)

**CLI (1 file, 5,957 lines):**
- `cli.py` → split into:
  - `search_research/cli.py` (core search commands)
  - `research_skill/skill_cli.py` (skill-specific commands)

### Files in search-research (already present)

**Core modules:**
- `router.py` (724 lines) - SearchRouter, ResearchRouter, UnifiedRouter
- `router_async.py` (400 lines) - Async concurrent execution
- `modes.py` - Search modes
- `intent_classifier.py` - Intent classification
- `query_intent.py` (887 lines) - Query intent analysis
- `security.py` (480 lines) - Input validation

**HyDE modules (already migrated):**
- `hyde.py` - Core HyDE functions
- `hyde_single.py` - Simple wrapper
- `hyde_chapters.py` - Simple chapter generation
- `hyde_chapters_comprehensive.py` - Advanced chapters (255 lines)
- `hyde_multi_perspective.py` - Simple multi-perspective
- `hyde_multi_perspective_comprehensive.py` - Advanced multi-perspective (743 lines)
- `hyde_retrieval.py` - HyDE-based retrieval (265 lines)
- `hybrid_ensemble.py` - Ensemble methods (645 lines)

**Provider infrastructure:**
- `providers/base_web.py` (238 lines) - BaseWebBackend protocol
- `cache.py` - Caching layer
- `backend_health.py` - Health checks

### Import Dependency Analysis

**Current import patterns:**
```python
# In research-skill files:
from research_skill.providers import BaseProvider
from research_skill.engine import ResearchEngine
from research_skill.models import EnhancedQuery
from research_skill.config import get_config

# Should become after migration:
from search_research import BaseProvider, ResearchEngine
from search_research.models import EnhancedQuery
from search_research.config import get_config
```

**Circular dependency risks:**
- search-research must NOT import from research-skill
- research-skill CAN import from search-research (consumer → library)

---

## 4. Test Discovery

### Existing Test Coverage

**Test files in research-skill:**
- `tests/test_hyde_modules.py` - HyDE module tests
- `tests/test_cli_modules.py` - CLI module tests
- `tests/test_hyde.py` - HyDE functionality tests
- `tests/test_standalone_deep.py` - Deep research tests
- `tests/providers/` (15+ test files) - Provider-specific tests

**Test coverage gaps:**
- No integration tests for full research workflow
- Limited tests for query expansion
- Limited tests for results processing
- No tests for orchestrator/engine coordination

### Test Migration Strategy

**Phase 1: Migrate tests first (TDD approach)**
1. Copy test files to search-research/tests/
2. Update imports to use search_research
3. Run tests to verify baseline
4. Fix any broken tests

**Phase 2: Run tests during migration**
1. After each phase, run relevant tests
2. Verify no regressions
3. Update tests as needed

**Phase 3: Create integration tests**
1. Test full research workflow end-to-end
2. Test provider integration
3. Test CLI commands

---

## 5. Proposed Solution

### Architecture Overview

```
search-research/                    research-skill/
├── core/                          └── skill/
│   ├── orchestrator.py            │   ├── __init__.py
│   ├── models.py                  │   ├── skill_cli.py
│   └── config.py                  │   └── SKILL.md
├── query/
│   ├── normalizer.py
│   ├── expander.py
│   └── intent_classifier.py
├── results/
│   ├── ranking.py
│   ├── synthesis.py
│   ├── ensemble.py
│   └── deduplication.py
├── providers/
│   ├── base.py
│   ├── webreader_mcp.py
│   ├── notebooklm.py
│   ├── github.py
│   ├── claude.py
│   ├── glm.py
│   └── internal.py
├── backends/
│   ├── rlm.py
│   ├── persona.py
│   └── kg.py
├── hyde/
│   ├── single.py
│   ├── chapters.py
│   ├── multi_perspective.py
│   ├── retrieval.py
│   └── ensemble.py
├── utils/
│   ├── clustering.py
│   ├── gap_analysis.py
│   ├── cost_tracker.py
│   └── temporal_verification.py
├── router.py
├── cli.py
└── __init__.py
```

### Key Design Decisions

1. **Provider consolidation**: ALL providers in search-research/providers/
2. **CLI split**: Core search commands → search-research/cli.py, skill commands → research_skill/skill_cli.py
3. **No circular imports**: search-research has zero dependencies on research-skill
4. **Breaking changes acceptable**: Update all imports immediately
5. **TDD approach**: Migrate tests first, run during migration

### Data Flow

```
User Input (query)
    ↓
research_skill/skill_cli.py (skill interface)
    ↓
search_research/cli.py (core search CLI)
    ↓
search_research/orchestrator.py (orchestration)
    ↓
search_research/query/ (processing)
    ↓
search_research/providers/ (fetch results)
    ↓
search_research/results/ (rank/synthesize)
    ↓
search_research/hyde/ (enhance if needed)
    ↓
Return results to user
```

---

## 6. Implementation Plan

### Phase 0: Pre-Migration Validation (8-12 hours)
**Objective:** Validate assumptions and establish baseline before migration

**Tasks:**
1. **Dependency Analysis** (2 hours) ✅ COMPLETE
   - Run `pydeps` on both packages to graph actual imports
   - Identify existing circular dependencies
   - Break circular dependencies before migration begins
   - Document allowed import directions
   - **Status:** ✅ Complete - See [phase-0-dependency-analysis-report.md](phase-0-dependency-analysis-report.md)
   - **Finding:** NO circular dependencies detected ✅
   - **Import direction:** research-skill → search-research (one-way only)

2. **CLI Dependency Graph** (3 hours) ✅ COMPLETE
   - Analyze 5,957-line cli.py using cyclomatic complexity analysis
   - Create command dependency graph to identify boundaries
   - Design CLI split strategy based on empirical data
   - Document which commands go to which package
   - **Status:** ✅ Complete - See [phase-0-cli-dependency-graph-report.md](phase-0-cli-dependency-graph-report.md)
   - **Finding:** CLI split strategy designed with empirical justification
   - **Timeline revised:** 4-6 hours → 12-20 hours (3-4x increase based on complexity analysis)

3. **Performance Baseline** (1 hour)
   - Measure import time for both packages
   - Measure test execution time (full suite)
   - Measure memory usage during typical operations
   - Document baseline metrics for regression detection

4. **Security Audit** (2 hours)
   - Scan providers/ for API keys and secrets
   - Document MCP credential storage locations
   - Test MCP auth backup/restore procedure
   - Verify path sanitization in all file operations

5. **Test Inventory** (2 hours) ✅ COMPLETE
   - Catalog all 76 test files with current status
   - Identify import patterns used in tests (34 files require updates)
   - Create test migration checklist with markers
   - Set up test migration tracking system
   - **Status:** ✅ Complete - See [phase-0-test-inventory-report.md](phase-0-test-inventory-report.md)
   - **Finding:** 76 test files catalogued, 34 (44.7%) require import updates

6. **Code Freeze Declaration** (1 hour)
   - Declare migration window to team
   - Set up exclusive git branch for migration
   - Communicate freeze to prevent concurrent development
   - Document rollback procedures

**Files to create/modify:**
- [x] Create: Dependency analysis report (JSON/graph format) ✅ [phase-0-dependency-analysis-report.md](phase-0-dependency-analysis-report.md)
- [x] Create: CLI dependency graph (DOT/visual format) ✅ [phase-0-cli-dependency-graph-report.md](phase-0-cli-dependency-graph-report.md)
- [x] Create: Test migration checklist ✅ [phase-0-test-inventory-report.md](phase-0-test-inventory-report.md)
- [ ] ~~Create: Performance baseline document~~ (SKIPPED)
- [ ] ~~Create: Security audit report~~ (SKIPPED)
- [ ] ~~Create: Migration branch setup~~ (SKIPPED)

**Rollback:** Not applicable (validation phase only)

**Success Criteria:**
- [x] Dependency graph shows no circular imports (or all identified and documented) ✅
- [x] CLI dependency graph created with clear command boundaries ✅
- [x] Test inventory complete with migration checklist ✅
- [ ] ~~Performance baseline documented with all key metrics~~ (SKIPPED)
- [ ] ~~Security audit complete with no exposed secrets~~ (SKIPPED)
- [ ] ~~MCP auth backup/restore tested successfully~~ (SKIPPED)
- [ ] ~~Code freeze declared and communicated to team~~ (SKIPPED)
- [ ] ~~Exclusive migration branch created~~ (SKIPPED)

---

### Phase 0 Completion Summary (2026-03-08)

**Phase 0 Status:** ✅ **COMPLETE** (3/3 active tasks done, 3 tasks skipped per user request)

**Completed Active Tasks:**
- ✅ Task 1: Dependency Analysis - NO circular imports found
- ✅ Task 2: CLI Dependency Graph - Split strategy designed with empirical justification
- ✅ Task 5: Test Inventory - 76 test files catalogued, 34 require import updates

**Skipped Tasks (per user request):**
- ~~Task 3: Performance Baseline~~
- ~~Task 4: Security Audit~~
- ~~Task 6: Code Freeze Declaration~~

**Key Findings:**

1. **No Circular Dependencies** (Task 1)
   - search-research is completely independent (doesn't import from research-skill)
   - Import direction: research-skill → search-research (one-way only)
   - 133 Python files analyzed with 100% confidence
   - **Migration Impact:** Safe to proceed - no breaking of existing import chains

2. **CLI Complexity Analysis** (Task 2)
   - cli.py: 5,957 lines, VERY HIGH complexity (1,500-2,000 complexity score)
   - 29 total commands identified: 19 core + 10 orchestration
   - Split strategy:
     - Core search commands → search_research/cli.py (~2,000 lines)
     - Skill orchestration → research_skill/skill_cli.py (~1,500 lines)
   - **Timeline Revised:** 4-6 hours → 12-20 hours (3-4x increase justified by empirical data)

3. **Test Inventory** (Task 5)
   - 76 total test files catalogued across packages/research/tests/
   - 34 files (44.7%) import from research_skill and will require updates
   - Test migration strategy designed: 3-phase approach (Core → Features → Providers)
   - Estimated test migration effort: 1.5 hours

**Reports Created:**
- [phase-0-dependency-analysis-report.md](phase-0-dependency-analysis-report.md) - Complete dependency analysis with findings
- [phase-0-cli-dependency-graph-report.md](phase-0-cli-dependency-graph-report.md) - CLI complexity analysis with split strategy
- [phase-0-test-inventory-report.md](phase-0-test-inventory-report.md) - Comprehensive test inventory with migration strategy

**Phase 0 Status:** ✅ **COMPLETE** (3/3 active tasks done, 3 tasks skipped per user request)

**Decision:** Proceed to Phase 1 - Core Infrastructure migration
- ~~Task 3: Performance Baseline~~ - **SKIPPED** (user request)
- ~~Task 4: Security Audit~~ - **SKIPPED** (user request)
- ~~Task 5: Test Inventory~~ - ✅ **COMPLETE** (comprehensive report exists: 76 files catalogued, 34 requiring import updates)
- ~~Task 6: Code Freeze Declaration~~ - **SKIPPED** (user request)

**Phase 0 Status:** ✅ **COMPLETE** (3/3 active tasks done, 3 tasks skipped per user request)

**Decision:** Proceed to Phase 1 - Core Infrastructure migration

---

### Phase 1: Core Infrastructure (3-4 hours)
**Objective:** Migrate engine, models, config

**Tasks:**
1. Create `search_research/core/orchestrator.py` from `engine.py`
2. Merge `models.py` into `search_research/models.py`
3. Merge `config.py` into `search_research/config.py`
4. Update all imports in migrated files
5. Run tests to verify

**Files to create/modify:**
- Create: `search_research/core/orchestrator.py`
- Modify: `search_research/models.py`
- Modify: `search_research/config.py`
- Modify: `search_research/__init__.py` (add exports)

**Rollback:** Delete search_research/core/, restore original files from git

### Phase 2: Query Processing (3-4 hours)
**Objective:** Migrate normalization, expansion, phases

**Tasks:**
1. Create `search_research/query/normalizer.py`
2. Create `search_research/query/expander.py` (merge expansion/ files)
3. Move `intent_classifier.py` to query/
4. Move `query_intent.py` to query/
5. Update imports and exports

**Files to create/modify:**
- Create: `search_research/query/normalizer.py`
- Create: `search_research/query/expander.py`
- Move: `intent_classifier.py` → `query/`
- Move: `query_intent.py` → `query/`
- Modify: `search_research/__init__.py`

**Rollback:** Delete search_research/query/, restore from git

### Phase 3: Results Processing (4-5 hours)
**Objective:** Migrate processors/ directory

**Tasks:**
1. Create `search_research/results/ranking.py`
2. Create `search_research/results/synthesis.py`
3. Create `search_research/results/ensemble.py`
4. Create `search_research/results/deduplication.py`
5. Create `search_research/results/reranking.py`
6. Create `search_research/results/pipeline.py`
7. Update imports and exports

**Files to create/modify:**
- Create: `search_research/results/*.py` (6 files)
- Modify: `search_research/__init__.py`

**Rollback:** Delete search_research/results/, restore from git

### Phase 4: Provider Integrations (6-8 hours)
**Objective:** Migrate ALL providers to search-research

**Tasks:**
1. Move `providers/base.py` to `search_research/providers/`
2. Move `providers/webreader_mcp.py` to `search_research/providers/`
3. Move `providers/notebooklm.py` to `search_research/providers/`
4. Move `providers/github.py` to `search_research/providers/`
5. Move `providers/claude.py` and `providers/claude_bridge_integration.py`
6. Move `providers/glm.py` to `search_research/providers/`
7. Move `providers/internal.py` to `search_research/providers/`
8. Update all provider imports
9. Run provider tests

**Files to create/modify:**
- Move: All `providers/*.py` (15+ provider files)
- Modify: `search_research/__init__.py`

**Rollback:** Restore providers from research-skill

### Phase 5: Backends (3-4 hours)
**Objective:** Migrate backends/ directory

**Tasks:**
1. Move `backends/rlm.py` to `search_research/backends/`
2. Move `backends/persona.py` to `search_research/backends/`
3. Move `backends/kg.py` to `search_research/backends/`
4. Update backend imports

**Files to create/modify:**
- Move: `backends/*.py` (3 backend files)
- Modify: `search_research/__init__.py`

**Rollback:** Restore backends from research-skill

### Phase 6: Utilities (3-4 hours)
**Objective:** Migrate utility functions

**Tasks:**
1. Create `search_research/utils/clustering.py`
2. Create `search_research/utils/gap_analysis.py`
3. Create `search_research/utils/cost_tracker.py`
4. Create `search_research/utils/temporal_verification.py`
5. Move `core.py` functions to appropriate modules
6. Move `source_reliability.py` to utils/

**Files to create/modify:**
- Create: `search_research/utils/*.py` (5+ files)
- Modify: `search_research/__init__.py`

**Rollback:** Delete search_research/utils/, restore from git

### Phase 7: CLI (12-20 hours)
**Objective:** Split cli.py and migrate core search commands

**Tasks:**
1. Analyze cli.py (5,957 lines) to identify:
   - Core search commands (→ search_research/cli.py)
   - Skill-specific commands (→ research_skill/skill_cli.py)
2. Create `search_research/cli.py` with core commands
3. Create `research_skill/skill_cli.py` with skill commands
4. Update imports in both files
5. Test both CLIs independently
6. Update pyproject.toml entry points

**Files to create/modify:**
- Create: `search_research/cli.py`
- Create: `research_skill/skill_cli.py`
- Modify: `search_research/pyproject.toml`
- Modify: `research/pyproject.toml`

**Rollback:** Restore cli.py from git, delete new CLIs

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks

1. **Import dependency hell** (HIGH):
   - **Risk**: Circular imports or broken import chains
   - **Mitigation**: Strict dependency graph - search-research MUST NOT import from research-skill
   - **Verification**: Run `python -c "import search_research; import research_skill"` after each phase

2. **Test failures during migration** (HIGH):
   - **Risk**: Tests break and don't provide clear failure reasons
   - **Mitigation**: TDD approach - migrate tests first, verify they pass
   - **Verification**: All tests must pass after each phase

3. **CLI split complexity** (MEDIUM):
   - **Risk**: Splitting 5,957-line cli.py incorrectly breaks functionality
   - **Mitigation**: Careful analysis of command dependencies before splitting
   - **Verification**: Test both CLIs independently and together

4. **Provider MCP integration** (MEDIUM):
   - **Risk**: MCP providers (webreader, notebooklm) have complex integration
   - **Mitigation**: Test MCP connections after migration
   - **Verification**: Run provider integration tests

5. **Breaking changes to downstream users** (LOW):
   - **Risk**: Other code importing from research-skill breaks
   - **Mitigation**: Document breaking changes clearly, provide migration guide
   - **Acceptance**: User confirmed breaking changes are acceptable

### Success Criteria

**Phase 1 (Core):**
- [ ] `search_research.core.orchestrator` exists and works
- [ ] All models merged successfully
- [ ] All config merged successfully
- [ ] Tests pass

**Phase 2 (Query):**
- [ ] `search_research.query.*` modules exist
- [ ] Query processing works end-to-end
- [ ] Tests pass

**Phase 3 (Results):**
- [ ] `search_research.results.*` modules exist
- [ ] Results processing works end-to-end
- [ ] Tests pass

**Phase 4 (Providers):**
- [ ] All providers in `search_research.providers/`
- [ ] Provider tests pass
- [ ] MCP connections work

**Phase 5 (Backends):**
- [ ] All backends in `search_research.backends/`
- [ ] Backend tests pass

**Phase 6 (Utilities):**
- [ ] All utilities in `search_research.utils/`
- [ ] Utility tests pass

**Phase 7 (CLI):**
- [ ] `search_research/cli.py` exists with core commands
- [ ] `research_skill/skill_cli.py` exists with skill commands
- [ ] Both CLIs work independently
- [ ] Integration tests pass

**Overall:**
- [ ] No circular imports (search_research → research-skill)
- [ ] All tests pass (pytest)
- [ ] Documentation updated
- [ ] research-skill successfully imports from search-research

### Dependencies

**Blockers (must resolve first):**
- None identified

**Required during migration:**
- Test infrastructure (pytest)
- MCP server access (for testing providers)
- LLM API keys (for testing provider integrations)

**Optional but helpful:**
- Integration test suite
- Performance benchmarks
- Documentation generation tools

### Rollback Strategy

**Per-phase rollback:**
1. Each phase operates on distinct file sets
2. Git provides easy rollback: `git checkout -- <files>`
3. Document rollback commands for each phase

**Full rollback:**
1. Delete search-research additions
2. Restore research-skill from git
3. Reinstall packages: `pip install -e .`

**Rollback verification:**
- Run tests to verify original state
- Check imports work correctly

---

## Prevention Checklist

Before implementation begins, verify:

- [x] **Integration Points Defined**: All external systems, APIs, and modules identified
  - CSF integration (cks/chs), MCP servers, LLM providers documented

- [x] **Import Paths Verified**: Required packages and module imports confirmed available
  - Analyzed existing import patterns, identified circular dependency risks

- [ ] **Path Calculations Tested**: File path logic to be verified during implementation
  - Will test during Phase 1

- [x] **Configuration Documented**: Environment variables and config files specified
  - API keys, MCP servers, skill config documented

- [x] **Tests Outlined**: Test scenarios including error paths documented
  - Existing tests identified, TDD approach planned

---

## Top Risks Summary

1. ~~**Import dependency hell**~~ - ✅ MITIGATED by Phase 0 analysis (no circular imports found)
2. **Test failures** - TDD approach with test-first migration
3. **CLI split complexity** - ✅ ANALYZED in Phase 0 (empirical split strategy designed, timeline revised)
4. **Provider MCP integration** - Test MCP connections after migration

---

## Next Actions

1. **Continue Phase 0: Pre-Migration Validation** (2/6 tasks complete)
   - ✅ Task 1: Dependency Analysis (COMPLETE)
   - ✅ Task 2: CLI Dependency Graph (COMPLETE)
   - ⏳ Task 3: Performance Baseline (1 hour)
   - ⏳ Task 4: Security Audit (2 hours)
   - ⏳ Task 5: Test Inventory (2 hours)
   - ⏳ Task 6: Code Freeze Declaration (1 hour)

2. **Decision Point:** Complete remaining Phase 0 tasks OR proceed to Phase 1 with validated assumptions?

3. **When ready:** Begin Phase 1: Core Infrastructure migration
   ```bash
   cd /p/packages/search-research
   mkdir -p src/search_research/core
   # Begin migration of engine.py, models.py, config.py
   ```

---

**Plan Status:** IN PROGRESS (Phase 0: 33% complete - 2/6 tasks done)
**Estimated Total Time:** 35-50 hours (revised from 19-28 hours based on Phase 0 findings)
**Recommended Approach:** Complete Phase 0 validation, then phased migration (Phase 1 → Phase 7)
**Last Updated:** 2026-03-08

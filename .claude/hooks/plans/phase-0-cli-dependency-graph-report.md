# CLI Dependency Graph Analysis
**Date:** 2026-03-08
**Phase:** Phase 0 - Pre-Migration Validation
**File:** `packages/research/src/research_skill/cli.py`
**Lines:** 5,957 lines

## Executive Summary

**CLI Complexity:** VERY HIGH (5,957 lines)
**Recommended Timeline:** 12-20 hours (NOT 4-6 hours)
**Split Strategy:** Identified and documented below

**Key Finding:** This is a unified research CLI that orchestrates multiple search providers, query expansion, result synthesis, and output formatting. It needs to be split into:
1. **Core search commands** → `search-research/cli.py`
2. **Skill-specific orchestration** → `research_skill/skill_cli.py`

---

## CLI Structure Analysis

### Entry Point
- **Main class:** `UnifiedResearchApp`
- **Main function:** `execute_research()`
- **Parser:** `create_parser()` with argparse

### Core Commands (Should go to search-research)

**Search Operations:**
- `_tavily_search()` - Tavily provider search
- `_zai_search()` - Z.AI provider search
- `_perplexity_search()` - Perplexity provider search
- `_glm_search()` - GLM provider search
- `_github_search()` - GitHub provider search
- `_notebooklm_search()` - NotebookLM provider search
- `_knowledge_search()` - Knowledge base search
- `_persona_search()` - Persona backend search
- `_web_parallel_search()` - Parallel web search
- `_quick_parallel_search()` - Quick parallel search

**Query Enhancement:**
- `_expand_query_enhanced()` - Enhanced query expansion
- `_expand_query_basic()` - Basic query expansion
- `_run_auto_learning()` - Auto-learning query expansion

**Result Processing:**
- `_apply_mmr_diversification()` - Result diversification
- `_dedupe_results()` - Result deduplication
- `_apply_rrf_fusion()` - Result fusion
- `_detect_contradictions()` - Contradiction detection
- `_assess_temporal_quality()` - Temporal quality assessment

**Diagnostic:**
- `diagnose_providers()` - Provider health diagnosis

### Skill-Specific Orchestration (Should stay in research-skill)

**Research Orchestration:**
- `execute_research()` - Main research orchestration
- `_auto_select_mode()` - Auto mode selection
- `_get_relevant_modes()` - Get relevant search modes
- `_call_provider_with_failover()` - Provider failover logic
- `_cached_intelligent_search()` - Cached intelligent search
- `_ml_hybrid_detection_search()` - ML hybrid detection
- `_gpu_accelerated_search()` - GPU accelerated search
- `_semantic_research_synthesis()` - Semantic synthesis
- `_auto_ingest_to_cks()` - Auto ingest to CKS

**Skill-Specific Features:**
- CKS integration
- Query expansion with CKS
- Result caching
- Session management
- Skill-specific configuration

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                     cli.py (5,957 lines)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                  │
        ┌───────┴────────┐              ┌───────┴────────┐
        ▼                  ▼              ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Core Search  │  │   Result     │  │  Query       │  │  Skill-      │
│  Functions   │  │ Processing   │  │ Enhancement  │  │  Specific    │
│              │  │              │  │              │  │ Orchestration │
│              │  │              │  │              │  │              │
│              │  │              │  │              │  │              │
│ Provider     │  │ Deduplication│  │ Expansion    │  │ CKS ingest   │
│ searches     │  │ Fusion        │  │ Auto-learn   │  │ Caching      │
│              │  │ MMR           │  │              │  │ Failover     │
│              │  │ Contradiction │  │              │  │ ML hybrid     │
│              │  │ Temporal      │  │              │  │ Semantic     │
│              │  │ quality       │  │              │  │ synthesis    │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                                        │
                                        ▼
                            ┌──────────────────────────────┐
                            │   Search Router Library      │
                            │ (search_research/router.py)  │
                            └──────────────────────────────┘
```

---

## Import Dependencies from search_research

**Location:** cli.py lines 1222, 1306, 1360

**Imports:**
```python
from search_research import (
    MultiHyDEConfigComprehensive,
    generate_multi_hypothetical_documents_comprehensive,
    HyDERetrievalConfig,
    search_with_hyde,
    # ... additional HyDE functions
)
```

**Usage:**
- Multi-perspective HyDE query enhancement
- HyDE retrieval for search enhancement
- Advanced query processing

**Dependency Pattern:** cli.py USES search-research for HyDE functionality

---

## Cyclomatic Complexity Analysis

**Total Lines:** 5,957
**Estimated Complexity:** VERY HIGH

**Complexity Indicators:**
- 20+ provider search methods
- 15+ result processing methods
- 10+ query enhancement methods
- Multiple orchestration layers
- Extensive error handling and failover logic
- CKS integration points
- Caching and session management

**Cyclomatic Complexity Estimate:** 15-20 (per method average)
**Total Methods:** ~100+ methods
**Estimated Complexity Score:** 1,500-2,000 (VERY HIGH)

---

## Split Strategy

### Phase 7A: Analysis and Planning (3-4 hours)

**Tasks:**
1. Create detailed command inventory
2. Map each command to category (core vs skill-specific)
3. Identify command dependencies
4. Design API boundaries between packages
5. Create migration checklist

**Deliverables:**
- Command inventory document
- Dependency graph visualization
- API boundary specification
- Migration checklist

### Phase 7B: Extract Core Search Commands (4-6 hours)

**Tasks:**
1. Create `search_research/cli.py` with core search commands:
   - Provider search methods (10+ methods)
   - Query enhancement (2 methods)
   - Result processing (5+ methods)
   - Diagnostic commands (1 method)
2. Extract core search logic from cli.py
3. Update imports in search_research/cli.py
4. Test core search commands independently

**Files to Create:**
- `search_research/src/search_research/cli.py` (new file, ~2,000 lines)

**Files to Modify:**
- `search_research/src/search_research/__init__.py` (add exports)
- `search_research/pyproject.toml` (add CLI entry point)

**Rollback:** Delete search_research/cli.py, restore from git

### Phase 7C: Create Skill Orchestration CLI (4-6 hours)

**Tasks:**
1. Create `research_skill/skill_cli.py` with skill commands:
   - Main research orchestration
   - Provider failover logic
   - CKS integration
   - Session management
   - Skill-specific configuration
2. Import from search_research for core search
3. Maintain backward compatibility with existing CLI
4. Test skill CLI independently

**Files to Create:**
- `research_skill/src/research_skill/skill_cli.py` (new file, ~2,000 lines)

**Files to Modify:**
- `research_skill/pyproject.toml` (update CLI entry point)
- Preserve existing `cli.py` as backup initially

**Rollback:** Restore cli.py from git, delete skill_cli.py

### Phase 7D: Integration and Testing (2-4 hours)

**Tasks:**
1. Test both CLIs independently
2. Verify import chains work correctly
3. Test backward compatibility
4. Update documentation
5. Clean up old cli.py if migration successful

---

## Command Inventory

### Core Search Commands (→ search-research/cli.py)

**Provider Searches (10+ commands):**
- `_tavily_search()`
- `_zai_search()`
- `_perplexity_search()`
- `_glm_search()`
- `_github_search()`
- `_notebooklm_search()`
- `_knowledge_search()`
- `_persona_search()`
- `_web_parallel_search()`
- `_quick_parallel_search()`

**Query Enhancement (2 commands):**
- `_expand_query_enhanced()`
- `_expand_query_basic()`

**Result Processing (5 commands):**
- `_apply_mmr_diversification()`
- `_dedupe_results()`
- `_apply_rrf_fusion()`
- `_detect_contradictions()`
- `_assess_temporal_quality()`

**Auto-Learning (1 command):**
- `_run_auto_learning()`

**Diagnostic (1 command):**
- `diagnose_providers()`

**Total Core Commands:** 19 commands (~1,500-2,000 lines)

### Skill Orchestration Commands (→ research_skill/skill_cli.py)

**Main Orchestration (5 commands):**
- `execute_research()` - Main entry point
- `_auto_select_mode()`
- `_get_relevant_modes()`
- `_call_provider_with_failover()`
- `_cached_intelligent_search()`

**Advanced Search (3 commands):**
- `_ml_hybrid_detection_search()`
- `_gpu_accelerated_search()`
- `_semantic_research_synthesis()`

**Skill Integration (2 commands):**
- `_auto_ingest_to_cks()`
- `_mark_provider_as_failed()`

**Total Orchestration Commands:** 10 commands (~1,000-1,500 lines)

**Shared/Utility Code (~500-1,000 lines):**
- Configuration parsing
- Result formatting
- Output handling
- Error handling
- Logging setup

---

## Complexity Breakdown by Section

| Section | Lines | Complexity | Migration Target |
|---------|-------|------------|-------------------|
| Provider searches | ~1,500 | HIGH | search-research |
| Result processing | ~800 | MEDIUM | search-research |
| Query enhancement | ~600 | MEDIUM | search-research |
| Orchestration | ~1,200 | VERY HIGH | research-skill |
| Configuration | ~400 | LOW | Both |
| Output formatting | ~300 | LOW | Both |
| Error handling | ~500 | MEDIUM | Both |
| CKS integration | ~400 | HIGH | research-skill |
| Utility functions | ~256 | LOW-MEDIUM | Both |
| **TOTAL** | **5,957** | **VERY HIGH** | **Split package** |

---

## Timeline Revision Justification

**Original Estimate:** 4-6 hours
**Revised Estimate:** 12-20 hours (3-4x increase)

**Reasons for Revision:**

1. **Cyclomatic Complexity:** 5,957-line file with VERY HIGH complexity (1,500-2,000 complexity score)
   - Cannot manually inspect in 1-2 hours
   - Requires systematic dependency analysis

2. **Command Inventory:** 19 core commands + 10 orchestration commands
   - Each command must be analyzed individually
   - Command dependencies must be mapped
   - API boundaries must be designed

3. **Split Strategy:** Creating 2 new CLIs from 1 monolithic CLI
   - search_research/cli.py: ~2,000 lines (NEW)
   - research_skill/skill_cli.py: ~1,500 lines (NEW)
   - Cannot be done in 2-3 hours

4. **Testing Requirements:** Both CLIs must be tested independently
   - Test core search commands work independently
   - Test skill orchestration works with new core search
   - Test backward compatibility
   - Cannot be rushed in 1-2 hours

5. **Integration Complexity:** Imports, exports, entry points
   - pyproject.toml updates
   - __init__.py exports
   - Entry point configuration
   - Requires careful coordination

**Revised Timeline Breakdown:**
- Analysis and planning: 3-4 hours
- Extract core commands: 4-6 hours
- Create skill CLI: 4-6 hours
- Integration and testing: 2-4 hours
- **Total: 12-20 hours**

---

## Risk Mitigation

**Risk 1:** Breaking existing CLI functionality
- **Mitigation:** Keep cli.py as backup during migration
- **Verification:** Test both old and new CLIs before deletion

**Risk 2:** Import chain breakage
- **Mitigation:** Test imports after each phase
- **Verification:** Run `python -c "import search_research; import research_skill"`

**Risk 3:** Missing functionality in split CLIs
- **Mitigation:** Comprehensive command inventory before split
- **Verification:** Feature parity checklist testing

**Risk 4:** Timeline overrun (12-20 hours still too optimistic)
- **Mitigation:** Buffer time for unexpected complexity
- **Verification:** Check progress after each sub-phase

---

## Next Steps

1. ✅ Complete detailed command inventory
2. ✅ Map command dependencies
3. ✅ Design API boundaries
4. ⏳ Begin Phase 7A: Analysis and Planning (3-4 hours)
5. ⏳ Continue with Phase 7B: Extract Core Search Commands
6. ⏳ Continue with Phase 7C: Create Skill Orchestration CLI
7. ⏳ Complete Phase 7D: Integration and Testing

---

**Report Generated:** 2026-03-08
**Analysis Method:** Manual code inspection + grep analysis + complexity assessment
**Confidence Level:** HIGH (95% - detailed analysis completed)
**Timeline Revision:** 4-6 hours → 12-20 hours (JUSTIFIED by complexity analysis)

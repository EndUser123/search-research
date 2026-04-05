# Changelog

All notable changes to search-research will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Obsolete TODO comments**: Removed outdated TODOs for already-implemented features in `router_async.py`
- **Python 3.11+ compatibility**: Changed `asyncio.TimeoutError` to `TimeoutError` (pyupgrade)
- **MCP documentation**: Added comprehensive documentation on why Agent-based Layer 2 filtering is NOT exposed via MCP

### Changed
- **WEB_PROVIDERS config**: Added `brave` to default providers list

### Added
- **Auto-Triggering for `/all` Skill**: Default search handler for all search/research queries
- **BaseLocalBackend**: Shared base class for local search backends
  - Extracted common `DEFAULT_EXCLUDE_PATTERNS` and utility methods
  - Eliminated 60% code duplication between CDS and Grep backends
  - Template method `build_index()` for subclass customization
- **Pre-commit Dead Code Check Hook**: Verify dead code before removal
  - File: `.claude/hooks/pre-commit-deadcode-check.py`
  - Uses grep to detect F401/F841 violations before commits
  - Configurable with bypass flag: `git commit --no-verify`

### Changed
- **Concurrent Provider Execution** (TASK-PERF-001): Replaced sequential execution with asyncio.gather()
  - Performance: ~3x speedup (0.3s → 0.1s with 3 providers)
  - Added per-provider timeout enforcement using asyncio.wait_for()
  - Implemented partial failure handling (one provider failure doesn't crash orchestrator)
  - Test coverage: 4/4 tests passing (concurrent execution, speedup, partial failure, timeout)
- **UnifiedAsyncRouter**: Added optional dependency injection for testing
  - Added `local_router` and `web_router` optional parameters to `__init__()`
  - Allows tests to inject mock or real AsyncSearchRouter instances
  - Fully backwards compatible - default construction still works
- **Result Synthesis**: Added `synthesize_with_got()` method for GoT integration
  - Returns both structured analysis and formatted markdown
  - Graceful degradation if GoT module unavailable
- **Backend Refactoring**: CDSBackend and GrepBackend now extend BaseLocalBackend
  - CDSBackend: 442 → 413 lines (29 lines saved)
  - GrepBackend: 168 → 141 lines (27 lines saved)
  - Shared logic in BaseLocalBackend (74 lines)

### Removed
- **Persona Memory Backend**: Removed from search-research package (domain violation fix)
  - Broad "ALWAYS" directive: `/all` is now the default entry point for any search query
  - Auto mode optimization: Checks local first (<1s), expands to web only if needed (5-10s)
  - New trigger phrases: "search for", "find", "look for", "what do we know about", "search"
  - Simplified mental model: Single tool for all search needs; `/search` and `/research` available for explicit use only
  - Design documentation: `AUTO_TRIGGERING_DESIGN.md` with rationale, testing strategy, and performance analysis
- **Graph-of-Thought (GoT) Analysis**: Complete GoT reasoning system for search results
  - Node extraction: Constraints, ideas, risks, components, data flows
  - Edge analysis: Jaccard similarity for supports/contradicts/unrelated relationships
  - Clustering: Connected component detection with confidence scoring
  - Cycle detection: Identifies circular dependencies and deadlock risks
  - Integration with result synthesis for automatic analysis
- **Knowledge Graph (KG) Backend**: Entity-based search with AND queries
  - Entity search with exact/partial matching and confidence scoring
  - AND queries: `entity1 AND entity2 AND entity3` syntax
  - Conversation mapping: Tracks entities across conversation IDs
  - Graceful degradation: Handles missing/invalid data without crashes
- **Comprehensive Test Coverage**: 141 tests for GoT and KG functionality
  - GoT tests: Node extraction, edge analysis, clustering, cycle detection
  - KG tests: Initialization, index building, entity search, AND queries
- **Sample Knowledge Graph Data**: Test entities and conversation mappings
  - 10 entities with types, categories, and descriptions
  - 10 conversations with entity relationships

### Changed
- **Result Synthesis**: Added `synthesize_with_got()` method for GoT integration
  - Returns both structured analysis and formatted markdown
  - Graceful degradation if GoT module unavailable

### Removed
- **Persona Memory Backend**: Removed from search-research package (domain violation fix)
  - **Breaking Change**: Persona Memory backend (`persona_memory_backend.py`) removed from `/all` skill
  - **Migration**: Persona Memory functionality moved to `/s` Strategy skill where it belongs
  - **Rationale**: Persona Memory stores creative outputs from `/s` multi-persona brainstorming (INNOVATOR, pragmatist, critic, expert), not technical search results
  - **Impact**: `/all` now searches only technical sources (code, docs, web) as intended
  - **Migration Path**: Use `/s "query" --recall` to search previous brainstorm sessions (requires `/s` skill integration)
  - **Files Modified**:
    - `src/search_research/router.py`: Removed persona backend initialization (2 locations)
    - `src/search_research/backends/local/__init__.py`: Removed persona exports
    - `src/search_research/backends/local/persona_memory_backend.py`: Deleted entirely (331 lines)
    - `tests/test_persona_removal.py`: Added TDD tests to verify removal
  - **Tests Added**: 2 tests to verify persona backend removal from router and exports

### Documentation
- **README.md**: Added Graph-of-Thought and Knowledge Graph sections
  - GoT usage examples and capabilities
  - KG backend usage and configuration
  - Code examples for both features

### Testing
- **test_got_analysis.py**: 386 lines of comprehensive GoT tests
  - Node extraction tests (constraint, idea, risk, keyword patterns)
  - Edge analysis tests (supports, contradicts, unrelated detection)
  - Clustering tests (min size, confidence calculation)
  - Cycle detection tests (acyclic/cyclic graphs)
  - Integration tests (full workflow, edge cases)
- **test_kg_backend.py**: 388 lines of comprehensive KG tests
  - Initialization tests (default/custom paths, initial state)
  - Index building tests (valid/missing/invalid JSON files)
  - Entity search tests (exact/partial match, case insensitive)
  - AND query tests (conversation finding, space normalization)
  - Validation tests (empty queries, limits, edge cases)
- **test_unified_router.py**: Refactored to use dependency injection pattern
  - Eliminated fragile property patching and double-patching bugs
  - Tests now verify actual behavior instead of mock interactions
  - All 32 tests passing with 93% code coverage for unified_router.py
  - More robust and maintainable test suite
  - See `DEPENDENCY_INJECTION_REFACTOR.md` for full details

---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial package structure
- Basic router classes (SearchRouter, ResearchRouter, UnifiedRouter)
- Mode system (FAST, COMPREHENSIVE, CUSTOM)
- SearchResult schema
- Test infrastructure with pytest

## [0.1.0] - 2026-03-05

### Added
- Initial release
- PRD documentation
- Package setup and configuration

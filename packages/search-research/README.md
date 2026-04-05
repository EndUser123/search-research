# search-research

> Unified search and research package with local code/knowledge search and web research capabilities

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](https://github.com/EndUser123/search-research)

## Overview

**search-research** provides a unified interface for searching across multiple knowledge sources, combining fast local code/knowledge search with comprehensive web research.

### Key Features

- **Fast Local Search** (<1s): Code patterns, documentation, chat history, knowledge base
- **Comprehensive Web Search** (5-10s): Web providers with HyDE query enhancement
- **Intelligent Routing**: Auto-detects query intent (local vs web vs mixed)
- **Unified API**: Single package for both `/search` and `/research` commands
- **Graceful Degradation**: Works without API keys, local always available

## Installation

```bash
# Basic installation (core backends only)
pip install search-research

# Full installation (all features including web providers)
pip install search-research[all]

# Development installation
pip install -e "P:/packages/search-research[all]"

# Migrating from unified-search?
# See "Migrating from unified-search" section below
```

## Quick Start

### Fast Local Search

```python
from core import SearchRouter

router = SearchRouter()
results = router.search("FastAPI patterns", limit=10)
# Returns: <1s, local backends only
```

### Comprehensive Web Search

```python
from core import ResearchRouter

router = ResearchRouter()
results = router.search("FastAPI best practices", limit=20)
# Returns: 5-10s, all backends with HyDE
```

### Full Control

```python
from core import UnifiedRouter, Mode

router = UnifiedRouter(mode=Mode.FAST)
results = router.search(
    "FastAPI patterns",
    limit=10,
    web=True,  # Include web providers
    hyde=False  # Disable HyDE
)
```

## Migrating from unified-search

If you're currently using `EnhancedUnifiedSearchRouter` from `__csf`, here's how to migrate:

### Installation

```bash
# Install the new package
pip install search-research[all]

# Or for development
pip install -e "P:/packages/search-research[all]"
```

### Code Changes

**Old code:**
```python
from search.unified_router import EnhancedUnifiedSearchRouter

router = EnhancedUnifiedSearchRouter(
    chs_backend=chs_backend,
    cks_backend=cks_backend,
    enable_cache=True,
)
results = router.search("query", limit=10)
```

**New code:**
```python
from core import SearchRouter

router = SearchRouter(
    cache_ttl=3600,
    enable_cache=True,
)
results = router.search("query", limit=10)
```

### Key Differences

- **Simpler API**: No manual backend initialization needed
- **Concurrent execution**: Parallel backend searches (faster)
- **8 local backends**: cds, grep, skills, chs, cks, kg, rlm, persona
- **Graceful degradation**: Failed backends don't crash search
- **Better performance**: ThreadPoolExecutor with timeouts

### Research Mode

For comprehensive web search, use `ResearchRouter`:

```python
from core import ResearchRouter

router = ResearchRouter(
    hyde_enabled=True,
    web_providers=["tavily", "brave", "serper"],
)
results = await router.search_async("FastAPI best practices", limit=20)
```

### CLI Commands

**Old:**
```bash
# Using __csf internal command
python -m __csf.src.cli.nip.search_enhanced "query"
```

**New:**
```bash
# Fast local search
search-research "query" --backend cds grep

# Comprehensive web research
research-research "query" --limit 30 --hyde
```

### Deprecation Timeline

- **2026-03-06**: unified-search deprecated
- **2026-06-01**: Migration period ends
- **2026-09-01**: End of life (Q3 2026)

For detailed migration guide, see [MIGRATION.md](MIGRATION.md)

## Search Modes

### FAST Mode (Default for SearchRouter)

**Characteristics:**
- **Backends**: Local only (CDS, Grep, CHS, CKS, RLM, Persona, MultiLang, NotebookLM)
- **Timeout**: 0.5s per backend
- **HyDE**: Disabled
- **Speed**: <1s total
- **Use case**: Quick code search, finding patterns

**Example:**
```python
router = SearchRouter()
results = router.search("FastAPI route decorator")
```

### COMPREHENSIVE Mode (Default for ResearchRouter)

**Characteristics:**
- **Backends**: All (local + web + NotebookLM)
- **Timeout**: 5s per web backend, 0.5s per local backend
- **HyDE**: Enabled
- **Speed**: 5-10s total
- **Use case**: Learning new topics, best practices, research

**Example:**
```python
router = ResearchRouter()
results = router.search("FastAPI best practices for authentication")
```

## Backends

### Local Backends

| Backend | Description | Source |
|---------|-------------|--------|
| CDS | Code Documentation Search (AST-based) | Docstrings |
| Grep | Code Pattern Search (AST-based) | Function/class names |
| CHS | Chat History Search | Conversation history |
| CKS | Constitutional Knowledge System | Knowledge base |
| KG | Knowledge Graph Search | Entity/conversation relationships |
| RLM | Recursive Language Model | Code generation |
| Persona | Persona Memory Search | Context-aware search |
| MultiLang | Multi-language code search | Tree-sitter parsing |
| NotebookLM | NotebookLM MCP integration | AI-synthesized research |

### Web Backends

| Backend | Description | API Key Required |
|---------|-------------|------------------|
| Tavily | AI-powered search with synthesis | Yes (or graceful degradation) |
| Serper | Google search with knowledge graph | Yes (or graceful degradation) |
| Exa | Neural/semantic search | Yes (or graceful degradation) |

**Note:** Web backends gracefully degrade when API keys are missing (skip with warning).

## Configuration

### API Keys

Web providers require API keys. Configure via environment variables:

```bash
export TAVILY_API_KEY="your-tavily-key"
export SERPER_API_KEY="your-serper-key"
export EXA_API_KEY="your-exa-key"
```

Without API keys, web backends are skipped with a warning message.

## Result Format

All search results follow a unified schema:

```python
@dataclass
class SearchResult:
    # Content
    title: str                    # Result title
    content: str                  # Result content/snippet
    url: str | None               # Source URL (web results)
    file_path: str | None         # File path (local results)
    line_number: int | None       # Line number (code results)

    # Metadata
    source: str                   # Backend name (e.g., "CDS", "Tavily")
    score: float                  # Relevance score (0-1)
    metadata: dict[str, Any]      # Backend-specific metadata

    # Timestamps
    created_at: datetime          # When result was generated
    cached: bool = False          # Whether from cache
```

## Advanced Research Components

search-research includes advanced research capabilities migrated from the research-skill and research-enhancement packages.

### Analysis Components

Located in `core.analysis`

**GapAnalyzer** - Detect coverage gaps and generate follow-up queries
```python
from core import GapAnalyzer

analyzer = GapAnalyzer()
gaps = analyzer.detect_gaps(
    results,
    topics={"python", "fastapi"},
    source_types={"docs", "community"},
    domains={"technical"}
)
# Returns: List[CoverageGap] sorted by severity
```

**ContradictionDetector** - Detect contradictions between sources
```python
from core import ContradictionDetector

detector = ContradictionDetector()
contradictions = detector.detect_contradictions(results)
# Returns: List[Contradiction] with confidence scores
```

**DensityCalculator** - Calculate numeric and technical density
```python
from core import DensityCalculator

calculator = DensityCalculator()
density = calculator.compute_density(results)
# Returns: float (0.0-1.0) indicating content density
```

**TopicClusterer** - Topic clustering with novelty tracking
```python
from core import TopicClusterer, NoveltyTracker

clusterer = TopicClusterer(top_n=10)
clusters = clusterer.extract_topics(results)
tracker = NoveltyTracker(novelty_threshold=0.1)
novelty = tracker.compute_novelty(clusters, coverage_state)
# Returns: float (0.0-1.0) indicating novelty level
```

### Orchestration Components

Located in `core.orchestration`

**PhaseController** - Two-phase research with novelty-based saturation
```python
from core import PhaseController

controller = PhaseController(
    search_provider=search_provider,
    normalizer=normalizer,
    budget=1.0,
    max_iterations=5
)
result = await controller.execute_research("FastAPI authentication")
# Automatically iterates until saturation or budget exhausted
```

**CostTracker** - Track API costs and budgets
```python
from core import CostTracker

tracker = CostTracker(budget_limit=1.0)
tracker.track_request(provider="google", cost=0.001)
tracker.check_budget()  # Returns True if under budget
total_cost = tracker.get_total_cost()
```

### Processing Components

Located in `core.processing`

**ResultNormalizer** - Normalize results from multiple providers
```python
from core import ResultNormalizer

normalizer = ResultNormalizer()
normalized = normalizer.normalize_result(raw_result, provider_name="google")
# Returns: NormalizedResult with standardized fields
```

### Enhancement Components

Located in `core.enhancement`

**SimplifiedDependencyAnalyzer** - Analyze query dependencies
```python
from core import SimplifiedDependencyAnalyzer

analyzer = SimplifiedDependencyAnalyzer()
dependencies = analyzer.analyze_dependencies(
    query="How to implement OAuth2 in FastAPI"
)
# Returns: QueryDependencies with complexity score
```

**LearningSystem** - Learn patterns from feedback
```python
from core import LearningSystem

learning = LearningSystem()
learning.collect_feedback(
    research_id="session_1",
    query="FastAPI patterns",
    modes_used=["octocode", "web"],
    predicted_quality=4.5,
    actual_quality_rating=4.2
)
recommendation = learning.get_pattern_based_recommendation("FastAPI patterns")
# Returns: dict with recommended modes and confidence
```

**ModeRelationshipMapper** - Find optimal mode combinations
```python
from core import ModeRelationshipMapper

mapper = ModeRelationshipMapper()
optimal = mapper.find_optimal_combination(
    query="FastAPI authentication",
    budget=0.5
)
# Returns: ModeCombination with expected performance
```

**MultiModeOrchestrator** - Execute multiple research modes in parallel
```python
from core import MultiModeOrchestrator

orchestrator = MultiModeOrchestrator(modes=["octocode", "web"])
result = await orchestrator.execute_research("FastAPI patterns", timeout=10)
# Returns: OrchestratedResult with synthesis from all modes
```

**QualityPredictor** - Predict result quality
```python
from core import QualityPredictor

predictor = QualityPredictor()
quality = predictor.predict_quality(
    query="FastAPI patterns",
    modes=["octocode", "web"],
    domain="technical"
)
# Returns: OptimizationResult with quality score
```

### Testing Migrated Components

Test suite for migrated components is located in `tests/test_migrated/`:

```bash
# Run all migrated component tests
pytest tests/test_migrated/ -v

# Run specific component tests
pytest tests/test_migrated/test_analysis.py -v
pytest tests/test_migrated/test_orchestration.py -v
pytest tests/test_migrated/test_enhancement.py -v
```

**Test Coverage:**
- 141 tests covering all migrated components
- Tests for gap analysis, contradiction detection, density calculation
- Tests for phase orchestration, cost tracking
- Tests for dependency analysis, learning system, mode orchestration
- Comprehensive edge case coverage


## Contrib Modules

### Semantic Daemon

The `contrib.semantic_daemon` module provides a Windows named pipe server for fast semantic search with CKS (Constitutional Knowledge System) and CHS (Chat History Search).

**Location:** `search_research.contrib.semantic_daemon`

**Features:**
- **Named pipe IPC**: Fast communication via Windows named pipes
- **Async CHS indexing**: Background chat history indexing, non-blocking requests
- **Automatic FAISS refresh**: Incremental updates every 10 minutes idle
- **Concurrent request handling**: ThreadPoolExecutor with configurable workers
- **Auto-start client**: Client automatically starts daemon if not running
- **Graceful fallback**: Falls back to direct backend calls on daemon failure

**Usage:**

```python
from search_research.contrib.semantic_daemon import (
    UnifiedSemanticDaemon,
    DaemonClient,
)

# Start daemon (usually auto-started by client)
daemon = UnifiedSemanticDaemon()
if not daemon.start():
    print("Failed to start daemon")

# Use client with auto-start and fallback
client = DaemonClient(
    auto_start=True,
    enable_fallback=True,
    timeout=30.0
)

# Search CKS (Constitutional Knowledge System)
results = client.search("cks", "async patterns", limit=5)

# Search CHS (Chat History Search)
results = client.search("chs", "conversation topic", limit=10)

# Query daemon actions
result = client.query(
    "skill_intent",
    {"command": "from src.rca import SimpleRCAEngine", "skill": "rca"}
)
```

**Installation:**

```bash
# Basic package installation
pip install search-research

# With daemon dependencies (Windows only)
pip install search-research[daemon]
```

**Documentation:** See `contrib/semantic_daemon/CLAUDE.md` for complete documentation including:
- Architecture and wire protocol
- Async CHS indexing details
- Dynamic pipe names and discovery file
- FAISS index management and rollover strategy
- Platform support and dependencies

## Graph-of-Thought (GoT) Analysis

search-research includes Graph-of-Thought reasoning for analyzing search results and discovering hidden relationships.

### Capabilities

**Node Extraction** - Automatically categorize information from search results:
- **Constraints**: Requirements ("must use", "required to", "should have")
- **Ideas**: Implementation approaches ("can use", "could implement", "might improve")
- **Risks**: Potential issues ("risk of", "warning", "danger", "error")
- **Components**: System boundaries and entities
- **Data flows**: Communication paths

**Edge Analysis** - Detect relationships between nodes:
- **Supports**: One idea enables another (Jaccard similarity)
- **Contradicts**: One idea conflicts with another
- **Unrelated**: No direct relationship
- **Depends**: Component dependencies

**Clustering** - Group related results automatically:
- Minimum cluster size filtering
- Confidence scoring per cluster
- Connected component detection

**Cycle Detection** - Find circular dependencies:
- Identifies deadlock risks
- Reports architectural circular reasoning
- Helps break circular patterns

### Usage

```python
from core import SearchRouter
from core.processing.got_analysis import GotAnalyzer

# Run search with GoT analysis
router = SearchRouter()
results = router.search("authentication patterns", limit=10)

# Analyze results with GoT
analyzer = GotAnalyzer(min_cluster_size=2)
got_analysis = analyzer.analyze_results(results)

# Get formatted output
formatted = analyzer.format_results_with_got(results, got_analysis)
print(formatted)

# Example output:
# **GoT Analysis**
#
# Nodes: 15 (Constraints: 3, Ideas: 7, Risks: 3, Components: 2)
# Edges: 8 (Supports: 5, Contradicts: 2, Unrelated: 1)
# Clusters: 2
# Cycles: 0
#
# **Summary**
# Analyzed 10 search results using Graph-of-Thought reasoning.
# Found 3 constraint nodes, 7 idea nodes, and 3 risk nodes.
# Results cluster into 2 groups with average confidence 0.76.
# No circular dependencies detected.
```

### Integration with Result Synthesis

GoT analysis is automatically integrated into result synthesis:

```python
from search_research.results import ResultSynthesizer

synthesizer = ResultSynthesizer()
synthesis = synthesizer.synthesize_with_got(
    results=results,
    query="authentication patterns"
)

# Returns:
# {
#     "summary": "Comprehensive synthesis...",
#     "got_analysis": {...},
#     "got_formatted": "**GoT Analysis**..."
# }
```

---

## Knowledge Graph (KG) Backend

The KG backend provides entity-based search and AND queries across conversation history.

### Capabilities

**Entity Search** - Find conversations by entities:
- Exact match: "async" → finds all mentions of "async"
- Partial match: "graph" → finds "knowledge graph", "graph database"
- Case-insensitive: "ASYNC" and "async" return same results
- Confidence scoring: Higher scores for better matches

**AND Queries** - Find conversations with multiple entities:
- `query: "async AND rag"` → Only conversations with BOTH entities
- `query: "async AND python AND rag"` → All three required
- Normalizes spaces: `async   AND   rag` works correctly

**Conversation Mapping** - Track entities across conversations:
- Maps entities to conversation IDs
- Supports multi-entity conversations
- Handles missing/invalid data gracefully

### Data Structure

The KG backend expects two JSON files in the knowledge graph directory:

**entities.json** - Entity definitions:
```json
[
  {
    "text": "async",
    "type": "concept",
    "category": "programming",
    "description": "Asynchronous programming pattern"
  },
  {
    "text": "knowledge graph",
    "type": "concept",
    "category": "data_structure",
    "description": "Graph-based knowledge representation"
  }
]
```

**conversation_entities.json** - Conversation mappings:
```json
{
  "conv_001": ["async", "await", "python"],
  "conv_002": ["knowledge graph", "entity extraction"],
  "conv_003": ["async", "rag", "vector"]
}
```

### Usage

```python
from core import SearchRouter

router = SearchRouter()

# Single entity search
results = router.search("async", limit=10)
# Returns: All conversations mentioning "async"

# AND query for multiple entities
results = router.search("async AND rag", limit=10)
# Returns: Only conversations with BOTH "async" AND "rag"

# Partial match
results = router.search("graph", limit=10)
# Returns: "knowledge graph", "graph database", etc.
```

### Configuration

Set the knowledge graph data path in your configuration:

```python
from core import SearchRouter
from pathlib import Path

router = SearchRouter(
    kg_data_path=Path("P:/projects/kg_builder/knowledge_graph_output")
)
```

The backend will automatically:
- Build index from entities.json and conversation_entities.json
- Gracefully handle missing/invalid files
- Support searches before manual index building (auto-index on first search)

### Graceful Degradation

If knowledge graph files are missing or invalid:
- Backend logs warning but continues operating
- Returns empty results rather than crashing
- Allows search-research to function without KG data


## Integration

### With `/search` Command (CSF)

```python
from core import SearchRouter

router = SearchRouter()
results = router.search("FastAPI patterns", limit=10)
# Fast local search, <1s
```

### With `/research` Command (research-skill)

```python
from core import ResearchRouter

router = ResearchRouter()
results = router.search("FastAPI best practices", limit=20)
# Comprehensive search with HyDE, 5-10s
```

## Development

### Setup

```bash
git clone https://github.com/EndUser123/search-research
cd search-research
pip install -e ".[all]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test
pytest tests/test_router.py
```

**Testing Approach:**

The test suite uses dependency injection for robust, maintainable tests. For example, `UnifiedAsyncRouter` tests inject mock or real router instances instead of patching internal properties:

```python
# Create mock routers with controlled behavior
mock_local = AsyncMock()
mock_local.search_async = AsyncMock(return_value=local_results)

mock_web = AsyncMock()
mock_web.search_web_providers_async = AsyncMock(return_value=web_results)

# Inject routers directly
router = UnifiedAsyncRouter(
    mode="auto",
    local_router=mock_local,
    web_router=mock_web
)

# Test behavior, not mock interactions
results = await router.search_async("test query")
assert len(results) == expected_count
```

This approach:
- ✅ Eliminates fragile property patching (`@property` can't be patched)
- ✅ Prevents double-patching bugs (second patch overriding first)
- ✅ Tests verify actual behavior instead of mock call counts
- ✅ Integration tests use real routers where possible
- ✅ Fully backwards compatible - default construction still works

See `DEPENDENCY_INJECTION_REFACTOR.md` for complete details.

### Code Quality

```bash
# Format code
ruff check core/ --fix

# Type checking
mypy core/
```

## Performance

| Mode | Target | Maximum |
|------|--------|----------|
| FAST | <1s | 1.5s |
| COMPREHENSIVE | 5-10s | 15s |

**Backend Timeouts:**
- Local backends: 0.5s
- Web backends: 5s

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built on top of the excellent work from:
- unified-search package
- research-skill package
- CSF framework

---

**Version:** 0.1.0
**Status:** Alpha (Under active development)

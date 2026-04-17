# PRD: Unified Search & Research

**Version:** 1.0
**Status:** Draft
**Date:** 2026-03-05

---

## 1. Executive Summary

**Problem:** Today, developers must choose between `/search` (code only) and `/research` (web only), and can't combine sources in a single query. Results vary between commands, it's unclear which to use for mixed questions, and many powerful features are hidden behind complex flags.

**Solution:** A unified search experience that automatically detects whether you need code, web, or both - and returns the best results from all relevant sources in a single, consistent format. Includes intelligent features like typo tolerance, source credibility scoring, and research report generation.

**Success Criteria:**
- Single command (`/search`) handles all query types intelligently
- Mixed queries (code + web) return unified, ranked results
- Results show clear source attribution (codebase vs web vs credibility)
- Zero performance regression on existing workflows
- 90%+ user satisfaction with result relevance
- Typo-tolerant search handles misspelled queries
- Research reports with citations available for complex topics

---

## 2. User Personas

**Primary: Solo Developer**
- Works across multiple projects daily
- Needs to find code patterns, API docs, and best practices quickly
- Values speed and accuracy over configuration
- Doesn't want to remember different commands for different query types
- Sometimes typos queries or forgets exact syntax
- Needs research reports with proper citations for documentation

**Secondary: AI-Assisted Developer**
- Uses AI agents for code exploration and research
- Needs consistent result formats across all search types
- Expects search to "just work" without manual routing
- Wants to trust that results are comprehensive and credible
- Benefits from auto-generated research summaries

---

## 3. User Stories

### US-001: Universal Search Command

**Description:** As a developer, I want to use a single command for all my searches so I don't have to think about whether I need code or web results.

**Acceptance Criteria:**
- [ ] `/search "FastAPI patterns"` returns relevant code from my codebase
- [ ] `/search "FastAPI best practices"` returns relevant web articles
- [ ] `/search "how to use FastAPI with websockets"` returns both code examples AND web tutorials
- [ ] Search completes in <1s for code-only queries
- [ ] Search completes in 5-10s for web or mixed queries
- [ ] Results clearly indicate source (local codebase vs web URL)
- [ ] No need to use `/research` command anymore (it becomes an alias)

### US-002: Intelligent Source Selection

**Description:** As a developer, I want the system to automatically figure out which sources to search so I don't have to specify flags or options.

**Acceptance Criteria:**
- [ ] Queries mentioning my codebase (function names, file paths) search code only
- [ ] Queries asking "how to", "best practices", "latest" search web + code
- [ ] Ambiguous queries search both sources and merge results
- [ ] Can override with `--local-only` or `--web-only` flags if needed
- [ ] Intent detection is >90% accurate on test queries

### US-003: Unified Result Format

**Description:** As a developer, I want all results to look and behave the same regardless of source so I can quickly scan and compare them.

**Acceptance Criteria:**
- [ ] All results show: title, snippet/relevance, source attribution
- [ ] Code results link to file:line
- [ ] Web results link to full URL
- [ ] Results ranked by relevance (not by source)
- [ ] Can filter by source after seeing results (e.g., "show only code")
- [ ] Source credibility shown for web results (high/medium/low)

### US-004: Best Answers From Everywhere

**Description:** As a developer, I want the most relevant results from ALL sources, not just the first source that returns something.

**Acceptance Criteria:**
- [ ] Results from code + web sources merged into single ranked list
- [ ] Duplicates removed (same content from multiple sources)
- [ ] Ranking considers both code match quality AND web relevance
- [ ] Top 10 results include best matches from all sources
- [ ] Can see which sources were searched after the fact
- [ ] Query enhancement (HyDE) improves web search relevance for complex queries

### US-005: Performance Without Compromise

**Description:** As a developer, I want search to be fast but still comprehensive, so I don't have to choose between speed and quality.

**Acceptance Criteria:**
- [ ] Code-only queries return in <1s (same as today)
- [ ] Web queries return in 5-10s (same as `/research` today)
- [ ] Mixed queries parallelize sources (not sequential)
- [ ] Progress indicator shows which sources are being searched
- [ ] Can cancel long-running queries with Ctrl+C
- [ ] Repeated queries return instantly from cache (<100ms)

### US-006: Flawless Error Handling

**Description:** As a developer, I want search to work even when some sources fail, so I still get partial results instead of complete failure.

**Acceptance Criteria:**
- [ ] Missing API keys don't crash search (skip web with warning)
- [ ] Slow sources timeout and return results from other sources
- [ ] Network errors show clear message but return local results
- [ ] All errors are actionable (tell user what to fix)
- [ ] Backend health tracking prevents repeatedly failing backends from slowing searches

### US-007: Typo Tolerance

**Description:** As a developer, I want search to handle my typos so I don't need perfect spelling to find what I need.

**Acceptance Criteria:**
- [ ] Misspelled queries return corrected results ("FastAPII" → "FastAPI")
- [ ] Fuzzy matching handles up to 2 character edits
- [ ] Shows "Did you mean?" suggestion for significant corrections
- [ ] Works for both code and web searches

### US-008: Research Reports

**Description:** As a developer, I want comprehensive research reports with proper citations when I'm exploring complex topics.

**Acceptance Criteria:**
- [ ] `/search "topic" --report` generates markdown research summary
- [ ] Reports include key insights from multiple sources
- [ ] Proper citations in APA/MLA format included
- [ ] Source credibility assessment for each citation
- [ ] Reports exported to MD/JSON/PDF as needed
- [ ] Reports generated from cached results when possible

### US-009: Smart Filtering & Stats

**Description:** As a developer, I want to filter results and see search statistics so I can refine my queries and understand what's being searched.

**Acceptance Criteria:**
- [ ] Can filter results by time (last day, week, month)
- [ ] Can limit results per source (`--per-source 5`)
- [ ] `/search --stats` shows cache hit rate, backend health
- [ ] Can see which backends are enabled/healthy
- [ ] Debug mode shows query routing decisions

### US-010: Advanced Result Analysis

**Description:** As a developer, I want automatic analysis of search results so I can quickly understand contradictions, insights, and information quality.

**Acceptance Criteria:**
- [ ] Contradiction detection flags conflicting information
- [ ] Temporal quality assessment weights recent results higher
- [ ] Insight extraction highlights key findings
- [ ] Semantic synthesis combines related results into summary
- [ ] Source credibility scores shown for all results

### US-011: Intelligent Ranking & Fusion

**Description:** As a developer, I want results ranked using multiple methods combined so I get the most relevant results regardless of ranking algorithm.

**Acceptance Criteria:**
- [ ] Hybrid scoring combines BM25 + cosine similarity
- [ ] RRF (Reciprocal Rank Fusion) merges multiple ranking methods
- [ ] MMR diversification ensures result variety
- [ ] Results re-ranked after all sources complete

### US-012: Auto-Learning & Optimization

**Description:** As a developer, I want the system to learn from my searches so future queries are more accurate.

**Acceptance Criteria:**
- [ ] Auto-learning mode improves routing based on past queries
- [ ] Valuable findings auto-ingested into knowledge base (CKS)
- [ ] Query expansion generates variants for better coverage
- [ ] Learning can be disabled for privacy

---

## 4. Functional Requirements

**FR-1:** Single command `/search` must handle code-only, web-only, and mixed queries
**FR-2:** System must automatically detect query intent (code vs web vs both)
**FR-3:** Results from multiple sources must be merged into unified ranked list
**FR-4:** Results must show clear source attribution (codebase file vs web URL)
**FR-5:** Code-only queries must complete in <1s
**FR-6:** Web or mixed queries must complete in 5-10s
**FR-7:** System must gracefully degrade when sources fail (return partial results)
**FR-8:** Result ranking must consider relevance from all sources, not just first source
**FR-9:** Duplicates across sources must be removed from results
**FR-10:** System must support manual overrides (`--local-only`, `--web-only`)
**FR-11:** System must cache repeated queries (LRU with 3600s TTL)
**FR-12:** System must use HyDE query enhancement for web searches to improve relevance
**FR-13:** System must handle typos via fuzzy matching (max 2 edit distance)
**FR-14:** System must track backend health with exponential backoff for failing sources
**FR-15:** System must show source credibility scores for web results
**FR-16:** System must generate research reports with citations (APA/MLA formats)
**FR-17:** System must support time-based filtering (day/week/month)
**FR-18:** System must expose cache stats and backend health via `/search --stats`
**FR-19:** System must support semantic synthesis of results
**FR-20:** System must detect and flag contradictions in results
**FR-21:** System must assess temporal quality of results
**FR-22:** System must support MMR diversification for result variety
**FR-23:** System must support RRF fusion for combining ranking methods
**FR-24:** System must support hybrid scoring (BM25 + cosine similarity)
**FR-25:** System must implement provider failover (skip failing providers)
**FR-26:** System must track provider expiration and health over time
**FR-27:** System must provide provider diagnostics for troubleshooting
**FR-28:** System must support query expansion (generate query variants)
**FR-29:** System must support auto-learning mode (improve from past queries)
**FR-30:** System must detect and crawl URLs in results
**FR-31:** System must extract insights from aggregated results
**FR-32:** System must auto-ingest valuable findings into CKS

**FR-33:** System must support streaming results for long-running searches
**FR-34:** System must provide progress callbacks for user feedback during search
**FR-35:** System must support result filtering and sorting options
**FR-36:** System must support pagination for large result sets
**FR-37:** System must implement configuration hierarchy (env vars → config file → defaults)
**FR-38:** System must validate API keys at startup
**FR-39:** System must provide provider health monitoring with automatic failover
**FR-40:** System must validate configuration with clear error messages
**FR-41:** System must conduct technical debt assessment before implementation
**FR-42:** System must evaluate external provider reliability as part of risk analysis
**FR-43:** System must establish performance baseline metrics before implementation
**FR-44:** System must provide detailed fallback strategies for each failure scenario

---

## 6. Advanced Features (v1.1+)

### Additional Providers (Beyond MVP)

**Code & Knowledge Sources:**
- **GitHub Search** - Search code repositories
- **NotebookLM** - Search interactive notebooks
- **Knowledge Search** - Various knowledge bases
- **Persona Search** - Context-aware search
- **Zai Search** - Alternative AI search
- **GLM Search** - Chinese language model
- **Perplexity** - AI-powered search
- **WebReader** - Content extraction from URLs

**ML & Performance:**
- **GPU Accelerated Search** - Use GPU when available for ML operations
- **Auto-Learning Mode** - Improve routing based on past query performance

**Content Processing:**
- **URL Detection & Crawling** - Find and process URLs in search results
- **Insight Extraction** - Pull key insights from aggregated results
- **Semantic Synthesis** - Combine results into cohesive summary

**Reporting (v1.1):**
- **Export Formats** - MD/JSON/PDF
- **Citation Formatting** - APA/MLA/Chicago

### Implementation Priority

**MVP (v1.0) - Core 9 User Stories:**
- US-001 through US-009 (single command, auto-routing, unified format, etc.)

**v1.1 - Advanced Analytics:**
- US-010 (Result Analysis)
- US-011 (Ranking & Fusion)
- US-012 (Auto-Learning)
- Advanced providers (GitHub, NotebookLM, Perplexity, etc.)
- Export formats

**v1.2 - Full Optimization:**
- GPU acceleration
- Query expansion
- Auto-ingestion to CKS
- All remaining providers

---

## 7. Non-Functional Requirements

---

## 5. Non-Functional Requirements

**NFR-1:** Backward Compatibility - Existing `/search` workflows must continue working
**NFR-2:** Backward Compatibility - Existing `/research` workflows must continue working
**NFR-3:** Performance - No regression on code-only search speed
**NFR-4:** Reliability - >99% of searches return results (no hard failures)
**NFR-5:** Usability - <5 seconds to learn how to use (intuitive interface)
**NFR-6:** Maintainability - Fuzzy matching, HyDE, and health tracking must be testable

---

## 6. Success Metrics

- **Adoption:** 80% of users switch to unified `/search` within 2 weeks
- **Satisfaction:** 90%+ rate results as "relevant" or "very relevant"
- **Performance:** 95% of code queries <1s, 95% of web queries <10s
- **Reliability:** <1% of searches fail completely
- **Quality:** Intent detection accuracy >90% on test corpus
- **Cache Hit Rate:** >50% for repeated queries in active sessions
- **Typo Recovery:** >80% of misspelled queries return relevant results

---

## 7. Out of Scope (Non-Goals)

- ~~Custom search result filtering~~ (deferred to v1.1)
- ~~Search result history/saved searches~~ (deferred to v1.2)
- ~~Advanced relevance tuning per user~~ (deferred to v2.0)
- ~~UI for result preview/rendering~~ (CLI only for now)
- ~~Real-time search as you type~~ (not feasible for CLI)
- ~~Custom citation formats beyond APA/MLA~~ (deferred to v1.1)

---

## 8. Feature Mapping: Existing → New System

| Feature | unified-search | research-skill | search-research |
|---------|----------------|----------------|-----------------|
| Local backends (8) | ✅ | ❌ | ✅ |
| Web backends (5) | ❌ | ✅ | ✅ |
| Query caching | ✅ | ❌ | ✅ |
| HyDE enhancement | ❌ | ✅ | ✅ |
| Fuzzy matching | ✅ | ❌ | ✅ |
| Backend health | ✅ | ❌ | ✅ |
| Deduplication | ✅ | ✅ | ✅ |
| Result aggregation | ✅ | ✅ | ✅ |
| Intent detection | ❌ | ⚠️ partial | ✅ |
| Source credibility | ❌ | ⚠️ partial | ✅ |
| Research reports | ❌ | ✅ | ✅ |
| Citation formatting | ❌ | ✅ | ✅ |
| Time filtering | ✅ | ❌ | ✅ |
| Stats/debug mode | ✅ | ❌ | ✅ |

**Legend:** ✅ Fully implemented | ⚠️ Partially implemented | ❌ Not implemented

---

## 9. Risks & Mitigations

### 9.1 Core Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Intent detection makes wrong choice | High | Add manual override flags, log detections for analysis |
| Web search slows down code queries | High | Parallelize sources, timeout slow web backends |
| Users confused by merged results | Medium | Clear source attribution, show which sources searched |
| Breaking existing workflows | High | Maintain backward compatibility, deprecate gradually |
| API key management burden | Low | Graceful degradation without keys, clear docs |
| Cache memory leaks | Medium | LRU size limits (1000 queries), monitoring |
| HyDE adds latency | Medium | Make HyDE optional, measure effectiveness before enabling |
| Fuzzy matching returns wrong results | Medium | Limit to 2 edits, show "Did you mean?" suggestions |

### 9.2 Technical Debt Management (FR-41)

**Assessment Areas:**
- Identify potential architectural bottlenecks in unified router
- Evaluate code duplication between local and web backends
- Assess test coverage gaps for complex features (intent detection, HyDE)
- Review dependency management for optional backends

**Mitigation Strategy:**
- Document known limitations and technical debt tickets
- Schedule quarterly technical debt reviews
- Allocate 20% of sprint time for debt reduction
- Prioritize debt that impacts performance or reliability

### 9.3 Dependency Risk Analysis (FR-42)

**External Provider Reliability:**
- **Tavily**: AI search provider - Rate limits: 1000 req/day
- **Serper**: Google search API - Rate limits: 100 req/day
- **Exa**: Neural search - Rate limits: 1000 req/month
- **Perplexity**: AI search - Rate limits: varies by tier

**Risk Mitigation:**
- Implement request queuing and throttling for each provider
- Track provider uptime and response times
- Automatic failover to alternative providers
- Graceful degradation when all providers exhausted
- Provider health dashboard in `/search --stats`

**Internal Dependencies:**
- **sentence-transformers**: Required for CHS/CKS - 1.5GB model download
- **faiss-cpu**: Required for CKS vector search - 500k item limit
- **tree-sitter**: Optional for MultiLang - slow on large codebases

**Mitigation Strategy:**
- Lazy-load optional dependencies with clear error messages
- Provide fallback implementations (FTS5-only for CHS, hash-based for CKS)
- Document minimum viable vs. full feature set requirements

### 9.4 Performance Regression Testing (FR-43)

**Baseline Metrics (to be established):**
- Code-only search: p50 < 500ms, p95 < 1000ms, p99 < 1500ms
- Web search: p50 < 5s, p95 < 10s, p99 < 15s
- Cache lookup: p50 < 10ms, p95 < 50ms
- Backend timeout: 500ms local, 5s web

**Regression Testing Strategy:**
- Automated performance benchmarks on every PR
- Historical performance tracking (last 30 days)
- Alert on 10% degradation in p95 latency
- Load testing for concurrent searches (10, 50, 100 parallel queries)

**Performance Budget:**
- Router overhead: <50ms
- Result aggregation: <100ms
- Deduplication: <50ms
- Ranking/fusion: <200ms

### 9.5 Fallback Strategies (FR-44)

**Failure Mode 1: Web Provider Timeout**
- Detection: No response within 5s
- Fallback: Return local results only with warning
- Recovery: Retry provider after 60s exponential backoff

**Failure Mode 2: Semantic Embeddings Unavailable**
- Detection: Named pipe connection fails
- Fallback: CHS uses FTS5-only search (keyword matching)
- User Notification: One-time warning per session
- Recovery: Retry embeddings on next search

**Failure Mode 3: Database Locked**
- Detection: SQLite database is locked error
- Fallback: Use in-memory cache for read-only queries
- Recovery: Wait up to 1s for lock release, then proceed

**Failure Mode 4: Out of Memory**
- Detection: Cache exceeds 100MB limit
- Fallback: Flush 50% of cache entries (LRU eviction)
- Recovery: Reduce cache size to 80% of previous limit

**Failure Mode 5: All Web Providers Down**
- Detection: All web providers fail health check
- Fallback: Local-only mode with clear notification
- Recovery: Re-check provider health every 5 minutes
- Manual Override: User can force web search with `--force-web`

---

## 10. API Design Specifications

### 10.1 Streaming Results (FR-33)

**Use Case:** Long-running web searches (5-10s) provide incremental feedback

**API Design:**
```python
async def search_streaming(query: str, **kwargs) -> AsyncIterator[SearchResult]:
    """Stream search results as they arrive from each backend."""
    for backend in active_backends:
        async for result in backend.search_streaming(query):
            yield result
```

**User Experience:**
- Results appear progressively in CLI (not wait for all to complete)
- Progress bar shows "Searching: [CHS] ✓ [CKS] ✓ [Tavily] ⏳..."
- User can cancel mid-search with Ctrl+C and keep partial results

**Implementation:**
- Use `asyncio.as_completed()` for streaming from parallel backends
- Buffer results by time (emit every 500ms) or count (every 5 results)
- Maintain ranking integrity (don't show final ranking until all complete)

### 10.2 Progress Callbacks (FR-34)

**Use Case:** Programmatic integration requires real-time progress updates

**API Design:**
```python
from typing import Callable

def search(
    query: str,
    progress_callback: Callable[[str, float], None] | None = None,
    **kwargs
) -> SearchResults:
    """Execute search with optional progress callback.

    Args:
        query: Search query string
        progress_callback: Callback receiving (stage, progress_pct)
            - stage: "Routing", "Searching CHS", "Searching Tavily", "Aggregating"
            - progress_pct: 0.0 to 1.0
    """
```

**Example Usage:**
```python
def my_progress(stage: str, progress: float):
    print(f"[{progress*100:.0f}%] {stage}")

results = search("FastAPI patterns", progress_callback=my_progress)
# Output:
# [10%] Routing query to local backends
# [30%] Searching CHS
# [50%] Searching Grep
# [80%] Searching Tavily
# [100%] Aggregating results
```

### 10.3 Result Filtering & Sorting (FR-35)

**API Design:**
```python
@dataclass
class ResultFilter:
    """Filter search results after retrieval."""
    backend: list[str] | None = None      # Filter to specific backends
    min_score: float | None = None         # Minimum relevance score
    time_range: str | None = None          # "today", "week", "month"
    source_type: list[str] | None = None   # "code", "web", "knowledge"

@dataclass
class SortOrder:
    """Sort search results."""
    by: str = "score"                      # "score", "date", "backend", "source"
    order: str = "desc"                    # "asc", "desc"

def search(
    query: str,
    filter: ResultFilter | None = None,
    sort: SortOrder | None = None,
    **kwargs
) -> SearchResults:
    """Execute search with filtering and sorting."""
```

**CLI Usage:**
```bash
# Filter to code results only
/search "FastAPI" --filter source_type=code

# Show high-score results from last week
/search "websockets" --filter min_score=0.7,time_range=week

# Sort by date (newest first)
/search "async" --sort by=date,order=desc
```

### 10.4 Pagination (FR-36)

**Use Case:** Large result sets (>100 results) need chunked retrieval

**API Design:**
```python
@dataclass
class Pagination:
    """Paginate search results."""
    page: int = 1              # Page number (1-indexed)
    per_page: int = 20         # Results per page

def search(
    query: str,
    pagination: Pagination | None = None,
    **kwargs
) -> SearchResults:
    """Execute search with pagination.

    Returns:
        SearchResults with pagination metadata:
        - total: Total matching results
        - page: Current page number
        - per_page: Results per page
        - total_pages: Total pages available
    """
```

**CLI Usage:**
```bash
# Get first page (default 20 results)
/search "FastAPI" --page 1

# Get second page with 50 results per page
/search "async" --page 2 --per-page 50

# Show pagination metadata
/search "patterns" --page 1 --per-page 10 --show-pagination
# Output: "Showing 1-10 of 847 results (page 1 of 85)"
```

---

## 11. Configuration Management

### 11.1 Configuration Hierarchy (FR-37)

**Priority Order (highest to lowest):**
1. **Command-line flags** - Explicit user intent
2. **Environment variables** - Machine/user-specific settings
3. **Config file** - Project-specific defaults
4. **Built-in defaults** - Fallback values

**Config File Locations:**
- `~/.search-research/config.toml` - User-global config
- `./.search-research.toml` - Project-local config
- `${SEARCH_RESEARCH_CONFIG}` - Custom path via env var

**Example Config File:**
```toml
# ~/.search-research/config.toml

[search]
# Default search mode: "fast", "comprehensive", "auto"
default_mode = "auto"

# Enable/disable features by default
hyde_enabled = true
fuzzy_matching = true
cache_enabled = true

# Performance tuning
cache_ttl = 3600
cache_size = 1000
backend_timeout_local = 500   # milliseconds
backend_timeout_web = 5000     # milliseconds

[backends.chs]
# CHS-specific configuration
db_path = "~/.search-research/chat_history.db"
jsonl_dir = "~/.search-research/chat_jsonl"
enable_semantic = true

[backends.cks]
# CKS-specific configuration
db_path = "~/.search-research/cks.db"
enable_vector_search = true

[providers.tavily]
api_key_env = "TAVILY_API_KEY"
enabled = true
max_retries = 3
timeout = 5

[providers.serper]
api_key_env = "SERPER_API_KEY"
enabled = true
max_retries = 3
timeout = 5

[logging]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR
file = "~/.search-research/search.log"
```

### 11.2 Key Validation (FR-38)

**Startup Validation:**
```python
def validate_config(config: Config) -> list[ValidationError]:
    """Validate configuration at startup.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check API keys for enabled providers
    if config.providers.tavily.enabled:
        if not os.getenv("TAVILY_API_KEY"):
            errors.append(ValidationError(
                provider="tavily",
                message="TAVILY_API_KEY not set",
                severity="error",
                fix="Set TAVILY_API_KEY environment variable or disable tavily in config"
            ))

    # Check database paths are writable
    for backend_name, backend_config in config.backends.items():
        db_path = Path(backend_config.db_path).expanduser()
        if db_path.exists() and not os.access(db_path, os.W_OK):
            errors.append(ValidationError(
                provider=backend_name,
                message=f"Database not writable: {db_path}",
                severity="error",
                fix=f"Check permissions for {db_path}"
            ))

    return errors
```

**User Experience:**
```bash
$ search-research
✗ Configuration validation failed:

Error: Tavily provider enabled but TAVILY_API_KEY not set
  Fix: export TAVILY_API_KEY=your_key_here
  Or disable tavily: ~/.search-research/config.toml: [providers.tavily] enabled=false

Warning: CHS database not found: ~/.search-research/chat_history.db
  Fix: Run search-research-init --chs to create database

Fix errors above or run with --skip-validation to proceed anyway.
```

### 11.3 Provider Health Monitoring (FR-39)

**Health Check System:**
```python
@dataclass
class ProviderHealth:
    """Health status for a provider."""
    name: str
    status: "healthy" | "degraded" | "down"
    last_check: datetime
    uptime_percent: float          # Last 24 hours
    avg_response_time: float       # milliseconds
    error_rate: float              # 0.0 to 1.0
    consecutive_failures: int

class ProviderHealthMonitor:
    """Monitor provider health with automatic failover."""

    def check_provider(self, provider: str) -> ProviderHealth:
        """Execute health check for single provider."""

    def is_healthy(self, provider: str) -> bool:
        """Return True if provider is healthy."""

    def mark_failure(self, provider: str):
        """Record provider failure and trigger backoff."""

    def should_use_provider(self, provider: str) -> bool:
        """Return False if provider is down or in backoff."""
```

**Automatic Failover Logic:**
1. **First failure**: Log warning, retry immediately
2. **Second consecutive failure**: Log error, retry after 60s
3. **Third consecutive failure**: Mark provider as "degraded", skip for 5 minutes
4. **Fourth+ consecutive failure**: Mark provider as "down", exponential backoff (5m, 15m, 1h)
5. **Recovery**: After successful request, reset failure count and mark "healthy"

**CLI Display:**
```bash
$ search --stats

Provider Health Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider     Status    Uptime   Avg Time   Failures
──────────────────────────────────────────────────────
Tavily       ✓ healthy  99.8%    850ms      0
Serper       ✓ healthy  97.2%    620ms      2
Exa          ⚠ degraded 85.1%    2.1s       5 (last 5m)
Perplexity   ✗ down     0.0%     -          12 (backoff: 15m)
──────────────────────────────────────────────────────

Cache: 47% hit rate (234/497 queries)
Last 24h: 1,847 searches, 1,829 successful (98.9%)
```

### 11.4 Configuration Validation (FR-40)

**Validation Categories:**

1. **Schema Validation** - Type checking, required fields
2. **Logic Validation** - Cross-field dependencies, mutual exclusions
3. **Runtime Validation** - File permissions, network connectivity
4. **Performance Validation** - Resource limits, timeout sanity

**Validation Commands:**
```bash
# Validate current configuration
$ search-research validate
✓ Configuration valid

# Validate with detailed output
$ search-research validate --verbose
✓ Config file loaded: ~/.search-research/config.toml
✓ All 5 providers configured
✓ API keys present for 3/3 enabled providers
✓ Database paths writable
✓ Cache size within limits (1000 < 10000)
✓ Timeout values reasonable (500ms local, 5000ms web)
✓ No conflicting settings detected

# Validate specific provider
$ search-research validate --provider tavily
✓ Tavily provider configuration valid
  API key: present
  Timeout: 5s
  Max retries: 3
  Health check: passing (850ms avg)
```

**Error Messages (Actionable):**
```bash
$ search-research validate
✗ Validation failed with 3 errors:

1. Cache size too large
   Current: 100000
   Maximum: 10000
   Fix: Set cache_size=1000 in ~/.search-research/config.toml

2. Backend timeout exceeds recommended maximum
   Provider: tavily
   Current: 30s
   Maximum: 10s
   Fix: Reduce timeout to 5s for better responsiveness

3. Conflicting settings
   Issue: Cannot enable both hyde_enabled=true AND mode=fast
   Fast mode skips web search (HyDE only applies to web)
   Fix: Either set mode=auto/comprehensive or hyde_enabled=false
```

---

---

## 12. Open Questions

- Should `/research` remain as separate command or become alias to `/search`?
- Should query intent be logged for privacy? (queries may contain sensitive info)
- Default behavior if user has no API keys configured?
- Should HyDE be enabled by default or opt-in?
- Cache TTL: 3600s default appropriate for all use cases?

---

## 13. Appendix: Example Usage

**Before (confusing):**
```bash
# User must guess which command to use
/search "FastAPI patterns"              # Returns code examples
/research "FastAPI best practices"      # Returns web articles
# No way to combine sources
# No handling of typos
# No research reports
```

**After (unified):**
```bash
# One command, intelligent routing
/search "FastAPI patterns"              # Returns code (detected local-only)
/search "FastAPI best practices"       # Returns web + code (detected web-enhanced)
/search "how to use FastAPI websockets" # Returns BOTH code examples AND web tutorials

# Typo tolerance
/search "FastAPII patterns"             # Returns FastAPI results with "Did you mean?"

# Research reports
/search "microservices patterns" --report  # Generates markdown report with citations

# Stats and debugging
/search --stats                         # Shows cache hits, backend health
```

---

## 14. Approval

- [ ] Product validation: User stories address real pain points
- [ ] Technical validation: Feasible to implement
- [ ] Timeline validation: Can deliver in 4 weeks

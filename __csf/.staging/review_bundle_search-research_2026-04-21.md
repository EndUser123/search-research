# Review Bundle: search-research

**Generated**: 2026-04-21
**Scope**: `P:/packages/search-research`
**File Count**: 657 Python files
**Execution Mode**: 4-agents (large scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-21
- **Scope**: P:/packages/search-research
- **File Count**: 657 Python files (excluding venv, cache, .git)
- **Execution Mode**: 4-agents (large scope)

### Domain & Purpose
Search research is a unified local search system for Claude Code that orchestrates 12+ backends (CKS, CHS, CDS, Grep, Skills, QMD Wiki, YouTube transcripts, etc.) using async concurrent execution with RRF fusion. It provides privacy-preserving search over personal knowledge, conversation history, code discoveries, and project documentation — without external API calls.

### Scale Metrics
- **LOC**: ~50K+ Python lines across core + backends + tests
- **Major subsystems**: 6 (core routing, backends, CHS, CKS, HyDE, research)
- **Backend count**: 12+ (CDS, Grep, Skills, CKS, KG, RLM, Claude History, NotebookLM, AST, LSP, QMD Wiki, YT-IS)
- **Deployment scope**: Personal Claude Code workspace
- **Change frequency**: Active development (recent commits visible)

### Your Environment
- **OS**: Windows 11 Pro (win32)
- **Shell**: bash (Unix-style on Windows)
- **Primary language**: Python 3.12+
- **Package manager**: uv (uv.lock present)
- **Databases**: SQLite (CKS at `P:/__csf/data/cks.db`, CHS at `P:/__csf/data/chat_history.db`)

---

## 2. ARCHITECTURE OVERVIEW

```
User Query
    │
    ▼
UnifiedAsyncRouter (core/unified_router.py)
    ├── intent classifier (conceptual vs code)
    ├── Phase 1: Fast local search (concurrent, 2s timeout)
    │       ├── CDSBackend
    │       ├── GrepBackend
    │       ├── SkillsBackend
    │       ├── CKSMetadataBackend ◄── recently fixed query expansion
    │       ├── KGBackend
    │       ├── RLMBackend
    │       ├── ClaudeHistoryBackend
    │       ├── NotebookLMBackend
    │       ├── ASTCodeBackend
    │       ├── QMDWikiBackend
    │       └── YTIsBackend
    ├── Phase 2: Quality check (is_satisfactory)
    ├── Phase 3: Web search (if needed, web-fallback mode)
    └── Phase 4: RRF fusion (reciprocal_rank_fusion)
```

### Fast-Path Routing
- **Conceptual queries** ("how does X work", "what did we discuss") → CHS semantic (FAISS embeddings)
- **Code queries** → Grep/CDS backends
- **Knowledge queries** → CKS metadata backend (SQLite LIKE + term expansion)
- **Wiki queries** → QMD CLI backend

---

## 3. EXECUTION AND DATA FLOW

### Main Search Flow
1. `UnifiedAsyncRouter.search_async(query, limit)` — entry point
2. Check conceptual query pattern → route to CHS semantic if matched
3. Concurrent gather via `asyncio.gather()` across all local backends (PERF-001)
4. Quality check via `is_satisfactory()` against `QualityConfig` thresholds
5. If `mode != 'local-only'` and quality insufficient → web search fallback
6. RRF fusion via `reciprocal_rank_fusion([local_results, web_results], k=60)`
7. TF-IDF topic alignment scoring added to results

### Backend Execution
- All backends run concurrently via `asyncio.gather()`
- Per-backend timeout: 2s (FAST mode), 8s (COMPREHENSIVE mode)
- Lazy initialization: backends created on first use
- Results cached with LRU (3600s TTL)

### Error Handling
- **Fail-open**: Individual backend failures logged and skipped, other backends continue
- **Timeout**: asyncio.wait_for with per-backend timeout (default 2s)
- **SQLite contention**: 3 retries with 100ms backoff in CKS backend

---

## 4. COMPONENT INVENTORY

### Core Logic
| File | Responsibility |
|------|----------------|
| `core/unified_router.py` | Main router — orchestrates phases, quality check, RRF fusion |
| `core/router_async.py` | Async execution engine — concurrent backend gather, caching |
| `core/quality_checker.py` | Quality threshold validation (is_satisfactory) |
| `core/hybrid_ensemble.py` | RRF fusion implementation |
| `core/intent_classifier.py` | Query intent classification (conceptual vs code) |
| `core/models.py` | SearchResult dataclass |
| `core/cache.py` | LRU query cache (3600s TTL) |

### Local Backends (`core/backends/local/`)
| Backend | Purpose |
|---------|---------|
| `cds_backend.py` | Code Documentation Search via AST |
| `grep_backend.py` | Full-text grep across source files |
| `skills_backend.py` | Skills and commands discovery |
| `cks_metadata_backend.py` | CKS SQLite queries with **term expansion** |
| `kg_backend.py` | Knowledge graph entity search |
| `rlm_backend.py` | Template-based code generation |
| `claude_history_backend.py` | Claude Code chat history keyword search |
| `notebooklm_backend.py` | NotebookLM integration |
| `ast_code_backend.py` | AST-aware code analysis |
| `lsp_backend.py` | LSP symbol navigation |
| `qmd_wiki_backend.py` | Obsidian vault search via qmd CLI |
| `yt_is_backend.py` | YouTube transcript search via Selenium |

### CHS (`core/chs/`)
| File | Purpose |
|------|---------|
| `db.py` | CHS SQLite connection management |
| `embeddings.py` | FAISS embedding generation |
| `indexer.py` | FTS5 index building |
| `search.py` | Semantic session search |

### HyDE (`core/hyde*.py`)
- `hyde.py`, `hyde_single.py`, `hyde_retrieval.py` — Hypothetical Document Embeddings
- `hyde_multi_perspective.py` — Multi-perspective HyDE
- `hyde_chapters.py` — Chapter-based HyDE

### Research (`core/research/`)
- `research.py` — Research engine with web providers
- `findings.py` — Structured finding storage

### CKS (`core/cks/`)
- `unified.py` — Main CKS interface (ingest_memory, ingest_pattern, search)
- `initialize_cks_direct.py` — Schema initialization
- `learning/` — Citation parser, diagnostic writer, file history

### CLI
- `core/cli.py` — Canonical CLI entry point

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
- **Privacy-first**: All search is local, no external API calls unless explicitly requested
- **Async concurrency**: All backends run in parallel via asyncio.gather
- **Graceful degradation**: Missing backends don't crash the router
- **Quality-gated web**: Web search only triggers when local quality is insufficient

### Technology Constraints
- Python 3.12+ with type hints
- SQLite for CKS and CHS (FTS5 for full-text)
- FAISS for semantic embeddings (CHS)
- uv for package management

### Performance SLAs
- Local search: <1s response (target)
- Quality check: <100ms
- Web fallback: 5-10s when triggered
- Backend timeout: 2s (fast), 8s (comprehensive)

### Non-Negotiable Behaviors
- **Never block on single backend** — all backends are concurrent
- **Fail-open on backend errors** — one bad backend doesn't crater the search
- **local-only mode** — skill execution directive hard-codes local-only (no automatic web)

---

## 6. KNOWN ISSUES

### Issue 1: CKS Multi-Word Query Failure (FIXED 2026-04-21)
- **Scenario**: `search("claude hooks")` returned 0 results even though CKS contained hooks entries
- **Root cause**: CKSMetadataBackend used SQLite LIKE `%query%` — multi-word phrase not found verbatim
- **Fix**: Added `_query_expansion()` method — when multi-word query returns 0, splits into individual terms
- **File**: `core/backends/local/cks_metadata_backend.py`
- **Verification**: `search("claude hooks")` now returns 5 results

### Issue 2: Hooks Documentation Not in CKS (FIXED 2026-04-21)
- **Scenario**: User wanted hooks docs searchable via /search but it returned 0 results
- **Fix**: Created `scripts/ingest_hooks_doc_to_cks.py` — chunks hooks doc into 58 entries
- **Verification**: 58 chunks ingested, confirmed via search

### Issue 3: Intent Routing Hard to Distinguish
- **Scenario**: Conceptual queries ("how does X work") routed to local-only even when web would be better
- **Proposed fix**: Intent classifier distinguishes conceptual vs code queries, routes conceptual to web-fallback
- **Status**: Identified gap, not yet implemented

---

## 7. INTEGRATION POINTS

### Entry Points
- **CLI**: `python -m core.cli` or `searchresearch` command
- **Python API**: `from core.unified_router import UnifiedAsyncRouter`
- **Skill**: `/search` command (search-research skill in `P:/.claude/skills/search/`)

### Configuration
- `core/config.py` — `Config` class with paths, env var support
- Key paths: `CKS_DB_PATH`, `CHS_DB_PATH`, `SOURCE_ROOTS`, `OBSIDIAN_VAULT_PATH`

### Web Search Integration
- `core/research/research.py` — ResearchEngine with Tavily, Serper, Exa, Brave providers
- Triggered only in `web-fallback` or `unified` mode (not `local-only`)

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

**Phase 1: Local Search**
- **Reads**: Query string, limit, backend list
- **Writes**: List[SearchResult] from each backend
- **Constraint**: All backends must complete within 2s (FAST) or 8s (COMPREHENSIVE)

**Phase 2: Quality Check**
- **Reads**: local_results from Phase 1
- **Writes**: Boolean (skip_web_search)
- **Constraint**: Returns True if best result score >= quality threshold

**Phase 3: Web Search (conditional)**
- **Reads**: Query string, limit (only if Phase 2 returned False)
- **Writes**: List[SearchResult] from web providers
- **Constraint**: Only runs if mode != 'local-only' and quality insufficient

**Phase 4: RRF Fusion**
- **Reads**: local_results, web_results
- **Writes**: Merged List[SearchResult] sorted by RRF score
- **Constraint**: k=60 constant for RRF formula

---

## 9. AGENT DISPATCH DEFINITIONS

Not applicable — this bundle was generated by a single agent. For 4-agent generation, dispatch:
- **Explorer**: File discovery, import tracing
- **Core Reader**: Core logic files (unified_router, router_async, quality_checker)
- **Config Reader**: Config, backends init
- **Dependency Scanner**: Env vars, external dependencies

---

## 10. FAILURE SCENARIOS

### Failure 1: CKS Backend Returns Empty (No Crash)
- **Trigger**: CKS database missing or corrupted
- **Propagation**: CKSMetadataBackend.search() catches sqlite3.Error, returns []
- **Detection**: Backend returns empty list — router continues with other backends
- **Actual vs expected**: Expected crash but gracefully degraded
- **Root cause**: Try/except pass in CKSMetadataBackend

### Failure 2: Query Expansion Creates Noisy Results
- **Trigger**: Multi-word query with very common individual terms (e.g., "the code")
- **Propagation**: Expansion returns many unrelated results
- **Detection**: User sees low-relevance results in output
- **Mitigation**: Expansion score (0.7) is lower than verbatim score (0.9)

### Failure 3: Intent Classifier Routes Wrong
- **Trigger**: Ambiguous query that could be conceptual or code
- **Propagation**: Routed to wrong backend, returns空洞 (empty) results
- **Detection**: User gets 0 results for a query that should match
- **Current workaround**: None — intent classifier needs improvement

---

## 11. APPENDIX: RECENT CHANGES (2026-04-21)

### Query Expansion Fix
```python
# core/backends/local/cks_metadata_backend.py
def _query_expansion(self, query: str, limit: int) -> list[dict[str, Any]]:
    # When multi-word query returns 0, try each term individually
    terms = [t.strip() for t in query.split() if t.strip()]
    ...
```

### CKS Ingest Script
- **File**: `scripts/ingest_hooks_doc_to_cks.py`
- **Action**: Chunks `claude-hooks-v3.1.md` into 58 CKS pattern entries
- **Category**: DOCUMENTATION
- **Verification**: Confirmed 58 chunks ingested, search returns results

### Hooks Documentation
- **Source**: `P:/.claude/docs/claude-hooks-v3.1.md` (renamed from v3.0)
- **Ingested**: 58 chunks to CKS with category=DOCUMENTATION

---

## 12. KEY FILES REFERENCE

| File | Purpose |
|------|---------|
| `core/unified_router.py` | Main router with quality check and RRF |
| `core/router_async.py` | Async concurrent backend execution |
| `core/backends/local/cks_metadata_backend.py` | CKS SQLite backend with query expansion |
| `core/quality_checker.py` | is_satisfactory() for quality gating |
| `core/hybrid_ensemble.py` | reciprocal_rank_fusion() |
| `core/intent_classifier.py` | Query type detection |
| `scripts/ingest_hooks_doc_to_cks.py` | CKS ingest for hooks docs |
| `core/config.py` | Path configuration |

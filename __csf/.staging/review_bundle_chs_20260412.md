# Review Bundle: CHS Search Infrastructure

**Generated**: 2026-04-12
**Scope**: CHS (Chat History Search) and backends for searching session, chat, and tool transcripts
**File Count**: ~100 Python files across core/chs/, providers/, backends/, search-research core/
**Execution Mode**: 4 parallel agents

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-12T09:58:36
- **Scope**: CHS search infrastructure + session/history chain backends
- **File Count**: ~100 files across core/chs/, providers/, backends/, core/ (search-research)
- **Execution Mode**: 4 parallel agents (Explorer + 3 specialists)

### Domain & Purpose

CHS (Chat History Search) is a multi-provider, two-stage search system for Claude Code chat history. It indexes sessions and messages from three providers (claude_code_raw, claude_log, codex_desktop) into SQLite/FTS5 + FAISS, and exposes search via a skill CLI, backends, and a Rust/FTS5 fast-path via claude-history.

**Critical for**: session recovery, knowledge capture, continuity across compactions, transcript mining.

### Scale Metrics
- ~70 Python files in `core/chs/` alone
- 3 provider implementations (claude_code_raw, claude_log, codex_desktop)
- 13+ backend types in `backends/local/`
- 2 search methods (FTS5 BM25 + FAISS semantic)
- 4 routing modes (local-only, auto, web-fallback, unified)

### Your Environment
- **OS**: Windows 11 Pro 10.0.26200
- **Shell**: bash (Git Bash / WSL)
- **Primary Language**: Python 3.12+
- **Package Manager**: uv, pip
- **Database**: SQLite (WAL mode, 64MB cache) at `P:/__csf/data/chat_history.db`
- **Vector Store**: FAISS via semantic daemon (named pipe)

---

## 2. ARCHITECTURE OVERVIEW

### Data Flow

```
Providers (claude_code_raw, claude_log, codex_desktop)
    │
    ├─ discover() → source list
    ├─ ingest_since(watermark) → NormalizedEvent[]
    │       └─ archive.append_raw_event() → raw JSONL archive
    │       └─ normalized.upsert_event() → events table
    └─ fetch_session() / fetch_message()

Indexer (ChatIndexer)
    ├─ _index_file() → messages table (idempotent by message_id)
    ├─ _build_turns_for_session() → turns table
    └─ _summarize_session_sync() → sessions.summary_short + sessions.embedding

Search Pipeline
    ├─ CHSSearchV2.search(query, use_semantic)
    │       ├─ FTS: search_fts_turns() → turns_fts (BM25)
    │       ├─ Semantic: embed query → turn_embeddings cosine similarity
    │       └─ Fuse: fuse_scores() with adaptive lambda
    │
    └─ CHSSearchWithSession — adds SearchSession tracking
```

### Provider Architecture

| Provider | Source | Session ID | Task Events | Tool Events |
|---------|--------|-----------|-------------|-------------|
| `claude_code_raw` | `~/.claude/history.jsonl` | entry["sessionId"] | No | Yes |
| `claude_log` | `~/claude-log.jsonl` (logEvent=TRANSCRIPT_ITEM) | entry["sessionId"] | No | Yes |
| `codex_desktop` | `~/.codex/history.jsonl` | MD5(cwd)[:8] | Yes | Yes |

### Search Backend Registry

| Backend | Class | Description |
|---------|-------|-------------|
| `cds` | `CDSBackend` | AST-based Python docstring search |
| `grep` | `GrepBackend` | AST-based function/class name search |
| `skills` | `SkillsBackend` | Progressive disclosure for Claude Code skills |
| `cks` | `CKSMetadataBackend` | Structured metadata queries for CKS |
| `kg` | `KGBackend` | Knowledge graph entity search |
| `rlm` | `RLMBackend` | Template-based code generation |
| `claude-history` | `ClaudeHistoryBackend` | Rust CLI + SQLite FTS5 |
| `notebooklm` | `NotebookLMBackend` | NotebookLM integration |
| `ast_code` | `ASTCodeBackend` | Extended AST-aware code search |
| `cpg` | `CPGBackend` | Code Property Graph (graceful degradation) |
| `hdma` | `HDMABackend` | HDMA analysis (graceful degradation) |
| `lsp` | `LSPSymbolBackend` | LSP symbol search |
| `dependency` | `DependencyBackend` | Dependency graph analysis |

### Extended Backends

| Backend | File | Purpose |
|---------|------|---------|
| **KG Boosting** | `core/backends/kg_boosting.py` | Entity affinity via Jaccard similarity |
| **CPGBackend** | `core/backends/local/cpg_backend.py` | Code Property Graph — data/control flow |
| **HDMABackend** | `core/backends/local/hdma_backend.py` | Hybrid Dual-Map — anti-patterns, bottlenecks |
| **CallGraphBackend** | `core/backends/local/call_graph_backend.py` | Call relationship mapping |
| **ASTCodeBackend** | `core/backends/local/ast_code_backend.py` | Lightweight AST without CPG |
| **PersonaMemory** | `core/backends/persona.py` | 3D scoring (novelty, feasibility, impact) |
| **RLM Backend** | `core/backends/rlm.py` | Template-based code generation |

### Routing Modes (UnifiedAsyncRouter)

| Mode | Behavior | Use Case |
|------|----------|----------|
| `local-only` | Local sources only (CKS, CHS, CDS, code, docs, skills) | Privacy-preserving, fast |
| `auto` | Local + web quality check + optional web | Balanced coverage |
| `web-fallback` | Local first, then web if insufficient | Comprehensive |
| `unified` | Full progressive enhancement with RRF fusion | Best quality |

---

## 3. EXECUTION AND DATA FLOW

### Two-Stage Search Architecture

**Stage 1 (Fast, ~10ms)**: Index-only search on `firstPrompt`, `summary`, `terminalId`, `branch`, `timestamp`.
**Stage 2 (Deep, ~500ms)**: Full JSONL content scan — all message content, tool results, thinking blocks.

Default: `--stage auto` (Stage 1 first, Stage 2 on-demand).

### CHS Search Pipeline

1. **Intent classification** (`_classify_intent()`): maps queries to `code-first`, `knowledge-first`, `conversation-first`, `error`, `howto`, `general`
2. **Backend selection** (`_select_backends()`): maps intent to backend priority lists
3. **FTS5 search** via `search_fts_turns()` → BM25 ranked results from `turns_fts`
4. **Semantic search** via `embed_query()` → cosine similarity against `turn_embeddings`
5. **Score fusion** via `fuse_scores()` with adaptive lambda weighting
6. **RRF fusion** in `UnifiedAsyncRouter` merges local + web results

### Session Chain Traversal

**Strategy 1 — Handoff-file chain** (primary):
- Follows `~/.claude/state/handoff/console_*_handoff.json` files
- Each handoff file contains `resume_snapshot.transcript_path` pointing to prior session's `.jsonl`
- Security: validates `.jsonl` suffix before returning path; rejects path traversal

**Strategy 2 — sessions-index scan** (fallback):
- Computes mtime gap between sessions (< 120 seconds = candidate link)
- Semantic verification via cosine similarity ≥ 0.35 threshold

**Strategy 3 — Semantic similarity fallback**:
- Embeds all sessions in 7-day window
- Ranks by cosine similarity against target session's combined goals+first-message text

### History Chain Traversal

`walk_chain(start_uuid, session_id, depth=200, summary_only=False)`:
- Walks backward via `parentUuid` field in `~/.claude/history.jsonl`
- Returns `ChainWalkResult` with entries, depth, origin_session_id, compacted_sessions set
- Uses `UUIDIndex` for O(1) random access to `history.jsonl`

---

## 4. COMPONENT INVENTORY

### Core Logic

| Component | Path | Responsibility |
|-----------|------|----------------|
| `search.py` | `core/chs/search.py` | FTS + semantic hybrid search, intent classification, backend selection |
| `db.py` | `core/chs/db.py` | SQLite WAL connection, schema init, embeddings config |
| `embeddings.py` | `core/chs/embeddings.py` | EmbedClient (daemon named pipe + SentenceTransformer fallback) |
| `indexer.py` | `core/chs/indexer.py` | ChatIndexer for incremental JSONL ingestion, checkpointing, summarization |
| `summarizer.py` | `core/chs/summarizer.py` | LLM-based session summarization via `generate_with_fallback` |
| `config.py` | `core/chs/config.py` | Env var config: CHS_DB_PATH, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS |
| `search_session.py` | `core/chs/search_session.py` | SearchSession (in-memory tracking), SearchSessionManager (file persistence) |
| `task_projection.py` | `core/chs/task_projection.py` | open_tasks / resolve_task on tasks table |

### Providers

| Provider | Path | Notes |
|----------|------|-------|
| `base.py` | `core/chs/providers/base.py` | ProviderCapabilities dataclass, NormalizedEvent dataclass, Provider Protocol |
| `claude_code_raw.py` | `core/chs/providers/claude_code_raw.py` | Reads `~/.claude/history.jsonl`, FileLock per terminal_id |
| `claude_log.py` | `core/chs/providers/claude_log.py` | Reads `~/claude-log.jsonl`, second-level timestamps |
| `codex_desktop.py` | `core/chs/providers/codex_desktop.py` | Reads `~/.codex/history.jsonl`, workspace-scoped terminal ID |

### Backends

| Backend | Path | Notes |
|---------|------|-------|
| `claude_history_backend.py` | `core/backends/local/claude_history_backend.py` | Wraps Rust `claude-history.exe`, LIKE fallback to SQLite |
| `chs_incremental.py` | `core/backends/local/chs_incremental.py` | Incremental FAISS index updates via `IncrementalIndexUpdater` |
| `enhanced_cds_backend.py` | `core/backends/local/enhanced_cds_backend.py` | jMRI four-operation interface (discover/search/retrieve/metadata) |
| `unified_router.py` | `core/unified_router.py` | 4-mode routing, RRF fusion, progressive enhancement |
| `router_async.py` | `core/router_async.py` | AsyncSearchRouter with `asyncio.gather()` parallel execution |

### Session/History Chain

| Component | Path | Notes |
|-----------|------|-------|
| `session_chain.py` | `core/session_chain.py` | walk_session_chain() with 3 strategies |
| `history_chain.py` | `core/history_chain.py` | walk_chain() via parentUuid, UUIDIndex for O(1) random access |
| `handoff_chain.py` | `core/handoff_chain.py` | walk_handoff_chain() for post-compaction traversal |

### Skill CLI

| Component | Path | Notes |
|-----------|------|-------|
| `chs_cli.py` (skill) | `P:/packages/search-research/skills/chs/scripts/chs_cli.py` | CHSConfig, CHSSearch, CHSSummarizer, CHSExporter, CHSContext |
| `chs_cli.py` (core) | `core/chs/scripts/chs_cli.py` | Core CLI interface |
| `run_indexer.py` | `core/chs/scripts/run_indexer.py` | ChatIndexer.daemon_loop() entry point |
| `health_check.py` | `core/chs/scripts/health_check.py` | Provider health via `projections.health_check()` |

### Rust CLI

| Component | Path | Notes |
|-----------|------|-------|
| `claude-history.exe` | `P:/packages/claude-history/target/release/claude-history.exe` | Rust CLI for fast FTS5 chat history search |
| `src/cli.rs` | `P:/packages/claude-history/src/cli.rs` | search, get, list, stats commands |
| `src/database.rs` | `P:/packages/claude-history/src/database.rs` | SQLite FTS5 backend |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
- **Two-stage search**: Fast index search before deep content scan (never load full conversations unnecessarily)
- **Multi-provider**: claude_code_raw + claude_log + codex_desktop unified via NormalizedEvent
- **Deduplication**: SHA256(content_hash) as events table PK prevents duplicate content
- **Append-only archive**: Raw events staged to tempfile then atomically renamed
- **Graceful degradation**: Optional backends wrapped in try/except; FTS5 index may not be built

### Technology Constraints
- **Solo-dev**: No CI/CD pipelines, no approval workflows
- **Privacy-first**: local-only mode, no external dependencies
- **Windows-compatible**: FileLock with stale lock recovery (5-minute timeout)

### Performance SLAs
- FTS5 search: ~10ms
- Hybrid search: ~50ms
- Semantic search: ~200ms
- Backend timeout (fast): 2s
- Backend timeout (comprehensive): 8s

### Things That Must NOT Change
- Provider protocol (ProviderCapabilities, NormalizedEvent dataclasses)
- events table PK `(provider_id, source_id, content_hash)` — deduplication depends on this
- Watermark per-terminal tracking — multi-terminal coexistence depends on this

---

## 6. KNOWN ISSUES

### Issue 1: FTS5 index may not be built
- **Scenario**: `claude_history_backend.py` falls back to `LIKE %query%` when FTS5 index unavailable
- **Expected**: Fast FTS5 search
- **Actual**: Slow LIKE scan
- **Impact**: Poor performance on chat history queries
- **Workaround**: Run full reindex via `reindex_from_jsonl.py`

### Issue 2: Semantic daemon named pipe failure
- **Scenario**: `EmbedClient` connects via named pipe to semantic daemon
- **Expected**: Fast embeddings via daemon
- **Actual**: Falls back to direct `SentenceTransformer("all-MiniLM-L6-v2")` with 5-minute idle TTL
- **Impact**: Slower semantic search on first query after idle period

### Issue 3: Compacted sessions undetectable by session_chain fallback
- **Scenario**: Session chain Strategy 2 (sessions-index scan) fails for compacted sessions because transcript is gone
- **Expected**: Chain continues through compacted sessions via handoff chain
- **Actual**: Chain breaks unless handoff files exist
- **Workaround**: Strategy 1 (handoff-file chain) handles this case

### Issue 4: LIKE fallback in claude_history_backend
- **Scenario**: Direct SQLite uses `LIKE %query%` on messages table
- **Expected**: FTS5 BM25 ranking
- **Actual**: Simple substring match with no ranking
- **Impact**: Lower quality results when Rust CLI unavailable

---

## 7. INTEGRATION POINTS

### Where CHS plugs into search-research

- `UnifiedAsyncRouter` routes chat/conversation queries to `claude-history` backend
- `CHSBackend` (in backends/local/) provides FTS5 + semantic search
- `CHSSearchV2` and `CHSSearchWithSession` are the core search interfaces
- Skill CLI at `skills/chs/scripts/chs_cli.py` provides user-facing commands

### Skill → CHS Integration

| Skill | Integration |
|-------|-------------|
| `/search` | Uses `UnifiedAsyncRouter` with CHS as one backend |
| `/chs` | Direct CLI at `skills/chs/scripts/chs_cli.py` with 7 features |
| `/recap` | Reads transcript files via session chain traversal |

### External Integration Points

- `semantic_daemon`: Named pipe at `P:/__csf/data/semantic_daemon` for FAISS embeddings
- `claude-history`: Rust CLI at `P:/packages/claude-history/target/release/claude-history.exe`
- `history.jsonl`: Append-only transcript at `~/.claude/history.jsonl`
- Watermarks: `P:/__csf/data/chs_archive/watermarks/{provider_id}/{source_id}/`

---

## 8. INPUT/OUTPUT CONTRACT

### Phase 1: Agent Dispatch

Four agents dispatched in parallel:

| Agent | Scope | Reads |
|-------|-------|-------|
| Agent 1 | CHS skill structure | `skills/chs/SKILL.md`, `skills/chs/scripts/chs_cli.py`, `references/` |
| Agent 2 | CHS core backend | `core/chs/search.py`, `core/chs/db.py`, `core/chs/embeddings.py`, `providers/` |
| Agent 3 | Session chain | `core/session_chain.py`, `core/history_chain.py`, `backends/local/` |
| Agent 4 | Search backends | `core/unified_router.py`, `core/router_async.py`, `core/backends/local/__init__.py` |

### Phase 2: Synthesis

Generator reads all 4 agent output files and synthesizes into single Markdown bundle.

### Output Contract

- **Output file**: `P:\__csf\.staging\review_bundle_chs_20260412.md`
- **Format**: Single Markdown file with all 11 sections per REVIEW BUNDLE CONTRACT
- **Evidence**: Generator must cite specific files:lines for key claims

---

## 9. AGENT DISPATCH DEFINITIONS

### Agent 1: CHS Skill Structure (COMPLETED)
- **Agent type**: `explore`
- **Role**: Map CHS skill files and references
- **What it reads**: `skills/chs/SKILL.md`, `skills/chs/scripts/chs_cli.py`, `references/*`
- **Output file**: `a34843f99f8b00b92.output`

### Agent 2: CHS Core Backend (COMPLETED)
- **Agent type**: `explore`
- **Role**: Deep analysis of search.py, db.py, embeddings.py, providers/, indexer.py
- **What it reads**: All files under `core/chs/`
- **Output file**: `a7a5f7d632d9cb76a.output`

### Agent 3: Session Chain Infrastructure (COMPLETED)
- **Agent type**: `explore`
- **Role**: Map session_chain.py, history_chain.py, backends/local/ for session traversal
- **What it reads**: `core/session_chain.py`, `core/history_chain.py`, `core/handoff_chain.py`, `backends/local/`
- **Output file**: `a16a57e600bfefcde.output`

### Agent 4: Search Backends (COMPLETED)
- **Agent type**: `explore`
- **Role**: Map unified_router.py, backend registry, Rust claude-history
- **What it reads**: `core/unified_router.py`, `core/router_async.py`, `core/backends/local/`, Rust sources
- **Output file**: `a68706157755c2210.output`

### Dispatch Order
All 4 agents run in parallel (discovery phase). Synthesis is serial after all complete.

---

## 10. FAILURE SCENARIOS

### Failure: Provider discovery returns empty list
- **Trigger**: `discover_all()` finds no providers
- **Propagation**: No sessions indexed, CHS returns no results
- **Detection**: `health_check.py` reports provider offline
- **Actual**: Empty result set, no error raised
- **Root cause**: Provider files not found or permissions issue

### Failure: FTS5 schema not built
- **Trigger**: Database created but schema.sql not run
- **Propagation**: `search_fts_turns()` fails with "no such table: turns_fts"
- **Detection**: Search raises SQLite error
- **Root cause**: `init_db()` not called before search

### Failure: Embedding model mismatch
- **Trigger**: `EMBEDDING_DIMENSIONS` set incorrectly (e.g., 384 vs 768)
- **Propagation**: FAISS dimension mismatch raises exception
- **Detection**: Semantic search raises ValueError
- **Root cause**: Env var not matching deployed model

### Failure: History.jsonl locked by concurrent writer
- **Trigger**: Two terminals writing to history.jsonl simultaneously
- **Propagation**: FileLock blocks, provider times out
- **Detection**: Stale lock recovery deletes lock after 5 minutes
- **Root cause**: No cross-terminal coordination beyond FileLock

---

## 11. APPENDIX: KEY FILE PATHS

| Component | Path |
|-----------|------|
| CHS skill SKILL.md | `P:/packages/search-research/skills/chs/SKILL.md` |
| CHS skill CLI | `P:/packages/search-research/skills/chs/scripts/chs_cli.py` |
| CHS core search | `P:/packages/search-research/core/chs/search.py` |
| CHS core db | `P:/packages/search-research/core/chs/db.py` |
| CHS embeddings | `P:/packages/search-research/core/chs/embeddings.py` |
| CHS indexer | `P:/packages/search-research/core/chs/indexer.py` |
| CHS providers | `P:/packages/search-research/core/chs/providers/` |
| CHS schema | `P:/packages/search-research/core/chs/schema.sql` |
| Session chain | `P:/packages/search-research/core/session_chain.py` |
| History chain | `P:/packages/search-research/core/history_chain.py` |
| Handoff chain | `P:/packages/search-research/core/handoff_chain.py` |
| Unified router | `P:/packages/search-research/core/unified_router.py` |
| Async router | `P:/packages/search-research/core/router_async.py` |
| Local backends | `P:/packages/search-research/core/backends/local/__init__.py` |
| Claude history backend | `P:/packages/search-research/core/backends/local/claude_history_backend.py` |
| CHS incremental FAISS | `P:/packages/search-research/core/backends/local/chs_incremental.py` |
| Enhanced CDS | `P:/packages/search-research/core/backends/local/enhanced_cds_backend.py` |
| Rust claude-history | `P:/packages/claude-history/` |
| CHS database | `P:/__csf/data/chat_history.db` |
| Watermarks | `P:/__csf/data/chs_archive/watermarks/` |
| Raw archive | `P:/__csf/data/chs_archive/{provider_id}/{year}/{month}/{source_id}/raw_*.jsonl` |

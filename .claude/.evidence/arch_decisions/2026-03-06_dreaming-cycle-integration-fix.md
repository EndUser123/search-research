# Architecture Decision: Dreaming Cycle Integration Fix

**Date**: 2026-03-06
**Status**: Accepted
**Decision**: Replace vector search with direct SQL query for orphan detection, use `aiosqlite` for async database access
**Impact**: High (fixes critical non-functional dreaming cycle)

---

## Context

The dreaming cycle (`P:\__csf\src\cks\consolidation\dreaming_cycle.py`) is currently non-functional due to a vector search integration gap:

**Problem Evidence**:
- Empty vector search results (`self.vector_manager.search("", limit=20)` returns 0 results)
- CKS database contains 2,142 entries with embeddings
- `VectorKnowledgeManager()` creates empty in-memory FAISS index instead of loading existing embeddings
- `get_orphans()` method cannot find candidates for relationship discovery

**Root Cause**:
Vector search abstraction layer is broken. The `VectorKnowledgeManager` creates a new empty FAISS index on instantiation instead of loading the existing 2,142 embeddings from `P:\__csf\data\cks.db`.

---

## Decision

**Replace vector search with direct SQL query for orphan detection and adopt `aiosqlite` for async database access.**

### Implementation Plan

**Phase 1: SQL-Based Orphan Detection**
```python
async def get_orphans(self, limit: int = 10) -> list[dict[str, Any]]:
    """Find disconnected entries with quality-based ranking."""

    # Step 1: Relational filter (SQL)
    async with aiosqlite.connect(self.db_path) as db:
        cursor = await db.execute("""
            SELECT id, title, content, metadata, created_at
            FROM entries
            WHERE id NOT IN (
                SELECT DISTINCT source_id FROM graph_edges
                UNION
                SELECT DISTINCT target_id FROM graph_edges
            )
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit * 3,))

        rows = await cursor.fetchall()
        candidates = [dict(row) for row in rows]

    # Step 2: Quality score ranking
    from .scripts.cleanup_cks import calculate_entry_quality
    scored_candidates = [
        (entry, calculate_entry_quality(entry))
        for entry in candidates
    ]
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return [entry for entry, score in scored_candidates[:limit]]
```

**Phase 2: Replace All SQLite Calls with `aiosqlite`**
- Update `get_orphans()` (async SQLite)
- Update `validate_and_process()` (async SQLite for graph_edges INSERT)
- Update `_commit_to_graph()` (async SQLite)
- Update `_queue_for_review()` (async SQLite)
- Update `_record_activity()` (async SQLite)

**Phase 3: Remove VectorManager Dependency**
- Remove `self.vector_manager = VectorKnowledgeManager()` from `__init__`
- Remove vector search calls from `run_cycle()`
- Simplify semantic matching using SQL LIKE or full-text search

**Phase 4: Add Database Indexes** (if performance degrades)
```sql
CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries(created_at DESC);
```

---

## Rationale

### 1. Database-First Alignment
- CKS is a **SQLite-first system** (2,163 entries stored in database)
- Vector embeddings are **cached representations** of database content
- Orphan detection is a **relational query** ("find entries without graph_edges")
- SQL is the **source of truth**, vector store is a **derived index**
- Design principle: Query the source of truth directly

### 2. I/O Blocking Prevention (Asyncio Best Practice)
```python
# Current (blocks event loop):
conn = sqlite3.connect(self.db_path)
cursor = conn.execute("SELECT ...")  # ❌ Blocks

# Fixed (non-blocking):
async with aiosqlite.connect(self.db_path) as db:
    cursor = await db.execute("SELECT ...")  # ✅ Yields to event loop
```
- `sqlite3` calls block ~10-50ms per query
- Dreaming cycle runs 3-5 queries per orphan
- With 10 orphans: 300ms of blocking time prevents concurrent LLM requests
- `aiosqlite` yields control during disk I/O, enabling true async concurrency

### 3. Simplicity Over Abstraction (Zen of Python)
- SQL approach: **1 query, deterministic results**
- Vector approach: **N+1 queries, empty results due to missing embeddings**
- Simplicity wins: "Simple is better than complex" (PEP 20)

### 4. Fail-Safe Design
- Vector search fails silently (returns empty list)
- SQL query fails explicitly (database errors logged)
- SQL query works **immediately** (no FAISS index loading required)
- Vector search requires **external state** (FAISS index file must exist and be compatible)

---

## Alternatives Considered

### Alternative A: Load Existing Embeddings on Startup
**Rejected**: High complexity, low reliability. Requires FAISS index file to exist and be compatible. Single point of failure.

### Alternative B: Use `asyncio.to_thread()` for SQLite Calls
**Rejected**: Incremental improvement, but doesn't solve root cause (vector search returns empty results).

### Alternative C: Hybrid Approach (Vector + SQL Fallback)
**Rejected**: Over-engineering. The "fallback" becomes the permanent path. Violates "explicit is better than implicit".

---

## Risk Assessment

### HIGH RISK: Current Implementation is Non-Functional
- **Severity**: 🔴 **Critical** - Dreaming cycle cannot find entries
- **Evidence**: Empty vector search results (empirical test)
- **Impact**: Background daemon runs but produces no relationships
- **Mitigation**: Implement SQL-based orphan detection immediately

### MEDIUM RISK: `aiosqlite` Dependency
- **Risk**: New dependency (`pip install aiosqlite`)
- **Impact**: Low - pure Python package, no C extensions, compatible with SQLite 3
- **Mitigation**: Add to `requirements.txt` / `pyproject.toml`

### LOW RISK: SQL Query Performance
- **Risk**: Full-table scan on `entries` + `graph_edges`
- **Impact**: Negligible for 2,163 entries (~10-50ms)
- **Mitigation**: Add indexes if database grows >100K entries

---

## Implementation Status

**Current**: ❌ Non-functional (vector search returns empty results)
**Target**: ✅ Functional SQL-based orphan detection with `aiosqlite`

**Next Steps**:
1. Install `aiosqlite` dependency
2. Replace `get_orphans()` with SQL-based implementation
3. Replace all `sqlite3` calls with `aiosqlite`
4. Remove `VectorKnowledgeManager` dependency
5. Test dreaming cycle with `--once --ignore-resources` flags

---

## Confidence: **High** (9/10)

### Evidence Tiers:
- **Tier 1 (Direct Evidence)**:
  - Empty vector search results (empirical test)
  - Database contains 2,142 entries with embeddings (direct query)
  - Current code uses synchronous SQLite in async function (code analysis)

- **Tier 2 (Indirect Evidence)**:
  - CKS design is database-first (architectural documentation)
  - `aiosqlite` is standard solution for async SQLite (community consensus)
  - SQL orphan detection is industry standard (relational algebra)

- **Tier 3 (Absence of Counter-evidence)**:
  - No evidence of vector search working correctly
  - No documentation of FAISS index location or format
  - No existing tests for `get_orphans()` method

---

## References

- **File**: `P:\__csf\src\cks\consolidation\dreaming_cycle.py`
- **File**: `P:\__csf\src\cks\consolidation\run_daemon.py`
- **File**: `P:\.claude\hooks\scripts\cleanup_cks.py` (quality scoring logic)
- **Documentation**: `P:\__csf\CLAUDE.md` (CKS architecture)
- **Python Package**: `aiosqlite` (https://aiosqlite.omnilib.dev)

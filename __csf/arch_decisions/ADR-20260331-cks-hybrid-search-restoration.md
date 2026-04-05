# ADR-20260331: CKS Hybrid Search Restoration and Quality Optimization

**Date:** 2026-03-31
**Status:** Proposed
**Decision Maker:** Solo developer (architecture review)
**Supersedes:** ADR-20260320-cleanup-violation-detection-overhaul (unrelated but relevant to knowledge systems)

---

## Context and Problem Statement

The CKS (Constitutional Knowledge System) at `P:/__csf/data/cks.db` (~998MB, 507,969 entries) is failing to provide useful context and suggestions. Investigation revealed multiple critical failures:

1. **CRITICAL: FTS5 table missing** — Database has 503,728 entries with embeddings but NO FTS5 full-text search index, breaking hybrid search
2. **HIGH: Entry type skew** — 99.998% of entries are "pattern" type (507,961/507,969)
3. **HIGH: Zero usage** — 507,873 entries (99.98%) have `usage_count = 0` — never retrieved
4. **MEDIUM: Low quality thresholds** — Thresholds at 0.12-0.20 return almost anything as "relevant"
5. **MEDIUM: Recency decay floor** — Old patterns never decay below 50% relevance

**Root cause hypothesis:** The FTS5 table was never created or was dropped during a migration. The hybrid search pipeline (`hybrid_search_patch.py`) expects `entries_fts` table but falls back to slow LIKE queries when missing.

---

## Decision

**Restore hybrid search by rebuilding the FTS5 index and optimize quality parameters.**

### Option A: Rebuild FTS5 + Raise Thresholds (CHOSEN)

**Differs from others on:** Technology choice (FTS5 vs third-party), approach (repair vs replace)

| Component | Action | Location |
|-----------|--------|----------|
| FTS5 Index | Rebuild `entries_fts` table via `CREATE VIRTUAL TABLE entries_fts USING fts5(...)` | `P:/packages/search-research/core/cks/` |
| Quality Thresholds | Raise from 0.12-0.20 back to 0.30-0.35 with better filtering | `unified.py:68-72` |
| Recency Decay | Remove 0.5 floor to allow obsolescence | `unified.py:1155` |
| Entry Type Audit | Investigate 99.998% pattern skew and normalize distribution | Auto-ingestion system |

### Option B: Hybrid Fallback Optimization

Keep LIKE-based fallback but optimize ranking. Rejected because:
- LIKE queries cannot match FTS5 quality
- 49-67% hybrid improvement would be permanently lost
- FTS5 is standard SQLite — no new dependencies

### Option C: Complete Rebuild

Delete database and rebuild from source. Rejected because:
- 507,969 entries would be lost
- No clear source for regeneration
- Overkill for a missing index

---

## Rationale

**Evidence sources:**
- `P:/packages/search-research/core/cks/hybrid_search_patch.py:37-48` — Hybrid search requires FTS5
- `P:/packages/search-research/core/cks/hybrid_search_patch.py:196-200` — FTS5 existence check
- `P:/packages/search-research/core/cks/unified.py:68-72` — Quality thresholds lowered empirically without fixing root cause
- Database query: `SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'` returns empty

**Why Option A:**
1. FTS5 is native SQLite — no new dependencies
2. Rebuilding index is O(n) with minimal risk
3. Restoring hybrid search unlocks 49-67% accuracy improvement
4. Threshold adjustment should follow FTS5 restoration (better FTS5 → higher thresholds viable)

---

## Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| Option B (Fallback optimization) | Quick fix | LIKE never matches FTS5 quality | Permanent accuracy loss |
| Option C (Complete rebuild) | Clean slate | Data loss, no regeneration source | Overkill, destroys institutional knowledge |
| Option D (Third-party search) | Better search (Elasticsearch) | New dependencies, ops burden | Solo dev, Windows — not appropriate |

---

## Consequences

### Positive
- Hybrid search accuracy improvement: **49-67%** (Anthropic's Contextual Retrieval paper)
- Database size reduction: FTS5 compact representation
- Better relevance: Higher thresholds + recency decay

### Negative
- Rebuild time: ~10-30 minutes for 500K entries (acceptable offline operation)
- Temporary search unavailability during rebuild

### Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Rebuild fails mid-operation | Low | High | Full database backup before rebuild |
| LIKE fallback masks future FTS5 failures | Medium | Medium | Add FTS5 health check to MCP tool responses |

---

## Implementation

### Phase 1: FTS5 Index Rebuild (CRITICAL)
1. **Backup database** — `cp P:/__csf/data/cks.db P:/__csf/data/cks.db.bak`
2. **Verify current state** — Query `entries` table schema and row count
3. **Create FTS5 virtual table** — Match schema to existing `entries` table
4. **Populate via INSERT...SELECT** — Transfer content columns to FTS5
5. **Verify index** — Query `entries_fts` and compare result counts

**Effort:** 2-3 hours (mostly automated)

### Phase 2: Quality Threshold Audit
1. **Profile similarity scores** — Log score distribution for 100 random queries
2. **Determine actual max similarity** — Was 0.47, check if embedding model changed
3. **Raise thresholds conservatively** — 0.25/0.20/0.18 as starting point
4. **Add threshold monitoring** — Log when results fall below threshold

**Effort:** 1-2 hours

### Phase 3: Entry Type Investigation
1. **Query type distribution over time** — `SELECT entry_type, COUNT(*), MIN(created_at), MAX(created_at) FROM entries GROUP BY entry_type`
2. **Identify auto-ingestion source** — Find what created 507,961 patterns
3. **Normalize if needed** — Archive duplicate patterns, diversify entry types

**Effort:** 2-4 hours (requires analysis)

### Phase 4: Recency Decay Fix
1. **Remove floor or lower to 0.3** — `max(0.3, 0.97**days_old)`
2. **Add decay monitoring** — Log entries that decay below 0.5
3. **Consider TTL-based eviction** — Entries older than 2 years auto-archive

**Effort:** 1 hour

---

## Rollback Strategy

- **FTS5 rebuild:** Restore from `cks.db.bak` backup
- **Threshold changes:** Revert `QUERY_TYPE_THRESHOLDS` to original values (commented in code)
- **Recency decay:** Restore `max(0.5, ...)` floor

---

## Success Criteria

- [ ] FTS5 table exists: `SELECT COUNT(*) FROM entries_fts` returns 503,728+
- [ ] Hybrid search returns results: `/search` MCP tool returns structured output
- [ ] Threshold adjustment: Technical queries return <20 results at threshold 0.25
- [ ] Usage tracking active: `usage_count` increments on retrieval
- [ ] Entry diversity: Non-pattern entries > 0.01% (currently 0.002%)

---

## Multi-Terminal Isolation Assessment

**State sharing:** YES — CKS database is shared across all terminals
- Single SQLite database at `P:/__csf/data/cks.db`
- WAL mode enabled for concurrent readers
- Write operations require file locking

**Concurrency safety:**
- FTS5 rebuild is write operation — must not run during active search
- Use `WITHOUT RECOMMENDATION` or schedule during low-usage window

**Stale data immunity:**
- FTS5 rebuild creates new index atomically
- Old index remains until new is fully populated
- Readers see consistent snapshot during rebuild

---

## Related Decisions
- **ADR-20260320-cleanup-violation-detection-overhaul:** Cleanup system (related to knowledge management)
- **ADR-20260328-search-research-hook-architecture:** Search/research hooks (uses CKS)

---

## References
- [Anthropic Contextual Retrieval](https://www.anthropic.com/research/contextual-retrieval): 49-67% hybrid search improvement
- [SQLite FTS5 Documentation](https://www.sqlite.org/fts5.html): Index creation syntax
- `P:/packages/search-research/core/cks/hybrid_search_patch.py:4-8`: Hybrid search implementation

---

**Confidence:** 78%

**Evidence basis:**
- Investigation findings: Database analysis + code review
- CKS CLAUDE.md: Documents expected architecture
- hybrid_search_patch.py: FTS5 dependency

**Key assumptions:**
1. FTS5 table was never created or was dropped during migration
2. Embedding model quality is sufficient for higher thresholds
3. Auto-ingestion can be reconfigured to create diverse entry types

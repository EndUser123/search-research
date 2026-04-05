# CKS Pre-Query Optimization Specification

**TSK ID:** TSK-231223-CKSPrequeryOpt-2024
**Project:** CKS Pre-Query Optimization (FTS5 + Performance)
**Created:** 2025-12-23
**Status:** In Progress

## 1. Executive Summary

Enhance the CKS (Cognitive Knowledge System) pre-query integration with the /discover command by implementing three critical improvement areas identified through research:

1. **SQLite FTS5 Full-Text Search** - Enable fast, ranked text search with BM25 scoring
2. **Performance Optimization** - Ensure CKS pre-query doesn't degrade discovery performance (<200ms target)
3. **Medium-Priority Enhancements** - Entity relationship traversal, session context, UX improvements

These enhancements focus on foundational improvements that will enable future advanced features (semantic search, embeddings) while providing immediate value to users.

## 2. Problem Statement

### Current State

The CKS pre-query integration (`__csf.nip/src/modules/discover/cks_prequery.py`) provides basic pattern discovery using SQL `LIKE` queries:

```python
# Current implementation - slow and unranked
cursor.execute(
    """
    SELECT id, type, title, content, metadata
    FROM entries
    WHERE content LIKE ? OR title LIKE ? OR type LIKE ?
    ORDER BY success_count DESC, usage_count DESC
    LIMIT ?
    """,
    (search_pattern, search_pattern, search_pattern, limit * 2)
)
```

**Limitations:**
- **Performance:** `LIKE` queries are slow on large datasets (O(n) table scan)
- **No Ranking:** Results aren't ranked by relevance
- **No Optimization:** Missing indexes, caching, or query monitoring
- **Limited Context:** No session history or entity graph utilization

### Research Findings

Comprehensive research (`P:\research-output\researcher_report.md`) identified 10 enhancement opportunities with the following priority matrix:

| Finding | Impact | Effort | Priority | Status |
|---------|--------|--------|----------|--------|
| 1. Semantic Search (Embeddings) | HIGH | HIGH | Phase 3 | **Other LLM** |
| 2. SQLite FTS5 | HIGH | LOW | **Phase 1** | **THIS WORK** |
| 3. Temporal Decay | MEDIUM | LOW | Phase 1 | **Other LLM** |
| 4. Feedback Loop | HIGH | MEDIUM | Phase 1 | **Other LLM** |
| 5. Session History | MEDIUM | MEDIUM | **Phase 2** | **THIS WORK** |
| 6. Entity Relationships | MEDIUM | MEDIUM | **Phase 2** | **THIS WORK** |
| 7. Multi-Candidate Queries | LOW-MED | HIGH | Phase 3 | Future |
| 8. Adaptive Thresholding | LOW-MED | MEDIUM | Phase 3 | Future |
| 9. Performance Optimization | HIGH | MEDIUM | **Phase 1** | **THIS WORK** |
| 10. UX Enhancements | MEDIUM | LOW-MED | **Phase 2** | **THIS WORK** |

**Scope Split:**
- **This LLM:** Findings #2 (FTS5), #9 (Performance), #5/#6/#10 (Medium-priority)
- **Other LLM:** Findings #1 (Embeddings), #3 (Temporal), #4 (Feedback)

## 3. Solution Requirements

### 3.1 SQLite FTS5 Integration (Finding #2)

**Functional Requirements:**
- FR1: Create FTS5 virtual table for entries content
- FR2: Implement BM25 ranking for search results
- FR3: Set up triggers for automatic FTS index maintenance
- FR4: Support FTS5 MATCH query syntax
- FR5: Provide fallback to LIKE queries if FTS unavailable

**Non-Functional Requirements:**
- NFR1: Query performance <50ms for 100K entries
- NFR2: Index overhead <50% of original data size
- NFR3: Automatic synchronization between entries and entries_fts
- NFR4: Backward compatibility with existing CKS schema

### 3.2 Performance Optimization (Finding #9)

**Functional Requirements:**
- FR6: Create composite indexes on (type, confidence_score, timestamp)
- FR7: Implement LRU caching for frequent queries
- FR8: Add query performance monitoring and logging
- FR9: Implement pagination for large result sets
- FR10: Create materialized views for expensive aggregations

**Non-Functional Requirements:**
- NFR5: Overall CKS pre-query latency <200ms (95th percentile)
- NFR6: Cache hit rate >60% for repeated queries
- NFR7: Memory overhead for caching <100MB
- NFR8: Performance monitoring overhead <5ms per query

### 3.3 Medium-Priority Enhancements (Findings #5, #6, #10)

**Session History (Finding #5):**
- FR11: Track last 5-10 queries in session context
- FR12: Boost entries related to recent queries
- FR13: Maintain entity continuity across queries
- FR14: Provide query suggestions based on history

**Entity Relationships (Finding #6):**
- FR15: Implement depth-1 entity relationship traversal
- FR16: Boost discovery results with related entries
- FR17: Use recursive CTEs for graph queries
- FR18: Filter weak relationships (<0.3 weight)

**UX Enhancements (Finding #10):**
- FR19: Rich result formatting with confidence indicators
- FR20: Show confidence bars and age badges
- FR21: Explain scoring factors to users
- FR22: Provide "Searching CKS..." status feedback

## 4. Implementation Scope

### In Scope

1. **FTS5 Integration:**
   - Create `entries_fts` virtual table
   - Implement triggers for index sync
   - Update `_query_patterns()` to use FTS5
   - Add FTS5 fallback mechanism

2. **Performance Optimization:**
   - Add composite indexes to CKS database
   - Implement `@lru_cache` decorator for query caching
   - Add query metrics logging
   - Implement result pagination

3. **Entity Relationships:**
   - Implement `find_related_entries()` function
   - Add graph boost to discovery results
   - Create recursive CTE for depth-1 traversal

4. **Session Context:**
   - Create `DiscoverySession` class
   - Track query history and entities
   - Implement contextual scoring boost

5. **UX Improvements:**
   - Format results with confidence bars
   - Add age badges and source indicators
   - Show search status feedback

### Out of Scope (Other LLM or Future)

- ❌ Semantic search with embeddings (Finding #1) - **Other LLM**
- ❌ Temporal decay scoring (Finding #3) - **Other LLM**
- ❌ Discovery feedback loop (Finding #4) - **Other LLM**
- ❌ Multi-candidate query strategy (Finding #7) - Future
- ❌ Adaptive confidence thresholding (Finding #8) - Future
- ❌ Interactive result filtering (Finding #10 advanced) - Future

## 5. Technical Approach

### 5.1 Database Schema Changes

```sql
-- FTS5 Virtual Table
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    entry_id UNINDEXED,
    content,
    title,
    type,
    metadata,
    content='entries',
    content_rowid='rowid'
);

-- Composite Indexes
CREATE INDEX IF NOT EXISTS idx_entries_type_confidence
ON entries(type, confidence_score DESC, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_entries_project_type
ON entries(project_path, type, timestamp DESC);

-- Query Metrics Table
CREATE TABLE IF NOT EXISTS query_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT,
    duration_ms REAL,
    result_count INTEGER,
    timestamp INTEGER DEFAULT (strftime('%s', 'now'))
);
```

### 5.2 Architecture

```
CKSPreQuery (Enhanced)
├── Database Layer
│   ├── FTS5 Search (NEW)
│   ├── LIKE Fallback (EXISTING)
│   └── Entity Graph Traversal (NEW)
├── Caching Layer (NEW)
│   ├── LRU Cache
│   └── Query Hashing
├── Context Layer (NEW)
│   ├── Session History
│   └── Entity Tracking
├── Scoring Layer
│   ├── BM25 Ranking (NEW)
│   ├── Graph Boost (NEW)
│   └── Context Boost (NEW)
└── Presentation Layer (NEW)
    ├── Rich Formatting
    └── Confidence Indicators
```

### 5.3 File Modifications

**Primary Files:**
1. `__csf.nip/src/modules/discover/cks_prequery.py` - Main enhancements
2. `__csf.nip/data/cks.db` - Database schema updates
3. `__csf.nip/src/cks/storage.py` - May need updates for FTS support

**New Files:**
1. `__csf.nip/src/modules/discover/cks_session.py` - Session management (optional)
2. `__csf.nip/tests/test_cks_prequery_enhanced.py` - Comprehensive tests

## 6. Success Criteria

### 6.1 Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| FTS5 Query Latency | <50ms | 95th percentile |
| Overall Pre-Query Latency | <200ms | 95th percentile |
| Cache Hit Rate | >60% | After warm-up |
| Index Overhead | <50% | Database size ratio |
| Memory Overhead | <100MB | Cache + indexes |

### 6.2 Functional Metrics

| Feature | Acceptance Criteria |
|---------|---------------------|
| FTS5 Search | Returns ranked results, supports MATCH syntax |
| Entity Traversal | Finds related entries within 100ms |
| Session Context | Boosts relevant entries by 10-20% |
| UX Formatting | Shows confidence bars, age badges |

### 6.3 Quality Metrics

- All existing tests pass
- New test coverage >80%
- No regression in CKS pre-query functionality
- Documentation updated for new features

## 7. Dependencies

### Internal
- Existing CKS database schema (`entries`, `entities`, `relationships`)
- `cks_prequery.py` module
- `/discover` command integration

### External
- Python 3.12+
- SQLite 3.38+ (FTS5 support)
- `functools.lru_cache` (built-in)

**No new dependencies required** - all enhancements use Python/SQLite built-ins.

## 8. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| FTS5 index sync issues | HIGH | MEDIUM | Use triggers, add health checks |
| Performance degradation | HIGH | LOW | Set 200ms budget, monitor metrics |
| Schema migration errors | MEDIUM | LOW | Backup database, test migration |
| Cache memory bloat | MEDIUM | LOW | Limit cache size, add TTL |
| Graph query performance | MEDIUM | MEDIUM | Limit depth-1, use indexes |

## 9. Timeline Estimates

**Phase 1: FTS5 + Performance** (3-4 hours)
- FTS5 integration: 90 min
- Performance optimization: 60 min
- Testing: 30-60 min

**Phase 2: Medium-Priority** (2-3 hours)
- Entity relationships: 60 min
- Session context: 45 min
- UX improvements: 30 min
- Testing: 30-45 min

**Total:** 5-7 hours

## 10. Handoff Plan

### After Implementation:
1. Run full test suite and validate performance metrics
2. Document new features in `/discover` command docs
3. Provide usage examples for FTS5 search
4. Create migration guide for existing CKS databases
5. Coordinate with other LLM to integrate temporal decay and feedback loop

### For Other LLM:
- FTS5 tables and indexes will be available
- Performance monitoring infrastructure in place
- Session context ready for temporal decay integration
- Entity graph traversal ready for feedback loop enhancement

---

**Specification Status:** ✅ Complete
**Next Step:** Begin implementation with FTS5 integration

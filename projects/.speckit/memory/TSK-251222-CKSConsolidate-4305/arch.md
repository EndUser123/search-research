# CKS Consolidation Architecture

## Current State Analysis

### Database Inventory
Total: 53 database files, 9 MB

**Active Databases (3):**
1. src/data/cks.db (229 KB, 309 memories)
2. src/data/cks_hypergraph/cks_hypergraph.db (446 KB, 40 knowledge nodes)
3. data/cks_hypergraph/cks_hypergraph.db (720 KB, 19 knowledge nodes)

### Schema Comparison

**cks.db (Memories Schema):**
- memories table with id, question, answer, embedding, metadata

**cks_hypergraph.db (Knowledge Schema):**
- knowledge_nodes table with id, type, content, metadata
- knowledge_edges table (relationships)
- vector_nodes table (semantic search)

## Proposed Architecture

### Unified Schema

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,        -- 'memory', 'pattern', 'code', 'knowledge'
    title TEXT,
    content TEXT NOT NULL,
    metadata TEXT,              -- JSON
    embedding BLOB,             -- Optional
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_type ON entries(type);
CREATE INDEX idx_created ON entries(created_at DESC);
```

### Interface Design

```python
# src/cks/__init__.py
class CKS:
    def __init__(self, db_path: str = "data/cks.db"):

    # Memory operations
    def ingest_memory(self, question: str, answer: str, **metadata)
    def search_memories(self, query: str, limit: int = 5)

    # Pattern operations
    def ingest_pattern(self, title: str, content: str, **metadata)
    def search_patterns(self, query: str, limit: int = 5)

    # Universal
    def search(self, query: str, entry_type: str = None)
    def get_statistics(self)
```

### Migration Strategy

**Phase 1: Backup** - Backup all src/data and data directories

**Phase 2: New Schema** - Create P:/__csf.nip/data/cks.db

**Phase 3: Migration** - Migrate 368 total records (309 memories + 59 knowledge nodes)

**Phase 4: Compatibility Layer** - New src/cks module with deprecation warnings for old paths

**Phase 5: Cleanup** - 1 week grace period, then archive old databases

## Failure Mode Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss during migration | Low | Critical | Full backups before migration |
| Breaking existing code | Medium | High | Compatibility layer with deprecation warnings |
| Migration script bugs | Medium | Medium | Test on copy of data first |
| Performance regression | Low | Low | Indexes optimize query performance |

## Success Metrics
- 1 database file instead of 53
- < 2 MB instead of 9 MB
- Zero data loss
- All existing code still works (with warnings)
- Simple interface: from src.cks import CKS

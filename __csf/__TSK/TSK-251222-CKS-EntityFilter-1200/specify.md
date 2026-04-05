# CKS Entity Filter & Hybrid Retrieval - Specification

**Task ID:** TSK-251222-CKS-EntityFilter-1200
**Created:** 2025-12-22
**Status:** Implementation

---

## Executive Summary

Implement high-value recommendations from memory landscape research to add hybrid entity + semantic retrieval, session recall logging, and PostToolUse hook integration to CKS. These features enable queries like "what mistakes did we make on CKS?" while maintaining backward compatibility.

**Research Validation:**
- ChromaDB - Multi-modal search (vector + full-text + regex + metadata)
- Memori - SQL-native with full-text search
- H-MEM - Hierarchical memory organization
- Task Memory Engine - Revision-aware tracking

---

## Requirements

### High Value: Entity Filtering (Must Have)

**Requirement 1.1:** Add entity table to CKS schema
- Entities table with slug, name, type (project/environment/cluster)
- Entry-entity junction table for many-to-many relationships
- Example entities: "cks", "desktop-commander", "foo-prod"

**Requirement 1.2:** Implement search_with_entity_filter() method
- Accept entity_slug parameter to filter results
- Return semantic results filtered by entity
- Maintain backward compatibility (entity_slug=None returns all results)

**Requirement 1.3:** Entity detection in queries
- Auto-detect entity mentions in queries (e.g., "CKS", "cluster foo-prod")
- Filter results to detected entity
- Optional explicit entity filter via parameter

**Requirement 1.4:** Bridge integration
- Update prepare_session() to support entity filtering
- Display entity information in verbose output

### Medium Value: Session Recall Logging (Should Have)

**Requirement 2.1:** Add recall_log table
- Fields: session_id, timestamp, query, entry_id, ranking, entity_slug
- Tracks what was recalled when for debugging

**Requirement 2.2:** Implement log_recall() method
- Called after each search_semantic() invocation
- Records query, results, rankings, entities
- Lightweight - no performance impact

**Requirement 2.3:** Query recall history
- Method to retrieve recall history for debugging
- Filter by session_id, date range, entity

### Medium Value: PostToolUse Hook Integration (Should Have)

**Requirement 3.1:** Create PostToolUse hook script
- Detect when CKS files are touched
- Query for related memories automatically
- Inject context into next prompt

**Requirement 3.2:** Smart context injection
- Only inject when relevant (semantic similarity > threshold)
- Limit to top 3 related memories
- Prevent context explosion

---

## Architecture

### Schema Changes

```sql
-- Entity table
CREATE TABLE IF NOT EXISTS entities (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('project', 'environment', 'cluster', 'component')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug, type)
);

-- Entry-entity junction table
CREATE TABLE IF NOT EXISTS entry_entities (
    entry_id TEXT NOT NULL,
    entity_slug TEXT NOT NULL,
    linked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, entity_slug),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_slug) REFERENCES entities(slug) ON DELETE CASCADE
);

-- Recall log table
CREATE TABLE IF NOT EXISTS recall_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    ranking REAL,
    entity_slug TEXT,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);
```

### Class Changes

**CKS class (src/cks/unified.py):**
- Add `search_with_entity_filter(query, entity_slug=None, limit=5)`
- Add `log_recall(session_id, query, results)`
- Add `_detect_entities_in_query(query)` method
- Add `link_entity(entry_id, entity_slug)` method
- Add `create_entity(slug, name, type)` method

**Bridge class (src/lib/core_utils/claude_code_ks_bridge.py):**
- Update `prepare_session()` to support entity_slug parameter
- Add automatic recall logging
- Display entity information in verbose output

### Hook Scripts

**PostToolUse hook (.claude/hooks/PostToolUse.py):**
- Detect CKS file modifications
- Query related memories
- Format and inject context

---

## Implementation Plan

### Phase 1: Schema & Basic Entity Support (Step 1-2)

1. **Step 1:** Database schema migration
   - Create entities table
   - Create entry_entities table
   - Create indexes for performance

2. **Step 2:** Basic entity methods
   - create_entity()
   - link_entity()
   - unlink_entity()
   - get_entities_for_entry()

### Phase 2: Entity Filtering (Step 3-4)

3. **Step 3:** Entity detection
   - _detect_entities_in_query()
   - Simple keyword-based matching
   - Return list of detected entity slugs

4. **Step 4:** Entity-filtered search
   - search_with_entity_filter()
   - Integrate with existing search_semantic()
   - Maintain backward compatibility

### Phase 3: Recall Logging (Step 5-6)

5. **Step 5:** Recall log table
   - Create recall_log table
   - Add indexes for querying

6. **Step 6:** Logging implementation
   - log_recall() method
   - get_recall_history() method
   - Bridge integration

### Phase 4: PostToolUse Hook (Step 7)

7. **Step 7:** Hook implementation
   - PostToolUse.py script
   - Smart context injection
   - Testing and validation

---

## Testing Strategy

### Unit Tests

```python
def test_entity_creation():
    """Test creating entities"""
    cks.create_entity("cks", "Constitutional Knowledge System", "project")
    # Verify entity exists

def test_entity_linking():
    """Test linking entities to entries"""
    entry_id = cks.ingest_memory("test", "test")
    cks.link_entity(entry_id, "cks")
    # Verify link exists

def test_entity_filtering():
    """Test entity-filtered search"""
    results = cks.search_with_entity_filter("database", entity_slug="cks")
    # Verify all results have entity "cks"

def test_entity_detection():
    """Test automatic entity detection"""
    entities = cks._detect_entities_in_query("what mistakes did we make on CKS?")
    # Verify ["cks"] returned

def test_recall_logging():
    """Test recall logging"""
    cks.log_recall("session-1", "test query", results)
    history = cks.get_recall_history(session_id="session-1")
    # Verify log entry exists
```

### Integration Tests

```python
def test_hybrid_retrieval():
    """Test entity + semantic hybrid retrieval"""
    # Create entries with different entities
    # Query with entity filter
    # Verify correct results returned

def test_post_tool_use_hook():
    """Test PostToolUse hook integration"""
    # Modify CKS file
    # Verify hook triggers
    # Verify related memories injected
```

---

## Backward Compatibility

**Guarantee:** All existing CKS functionality must continue to work without modification.

- entity_slug parameter is optional (defaults to None)
- None returns all results (no filtering)
- Existing entries without entities still work
- No breaking changes to API

---

## Performance Considerations

**Entity filtering:**
- Add index on entry_entities(entry_id, entity_slug)
- Filter after semantic search (reduce candidates)
- Limit overhead to <10% additional latency

**Recall logging:**
- Async logging to avoid blocking search
- Batch inserts for efficiency
- Prune old logs (>90 days) automatically

---

## Success Criteria

1. ✅ Entity filtering reduces noise in entity-specific queries by >50%
2. ✅ Recall logging enables debugging of CKS behavior
3. ✅ PostToolUse hook reduces manual context injection by >80%
4. ✅ Backward compatibility maintained (all existing tests pass)
5. ✅ Performance impact <10% for entity-filtered queries
6. ✅ Zero breaking changes to public API

---

## Files to Modify

1. `src/cks/unified.py` - Core CKS implementation
2. `src/lib/core_utils/claude_code_ks_bridge.py` - Bridge integration
3. `.claude/hooks/PostToolUse.py` - Hook implementation (new file)

---

## Next Steps

**Immediate:** Execute implementation plan (Steps 1-7)

**Following:** Test and validate all features

**Future:** Consider advanced entity resolution (fuzzy matching, hierarchical entities)

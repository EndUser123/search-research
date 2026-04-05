# Architecture Analysis: CKS-First /discover Design

**TSK-ID**: TSK-251224-CKS-Discover-05b7aa
**Step**: 5 - Architecture Analysis
**Created**: 2025-12-24 03:05

## Executive Summary

**Proposed Architecture**: CKS-first unified knowledge system for `/discover` command.

**Design Decision**: Replace RAG semantic search with CKS `search_semantic()` as the primary knowledge backend, eliminating duplication and providing richer features.

**Benefits**:
- ✅ Single source of truth (CKS)
- ✅ Coding standards included in search
- ✅ Rich metadata and cross-graph relationships
- ✅ Simplified maintenance (1 system vs 3)
- ⚠️ Acceptable performance trade-off (50-200ms vs 13-22ms)

---

## 1. Current Architecture Analysis

### 1.1 Existing Data Flow

```
/discover Command
    │
    ├─→ VectorKnowledgeManager (RAG)
    │   ├─ Chat history (~8,760 entries)
    │   ├─ patterns.jsonl (22 patterns)
    │   ├─ FAISS IVF+PQ index
    │   └─ Speed: 13-22ms
    │
    ├─→ CKSQueryInterface
    │   ├─ Python/TypeScript standards (20 standards)
    │   ├─ Hyper-graph query
    │   ├─ Cross-graph relationships
    │   └─ Speed: 50-200ms
    │
    └─→ Code Intelligence Explorer
        ├─ LSP integration
        ├─ ast-grep patterns
        └─ Graph database queries
```

### 1.2 Current Issues

**Duplication**:
- ❌ patterns.jsonl stored in both RAG and separately
- ❌ Semantic search implemented twice
- ❌ Chat history in RAG, not in CKS

**Inconsistency**:
- ❌ RAG doesn't include coding standards
- ❌ Rich metadata only in CKS
- ❌ Two different query APIs

**Maintenance**:
- ❌ 3 separate systems to sync
- ❌ No single source of truth
- ❌ Complex integration points

---

## 2. Proposed Architecture

### 2.1 Target Data Flow

```
/discover Command
    │
    └─→ CKS Unified Interface (PRIMARY)
        │
        ├─→ search_semantic()
        │   ├─ KNOWLEDGE graph
        │   │   ├─ Patterns (22 from patterns.jsonl)
        │   │   ├─ Coding standards (20: Python + TypeScript)
        │   │   ├─ Knowledge articles
        │   │   └─ Rich metadata (categories, focus areas, tags)
        │   │
        │   ├─ VECTOR graph
        │   │   ├─ Embeddings (SQLite BLOB)
        │   │   ├─ Cosine similarity (Python)
        │   │   └─ Adaptive thresholds (0.45-0.55)
        │   │
        │   ├─ Cross-graph relationships
        │   │   ├─ Semantic similarity
        │   │   ├─ Knowledge representation
        │   │   └─ Temporal sequences
        │   │
        │   └─ Speed: 50-200ms (acceptable)
        │
        ├─→ RAG Fallback (OPTIONAL)
        │   └─ Graceful degradation if CKS unavailable
        │
        └─→ Code Intelligence Explorer
            ├─ LSP integration (unchanged)
            ├─ ast-grep patterns (unchanged)
            └─ Graph database queries (unchanged)
```

### 2.2 Simplified View

```
BEFORE (3 systems):
  RAG (patterns + chat) + CKS (standards) + VectorManager

AFTER (1 system):
  CKS (patterns + standards + chat + metadata + cross-graph)
```

---

## 3. Component Design

### 3.1 explorer_spec.py Changes

**File**: `P:/__csf.nip/src/modules/discover/explorer_spec.py`

#### Change 1: Import CKS

**Location**: Lines 1-50 (imports section)

**BEFORE**:
```python
from modules.knowledge_system.knowledge_system.src.vector_rag_integration import VectorKnowledgeManager
# No CKS import for semantic search
```

**AFTER**:
```python
from modules.knowledge_system.knowledge_system.src.vector_rag_integration import VectorKnowledgeManager
from src.cks.unified import CKS  # NEW: Import CKS
```

#### Change 2: Initialize CKS

**Location**: Lines 214-300 (`_initialize_components` method)

**BEFORE**:
```python
# Line 236-238
if VectorKnowledgeManager:
    self.vector_manager = VectorKnowledgeManager()
    logger.debug("Vector Manager ready for semantic search")
```

**AFTER**:
```python
# Line 236-238 (keep for fallback)
if VectorKnowledgeManager:
    self.vector_manager = VectorKnowledgeManager()  # Keep as fallback
    logger.debug("Vector Manager ready (backup)")

# NEW: Initialize CKS
try:
    self.cks = CKS()
    logger.info("CKS initialized as primary semantic search backend")
except Exception as e:
    logger.warning(f"CKS initialization failed, using RAG fallback: {e}")
    self.cks = None
```

#### Change 3: Update semantic_search()

**Location**: Lines 583+ (semantic_search method)

**BEFORE**:
```python
def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
    """Semantic search using VectorKnowledgeManager."""
    return self.vector_manager.search(query, limit=limit)
```

**AFTER**:
```python
def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
    """Semantic search using CKS (primary) with RAG fallback.

    Priority:
    1. CKS search_semantic() (rich metadata, standards, cross-graph)
    2. RAG fallback (graceful degradation)
    """
    try:
        if self.cks:
            # Use CKS as primary semantic search backend
            results = self.cks.search_semantic(
                query=query,
                limit=limit,
                entry_type=None  # Search all types (pattern, memory, code, knowledge)
            )

            # Transform CKS results to expected format
            return [
                {
                    'id': r['id'],
                    'type': r['type'],
                    'title': r.get('title', ''),
                    'content': r['content'],
                    'similarity': r.get('similarity', 0.0),
                    'metadata': json.loads(r.get('metadata', '{}')),
                    'source': 'cks'
                }
                for r in results
            ]
    except Exception as e:
        logger.warning(f"CKS semantic search failed, using RAG fallback: {e}")

    # Fallback to RAG if CKS unavailable or failed
    if self.vector_manager:
        logger.debug("Using RAG fallback for semantic search")
        rag_results = self.vector_manager.search(query, limit=limit)

        # Mark results as RAG source
        for result in rag_results:
            result['source'] = 'rag'

        return rag_results

    # No backend available
    logger.error("Both CKS and RAG unavailable")
    return []
```

### 3.2 Pattern Migration Script

**New File**: `P:/__csf.nip/src/modules/discover/migrate_patterns_to_cks.py`

```python
#!/usr/bin/env python3
"""
Migrate patterns.jsonl to CKS knowledge base.

This script:
1. Reads patterns from .data/knowledge/patterns.jsonl
2. Ingests each pattern into CKS using ingest_pattern()
3. Verifies all patterns ingested successfully
4. Reports results

Usage:
    python migrate_patterns_to_cks.py
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cks.unified import CKS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def extract_title_from_markdown(content: str) -> str:
    """Extract title from markdown content.

    Args:
        content: Full markdown content

    Returns:
        First heading as title, or "Untitled Pattern"
    """
    # Match first # heading
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fallback: use first line
    first_line = content.split('\n')[0].strip()
    if first_line:
        return first_line[:100]  # Truncate long titles

    return "Untitled Pattern"


def migrate_patterns_to_cks(
    patterns_path: Path,
    backup_path: Path,
    verify_count: int = 22
) -> bool:
    """Migrate patterns from patterns.jsonl to CKS.

    Args:
        patterns_path: Path to patterns.jsonl
        backup_path: Path to backup directory
        verify_count: Expected number of patterns (default: 22)

    Returns:
        True if successful
    """
    logger.info(f"Starting pattern migration from {patterns_path}")

    # Verify patterns.jsonl exists
    if not patterns_path.exists():
        logger.error(f"Patterns file not found: {patterns_path}")
        return False

    # Create backup
    backup_path.mkdir(parents=True, exist_ok=True)
    backup_file = backup_path / f"patterns.jsonl.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(patterns_path, backup_file)
    logger.info(f"Backup created: {backup_file}")

    # Initialize CKS
    cks = CKS()
    logger.info("CKS initialized")

    # Read and migrate patterns
    ingested_count = 0
    skipped_count = 0

    with open(patterns_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                pattern = json.loads(line)
                content = pattern.get('content', '')

                if not content or not content.strip():
                    logger.warning(f"Line {line_num}: Empty content, skipping")
                    skipped_count += 1
                    continue

                # Extract title
                title = extract_title_from_markdown(content)

                # Ingest into CKS
                entry_id = cks.ingest_pattern(
                    title=title,
                    content=content,
                    entry_type="pattern",
                    source_chunk=content,  # Use full content for embedding
                    metadata={
                        'source': 'patterns.jsonl',
                        'category': pattern.get('session_id', 'general'),
                        'project': pattern.get('project', 'knowledge_base'),
                        'timestamp': pattern.get('timestamp', 0),
                        'migrated_at': datetime.now(timezone.utc).isoformat(),
                        'original_line': line_num
                    }
                )

                ingested_count += 1
                logger.info(f"[{ingested_count}/{verify_count}] Ingested: {title}")

            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: Invalid JSON, skipping: {e}")
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"Line {line_num}: Failed to ingest: {e}")
                skipped_count += 1
                continue

    # Verification
    logger.info(f"\nMigration complete:")
    logger.info(f"  Ingested: {ingested_count} patterns")
    logger.info(f"  Skipped: {skipped_count} patterns")
    logger.info(f"  Expected: {verify_count} patterns")

    if ingested_count != verify_count:
        logger.error(f"❌ Count mismatch! Expected {verify_count}, got {ingested_count}")
        return False

    # Verify with CKS query
    logger.info("\nVerifying with CKS semantic search...")
    test_queries = [
        "database connection pooling",
        "memoization and caching",
        "type hints"
    ]

    for query in test_queries:
        results = cks.search_semantic(query, entry_type="pattern", limit=5)
        logger.info(f"  Query '{query}': {len(results)} results")

    logger.info("\n✅ Migration successful!")
    return True


def main():
    print("=" * 60)
    print("Pattern Migration: patterns.jsonl → CKS")
    print("=" * 60)
    print()

    # Paths
    project_root = Path('P:/__csf.nip')
    patterns_path = project_root / '.data' / 'knowledge' / 'patterns.jsonl'
    backup_path = project_root / '.data' / 'archive'

    # Run migration
    success = migrate_patterns_to_cks(
        patterns_path=patterns_path,
        backup_path=backup_path,
        verify_count=22
    )

    if not success:
        print("\n❌ Migration failed. Check logs above.")
        print(f"Backup available at: {backup_path}")
        return 1

    print()
    print("Next steps:")
    print("1. Test /discover command to verify CKS integration")
    print("2. If satisfied, deprecate patterns.jsonl:")
    print(f"   mv {patterns_path} {backup_path / 'patterns.jsonl.deprecated'}")
    print()
    return 0


if __name__ == '__main__':
    exit(main())
```

---

## 4. Data Flow Diagram

### 4.1 Migration Flow

```
patterns.jsonl (22 patterns)
    │
    ├─→ Backup to .archive/
    │   └─→ patterns.jsonl.backup.20251224_030000
    │
    └─→ migrate_patterns_to_cks.py
        │
        ├─→ For each pattern:
        │   ├─ Extract title (first # heading)
        │   ├─ Call cks.ingest_pattern()
        │   │   ├─ Generate embedding (all-MiniLM-L6-v2)
        │   │   ├─ Store in entries table (SQLite)
        │   │   └─ Return entry_id
        │   └─ Log progress
        │
        ├─→ Verification:
        │   ├─ Count = 22 ✅
        │   ├─ Test queries return results ✅
        │   └─ Embeddings generated ✅
        │
        └─→ Success! patterns.jsonl can be deprecated
```

### 4.2 Query Flow (After Migration)

```
/discover "database patterns"
    │
    └─→ explorer_spec.py::semantic_search()
        │
        ├─→ Try CKS first:
        │   ├─ cks.search_semantic("database patterns")
        │   │
        │   ├─→ Phase 1: Query expansion (optional)
        │   │   └─→ "database connection pooling patterns"
        │   │
        │   ├─→ Embedding generation:
        │   │   └─→ all-MiniLM-L6-v2 (384-dim)
        │   │
        │   ├─→ Fetch from SQLite:
        │   │   └─→ SELECT * FROM entries WHERE embedding IS NOT NULL
        │   │
        │   ├─→ Cosine similarity:
        │   │   ├─→ Compare query embedding with each entry
        │   │   └─→ Filter by adaptive threshold (0.50)
        │   │
        │   ├─→ Apply boosts:
        │   │   ├─→ Success boost (usage_count)
        │   │   ├─→ Intent boost (keyword matching)
        │   │   └─→ Temporal boost (recent entries)
        │   │
        │   ├─→ Rank by final_score
        │   │
        │   └─→ Return top-10 results:
        │       ├─→ database.md (similarity: 0.89)
        │       ├─→ caching.md (similarity: 0.75)
        │       ├─→ Python Standard #3 (similarity: 0.71)
        │       └─→ ... (10 results total)
        │
        ├─→ Transform to expected format:
        │   └─→ Add 'source': 'cks' metadata
        │
        └─→ Return to /discover
```

---

## 5. Migration Strategy

### 5.1 Phase 1: Patterns Migration (REQUIRED)

**Objective**: Migrate 22 patterns from patterns.jsonl to CKS

**Steps**:
1. ✅ Backup patterns.jsonl to `.archive/`
2. ✅ Run `migrate_patterns_to_cks.py`
3. ✅ Verify count (22 patterns)
4. ✅ Test semantic search queries
5. ✅ Keep patterns.jsonl as backup (don't delete yet)

**Rollback Plan**:
- If migration fails: Restore from backup
- If queries fail: Debug CKS search_semantic()
- If count mismatch: Check for skipped entries in logs

**Success Criteria**:
- [ ] 22 patterns ingested into CKS
- [ ] Test queries return results
- [ ] Similarity scores > 0.5 for relevant queries
- [ ] Metadata preserved (category, project, timestamp)

### 5.2 Phase 2: /discover Integration (REQUIRED)

**Objective**: Update /discover to use CKS as primary backend

**Steps**:
1. ✅ Modify `explorer_spec.py` to import CKS
2. ✅ Initialize CKS in `_initialize_components()`
3. ✅ Update `semantic_search()` to use CKS
4. ✅ Keep RAG as fallback (graceful degradation)
5. ✅ Test with various queries

**Rollback Plan**:
- If CKS fails: Automatic fallback to RAG
- If performance issues: Revert to RAG-only
- If breaking changes: Git revert explorer_spec.py changes

**Success Criteria**:
- [ ] /discover uses CKS by default
- [ ] RAG fallback works when CKS unavailable
- [ ] Query performance <200ms
- [ ] Results include patterns + standards

### 5.3 Phase 3: Deprecation (OPTIONAL)

**Objective**: Deprecate legacy systems after successful migration

**Steps**:
1. ⚠️ Verify /discover working correctly with CKS for 1 week
2. ⚠️ Move patterns.jsonl to `.archive/patterns.jsonl.deprecated`
3. ⚠️ Update `build_production_compressed_rag.py` to skip patterns.jsonl
4. ⚠️ Update documentation to reflect CKS-first architecture
5. ⚠️ Mark RAG as "legacy backup only"

**Rollback Plan**:
- Keep patterns.jsonl in `.archive/` for 6 months
- Keep RAG code available for quick rollback
- Document rollback procedure

**Success Criteria**:
- [ ] No regressions in /discover functionality
- [ ] All queries return expected results
- [ ] Performance acceptable (<200ms)
- [ ] Documentation updated

---

## 6. Configuration Changes

### 6.1 CKS Configuration

**File**: `P:/__csf.nip/.cks/cks_config.json`

**Current Configuration**:
```json
{
  "database_path": "P:/__csf.nip/.cks/cks.db",
  "enable_semantic": true,
  "embedding_model": "all-MiniLM-L6-v2",
  "enable_memory_efficient_rag": false,
  "phase1_available": true,
  "phase2_available": true
}
```

**No Changes Required**: CKS already configured correctly

### 6.2 /discover Configuration

**File**: `P:/__csf.nip/src/modules/discover/config.json` (if exists)

**Add**:
```json
{
  "semantic_search_backend": "cks",
  "enable_rag_fallback": true,
  "cks_priority": 1,
  "rag_priority": 2
}
```

**Note**: If no config file exists, use environment variables or constants

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Test 1: Pattern Migration**
```python
def test_pattern_migration():
    cks = CKS()

    # Before migration
    results_before = cks.search_semantic("database", entry_type="pattern")
    count_before = len(results_before)

    # Migrate single pattern
    entry_id = cks.ingest_pattern(
        title="Test Pattern",
        content="# Test Pattern\n\nDatabase connection pooling...",
        entry_type="pattern"
    )

    # After migration
    results_after = cks.search_semantic("database", entry_type="pattern")
    count_after = len(results_after)

    assert count_after == count_before + 1
    assert any(r['id'] == entry_id for r in results_after)
```

**Test 2: CKS Semantic Search**
```python
def test_cks_semantic_search():
    cks = CKS()

    results = cks.search_semantic("database connection pooling", limit=5)

    assert len(results) > 0
    assert all('similarity' in r for r in results)
    assert all(r['similarity'] > 0.5 for r in results)
    assert results[0]['similarity'] >= results[-1]['similarity']  # Sorted
```

**Test 3: /discover Integration**
```python
def test_discover_cks_integration():
    explorer = ExplorerSpec()

    # Test CKS primary
    results = explorer.semantic_search("type safety patterns")

    assert len(results) > 0
    assert all('source' in r for r in results)
    assert any(r['source'] == 'cks' for r in results)

    # Verify results include standards
    assert any('standard' in r.get('metadata', {}).get('focus_area', '') for r in results)
```

### 7.2 Integration Tests

**Test 1: End-to-End Query**
```bash
# Test query
/discover "database connection pooling"

# Expected output:
# - 10 results
# - Includes database.md pattern (similarity > 0.8)
# - Includes relevant standards
# - Query time <200ms
```

**Test 2: RAG Fallback**
```python
def test_rag_fallback():
    explorer = ExplorerSpec()

    # Simulate CKS failure
    explorer.cks = None

    # Should fallback to RAG
    results = explorer.semantic_search("database patterns")

    assert len(results) > 0
    assert all(r['source'] == 'rag' for r in results)
```

### 7.3 Performance Tests

**Test 1: Query Latency**
```python
import time

def test_query_latency():
    cks = CKS()

    queries = [
        "database connection pooling",
        "memoization and caching",
        "type safety patterns",
        "async error handling",
        "API design best practices"
    ]

    times = []
    for query in queries:
        start = time.time()
        results = cks.search_semantic(query, limit=10)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    assert avg_time < 200, f"Average query time {avg_time:.2f}ms exceeds 200ms threshold"

    print(f"✅ Average query time: {avg_time:.2f}ms")
```

**Test 2: Scalability**
```python
def test_scalability():
    cks = CKS()

    # Query with increasing limits
    for limit in [10, 20, 50, 100]:
        start = time.time()
        results = cks.search_semantic("database patterns", limit=limit)
        elapsed = (time.time() - start) * 1000  # ms

        print(f"Limit={limit}: {elapsed:.2f}ms, {len(results)} results")
        assert len(results) <= limit
```

---

## 8. Risk Mitigation

### 8.1 Technical Risks

| Risk | Mitigation |
|------|------------|
| **Query performance degradation** | Acceptable trade-off (50-200ms vs 13-22ms), monitor after migration |
| **Missing patterns during migration** | Count verification (22), test queries, backup before migration |
| **Embedding dimension mismatch** | Verify 384-dim consistency, test single pattern first |
| **CKS initialization failure** | RAG fallback, graceful degradation, error logging |

### 8.2 Operational Risks

| Risk | Mitigation |
|------|------------|
| **Breaking existing /discover workflows** | Keep RAG fallback, gradual rollout, extensive testing |
| **Data loss during migration** | Backup patterns.jsonl, verify count, test queries |
| **User confusion** | Transparent communication, documentation update, changelog |

---

## 9. Rollback Plan

### 9.1 Immediate Rollback (<1 hour)

**Trigger**: Critical bug in /discover

**Steps**:
1. Git revert `explorer_spec.py` changes
2. Restart /discover service
3. Verify /discover working with RAG

**Time to Recovery**: <5 minutes

### 9.2 Short-term Rollback (<1 day)

**Trigger**: Performance issues or data inconsistency

**Steps**:
1. Restore patterns.jsonl from `.archive/`
2. Disable CKS integration (comment out)
3. Rebuild RAG index with patterns.jsonl
4. Verify /discover working with RAG

**Time to Recovery**: <1 hour

### 9.3 Long-term Rollback (<1 week)

**Trigger**: Fundamental architecture issue

**Steps**:
1. Document issues and lessons learned
2. Design alternative architecture
3. Implement new solution
4. Migrate back to RAG + CKS hybrid

**Time to Recovery**: <1 week

---

## 10. Success Metrics

### 10.1 Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pattern migration success | 22/22 patterns | Count verification |
| Query success rate | >95% | Test query suite |
| Standards in results | Yes | Query for "Python standard" |
| RAG fallback rate | <5% | Monitor fallback logs |

### 10.2 Performance Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Query latency (p50) | 15ms | 100ms | <200ms |
| Query latency (p95) | 22ms | 180ms | <200ms |
| Query latency (p99) | 30ms | 200ms | <200ms |

### 10.3 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Result relevance | >0.7 similarity | Manual inspection |
| Standards coverage | 20 standards | Count query |
| Pattern availability | 22 patterns | Count query |
| Cross-graph relationships | Yes | Test query |

---

## 11. Documentation Updates

### 11.1 /discover Documentation

**Update**: `P:/__csf.nip/src/modules/discover/README.md`

**Add**:
```markdown
## Architecture

The `/discover` command uses the **CKS (Constitutional Knowledge System)** as its primary semantic search backend.

### Knowledge Sources

- **Patterns**: 22 patterns from `.data/knowledge/patterns.jsonl` (migrated to CKS)
- **Coding Standards**: 20 standards (10 Python + 10 TypeScript)
- **Knowledge Articles**: Cross-referenced documentation
- **Cross-Graph Relationships**: Semantic links across all graph types

### Query Flow

1. User query → CKS search_semantic()
2. Embedding generation (all-MiniLM-L6-v2)
3. Semantic similarity search (KNOWLEDGE + VECTOR graphs)
4. Cross-graph relationship expansion
5. Result ranking with multi-signal scoring
6. Top-10 results returned

### Fallback

If CKS is unavailable, the system automatically falls back to the legacy RAG system.

### Performance

- Average query time: 50-200ms (acceptable for development workflow)
- Result relevance: >0.7 similarity score
- Coverage: Patterns + Standards + Knowledge + Cross-graph
```

### 11.2 Migration Guide

**Create**: `P:/__csf.nip/docs/CKS_MIGRATION_GUIDE.md`

**Content**:
- Migration overview
- Step-by-step instructions
- Verification procedures
- Troubleshooting guide
- Rollback procedures

---

## 12. Next Steps

1. ✅ **Architecture Analysis Complete** - Design documented
2. **Step 6**: Create detailed implementation plan with code changes
3. **Step 7**: Task decomposition for execution
4. **Step 8**: Execute implementation (migration + /discover update)

---

**Architecture Status**: ✅ COMPLETE
**Design Decision**: CKS-first with RAG fallback
**Confidence**: HIGH
**Risk**: LOW (backup + verification + fallback)
**Recommendation**: ✅ PROCEED TO IMPLEMENTATION

---

**Next Step**: Step 6 - Implementation Plan

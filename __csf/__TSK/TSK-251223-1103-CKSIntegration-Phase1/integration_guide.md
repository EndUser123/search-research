# CKS Phase 1 Integration Guide

**TSK:** TSK-251223-1103-CKSIntegration-Phase1
**Date:** 2025-12-23
**Purpose:** Integrate query expansion and re-ranking modules into CKS unified interface

---

## Integration Overview

This document provides step-by-step instructions for integrating the Phase 1 enhancements (Query Expansion and Advanced Re-ranking) into the CKS unified interface.

**Files to Modify:**
1. `src/cks/unified.py` - Add imports and modify `search_semantic` method
2. `commands/knowledge/cks_spec.py` (or equivalent CLI command) - Add CLI flags

**Expected Impact:**
- Query expansion: +20-30% recall improvement
- Re-ranking: +15-25% precision improvement
- Combined: 35-55% search quality improvement

---

## Step 1: Add Phase 1 Imports to unified.py

**Location:** After line 31 (after `from uuid import uuid4`)

**Add:**
```python
# Phase 1 enhancement imports
try:
    from cks.query_expansion import QueryExpander, expand_query_if_enabled
    from cks.reranking import (
        reciprocal_rank_fusion,
        maximal_marginal_relevance,
        calculate_temporal_boost,
        SearchResultsMerger
    )
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
```

---

## Step 2: Modify search_semantic Signature

**Location:** Line 645 in `src/cks/unified.py`

**Current signature:**
```python
def search_semantic(self, query: str, entry_type: Optional[str] = None, limit: int = 5) -> List[Dict]:
```

**Replace with:**
```python
def search_semantic(
    self,
    query: str,
    entry_type: Optional[str] = None,
    limit: int = 5,
    expand_query: bool = False,
    fusion_method: Optional[str] = None,
    diversity: Optional[float] = None,
    entity_slug: Optional[str] = None
) -> List[Dict]:
    """
    Search entries using semantic similarity with Phase 1 enhancements.

    Args:
        query: Search query text
        entry_type: Filter by type (optional)
        limit: Max results to return
        expand_query: Enable query expansion using synonyms/abbreviations (Phase 1)
        fusion_method: Method for combining results ('rrf', None)
        diversity: MMR diversity balance (0.0=pure relevance, 1.0=pure diversity)
        entity_slug: Entity slug for entity-specific term expansion

    Returns:
        List of matching entries with enhanced scoring
    """
```

---

## Step 3: Add Phase 1 Logic to search_semantic

**Location:** After line 656 (after the `if not self.enable_semantic` check)

**Insert the following logic:**

```python
# ========================================================================
# Phase 1: Query Expansion
# ========================================================================
if expand_query and PHASE1_AVAILABLE:
    expander = QueryExpander()
    expanded_queries = expander.expand_query(
        query,
        entity_slug=entity_slug,
        max_variations=5
    )

    # Search all query variations and collect results
    all_results = []
    seen_ids = set()

    for expanded_query in expanded_queries:
        # Generate embedding for this variation
        query_embedding = self._generate_embedding(expanded_query)
        if query_embedding is None:
            continue

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            continue

        cursor = self.conn.cursor()
        if entry_type:
            cursor.execute("""
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE type = ? AND embedding IS NOT NULL
            """, (entry_type,))
        else:
            cursor.execute("""
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE embedding IS NOT NULL
            """)

        for row in cursor.fetchall():
            # Skip duplicates
            if row["id"] in seen_ids:
                continue
            seen_ids.add(row["id"])

            entry_vec = self._deserialize_embedding(row["embedding"])
            if entry_vec is None:
                continue

            similarity = self._cosine_similarity(query_vec, entry_vec)
            if similarity < adaptive_threshold:
                continue

            success_boost = self.get_success_boost(row["id"])
            intent_boost = self._detect_intent_boost(expanded_query, row["type"])
            boost = success_boost * intent_boost

            usage_count = row["usage_count"] or 0
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=success_boost,
                created_at=row["created_at"],
                usage_count=usage_count,
                intent_boost=intent_boost
            )

            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            display_content = row["source_chunk"] if row["source_chunk"] else row["content"]

            all_results.append({
                "id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "source_chunk": row["source_chunk"],
                "display_content": display_content,
                "metadata": metadata,
                "created_at": row["created_at"],
                "similarity": similarity,
                "boost": boost,
                "success_boost": success_boost,
                "intent_boost": intent_boost,
                "boosted_similarity": similarity * boost,
                "usage_count": usage_count,
                "final_score": final_score,
                "query_type": query_type,
                "threshold_used": adaptive_threshold
            })

    # Sort by final_score
    all_results.sort(key=lambda x: x["final_score"], reverse=True)
    results = all_results[:limit * 2]  # Keep more for fusion/diversity

else:
    # Original semantic search (no expansion) - keep existing code
    # ... existing code continues ...
```

---

## Step 4: Add RRF Fusion Logic

**Location:** After Phase 1 expansion code, before final return

**Insert:**
```python
# ========================================================================
# Phase 2: RRF Fusion (if requested)
# ========================================================================
if fusion_method == 'rrf' and PHASE1_AVAILABLE:
    keyword_results = self.search(query, entry_type=entry_type, limit=limit)

    # Merge semantic and keyword results with RRF
    merged = reciprocal_rank_fusion(
        [results, keyword_results],
        k=60
    )
    results = merged[:limit * 2]
```

---

## Step 5: Add MMR Diversity Logic

**Location:** After RRF fusion logic

**Insert:**
```python
# ========================================================================
# Phase 3: MMR Diversity (if requested)
# ========================================================================
if diversity is not None and PHASE1_AVAILABLE and len(results) > 1:
    results = maximal_marginal_relevance(
        query=query,
        results=results,
        lambda_param=diversity,
        limit=limit
    )
else:
    results = results[:limit]
```

---

## Step 6: Add Enhanced Temporal Boosting

**Location:** After MMR logic, before final return

**Insert:**
```python
# ========================================================================
# Phase 4: Enhanced Temporal Boosting
# ========================================================================
if PHASE1_AVAILABLE:
    for result in results:
        if 'temporal_boost' not in result:
            entry = {
                'created_at': result.get('created_at', ''),
                'type': result.get('type', 'memory'),
                'usage_count': result.get('usage_count', 0),
                'thumbs_up': result.get('thumbs_up', 0),
                'thumbs_down': result.get('thumbs_down', 0)
            }
            temporal_boost = calculate_temporal_boost(entry)
            result['temporal_boost'] = temporal_boost
            result['final_score'] *= temporal_boost

# Final sort by enhanced score
results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
return results[:limit]
```

---

## CLI Integration (Step 4)

**File:** `commands/knowledge/cks_spec.py` (or equivalent CLI command)

**Add the following CLI options:**

```python
@click.option('--expand-query', is_flag=True,
              help='Expand query using synonyms and abbreviations')
@click.option('--fusion-method', type=click.Choice(['rrf', 'score', 'rank']),
              help='Method for combining search results (rrf=Reciprocal Rank Fusion)')
@click.option('--diversity', type=float, default=None,
              help='Diversity balance (0.0=pure relevance, 0.7=balanced, 1.0=pure diversity)')
@click.option('--entity', type=str, default=None,
              help='Entity slug for entity-specific term expansion')
```

**Example usage:**
```bash
# Query expansion
/cks search "db timeout" --expand-query

# RRF fusion
/cks search "api error" --fusion-method rrf

# MMR diversity
/cks search "database" --diversity 0.7

# Combined
/cks search "fix bug" --expand-query --fusion-method rrf --diversity 0.6 --entity taskmaster
```

---

## Testing Instructions

### Manual Integration Tests

**Test 1: Query Expansion**
```python
from cks.unified import CKS

cks = CKS()

# Test abbreviation expansion
results = cks.search_semantic("cks db auth", expand_query=True)
print(f"Found {len(results)} results with expansion")
for r in results:
    print(f"  - {r['title']}: {r['final_score']:.3f}")
```

**Test 2: RRF Fusion**
```python
results = cks.search_semantic("api timeout", fusion_method='rrf')
print(f"Found {len(results)} results with RRF fusion")
```

**Test 3: MMR Diversity**
```python
results = cks.search_semantic("error", diversity=0.7)
print(f"Found {len(results)} diverse results")
```

**Test 4: Combined Features**
```python
results = cks.search_semantic(
    "fix bug",
    expand_query=True,
    fusion_method='rrf',
    diversity=0.6,
    entity_slug="taskmaster"
)
print(f"Found {len(results)} results with all features")
```

### Expected Results

- **Query Expansion:** Should find more results for abbreviated queries (e.g., "db" → "database")
- **RRF Fusion:** Should combine the best of semantic and keyword search
- **MMR Diversity:** Should show more diverse, less redundant results
- **Combined:** Should show the best overall improvement

---

## Troubleshooting

### Issue: Import errors for Phase 1 modules

**Solution:** Ensure the following files exist:
- `src/cks/query_expansion.py`
- `src/cks/reranking.py`

### Issue: No improvement in results

**Possible causes:**
1. Query expansion not working - check that expanded queries are being generated
2. RRF fusion not combining results - check that keyword search is working
3. MMR diversity not applied - check diversity parameter is not None

**Debug:**
```python
# Enable debug prints
expander = QueryExpander()
expanded = expander.expand_query("db timeout")
print(f"Expanded queries: {expanded}")
```

### Issue: Performance degradation

**Expected:** Query expansion adds 50-100ms latency

**If slower than expected:**
- Check that embeddings are being cached properly
- Limit `max_variations` to 5 or less
- Consider not using all features simultaneously

---

## Performance Baseline

Run before and after integration to measure improvement:

```python
from cks.unified import CKS
import time

cks = CKS()

test_queries = [
    "db timeout",
    "cks auth",
    "api error",
    "fix bug",
    "test pattern"
]

print("=== Before Phase 1 ===")
for q in test_queries:
    start = time.time()
    results = cks.search_semantic(q)
    elapsed = time.time() - start
    print(f"{q}: {len(results)} results in {elapsed:.3f}s")

print("\n=== After Phase 1 (with expansion) ===")
for q in test_queries:
    start = time.time()
    results = cks.search_semantic(q, expand_query=True)
    elapsed = time.time() - start
    print(f"{q}: {len(results)} results in {elapsed:.3f}s")
```

---

## Next Steps After Integration

1. **Run integration tests** - Verify all features work
2. **Performance baseline** - Measure actual improvement
3. **Create automated test suite** - Prevent regressions
4. **Git commit** - Save integrated code

---

**Status:** Integration guide complete, ready for implementation
**Last Updated:** 2025-12-23

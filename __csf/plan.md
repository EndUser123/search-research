# HyDE Search Enhancement Implementation

**Status**: Active
**Created**: 2026-03-04
**Phase**: Implementation

## Overview

Implement three HyDE (Hypothetical Document Embeddings) search enhancements identified in architecture decision `2026-03-04_hyde-techniques-recommendation.md`:

1. **Enable Cross-Encoder Reranking** (Priority #1, 5 min) - Already implemented, just disabled
2. **Implement Multi-Query Expansion** (Priority #2, 8-12 hours) - New feature
3. **Implement Adaptive Query Routing** (Priority #3, 6-8 hours) - Use existing intent detection

**Estimated effort**: 8-12 hours total

## Current State

**Existing HyDE Implementation**:
- CKS has rule-based HyDE (`src/cks/hyde.py`) - solid implementation
- Query intent detection exists (`src/knowledge/search/query_intent.py`)
- Cross-encoder reranking exists but **disabled** (`src/knowledge/search/reranking/cross_encoder.py`)

**Missing Features**:
- Multi-query expansion: ✅ IMPLEMENTED (see `src/knowledge/search/expansion/multi_query.py`)
- Cross-encoder reranking: ✅ Implemented but disabled (requires `CROSS_ENCODER_ENABLED=1`)
- Adaptive routing: ✅ IMPLEMENTED (see `src/knowledge/search/routing/adaptive_router.py`)

## Architecture

### Module Structure

```
src/knowledge/search/
├── expansion/
│   ├── __init__.py
│   └── multi_query.py          # NEW: MultiQueryExpander class
├── routing/
│   ├── __init__.py
│   └── adaptive_router.py      # NEW: AdaptiveQueryRouter class
└── reranking/
    └── cross_encoder.py         # EXISTING: Just needs enablement
```

### Data Flow

```
Query → AdaptiveQueryRouter
    ├─→ Fast Path (keyword queries)
    ├─→ Standard Path (HyDE only)
    └─→ Enhanced Path (Multi-Query + HyDE + Reranking)
          ↓
    MultiQueryExpander → 3-5 query variants
          ↓
    Search backends (CKS, CHS, CDS, etc.)
          ↓
    CrossEncoderReranker → Re-rank top-K
          ↓
    Results
```

## Implementation Plan

### Task 1: Enable Cross-Encoder Reranking (Priority #1) ✅ FASTEST WIN

**File**: Environment configuration only (no code changes needed)

**Action**:
```bash
export CROSS_ENCODER_ENABLED=1
```

**Verification**:
- Run search query and verify `cross_encoder_score` appears in results
- Check that results are re-ranked by cross-encoder score

**Acceptance**:
- [ ] Setting `CROSS_ENCODER_ENABLED=1` enables reranking
- [ ] Results include `cross_encoder_score` field
- [ ] Top results are reordered by relevance
- [ ] No errors in logs

**Estimated effort**: 5 minutes

---

### Task 2: Implement Multi-Query Expansion (Priority #2) ✅ COMPLETE

**File**: `src/knowledge/search/expansion/multi_query.py` (new)

**Class**: `MultiQueryExpander`

**Implementation**:
```python
class MultiQueryExpander:
    """Generate 3-5 semantic variants of query for different angles.

    Uses existing query intent detection to determine expansion strategy.
    """

    def generate(self, query: str, num_variants: int = 3) -> list[str]:
        """Generate semantic paraphrases using templates.

        Args:
            query: Original search query
            num_variants: Number of variants to generate (default: 3)

        Returns:
            List of query variants including original
        """
        # Use existing query intent detection
        from knowledge.search.query_intent import classify_query_intent

        intent = classify_query_intent(query)

        if intent.intent == IntentType.TECHNICAL:
            return self._expand_technical(query, num_variants)
        elif intent.intent == IntentType.INFORMATIONAL:
            return self._expand_informational(query, num_variants)
        else:
            return [query]  # Don't expand unclear intents

    def _expand_technical(self, query: str, num_variants: int) -> list[str]:
        """Generate technical query variants."""
        variants = [query]
        # Add implementation-focused variant
        variants.append(f"{query} implementation")
        # Add best practices variant
        if num_variants > 1:
            variants.append(f"Best practices for {query}")
        # Add tutorial variant
        if num_variants > 2:
            variants.append(f"{query} tutorial")
        return variants[:num_variants]

    def _expand_informational(self, query: str, num_variants: int) -> list[str]:
        """Generate informational query variants."""
        variants = [query]
        # Add definition variant
        variants.append(f"Define {query}")
        # Add explanation variant
        if num_variants > 1:
            variants.append(f"{query} explanation")
        # Add examples variant
        if num_variants > 2:
            variants.append(f"Examples of {query}")
        return variants[:num_variants]
```

**Integration**: Update `unified_router.py` to use multi-query expansion for enhanced path

**Test**:
- Query: "async python patterns" → ["async python patterns", "async python patterns implementation", "Best practices for async python patterns"]
- Verify: Variants are semantically distinct but relevant

**Estimated effort**: 4-6 hours

---

### Task 3: Implement Adaptive Query Router (Priority #3) ✅ COMPLETE

**File**: `src/knowledge/search/routing/adaptive_router.py` (new)

**Class**: `AdaptiveQueryRouter`

**Implementation**:
```python
class AdaptiveQueryRouter:
    """Route queries to appropriate processing path.

    Uses existing QueryIntentDetector to determine complexity
    and route through fast/standard/enhanced paths.
    """

    def __init__(self):
        self.simple_threshold = 0.7  # Tune based on metrics

    def route(self, query: str, search_context) -> str:
        """Determine which pipeline to use.

        Returns:
            "fast" - No expansion (keyword queries)
            "standard" - HyDE only (existing behavior)
            "enhanced" - Multi-query + HyDE + Reranking
        """
        complexity = self._assess_complexity(query)

        if complexity >= 0.8:
            return "enhanced"
        elif complexity >= 0.5:
            return "standard"
        else:
            return "fast"

    def _assess_complexity(self, query: str) -> float:
        """Score query complexity 0-1."""
        from knowledge.search.query_intent import classify_query_intent

        intent = classify_query_intent(query)

        score = 0.0
        # High-complexity indicators
        if intent.intent in [IntentType.TECHNICAL, IntentType.EXPLORATORY]:
            score += 0.4
        # Low confidence increases complexity (need more processing)
        score += (1.0 - intent.confidence) * 0.3
        # Long queries are complex
        if len(query.split()) > 10:
            score += 0.3

        return min(score, 1.0)
```

**Integration**: Update `unified_router.py` to route queries through adaptive router

**Test**:
- "async python" → 0.5 → standard path (HyDE only)
- "how to implement async in python" → 0.9 → enhanced path
- "define async" → 0.6 → standard path

**Estimated effort**: 4-6 hours

---

## Error Handling

**Cross-Encoder Errors**:
- Model loading failure: Log warning, fall back to no reranking
- Scoring timeout: Return results unranked with warning

**Multi-Query Expansion Errors**:
- Intent detection failure: Return original query only (no expansion)
- Too many variants: Cap at 5 to avoid explosion

**Adaptive Routing Errors**:
- Router failure: Default to standard path (HyDE only)
- Complexity assessment failure: Default to enhanced path (safer)

## Test Strategy

### Unit Tests

**Cross-Encoder**:
- Test reranking with mock model
- Test feature flag behavior (enabled/disabled)
- Test timeout handling

**Multi-Query Expansion**:
- Test expansion for different intent types
- Test variant generation (technical, informational)
- Test edge cases (empty query, single word)

**Adaptive Routing**:
- Test complexity assessment
- Test routing decisions (fast/standard/enhanced)
- Test edge cases (low confidence, long queries)

### Integration Tests

- Test full pipeline: Router → Multi-Query → Search → Reranking
- Test performance: Multi-query should add <500ms per variant
- Test result quality: Enhanced path should improve relevance by 15%

### Regression Tests

- Verify existing search functionality still works
- Verify HyDE still works for CKS
- Verify query intent detection still works

## Standards Compliance

**Python 2025+ Standards** (`/code-python`):
- Type hints for all function signatures
- `dataclass` for configuration objects
- Async/await for I/O operations (model loading, scoring)
- Context managers for resource cleanup
- Error handling with specific exceptions
- Docstrings with Google style format

**Code Quality**:
- ruff for linting
- mypy for type checking
- pytest for testing (80%+ coverage required)
- Pre-commit hooks for quality gates

## Ramifications

**Impact on existing code**:
- `unified_router.py` - Add routing logic and multi-query expansion
- Environment variables - Add `CROSS_ENCODER_ENABLED` to deployment config
- Test suite - Add 15-20 new tests for new features

**Backwards compatibility**:
- All changes are additive (no breaking changes)
- Existing search behavior preserved when features disabled
- Migration path: Enable features incrementally

**Performance impact**:
- Cross-encoder: +100-200ms per query (only for top-K results)
- Multi-query: +500ms per variant (only for enhanced path)
- Routing: +50ms per query (intent detection already exists)

**Estimated total latency**:
- Fast path: No change (baseline)
- Standard path: No change (HyDE already exists)
- Enhanced path: +1.5-3s (3 variants × 500ms + reranking)

## Risk Summary

**Technical risks**:
- Cross-encoder model loading (~200MB, ~5s first load) - Mitigation: Lazy loading
- Multi-query LLM API costs (3-5x queries) - Mitigation: Adaptive routing, monitoring
- Router misclassification - Mitigation: Calibration with production data

**Operational risks**:
- Increased latency for enhanced path - Mitigation: Only route complex queries
- API quota exhaustion - Mitigation: Monitoring and throttling

**Integration risks**:
- Query intent classifier accuracy - Mitigation: Fallback to safe defaults
- Conflict with existing HyDE - Mitigation: Use existing CKS HyDE, don't duplicate

## Success Criteria

- [ ] Cross-encoder enabled and reranking works (test with `CROSS_ENCODER_ENABLED=1`)
- [ ] Multi-query expansion generates 3-5 semantic variants
- [ ] Adaptive router directs queries based on complexity
- [ ] All tests pass (unit + integration + regression)
- [ ] Test coverage ≥80% for new modules
- [ ] Performance acceptable (enhanced path <5s)
- [ ] No regressions in existing search functionality
- [ ] Knowledge updated (CKS, CLAUDE.md)

## Implementation Order

1. **Task 1** (5 min): Enable cross-encoder reranking
2. **Task 2** (4-6 hours): Implement multi-query expansion
3. **Task 3** (4-6 hours): Implement adaptive routing
4. **Integration** (2 hours): Integrate with unified_router.py
5. **Testing** (2 hours): Write and run tests
6. **Documentation** (1 hour): Update CLAUDE.md, CKS

**Total estimated effort**: 14-18 hours (consistent with architecture decision)

## References

- Architecture decision: `P:\.claude\arch_decisions\2026-03-04_hyde-techniques-recommendation.md`
- Existing query intent: `src/knowledge/search/query_intent.py`
- Existing cross-encoder: `src/knowledge/search/reranking/cross_encoder.py`
- Fudan University 2024 RAG study: "HyDE + multi-query achieves +37% relevance"

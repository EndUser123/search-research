# CKS Integration for EvidenceLedger - Implementation Summary

**Task**: Wire rca to CKS (Meta-RAG alternative)
**Status**: ✅ Completed
**Date**: 2026-02-16

## What Was Implemented

### Core Change

Added CKS integration to `EvidenceLedger` class in `evidence_tier.py`:

1. **`EvidenceLedger.store_to_cks()`** - Store evidence ledger to CKS as a pattern
   - Uses existing `cks.ingest_pattern()` with automatic embedding
   - No new `embed_and_store()` helper needed - infrastructure already exists
   - Graceful fallback if CKS is unavailable

2. **`store_rca_finding()`** - Convenience function for quick RCA finding storage
   - Creates EvidenceLedger, populates it, and stores to CKS in one call

### Key Features

- **Automatic embedding**: CKS's `ingest_pattern()` generates 768-dimension vectors via sentence-transformers
- **Structured metadata**: Stores outcome, confidence ceiling, evidence tier breakdown
- **Semantic search**: RCA findings are searchable via CKS semantic search
- **Evidence tier tracking**: Each finding includes tier breakdown for confidence ceiling calculation

### Files Modified

| File | Changes |
|------|---------|
| `src/rca/evidence_tier.py` | Added `store_to_cks()` method and `store_rca_finding()` convenience function, added CKS import with graceful fallback |
| `src/rca/__init__.py` | Exported `store_rca_finding` |

## API Usage

```python
from rca import EvidenceLedger, classify_evidence, store_rca_finding

# Method 1: Using EvidenceLedger
ledger = EvidenceLedger(claim="Database connection timeout")
ledger.add_classified("stack_trace", "TimeoutError at db.py:42", citation="db.py:42")
ledger.add_classified("log_correlation", "Timeouts correlate with high load")

entry_id = ledger.store_to_cks(
    outcome="resolved",
    root_cause="Missing connection pool timeout configuration",
    fix_applied="Added connect_timeout=5 to database config",
    verification_method="pytest test_db_timeout.py -v",
)

# Method 2: Using convenience function
entry_id = store_rca_finding(
    claim="API rate limiting errors",
    outcome="resolved",
    root_cause="Missing backoff retry logic",
    fix_applied="Added exponential backoff with tenacity library",
    verification_method="Load test with 100 concurrent requests",
    evidence_sources=[
        classify_evidence("stack_trace", "RateLimitError at api.py:55"),
        classify_evidence("test_output", "pytest test_api_rate_limit.py::test_concurrent_requests FAILED"),
    ],
)
```

## CKS Entry Structure

Entries stored with:
- **Title**: `RCA: {claim}`
- **Type**: `pattern` (for semantic search)
- **Content**: Full investigation summary with evidence details
- **Source chunk**: `claim | root_cause | fix_applied` (for semantic embedding)
- **Metadata**:
  - `rca_outcome`: resolved/failed/partial/unknown
  - `confidence_ceiling`: e.g., "75%" (based on lowest evidence tier)
  - `lowest_tier`: TIER_1/TIER_2/TIER_3/TIER_4
  - `evidence_count`: Number of evidence sources
  - `tier_1_count` through `tier_4_count`: Evidence by tier
  - `root_cause`, `fix_applied`, `verification_method`: If provided

## Test Results

All 46 existing tests pass:
- `test_evidence_tier.py`: 46 tests ✅

CKS integration verified:
- Successfully stores to CKS with entry ID: `pat_92a41450da3d4aa7`
- Semantic search returns RCA findings with metadata
- Graceful fallback when CKS unavailable

## Architecture Decision

### Task #987 Resolution: Meta-RAG vs. CKS Integration

**Decision**: Use CKS instead of building separate Meta-RAG codebase indexer

**Rationale**:
1. CDS already exists for structural code indexing (AST, mtime caching, `/search` integration)
2. The gap is **semantic** search for RCA findings, not structural indexing
3. CKS already has embedding infrastructure via `sentence-transformers` (768-dim vectors)
4. `CKS.ingest_pattern()` automatically generates and stores embeddings

**What this means**:
- No new `embed_and_store()` helper needed
- No separate Meta-RAG module
- rca findings now semantically searchable via CKS
- Existing CDS provides structural code search; CKS provides semantic RCA search

## Next Steps (Future Enhancements)

1. **CLI Integration**: Add `--store-cks` flag to `/rca` command
2. **CKS Learning**: Query CKS for similar past investigations during Phase -1
3. **Pattern Extraction**: Auto-extract successful investigation patterns from stored findings
4. **Evidence Ledger Queries**: Add `query_similar_investigations()` method using CKS semantic search

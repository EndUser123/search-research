# Specification: CKS-First /discover Consolidation

**TSK-ID**: TSK-251224-CKS-Discover-05b7aa
**Created**: 2025-12-24 02:34
**Status**: In Progress

## Overview

Consolidate `/discover` command to use **CKS (Constitutional Knowledge System)** as the single unified knowledge system, eliminating the current duplication between:
- RAG semantic search (FAISS) with patterns.jsonl
- CKS hyper-graph with coding standards
- Separate vector manager backends

## Problem Statement

The `/discover` command currently uses **three separate knowledge systems**:

1. **RAG (FAISS)**: GPU-accelerated semantic search
   - Chat history (~8,760 entries)
   - patterns.jsonl (22 patterns)
   - Speed: 13-22ms
   - NO coding standards

2. **CKS Hyper-Graph**: Rich semantic knowledge
   - Python/TypeScript coding standards (ingested)
   - Knowledge patterns
   - Cross-graph relationships
   - Rich metadata and tags
   - Speed: 50-200ms (SQLite BLOB embeddings)

3. **Vector Manager**: Codebase indexing
   - Separate vector backend

**Issues:**
- **Duplication**: Patterns stored in both RAG and CKS
- **Incomplete search**: RAG doesn't include standards
- **Confusion**: Which system is authoritative?
- **Maintenance burden**: Three systems to sync
- **Architectural debt**: No single source of truth

## Proposed Solution

**Make CKS the single unified knowledge system for `/discover`:**

```
/discover command
    ↓
CKS search_semantic()
    ↓
Unified results from:
├─ KNOWLEDGE graph (patterns, standards, chat history)
├─ VECTOR graph (fast semantic search via Qdrant/FAISS)
├─ Cross-graph relationships (context)
└─ Rich metadata (tags, focus areas, constitutional compliance)
```

## Key Changes

### 1. Migrate Data to CKS
- Ingest patterns.jsonl into CKS KNOWLEDGE graph
- Migrate chat history into CKS memory entries
- Ingest RAG index entries into CKS VECTOR graph

### 2. Update /discover to Use CKS
- Replace RAG semantic search with `cks.search_semantic()`
- Remove patterns.jsonl dependency
- Keep hyper-graph query for advanced use

### 3. Cleanup
- Delete patterns.jsonl (legacy)
- Deprecate standalone RAG index (backup/export only)
- Unify documentation

## Benefits

| Feature | Current (RAG) | Proposed (CKS) |
|---------|---------------|----------------|
| **Speed** | 13-22ms | 50-200ms (acceptable) |
| **Patterns** | 22 patterns | ALL patterns + standards |
| **Standards** | ❌ Not included | ✅ Included |
| **Metadata** | Minimal | Rich (tags, focus areas) |
| **Cross-graph** | ❌ No | ✅ Yes |
| **Constitutional** | ❌ No | ✅ Yes |
| **Single system** | ❌ No | ✅ Yes |

## Success Criteria

- [ ] All patterns ingested into CKS KNOWLEDGE graph
- [ ] Chat history ingested into CKS memory
- [ ] `/discover` uses `cks.search_semantic()` by default
- [ ] Standards included in search results
- [ ] patterns.jsonl removed/deprecated
- [ ] No functionality regression
- [ ] Documentation updated
- [ ] Performance acceptable (<200ms queries)

## Non-Goals

- Optimize for speed (130ms difference is trivial for dev work)
- Implement Qdrant backend immediately (use existing SQLite embeddings)
- Rewrite CKS from scratch
- Change CKS database schema

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Query speed degradation | Accept 50-200ms as sufficient for development |
| Missing patterns in migration | Verify all patterns.jsonl ingested |
| Breaking existing workflows | Keep hyper-graph tool available |
| Data loss | Backup RAG index before migration |

## Files to Modify

1. `src/modules/discover/explorer_spec.py` - Use CKS search
2. `scripts/build_production_compressed_rag.py` - Export from CKS instead
3. `.data/knowledge/patterns.jsonl` - Deprecated after migration
4. Documentation updates

## Related Artifacts

- CKS Documentation: `P:/__csf.nip/src/cks/`
- CKS CLI: `P:/__csf.nip/src/cks/unified.py`
- Hyper-Graph: `P:/__csf.nip/src/cks/core/multi_graph_engine.py`
- Current /discover: `P:/__csf.nip/src/modules/discover/explorer_spec.py`

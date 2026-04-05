# Integration Architecture: claude-mem, /search, Checkpoint, and Memory

## Overview

**Document Version**: 1.0
**Created**: 2025-02-11
**Status**: Design Proposal (Not Implemented)

This document describes the integration architecture for four complementary systems in the CSF NIP ecosystem:

| System | Purpose | Current State |
|--------|---------|---------------|
| **claude-mem** | Persistent session memory via SQLite + Chroma vector DB | Third-party plugin, NOT installed |
| **/search** | Unified search command across CHS, CKS, CDS, code, docs, skills | Installed at `P:/__csf/src/cli/nip/search.py` |
| **Checkpoint** | Git-based rollback system with JSON snapshots | Installed at `P:/packages/checkpoint/` |
| **Memory (CKS)** | Constitutional Knowledge System for long-term storage | Installed via CKS commands |

## Executive Summary

The integration creates a **temporal knowledge fabric** spanning:
- **Session scope**: claude-mem (persistent context across sessions)
- **Query scope**: /search (unified access to all backends)
- **Recovery scope**: Checkpoint (rollback points in time)
- **Knowledge scope**: CKS (long-term verified learnings)

### Key Insight
These systems operate at **different time granularities**:
- claude-mem: Observations per conversation turn (seconds)
- /search: Query-time aggregation (milliseconds)
- Checkpoint: Snapshots per atomic operation (minutes)
- CKS: Verified knowledge (indefinite)

The integration enables **cross-system referencing** and **unified timeline views** without duplicating storage.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          UNIFIED QUERY LAYER                               │
│                           /search Command                                  │
└───────┬────────────────────────────────────────────────────────────────────┘
        │
        │ Queries all backends in parallel
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND FEDERATION                                  │
├─────────────┬─────────────┬─────────────┬─────────────┬───────────────────┤
│   CKS       │   CHS       │   CDS       │  claude-mem │    Checkpoint     │
│ (Knowledge) │ (Chat Hist) │ (Discovery) │ (Session)   │   (Snapshots)     │
├─────────────┼─────────────┼─────────────┼─────────────┼───────────────────┤
│ SQLite      │ FAISS       │ JSON        │ SQLite      │   JSON files       │
│ + Chroma    │ vectors     │ findings    │ + Chroma    │   ~/.claude/      │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────────┘
       │             │             │             │             │
       │             │             │             │             │
       ▼             ▼             ▼             ▼             ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │                    REFERENCE LINKING LAYER                             │
   │  (Cross-system IDs: checkpoint_id, observation_id, cks_entry_id)     │
   └───────────────────────────────────────────────────────────────────────┘
       │
       │ Unified Timeline View
       │
       ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │              claude-mem Web Viewer (Enhanced)                         │
   │    - Checkpoint markers on timeline                                    │
   │    - CKS cross-references from observations                           │
   │    - Search results overlay                                           │
   └───────────────────────────────────────────────────────────────────────┘
```

---

## System Profiles

### 1. claude-mem (Third-Party Plugin)

**Repository**: https://github.com/thedotmack/claude-mem

**Capabilities**:
- Persistent session memory via SQLite database
- Vector embeddings via ChromaDB (semantic search)
- Web-based viewer UI for browsing sessions
- 5 lifecycle hooks for observation capture
- Cross-session context retention

**Data Model**:
```sql
-- Core tables
observations (id, session_id, timestamp, content, embedding)
sessions (id, created_at, updated_at, metadata)
```

**Hook Points**:
1. `pre-tool` - Before tool execution
2. `post-tool` - After tool completion
3. `pre-response` - Before generating response
4. `post-response` - After response delivered
5. `session-end` - On session termination

### 2. /search (Unified Search)

**Location**: `P:/__csf/src/cli/nip/search.py`

**Current Backends**:
```python
BACKEND_CKS           # Constitutional Knowledge System
BACKEND_CHS           # Chat History Search (FAISS)
BACKEND_CDS           # Discovery findings
BACKEND_CODE_SEMANTIC # Semantic code search
BACKEND_GREP          # Text-based code search
BACKEND_DOCS          # Documentation search
BACKEND_LSP           # LSP symbol search
BACKEND_SKILLS        # Skills search
```

**Integration Point**: Add `BACKEND_CLAUDE_MEM` constant and query handler

### 3. Checkpoint System

**Location**: `P:/packages/checkpoint/`

**Data Model** (simplified):
```json
{
  "checkpoint_id": "sha256-hash",
  "timestamp": "ISO-8601",
  "files": [...],
  "metadata": {
    "terminal_id": "...",
    "complexity_score": 0-100,
    "related_observations": []  // NEW: claude-mem references
  }
}
```

**Key Constraints**:
- Max checkpoint size: 500,000 bytes
- GZIP compression for storage
- SHA-256 validation on restore

### 4. CKS (Constitutional Knowledge System)

**Purpose**: Long-term verified knowledge storage

**Integration Point**: Cross-reference observations that become verified knowledge

---

## Integration Design

### Phase 1: Reference Linking Layer

**Objective**: Enable cross-system references without data migration.

#### 1.1 Schema Extensions

**claude-mem observation metadata**:
```json
{
  "observation_id": "uuid",
  "checkpoint_id": "sha256-hash",  // Link to checkpoint if applicable
  "cks_entry_id": "cks-key",        // Link if promoted to knowledge
  "search_queries": [                // Queries that retrieved this
    {"query": "...", "backend": "...", "timestamp": "..."}
  ]
}
```

**Checkpoint metadata extension**:
```json
{
  "related_observations": [  // NEW field
    {
      "observation_id": "uuid",
      "session_id": "uuid",
      "relevance_score": 0.0-1.0
    }
  ]
}
```

**CKS entry enhancement**:
```yaml
---
source_observation_id: uuid
checkpoint_created_at: timestamp
related_checkpoints: [sha256-hash]
---
```

#### 1.2 Reference Inference Logic

When creating a checkpoint:
1. Scan claude-mem observations in current time window (±30 seconds)
2. Calculate relevance using:
   - Temporal proximity
   - Content similarity (vector search)
   - Tool usage overlap
3. Link top N observations (default: N=3, relevance > 0.7)

---

### Phase 2: Query Federation

**Objective**: Make `/search` query all backends including claude-mem.

#### 2.1 Backend Implementation

**File**: `P:/__csf/src/cli/nip/search.py`

```python
# Add to backend constants
BACKEND_CLAUDE_MEM = "claude-mem"

# Add to backend registry
_BACKENDS = {
    # ... existing backends ...
    BACKEND_CLAUDE_MEM: ClaudeMemSearchBackend,
}
```

#### 2.2 Backend Class

```python
class ClaudeMemSearchBackend(SearchBackend):
    """Search claude-mem observations."""

    def __init__(self):
        self.db_path = Path.home() / ".claude" / "claude-mem" / "observations.db"
        self.vector_store = Chroma(
            persist_directory=Path.home() / ".claude" / "claude-mem" / "chroma"
        )

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        # Hybrid search: keyword + semantic
        keyword_results = self._keyword_search(query, limit)
        semantic_results = self._semantic_search(query, limit)
        return self._merge_and_rank(keyword_results, semantic_results, limit)
```

#### 2.3 Result Format

```python
@dataclass
class SearchResult:
    backend: str          # "claude-mem", "cks", "chs", etc.
    title: str
    content: str
    score: float
    metadata: dict
    cross_refs: dict      # NEW: Links to other systems
    # {
    #   "checkpoint_id": "sha256-hash",
    #   "cks_entries": ["key1", "key2"],
    #   "related_observations": ["uuid1", "uuid2"]
    # }
```

---

### Phase 3: Unified Timeline View

**Objective**: Enhanced claude-mem web viewer showing cross-system context.

#### 3.1 UI Components

**Timeline with Event Types**:
- 💬 **Chat messages** (existing)
- 🔧 **Tool executions** (existing)
- 📌 **Checkpoint markers** (NEW)
- 📚 **CKS cross-references** (NEW)
- 🔍 **Search queries** (NEW)

#### 3.2 Checkpoint Detail Panel

When clicking a checkpoint marker:
```json
{
  "checkpoint_id": "sha256-hash",
  "timestamp": "2025-02-11T14:30:00Z",
  "files_changed": 12,
  "complexity_score": 45,
  "related_observations": [
    {
      "id": "uuid-1",
      "content_preview": "Discussion of auth refactor...",
      "relevance": 0.89
    }
  ],
  "restore_action": "Rollback to this point"
}
```

#### 3.3 CKS Promotion Flow

From any observation:
1. Click "Promote to CKS" button
2. Opens CKS creation form pre-filled with:
   - Observation content
   - Related checkpoint IDs
   - Timestamps
   - Cross-references
3. Save creates CKS entry with source metadata

---

## Implementation Plan

### Phase 1: Reference Linking (2-3 days)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Define schema extensions | 2h | None |
| Implement checkpoint observation scanner | 4h | None |
| Add cross-reference storage to checkpoint_store.py | 3h | None |
| Update claude-mem hook for checkpoint awareness | 3h | claude-mem installed |
| Unit tests for reference linking | 2h | All above |

**Acceptance Criteria**:
- Checkpoints include `related_observations` array
- Observations link to `checkpoint_id` when created during checkpoint window
- Query backlinks work both directions

### Phase 2: Query Federation (2-3 days)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Install claude-mem plugin | 1h | None |
| Create ClaudeMemSearchBackend class | 4h | claude-mem installed |
| Add backend to /search registry | 1h | Backend class |
| Implement hybrid search (keyword + semantic) | 3h | Backend class |
| Update search CLI with claude-mem option | 2h | All above |
| Integration tests | 2h | All above |

**Acceptance Criteria**:
- `/search --backend claude-mem "query"` returns results
- `/search --all` includes claude-mem results
- Results include cross-reference metadata
- Fallback graceful if claude-mem not available

### Phase 3: Unified Timeline (3-4 days)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Fork/clone claude-mem web viewer | 1h | None |
| Add checkpoint marker component | 4h | Phase 1 complete |
| Add CKS cross-reference component | 3h | Phase 1 complete |
| Implement checkpoint detail panel | 3h | Marker component |
| Add CKS promotion flow | 4h | CKS component |
| Style consistency with existing UI | 2h | All components |

**Acceptance Criteria**:
- Timeline shows all event types
- Clicking checkpoint marker shows details
- CKS promotion creates entries with source metadata
- No regression in existing claude-mem functionality

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| claude-mem not maintained | Medium | High | Design for graceful degradation, wrap with adapter |
| Schema conflicts between systems | Low | Medium | Use loose coupling (references not joins) |
| Performance degradation | Low | High | Async queries, result caching, pagination |
| Checkpoint size bloat | Medium | Medium | Limit references stored, use deduplication |
| claude-mem install fails | Low | High | Provide install script, verify prerequisites |

---

## Compatibility Analysis

### No Conflicts Detected

1. **Storage Isolation**: Each system uses distinct storage locations
2. **No API Overlap**: Hook points are complementary, not competing
3. **Data Format Compatibility**: All use JSON/SQLite, easily cross-referenced

### Dependency Requirements

```
claude-mem requires:
  - Python 3.10+
  - SQLite (built-in)
  - ChromaDB (pip install)
  - Flask (for web viewer)

/search requires:
  - Existing Python dependencies (no change)

Checkpoint requires:
  - No new dependencies
```

---

## Success Metrics

1. **Integration Completeness**
   - All 4 systems accessible via unified interface
   - Cross-system references functional
   - Timeline view operational

2. **Performance**
   - Unified search completes in < 2 seconds
   - Checkpoint creation overhead < 100ms
   - Web viewer load time < 1 second

3. **Adoption**
   - 0 data migration required (backwards compatible)
   - Existing workflows continue unchanged
   - New features opt-in, not forced

---

## Open Questions

1. **claude-mem Installation**: Should we fork the claude-mem repo for customizations or use adapter pattern?
2. **Checkpoint Retention**: How long to keep cross-references for deleted observations?
3. **Privacy**: Should claude-mem observations be encrypted before storage?
4. **Multi-tenancy**: How to handle multiple Claude Code instances accessing same claude-mem DB?

---

## Appendix: File Changes Summary

| File | Change | Type |
|------|--------|------|
| `P:/__csf/src/cli/nip/search.py` | Add BACKEND_CLAUDE_MEM constant and backend class | Modify |
| `P:/packages/checkpoint/src/checkpoint/hooks/__lib/checkpoint_store.py` | Add `related_observations` field to metadata | Modify |
| `P:/packages/checkpoint/src/checkpoint/hooks/__lib/observer_scanner.py` | NEW: Scan claude-mem for related observations | Create |
| `P:/.claude/hooks/PostTool_checkpoint_linker.py` | NEW: Hook to link tool results to checkpoints | Create |
| `P:/__csf/docs/design/claude-mem-web-enhancements.md` | NEW: UI component specs | Create |

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2025-02-11 | 1.0 | Initial design document |

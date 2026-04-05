# Requirements Analysis: CKS-First /discover Consolidation

**TSK-ID**: TSK-251224-CKS-Discover-05b7aa
**Step**: 2 - Requirements Analysis
**Created**: 2025-12-24 02:35

## Functional Requirements

### FR-1: Single Knowledge System
The `/discover` command must use CKS as the single unified knowledge system for all semantic search queries.

### FR-2: Patterns Ingestion
All patterns from `.data/knowledge/patterns.jsonl` must be ingested into CKS KNOWLEDGE graph before deprecation.

### FR-3: Standards Included
Coding standards (Python 2025, TypeScript 2025) must be included in `/discover` search results.

### FR-4: Chat History Access
Historical chat context must remain accessible through CKS memory system.

### FR-5: Cross-Graph Relationships
Results should leverage CKS's cross-graph relationship capabilities when relevant.

## Non-Functional Requirements

### NFR-1: Query Performance
- Target: <200ms for semantic search queries
- Acceptable trade-off: 130ms slower than RAG (13-22ms → 50-200ms)
- Rationale: 130ms difference is trivial for development workflow

### NFR-2: Backward Compatibility
- Existing `/discover` functionality must be preserved
- No breaking changes to command interface
- Tool availability flags must work

### NFR-3: Data Integrity
- No data loss during migration
- All 22 patterns from patterns.jsonl preserved
- All 8,760 chat history entries preserved

### NFR-4: Maintainability
- Single system easier to maintain than 3 separate systems
- Clear data ownership (CKS is authoritative)
- No sync issues between multiple systems

## Data Migration Requirements

### DM-1: Pattern Ingestion
- Source: `.data/knowledge/patterns.jsonl` (22 patterns)
- Destination: CKS KNOWLEDGE graph
- Method: `cks.ingest_pattern()` for each pattern
- Validation: Count matches (22 ingested = 22 in source)

### DM-2: Chat History Migration
- Source: `~/.claude/history.jsonl` (8,760 entries)
- Destination: CKS memory entries
- Method: `cks.ingest_memory()` for relevant entries
- Validation: Sample verification of migrated content

### DM-3: Standards Verification
- Source: Already ingested via `ingest_coding_standards.py`
- Verification: Query for "Python Standard" and "TypeScript Standard"
- Expected: 10 Python standards + 10 TypeScript standards

## Interface Requirements

### IR-1: explorer_spec.py Changes
- Replace RAG import with CKS import
- Update `semantic_search()` to use `cks.search_semantic()`
- Keep `hyper_graph_query()` for advanced use
- Maintain graceful fallbacks

### IR-2: RAG Deprecation
- Keep `build_production_compressed_rag.py` as export tool
- Document that patterns.jsonl is deprecated
- Update documentation to reference CKS instead

### IR-3: Documentation Updates
- Update `/discover` command documentation
- Update CKS documentation for /discover integration
- Create migration guide for any custom integrations

## Success Criteria

### SC-1: Functional
- [ ] `/discover` queries return results from CKS
- [ ] Standards appear in search results
- [ ] All 22 patterns accessible
- [ ] Cross-graph relationships available

### SC-2: Non-Functional
- [ ] Query performance <200ms
- [ ] No data loss
- [ ] All existing tools still work
- [ ] No breaking changes

### SC-3: Maintainability
- [ ] Single system documentation
- [ ] Clear data flow diagram
- [ ] Migration guide complete
- [ ] Legacy systems deprecated

## Constraints

### C-1: Time
- User requested immediate implementation ("do all of it")
- Full CWO12 workflow execution

### C-2: Scope
- Focus on /discover command only
- Don't modify CKS core functionality
- Don't rewrite RAG from scratch

### C-3: Quality
- Maintain constitutional compliance
- No data loss
- Preserve existing functionality

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Query speed degradation | High | Low | Accept 50-200ms as sufficient |
| Missing patterns during migration | Medium | High | Verify count before deprecation |
| Breaking existing workflows | Low | High | Keep all tools, just change backend |
| Data loss during migration | Low | Critical | Backup before migration |

## Dependencies

### D-1: CKS Components
- `src/cks/unified.py` - CKS API
- `src/cks/core/multi_graph_engine.py` - Hyper-graph
- `src/cks/commands/ingest_coding_standards.py` - Standards ingestion

### D-2: Current /discover
- `src/modules/discover/explorer_spec.py` - Main implementation
- `src/modules/discover/discover_database.py` - Findings storage

### D-3: Data Sources
- `.data/knowledge/patterns.jsonl` - 22 patterns
- `~/.claude/history.jsonl` - Chat history
- CKS database - Standards already ingested

## Acceptance Criteria

1. **Query**: `/discover "type safety patterns"` returns results from CKS
2. **Verification**: Query includes both patterns and standards
3. **Performance**: Query completes in <200ms
4. **Integrity**: All 22 patterns accessible
5. **Documentation**: Updated to reflect CKS-first architecture

# Specification: Add Coding Standards to CKS + Use Discover for Standards Analysis

**TSK:** TSK-231223-CKSStandards-1258
**Created:** 2025-12-23 12:58 UTC
**Status:** Draft

## Overview

Index Python and TypeScript coding standards into the Cognitive Knowledge System (CKS) to make them discoverable through the `/discover` command's enhanced pre-query functionality. This will enable intelligent context-aware codebase analysis and standards compliance checking.

### Problem Statement

Currently:
- Coding standards exist in `P:/.claude/commands/` but are NOT indexed in CKS
- The `/discover` command cannot retrieve coding standards context during exploration
- Manual compliance scanning (`test_coding_standards_compliance.py`) bypasses CKS
- Previous attempt to use `/discover` for standards analysis failed due to missing CKS data

### Solution

1. **Ingest Phase**: Parse and ingest coding standards from `.claude/commands/` into CKS knowledge base
2. **Discovery Phase**: Use `/discover` with CKS enhanced pre-query for standards analysis
3. **Integration Phase**: Ensure discover's venv/cache filtering (from other LLM) works with standards queries

## Requirements

### Functional Requirements

#### FR-1: Coding Standards Ingestion
- **FR-1.1**: Parse Python coding standards from `code_python_2025_quick_reference.md` (10 mandatory standards)
- **FR-1.2**: Parse TypeScript standards from `code_ts_2025_quick_reference.md` (10 mandatory standards)
- **FR-1.3**: Extract anti-patterns from both files (e.g., bare except, os.getenv, any type)
- **FR-1.4**: Create CKS entries with proper metadata (language, category, focus_area, tags)
- **FR-1.5**: Store code examples and configuration samples with each standard

#### FR-2: CKS Query Integration
- **FR-2.1**: Standards discoverable via `/discover` query
- **FR-2.2**: CKS pre-query returns relevant standards with confidence scores
- **FR-2.3**: Filter by language, category, and focus_area
- **FR-2.4**: Entity relationships link related standards (e.g., type hints → mypy)

#### FR-3: Standards Compliance Analysis
- **FR-3.1**: Query for specific violations (e.g., "bare except clauses")
- **FR-3.2**: Discover returns standards context + relevant code locations
- **FR-3.3**: Rich formatting with confidence bars and performance metrics
- **FR-3.4**: Exclude venv/cache directories (use `filter_venv_and_cache` from other LLM)

### Non-Functional Requirements

#### NFR-1: Performance
- Ingestion completes in <30 seconds for all standards
- CKS query response time <10ms (FTS5) or <50ms (LIKE fallback)
- Discover with CKS pre-query adds <100ms overhead

#### NFR-2: Data Quality
- Each standard tagged with: language, category, tools, focus_area
- Code examples included for each standard
- Cross-references between related standards

#### NFR-3: Compatibility
- Works with existing CKS schema (entries, entities, relationships)
- Compatible with `/discover` enhanced pre-query (FTS5, graph traversal, session)
- Respects `filter_venv_and_cache` filtering in explorer_spec.py

## User Stories

### US-1: Developer Queries Standards
**As a** developer
**I want** to query coding standards from CKS
**So that** I can understand best practices while exploring code

**Acceptance Criteria:**
- [ ] `/discover "python linting standards"` returns Python Standard #2 (Use ruff)
- [ ] Result includes standard description, examples, and configuration
- [ ] Confidence score displayed (e.g., `[█████░░░] 0.80`)
- [ ] Query time <100ms

### US-2: Standards Compliance Analysis
**As a** developer
**I want** to find code that violates coding standards
**So that** I can fix compliance issues

**Acceptance Criteria:**
- [ ] `/discover "bare except clauses"` finds violations with context
- [ ] CKS returns standard + explanation of why it's problematic
- [ ] Results exclude venv/cache directories
- [ ] Related standards suggested (e.g., exception handling patterns)

### US-3: Knowledge Base Management
**As a** maintainer
**I want** to easily update coding standards in CKS
**So that** the knowledge base stays current

**Acceptance Criteria:**
- [ ] CLI command to ingest all standards: `/cks standards ingest --all`
- [ ] CLI command to query standards: `/cks standards query "async"`
- [ ] CLI command to show statistics: `/cks standards stats`
- [ ] Incremental updates supported (update specific standard)

## Scope

### In Scope

- **Files to ingest:**
  - `P:/.claude/commands/code_python_2025_quick_reference.md` (Python standards)
  - `P:/.claude/commands/code_ts_2025_quick_reference.md` (TypeScript standards)
  - Optional: Detailed guides (code_python_2025_guide.md, code_ts_2025_guide.md)

- **CKS integration:**
  - Create ingestion script in `P:\__csf.nip/src/cks/commands/ingest_coding_standards.py`
  - Use CKS storage API from `cks.core.storage_manager.StorageManager`
  - Follow entry schema: type, title, content, metadata

- **Discover integration:**
  - Test `/discover` with standards queries
  - Verify CKS enhanced pre-query returns standards
  - Use `filter_venv_and_cache` to exclude non-source code

### Out of Scope

- **Full documentation ingestion:** Detailed guides are lower priority
- **Automatic violation fixing:** Only detection, not remediation
- **CI/CD integration:** Not building GitHub Actions workflows
- **Other language standards:** Only Python and TypeScript in scope

## Success Criteria

- **20+ Python standards/anti-patterns** indexed in CKS
- **20+ TypeScript standards/anti-patterns** indexed in CKS
- **Query "python coding standards"** returns relevant entries
- **Query "ruff linting"** returns Python Standard #2
- **Query "bare except clauses"** finds actual violations in codebase
- **All queries exclude venv/cache** directories
- **CKS context displayed** with confidence scores in `/discover` output

## Technical Considerations

### CKS Entry Schema
```python
{
    "type": "coding_standard",
    "title": "Standard Name (e.g., 'Use ruff for linting')",
    "content": "Full description with examples...",
    "metadata": {
        "language": "python" | "typescript" | "common",
        "category": "mandatory" | "recommended" | "avoid",
        "standard_number": 1-10,
        "tools": ["ruff", "mypy", ...],
        "focus_area": "linting" | "packaging" | "async" | ...,
        "source_file": "code_python_2025_quick_reference.md",
        "tags": ["python", "2025-standards", "mandatory"]
    }
}
```

### Chunking Strategy
- Each of 10 mandatory standards → separate CKS entry
- Each anti-pattern → separate "avoid" type entry
- Include code examples and configuration samples
- Tag with language, category, tools, focus_area

### Venv/Cache Filtering
- Use `filter_venv_and_cache()` function from explorer_spec.py (lines 124-152)
- Skip patterns: `venv`, `env`, `.venv`, `__pycache__`, `node_modules`, `.git`
- Also skip: `site-packages`, `dist`, `build`, `.eggs`, `*.egg-info`

### File Locations

**Coding Standards Source:**
- `P:/.claude/commands/code_python_2025_quick_reference.md`
- `P:/.claude/commands/code_ts_2025_quick_reference.md`

**CKS Storage:**
- Database: `P:/.cks/storage/cks.db`
- Schema: entries, entities, relationships tables

**Ingestion Script:**
- `P:\__csf.nip/src/cks/commands/ingest_coding_standards.py`

**Discover Module:**
- `P:\__csf.nip/src/modules/discover/explorer_spec.py` (has venv filter)

## Open Questions

### Q1: Detailed Guides Ingestion?
**Question:** Should we ingest the detailed guides (code_python_2025_guide.md = 1,012 lines)?

**Options:**
1. **Yes, chunk by chapter:** More comprehensive but verbose
2. **No, quick reference only:** Concise, focus on 10 mandatory standards
3. **Hybrid:** Quick reference now, detailed guides as separate task

**Recommendation:** Option 3 - Start with quick reference, add detailed guides later if needed.

### Q2: CKS Entry Type?
**Question:** What `type` value should coding standards use in CKS?

**Options:**
1. `"coding_standard"` - New type, needs schema update?
2. `"pattern"` - Reuse existing type
3. `"standard"` - Simpler name

**Recommendation:** Use `"coding_standard"` - clear and specific. Check if CKS schema supports custom types.

### Q3: Anti-patterns as Separate Entries?
**Question:** Should anti-patterns (e.g., "bare except clauses") be separate CKS entries?

**Options:**
1. **Yes, separate entries:** Easier to query for violations
2. **No, embedded in standards:** Linked via metadata
3. **Hybrid:** Separate entries with relationship to parent standard

**Recommendation:** Option 1 - Separate entries make queries like "find bare except violations" more intuitive.

### Q4: Test Data?
**Question:** Do we need test data to verify CKS ingestion works?

**Options:**
1. **Yes, use existing violations:** Query known issues (e.g., os.getenv in codebase)
2. **No, manual verification:** Search and inspect results manually
3. **Create synthetic test:** Add temporary standard, query for it, remove it

**Recommendation:** Option 1 - Use the 6,007 violations found by previous scan as validation data.

## Dependencies

### Internal Dependencies
- **CKS Storage:** `P:\__csf.nip/src/cks/core/storage_manager.py`
- **Direct Ingestion:** `P:\__csf.nip/src/cks/integration/commands/direct_knowledge_ingestion.py`
- **Discover Module:** `P:\__csf.nip/src/modules/discover/explorer_spec.py`
- **TaskMaster:** `P:\__csf.nip/scripts/taskmaster.db`

### External Dependencies
- SQLite 3 (for CKS storage)
- Python 3.11+ (standard in .csf.nip)

## Implementation Phases

1. **Phase 1:** Create CKS ingestion script
2. **Phase 2:** Ingest Python standards (10 mandatory + anti-patterns)
3. **Phase 3:** Ingest TypeScript standards (10 mandatory + anti-patterns)
4. **Phase 4:** Create CLI wrapper for standards management
5. **Phase 5:** Test `/discover` with standards queries
6. **Phase 6:** Validate with actual codebase violations

## Risk Mitigation

### Risk 1: CKS Schema Constraints
**Mitigation:** Check CKS schema before creating ingestion script. Use compatible field types.

### Risk 2: Discover Still Broken
**Mitigation:** Other LLM fixed imports but noted "empty exploration results" issue. Have fallback manual scanner ready.

### Risk 3: Performance Issues
**Mitigation:** Start with quick reference (smaller files). Test query times before ingesting detailed guides.

## Acceptance

**Definition of Done:**
- [ ] specify.md reviewed and approved
- [ ] All open questions resolved
- [ ] Implementation phases defined
- [ ] Risks identified with mitigations
- [ ] TaskMaster updated with Step 1 complete

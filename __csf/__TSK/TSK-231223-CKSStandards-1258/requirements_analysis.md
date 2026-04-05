# Requirements Analysis: Coding Standards CKS Integration

**TSK:** TSK-231223-CKSStandards-1258
**Step:** CWO14 Step 2 - Requirement Analysis (/ask)
**Created:** 2025-12-23 13:15 UTC
**Status:** Draft

---

## Executive Summary

This analysis examines the requirements for ingesting Python and TypeScript coding standards into the Cognitive Knowledge System (CKS) and enabling `/discover` command integration for standards compliance analysis.

**Key Findings:**
- **Source Material**: 2 quick reference files containing 20 mandatory standards (10 Python + 10 TypeScript)
- **Storage System**: CKS uses SQLite with knowledge_nodes table (type, content, metadata JSON)
- **Ingestion Pattern**: Direct CKS ingestion script exists (`direct_knowledge_ingestion.py`)
- **Integration Point**: `/discover` command has CKS enhanced pre-query (FTS5 + graph traversal)

**Risk Assessment:**
- **Low Risk**: CKS schema supports custom types, storage manager has batch operations
- **Medium Risk**: Need to parse markdown structure into individual standards
- **Open Question**: Whether to use `type: "coding_standard"` or reuse existing types

---

## Requirement Decomposition

### FR-1: Coding Standards Ingestion

**Breakdown:**

| Sub-Requirement | Description | Priority | Complexity |
|----------------|-------------|----------|------------|
| FR-1.1 | Parse Python standards from quick reference | High | Medium |
| FR-1.2 | Parse TypeScript standards from quick reference | High | Medium |
| FR-1.3 | Extract anti-patterns from both files | Medium | Low |
| FR-1.4 | Create CKS entries with metadata | High | Low |
| FR-1.5 | Store code examples with each standard | Medium | Low |

**Technical Analysis:**

**Source Structure (Python):**
```markdown
## The 10 Mandatory Standards
| # | Standard | DO THIS | NOT THIS | Why |
| 1 | Packaging | uv sync | requirements.txt | 100x faster |
...
## Code Patterns: REFUSE These
- Circular imports
- Classes > 300 lines
...
```

**Parsing Strategy:**
1. Parse markdown table for 10 mandatory standards
2. Parse "REFUSE These" section for anti-patterns
3. Extract: standard_number, title, do_this, not_this, rationale
4. Generate CKS entry with proper metadata

**CKS Entry Schema:**
```python
{
    "id": "standard_python_001",
    "type": "coding_standard",  # NEW TYPE
    "content": "Full standard description with examples...",
    "metadata": {
        "language": "python",
        "category": "mandatory",  # mandatory | recommended | avoid
        "standard_number": 1,
        "tools": ["uv", "pyproject.toml"],
        "focus_area": "packaging",
        "source_file": "code_python_2025_quick_reference.md",
        "tags": ["python", "2025-standards", "mandatory", "packaging"]
    }
}
```

### FR-2: CKS Query Integration

**Breakdown:**

| Sub-Requirement | Description | Priority | Complexity |
|----------------|-------------|----------|------------|
| FR-2.1 | Standards discoverable via `/discover` | High | Low |
| FR-2.2 | CKS pre-query returns relevant standards | High | Medium |
| FR-2.3 | Filter by language, category, focus_area | Medium | Low |
| FR-2.4 | Entity relationships link related standards | Medium | Medium |

**Technical Analysis:**

**CKS Enhanced Pre-Query Architecture:**
- FTS5 full-text search on knowledge_nodes.content
- Graph traversal for entity relationships
- Session context tracking
- Average query time: 2.1ms

**Query Examples:**
```python
# Query for specific standard
"python linting standard"
→ Returns: Python Standard #2 (Use ruff)

# Query for anti-patterns
"bare except clauses"
→ Returns: Anti-pattern entry with explanation

# Query by focus area
"async best practices"
→ Returns: Python Standard #5, TypeScript async patterns
```

**Metadata Filtering:**
```sql
-- Filter by language
WHERE metadata LIKE '%"language": "python"%'

-- Filter by category
WHERE metadata LIKE '%"category": "mandatory"%'

-- Filter by focus_area
WHERE metadata LIKE '%"focus_area": "async"%'
```

### FR-3: Standards Compliance Analysis

**Breakdown:**

| Sub-Requirement | Description | Priority | Complexity |
|----------------|-------------|----------|------------|
| FR-3.1 | Query for specific violations | High | Low |
| FR-3.2 | Discover returns standards + code locations | High | High |
| FR-3.3 | Rich formatting with confidence scores | Medium | Medium |
| FR-3.4 | Exclude venv/cache directories | High | Low |

**Technical Analysis:**

**Venv/Cache Filter (from other LLM):**
```python
skip_patterns = [
    'venv', 'env', '.venv', '__pycache__',
    'node_modules', '.git', '.pytest_cache',
    'site-packages', 'dist', 'build',
    '.eggs', '*.egg-info',
    '/Lib/site-packages/', '/lib/python', '/Scripts/'
]
```

**Results:**
- 61% file reduction (33,912 → 13,068 Python files)
- Applied to 9 locations in explorer_spec.py

**Integration Pattern:**
```python
# User query: "bare except clauses"
# 1. CKS pre-query returns standard
standard = cks.query("bare except clauses")
# → Returns: Anti-pattern entry with explanation

# 2. Discover searches codebase with filter
violations = discover.search("except:", filter_func=filter_venv_and_cache)

# 3. Display results with context
display_results(standard, violations, confidence_score)
```

---

## Non-Functional Requirements Analysis

### NFR-1: Performance

| Metric | Target | Current CKS Performance | Assessment |
|--------|--------|-------------------------|------------|
| Ingestion time | <30 seconds | TBD | Needs measurement |
| CKS query time | <10ms (FTS5) | 2.1ms average | ✅ Meets requirement |
| Discover overhead | <100ms | TBD | Needs measurement |

**Analysis:**
- CKS query performance is excellent (2.1ms vs 10ms target)
- Ingestion time depends on file parsing and batch insert operations
- Discover overhead needs measurement after implementation

### NFR-2: Data Quality

| Requirement | Implementation Strategy |
|-------------|------------------------|
| Language tags | Auto-tag: `python`, `typescript`, `common` |
| Category tags | Auto-categorize: `mandatory`, `avoid`, `recommended` |
| Code examples | Include from source markdown |
| Cross-references | Create entity relationships between related standards |

**Analysis:**
- Source files are well-structured (markdown tables)
- Automatic extraction of metadata is feasible
- Code examples embedded in source files

### NFR-3: Compatibility

| Component | Compatibility Status | Notes |
|-----------|---------------------|-------|
| CKS schema | ✅ Compatible | Uses existing knowledge_nodes table |
| CKS storage API | ✅ Compatible | Direct ingestion pattern exists |
| Discover pre-query | ✅ Compatible | Enhanced pre-query supports FTS5 |
| Venv/filter | ✅ Compatible | Function already implemented |

---

## User Stories Analysis

### US-1: Developer Queries Standards

**Acceptance Criteria Mapping:**

| Criterion | Implementation Strategy |
|-----------|------------------------|
| Query returns Python Standard #2 | FTS5 search on "ruff linting" |
| Includes description + examples | Content field contains full markdown |
| Confidence score displayed | CKS returns relevance score |
| Query time <100ms | CKS query 2.1ms + discover overhead |

**Estimated Effort:** 2 hours

### US-2: Standards Compliance Analysis

**Acceptance Criteria Mapping:**

| Criterion | Implementation Strategy |
|-----------|------------------------|
| Finds violations with context | Discover search + CKS standard lookup |
| Returns explanation | CKS content field has rationale |
| Excludes venv/cache | Use filter_venv_and_cache() function |
| Suggests related standards | Entity relationships graph traversal |

**Estimated Effort:** 4 hours

### US-3: Knowledge Base Management

**Acceptance Criteria Mapping:**

| Criterion | Implementation Strategy |
|-----------|------------------------|
| CLI ingest command | `/cks standards ingest --all` |
| CLI query command | `/cks standards query "async"` |
| CLI stats command | `/cks standards stats` |
| Incremental updates | Update by standard_id or re-run ingest |

**Estimated Effort:** 3 hours

---

## Technical Architecture Analysis

### CKS Storage Schema

**Existing Schema (knowledge_nodes):**
```sql
CREATE TABLE knowledge_nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,          -- "coding_standard"
    content TEXT NOT NULL,       -- JSON with title, description, examples
    metadata TEXT,               -- JSON with language, category, tags
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**Indexes:**
```sql
CREATE INDEX idx_knowledge_type ON knowledge_nodes(type)
```

**FTS5 Search:**
- Full-text search on content field
- BM25 ranking for relevance scoring
- Sub-10ms query performance

### Ingestion Architecture

**Component: ingest_coding_standards.py**

```
┌─────────────────────────────────────────────────────────┐
│           Coding Standards Ingestion Pipeline           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  Parse Markdown Files                │
        │  - code_python_2025_quick_reference  │
        │  - code_ts_2025_quick_reference      │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  Extract Standards                   │
        │  - 10 mandatory per language         │
        │  - Anti-patterns                     │
        │  - Code examples                     │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  Generate CKS Entries                │
        │  - Unique IDs                        │
        │  - Metadata (language, category)     │
        │  - Tags (focus_area, tools)          │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  Batch Insert to CKS                 │
        │  - Use StorageManager                │
        │  - Create entity relationships       │
        └──────────────────────────────────────┘
```

### Discover Integration Architecture

**Enhanced Pre-Query Flow:**

```
┌─────────────────────────────────────────────────────────┐
│              /discover Command Flow                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  User Query: "bare except clauses"   │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  CKS Enhanced Pre-Query              │
        │  - FTS5 search (2.1ms)               │
        │  - Graph traversal                   │
        │  - Session context                   │
        └──────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
        ┌──────────────┐   ┌──────────────────┐
        │ CKS Results  │   │ Codebase Search  │
        │ - Standard   │   │ - File globbing  │
        │ - Explanation│   │ - Venv filter    │
        └──────────────┘   └──────────────────┘
                    │               │
                    └───────┬───────┘
                            ▼
        ┌──────────────────────────────────────┐
        │  Merge and Display Results           │
        │  - Standard context                  │
        │  - Violation locations               │
        │  - Confidence scores                 │
        └──────────────────────────────────────┘
```

---

## Implementation Complexity Analysis

### Phase 1: CKS Ingestion Script

**Complexity:** Medium

**Tasks:**
1. Create `ingest_coding_standards.py` (200 lines)
2. Parse markdown tables (regex/string parsing)
3. Extract anti-patterns (line-by-line parsing)
4. Generate CKS entries with metadata
5. Batch insert using StorageManager

**Estimated Effort:** 4 hours

**Dependencies:**
- `P:\__csf.nip\src\cks\core\storage_manager.py`
- `P:\.claude\commands\code_python_2025_quick_reference.md`
- `P:\.claude\commands\code_ts_2025_quick_reference.md`

### Phase 2: CLI Wrapper

**Complexity:** Low

**Tasks:**
1. Create `/cks standards` subcommand
2. Implement `ingest --all`, `query`, `stats` actions
3. Add help text and examples

**Estimated Effort:** 2 hours

**Dependencies:**
- Existing CKS CLI structure

### Phase 3: Testing /discover Integration

**Complexity:** Medium

**Tasks:**
1. Run `/discover` with standards queries
2. Verify CKS pre-query returns standards
3. Test venv/cache filtering
4. Validate confidence scores

**Estimated Effort:** 2 hours

**Dependencies:**
- `P:\__csf.nip\src\modules\discover\explorer_spec.py`

---

## Risk Assessment

### Risk 1: CKS Schema Constraints

**Probability:** Low
**Impact:** Medium
**Mitigation:**

- ✅ Schema supports custom `type` values
- ✅ Metadata field is flexible JSON
- ✅ Existing entries use various types (implementation, pattern, etc.)

**Action:** Use `type: "coding_standard"` - no schema changes needed.

### Risk 2: Discover Still Broken

**Probability:** Medium
**Impact:** High
**Mitigation:**

- ⚠️ Other LLM noted "empty exploration results" issue
- ✅ Venv/filter function already implemented
- 🔄 Have fallback manual scanner ready (`test_coding_standards_compliance.py`)

**Action:** Test discover early in Phase 3. If broken, use manual scanner with CKS lookup.

### Risk 3: Performance Issues

**Probability:** Low
**Impact:** Low
**Mitigation:**

- ✅ CKS query performance is excellent (2.1ms)
- ✅ Quick reference files are small (<200 lines each)
- ✅ Batch insertion minimizes database round-trips

**Action:** Start with quick reference. Test query times before ingesting detailed guides.

---

## Data Model

### CKS Entry Structure

**Mandatory Standards:**
```python
{
    "id": "standard_python_001",
    "type": "coding_standard",
    "title": "Use uv for dependency management",
    "content": """
    # Python Standard #1: Use uv for dependency management

    **DO THIS:** `uv sync` from `pyproject.toml` + dependency groups
    **NOT THIS:** `pip install -r requirements.txt`

    **Why:** 100x faster, reproducible, organized deps

    **Migration Guide:**
    1. Create pyproject.toml
    2. Convert requirements.txt to dependency groups
    3. Run `uv sync`
    """,
    "metadata": {
        "language": "python",
        "category": "mandatory",
        "standard_number": 1,
        "tools": ["uv", "pyproject.toml"],
        "focus_area": "packaging",
        "source_file": "code_python_2025_quick_reference.md",
        "tags": ["python", "2025-standards", "mandatory", "packaging", "dependency-management"]
    }
}
```

**Anti-Patterns:**
```python
{
    "id": "antipattern_python_bare_except",
    "type": "coding_standard",
    "title": "Anti-pattern: Bare except clauses",
    "content": """
    # Anti-Pattern: Bare Except Clauses (Silent Exception Handling)

    **PROBLEM:**
    ```python
    try:
        risky_operation()
    except:  # ❌ Catches everything, hides errors
        pass
    ```

    **SOLUTION:**
    ```python
    try:
        risky_operation()
    except SpecificError as e:  # ✅ Catch specific exceptions
        logger.error(f"Operation failed: {e}")
    ```

    **Why Bare Except is Dangerous:**
    - Catches system exceptions (KeyboardInterrupt, SystemExit)
    - Hides errors, making debugging impossible
    - Violates "fail fast" principle
    """,
    "metadata": {
        "language": "python",
        "category": "avoid",
        "focus_area": "exception-handling",
        "source_file": "code_python_2025_quick_reference.md",
        "tags": ["python", "anti-pattern", "exception-handling", "debugging"]
    }
}
```

### Entity Relationships

**Relationship Types:**
- `related_to` - Similar standards
- `alternative_to` - Different approaches to same problem
- `requires` - Prerequisite standard
- `violated_by` - Anti-pattern violates this standard

**Example Relationships:**
```
Python Standard #2 (Use ruff)
  ├── related_to → Python Standard #3 (Use mypy)
  ├── alternative_to → Legacy linting (black + isort + flake8)
  └── violated_by → Anti-pattern: Legacy linting configs

Python Standard #5 (asyncio.TaskGroup)
  ├── requires → Python Standard #9 (Python 3.11+)
  └── related_to → TypeScript Standard #7 (Zod validation startup)
```

---

## Success Criteria Analysis

| Criterion | Verification Method | Target |
|-----------|-------------------|--------|
| 20+ Python standards/anti-patterns indexed | Query CKS for `type: "coding_standard" AND language: "python"` | ≥20 entries |
| 20+ TypeScript standards/anti-patterns indexed | Query CKS for `type: "coding_standard" AND language: "typescript"` | ≥20 entries |
| Query "python coding standards" returns entries | `/discover "python coding standards"` | Relevant results |
| Query "ruff linting" returns Standard #2 | `/discover "ruff linting"` | Python Standard #2 |
| Query "bare except clauses" finds violations | `/discover "bare except clauses"` | Violations + standard |
| All queries exclude venv/cache | Inspect search results | No venv/cache paths |
| CKS context displayed with confidence | Inspect `/discover` output | Confidence bars visible |

---

## Open Questions Resolution

### Q1: Detailed Guides Ingestion?

**Recommendation:** Option 3 - Start with quick reference, add detailed guides later.

**Rationale:**
- Quick reference has 10 mandatory standards per language (core content)
- Detailed guides are 1,012+ lines (lower priority)
- Can ingest detailed guides as separate task if needed

### Q2: CKS Entry Type?

**Recommendation:** Use `"coding_standard"` - clear and specific.

**Rationale:**
- CKS schema supports custom types
- Existing entries use various types (implementation, pattern, tag)
- `"coding_standard"` is self-documenting

### Q3: Anti-patterns as Separate Entries?

**Recommendation:** Option 1 - Separate entries make queries more intuitive.

**Rationale:**
- Query: "find bare except violations" → Returns anti-pattern entry directly
- Entity relationships link anti-patterns to parent standards
- Easier to maintain (update anti-pattern without touching standard)

### Q4: Test Data?

**Recommendation:** Option 1 - Use existing violations from previous scan.

**Rationale:**
- 6,007 violations found by `test_coding_standards_compliance.py`
- Real validation data in actual codebase
- No need to create synthetic test cases

---

## Dependencies Analysis

### Internal Dependencies

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| CKS Storage Manager | `P:\__csf.nip\src\cks\core\storage_manager.py` | Database operations | ✅ Available |
| Direct Ingestion | `P:\__csf.nip\src\cks\integration\commands\direct_knowledge_ingestion.py` | Ingestion pattern | ✅ Available |
| Discover Module | `P:\__csf.nip\src\modules\discover\explorer_spec.py` | CKS pre-query | ✅ Available |
| Venv Filter | `P:\__csf.nip\src\modules\discover\explorer_spec.py:124-152` | File filtering | ✅ Available |

### External Dependencies

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| SQLite 3 | Built-in | Database storage | ✅ Available |
| Python | 3.11+ | Runtime | ✅ Available |

---

## Implementation Estimate

**Total Estimated Effort:** 8-12 hours

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: CKS Ingestion Script | 4 hours | High |
| Phase 2: CLI Wrapper | 2 hours | Medium |
| Phase 3: Testing /discover Integration | 2 hours | High |
| Phase 4: Documentation & Cleanup | 2 hours | Low |

**Critical Path:** Phase 1 → Phase 3 (Phase 2 can be done in parallel)

---

## Conclusion

**Requirements Status:** ✅ Complete and Well-Defined

**Key Insights:**
1. CKS schema supports custom types - no database changes needed
2. Direct ingestion pattern exists - can adapt for coding standards
3. Venv/cache filter already implemented - reduces codebase scanning by 61%
4. CKS query performance is excellent (2.1ms) - no performance concerns

**Recommended Approach:**
1. Create ingestion script using StorageManager API
2. Parse quick reference files (small, well-structured)
3. Use `type: "coding_standard"` for entries
4. Create entity relationships between related standards
5. Test `/discover` integration early to catch any issues

**Next Step:** Proceed to Step 3 (Research Intelligence) to investigate any remaining unknowns and validate the ingestion approach.

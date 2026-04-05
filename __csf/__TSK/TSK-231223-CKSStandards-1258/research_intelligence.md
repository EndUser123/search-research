# Research Intelligence: CKS Standards Integration

**TSK:** TSK-231223-CKSStandards-1258
**Step:** CWO14 Step 3 - Research Intelligence (/research)
**Created:** 2025-12-23 13:30 UTC
**Status:** Complete

---

## Executive Summary

Research conducted across CKS codebase to understand storage patterns, CLI architecture, and integration points for coding standards ingestion.

**Key Findings:**
- **Unified CKS Interface** (`unified.py`) supports custom entry types
- **Valid Entry Types** include: memory, pattern, code, knowledge, correction, decision, commitment, insight, learning
- **Multiple Ingestion Patterns** exist in `src/cks/integration/commands/`
- **CKS CLI** (`cks_cli.py`) provides command-line interface foundation

---

## CKS Architecture Research

### Entry Schema (unified.py:191-217)

**Core Table Structure:**
```sql
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,          -- Entry type (pattern, knowledge, etc.)
    title TEXT,                  -- Title/heading
    content TEXT NOT NULL,       -- Main content
    metadata TEXT,               -- JSON metadata
    embedding BLOB,              -- Semantic search embedding
    source_chunk TEXT,           -- Source reference
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Valid Entry Types:**
```python
VALID_ENTRY_TYPES = [
    "memory",        # Generic memories
    "pattern",       # Repeating patterns
    "code",          # Code snippets
    "knowledge",     # Factual knowledge
    "correction",    # Mistakes and fixes
    "decision",      # Choices made and why
    "commitment",    # Promises/resolutions
    "insight",       # Realizations and aha moments
    "learning",      # Lessons learned
]
```

**Key Insight:** `coding_standard` is NOT in the valid types list. Two options:
1. Use `type: "pattern"` (best fit for reusable standards)
2. Use `type: "knowledge"` (factual information about standards)

**Recommendation:** Use `type: "pattern"` since coding standards are repeatable best practices.

### Ingestion Methods (unified.py)

**Primary Ingestion Method:**
```python
def ingest_pattern(
    self,
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Ingest a pattern (repeating best practice)."""
```

**Usage:**
```python
cks = CKS()
entry_id = cks.ingest_pattern(
    title="Use ruff for linting",
    content="Full description with examples...",
    metadata={
        "language": "python",
        "category": "mandatory",
        "standard_number": 2,
        "focus_area": "linting",
        "tools": ["ruff"]
    },
    tags=["python", "2025-standards", "mandatory", "linting"]
)
```

### Search Methods (unified.py)

**Text Search (FTS5):**
```python
def search(
    self,
    query: str,
    entry_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search entries using FTS5 full-text search."""
```

**Semantic Search:**
```python
def search_semantic(
    self,
    query: str,
    entry_type: Optional[str] = None,
    threshold: float = 0.50,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search entries using semantic similarity."""
```

---

## Existing Ingestion Patterns

### Pattern 1: Direct Knowledge Ingestion

**File:** `src/cks/integration/commands/direct_knowledge_ingestion.py`

**Approach:**
- Direct SQLite access (bypasses CKS class)
- Custom schema (knowledge_nodes, knowledge_edges, vector_nodes)
- Batch insertion with relationships

**Code Sample:**
```python
def ingest_knowledge(
    self,
    title: str,
    content: str,
    category: str,
    knowledge_type: str = "implementation",
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """Ingest knowledge entry into CKS."""
    cursor = self.conn.cursor()
    entry_id = self.generate_entry_id(title, category)

    # Insert knowledge node
    cursor.execute("""
        INSERT INTO knowledge_nodes (id, type, content, metadata)
        VALUES (?, ?, ?, ?)
    """, (
        entry_id,
        knowledge_type,
        structured_content,
        json.dumps(entry_metadata)
    ))

    # Create relationships
    self._create_tag_relationships(cursor, entry_id, tags or [])
```

**Pros:**
- Fast batch operations
- Custom schema control
- Relationship creation built-in

**Cons:**
- Uses separate database from unified CKS (`data/cks_hypergraph/cks_hypergraph.db`)
- Doesn't use unified CKS interface
- More maintenance burden

### Pattern 2: NSE Task Awareness Ingestion

**File:** `src/cks/integration/commands/nse_task_awareness_knowledge_ingestion.py`

**Approach:**
- Uses unified CKS class (`from src.cks.unified import CKS`)
- Simple `ingest_pattern()` calls
- Clean, maintainable code

**Code Sample:**
```python
from src.cks.unified import CKS

cks = CKS()
cks.ingest_pattern(
    title=f"Task {task_id}: {task_name}",
    content=task_description,
    metadata={
        "task_id": task_id,
        "status": task_status,
        "priority": priority
    },
    tags=["nse", "task", task_status]
)
```

**Pros:**
- Uses unified CKS interface
- Simple, clean code
- Consistent with other entries
- Semantic search enabled

**Cons:**
- No batch operations (must ingest one at a time)

---

## CKS CLI Research

### CLI Structure (cks_cli.py)

**Entry Point:**
```bash
python -m src.cks.cks_cli stats     # Show statistics
python -m src.cks.cks_cli query X   # Search for X
```

**Class Structure:**
```python
class CKSCLI:
    def __init__(self):
        self.cks = CKSQueryInterface()  # Uses legacy interface

    def show_statistics(self) -> Dict[str, Any]:
        """Display CKS system statistics."""

    def search(self, query: str, graph_type: str = 'knowledge') -> List[Dict]:
        """Search content across CKS graphs."""
```

**Key Insight:** CLI uses `CKSQueryInterface` (legacy), not `CKS` (unified).

**Two CKS Interfaces:**
1. **Legacy:** `CKSQueryInterface` in `cks_query_interface.py`
2. **Unified:** `CKS` in `unified.py`

**Recommendation:** Use unified `CKS` interface for new code.

---

## Discover Integration Research

### CKS Enhanced Pre-Query

**Location:** `src/modules/discover/explorer_spec.py`

**Integration Point:**
```python
# CKS pre-query for context
cks_results = cks_enhanced_pre_query(
    query=user_query,
    limit=5,
    session_id=session_id
)
```

**Query Types Supported:**
- FTS5 full-text search (sub-10ms)
- Graph traversal for entity relationships
- Session context tracking

**Entry Type Support:**
The unified CKS `search()` method filters by `entry_type`:
```python
def search(
    self,
    query: str,
    entry_type: Optional[str] = None,  -- Can filter by "pattern"
    limit: int = 10
) -> List[Dict[str, Any]]:
```

**Conclusion:** Using `type: "pattern"` will work seamlessly with discover's CKS pre-query.

---

## Venv/Cache Filter Research

### Filter Function (explorer_spec.py:124-152)

**Implementation:**
```python
def filter_venv_and_cache(files):
    """Filter out venv, cache, and other non-source directories.

    Args:
        files: Iterable of Path objects

    Returns:
        Generator yielding only source files (not venv/cache)
    """
    skip_patterns = [
        'venv', 'env', '.venv', '__pycache__',
        'node_modules', '.git', '.pytest_cache',
        'site-packages', 'dist', 'build',
        '.eggs', '*.egg-info',
        # Virtual environment markers
        '/Lib/site-packages/', '/lib/python', '/Scripts/'
    ]

    for file in files:
        file_str = str(file)
        if not any(pattern in file_str for pattern in skip_patterns):
            parent_parts = file.parts
            has_venv_marker = any(
                part in ['venv', 'env', '.venv', 'site-packages', 'Scripts']
                for part in parent_parts
            )
            if not has_venv_marker:
                yield file
```

**Usage Locations:** 9 places in explorer_spec.py

**Results:**
- 61% file reduction (33,912 → 13,068 Python files)
- Significant performance improvement

**Reusability:** Function is standalone, can be imported for use in standards scanner.

---

## Coding Standards File Analysis

### Python Quick Reference Structure

**File:** `.claude/commands/code_python_2025_quick_reference.md` (105 lines)

**Structure:**
```markdown
# LLM Quick Reference: 10 Non-Negotiables

## The 10 Mandatory Standards
| # | Standard | DO THIS | NOT THIS | Why |
|---|----------|---------|----------|-----|
| 1 | Packaging | uv sync | requirements.txt | 100x faster |
...

## Code Patterns: REFUSE These
- Circular imports
- Classes > 300 lines
...

## The Judgment Test
When asked to do something that breaks these standards...

## Why Compliance = Competence
...

## The 3-Second Decision Framework
...

## CSF NIP Python Skills Integration
...

## One More Thing
...
```

**Parsing Strategy:**
1. Lines 9-20: Parse markdown table for 10 standards
2. Lines 24-36: Parse "REFUSE These" list for anti-patterns
3. Extract: standard_number, title, do_this, not_this, rationale

### TypeScript Quick Reference Structure

**File:** `.claude/commands/code_ts_2025_quick_reference.md` (51 lines)

**Structure:**
```markdown
# LLM Quick Reference: TypeScript 2025

## The 10 Mandatory Standards
| # | Standard | DO THIS | NOT THIS | Why |
|---|----------|---------|----------|-----|
| 1 | Runtime | Node 22 (LTS) or Bun | Node 18, 16 | Native fetch |
...

## Code Patterns: REFUSE These
- require() or module.exports
- explicit 'any' type
...

## The Judgment Test
...

**Status**: Production Standard (v3.0+)
```

**Parsing Strategy:** Same as Python (parse table + anti-patterns list)

---

## Technical Decisions

### Decision 1: Entry Type for Coding Standards

**Options:**
1. `type: "pattern"` - Repeating best practices
2. `type: "knowledge"` - Factual information
3. `type: "coding_standard"` - New custom type

**Recommendation:** Use `type: "pattern"`

**Rationale:**
- Coding standards ARE repeatable best practices (patterns)
- Existing type, no schema changes needed
- Aligns with CKS design intent
- Compatible with CKS search and discover integration

### Decision 2: Ingestion Approach

**Options:**
1. Direct SQLite (like `direct_knowledge_ingestion.py`)
2. Unified CKS class (like `nse_task_awareness_knowledge_ingestion.py`)

**Recommendation:** Use unified CKS class

**Rationale:**
- Simpler, cleaner code
- Uses single database (`data/cks.db`)
- Semantic search enabled automatically
- Consistent with other entries
- Easier maintenance

**Trade-off:** No batch operations, but 40 entries total (20 per language) is manageable.

### Decision 3: CLI Integration

**Options:**
1. Extend existing `cks_cli.py`
2. Create separate command script
3. Add subcommand to existing CLI

**Recommendation:** Create separate script in `src/cks/commands/`

**Rationale:**
- `cks_cli.py` uses legacy interface
- Separate script can use unified CKS
- Can be invoked as `python -m cks.ingest_coding_standards`
- Cleaner separation of concerns

---

## Implementation Strategy

### Phase 1: Create Ingestion Script

**File:** `src/cks/commands/ingest_coding_standards.py`

**Structure:**
```python
#!/usr/bin/env python3
"""
Coding Standards Ingestion Script

Ingests Python and TypeScript coding standards into CKS knowledge base.
Usage:
    python -m cks.commands.ingest_coding_standards --all
    python -m cks.commands.ingest_coding_standards --language python
    python -m cks.commands.ingest_coding_standards --stats
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from cks.unified import CKS

class CodingStandardsIngestion:
    """Ingest coding standards into CKS."""

    def __init__(self):
        self.cks = CKS()

    def ingest_python_standards(self):
        """Parse and ingest Python coding standards."""
        # Parse code_python_2025_quick_reference.md
        # Create pattern entries for each standard
        pass

    def ingest_typescript_standards(self):
        """Parse and ingest TypeScript coding standards."""
        # Parse code_ts_2025_quick_reference.md
        # Create pattern entries for each standard
        pass

    def show_stats(self):
        """Show statistics on ingested standards."""
        results = self.cks.search("", entry_type="pattern")
        python_standards = [r for r in results if r.get('metadata', {}).get('language') == 'python']
        ts_standards = [r for r in results if r.get('metadata', {}).get('language') == 'typescript']
        print(f"Python standards: {len(python_standards)}")
        print(f"TypeScript standards: {len(ts_standards)}")
```

### Phase 2: Parse Markdown Tables

**Parser Function:**
```python
import re

def parse_markdown_table(lines: list) -> list:
    """Parse markdown table from quick reference files.

    Args:
        lines: List of file lines

    Returns:
        List of dicts with keys: number, standard, do_this, not_this, why
    """
    standards = []
    in_table = False

    for line in lines:
        # Detect table header
        if line.strip().startswith('| # | Standard |'):
            in_table = True
            continue

        # Skip separator row
        if in_table and line.strip().startswith('|---'):
            continue

        # Parse table row
        if in_table and line.strip().startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Remove empty first/last
            if len(parts) >= 5:
                standards.append({
                    'number': parts[0],
                    'standard': parts[1],
                    'do_this': parts[2],
                    'not_this': parts[3],
                    'why': parts[4]
                })

        # End of table
        if in_table and not line.strip().startswith('|'):
            break

    return standards
```

### Phase 3: Parse Anti-Patterns

**Parser Function:**
```python
def parse_anti_patterns(lines: list) -> list:
    """Parse anti-patterns list from quick reference files.

    Args:
        lines: List of file lines

    Returns:
        List of anti-pattern strings
    """
    anti_patterns = []
    in_section = False

    for line in lines:
        # Detect start of section
        if 'REFUSE These' in line or 'REFUSE THESE' in line:
            in_section = True
            continue

        # Parse list items
        if in_section:
            if line.strip().startswith('- '):
                anti_patterns.append(line.strip()[2:])
            elif line.strip().startswith('```'):
                # Code block
                continue
            elif not line.strip():
                # Empty line
                continue
            else:
                # End of section
                break

    return anti_patterns
```

---

## Validation Strategy

### Test 1: Ingestion Completeness

**Verify:**
- 20 Python entries (10 standards + 10 anti-patterns)
- 20 TypeScript entries (10 standards + 10 anti-patterns)

**Method:**
```python
cks = CKS()
results = cks.search("", entry_type="pattern")
standards = [r for r in results if 'standard' in r.get('tags', [])]
print(f"Total standards ingested: {len(standards)}")
```

### Test 2: Discover Integration

**Verify:**
- `/discover "ruff linting"` returns Python Standard #2
- `/discover "bare except"` returns anti-pattern entry
- Results exclude venv/cache directories

**Method:**
```bash
/discover "ruff linting" --project-path P:/__csf.nip/src
```

### Test 3: Query Performance

**Verify:**
- Query time <10ms (FTS5)
- Discover overhead <100ms

**Method:**
```python
import time

start = time.time()
results = cks.search("python linting", entry_type="pattern")
elapsed = (time.time() - start) * 1000
print(f"Query time: {elapsed:.2f}ms")
```

---

## Risk Mitigation

### Risk 1: Discover Still Broken

**Mitigation:**
- Test discover early after ingestion
- If broken, use manual scanner with CKS lookup:
  ```python
  # Manual fallback
  cks = CKS()
  standard = cks.search("bare except", entry_type="pattern")[0]
  violations = find_violations_in_codebase("except:", filter_func=filter_venv_and_cache)
  display_results(standard, violations)
  ```

### Risk 2: Parsing Failures

**Mitigation:**
- Simple regex-based parsing (robust)
- Test parser on both files before ingestion
- Fallback to manual entry if parsing fails

### Risk 3: CKS Schema Constraints

**Mitigation:**
- Using existing `type: "pattern"` (no schema changes)
- Validated against `VALID_ENTRY_TYPES` list
- Tested with unified CKS class

---

## Next Steps

1. **Create ingestion script** (`src/cks/commands/ingest_coding_standards.py`)
2. **Implement parsers** for markdown tables and anti-patterns
3. **Ingest Python standards** (10 mandatory + anti-patterns)
4. **Ingest TypeScript standards** (10 mandatory + anti-patterns)
5. **Test `/discover` integration** with standards queries
6. **Verify venv/cache filtering** works correctly

**Estimated Implementation Time:** 4-6 hours

---

## Conclusion

Research confirms feasibility of coding standards ingestion into CKS:

- ✅ **Schema supports it:** Use `type: "pattern"` (existing valid type)
- ✅ **Ingestion pattern exists:** Unified CKS class provides clean API
- ✅ **Discover integration ready:** FTS5 search + entry_type filtering
- ✅ **Venv filtering available:** Function already implemented

**No technical blockers identified.** Proceed to implementation.

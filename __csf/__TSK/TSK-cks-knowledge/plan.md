# CKS Knowledge Enhancement - Implementation Plan

## Project Overview

**Goal**: Enhance existing CKS with AST-based chunking, incremental indexing, and auto-injection.

**Location**: `P:/__csf.nip/src/knowledge/`

**Timeline**: ~20 hours across 3 weeks

## Architecture

### The 3-Piece System

1. **AST-Based Chunking** (`chunking.py`)
   - Parse Python via AST (not regex)
   - Respect function/class boundaries
   - Handle decorators, async, nested classes
   - Generate SHA256 for dedup

2. **Incremental Indexer** (`indexing.py`)
   - File-timestamp based (skip unchanged)
   - SHA256 deduplication
   - Ingest via `cks.ingest_pattern()`

3. **Auto-Injection Hook** (`injection.py`)
   - Detect keywords in user message
   - Search CKS via `search_semantic()`
   - Inject top result into context

## Directory Structure

```
P:/__csf.nip/src/knowledge/
├── __init__.py
├── chunking.py
├── indexing.py
├── injection.py
└── tests/
    ├── test_chunking.py
    ├── test_indexing.py
    └── test_injection.py
```

## Implementation Order (TDD)

### Week 1: Core Files

| Day | Task | TDD Approach |
|-----|------|--------------|
| 1-2 | `chunking.py` | RED: Write test → GREEN: Implement |
| 3-4 | `indexing.py` | RED: Write test → GREEN: Implement |
| 5-6 | `injection.py` | RED: Write test → GREEN: Implement |
| 7 | Integration | End-to-end test with CKS |

### Week 2: Skill Extensions

| Day | Task |
|-----|-------|
| 1-2 | Extend `csf-nip-integration` skill |
| 3-4 | Extend `recent` skill |
| 5-7 | Test auto-injection in Claude Code |

### Week 3: Optimization

| Day | Task |
|-----|-------|
| 1-2 | Measure token savings |
| 3-4 | Refine keyword detection |
| 5-7 | Production hardening |

## Success Criteria

- [ ] `test_chunking.py`: All tests pass
- [ ] `test_indexing.py`: All tests pass
- [ ] `test_injection.py`: All tests pass
- [ ] 50+ chunks indexed into CKS
- [ ] Hook auto-injects context in Claude Code
- [ ] No duplicate chunks in CKS

## CKS API Reference

```python
from src.cks.unified import CKS

cks = CKS()  # P:/__csf.nip/data/cks.db

# Search (hook uses this)
results = cks.search_semantic(query, limit=5)

# Ingest (indexer uses this)
entry_id = cks.ingest_pattern(
    title="Function Name",
    content="def function(): ...",
    entry_type="code",
    source_chunk={"file": "path", "lines": "45-67"}
)
```

## Windows Path Handling

```python
from pathlib import Path

# CORRECT - forward slashes
db_path = Path("P:/__csf.nip/data/cks.db")
code_root = Path("P:/__csf.nip/src")

# Python-native globbing
for py_file in code_root.rglob("*.py"):
    pass
```

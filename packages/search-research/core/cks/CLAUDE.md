# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CKS (Constitutional Knowledge System)

CKS is a knowledge management and retrieval system built on SQLite with multi-graph architecture support. It serves as the central repository for all knowledge artifacts in the CSF ecosystem.

## Development Commands

```bash
# Testing
pytest tests/                          # Run all tests
pytest tests/ -m performance          # Performance tests only
pytest tests/ -m security             # Security tests only
pytest tests/ --cov=src/cks           # With coverage

# Linting and formatting (Ruff)
ruff check .                          # Check for issues
ruff format .                         # Format code
ruff check --fix .                    # Auto-fix issues

# Type checking
mypy src/cks                         # Strict type checking

# Security scanning
bandit -r src/cks                    # Security linting

# CKS CLI operations
python -m features.cks.cks_cli stats           # Show statistics
python -m features.cks.cks_cli query X         # Search for X
python -m features.cks.cks_cli rebuild-index   # Rebuild search index
python -m features.cks.cks_cli backfill        # Generate embeddings for new entries

# Validation
python validate_cks_2025.py           # Validate 2025 standards
```

## Import Patterns

**Correct CKS import for Python code:**
```python
from cks.unified import CKS  # ✅ CORRECT
```

**Incorrect imports (will fail):**
```python
from cks.cks_cli import CKS  # ❌ WRONG - CKS not exported from cks_cli
import cks.CKS               # ❌ WRONG - No top-level export
```

**Why:** `cks_cli.py` is a CLI wrapper that uses `CKS` internally via `UnifiedCKS`. The actual `CKS` class lives in `unified.py`.

## Architecture Overview

### Two-Tier Architecture

CKS has two interfaces:

1. **Unified Interface** (`unified.py`) - Simplified single-database interface for common operations
   - Database: `data/cks.db`
   - Use this for most operations

2. **Legacy Interface** (`core/`) - Original multi-graph engine with complex abstractions
   - Preserved for backward compatibility
   - Five distinct graph types: Knowledge, Vector, Causal, Social, System

### Core Components

| Component | Purpose |
|-----------|---------|
| `unified.py` | Main CKS class for ingest/search operations |
| `core/multi_graph_engine.py` | Hyper-graph operations across 5 graph types |
| `core/storage_manager.py` | Storage abstraction with SQLite backend |
| `core/gpu_manager.py` | GPU acceleration with CPU fallback |
| `core/pytorch_vector_storage.py` | Vector storage and similarity search |

### Search Enhancement Modules

| Module | Purpose |
|--------|---------|
| `query_expansion.py` | Intelligent query expansion |
| `reranking.py` | Multi-signal result fusion and ranking |
| `spell_correction.py` | Query spell correction |
| `hybrid_search_patch.py` | Hybrid search optimization |
| `commands/auto_learning_expander.py` | Auto abbreviation learning |

## Entry Types

CKS stores knowledge as typed entries:

- `memory` - Chat history, Q&A sessions
- `pattern` - Documentation, best practices
- `code` - Code snippets, examples
- `knowledge` - Articles, references
- `correction` - Mistakes and fixes
- `decision` - Choices made and rationale
- `commitment` - Promises/resolutions
- `insight` - Realizations and epiphanies
- `learning` - Lessons learned

## Quick Start

### CLI Commands (Recommended)

```bash
# Add content with auto-detection
python -m src.cks.cks_cli add "Results: 32% reduction in latency"
python -m src.cks.cks_cli add --file pattern.md

# Search CKS
python -m src.cks.cks_cli query "hook patterns"

# Show statistics
python -m src.cks.cks_cli stats

# Extract lessons from session
python -m src.cks.cks_cli session

# Rebuild search index
python -m src.cks.cks_cli rebuild-index

# Backfill embeddings
python -m src.cks.cks_cli backfill
```

### Python API

```python
from cks.unified import CKS

# Initialize (defaults to data/cks.db)
with CKS() as cks:
    # Store memories and patterns
    cks.ingest_memory("What is JWT?", "JWT is JSON Web Tokens...")
    cks.ingest_pattern("Dual Sink Logging", "Route logs to both JSON and text...")

    # Search
    results = cks.search("logging")
    stats = cks.get_statistics()
```

### Entry Type Auto-Detection

The `add` command automatically detects content type:

| Pattern | Detected Type | Example |
|---------|---------------|---------|
| "Results:", "Anti-pattern:", "%" | `pattern` | `Results: 32% faster` |
| Question starts (What/How/Why) | `memory` | `What is JWT?` |
| "def ", "class " | `code` | `def process():` |
| "decided to", "chose to" | `decision` | `Decided to use FAISS` |
| "fixed:", "correction:" | `correction` | `Fixed: missing import` |
| "realized:", "insight:" | `insight` | `Realized: GPU bottleneck` |
| "learned:", "lesson:" | `learning` | `Lesson: always test first` |
| Default | `knowledge` | General documentation |

## Integration Layer

CKS integrates with external systems via `integration/`:

- **HDMA Client** - Static analysis pattern integration
- **Serena Client** - LSP-based multi-language code analysis
- **Chat History Client** - Conversation pattern extraction
- **Web Content Client** - Web content extraction with security scanning

See `integration/README.md` for integration details.

## Configuration

Environment variables:

```bash
# Spell correction
export CKS_SPELL_CORRECTION_ENABLED=true

# HDMA integration
export HDMA_API_URL="http://localhost:8080"

# Serena integration
export SERENA_WORKSPACE_ROOT="/path/to/workspace"

# GPU selection
export CUDA_VISIBLE_DEVICES=0
```

## Data Storage

- **Database**: `P:\\\\__csf.nip/data/cks.db`
- **FAISS Index**: `P:\\\\__csf.nip/data/cks_hypergraph/`

### Real-Time FAISS Updates

CKS entries are queryable via semantic search within ~2 seconds of ingest via the write-signal mechanism:

1. Stop hooks (`Stop_cks_correction_anchor.py`, `Stop_cks_decision_capture.py`) call `DaemonClient.send_write_signal()` after ingest
2. `UnifiedSemanticDaemon` receives the signal on `\\.\pipe\csf_semantic_write_signal` and sets `_faiss_dirty = True`
3. `check_idle_work()` triggers immediate FAISS refresh — no 10-minute staleness window

This replaces time-based FAISS staleness (600s interval) with event-driven updates.

## Related Systems

CKS is part of the unified search ecosystem:

- **CHS** (`src/features/chs/`) - Chat History Search
- **Search** (`src/features/search/`) - Unified search router
- **CDS** - Code Documentation Search (part of search backends)

The `/search` command orchestrates queries across CKS, CHS, CDS, and other backends.

## Per-File Learning Tracking

CKS supports structured file citation tracking for lessons and diagnostic findings.

### Citation Format

File references are automatically extracted from lesson text in the format: `path/to/file.py:123`

Supported formats:
- Relative paths: `contract_api.py:142`
- Absolute paths (Windows): `P:\\\\__csf/src/core/lesson_extractor_claude.py:387`
- Nested paths: `src/cks/unified.py:410`

Supported extensions: `.py`, `.md`, `.ts`, `.js`, `.yaml`, `.yml`, `.json`, `.sh`

### Citation Parser API

```python
from src.cks.learning.citation_parser import extract_citations

text = "The bug is in contract_api.py:142 where null check was added."
citation = extract_citations(text)
# Returns: {"file_path": "contract_api.py", "line_number": 142}
```

### Diagnostic Writer API

For diagnostic skills (`/rca`, `/debug`, `/tdd`, `/arch`) to store structured findings:

```python
from src.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding

finding = DiagnosticFinding(
    category="BUG",  # FIX, BUG, VULNERABILITY, PATTERN, DISCOVERY
    file_path="auth.py",
    line_number=88,
    summary="SQL injection risk",
    details="User input not sanitized before query",
    skill_source="rca",  # rca, debug, tdd, arch, security
)

store_finding(finding)  # Returns True on success, False on error
```

### File History Query

Query all lessons for a specific file:

```python
from src.cks.commands.file_history import query_file_history

results = query_file_history("contract_api.py")
# Returns list of entries with file_path metadata or title matches
```

### Metadata Structure

Entries with citations include additional metadata:

```json
{
  "category": "BUG",
  "source": "retrospective_hook_claude",
  "timestamp": "2026-02-03T10:00:00Z",
  "file_path": "contract_api.py",
  "line_number": 142
}
```

This enables file-level learning queries across all sessions.

# CSF Search Patterns - Working Methods

This document summarizes the working search patterns for querying CKS, CHS, and other CSF data stores.

## 1. Direct SQLite Query (Most Reliable)

**When to use**: When you need direct, reliable access to the database without dependencies.

**CKS (Constitutional Knowledge System)**:
```python
import sqlite3
from pathlib import Path

db_path = Path('P:/__csf/data/cks.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Search by content
cursor.execute('''
    SELECT type, title, substr(content, 1, 200)
    FROM entries
    WHERE content LIKE '%hook%'
    ORDER BY created_at DESC
    LIMIT 10
''')

for entry_type, title, content in cursor.fetchall():
    print(f"[{entry_type}] {title}")
    print(f"    {content}...")
```

**CHS (Chat History)**:
```python
db_path = Path('P:/__csf/data/chat_history.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Recent messages (timestamps are ISO 8601 strings)
cursor.execute('''
    SELECT substr(content, 1, 100), timestamp
    FROM chat_messages
    ORDER BY timestamp DESC
    LIMIT 5
''')

for content, ts in cursor.fetchall():
    print(f"[{ts}] {content}")
```

**Note**: CHS timestamps are stored as ISO 8601 strings (e.g., `2026-01-16T22:30:09.340000`), not as epoch integers.

---

## 2. CSF Search CLI (Unified Interface)

**When to use**: When you want a unified interface to search across all backends.

**Location**: `P:/__csf/src/cli/nip/search.py`

**Usage**:
```bash
cd P:/__csf
python src/cli/nip/search.py "your query" --limit 10 --backend cks
```

**Available Backends**:
- `cks` - Constitutional Knowledge System
- `chs` - Chat History
- `cds` - Code Documentation Search
- `code` or `grep` - Source code search
- `docs` - Documentation folder

**Filtering Options**:
```bash
# Filter by backend/source
python src/cli/nip/search.py "query" --filter backend:CKS

# Filter by result type
python src/cli/nip/search.py "query" --filter-type memory,pattern

# Filter by date range
python src/cli/nip/search.py "query" --filter-after 2024-01-01

# Minimum relevance score
python src/cli/nip/search.py "query" --min-score 0.7
```

---

## 3. Semantic Daemon Client

**When to use**: When you need semantic search with automatic daemon startup.

```python
from daemons.daemon_client import DaemonClient

client = DaemonClient(auto_start=True, enable_fallback=True)

# Search CKS
cks_results = client.search("cks", "query text", limit=10)

# Search CHS
chs_results = client.search("chs", "chat topic", limit=10)

# Process results
for result in cks_results:
    print(f"[{result.get('type', 'unknown')}] {result.get('title', 'no title')}")
```

**Daemon Discovery**: The daemon writes its location to `P:/__csf/data/semantic_daemon_discovery.json`.

---

## 4. Claude Code /search Skill

**When to use**: From within Claude Code sessions.

```bash
/search "your query"
/search "query" --limit 10
/search "query" --backend chs,cks
```

---

## 5. Codebase Search Patterns (Grep/Glob)

**When to use**: When searching source code, finding files by type, or locating specific patterns in the codebase.

### File Glob Patterns

**Common file type patterns**:
```bash
# Python files
**/*.py
src/**/*.py
tests/test_*.py

# Documentation
**/*.md
docs/**/*.md

# Configuration
**/*.json
**/*.yaml
**/*.yml
**/*.toml

# Skills and hooks
.claude/skills/**/SKILL.md
.claude/hooks/*_gate.py
```

### Grep/Ripgrep Patterns

**Best practices for content search**:
```bash
# Search for function definitions
grep -r "def my_function" src/
rg "def my_function" src/

# Search for imports/dependencies
grep -rh "^import \|^from " src/
rg "^(import|from) " src/

# Search for TODO/FIXME comments
grep -rh "TODO\|FIXME\|XXX" src/
rg "TODO|FIXME|XXX" src/

# Case-insensitive search
grep -ri "error" src/
rg -i "error" src/

# Search with context lines
grep -rn "hook" src/ -A 2 -B 2
rg "hook" src/ -C 2
```

### Common Pitfalls

**Directories to avoid searching**:
- `node_modules/` - NPM dependencies (huge, binary files)
- `.git/` - Version control metadata
- `__pycache__/` - Python bytecode cache
- `.venv/`, `venv/` - Virtual environments
- `dist/`, `build/` - Build artifacts
- `.pytest_cache/` - Test cache
- `*.egg-info/` - Package metadata

**Exclusion patterns**:
```bash
# Exclude directories from grep
grep -r --exclude-dir=node_modules --exclude-dir=.git "pattern" src/

# Exclude with ripgrep (recommended)
rg "pattern" src/ --glob='!node_modules/**' --glob='!.git/**'

# Only search specific file types
rg "pattern" --type py
rg "pattern" -g "*.py"
```

### Claude Code Tool Usage

**Grep tool** (preferred over bash grep):
```
# Search with context
Search for: "def my_function"
In: src/
pattern: "def my_function"
-C: 3
```

**Glob tool** (find files by pattern):
```
# Find Python files
Pattern: **/*.py
Path: src/

# Find markdown docs
Pattern: **/*.md
Path: docs/
```

**Read tool** (with glob):
```
# Read all test files
Files: tests/test_*.py
```

### Performance Tips

1. **Use ripgrep (rg) instead of grep** - 10-100x faster
2. **Narrow your scope** - Search specific directories, not the entire repo
3. **Use file type filters** - `--type py` is faster than `| grep "\.py$"`
4. **Avoid searching build artifacts** - Exclude node_modules, dist, build
5. **Use Grep tool first, then Read** - Pattern match before reading full files

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors in search.py | Fixed - now uses importlib for local modules |
| Timestamps showing 1970-01-01 | Timestamps are ISO strings, not epoch integers |
| Daemon not responding | Check discovery file or use fallback mode |
| Empty results | Verify database path and table names |

---

## Database Schema Reference

**CKS Tables**:
- `entries` - Main knowledge entries (type, title, content, created_at)
- `entry_entities` - Entity links
- `knowledge_nodes`, `knowledge_edges` - Knowledge graph

**CHS Tables**:
- `chat_messages` - Chat history (content, timestamp, session_id)
- `chat_sessions` - Session metadata
- FTS tables for full-text search

---

## Related Files

- `P:/__csf/src/cli/nip/search.py` - Unified search CLI
- `P:/packages/search-research/contrib/semantic_daemon/daemon_client.py` - Daemon client
- `P:/__csf/data/semantic_daemon_discovery.json` - Daemon discovery file
- `P:/__csf/data/cks.db` - CKS database
- `P:/__csf/data/chat_history.db` - CHS database

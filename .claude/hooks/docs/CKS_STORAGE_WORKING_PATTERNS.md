# CKS Storage Working Patterns

## ~~Problem: "No stderr output" Error~~ **RESOLVED**

**Previous behavior (before 2026-03-01 fix):**
When running `python -c` commands for CKS storage, you may have seen:

```
Error: PreToolUse:Bash hook error: [python ...hook_runner.py...]: No stderr output
```

**This is NOT a cosmetic error** - it was caused by PreToolUse hooks writing to `sys.stderr`. Claude Code treats ANY stderr from hooks as "hook error".

**Fix applied 2026-03-01:** Commented out all stderr writes in PreToolUse hooks (verified counts):
- `PreToolUse.py` (6 instances)
- `PreToolUse_authorization_gate.py` (2 instances)
- `PreToolUse_destructive_git_guard.py` (5 instances)
- `PreToolUse_python_c_validator.py` (1 instance)
- `PreToolUse_syntax_gate.py` (3 instances)

**Current behavior:** Hooks now use stdout for JSON output and exit codes only. No stderr writes.

## Working CKS Storage Patterns

### Method 1: Direct SQL (Fastest, No Embeddings)

```python
cd P:/__csf && python -c "
import sqlite3
db = sqlite3.connect('data/cks.db', timeout=10)
cursor = db.cursor()
cursor.execute('INSERT INTO entries (type, title, content) VALUES (?, ?, ?)',
    ('pattern', 'Title here', 'Content here'))
db.commit()
print('✅ Stored')
"
```

**⚠️ WARNING**: Direct SQL inserts do NOT generate embeddings. Entries stored this way will NOT be found by semantic search via the daemon. Use Method 2 if you need semantic search.

**Schema**: `id, type, title, content, metadata, embedding, source_chunk, usage_count, success_count, thumbs_up, thumbs_down, created_at, updated_at`

**Entry types**: `pattern`, `memory`, `code`, `knowledge`, `correction`, `decision`, `commitment`, `insight`, `learning`

### Method 2: CKS Unified API (RECOMMENDED - Includes Embeddings)

```python
cd P:/__csf && python -c "
import sys
sys.path.insert(0, 'src')
from cks.unified import CKS

with CKS() as cks:
    cks.ingest_pattern('Pattern title', 'Pattern content...')
    cks.ingest_memory('What is X?', 'X is...')
    print('✅ Stored via CKS.unified with embeddings')
"
```

**Use this method when**: You need entries to be searchable via semantic search (daemon). The `ingest_pattern` and `ingest_memory` methods automatically generate embeddings.

### Method 3: CLI (Best for Interactive Use)

```bash
# From P:/__csf directory
python -m cks.cks_cli add "Results: 32% reduction"
python -m cks.cks_cli add --file pattern.md
python -m cks.cks_cli query "hook patterns"
python -m cks.cks_cli stats
```

## What NOT To Do

1. **Don't use made-up env vars** like `CDSF_INVESTIGATION_GATE=0` - they don't actually do anything
2. **Don't use `from knowledge.storage import store`** - that module doesn't exist

## ~~Root Cause of "No stderr output" Error~~ **FIXED**

**Previous incorrect explanation (DEPRECATED):**
The documentation previously claimed this was a "Claude Code internal behavior" that couldn't be fixed. **This was incorrect.**

**Actual root cause:**
PreToolUse hooks were writing to `sys.stderr` for warnings, errors, and status messages. Claude Code treats ANY stderr from hooks as "hook error" and displays it to the user.

**Correct fix (applied 2026-03-01):**
Following the pattern from `bugfixes.md` (SessionStart "Hook Error" False Positive, 2026-02-15), all stderr writes in PreToolUse hooks were commented out. Hooks now:
- Use stdout for JSON output (`{}` for allow, `{"decision": "block"}` for deny)
- **Never write to stderr** (even for warnings/errors)
- Use exit codes (0 for allow, 2 for block)

**Key lesson from bugfixes.md:**
> Claude Code hooks must NEVER write to stderr. Use stdout for output, silence for no-op.

## Verification

CKS storage is working correctly:

```bash
cd P:/__csf && python -c "
import sqlite3
db = sqlite3.connect('data/cks.db', timeout=10)
cursor = db.cursor()
cursor.execute('SELECT COUNT(*) FROM entries WHERE type=\"pattern\"')
print('Patterns stored:', cursor.fetchone()[0])
"
```

## Related Documentation

- `P:/__csf/src/cks/CLAUDE.md` - Full CKS documentation
- `P:/.claude/hooks/CLAUDE.md` - Hook behavior documentation
- `C:/Users/brsth/.claude/projects/P--/memory/bugfixes.md` - Historical bug fixes (see "SessionStart 'Hook Error' False Positive (2026-02-15)")

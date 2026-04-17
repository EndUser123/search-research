# Repo Context for PreToolUse Discovery Gate Design

## 1. Repo Layout

**Project root**: `P:/packages/search-research/`
**Total Python files**: 620 (excluding `.venv/`, `.git/`)
**Module structure**: Flat-ish with `core/`, `core/backends/local/`, `core/backends/web/`, `core/chs/`, `core/analysis/`, `contrib/` subdirs

**Key Python file locations** (edit targets):
```
./core/                    # Main router, cache, config, metrics, tracing, models, modes, hyde, backends
./core/backends/local/     # 14 local backends (grep, cds, cks, chs, ast, call_graph, kg, rlm, ...)
./core/backends/web/       # Web providers
./core/chs/                # Chat history system (db, embeddings, indexer, clustering, ...)
./contrib/                 # Semantic daemon, tests
./tests/                   # Test suite
```

**Session isolation mechanism**:
- Worktree-based: Multiple terminals use separate git worktrees under `P:/.claude/worktrees/`
- Session state: `P:/.claude/state/investigation_state_{terminal_id}.json`
- Terminal ID extracted via `_safe_id_str()` → sanitized filenames

**Current investigation state file** (example path):
```
P:/.claude/state/investigation_state_console_abc123.json
```

---

## 2. Current Hooks (PreToolUse)

### Primary router: `P:/.claude/hooks/PreToolUse.py` (57KB)
- Entry: `process_hook()` function
- Dispatches to TOOL_HOOKS via `PreToolUse_write_router.py`
- Key constants:
  - `WRITE_TOOLS = {"write_file", "str_replace_editor", "edit_file", "Write", "patch", "Edit", "MultiEdit"}`
  - `READ_TOOLS = {"read_file", "View", "cat", "grep", "find", "search_files", "Bash", "Read", "Glob", "Grep", "WebFetch", "WebSearch"}`

### Investigation Gate: `P:/.claude/hooks/PreToolUse_investigation_gate.py` (48KB, 1200+ lines)
- Tracks `files_read` list in state file per terminal
- `check_write_permission()`: Requires at least 1 related read before Edit/Write
- `paths_related()`: Same directory OR parent/child relationship = related
- **Auto-read fallback** (lines 1113-1152): If you Edit without reading, hook auto-reads the file content and lets you proceed — it does NOT block, it reads-for-you
- Has compaction-aware state reconstruction (`_reconstruct_files_read_from_input()`)

### Other PreToolUse hooks (not exhaustive):
| Hook | Size | Purpose |
|------|------|---------|
| `PreToolUse_authorization_gate.py` | 33KB | Blocks destructive actions without plan |
| `PreToolUse_investigation_gate.py` | 48KB | Discovery-before-edit enforcement |
| `PreToolUse_git_safety.py` | 18KB | Worktree cross-contamination, git restore suggestions |
| `PreToolUse_dependency_verification_gate.py` | 19KB | Blocks pip/npm install without prior verification |
| `PreToolUse_directory_policy.py` | 37KB | Path protection, restricted paths |
| `PreToolUse_import_deletion_guard.py` | 14KB | Catches imports referencing staged-for-deletion modules |
| `PreToolUse_breadcrumb_gate.py` | 9KB | Workflow step enforcement |
| `PreToolUse_command_intent_gate.py` | 10KB | Validates bash commands match user intent |

### Registration (from `PreToolUse.py` TOOL_HOOKS):
```python
TOOL_HOOKS = {
    "Edit": [
        "PreToolUse_investigation_gate.py",
        "PreToolUse_authorization_gate.py",
        "PreToolUse_git_safety.py",
        "PreToolUse_dependency_verification_gate.py",
        ...
    ],
    "Write": [...],
    ...
}
```

### `PreToolUse_import_deletion_guard.py` — Relevant for tombstone detection
This hook already exists and catches imports referencing staged-for-deletion modules. It was added after the tombstone bug pattern was identified.

---

## 3. Terminal / Session Setup

**Shell**: `bash` (Git Bash on Windows 11)
**Session ID**: Not set via `CLAUDE_SESSION_ID` env var (returns `unset`)
**Terminal ID extraction**: `_safe_id_str()` sanitizes strings (strips `<>:"/\|?*`, replaces spaces with `_`, truncates to 64 chars)

**Typical multi-terminal setup**:
- Terminal 1: `P:/packages/search-research/` (main worktree)
- Terminal 2+: Worktrees under `P:/.claude/worktrees/ai-task-YYYYMMDD-HHMMSS/`
- Each terminal has isolated `investigation_state_{terminal_id}.json`

**Path normalization**: Windows paths use `P:/...` style (forward slashes accepted)

---

## 4. Shell / Platform

- **Platform**: Windows 11 Pro, `bash` (Git Bash / WSL-style)
- **Python**: 3.12+ via `.venv` virtualenv
- **Hooks**: Python subprocess via `settings.json` registration OR in-process via `PreToolUse.py` IN_PROCESS_HOOKS
- **Concurrent access**: Cross-platform file locking via `filelock` library

---

## 5. What the Tombstone Bug Actually Was

```
router_async.py:32 → from .tracing import QueryTracer, QueryTrace
core/tracing.py     → was STAGED FOR DELETITION (not on disk, but import remained)
```

The `PreToolUse_import_deletion_guard.py` hook catches this AFTER staging (`git add`), but NOT before editing — because the import was already in the file before it was staged.

**What would have caught it earlier**:
1. `git ls-files --deleted` → cross-reference imports in surviving files
2. A pre-git-check that validates "every import's target is either on disk OR in git staging"
3. The Edit tool itself checking if any `from .X import` in the target file resolves to a deleted file

---

## 6. MVP Sketch (Current Gap)

The existing `PreToolUse_investigation_gate.py` enforces read-before-edit but has a wide auto-read fallback. The design question is whether to:

**Option A**: Tighten the auto-read fallback (require explicit Grep/Read, disable auto-read) — simpler but more invasive to workflow
**Option B**: Add a separate pre-edit tombstone scanner (checks imports in target file against git deleted files) — surgical, doesn't change discovery gate behavior
**Option C**: Combine with import_deletion_guard to form a two-stage gate — Stage 1: discovery, Stage 2: tombstone check

---

## 7. What the Other LLM Needs to Design Properly

1. **Repo root**: `P:/packages/search-research/` — 620 Python files
2. **Hooks dir**: `P:/.claude/hooks/` (NOT `.claude/hooks/` in the project — that's empty)
3. **Registration mechanism**: `PreToolUse.py` TOOL_HOOKS dict, NOT `settings.json` subprocess (for in-process hooks)
4. **Terminal isolation**: Per-terminal state file, worktree-isolated, no cross-terminal bleed
5. **Existing auto-read fallback** (lines 1113-1152 of investigation_gate.py): Any redesign must decide whether to keep, disable, or modify this behavior
6. **Import deletion guard** already exists at `P:/.claude/hooks/PreToolUse_import_deletion_guard.py` — tombstone pattern is partially covered post-git-add, but not at edit time
7. **Shell**: bash on Windows, Python 3.12, forward-slash paths accepted
8. **CLAUDE_SESSION_ID**: Not set — terminal ID is derived from context, not env var
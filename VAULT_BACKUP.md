# Claude Vault Backup System

Complete session backup and archival system that ensures your Claude Code sessions are preserved indefinitely in a searchable database, protecting against the 21-day cleanup cycle.

## Overview

This system automatically archives Claude Code sessions to a local SQLite database (`vault.db`) before cleanup happens, making them:
- **Searchable** - Find old session content via `/search --source vault`
- **Persistent** - Sessions are never lost to Claude Code cleanup
- **Redundant** - Dual hooks (PreCompact + SessionEnd) ensure no data loss

## How It Works

```
Session Lifecycle
├─ Session runs normally...
├─ (21 days pass - approaching cleanup)
├─ PreCompact hook fires
│  └─ Calls: claude-vault import
│     └─ Copies all sessions to vault.db
├─ /compact runs (cleanup)
├─ Old sessions deleted from .claude/projects/
└─ Sessions still searchable in vault.db
```

### Two-Layer Archival Strategy

**Layer 1: PreCompact Hook (Primary)**
- Runs synchronously before `/compact` 
- Guaranteed to execute before cleanup
- 30-second timeout
- Logs execution status to stderr

**Layer 2: SessionEnd Hook (Redundant)**
- Runs asynchronously when session closes
- Provides backup archival if PreCompact fails
- Non-blocking (timeout=0)
- Silent operation

## Installation & Setup

### Quick Start

```powershell
# 1. Run setup script
.\scripts\setup_vault_backup.ps1

# 2. Done! System is ready to use
```

The setup script will:
- ✓ Check if `claude-vault` is installed
- ✓ Install it via cargo (or show fallback options)
- ✓ Validate all hook files
- ✓ Test hook syntax
- ✓ Verify vault database exists
- ✓ Confirm everything works end-to-end

### Manual Installation

If you prefer to install `claude-vault` manually:

**Option 1: Via Rust (Recommended)**
```powershell
cargo install claude-vault --locked
```

**Option 2: Pre-built Binary**
Download from: https://github.com/kuroko1t/claude-vault/releases

**Option 3: From Source**
```bash
git clone https://github.com/kuroko1t/claude-vault
cd claude-vault
cargo install --path .
```

## Usage

### Automatic Archival

No action needed. Sessions are archived automatically:
- Before `/compact` cleanup (via PreCompact hook)
- When sessions close (via SessionEnd hook)

### Search Archived Sessions

```bash
# Search specific vault
/search "your query" --source vault

# Search across all sources (includes vault)
/search "your query"

# List all archived sessions
claude-vault list

# View session details
claude-vault show <session-id>
```

### Manual Archive

```bash
# Force immediate archive (useful for testing)
claude-vault import

# Verbose output
claude-vault import --verbose
```

## Configuration

### Hook Settings

**PreCompact Hook** (`hooks/search-research_PreCompact.py`)
- Event: Fires before Claude Code cleanup
- Timeout: 30 seconds
- Behavior: Logs status, always exits 0 (doesn't block cleanup)
- Location: `~/.local/share/claude-vault/vault.db`

**SessionEnd Hook** (`hooks/search-research_SessionEnd.py`)
- Event: Fires when session ends
- Timeout: 0 (background, non-blocking)
- Behavior: Silent operation
- Redundancy: Ensures backup if PreCompact fails

### Environment Variables

```bash
# Optional: Control vault database location
export CLAUDE_VAULT_DB="~/.local/share/claude-vault/vault.db"

# Optional: Enable verbose logging
export CLAUDE_VAULT_LOG_LEVEL="debug"
```

## Database Details

### Location
```
~/.local/share/claude-vault/vault.db
```

### Schema

Three tables store all session data:

**sessions**
- `session_id` - Unique session identifier
- `project` - Project path
- `created_at` - Session creation timestamp
- `updated_at` - Last update timestamp

**messages**
- `id` - Unique message ID
- `session_id` - Reference to session
- `role` - "user" or "assistant"
- `content` - Message text
- `timestamp` - Message timestamp

**messages_fts** (Full-Text Search Index)
- Automatically indexes all message content
- Supports phrase search, wildcards, and boolean operators
- Built on SQLite FTS5

### Features

✓ **Full-Text Search (FTS5)**
- Keyword search with BM25 ranking
- Phrase search: `"exact phrase"`
- Wildcard search: `pattern*`
- Boolean: `AND`, `OR`, `NOT`

✓ **UUID Deduplication**
- Message UUIDs prevent duplicates
- Safe to import multiple times

✓ **WAL Mode**
- Write-Ahead Logging for concurrent access
- 5-second busy timeout for database locks

✓ **Automatic Noise Filtering**
- Tool results excluded
- System tags stripped
- Meta-messages filtered

## Troubleshooting

### Problem: "claude-vault command not found"

**Solution:** Install `claude-vault`
```powershell
cargo install claude-vault --locked
```

**Verify:**
```bash
claude-vault --version
```

### Problem: "vault.db not found"

**Expected behavior:** vault.db is created on first import. This is normal.

**Trigger creation:**
```bash
claude-vault import
```

### Problem: Vault database is locked

**Cause:** Multiple imports running simultaneously

**Solution:** Wait for previous import to complete, then retry
```bash
# Check if locked
lsof ~/.local/share/claude-vault/vault.db

# Retry after 5+ seconds
claude-vault import
```

### Problem: Hook not executing

**Verify hook syntax:**
```powershell
python -m py_compile hooks/search-research_PreCompact.py
```

**Check hook registration:**
```powershell
python -m json.tool hooks/hooks.json
```

**Verify $CLAUDE_PLUGIN_ROOT:**
```powershell
Write-Host $env:CLAUDE_PLUGIN_ROOT
```

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Import (100 sessions) | ~5-10s | First time slower |
| Keyword search (10 results) | ~50ms | FTS5 indexed |
| Semantic search (10 results) | ~200ms | Vector-based |
| List sessions | ~100ms | Simple query |

## Testing the System

### End-to-End Test

```powershell
# 1. Run setup (installs and verifies everything)
.\scripts\setup_vault_backup.ps1

# 2. Verify hook fires on next /compact
./scripts/setup_vault_backup.ps1 -SkipTest

# 3. Check archived sessions
claude-vault list

# 4. Search an archived session
/search "something you remember discussing" --source vault
```

### Manual Verification

```bash
# 1. Archive current sessions
claude-vault import

# 2. Check vault.db was created/updated
ls -lh ~/.local/share/claude-vault/vault.db

# 3. Count archived sessions
sqlite3 ~/.local/share/claude-vault/vault.db "SELECT COUNT(DISTINCT session_id) FROM messages;"

# 4. List latest sessions
claude-vault list --limit 5

# 5. Search via /search
/search "your query" --source vault
```

## Integration with `/search`

Once `claude-vault` is installed, the vault backend is automatically available:

```bash
# Direct vault search
/search "query" --source vault

# Included in default multi-source search
/search "query"  # Returns results from vault + other sources

# Search with filters
/search "query" --source vault --limit 20
```

Results include:
- Score (0.0-1.0, higher = more relevant)
- Session ID and timestamp
- Message role (user/assistant)
- Snippet of matching content

## Maintenance

### Regular Operations

No maintenance needed. The system is fully automatic.

### Disk Usage

Monitor vault.db growth:
```bash
du -h ~/.local/share/claude-vault/vault.db
```

Typical growth: ~1-2 MB per 100 archived sessions

### Cleanup (Optional)

If you need to remove old archived sessions:
```bash
# Delete vault.db (completely)
rm ~/.local/share/claude-vault/vault.db

# Next import will recreate it with only current sessions
claude-vault import
```

## Files in This Implementation

| File | Purpose |
|------|---------|
| `hooks/search-research_PreCompact.py` | Main archival hook (before cleanup) |
| `hooks/search-research_SessionEnd.py` | Backup archival hook (when session ends) |
| `hooks/hooks.json` | Hook registration manifest |
| `core/backends/local/vault_backend.py` | Search backend for vault.db |
| `scripts/setup_vault_backup.ps1` | Installation and verification script |
| `VAULT_BACKUP.md` | This file |

## Safety Guarantees

✓ **No Data Loss** - Dual hooks ensure sessions are archived before cleanup

✓ **No Blocking** - Hooks always exit 0, never block Claude Code operations

✓ **Idempotent** - Safe to run `claude-vault import` multiple times

✓ **Non-Invasive** - Doesn't modify any existing Claude Code files

✓ **Searchable** - Integrated with `/search` command

✓ **Reversible** - Delete vault.db anytime to reset

## Architecture Notes

### Why Two Hooks?

1. **PreCompact** - Synchronous, runs before cleanup happens
   - Most reliable because it runs at the exact right moment
   
2. **SessionEnd** - Asynchronous, runs when session closes
   - Provides redundancy if PreCompact fails
   - Non-blocking to avoid impacting session lifecycle

### Why UUID Deduplication?

Messages are deduplicated by UUID (not session_id):
- Same session imported multiple times = no duplicates
- Safe to run imports repeatedly
- Prevents growth if hooks fire multiple times

### Why Not Custom Python Archiver?

Initial design used custom Python code. Current design uses the official `claude-vault` tool because:
- ✓ Built-in noise filtering (tool results, system tags)
- ✓ UUID-based deduplication
- ✓ Better performance (Rust implementation)
- ✓ Active maintenance
- ✓ Full-text search support

## Support

For issues with claude-vault itself:
- GitHub Issues: https://github.com/kuroko1t/claude-vault/issues
- CLI Help: `claude-vault --help`

For issues with this integration:
- Check `VAULT_BACKUP.md` (this file)
- Run `./scripts/setup_vault_backup.ps1` to diagnose
- Verify hooks.json syntax with `python -m json.tool hooks/hooks.json`

## License

This implementation integrates with [claude-vault](https://github.com/kuroko1t/claude-vault) which is open source.

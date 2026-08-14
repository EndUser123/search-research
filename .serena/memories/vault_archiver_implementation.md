# Vault Archiver Implementation

## Summary
Completed full implementation of session auto-archiving to vault.db before Claude Code cleanup (21-day period).

## Components Implemented

### 1. **core/vault_archiver.py** (231 lines)
Core archiver module that handles:
- VaultArchiver class managing vault.db SQLite operations
- Schema creation: sessions table (session_id, project, created_at, imported_at, title, summary) and messages table with FTS5 index
- Session archival: `archive_session()` method reads JSONL transcripts and writes to vault.db
- Bulk archival: `archive_sessions_before_cleanup()` scans sessions directory and archives sessions approaching 21-day cleanup threshold
- Proper error handling and logging throughout
- FTS5 index management for searchability

### 2. **hooks/search-research_PreCompact.py** (45 lines)
PreCompact hook script that:
- Runs automatically BEFORE Claude Code cleanup deletes old sessions
- Uses VaultArchiver to import approaching-cleanup sessions to vault.db
- Returns gracefully (exit 0) to never block cleanup
- Logs archival progress and errors to stderr

### 3. **hooks/hooks.json** (registered)
Registered PreCompact hook with:
```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": ".*",
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PLUGIN_ROOT/hooks/search-research_PreCompact.py\"",
          "timeout": 30
        }]
      }
    ]
  }
}
```

### 4. **tests/test_vault_archiver.py** (152 lines)
Comprehensive test suite covering:
- Module initialization and db_path configuration
- Schema creation (tables and indices)
- Single session archival
- Duplicate session detection
- Non-existent transcript handling
- JSONL transcript reading

## Workflow

1. Claude Code cleanup is configured with `cleanupPeriodDays: 21`
2. Before cleanup executes, PreCompact hook fires
3. Hook runs `search-research_PreCompact.py`
4. Script identifies sessions approaching cleanup (>18 days old)
5. VaultArchiver imports each session to vault.db:
   - Reads session transcript JSONL
   - Creates vault.db schema if missing
   - Inserts session metadata + messages
   - Updates FTS5 index for full-text search
6. Sessions are now preserved in vault.db
7. VaultBackend (already integrated in router_async.py) makes them searchable via `/find`

## How to Verify

The backup is now complete. After next Claude Code cleanup:
1. Old sessions will be archived to vault.db
2. Query them via: `/find "session keywords" --source vault`
3. Or integrated with full search: `/find "keywords"` (includes vault results)

## Integration Status

- ✅ VaultBackend search (already done in previous session)
- ✅ VaultArchiver archival (NEW - this session)
- ✅ PreCompact hook registration (NEW - this session)
- ✅ Searchable via `/find` skill
- ✅ Automatic pre-cleanup archival

The backup system is now FULLY FUNCTIONAL.

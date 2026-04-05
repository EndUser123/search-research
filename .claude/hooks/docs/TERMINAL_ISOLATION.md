# Terminal Isolation

## Overview

Terminal isolation prevents cross-instance contamination when multiple Claude Code sessions run concurrently. Each session is tagged with a unique terminal ID, and all state/logs are filtered by this ID.

## Problem (Pre-v2.1)

Without terminal isolation:
- Session A logs 3 blocks
- Session B logs 2 blocks  
- Both sessions see "5/5 blocked (100%)" alert
- Aggregate masking true per-instance rates

## Solution (v2.1)

Each terminal now has a **normalized ID** with format: `{source}_{raw_id}`

| Source | Example | When Used |
|--------|---------|-----------|
| `env_` | `env_58fe0386-...` | From CLAUDE_TERMINAL_ID env var |
| `tempfile_` | `tempfile_58a8e5f3-...` | From temp file (legacy compat) |
| `console_` | `console_1a2b3c` | From Windows ConsoleHost handle |
| `fallback_` | `fallback_1` | When nothing detected |

## Key Files

| File | Purpose |
|------|---------|
| `terminal_detection.py` | Core detection logic, normalization, diagnostics |
| `SessionStart_terminal_id.py` | Sets CLAUDE_TERMINAL_ID env var at session start |
| `assumption_audit_summary.py` | Filters audit events by terminal |
| `test_assumption_audit.py` | Logs terminal ID with each event |
| `analyze_assumption_audit.py` | Supports `--terminal` and `--all` flags |
| `Stop_router.py` | Logs terminal ID at hook execution for diagnostics |

## Detection Priority

1. **CLAUDE_TERMINAL_ID** env var (process-scoped, inherited by subprocesses)
2. **TERMINAL_ID**, **TERM_ID**, **SESSION_TERMINAL** env vars
3. **Temp file** `%TEMP%\claude_terminal_id.txt` (legacy, age-limited to 48h)
4. **ConsoleHost handle** (Windows only, via GetConsoleWindow)
5. **Fallback** to `fallback_1`

## Usage

### View Current Terminal ID

```python
from terminal_detection import detect_terminal_id, get_terminal_id_diagnostic

# Simple
print(detect_terminal_id())  # e.g., "tempfile_58a8e5f3-..."

# With diagnostics
import json
print(json.dumps(get_terminal_id_diagnostic(), indent=2))
```

### Filter Analysis by Terminal

```bash
# Current terminal only
python analyze_assumption_audit.py --terminal

# All terminals separately
python analyze_assumption_audit.py --all

# All terminals combined (default)
python analyze_assumption_audit.py
```

### Check Terminal ID Stability

The Stop_router logs terminal ID at execution. If you see different IDs in the decision log for the same CC session, that indicates instability:

```bash
# Check decision log for terminal_id values
grep "terminal_id" P:/.claude/hooks/session_data/hook_decisions_*.jsonl | tail -20
```

## Backward Compatibility

The `_matches_terminal()` function handles both formats:

```python
def _matches_terminal(event_tid: str) -> bool:
    # Compares raw IDs after stripping source prefix
    # So "58a8e5f3-..." matches "tempfile_58a8e5f3-..."
```

This means:
- Old logs with raw UUIDs still match
- New logs with normalized IDs match
- Different source prefixes for same raw ID match

## State Files

Terminal-scoped state files use hashed terminal ID for filename safety:

```python
TERMINAL_HASH = hashlib.md5(TERMINAL_ID.encode()).hexdigest()[:16]
PENDING_FILE = STATE_DIR / f"pending_assumption_audit_{TERMINAL_HASH}.json"
```

## Troubleshooting

### "5/5 blocked" alert on multiple terminals

**Check:** Are both terminals legitimately blocking, or is there cross-contamination?

```bash
python analyze_assumption_audit.py --all
```

If terminals show different block rates, isolation is working.

### Terminal ID changes mid-session

**Symptoms:** Events logged under multiple terminal IDs for same session

**Diagnosis:**
```bash
grep "Stop_router" P:/.claude/hooks/session_data/hook_decisions_*.jsonl | grep terminal_id
```

**Likely causes:**
- SessionStart hook not running (env var not set)
- Temp file overwritten by another session
- Process restart within same terminal

### No terminal ID detected

**Falls back to:** `fallback_1`

**Check:**
```python
from terminal_detection import get_terminal_id_diagnostic
print(get_terminal_id_diagnostic())
```

Look at `env_vars`, `tempfile_exists`, `console_handle` to see what's available.

## Version History

- **v2.1** (2026-01-25): Normalized format, backward compat, diagnostics
- **v2.0** (2026-01-25): Environment variables prioritized, 48h temp file age limit
- **v1.0**: Basic temp file detection

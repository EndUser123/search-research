# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Unified Semantic Daemon

Windows named pipe server providing fast semantic search for CKS (Constitutional Knowledge System) and CHS (Chat History Search).

## Architecture

### Core Components

| Component                    | Purpose                                  |
| ---------------------------- | ---------------------------------------- |
| `unified_semantic_daemon.py` | Main daemon server with named pipe IPC   |
| `daemon_client.py`           | Auto-starting client with fallback logic |

### Features

- **Named pipe IPC**: Windows named pipes (`\\.\pipe\csf_semantic`) for fast communication
- **Async CHS indexing**: Background thread for chat history indexing, non-blocking requests
- **Automatic FAISS refresh**: Incremental FAISS index updates every 10 minutes idle (prevents staleness)
- **Concurrent request handling**: ThreadPoolExecutor with configurable workers
- **Auto-start client**: Client automatically starts daemon if not running
- **Graceful fallback**: Falls back to direct backend calls on daemon failure

### Search Scopes

| Scope   | Description                                                           |
| ------- | --------------------------------------------------------------------- |
| `cks`   | Constitutional Knowledge System (memories, patterns, code, knowledge) |
| `chs`   | Chat History Search (conversation history, context)                   |
| `plans` | Plan Search (implementation plans from .claude/plans/)                |

## Usage

### Starting the Daemon

```python
from daemons.unified_semantic_daemon import UnifiedSemanticDaemon

# Create and start daemon
daemon = UnifiedSemanticDaemon(pipe_name=r"\\.\pipe\csf_semantic", num_workers=4)
if not daemon.start():
    print("Failed to start daemon")

# Daemon runs in background thread, handling requests via named pipe
```

### Using the Client

Two client options are available:

#### 1. SemanticClient (Low-Level)

```python
from daemons.unified_semantic_daemon import SemanticClient

# Create client (auto-connects to daemon)
client = SemanticClient()

# Search using scope parameter
results = client.search("cks", "async patterns", limit=5)
results = client.search("chs", "conversation topic", limit=10)

# Returns: {"scope": "cks"/"chs", "results": [...], ...}
```

**Use SemanticClient when:**

- Direct daemon communication is needed
- You don't need auto-start functionality
- You want minimal overhead

#### 2. DaemonClient (High-Level)

```python
from daemons.daemon_client import DaemonClient

# Create client with auto-start and fallback
client = DaemonClient(
    auto_start=True,      # Auto-start daemon if not running
    enable_fallback=True, # Fall back to direct backend on failure
    timeout=30.0
)

# Search using backend parameter
results = client.search("cks", "async patterns", limit=5)
results = client.search("chs", "conversation topic", limit=10)

# Query generic daemon actions (skill_intent, classify_intent)
result = client.query(
    "skill_intent",
    {"command": "from src.rca import SimpleRCAEngine", "skill": "rca"}
)
if result["status"] == "success":
    match = result["result"].get("match", False)

# Returns normalized format:
# {
#   "status": "success",
#   "count": N,
#   "results": [...],
#   "backend": "cks"/"chs",
#   "query": "...",
#   "timing_seconds": N
# }
```

**Use DaemonClient when:**

- You want auto-start functionality
- You need fallback to direct backend
- You prefer normalized response format

**Key Differences:**

| Feature          | SemanticClient                     | DaemonClient                                                    |
| ---------------- | ---------------------------------- | --------------------------------------------------------------- |
| Auto-start       | ❌ No                              | ✅ Yes                                                          |
| Fallback         | ❌ No                              | ✅ Yes                                                          |
| Response format  | `{"scope": ..., "results": [...]}` | `{"status": ..., "backend": ..., "count": N, "results": [...]}` |
| Timeout handling | Manual                             | Built-in retries                                                |
| Use case         | Direct control                     | Production resilience                                           |

### Standalone Daemon Process

```bash
# Run as standalone process
cd P:/__csf/src
python -m daemons.unified_semantic_daemon --verbose

# With custom workers
python -m daemons.unified_semantic_daemon --workers 4
```

## Wire Protocol

The daemon uses a **length-prefixed JSON** protocol for communication:

**Request Format:**

```
[4 bytes: little-endian length][JSON payload]
```

**Response Format:**

```
[4 bytes: little-endian length][JSON payload]
```

**Example:**

```python
import struct
import json

# Client sends:
request = {"scope": "cks", "query": "test", "limit": 5}
data = json.dumps(request).encode("utf-8")
message = struct.pack("<I", len(data)) + data
# Send: [0x00000015][{"scope":"cks",...}]

# Daemon responds:
response_data = json.dumps({"results": [], "scope": "cks"}).encode("utf-8")
response = struct.pack("<I", len(response_data)) + response_data
```

**Important:** Both `SemanticClient` and `DaemonClient` handle this protocol automatically. Direct implementation is only needed for custom clients.

## Async CHS Indexing

The daemon implements async CHS indexing to prevent blocking during model loading:

**How it works:**

1. First CHS search spawns background indexing thread
2. Request handler returns immediately (non-blocking)
3. Model loading (~2.5s) happens in background
4. Indexing progress: 0→100 messages in ~1 second
5. Subsequent searches use cached index

**Key logs:**

- `CHS not indexed, spawning background indexing thread`
- `Background CHS indexing started`
- `Background CHS indexing complete`

**Threading primitives:**

- `_chs_index_thread`: Background indexing thread
- `_chs_index_complete`: Threading.Event signaling completion
- `_chs_indexing`: Boolean flag to prevent concurrent indexing

## Skill Intent Endpoint

The daemon provides a `skill_intent` action for semantic validation of skill command execution.

**Purpose**: Validates whether a command matches the expected execution pattern for a skill using embedding similarity.

**Request format:**

```python
{
    "action": "skill_intent",
    "command": "from src.rca import SimpleRCAEngine",
    "skill": "rca"
}
```

**Response format:**

```python
{
    "match": True,           # True if similarity >= 0.75
    "similarity": 0.87,      # Maximum similarity score (0.0-1.0)
    "threshold": 0.75        # Similarity threshold used
}
```

**Usage from client:**

```python
from daemons.daemon_client import DaemonClient

client = DaemonClient(auto_start=True, enable_fallback=True)
result = client.query(
    "skill_intent",
    {"command": "python -m src.rca.simple_rca_engine", "skill": "rca"}
)
```

**Supported skills:** `rca`, `truth`, `ask-olymp` (see `SKILL_COMMAND_EXAMPLES` in `unified_semantic_daemon.py`)

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (loaded lazily on first use)

## Constants

| Constant                | Value                   | Purpose                             |
| ----------------------- | ----------------------- | ----------------------------------- |
| `PIPE_NAME`             | `\\.\pipe\csf_semantic` | Default named pipe                  |
| `STARTUP_TIMEOUT`       | 6.0s                    | Max wait for daemon ready           |
| `REQUEST_TIMEOUT`       | 5.0s                    | Per-request timeout                 |
| `IDLE_SHUTDOWN_TIMEOUT` | Time-based              | Disabled until 9pm, then 30 minutes |

### Time-Based Idle Timeout

The daemon uses time-based idle timeout to balance availability and resource usage:

- **Before 9pm (21:00)**: Idle timeout disabled, daemon runs indefinitely
- **9pm or later**: Idle timeout = 30 minutes (1800 seconds)

This ensures the daemon stays available during active work hours and auto-shuts down at night to free resources.

**Override**: Use `--idle-timeout` argument to manually set idle timeout (0 = disabled, >0 = seconds).

### Dynamic Pipe Names and Discovery File

The daemon generates dynamic pipe names to avoid Windows stale handle problems:

**Problem**: After daemon crash, Windows retains stale pipe handles, preventing new daemons from using the same pipe name.

**Solution**: Generate unique pipe names per daemon instance using PID and timestamp.

**Pipe name format**: `\\.\pipe\csf_semantic_{PID}_{timestamp}`

Example: `\\.\pipe\csf_semantic_12345_1769657446`

**Discovery File**: `P:/__csf/data/semantic_daemon_discovery.json`

Clients read this file to find the current daemon's dynamic pipe name.

**Discovery file format**:

```json
{
  "pipe_name": "\\\\.\\pipe\\csf_semantic_12345_1769657446",
  "pid": 12345,
  "timestamp": 1769657446
}
```

**Client auto-discovery**:

- `SemanticClient` and `DaemonClient` automatically read discovery file
- If discovery file doesn't exist, clients fall back to hardcoded `PIPE_NAME`
- `SessionStart_semantic_daemon.py` hook also uses discovery file

**Constants**:
| Constant | Value | Purpose |
|----------|-------|---------|
| `DISCOVERY_FILE` | `P:/__csf/data/semantic_daemon_discovery.json` | Discovery file path |
| `FAISS_UPDATE_INTERVAL` | `600.0` (10 minutes) | FAISS auto-refresh idle interval |
| `FAISS_INDEX_PATH` | `P:/__csf/data/chat_history_faiss_424k` | FAISS index location |
| `FAISS_STATE_PATH` | `P:/__csf/data/chs_index_state.json` | FAISS incremental state |
| `FAISS_LOCK_PATH` | `P:/__csf/.data/daemon/faiss_update.lock` | Multi-terminal FAISS update lock |

## FAISS Index Management

### Current Status (V2 Schema)

- **Database**: `P:/__csf/data/chat_history.db` (v2 schema)
- **Messages**: 389,332 messages indexed
- **Turns**: 133,231 turn pairs
- **Sessions**: 2,008 sessions
- **FTS5 Tables**: `messages_fts`, `turns_fts` (BM25 ranking)

### Data Topology

| Data Type | Location | Owner |
|-----------|----------|-------|
| **Source** | `~/.claude/history.jsonl` (2.7GB) | Claude Code system |
| **Derived (SQLite)** | `P:/__csf/data/chat_history.db` | Project-managed |
| **Derived (FAISS)** | `P:/__csf/data/chat_history_faiss_424k` | Project-managed (legacy) |

**Important**: The source data (`~/.claude/history.jsonl`) is system-owned and never moved. The derived indexes are project-managed.

### Manual Reindex

When reindex is needed (schema update, corruption, or initial setup):

```bash
cd P:/packages/search-research
PYTHONPATH=P:/packages/search-research/core python -m core.chs.scripts.reindex_from_jsonl
```

This will:
- Read from `~/.claude/history.jsonl` (~465k entries)
- Create/replace `P:/__csf/data/chat_history.db` with v2 schema
- Populate `messages`, `turns`, and FTS5 tables
- Extract plain text from complex message structures

### Post-Reindex Verification

```bash
# 1. Check database record counts
python -c "
import sqlite3
conn = sqlite3.connect('P:/__csf/data/chat_history.db')
print('messages:', conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0])
print('turns:', conn.execute('SELECT COUNT(*) FROM turns').fetchone()[0])
print('messages_fts:', conn.execute('SELECT COUNT(*) FROM messages_fts').fetchone()[0])
print('turns_fts:', conn.execute('SELECT COUNT(*) FROM turns_fts').fetchone()[0])
"

# 2. Test FTS5 search directly
PYTHONPATH=P:/packages/search-research/core python -c "
from core.chs.db import get_connection
conn = get_connection('P:/__csf/data/chat_history.db')
cursor = conn.execute('''
    SELECT m.role, SUBSTR(m.content, 1, 80)
    FROM messages_fts
    INNER JOIN messages m ON messages_fts.rowid = m.id
    WHERE messages_fts MATCH \"cognitive steering framework\"
    LIMIT 3
''')
for row in cursor: print(f'  [{row[0]}] {row[1]}...')
"
```

### Scheduled Rebuild

The current scheduled task runs daily at 4am to rebuild indexes. This ensures:
- Fresh embeddings for new messages
- Incremental updates via watermark state
- FTS5 index maintenance for SQLite

## Staleness Half-Lives

Knowledge entry types have different staleness half-lives (in days):

| Type         | Half-Life |
| ------------ | --------- |
| `memory`     | 180 days  |
| `correction` | 365 days  |
| `pattern`    | 120 days  |
| `learning`   | 730 days  |
| `code`       | 90 days   |
| `insight`    | 365 days  |

## Migration Status

Migration from `__csf.nip` to `__csf` is **complete**. The daemon uses `__csf` paths exclusively:

```python
def _get_chs_db_path(self) -> Path:
    """Get path to chat history SQLite database.
    Migration from __csf.nip to __csf is complete.
    """
    # Use __csf location
    return _csf_root / "data" / "chat_history.db"
```

## Testing

Test files for concurrent search, async indexing, and zombie cleanup:

| Test File                   | Purpose                                     |
| --------------------------- | ------------------------------------------- |
| `test_concurrent_search.py` | Verify 8 concurrent searches with 4 workers |
| `test_async_indexing.py`    | Verify non-blocking CHS indexing            |
| `test_zombie_cleanup.py`    | Verify discovery file cleanup prevents zombie accumulation |

**Test Results (w1t6):**

- Concurrent search: 8/8 completed, 5193ms avg
- Async indexing: Non-blocking, background thread spawns correctly
- Zombie cleanup (2026-02-08): 3/3 passed - no zombie accumulation after multiple daemon cycles

## Platform Support

- **Windows**: Full support with named pipes (pywin32 required)
- **Linux/macOS**: Not supported (named pipes are Windows-specific)

## Dependencies

```
pywin32  # Windows named pipe support
cks      # Constitutional Knowledge System
```

## Known Issues

| Issue                              | Status   | Solution                                  |
| ---------------------------------- | -------- | ----------------------------------------- |
| Pipe "All pipe instances are busy" | ✅ Fixed | Dynamic pipe names + stale daemon cleanup |
| Model loading blocks first search  | ✅ Fixed | Async indexing (background thread)        |
| ConnectNamedPipe blocking forever  | ✅ Fixed | Overlapped I/O with timeout               |
| Zombie daemon accumulation         | ✅ Fixed | Discovery file cleanup + pipe connectivity test |
| Blue console flash / typing capture on Windows startup | ✅ Fixed | Fully detached startup with `pythonw.exe` + `DEVNULL` stdio |

## Windows Console Flash Fix

**Problem**: The daemon auto-start path could briefly show a blue console window and interfere with typing in Claude Code on Windows.

**Root cause**: The keep-alive wrapper and daemon startup chain were not fully detached from the active console. The wrapper was launched with `python.exe` and inherited terminal handles, including `stdin`.

**Fix** (2026-03-14):

- `daemon_client.py` now launches the keep-alive wrapper with `pythonw.exe` on Windows
- Both startup hops now set `stdin`, `stdout`, and `stderr` to `subprocess.DEVNULL`
- Both startup hops now set `close_fds=True`

**Operator action**: Restart any existing daemon processes so new launches use the fixed behavior.

```powershell
Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -match 'src\.daemons\.daemon_keep_alive' -or
    $_.CommandLine -match 'src\.daemons\.unified_semantic_daemon'
  } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

See: `P:/__csf/docs/semantic_daemon_console_flash_typing_issue.md`

## Zombie Daemon Prevention

**Problem**: Multiple daemon processes running with inaccessible named pipes, wasting memory (6GB+) and violating single-daemon requirement.

**Root Cause**: Discovery file was being deleted by stale-file cleanup even when the daemon was still running, causing new sessions to spawn duplicate daemons.

**Solution** (implemented 2026-02-14):

1. **Aggressive cleanup wired into startup flow** (`SessionStart_semantic_daemon.py`):
   - `_kill_stale_daemons_aggressive()` now called BEFORE `is_daemon_running()`
   - Kills all pythonw processes running `unified_semantic_daemon.py` except the one in discovery file
   - Ensures cleanup happens while discovery file is still intact

2. **Smart discovery file staleness check** (`SessionStart_semantic_daemon.py:158-217`):
   - `_cleanup_stale_discovery_file()` now checks if daemon is actually running before deleting
   - Only removes discovery files if: file is stale (>5 min) AND daemon is not running
   - Prevents deleting discovery files for healthy long-running daemons

3. **Discovery file cleanup on shutdown** (`unified_semantic_daemon.py:930-960`):
   - Added `_cleanup_discovery_file()` method
   - Called in `stop()` method with PID validation
   - Prevents stale discovery files from accumulating

4. **Crash cleanup via atexit** (`unified_semantic_daemon.py:3300-3315`):
   - `atexit.register(cleanup_on_exit)` for abnormal termination
   - Signal handlers also call cleanup
   - Ensures cleanup even on crashes

5. **Client-side pipe connectivity test** (`daemon_client.py:45-88`):
   - `_is_pipe_accessible()` tests pipe before trusting discovery file
   - `_read_discovery_pipe_name()` cleans stale files automatically
   - Prevents connecting to zombie daemons with dead pipes

**Multi-terminal safe**: Uses Windows Named Mutex (`Global\CSF_NIP_SemanticDaemon_Startup`) for cross-process synchronization to prevent race conditions when multiple terminals start simultaneously.

**Verification**: Manual testing confirms:
- Only one daemon runs per session
- Existing daemon is preserved on new session start
- Old daemons are automatically killed
- No accumulation of zombie processes

## Server Loop Architecture

The daemon uses **overlapped I/O** for non-blocking pipe connections:

```python
# Create overlapped structure for non-blocking ConnectNamedPipe
overlapped = pywintypes.OVERLAPPED()
overlapped.hEvent = win32event.CreateEvent(None, True, False, None)

while self._running:
    win32event.ResetEvent(overlapped.hEvent)
    win32pipe.ConnectNamedPipe(self._pipe_handle, overlapped)

    # Wait with 1-second timeout
    result = win32event.WaitForSingleObject(overlapped.hEvent, 1000)

    if result == win32event.WAIT_TIMEOUT:
        self.check_idle_work()  # CHS indexing, FAISS updates
        continue  # Check self._running flag

    # Handle client connection...
```

**Why Overlapped I/O?**

- Blocking `ConnectNamedPipe` waits indefinitely with no client
- Daemon thread becomes unresponsive (no idle work, no shutdown)
- Overlapped I/O allows 1-second timeouts for:
  - Idle work execution (CHS reindex, FAISS updates)
  - Shutdown signal response (`self._running = False`)
  - Health monitoring

**Pipe Creation Flags:**

```python
win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED
```

## Related Systems

- **CKS**: `from cks import CKS` - Knowledge system backend
- **CHS**: `from modules.chat_search.chat_search import ChatHistorySearcher`
- **Search**: `from search.unified_router import EnhancedUnifiedSearchRouter`

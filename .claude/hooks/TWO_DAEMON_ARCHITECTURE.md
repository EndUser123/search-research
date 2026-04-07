# Daemon Architecture

**Last Updated**: 2026-04-06
**Status**: Production (2 active daemons)
**Implementation Plan**: `plan-20260308-two-daemon-architecture.md`

---

## Overview

The daemon architecture enables multiple specialized background services to run concurrently without interference.

**Active Daemons:**
1. **Dreaming daemon** — Analyzes principle-events.jsonl to generate insights
2. **Semantic daemon** — Provides fast semantic search for CKS and CHS via Windows named pipes

**Inactive:**
- **Search daemon** — Configured but never implemented. The `--daemon-type search` option runs identical code to `--daemon-type dreaming` with no differentiation. Hook disabled in SessionStart.py.

**Why This Matters:**
- Dreaming daemon analyzes behavioral patterns from principle-events
- Semantic daemon provides vector search for knowledge retrieval
- Both can run simultaneously without WinError 32 file corruption or mutex conflicts

**Key Features:**
- Type-specific mutex enforcement (one instance per daemon type)
- Separate PID, state, and log files per daemon
- Backward compatible (default behavior unchanged)
- Configurable via `DAEMON_TYPES` in `config/daemon_config.py`

---

## Daemon Types

### Dreaming Daemon

**Purpose**: Async background service that analyzes principle-events.jsonl to generate insights and patterns.

**Resources:**
- **Mutex**: `Global\ClaudeInsightDaemon`
- **PID File**: `state/dreaming-daemon.pid`
- **State File**: `state/dreaming-daemon-state.json`
- **Log File**: `logs/dreaming-daemon.log`

**Data Flow:**
```
P:/.claude/logs/principle-events.jsonl (input)
    ↓
Dreaming daemon analyzes events (async tailing)
    ↓
P:/.claude/state/dreaming-insights.json (output)
P:/.claude/state/dreaming-insights.md (human-readable)
```

**Architecture:**
- Windows mutex + PID file for singleton enforcement
- Offset-based JSONL tailing with rotation detection
- Sliding window aggregation (1-hour default)
- Heartbeat for health monitoring (90s threshold)
- Zombie detection and cleanup (180s timeout)

### Search Daemon

**Purpose**: (INACTIVE) Was planned to manage search operations and indexing for semantic search.

**Resources:**
- **Mutex**: `Global\ClaudeSearchDaemon`
- **PID File**: `state/search-daemon.pid`
- **State File**: `state/search-daemon-state.json`
- **Log File**: `logs/search-daemon.log`

**Status**: Configuration exists but daemon never built. The `--daemon-type search` option runs identical code to `--daemon-type dreaming` with no behavioral differentiation. Hook disabled in SessionStart.py.

### Semantic Daemon

**Purpose**: Provides fast semantic search for CKS and CHS via Windows named pipes.

**Resources:**
- **Mutex**: `Global\CSF_Semantic_Daemon_Startup`
- **Discovery File**: `data/semantic_daemon_discovery.json`
- **Named Pipe**: `\\.\pipe\csf_nip_semantic_{PID}_{timestamp}`

**Architecture:**
- Named pipe server (`unified_semantic_daemon.py`) avoids Windows stale handles
- Clients auto-start daemon if not running via `DaemonClient`
- Fallback to direct SentenceTransformer (`all-MiniLM-L6-v2`) when daemon unavailable
- 5-minute idle timeout unloads model to free memory

**Startup Integration:**
- `SessionStart_semantic_daemon.py` auto-starts daemon on session begin
- Multi-terminal coordination via Windows mutex with randomized backoff
- Health check verifies daemon responds before declaring ready

**Key Fix (2026-04-06)**: Added `stdin=subprocess.DEVNULL` to daemon startup to prevent Windows subprocess hang.

---

## Configuration

### DAEMON_TYPES Structure

Located in `config/daemon_config.py`:

```python
DAEMON_TYPES: Dict[DaemonType, Dict[str, str]] = {
    "dreaming": {
        "mutex_name": "Global\\ClaudeInsightDaemon",
        "pid_file": "dreaming-daemon.pid",
        "state_file": "dreaming-daemon-state.json",
        "daemon_log": "dreaming-daemon.log",
    },
    "search": {
        "mutex_name": "Global\\ClaudeSearchDaemon",
        "pid_file": "search-daemon.pid",
        "state_file": "search-daemon-state.json",
        "daemon_log": "search-daemon.log",
    },
}
```

### Adding New Daemon Types

To add a new daemon type:

1. **Add to DAEMON_TYPES** in `config/daemon_config.py`:
   ```python
   "your_daemon": {
       "mutex_name": "Global\\YourDaemonMutex",
       "pid_file": "your-daemon.pid",
       "state_file": "your-daemon-state.json",
       "daemon_log": "your-daemon.log",
   }
   ```

2. **Use get_daemon_config()** to retrieve configuration:
   ```python
   from config.daemon_config import get_daemon_config
   config = get_daemon_config("your_daemon")
   # Returns: {'mutex_name': 'Global\\YourDaemonMutex', ...}
   ```

3. **Pass mutex_name** to `acquire_singleton()`:
   ```python
   from dreaming_mutex import acquire_singleton
   acquire_singleton(pid_file, config["mutex_name"], state_file)
   ```

---

## Usage

### Starting Daemons

**Default (backward compatible):**
```bash
# Starts dreaming daemon by default
python dreaming-daemon.py
```

**Explicit daemon type:**
```bash
# Start dreaming daemon
python dreaming-daemon.py --daemon-type dreaming

# Start search daemon (when implemented)
python dreaming-daemon.py --daemon-type search
```

### SessionStart Hook Integration

The `SessionStart_dreaming_daemon.py` and `SessionStart_semantic_daemon.py` hooks automatically start their respective daemons when a Claude Code session begins.

**Health Checks:**
- Heartbeat-based (90s threshold) for dreaming daemon
- Named pipe connectivity + health query for semantic daemon
- Auto-start if daemon is unhealthy or missing
- Multi-terminal coordination via Windows mutex with randomized backoff
- Latency monitoring and instrumentation

**Manual hook invocation:**
```bash
# Test the dreaming daemon hook
python SessionStart_dreaming_daemon.py

# Test the semantic daemon hook
python SessionStart_semantic_daemon.py
```

### Manual Testing

**Terminal 1: Start dreaming daemon**
```bash
python dreaming-daemon.py --daemon-type dreaming
```

**Terminal 2: Start search daemon** (future)
```bash
python dreaming-daemon.py --daemon-type search
```

**Terminal 3: Verify singleton enforcement**
```bash
# This should fail - dreaming daemon already running
python dreaming-daemon.py --daemon-type dreaming
# Expected: "Daemon is already running (PID XXXXX)"
```

---

## File Paths

### Location

All daemon files are located under `P:\.claude\hooks\`:

```
P:\.claude\hooks\
├── dreaming_daemon.py                  # Dreaming daemon script (handles dreaming/search types)
├── SessionStart_dreaming_daemon.py    # Dreaming daemon auto-start hook
├── SessionStart_semantic_daemon.py    # Semantic daemon auto-start hook
├── config/
│   └── daemon_config.py                # DAEMON_TYPES configuration (dreaming + search)
├── state/
│   ├── dreaming-daemon.pid             # Dreaming daemon PID
│   ├── dreaming-daemon-state.json      # Dreaming daemon state
│   ├── search-daemon.pid               # Search daemon PID (inactive)
│   └── search-daemon-state.json        # Search daemon state (inactive)
└── logs/
    ├── dreaming-daemon.log             # Dreaming daemon logs
    └── search-daemon.log               # Search daemon logs (inactive)

Semantic daemon lives in the search-research package:
P:\packages\search-research\
├── src\daemons\unified_semantic_daemon.py  # Named pipe server
├── data\semantic_daemon_discovery.json     # Daemon discovery file
└── core\chs\embeddings.py                  # Embedding client with fallback
```

### State File Structure

**dreaming-daemon-state.json:**
```json
{
  "pid": 12345,
  "start_time": "2026-03-08T10:30:00Z",
  "last_event_offset": 1048576,
  "heartbeat": "2026-03-08T10:31:00Z",
  "zombie_cleanup_count": 0,
  "events_processed": 42
}
```

**Fields:**
- `pid`: Process ID of running daemon
- `start_time`: ISO 8601 timestamp when daemon started
- `last_event_offset`: Byte offset in principle-events.jsonl for resume capability
- `heartbeat`: Last heartbeat timestamp (health check)
- `zombie_cleanup_count`: Number of zombie daemons cleaned up
- `events_processed`: Total events analyzed since start

---

## Troubleshooting

### Common Issues

#### Issue 1: Daemon won't start

**Symptoms:**
```
Failed to start daemon: [Errno 13] Permission denied
```

**Diagnosis:**
1. Check if daemon is already running:
   ```bash
   # Check PID file exists
   cat P:\.claude\hooks\state\dreaming-daemon.pid

   # Check if process is alive
   ps aux | grep dreaming-daemon
   ```

2. Check mutex status:
   - On Windows, use Process Explorer to search for `Global\ClaudeInsightDaemon`

**Solutions:**
- If daemon is dead but PID file exists, delete PID file and retry
- If mutex is stale, reboot Windows to clear named mutexes
- Check log file for errors: `logs/dreaming-daemon.log`

#### Issue 2: Multiple daemons running

**Symptoms:**
```
Daemon is already running (PID XXXXX)
```

**Diagnosis:**
```bash
# List all daemon processes
ps aux | grep dreaming-daemon

# Check PID files
ls -la P:\.claude\hooks\state/*daemon*.pid
```

**Solutions:**
- This is expected behavior - singleton enforcement is working
- If you need to restart, kill existing daemon first:
  ```bash
  kill $(cat P:\.claude\hooks\state\dreaming-daemon.pid)
  ```

#### Issue 3: Zombie daemon detected

**Symptoms:**
```
Zombie daemon detected - cleaning up stale mutex and PID file
```

**Diagnosis:**
- State file has stale heartbeat (>180s old)
- Process listed in PID file is not running
- Mutex exists but no process owns it

**Solutions:**
- Daemon auto-cleanup will handle this (T-009 zombie detection)
- Manual cleanup if needed:
  ```bash
  # Kill stale process if still running
  ps aux | grep dreaming-daemon | awk '{print $2}' | xargs kill

  # Remove stale state files
  rm P:\.claude\hooks\state\dreaming-daemon.pid
  rm P:\.claude\hooks\state\dreaming-daemon-state.json

  # Restart daemon
  python dreaming-daemon.py
  ```

#### Issue 4: Heartbeat timeout

**Symptoms:**
```
Daemon unhealthy - heartbeat 195s old (exceeds 90s threshold)
```

**Diagnosis:**
- Daemon is stuck or hung
- System is under heavy load
- principle-events.jsonl is locked by another process

**Solutions:**
1. Check daemon log for errors:
   ```bash
   tail -n 50 P:\.claude\hooks\logs\dreaming-daemon.log
   ```

2. Check upstream data source:
   ```bash
   # Check if events file is being updated
   ls -la P:\.claude\hooks\logs\principle-events.jsonl
   ```

3. Restart daemon if needed:
   ```bash
   kill $(cat P:\.claude\hooks\state\dreaming-daemon.pid)
   python dreaming-daemon.py
   ```

#### Issue 5: Invalid daemon type

**Symptoms:**
```
Unknown daemon type: 'invalid'. Valid types are: 'dreaming', 'search'
```

**Diagnosis:**
- Typo in `--daemon-type` parameter
- Configuration file missing or corrupted

**Solutions:**
- Check spelling: `--daemon-type dreaming` (not `dreaming-daemon`)
- Verify config exists: `config/daemon_config.py`
- Check DAEMON_TYPES dictionary has your daemon type

---

## Architecture Details

### Singleton Enforcement

**Problem**: Prevent multiple instances of the same daemon type from running simultaneously.

**Solution**: Windows named mutex + PID file dual enforcement.

**How It Works:**
1. Daemon startup calls `acquire_singleton(pid_file, mutex_name, state_file)`
2. `_create_windows_mutex()` attempts to create named mutex:
   - Success → We're the first instance, continue startup
   - ERROR_ALREADY_EXISTS → Another instance is running, exit with error
3. PID file provides secondary enforcement (check if process is alive)

**Mutex Names:**
- Dreaming: `Global\ClaudeInsightDaemon`
- Search: `Global\ClaudeSearchDaemon`

**Why "Global\" prefix?**
- Windows named mutexes without "Global\" are session-local
- "Global\" makes mutex system-wide (all sessions, all terminals)
- Prevents cross-terminal race conditions

### Zombie Detection (T-009)

**Problem**: Stale mutex + PID file when daemon crashes without cleanup.

**Solution**: Heartbeat-based zombie detection before mutex acquisition.

**How It Works:**
1. Check if state file exists
2. If heartbeat >180s old, daemon is zombie
3. Verify PID from state file is not running
4. Clean up stale state files
5. Proceed with normal startup

**Timeout Configuration:**
- `DEFAULT_HEARTBEAT_INTERVAL = 60` seconds
- `DEFAULT_ZOMBIE_TIMEOUT = 180` seconds

### Multi-Terminal Coordination (Phase 2)

**Problem**: Multiple terminals opening simultaneously race to start daemon.

**Solution**: Windows mutex with randomized backoff.

**How It Works:**
1. Terminal A checks daemon → not running
2. Terminal B checks daemon → not running (A hasn't finished yet)
3. Both try to create startup mutex: `Global\ClaudeDaemonStartup`
4. Terminal A gets mutex, starts daemon
5. Terminal B sees mutex exists, waits 50-150ms with jitter
6. Terminal B checks again → daemon is now running
7. Both terminals continue without duplicate daemons

**Jitter Benefits:**
- Prevents synchronized retry collisions
- Random 50-150ms delay desynchronizes attempts
- Max 3 retries with exponential backoff (50ms, 100ms, 150ms)

---

## Testing

### Unit Tests

```bash
# Run two-daemon architecture tests
pytest P:\.claude\hooks\tests\test_two_daemon_architecture.py -v

# Run daemon CLI tests
pytest P:\.claude\hooks\tests\test_dreaming_daemon_cli.py -v

# Run semantic daemon tests
pytest P:\.claude\hooks\tests\test_semantic_daemon_health.py -v
```

**Test Coverage:**
- Configuration system (10 tests)
- Mutex differences (2 tests)
- Path differences (3 tests)
- Backward compatibility (1 test)
- CLI argument parsing (5 tests)

### Integration Tests

**Manual testing procedure:**
1. Start dreaming daemon in terminal 1
2. Start search daemon in terminal 2
3. Verify both are running (check PID files)
4. Try to start second dreaming daemon in terminal 3 (should fail)
5. Verify log files show correct daemon types

**Success criteria:**
- Both daemons run simultaneously
- Second dreaming daemon is rejected
- Log files are separate
- No WinError 32 errors

---

## Backward Compatibility

**Breaking Changes**: NONE

All changes are backward compatible:
- Default `--daemon-type` is "dreaming"
- Existing `dreaming-daemon.pid` files continue working
- Optional parameters with sensible defaults
- Clear error messages for misconfiguration

**Migration**: Not required - existing daemons work as before.

---

## Performance

**Startup Latency:**
- Dreaming daemon: ~100ms on modern machines
- Health check: <10ms (cached state)
- Mutex acquisition: <5ms

**Runtime Overhead:**
- Heartbeat updates every 60s
- JSONL tailing with offset (no full file reads)
- Sliding window aggregation (O(window_size), not O(total_events))

**Multi-Terminal Coordination:**
- Max total wait: ~500ms (100ms + jitter) × 3 attempts
- Typical wait: <100ms (first attempt succeeds)

---

## Related Documentation

- **Implementation Plan**: `plan-20260308-two-daemon-architecture.md`
- **Daemon Configuration**: `config/daemon_config.py`
- **Dreaming Daemon**: `dreaming_daemon.py`
- **SessionStart Hook**: `SessionStart_dreaming_daemon.py`
- **Semantic Daemon**: `SessionStart_semantic_daemon.py`

---

## Changelog

### 2026-04-06 - Daemon Architecture Cleanup

**Changed:**
- Renamed from "Two-Daemon Architecture" to "Daemon Architecture" (reflects actual state)
- Documented semantic daemon as active (third daemon, separate from dreaming)
- Marked search daemon as INACTIVE (configured but never built, code identical to dreaming)
- Updated file path documentation to include search-research package location
- Added semantic daemon resources (mutex, discovery file, named pipe)
- Added `stdin=subprocess.DEVNULL` fix documentation (prevents Windows subprocess hang)

**Fixed:**
- Search daemon entry: was "configuration complete, implementation pending" → "configured but never built"
- Added missing semantic daemon startup integration documentation

### 2026-03-08 - Two-Daemon Architecture

**Added:**
- DAEMON_TYPES configuration in `config/daemon_config.py`
- `get_daemon_config(daemon_type)` function
- `--daemon-type` CLI argument to `dreaming_daemon.py`
- Configurable mutex names in `dreaming_mutex.py`
- Comprehensive test suite (10+ tests)
- Two-daemon architecture documentation

**Changed:**
- `acquire_singleton()` accepts `mutex_name` parameter
- `dreaming_daemon.py` builds paths from DAEMON_TYPES config
- Logging includes daemon type in messages

**Backward Compatible:**
- Default `--daemon-type` is "dreaming"
- Existing dreaming daemon behavior unchanged
- No migration required

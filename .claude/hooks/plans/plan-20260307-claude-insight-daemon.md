# Implementation Plan: Claude Insight Daemon

**Created:** 2026-03-07
**Status:** READY-FOR-IMPLEMENTATION (verification passed, improvements integrated)
**Priority:** MEDIUM
**Last Updated:** 2026-03-07 (pre-mortem integration + verification improvements)

## Objective

Build a Windows-friendly background daemon that analyzes `principle-events.jsonl` from the principle monitoring hook to generate machine-readable insights about behavioral patterns over time.

**Key Design Decisions:**
- **Use existing principle_monitor.py** (no new Stop hook needed)
- **ctypes for mutex** (no pywin32 dependency)
- **JSON config** (simple, no extra deps)
- **Machine-readable insights first** (JSON schema + optional markdown)
- **Simple and robust** (no OS-level file locking, skip partial lines)

---

## Kill Criteria (Pre-Commit Abandonment Thresholds)

**Before starting implementation**, these criteria trigger immediate project reassessment:

**Time-Based Kill Criteria:**
- □ "If I spend more than 4 hours on this without a working daemon that processes JSONL, reconsider"
- □ "If 2026-03-21 passes without daemon successfully generating insights from real JSONL data, abandon or pivot"

**Value-Based Kill Criteria:**
- □ "If I can't explain the value proposition of daemon analysis vs manual log review in one sentence, stop"
- □ "If grep/less manual log review is faster than using the daemon insights, it's not solving the problem"

**Usage-Based Kill Criteria:**
- □ "If I don't use the insights myself after 2 weeks, nobody else will"
- □ "If I never check the insights JSON file even once during active development, the workflow isn't integrated"

**Technical Kill Criteria:**
- □ "If mutex zombie state isn't fixable in 2 hours, the approach is wrong"
- □ "If SessionStart slowdown >1 second, the architecture is wrong"

**Anti-Pattern**: "I'll know when to stop." Solo devs are terrible at knowing when to stop. These criteria are defined dispassionately BEFORE starting, not when emotionally invested.

---

## 1. Problem Statement

The principle monitoring system (`principle_monitor.py`) successfully logs behavioral violations to JSONL, but lacks automated analysis of patterns over time. Users must manually review logs to identify trends such as:

- Which principles are violated most frequently
- Sessions with high violation rates
- Temporal patterns (e.g., violation spikes during certain activities)

**Current Gap:**
- No automated insights from accumulated violation data
- No trend analysis across sessions
- No detection of systemic patterns

**Desired State:**
- Background daemon continuously analyzes JSONL logs
- Machine-readable insights generated on configurable schedule
- Human-readable markdown optionally available
- Windows-friendly with single-instance enforcement

---

## 2. Context Analysis

### System Architecture

The Claude Insight Daemon extends the existing principle monitoring system:

```
[Stop Hook] principle_monitor.py
        ↓ (writes)
[P:/.claude/logs/principle-events.jsonl]
        ↓ (reads via offset)
[dreaming-daemon.py]
        ↓ (generates)
[P:/.claude/state/dreaming-insights.json] (machine-readable)
[P:/.claude/state/dreaming-insights.md] (human-readable)
```

### Allowed APIs

**From existing codebase:**

1. **principle_monitor.py constants** (lines 26-37):
   - `LOG_PATH = Path("P:/.claude/logs/principle-events.jsonl")`
   - `STATE_PATH = Path("P:/.claude/state/behavior-counters.json")`
   - `EVENT_TO_PRINCIPLE` mapping (4 event types)

2. **JSONL format** (confirmed from actual log file):
   ```json
   {
     "ts": "2026-03-07T14:22:42.491609+00:00",
     "session_id": "test-session-123",
     "event_type": "change_without_evidence",
     "principle": "grounded_changes",
     "assistant_preview": "You're right about that."
   }
   ```

3. **Windows mutex patterns** (from SessionStart_semantic_daemon.py):
   - `ctypes.windll.kernel32.CreateMutexW`
   - `ERROR_ALREADY_EXISTS = 183`
   - Global mutex naming: `Global\\ClaudeInsightDaemon`

4. **JSONL tailing patterns** (from shared_utils.py):
   - Offset tracking with `f.seek(offset)` and `f.tell()`
   - Rotation detection via `f.stat().st_size < last_size`
   - Error handling: skip malformed lines, log warnings

### Anti-Patterns to Avoid

1. **Don't invent new event types** - Use only the 4 existing types from `EVENT_TO_PRINCIPLE`
2. **Don't add OS-level file locking** - Skip partial lines instead (simple and robust)
3. **Don't use pywin32** - Use ctypes (built-in, no external dependency)
4. **Don't create new Stop hook** - Reuse existing `principle_monitor.py` output
5. **Don't block principle_monitor** - Daemon is read-only, never interferes with hook

### Technical Constraints

- **Platform:** Windows-only (uses Windows global mutex)
- **Python:** 3.12+ (matches existing codebase)
- **Dependencies:** Python standard library only (ctypes, json, pathlib, dataclasses)
- **File paths:** Aligned with existing structure (`P:/.claude/state/`, `P:/.claude/logs/`)
- **Hook compatibility:** Must not slow down Stop hook (read-only, async processing)

---

## 3. Existing Implementation Discovery

### Current System Components

1. **principle_monitor.py** (275 lines)
   - Location: `P:\.claude/hooks/principle_monitor.py`
   - Function: Detects 4 behavioral principle violations in Stop hook responses
   - Output: JSONL log at `P:/.claude/logs/principle-events.jsonl`
   - State: Per-session violation counters at `P:/.claude/state/behavior-counters.json`
   - Threshold: Emits suggestion at 5 violations per principle per session
   - **Status:** Production-ready, 33/33 tests passing, fully integrated

2. **Test Suite** (422 lines)
   - Location: `P:\.claude\hooks\tests\test_principle_monitor.py`
   - Coverage: All detection patterns with positive/negative/edge cases
   - **Status:** Complete, all tests pass

3. **Hook Registration**
   - File: `P:\.claude\settings.json` (lines 183-186)
   - Event: Stop hook
   - Timeout: 2 seconds
   - **Status:** Active and working

### JSONL Log Format

**Confirmed structure from actual log file:**
```json
{
  "ts": "2026-03-07T14:22:42.491609+00:00",
  "session_id": "test-session-123",
  "event_type": "change_without_evidence",
  "principle": "grounded_changes",
  "assistant_preview": "You're right about that."
}
```

**Event types (from EVENT_TO_PRINCIPLE mapping):**
- `context_grounding_violation` → `context_reuse`
- `change_without_evidence` → `grounded_changes`
- `redundant_broad_question` → `minimal_redundancy`
- `opaque_uncertainty` → `transparent_uncertainty`

### Integration Points

1. **Log reader** - Daemon reads `P:/.claude/logs/principle-events.jsonl` (append-only by hook)
2. **State manager** - Daemon writes `P:/.claude/state/dreaming-state.json` (heartbeat, offset)
3. **Insights writer** - Daemon writes `P:/.claude/state/dreaming-insights.{json,md}`
4. **SessionStart hook** - Checks daemon health, starts if needed (state file only, no mutex)

---

## 4. Test Discovery

### Required Test Scenarios

Based on existing patterns from `test_principle_monitor.py`:

**Unit Tests:**
1. **Config loading** - Default values, file creation, validation
2. **Mutex acquisition** - Single-instance enforcement, ERROR_ALREADY_EXISTS handling
3. **JSONL tailing** - Offset tracking, rotation detection, partial line handling
4. **Event aggregation** - Time window filtering, principle counting
5. **Insights generation** - Pattern detection, JSON schema validation
6. **State management** - Heartbeat updates, offset persistence

**Integration Tests:**
1. **Concurrent hook + daemon** - Verify no data loss during concurrent write/read
2. **Malformed JSON handling** - Verify daemon skips partial lines without crashing
3. **Log rotation** - Verify daemon detects rotation and resets offset
4. **Multi-session startup** - Verify only one daemon runs when multiple terminals start

**Error Path Tests:**
1. **Missing log file** - Daemon handles FileNotFoundError gracefully
2. **Corrupted state file** - Daemon recovers or creates fresh state
3. **Mutex contention** - Multiple SessionStart hooks race to start daemon
4. **Stale heartbeat** - SessionStart detects dead daemon and starts new one

### Test Patterns from Existing Codebase

**From test_principle_monitor.py:**
- Use `pytest` with fixtures for sample data
- Mock stdin/stdout for hook testing
- Patch file paths for isolated testing
- Test both positive and negative cases
- Include edge cases (empty strings, whitespace, malformed input)

**From test_semantic_daemon_health.py:**
- Subprocess testing for daemon lifecycle
- PID verification and cleanup
- Health check validation
- Named pipe connectivity testing

---

## 5. Proposed Solution

### Architecture Overview

**Three-component system:**

1. **dreaming-daemon.py** - Background daemon process
   - Enforces single-instance via Windows global mutex
   - Tails JSONL log using byte offset tracking
   - Aggregates events in sliding time window
   - Generates insights (JSON + optional markdown)
   - Updates heartbeat in state file

2. **SessionStart_dreaming_daemon.py** - Hook to start/monitor daemon
   - Checks heartbeat freshness in state file
   - Starts daemon if stale or missing
   - Never touches mutex (daemon enforces single-instance)
   - Benign race: multiple SessionStart hooks may start daemon, but only one wins mutex

3. **dreaming_config.json** - Configuration file
   - JSON format (no YAML dependency)
   - Defaults created on first run
   - Tunable parameters (poll interval, window size, thresholds)

### Data Flow

```
[principle_monitor.py hook]
  Stop event → detect violation → append to JSONL
                                      ↓
[P:/.claude/logs/principle-events.jsonl] (append-only, 1 writer)
                                      ↓
[dreaming-daemon.py] (read-only, offset-based tailing)
  Read new lines → aggregate in window → generate insights
                                      ↓
[P:/.claude/state/dreaming-insights.json] (machine-readable)
[P:/.claude/state/dreaming-insights.md] (human-readable)
```

### Concurrency Policy

**Simple and robust approach (no OS-level locks):**

- **principle-events.jsonl**:
  - Writer: Stop hook (append-only)
  - Reader: Daemon (offset-based)
  - Race handling: Daemon skips JSON decode errors (partial lines), retries next cycle

- **dreaming-state.json**:
  - Writer: Daemon only (heartbeat, offset)
  - Reader: SessionStart hook (health check)
  - Race handling: SessionStart treats parse errors as "unknown state", lets mutex decide

- **dreaming-insights.{json,md}**:
  - Writer: Daemon only
  - Readers: User, tools
  - No concurrent writes (single daemon)

### Key Features

1. **Single-Instance Enforcement**
   - Windows global mutex: `Global\\ClaudeInsightDaemon`
   - Daemon exits immediately if mutex already held
   - SessionStart never touches mutex (daemon is authority)

2. **Offset-Based Log Tailing**
   - Track last processed byte offset in state file
   - Detect log rotation (file size shrinks)
   - Reset offset on rotation

3. **Sliding Window Aggregation**
   - Configurable time window (default: 60 minutes)
   - Count events per principle
   - Detect patterns (top principle, high-violation sessions, spikes)

4. **Machine-Readable Insights**
   - JSON schema with dataclasses
   - Optional markdown generation
   - Timestamps for freshness

5. **Health Monitoring**
   - Heartbeat updated every poll cycle
   - SessionStart checks heartbeat age (< 90 seconds = healthy)
   - Daemon logs to `dreaming-daemon.log`

---

## 6. Implementation Plan

### Phase 1: Core Infrastructure (Priority: HIGH)

**Task 1.1: Config System**
- File: `P:/.claude/hooks/dreaming_config.py`
- Actions:
  - Define `DEFAULT_CONFIG` dict with all parameters
  - Implement `load_config(path: Path) -> dict`
  - Create default config if file missing
  - Use JSON only (no YAML, no Pydantic)
- Acceptance Criteria:
  - Config file created at first run
  - Missing keys use defaults
  - Invalid JSON falls back to defaults
- Verification: `python -c "from dreaming_config import load_config; print(load_config(Path('test.json')))"`
- Effort: S

**Task 1.2: Windows Mutex + PID File (Hybrid Approach)**
- File: `P:/.claude/hooks/dreaming_mutex.py`
- Actions:
  - **[OPTIMIZED] Implement hybrid single-instance detection**:
    1. **Primary: PID file** (`dreaming-daemon.pid`):
       - Write PID on startup (atomic write to tmp + rename)
       - Lock PID file using `msvcrt.locking()` (exclusive access, non-blocking)
       - If lock succeeds → no other daemon running, we're the instance
       - If lock fails → another daemon holds lock, exit immediately
    2. **Secondary: Windows mutex** (fallback/enforcement):
       - Try `CreateMutexW` with name `Global\\ClaudeInsightDaemon`
       - If `ERROR_ALREADY_EXISTS` (183), verify PID file PID matches our process
       - If PIDs don't match → stale mutex from crashed daemon, log and acquire
       - Use mutex as "anti-tamper" (prevents manual mutex creation, but PID file is authority)
    3. **Zombie prevention**:
       - PID file locked → daemon alive
       - On crash: OS releases file lock automatically (no manual cleanup needed)
       - New daemon checks lock, not mutex (more reliable)
  - Implement `acquire_singleton() -> (bool, str)` returns (success, error_msg)
  - Implement `release_singleton() -> None` unlocks PID file, closes mutex
  - Implement `is_instance_running() -> bool` checks PID file lock
  - Copy-ready patterns from SessionStart_semantic_daemon.py (lines 54-90 for health check)
- Acceptance Criteria:
  - PID file lock acquisition returns True/False (atomic, no race)
  - Mutex used as enforcement layer, not primary detection
  - Stale mutex detected (PID mismatch) and recovered
  - No external dependencies (ctypes, msvcrt are built-in)
- **[OPTIMIZED] Zombie-proof**: PID file lock releases on crash (OS handles cleanup)
- Verification: Start daemon, kill process, verify new daemon acquires lock
- Effort: M

**Task 1.3: State Management**
- File: `P:/.claude/hooks/dreaming_state.py`
- Actions:
  - Implement `DreamingState` dataclass (PID, offset, heartbeat_ts)
  - Implement `load_state(path: Path) -> DreamingState`
  - Implement `save_state(state: DreamingState, path: Path)`
  - Handle missing/corrupted state files gracefully
- Acceptance Criteria:
  - Missing file returns default state
  - Corrupted JSON creates fresh state
  - Heartbeat updates are atomic
- Verification: `python -c "from dreaming_state import load_state, save_state; s = load_state(Path('test.json')); s.heartbeat_ts = time.time(); save_state(s, Path('test.json'))"`
- Effort: S

### Phase 2: JSONL Tailing (Priority: HIGH)

**Task 2.1: Offset-Based Log Reader + Rotation Policy**
- File: `P:/.claude/hooks/dreaming_tailer.py`
- Actions:
  - Implement `JSONLTailer` class (offset tracking, rotation detection)
  - Implement `read_new_events() -> Iterator[dict]`
  - Skip JSON decode errors (partial lines)
  - Detect rotation (file size < last_size)
  - **[OPTIMIZED] Implement time-based log rotation** (preserves temporal granularity):
    - **Rotation policy**: Rotate JSONL when >50MB
    - **Time-based partitioning** (no compaction, no data loss):
      1. When file exceeds 50MB, rename with date suffix: `principle-events-2026-03-07.jsonl`
      2. Start fresh `principle-events.jsonl` for new events
      3. Keep all raw events in daily/weekly files (full temporal resolution preserved)
      4. Tailer tracks offset across partitioned files (maintain reading position)
      5. Optional: Generate aggregate stats to `principle-events-aggregates.jsonl` if needed for long-term storage
    - **Partition management**:
      - Config: `ROTATION_SIZE_THRESHOLD` (default 50MB)
      - Config: `ROTATION_PARTITION_BY` (default "daily" | "weekly")
      - Config: `ROTATION_RETENTION_DAYS` (default 30, delete partitions older than N days)
      - Tailer discovery: Scan partition directory for newest JSONL file on startup
    - **Offset tracking across partitions**:
      - State file stores: `{"current_file": "principle-events-2026-03-07.jsonl", "offset": 12345}`
      - On rotation: Reset offset to 0, update current_file to new partition
      - On startup: Detect newest partition, resume from saved offset
- Copy-ready code from documentation discovery
- Acceptance Criteria:
  - Returns only new lines since last offset
  - Skips malformed lines without crashing
  - Resets offset on file rotation
  - Logs warnings for skipped lines
  - **[OPTIMIZED] JSONL file never exceeds 100MB** (rotation enforced)
  - **[OPTIMIZED] All raw events preserved** (no aggregation, full temporal resolution)
  - **[OPTIMIZED] Time-series analysis possible** (per-event timestamps maintained)
  - **[OPTIMIZED] Old partitions cleaned up** (retention policy enforced)
- Verification: Write test JSONL with partial line, verify tailer skips it
- **[OPTIMIZED] Partition verification**: Create 60MB JSONL, rotate, verify:
  1. Old file renamed with date suffix (e.g., `principle-events-2026-03-07.jsonl`)
  2. New `principle-events.jsonl` created (empty, ready for new events)
  3. State file updated with new current_file and offset=0
  4. Tailer resumes reading from correct position across partitions
  5. Optional aggregates file created if enabled
  6. Partitions older than retention period deleted
- Effort: M

**Task 2.2: Event Aggregation**
- File: `P:/.claude/hooks/dreaming_aggregator.py`
- Actions:
  - Implement `InsightsGenerator` class (sliding window)
  - Implement `add_event(event: dict)` (prunes old events)
  - Implement `generate_insights() -> DreamingInsights`
  - Use 4 principle types from `EVENT_TO_PRINCIPLE`
- Acceptance Criteria:
  - Time window filters events correctly
  - Counts events per principle
  - Detects top violated principle
  - Detects high-violation sessions (>10 violations)
- Verification: Generate 50 events, verify insights show correct counts
- Effort: M

### Phase 3: Insights Generation (Priority: HIGH)

**Task 3.1: Insights Schema**
- File: `P:/.claude/hooks/dreaming_insights.py`
- Actions:
  - Define `PrincipleStats` dataclass
  - Define `Pattern` dataclass
  - Define `DreamingInsights` dataclass
  - Implement `to_markdown() -> str` method
  - Use `dataclasses.asdict()` for JSON serialization
- Acceptance Criteria:
  - JSON output validates against schema
  - Markdown output is human-readable
  - All fields have type hints
- Verification: `python -c "from dreaming_insights import DreamingInsights; import json; print(json.dumps(DreamingInsights.__dataclass_fields__))"`
- Effort: M

**Task 3.2: Insights Writer**
- File: `P:/.claude/hooks/dreaming_writer.py`
- Actions:
  - Implement `write_insights(insights: DreamingInsights, config: dict)`
  - Write JSON to `state/dreaming-insights.json`
  - Optionally write markdown to `state/dreaming-insights.md`
  - Use `Path.write_text()` with atomic writes (tmp + replace)
- Acceptance Criteria:
  - JSON file is valid and parseable
  - Markdown file is generated if configured
  - Writes are atomic (no partial writes)
- Verification: Run daemon, verify both files created with valid content
- Effort: S

### Phase 4: Daemon Main Loop (Priority: HIGH)

**Task 4.1: Daemon Core**
- File: `P:/.claude/hooks/dreaming-daemon.py`
- Actions:
  - **[OPTIMIZED] Implement async daemon loop** (consistent with existing codebase patterns):
    - Use `async def main()` with `asyncio.run()` entry point
    - Async operations: file I/O (aiofiles), JSON parsing, state loading
    - Rationale: I/O-bound operations (file reading, JSON parsing) benefit from async
    - Consistency: 19 existing files in codebase use async patterns
  - **Main loop sequence** (poll, read, aggregate, write, sleep):
    1. Acquire mutex + PID file lock on startup (sync, before async loop)
    2. Load state, get offset, start tailer (async file I/O)
    3. Enter infinite async loop:
       - Read new events from JSONL tailer (async)
       - Aggregate events (sync, CPU-bound)
       - Generate insights (sync, CPU-bound)
       - Write insights to JSON/MD (async file I/O)
       - Update heartbeat timestamp (sync)
       - Sleep for poll interval (asyncio.sleep)
  - **Signal handling** (Windows-specific, see Task 4.2):
    - Register signal handlers before async loop starts
    - Use `atexit` for cleanup on normal exit
    - Set shutdown flag for graceful async loop termination
- Acceptance Criteria:
  - Only one daemon runs at a time (mutex + PID file lock)
  - Daemon processes new events within poll interval
  - Heartbeat updated each cycle
  - Graceful shutdown on SIGTERM/SIGINT
  - **[OPTIMIZED] Async operations used for I/O-bound work** (file reads/writes)
  - **[OPTIMIZED] Consistent with existing codebase async patterns** (19 files use asyncio)
- Verification: Start daemon, verify mutex prevents second instance
- **[OPTIMIZED] Async verification**: Monitor event loop, verify:
  1. File I/O operations use async (aiofiles)
  2. No blocking calls in async loop (no time.sleep, no sync file I/O)
  3. Concurrent operations run in parallel where appropriate
- Effort: L

**Task 4.2: Error Handling + Reliable Cleanup**
- File: `P:/.claude/hooks/dreaming-daemon.py`
- Actions:
  - Wrap all I/O in try/except (file operations, JSON parsing)
  - Log errors to `dreaming-daemon.log`
  - Never crash on parse errors (skip and retry)
  - Implement exponential backoff on repeated errors
  - **[OPTIMIZED] Windows-specific reliable cleanup** (signal handlers unreliable on Windows):
    - **Problem**: SIGTERM/SIGINT handlers on Windows are unreliable for cleanup (platform limitation)
    - **Solution: Multi-layered cleanup approach**:
      1. **Primary: `atexit` handler** (fires on normal exit, most reliable)
         - Release mutex handle via `CloseHandle()`
         - Release PID file lock via `msvcrt.locking()`
         - Save final state with shutdown timestamp
      2. **Secondary: Periodic refresh check** (in main loop)
         - Check shutdown flag every poll interval
         - If set, save state and exit cleanly
         - Allows external trigger (e.g., touch `dreaming-daemon.stop` file)
      3. **Tertiary: Best-effort signal handlers** (SIGTERM, SIGINT)
         - Register via `signal.signal()` but don't rely on them
         - Set shutdown flag, let periodic check handle cleanup
         - Fallback to `atexit` if signals don't fire
    - **Zombie detection** (startup check):
      1. On startup, attempt mutex acquisition via `CreateMutexW`
      2. If `ERROR_ALREADY_EXISTS` (183), load state file
      3. Check heartbeat freshness: `now - heartbeat_ts > 180 seconds` = stale
      4. If mutex held AND heartbeat stale → zombie detected
      5. Log warning, attempt to acquire mutex again (Windows may auto-cleanup)
      6. If second acquisition fails → manual intervention required (log explicit instructions)
  - **[OPTIMIZED] Atomic heartbeat + state update** (prevent race condition):
    - **Problem**: Heartbeat update isn't atomic with state save → concurrent access can miss fresh daemon
    - **Solution**: Single atomic write operation for heartbeat + state
      - Use `write_text()` with full state dict including current timestamp
      - State structure: `{"offset": 12345, "heartbeat": "2026-03-07T12:34:56Z", "current_file": "principle-events-2026-03-07.jsonl", "shutdown": false}`
      - Update heartbeat AND state in one write (no separate heartbeat write)
      - Prevents stale check reading old heartbeat while daemon is alive
    - **Config option**: `DAEMON_HEARTBEAT_INTERVAL_SECONDS` (default 60, how often to update heartbeat)
    - **Config option**: `DAEMON_ZOMBIE_TIMEOUT_SECONDS` (default 180, how long before considered stale)
- Acceptance Criteria:
  - Daemon continues running after malformed JSON
  - Daemon continues after log rotation
  - Daemon continues after config file errors
  - All errors logged with context
  - **[OPTIMIZED] Mutex zombie detected and prevented** (new daemon can start after kill)
  - **[OPTIMIZED] Reliable cleanup on Windows** (atexit + periodic refresh, not just signal handlers)
  - **[OPTIMIZED] Heartbeat + state atomic** (no race condition in freshness check)
  - **[OPTIMIZED] Zombie detection logged with clear instructions** (if auto-recovery fails)
- Verification: Inject various error conditions, verify daemon recovers
- **[OPERATIONAL VERIFICATION REQUIRED]** Test with actual daemon kill:
  1. Start daemon, verify mutex acquired
  2. Kill daemon process (taskkill /PID)
  3. Try starting new daemon immediately (zombie scenario)
  4. Verify new daemon detects zombie (ERROR_ALREADY_EXISTS + stale heartbeat)
  5. Verify new daemon acquires mutex (auto-recovery or manual cleanup)
  6. Provide test output showing zombie detection and recovery
- **[OPTIMIZED] Test Windows cleanup reliability**:
  1. Start daemon, verify mutex + PID file lock acquired
  2. Kill daemon process (taskkill /PID) → simulates crash
  3. Verify OS releases file lock automatically (new daemon can acquire)
  4. Verify mutex released or detected as stale (PID file mismatch)
  5. Test normal shutdown: send SIGTERM, verify atexit cleanup fires
  6. Test periodic refresh: create `dreaming-daemon.stop` file, verify daemon shuts down
- **[OPTIMIZED] Test atomic heartbeat**:
  1. Start daemon, monitor heartbeat + state updates
  2. Verify single write operation updates both heartbeat and state
  3. Verify no separate heartbeat file (atomic with state)
  4. Verify SessionStart reads consistent state (no race condition)
- Effort: M

### Phase 5: SessionStart Hook (Priority: MEDIUM)

**Task 5.1: Health Check Hook + Latency Measurement**
- File: `P:/.claude/hooks/SessionStart_dreaming_daemon.py`
- Actions:
  - Load config and state
  - Check heartbeat age (< 90 seconds = healthy)
  - If stale/missing, start daemon via `subprocess.Popen`
  - Use `pythonw.exe` on Windows (no console window)
  - Use `CREATE_NO_WINDOW` flag
  - Print `{}` to stdout (hook protocol)
  - **[NEW] Measure and log latency** (detect slowdown early):
    - Track time to load and check state file
    - Log latency if >50ms, >100ms thresholds
    - Add `LATENCY_WARNING_THRESHOLD` to config (default 100ms)
  - **[OPTIMIZED] Check upstream data source health** (detect principle_monitor.py failure):
    - Check `principle-events.jsonl` modification time
    - If file exists but no new events for >10 minutes → upstream may have stopped
    - Log warning: "No new principle events for {age} minutes - principle_monitor may not be running"
    - Add `UPSTREAM_IDLE_WARNING_MINUTES` to config (default 10)
    - Don't auto-fix (principle_monitor is Stop hook, can't restart it)
    - Purpose: Alert user to upstream monitoring gap, not silent failure
- Acceptance Criteria:
  - Daemon started if missing
  - Daemon started if heartbeat stale
  - No new daemon if healthy
  - Hook exits within 2 seconds
  - **[NEW] State file read latency <100ms** (measured)
  - **[OPTIMIZED] Upstream idle warning logged** (no new events for >10 minutes)
- Verification: Run SessionStart with stale heartbeat, verify daemon starts
- **[OPERATIONAL VERIFICATION REQUIRED]** Measure actual latency:
  1. Run SessionStart hook 100 times with fresh state file
  2. Measure mean, max, p95 latency
  3. Verify p95 <100ms
  4. Provide latency measurements in test results
- **[OPTIMIZED] Test upstream monitoring**:
  1. Stop principle_monitor.py (disable hook)
  2. Generate some events, then stop
  3. Run SessionStart hook after 10+ minutes
  4. Verify warning logged: "No new principle events for X minutes"
  5. Verify warning includes actionable guidance (check principle_monitor hook)
- Effort: M
- Verification: Run SessionStart with stale heartbeat, verify daemon starts
- **[OPERATIONAL VERIFICATION REQUIRED]** Measure actual latency:
  1. Run SessionStart hook 100 times with fresh state file
  2. Measure mean, max, p95 latency
  3. Verify p95 <100ms
  4. Provide latency measurements in test results
- Effort: M

### Phase 6: Testing (Priority: MEDIUM)

**Task 6.1: Unit Tests**
- File: `P:/.claude/hooks/tests/test_dreaming_daemon.py`
- Actions:
  - Test config loading (defaults, file creation, validation)
  - Test mutex acquisition (single-instance enforcement)
  - Test JSONL tailing (offset tracking, rotation, partial lines)
  - Test event aggregation (windowing, counting, patterns)
  - Test insights generation (schema validation, markdown output)
  - Test state management (load, save, corruption recovery)
- Use `pytest` with fixtures
- Acceptance Criteria:
  - All tests pass
  - Coverage > 80% for core modules
  - Edge cases tested (empty files, malformed JSON, rotation)
- Verification: `pytest P:/.claude/hooks/tests/test_dreaming_daemon.py -v`
- Effort: L

**Task 6.2: Integration Tests + Operational Verification**
- File: `P:/.claude/hooks/tests/test_dreaming_integration.py`
- Actions:
  - **[OPERATIONAL VERIFICATION REQUIRED]** Test malformed JSON with ACTUAL partial lines (not mocks)
  - **[OPERATIONAL VERIFICATION REQUIRED]** Test log rotation with ACTUAL file truncation
  - **[OPERATIONAL VERIFICATION REQUIRED]** Test mutex cleanup with ACTUAL daemon kill (not simulated)
  - **[OPERATIONAL VERIFICATION REQUIRED]** Measure SessionStart latency with actual state file reads
  - Test concurrent hook write + daemon read
  - Test multi-session startup (only one daemon wins mutex)
- Use subprocess to run daemon
- Acceptance Criteria:
  - No data loss during concurrent operations
  - Daemon recovers from all error scenarios
  - Only one daemon runs at a time
  - **[OPERATIONAL VERIFICATION]** Malformed JSON lines skipped without crash (actual partial line in file)
  - **[OPERATIONAL VERIFICATION]** Rotation detected and offset reset (actual file truncation)
  - **[OPERATIONAL VERIFICATION]** Mutex released after daemon kill (actual process termination)
  - **[OPERATIONAL VERIFICATION]** SessionStart latency <100ms (measured with actual state file)
- Verification: Run integration tests, verify all pass
- **Operational Verification Gate**: Before marking task complete, provide actual test output showing:
  1. Malformed JSON line content + daemon log showing "skipped partial line"
  2. Log rotation command + daemon state showing offset reset to 0
  3. Daemon kill command + subsequent successful mutex acquisition
  4. SessionStart latency measurements (mean, max, p95)
- Effort: L

**Task 6.3: 1-Week Pilot Usage Verification**
- Actions:
  - Run daemon for 1 week during active development
  - **[NEW] Track insights file access** (manual method):
    1. Create `P:/.claude/state/insights-access-log.txt` (manual diary)
    2. Each time you read insights JSON file: Log timestamp + reason
       - Example: `"2026-03-07T14:30:00Z - Checked if opaque_uncertainty increased"`
    3. Each time tools read insights file: Log timestamp + tool name
       - Example: `"2026-03-07T15:00:00Z - /code skill read insights for context"`
    4. **Daily check**: Review access log, verify ≥1 entry/day
  - **[NEW] Alternative: Windows file access logging** (optional, requires admin):
    1. Enable Windows audit logging: `auditpol /set /Object Access /Success /Enabled`
    2. Check event log for `dreaming-insights.json` access events
    3. Export daily: `wevtutil qe Security /c:1 /f:text > access-log.txt`
  - Measure latency impact on SessionStart
  - Verify insights show actual behavioral patterns (not "no data")
- Acceptance Criteria:
  - **[NEW] Insights access log has ≥7 entries** (at least 1/day for 1 week)
  - **[NEW] At least 3 different access reasons logged** (not just repetitive checks)
  - SessionStart latency <100ms measured
  - Insights show non-zero violation counts
  - User confirms insights influenced workflow (even once)
- Verification:
  - **[NEW] Provide access log excerpt showing 7+ entries with varied reasons**
  - User confirmation + access logs
- **Kill criterion check**: If access log has <3 entries after 1 week, daemon is not integrated into workflow → fail "usage-based" kill criterion
- Effort: M (blocking task for DONE certification)

### Phase 7: Documentation & Cleanup (Priority: LOW)

**Task 7.1: Documentation**
- File: `P:/.claude\hooks\plans\plan-20260307-claude-insight-daemon.md`
- Actions:
  - Document architecture and data flow
  - Document configuration options
  - Document JSONL format and event types
  - Document insights schema
  - Add troubleshooting section
- Acceptance Criteria:
  - User can understand system from docs
  - User can configure daemon from docs
  - User can debug issues from docs
- Verification: Peer review of documentation
- Effort: M

**Task 7.2: Cleanup**
- Actions:
  - Remove debug prints
  - Consolidate duplicate code
  - Add type hints to all functions
  - Add docstrings to all modules
  - Run `ruff` and `mypy`
- Acceptance Criteria:
  - `ruff check` passes
  - `mypy` passes (strict mode)
  - All modules have docstrings
  - All public functions have type hints
- Verification: `ruff check P:/.claude/hooks/dreaming_*.py && mypy P:/.claude/hooks/dreaming_*.py`
- Effort: S

---

## 7. Risks, Success Criteria, Dependencies

### Risks and Mitigations

**Original Risks:**

| Risk | Severity | Likelihood | Cascade Depth | Mitigation |
|------|----------|------------|---------------|------------|
| **Daemon crashes on malformed JSON** | HIGH | MEDIUM | Shallow (2 steps) | Skip partial lines, log warnings, retry next cycle (Task 2.1, 4.2) |
| **Multiple daemons start simultaneously** | MEDIUM | HIGH | Shallow (2 steps) | Global mutex enforcement, only one wins (Task 1.2, 4.1) |
| **Log rotation causes data loss** | MEDIUM | LOW | Shallow (2 steps) | Detect rotation via file size, reset offset (Task 2.1) |
| **State file corruption prevents startup** | MEDIUM | LOW | Shallow (2 steps) | Graceful degradation, create fresh state on corruption (Task 1.3, 4.2) |
| **Daemon grows memory unbounded** | LOW | MEDIUM | Medium (3 steps) | Sliding window aggregation, prune old events (Task 2.2) |
| **SessionStart hook slows down session start** | LOW | LOW | Medium (4 steps) | Hook only checks state file, never waits for mutex (Task 5.1) |

**Fix Side Effects (NEW risks from proposed daemon solution):**

| Risk | Severity | Likelihood | Cascade Depth | Mitigation |
|------|----------|------------|---------------|------------|
| **SessionStart slowdown** (4-step cascade) | MEDIUM | MEDIUM | Medium (4 steps) | Measure latency baseline in Task 6.2, target <100ms for state check alone |
| **Unbounded JSONL growth** (4-step cascade) | HIGH | MEDIUM | Deep (5 steps) | Add log rotation policy to Task 2.1, prune/compact old events |
| **Daemon orphaned via mutex zombie** (6-step cascade) | HIGH | LOW | **Deep (6 steps)** | Add mutex health check + cleanup in Task 4.2, test with actual daemon kill |

**Cascade Traces (for fix side effects):**

1. **SessionStart slowdown**:
   - First order: SessionStart hook reads state file every session
   - Second order: State file grows large (heartbeat history accumulates)
   - Third order: File read time increases (>100ms, then >500ms)
   - Fourth order: User notices session start delay, disables daemon hook
   - **CASCADE DEPTH: MEDIUM (4 steps)**

2. **Unbounded JSONL growth**:
   - First order: JSONL log file grows without rotation
   - Second order: Daemon tailing slows down (seek/read larger file)
   - Third order: Insights generation takes longer (>1s, then >5s)
   - Fourth order: Daemon falls behind real-time, insights are stale
   - Fifth order: User stops trusting insights, daemon becomes abandoned
   - **CASCADE DEPTH: DEEP (5 steps)** → Boost to HIGH priority

3. **Daemon orphaned via mutex zombie**:
   - First order: Daemon crashes (exception, killed, system shutdown)
   - Second order: Global mutex remains held (Windows doesn't auto-cleanup)
   - Third order: New daemon instances blocked (ERROR_ALREADY_EXISTS)
   - Fourth order: SessionStart assumes daemon is running (state file exists)
   - fifth order: No insights generated, stale state file misleads health checks
   - Sixth order: User thinks daemon is broken, abandons system entirely
   - **CASCADE DEPTH: DEEP (6 steps)** → Boost to HIGH priority

### Success Criteria

**Functional:**
1. Daemon runs continuously and processes new JSONL events
2. Only one daemon instance runs at a time (mutex enforcement)
3. Insights generated reflect recent behavioral patterns
4. JSON insights are machine-readable and parseable
5. Markdown insights are human-readable (optional)
6. Daemon recovers from all error scenarios without crashing
7. SessionStart hook starts daemon if missing or stale
8. **[NEW] Workflow integration - insights are actually used in development**

**Non-Functional:**
1. Daemon CPU usage < 5% (poll-based, not busy-wait)
2. Daemon memory usage < 50MB (sliding window limits events)
3. Daemon startup time < 2 seconds (SessionStart timeout)
4. SessionStart latency impact < 100ms (state file read only)
5. JSONL tailing keeps up with hook write rate
6. Insights generation time < 1 second (per cycle)
7. **[NEW] JSONL log file rotation policy implemented (prevent unbounded growth)**

**Quality:**
1. Test coverage > 80% for core modules
2. All tests pass (unit + integration)
3. `ruff` linting passes with zero warnings
4. `mypy` type checking passes (strict mode)
5. Documentation is complete and accurate
6. **[NEW] Mutex zombie cleanup tested (daemon kill scenario)**
7. **[NEW] 1-week pilot completed to verify insights are actually used**

### Dependencies

**Internal:**
1. **principle_monitor.py** - Must be active and logging JSONL
2. **settings.json** - Hook registration for SessionStart
3. **P:/.claude/logs/** - Directory must exist (created by hook)
4. **P:/.claude/state/** - Directory must exist (created by hook)

**External:**
1. **Python 3.12+** - For dataclasses, type hints, pathlib
2. **Windows OS** - For global mutex (ctypes.windll.kernel32)
3. **pytest** - For test suite (development dependency only)

**No PyPI packages required** - Uses Python standard library only.

### Rollback Strategy

**If daemon causes issues:**
1. Unregister SessionStart hook from `settings.json`
2. Kill daemon process (if running)
3. Delete `P:/.claude/hooks/dreaming-daemon.py`
4. Delete `P:/.claude/hooks/SessionStart_dreaming_daemon.py` entry from settings.json
5. Principle monitoring continues unaffected (daemon is read-only)

**Principle monitoring is unaffected by daemon issues** - daemon only reads JSONL, never writes.

---

## Top Risks

**After pre-mortem cascade analysis, these are the highest priorities:**

1. **[RISK:9] Daemon orphaned via mutex zombie** - CASCADE: DEEP (6 steps)
   - Prevent: Mutex health check + cleanup in Task 4.2, test with actual daemon kill
   - Warning: New daemon instances fail to start with ERROR_ALREADY_EXISTS
   - Owner: Implementation phase

2. **[RISK:9] Unbounded JSONL growth** - CASCADE: DEEP (5 steps)
   - Prevent: Add log rotation policy to Task 2.1, prune/compact old events
   - Warning: JSONL file > 100MB, daemon tailing slows >1s
   - Owner: Implementation phase

3. **[RISK:6] SessionStart slowdown** - CASCADE: MEDIUM (4 steps)
   - Prevent: Measure latency baseline in Task 6.2, target <100ms for state check
   - Warning: SessionStart latency >100ms, >500ms
   - Owner: Testing phase

**Original top risks (now lower priority after cascade analysis):**
4. Daemon crashes on malformed JSON - Mitigated by skip-and-retry pattern in Task 2.1
5. Memory growth from unbounded event storage - Mitigated by sliding window in Task 2.2
6. Multiple daemons start simultaneously - Mitigated by global mutex in Task 1.2

---

## Warning Signs to Monitor

**During Development (check daily):**
- □ Mutex acquisition fails repeatedly (ERROR_ALREADY_EXISTS when no daemon should be running)
- □ JSONL file growth rate > 10MB/day (indicates missing rotation policy)
- □ SessionStart latency >100ms measured (state file read taking too long)
- □ Daemon memory usage >50MB (sliding window not pruning)

**During Testing (check each test run):**
- □ Mutex zombie state detected (daemon killed but mutex still held)
- □ Malformed JSON causes daemon crash (should skip and continue)
- □ Log rotation causes offset corruption (should reset cleanly)

**During Pilot Week (check daily):**
- □ Insights file never checked (opened/read by user or tools)
- □ Insights file shows "no data" repeatedly (daemon not processing events)
- □ SessionStart hook disabled by user (latency too annoying)

**Anti-Pattern**: "I'll monitor later." These checks must be automated or scheduled NOW, or they won't happen.

---

## Next Actions

1. **Create config system** (Task 1.1): Implement `dreaming_config.py` with JSON loader
2. **Implement mutex** (Task 1.2): Implement `dreaming_mutex.py` with ctypes
3. **Build state manager** (Task 1.3): Implement `dreaming_state.py` with dataclass
4. **Create JSONL tailer** (Task 2.1): Implement `dreaming_tailer.py` with error handling
5. **Build aggregator** (Task 2.2): Implement `dreaming_aggregator.py` with sliding window
6. **Define insights schema** (Task 3.1): Implement `dreaming_insights.py` with dataclasses
7. **Create writer** (Task 3.2): Implement `dreaming_writer.py` for atomic writes
8. **Build daemon** (Task 4.1): Implement `dreaming-daemon.py` main loop
9. **Add error handling** (Task 4.2): Wrap all I/O in try/except
10. **Create SessionStart hook** (Task 5.1): Implement `SessionStart_dreaming_daemon.py`
11. **Write tests** (Task 6.1, 6.2): Unit and integration tests
12. **Final cleanup** (Task 7.1, 7.2): Documentation and linting

**Estimated Total Effort:** 6-8 hours for all phases

---

## Pre-Mortem Integration (2026-03-07)

This plan has been updated with comprehensive pre-mortem analysis including:

**Added Sections:**
1. **Kill Criteria** - Pre-commit abandonment thresholds for solo development
2. **Fix Side Effects** - 3 NEW risks from the proposed daemon solution itself
3. **Cascade Analysis** - Multi-step failure tracing (Shallow/Medium/Deep)
4. **Warning Signs** - 9 leading indicators to monitor during development, testing, and pilot
5. **Operational Verification** - Requirements for empirical evidence before closing risks

**Updated Sections:**
1. **Top Risks** - Re-prioritized based on cascade depth analysis (mutex zombie = HIGH priority)
2. **Success Criteria** - Added workflow integration requirement ("insights actually used")
3. **Task 2.1** - Added log rotation policy (prevent unbounded JSONL growth)
4. **Task 4.2** - Added mutex health check (prevent zombie state)
5. **Task 5.1** - Added latency measurement (detect SessionStart slowdown)
6. **Task 6.2** - Added operational verification gate (require actual test output, not mocks)
7. **Task 6.3** - NEW: 1-week pilot usage verification (block DONE until insights are actually used)

**Pre-Mortem Status:** ⚠️ BLOCKED - REQUIRES OPERATIONAL VERIFICATION AFTER IMPLEMENTATION

The pre-mortem identified critical failure modes that MUST be verified with actual test runs before the daemon can be considered production-ready:
- Mutex zombie cleanup must be tested with actual daemon kill
- Log rotation must be tested with actual file truncation
- SessionStart latency must be measured with actual state file reads
- Workflow integration must be verified by tracking actual insights file usage during 1-week pilot

**Reference Class Forecasting:**
- Base rate: 60% of solo dev daemons abandoned due to lack of workflow integration
- This plan addresses the #1 abandonment reason by adding Task 6.3 (pilot usage verification)
- If insights aren't used during pilot, the project fails the "value-based" kill criterion

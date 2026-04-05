# Implementation Plan: CKS Vector Search Daemon

## Overview

This plan follows TDD (Test-Driven Development) with RED->GREEN->REFACTOR cycles for each component. Implementation is ordered by dependency: daemon first, then launcher, then bridge integration, finally hook update.

## Phase 1: Vector Daemon Core

### Task 1.1: Daemon Skeleton with FastAPI
**File**: P:/__csf.nip/src/cks/vector_daemon.py

**RED** (Write failing test first):
- tests/test_vector_daemon.py::test_daemon_health_endpoint_returns_loading

**GREEN** (Minimal implementation):
- Create FastAPI app
- Add /health endpoint returning status=loading, model_loaded=False

**REFACTOR**: N/A (too simple)

### Task 1.2: Model Loading with Timeout Heartbeat
**File**: P:/__csf.nip/src/cks/vector_daemon.py

**RED**:
- tests/test_vector_daemon.py::test_model_loads_on_startup

**GREEN**:
- VectorDaemon class with load_model() method
- Uses sentence-transformers all-MiniLM-L6-v2
- TimeoutRefresh class tracks last_activity

**REFACTOR**: Extract model config to constants

### Task 1.3: Search Endpoint
**File**: P:/__csf.nip/src/cks/vector_daemon.py

**RED**:
- tests/test_vector_daemon.py::test_search_returns_results

**GREEN**:
- POST /search endpoint
- Encodes query to vector
- Searches FAISS index
- Returns ranked results with similarity scores

**REFACTOR**: Add pagination support

### Task 1.4: Background Heartbeat Thread
**File**: P:/__csf.nip/src/cks/vector_daemon.py

**RED**:
- tests/test_vector_daemon.py::test_daemon_shuts_down_after_timeout

**GREEN**:
- Background thread checks should_shutdown() every 60s
- Calls shutdown() when timeout exceeded
- Thread marked as daemon for auto-cleanup

**REFACTOR**: Make heartbeat interval configurable

## Phase 2: Daemon Launcher

### Task 2.1: State File Management
**File**: P:/__csf.nip/src/cks/daemon_launcher.py

**RED**:
- tests/test_daemon_launcher.py::test_state_file_persists_daemon_info

**GREEN**:
- DaemonState class with save() and load() methods
- Stores PID, port, start_time, model_loaded
- JSON format in P:/__csf.nip/data/daemon.json

**REFACTOR**: Add atomic write (temp file + rename)

### Task 2.2: Process Spawning
**File**: P:/__csf.nip/src/cks/daemon_launcher.py

**RED**:
- tests/test_daemon_launcher.py::test_spawn_creates_daemon_process

**GREEN**:
- spawn() creates subprocess with python -m cks.vector_daemon
- Returns subprocess.Popen object
- Captures stdout/stderr

**REFACTOR**: Add platform-specific handling (Windows vs Unix)

### Task 2.3: Health Check Polling
**File**: P:/__csf.nip/src/cks/daemon_launcher.py

**RED**:
- tests/test_daemon_launcher.py::test_wait_ready_blocks_until_model_loaded

**GREEN**:
- wait_ready() polls /health endpoint
- Returns True when model_loaded=True
- Default 15s timeout with 0.5s poll interval

**REFACTOR**: Add exponential backoff

### Task 2.4: Graceful Shutdown
**File**: P:/__csf.nip/src/cks/daemon_launcher.py

**RED**:
- tests/test_daemon_launcher.py::test_shutdown_sends_signal_to_daemon

**GREEN**:
- shutdown() POSTs to /shutdown endpoint
- Waits for process exit (default 5s timeout)
- Returns True if clean exit, False otherwise

**REFACTOR**: Add force-kill fallback

## Phase 3: CKS Bridge Integration

### Task 3.1: Daemon Client in Bridge
**File**: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py

**RED**:
- tests/test_cks_hybrid.py::test_vector_search_uses_daemon

**GREEN**:
- vector_search() method using DaemonLauncher
- Calls ensure_daemon() if not running
- Returns formatted results

**REFACTOR**: Add caching layer

### Task 3.2: Hybrid Search Implementation
**File**: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py

**RED**:
- tests/test_cks_hybrid.py::test_hybrid_search_combines_results

**GREEN**:
- hybrid_search() merges keyword and vector results
- Deduplicates by entry ID
- Re-ranks with semantic boost

**REFACTOR**: Add configurable weighting (keyword vs vector)

### Task 3.3: Timeout Fallback
**File**: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py

**RED**:
- tests/test_cks_hybrid.py::test_vector_timeout_falls_back_to_keyword

**GREEN**:
- vector_search() wrapped with try/except
- Catches requests.Timeout, DaemonUnavailable
- Returns empty list on error, triggers keyword fallback

**REFACTOR**: Add circuit breaker pattern

## Phase 4: Hook Integration

### Task 4.1: Use Enhanced Bridge in Hook
**File**: P:/.claude/hooks/user_prompt_submit_cks.py

**RED**:
- tests/test_hook_integration.py::test_hook_uses_hybrid_search

**GREEN**:
- Import CKSBridge
- Call hybrid_search() instead of keyword_search
- 2s timeout on vector search

**REFACTOR**: N/A (simple integration)

## Phase 5: Integration & Regression

### Task 5.1: End-to-End Test
**File**: tests/test_integration.py

Test sequence:
1. Verify no daemon running
2. Query triggers spawn
3. Wait for ready state
4. Execute search
5. Verify results returned
6. Verify timeout refresh on activity
7. Verify graceful shutdown

### Task 5.2: Performance Test
**File**: tests/test_performance.py

- test_query_latency_under_100ms: Warm query <100ms
- test_cold_start_under_15s: Daemon ready in <15s
- test_memory_under_500mb: Process RSS <500MB

### Task 5.3: Hook Timeout Test
**File**: tests/test_hook_timeout.py

- test_hook_never_exceeds_3_seconds: Hook completes in <3s

## Phase 6: Quality Gates

### Gate 1: Syntax Validation
python -m py_compile src/cks/vector_daemon.py
python -m py_compile src/cks/daemon_launcher.py
python -m py_compile src/lib/core_utils/claude_code_cks_bridge.py

### Gate 2: Unit Tests
pytest tests/test_vector_daemon.py -v
pytest tests/test_daemon_launcher.py -v
pytest tests/test_hybrid_search.py -v

### Gate 3: Integration Tests
pytest tests/test_integration.py -v
pytest tests/test_performance.py -v

### Gate 4: Manual Verification
- Daemon spawns on first query
- Daemon shuts down after 1h idle (simulate with shorter timeout)
- Hook still works with keyword-only fallback
- No zombie processes after crash

## Rollback Plan

If issues arise:
1. Revert hook to use keyword_search only
2. Disable daemon auto-spawn
3. Keep daemon code for manual testing

## Success Metrics

Metric | Target | Measurement
-------|--------|-------------
Cold start time | <15s | Time from spawn to /health ready
Query latency (warm) | <100ms | Median /search response time
Memory footprint | <500MB | Process RSS after model loaded
Hook success rate | >99% | Hook completions / total attempts
Fallback rate | <5% | Keyword-only searches / total

## Dependencies Check

- sentence-transformers installed
- FastAPI installed
- uvicorn installed
- requests installed
- psutil installed
- P:/__csf.nip/data/ directory exists

## Risk Mitigation

Risk | Mitigation
-----|------------
Model load exceeds 15s | Extend timeout, show progress
Port conflicts | Dynamic port selection
Zombie processes | Signal handlers, force kill fallback
Windows subprocess issues | Use proper shell escaping
Hook timeout exceeded | Aggressive fallback to keyword

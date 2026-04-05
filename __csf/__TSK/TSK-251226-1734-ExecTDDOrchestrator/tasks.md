# Task Decomposition: CKS Vector Search Daemon

## Task Overview

Total estimated tasks: 23
Implementation approach: TDD (RED ? GREEN ? REFACTOR)
Ordering: Dependency-first (daemon ? launcher ? bridge ? hook)

## Phase 1: Vector Daemon Core (5 tasks)

### T-1.1.1: Create vector_daemon.py skeleton
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Create empty module with FastAPI import
- Add app = FastAPI() entry point
- Acceptance: python -m py_compile passes
- Time: 2 min

### T-1.1.2: Add /health endpoint (loading state)
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Implement GET /health returning status=loading, model_loaded=False
- Acceptance: curl localhost:port/health returns JSON
- Time: 3 min

### T-1.2.1: Create TimeoutRefresh class
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Implement refresh() and should_shutdown() methods
- Track last_activity timestamp
- Acceptance: time-based logic works correctly
- Time: 5 min

### T-1.2.2: Implement VectorDaemon.load_model()
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Import sentence-transformers
- Load all-MiniLM-L6-v2 model
- Set model_loaded flag
- Acceptance: model loads without error, health returns ready
- Time: 5 min

### T-1.3.1: Implement POST /search endpoint
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Create SearchRequest pydantic model
- Encode query to vector
- Search FAISS index (using existing CKS index)
- Return ranked results with similarity scores
- Acceptance: Search returns results, refreshes timeout
- Time: 10 min

### T-1.4.1: Implement background heartbeat thread
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Create start_heartbeat() method
- Background thread checks should_shutdown() every 60s
- Call shutdown() when timeout exceeded
- Acceptance: Daemon exits after idle timeout
- Time: 8 min

### T-1.4.2: Add POST /shutdown endpoint
- File: P:/__csf.nip/src/cks/vector_daemon.py
- Manual shutdown trigger
- Clean shutdown (save state, close resources)
- Acceptance: curl POST /shutdown terminates daemon
- Time: 5 min

## Phase 2: Daemon Launcher (6 tasks)

### T-2.1.1: Create daemon_launcher.py module
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- Import dependencies (subprocess, requests, json, psutil)
- Create module skeleton
- Acceptance: python -m py_compile passes
- Time: 2 min

### T-2.1.2: Implement DaemonState class
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- save(pid, port, model_loaded) method
- load() method returning state dict
- Atomic write with temp file
- Acceptance: State persists across reads
- Time: 8 min

### T-2.2.1: Implement spawn() method
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- Find available port on localhost
- Start subprocess: python -m cks.vector_daemon
- Save PID and port to state file
- Acceptance: Process running, state file created
- Time: 10 min

### T-2.2.2: Implement is_running() check
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- Check if PID exists in process list
- Verify /health endpoint responds
- Return boolean
- Acceptance: Accurately detects daemon state
- Time: 5 min

### T-2.3.1: Implement wait_ready() polling
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- Poll /health endpoint
- Wait for model_loaded=True
- Default 15s timeout, 0.5s interval
- Acceptance: Blocks until ready, returns bool
- Time: 5 min

### T-2.4.1: Implement shutdown() method
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- POST to /shutdown endpoint
- Wait for process exit (5s timeout)
- Force kill if unresponsive
- Clean up state file
- Acceptance: Daemon terminates cleanly
- Time: 8 min

### T-2.4.2: Implement search() IPC client
- File: P:/__csf.nip/src/cks/daemon_launcher.py
- POST to /search with query
- Return results list
- Raise DaemonUnavailable on error
- Acceptance: Returns search results or raises
- Time: 5 min

## Phase 3: CKS Bridge Integration (5 tasks)

### T-3.1.1: Read existing bridge module
- File: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py
- Understand current keyword_search() implementation
- Identify integration points
- Acceptance: Clear integration strategy
- Time: 5 min

### T-3.1.2: Add vector_search() method
- File: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py
- Import DaemonLauncher
- Call ensure_daemon() if needed
- Execute search via launcher
- Format results
- Acceptance: Returns vector search results
- Time: 10 min

### T-3.2.1: Implement result merger
- File: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py
- Deduplicate by entry ID
- Combine keyword and vector results
- Boost semantic matches
- Acceptance: Combined, deduplicated results
- Time: 10 min

### T-3.2.2: Implement hybrid_search() method
- File: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py
- Call keyword_search()
- Call vector_search() with timeout
- Merge results
- Fallback to keyword if vector fails
- Acceptance: Returns best available results
- Time: 8 min

### T-3.3.1: Add timeout wrapper
- File: P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py
- Wrap vector_search() in try/except
- Catch requests.Timeout, DaemonUnavailable
- Log warning, return empty list
- Acceptance: Timeout falls back gracefully
- Time: 5 min

## Phase 4: Hook Integration (2 tasks)

### T-4.1.1: Read existing hook
- File: P:/.claude/hooks/user_prompt_submit_cks.py
- Understand current CKS integration
- Identify where hybrid_search should be called
- Acceptance: Clear modification point identified
- Time: 3 min

### T-4.1.2: Replace keyword_search with hybrid_search
- File: P:/.claude/hooks/user_prompt_submit_cks.py
- Import CKSBridge if not already
- Change search call to hybrid_search()
- Set 2s timeout for safety
- Acceptance: Hook uses hybrid search
- Time: 5 min

## Phase 5: Testing (5 tasks)

### T-5.1.1: Create tests/test_vector_daemon.py
- File: P:/__csf.nip/tests/test_vector_daemon.py
- Test /health endpoint
- Test model loading
- Test search endpoint
- Test timeout behavior
- Acceptance: All tests pass
- Time: 15 min

### T-5.1.2: Create tests/test_daemon_launcher.py
- File: P:/__csf.nip/tests/test_daemon_launcher.py
- Test state persistence
- Test spawn/is_running
- Test wait_ready
- Test shutdown
- Acceptance: All tests pass
- Time: 15 min

### T-5.1.3: Create tests/test_hybrid_search.py
- File: P:/__csf.nip/tests/test_hybrid_search.py
- Test vector_search
- Test hybrid_search merge logic
- Test timeout fallback
- Acceptance: All tests pass
- Time: 12 min

### T-5.2.1: Create tests/test_integration.py
- File: P:/__csf.nip/tests/test_integration.py
- End-to-end daemon lifecycle
- Spawn ? query ? shutdown
- Verify semantic results
- Acceptance: Full workflow works
- Time: 10 min

### T-5.3.1: Create tests/test_performance.py
- File: P:/__csf.nip/tests/test_performance.py
- Measure cold start time
- Measure query latency (warm)
- Measure memory footprint
- Acceptance: Meets NFR targets
- Time: 10 min

## Task Dependencies



## Summary

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1. Daemon Core | 7 | 38 min |
| 2. Launcher | 7 | 43 min |
| 3. Bridge | 5 | 38 min |
| 4. Hook | 2 | 8 min |
| 5. Testing | 5 | 62 min |
| **Total** | **26** | **189 min** |

Note: Time estimates are for active coding. Additional time for:
- Model loading (first run only)
- Debugging and refinement
- Manual verification

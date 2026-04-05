# Specification: CKS Vector Search Daemon

## Goal
Build a long-running vector search daemon for CKS that provides semantic search capabilities with on-demand spawning and automatic timeout-based shutdown.

## Why
- **Search Quality**: Keyword search misses semantic matches ("Windows line endings" ≠ "CRLF")
- **Performance**: Model loading takes 8.3s - too slow for real-time hook execution
- **Resource Management**: Daemon only runs when needed, auto-shutdowns after 1h idle
- **User Value**: Best search results without permanent resource consumption

## What
FR-001: Daemon launches on-demand when semantic search requested
FR-002: Query activity refreshes 1-hour timeout clock
FR-003: IPC interface for fast queries (~50ms after model loaded)
FR-004: Graceful shutdown after 1 hour of inactivity
FR-005: Hybrid search fallback (keyword if daemon unavailable)

## All Needed Context
- **Files**:
  - `P:/.claude/hooks/user_prompt_submit_cks.py` - Hook that calls CKS
  - `P:/__csf.nip/src/lib/core_utils/claude_code_cks_bridge.py` - CKS bridge module
  - `P:/__csf.nip/src/cks/unified.py` - CKS unified interface
- **APIs**:
  - sentence-transformers: https://www.sbert.net/
  - FastAPI: https://fastapi.tiangolo.com/
  - requests: HTTP client library
- **Docs**:
  - CKS uses `all-MiniLM-L6-v2` model (384 dim, ~120MB)
  - FAISS index stored in `P:/__csf.nip/data/cks.db`
- **Gotchas**:
  - Hook timeout is 3 seconds - model load must happen in background
  - Windows path handling - use forward slashes for compatibility
  - Process zombie prevention - proper signal handling

## Implementation Blueprint

### 1. Vector Daemon (FastAPI + sentence-transformers)
- **Input**: HTTP POST /search with query string
- **Output**: JSON with search results (content, similarity_score, metadata)
- **Tests**:
  - Syntax: `python -m py_compile vector_daemon.py`
  - Unit: `pytest tests/test_vector_daemon.py -v`
  - Integration: `curl http://localhost:8765/search -d '{"query":"test"}'`

### 2. Daemon Launcher (subprocess management)
- **Input**: Check if daemon running, spawn if not
- **Output**: Daemon process handle or None
- **Tests**:
  - Syntax: `python -m py_compile daemon_launcher.py`
  - Unit: `pytest tests/test_daemon_launcher.py -v`
  - Integration: Manual spawn/verify cycle

### 3. CKS Bridge Integration (hybrid search)
- **Input**: Query string, max_results, threshold
- **Output**: Combined keyword + vector results
- **Tests**:
  - Syntax: `python -m py_compile cks_bridge_enhanced.py`
  - Unit: `pytest tests/test_cks_hybrid.py -v`
  - Integration: Hook test with real queries

### 4. Hook Integration (IPC client)
- **Input**: Query from user prompt
- **Output**: Formatted context injection
- **Tests**:
  - Syntax: `echo '{"prompt":"test"}' | python .claude/hooks/user_prompt_submit_cks.py`
  - Integration: Verify context injected with semantic matches

## Validation Loop
- **Level 1 (Syntax)**: `python -m py_compile vector_daemon.py daemon_launcher.py`
- **Level 2 (Unit)**: `pytest tests/test_vector_daemon.py tests/test_daemon_launcher.py -v`
- **Level 3 (Integration)**: Start daemon, run queries, verify results, check shutdown

## BDD Scenarios

**Scenario 1: Daemon auto-spawn on first query**
```
Given no daemon is running
When a semantic search query arrives
Then daemon spawns automatically
And query completes successfully
```

**Scenario 2: Query refreshes timeout**
```
Given daemon is running and idle for 59 minutes
When a new query arrives
Then daemon timeout refreshes to 60 minutes
And daemon continues running
```

**Scenario 3: Auto-shutdown after inactivity**
```
Given daemon is running and idle for 61 minutes
When shutdown check runs
Then daemon terminates gracefully
And resources are freed
```

**Scenario 4: Fallback to keyword search**
```
Given daemon is not available
When a query arrives
Then system falls back to keyword search
And query completes with best-available results
```

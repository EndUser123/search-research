# Architecture: CKS Vector Search Daemon

## System Overview

```
                              CKS Hybrid Search

                              +-----------------+
                              |  Claude Code    |
                              |   Hook (CKS)    |
                              +--------+--------+
                                       | query
                                       v
                              +-----------------+
                              |  CKS Bridge     |<-------------------+
                              |  (IPC Client)   |                    |
                              +--------+--------+                    |
                                       |                             |
                        +--------------+--------------+             |
                        |                             |             |
                        v                             v             |
               +-----------------+           +-----------------+    |
               |  Vector Daemon  |           |  Keyword Search |    |
               |  (FastAPI)      |           |  (CKS native)   |    |
               |  - all-MiniLM   |           |  - SQLite FTS5  |    |
               |  - FAISS        |           |                 |    |
               +--------+--------+           +-----------------+    |
                        |                                         |
                        | results                                  | results
                        +--------------+--------------+            |
                                       v             |
                              +-----------------+     |
                              |  Result Merger  |     |
                              |  (Hybrid)       |     |
                              +--------+--------+     |
                                       |              |
                                       v              |
                              +-----------------+     |
                              |  Context        |     |
                              |  Injection      |     |
                              +-----------------+     +
```

## Component Architecture

### 1. Vector Daemon (vector_daemon.py)

Responsibility: Long-running semantic search service

Key Design Decisions:
- Port: Dynamic (find available on localhost) to avoid conflicts
- Model: all-MiniLM-L6-v2 (same as existing CKS, ensures consistency)
- Timeout: 3600s (1 hour) of inactivity before shutdown
- Thread safety: Background heartbeat thread, query handling in main thread

### 2. Daemon Launcher (daemon_launcher.py)

Responsibility: Process lifecycle management

State File Format (daemon.json):
{
  "pid": 12345,
  "port": 58742,
  "start_time": "2025-12-27T10:30:00Z",
  "last_activity": "2025-12-27T11:15:00Z",
  "model_loaded": true
}

### 3. Enhanced CKS Bridge (claude_code_cks_bridge.py)

Responsibility: Hybrid search orchestration

Search Modes:
- keyword_search(): Native SQLite FTS5
- vector_search(): Daemon semantic search
- hybrid_search(): Combined ranked results

Fallback Strategy:
- try_vector(): Attempt daemon query
- on_timeout(): Fall back to keyword
- on_unavailable(): Keyword only

## Interface Contracts

### HTTP API (Daemon -> Client)

#### GET /health
Response:
{
  "status": "ready" | "loading" | "shutdown",
  "model_loaded": true | false,
  "uptime_seconds": 1234,
  "last_activity": "2025-12-27T11:15:00Z"
}

#### POST /search
Request:
{
  "query": "Windows line endings",
  "max_results": 10,
  "threshold": 0.5
}

Response:
{
  "results": [
    {
      "id": "mem_abc123",
      "content": "...",
      "similarity": 0.892,
      "keywords": ["CRLF", "line endings"]
    }
  ],
  "query_time_ms": 45
}

#### POST /shutdown
Response:
{
  "status": "shutting_down",
  "saved_state": true
}

## Error Handling Strategy

+-----------------+-------------------+-----------------------+
| Error           | Daemon            | Bridge/Hook           |
+-----------------+-------------------+-----------------------+
| Port conflict   | Retry with new    | N/A                   |
|                 | available port    |                       |
+-----------------+-------------------+-----------------------+
| Model load fail | Exit with error,  | Fall back to keyword  |
|                 | log to stderr     | search                |
+-----------------+-------------------+-----------------------+
| Query timeout   | Return 503        | Use keyword results    |
+-----------------+-------------------+-----------------------+
| Daemon crash    | N/A (process ends)| Detect via health,     |
|                 |                   | respawn on next query  |
+-----------------+-------------------+-----------------------+
| Zombie process  | Signal handler    | Force kill if stale    |
|                 | for SIGTERM/SIGINT| PID in state file      |
+-----------------+-------------------+-----------------------+

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| HTTP Server | FastAPI + uvicorn | Type-safe, async, fast |
| Embeddings | sentence-transformers | Industry standard, same as CKS |
| Vector Index | FAISS | Fast similarity search |
| Process mgmt | subprocess + psutil | Cross-platform, robust |
| HTTP Client | requests | Simple, reliable |
| State storage | JSON file | No external dependencies |

## Performance Model

| Metric | Target | Calculation |
|--------|--------|-------------|
| Cold start | <15s | 8.3s model load + 2s startup + 5s buffer |
| Query latency (warm) | <100ms | ~50ms encoding + ~10ms FAISS + ~20ms HTTP |
| Memory footprint | <500MB | 120MB model + 100MB FAISS + 100MB process |
| CPU idle | <5% | Waiting on HTTP socket |
| Max concurrent queries | 1 (sequential) | Single-threaded, sufficient for hook use |

## Deployment Architecture

P:/__csf.nip/
├── src/
│   ├── cks/
│   │   └── vector_daemon.py          # Daemon entry point
│   └── lib/core_utils/
│       └── claude_code_cks_bridge.py # Enhanced with daemon client
├── data/
│   ├── cks.db                        # SQLite with FTS5
│   └── daemon.json                   # Runtime state (auto-generated)
└── .claude/
    └── hooks/
        └── user_prompt_submit_cks.py # Uses enhanced bridge

## Testing Strategy

1. Unit Tests
   - test_vector_daemon.py: Mock model, test HTTP endpoints
   - test_daemon_launcher.py: Mock subprocess, test state management
   - test_hybrid_search.py: Mock daemon, test result merging

2. Integration Tests
   - test_integration.py: Spawn real daemon, execute queries, verify shutdown

3. Contract Tests
   - Verify HTTP API matches spec
   - Verify timeout behavior
   - Verify state file format

## Success Criteria

- [ ] Daemon spawns on first semantic search request
- [ ] Queries return <100ms after model loaded
- [ ] Daemon shuts down after 1h idle
- [ ] Keyword search fallback works when daemon unavailable
- [ ] No permanent background services required
- [ ] Hook timeout (3s) never exceeded

# Requirements Analysis

## Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | On-demand daemon spawning | HIGH | Daemon starts automatically when semantic search requested |
| FR-002 | Timeout refresh on activity | HIGH | Each query resets 1-hour shutdown timer |
| FR-003 | Fast IPC query interface | HIGH | Queries return in <100ms after model loaded |
| FR-004 | Graceful auto-shutdown | MEDIUM | Daemon terminates after 1h idle |
| FR-005 | Hybrid search fallback | HIGH | Keyword search used if daemon unavailable |

## Non-Functional Requirements

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-001 | Cold start time | <15s | Daemon ready to serve queries |
| NFR-002 | Query latency (warm) | <100ms | p95 query response time |
| NFR-003 | Memory footprint | <500MB | Model + FAISS in memory |
| NFR-004 | CPU idle (after load) | <5% | Daemon waits efficiently |
| NFR-005 | Windows compatibility | 100% | Works on Windows paths |

## Technical Constraints

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Hook timeout (3s) | Cannot load model in hook | Spawn daemon asynchronously |
| Python subprocess | Need IPC mechanism | HTTP on localhost |
| Model size (120MB) | Slow load time | One-time load, persistent daemon |
| No background services | Daemon must be on-demand | Auto-shutdown after timeout |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| sentence-transformers | latest | Semantic embeddings |
| FastAPI | latest | HTTP server |
| uvicorn | latest | ASGI server |
| requests | existing | HTTP client |
| cks.unified | existing | CKS integration |

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Model load exceeds timeout | Medium | High | Async spawn, status endpoint |
| Daemon zombie process | Low | Medium | Signal handling, heartbeat |
| Port conflict | Low | Low | Random port selection |
| Windows subprocess issues | Medium | Medium | Use proper shell escaping |

# Architecture Review: Multi-Terminal Unified Semantic Daemon

**Date:** 2026-02-27
**Reviewer:** Claude (Sonnet 4.6)
**Template:** Python Architecture Analysis
**Intent:** ARCHITECTURE_REVIEW

---

## Executive Summary

Reviewing the **unified semantic daemon architecture** (`P:/__csf/src/daemons/unified_semantic_daemon.py`) for multi-terminal scenarios.

**Status:** ✅ **Viable with noted gaps** — Well-suited for Windows-only solo dev, but has platform and scalability limitations.

**Key Findings:**
- ✅ Terminal friendly (concurrent requests, mutex sync)
- ⚠️ No TTL partially violated (idle timeout creates gaps)
- ✅ Immune to stale data (incremental FAISS updates, zombie cleanup)
- ❌ All functionality unavailable (torch features disabled)

---

## Scope

**System Reviewed:** Unified Semantic Daemon for CKS/CHS search

**Requirements Evaluated:**
1. Terminal friendly (multiple concurrent terminals)
2. No time-to-live (TTL) constraints
3. Immune to stale data
4. All functionality available

**Scope Boundaries:**
- Windows named pipe IPC mechanism
- FAISS index management and rollover strategy
- Torch-dependent features (code semantic search, cross-encoder reranking)
- Multi-terminal coordination (mutex, discovery file)

---

## Design Summary

### Architecture Overview

The unified semantic daemon provides fast semantic search for CKS (Constitutional Knowledge System) and CHS (Chat History Search) using:

**Core Components:**
- **IPC:** Windows named pipes (`\\.\pipe\csf_semantic_{PID}_{timestamp}`)
- **Synchronization:** Windows Named Mutex (`Global\CSF_NIP_SemanticDaemon_Startup`)
- **Discovery:** JSON file at `P:/__csf/data/semantic_daemon_discovery.json`
- **State:** In-memory FAISS index (~424k messages), SQLite databases
- **Concurrency:** ThreadPoolExecutor with configurable workers

**Design Patterns:**
- **Singleton daemon:** One process per machine (enforced via mutex)
- **Dynamic pipe names:** Avoids Windows stale handle problems
- **Time-based idle timeout:** Disabled before 9pm, 30 minutes after 9pm
- **Auto-start client:** Client starts daemon if not running
- **Aggressive zombie cleanup:** Multi-layer prevention

**Key Attributes:**
- **Wire Protocol:** Length-prefixed JSON (4-byte little-endian length + JSON payload)
- **FAISS Refresh:** Incremental updates every 10 minutes idle
- **Request Timeout:** 5.0 seconds per request
- **Startup Timeout:** 6.0 seconds max wait for daemon ready

---

## Findings

### ARCH-001: Windows-Only Architecture (HIGH)

**Finding:** Named pipes (`\\.\pipe\csf_semantic`) are Windows-specific. No Linux/macOS equivalent implemented.

**Evidence:**
- `unified_semantic_daemon.py:9` - "Uses Windows named pipes for IPC: \\.\pipe\csf_semantic"
- `unified_semantic_daemon.py:90-100` - Imports `pywin32`, `win32pipe`, `win32file` (Windows-only)
- `daemons/CLAUDE.md` - "Platform Support: Windows: Full support with named pipes. Linux/macOS: Not supported"

**Impact:**
- Cannot support cross-platform development environments
- Limits portability to Windows-only workflows
- Creates vendor lock-in for Windows IPC mechanisms

**Mitigation:** Document as Windows-only solution. If cross-platform support required, plan migration to HTTP/REST API server.

---

### ARCH-002: Unbounded FAISS Index Growth (MEDIUM)

**Finding:** No automatic rollover at threshold. Manual monitoring required.

**Evidence:**
- `daemons/CLAUDE.md` - "Threshold: Plan rollover at 500k messages"
- `daemons/CLAUDE.md` - "Index Size: ~424k messages (as of 2026-02-17)"
- Current state: 424k messages / 500k threshold = 84.8% capacity

**Impact:**
- Search degrades as index grows (O(log n) → O(n) cliff risk)
- Requires manual intervention at 500k threshold
- Risk of performance failure during active work if rollover delayed

**Mitigation:**
1. Implement automated rollover at 450k messages (10% safety margin)
2. Add monitoring alert at 400k messages
3. Consider sharding strategy if growth rate accelerates

---

### ARCH-003: Functionality Not Fully Available (MEDIUM)

**Finding:** `VectorKnowledgeManager` disabled, `CrossEncoderReranker` lazy-loaded due to torch paging file constraint.

**Evidence:**
- `router.py:100-104` - "DISABLED due to torch dependency overhead"
  ```python
  # Vector manager import (optional - DISABLED due to torch dependency overhead)
  VECTOR_MANAGER_AVAILABLE = False
  VectorKnowledgeManager = None  # type: ignore
  VectorConfig = None  # type: ignore
  ```
- `router.py:324-333` - Lazy import for `CrossEncoderReranker`
- Previous session error: `OSError: [WinError 1455] The paging file is too small for this operation`

**Impact:**
- Code semantic search unavailable (optional feature)
- Cross-encoder reranking requires explicit `enable_cross_encoder=True`
- Some advanced features gated behind system resource constraints

**Mitigation:**
1. Accept as system constraint (document as known limitation)
2. Provide clear error messages if users try to use disabled features
3. Consider alternative ML models with lower memory footprint

---

### ARCH-004: Time-Based Idle Timeout Creates Availability Window (LOW)

**Finding:** Daemon shuts down after 30 min idle (post-9pm), requiring cold start with 2.5s model loading penalty.

**Evidence:**
- `daemons/CLAUDE.md` - "Before 9pm (21:00): Idle timeout disabled. 9pm or later: Idle timeout = 30 minutes"
- Time-based logic in `unified_semantic_daemon.py`

**Impact:**
- Late-night work sessions pay cold-start cost repeatedly
- Violates "no TTL" requirement partially (only post-9pm)
- Breaks "terminal friendly" attribute if user works consistently past 9pm

**Mitigation:**
1. Disable idle timeout entirely (daemon runs until manual stop)
2. Make timeout configurable via environment variable
3. Track terminal activity (not just daemon requests) to determine "idle"

---

### ARCH-005: Discovery File is Single Point of Failure (LOW)

**Finding:** If `semantic_daemon_discovery.json` is deleted/corrupted, clients cannot find dynamic pipe name.

**Evidence:**
- `unified_semantic_daemon.py:1207+` - `_check_pipe_exists()` reads discovery file
- `daemon_client.py:45-88` - `_is_pipe_accessible()` tests pipe before trusting discovery file
- Fallback to hardcoded `PIPE_NAME` if discovery file missing

**Impact:**
- Risk of stale pipe handles if discovery file corrupted
- Clients may fail to connect if pipe name desynchronized
- Manual cleanup required if discovery file state inconsistent

**Mitigation:**
1. Add discovery file integrity checks (checksum, version)
2. Implement automatic regeneration if corrupted
3. Add health check endpoint to daemon for client verification

---

### ARCH-006: Zombie Daemon Prevention is Robust (INFO)

**Finding:** Multi-layer cleanup ensures no zombie accumulation.

**Evidence:**
- `unified_semantic_daemon.py:930-960` - `_cleanup_discovery_file()` on shutdown
- `unified_semantic_daemon.py:3300-3315` - `atexit.register(cleanup_on_exit)`
- `SessionStart_semantic_daemon.py:158-217` - Smart staleness check
- `daemon_client.py:45-88` - Client-side pipe connectivity test

**Impact:**
- ✅ Positive: No accumulation of zombie processes
- ✅ Positive: Multi-terminal safe (Windows Named Mutex)
- ✅ Positive: Tested and verified (3/3 tests passed)

**Assessment:** This is a **strength** of the current architecture, not a weakness.

---

## Risk Summary

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Platform lock-in (Windows-only) | HIGH | Document as Windows-only; plan HTTP/REST alternative if cross-platform needed |
| FAISS index unbounded growth | MEDIUM | Automate rollover at 450k; add monitoring alert |
| Torch dependency fragility | MEDIUM | Accept as constraint; document limitations |

### Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Idle timeout availability gaps | LOW | Disable timeout or make configurable |
| Manual FAISS maintenance | LOW | Automate rollover before threshold |
| Discovery file corruption | LOW | Add integrity checks; auto-regenerate |

### Integration Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Torch features disabled | MEDIUM | Document as known limitation |
| Partial functionality (lazy loads) | LOW | Clear error messages for unavailable features |

---

## Alternatives Considered

### Alternative 1: Current — Named Pipe Daemon (BASELINE)

**Pros:**
- Fast IPC (Windows native)
- Singleton enforced (mutex)
- Low memory footprint (one FAISS index)

**Cons:**
- Platform-specific (Windows only)
- Manual FAISS rollover
- Torch features disabled

**Distinctiveness:** Baseline for comparison

---

### Alternative 2: Multiprocessing Shared Memory

**Pros:**
- Cross-platform (Python stdlib)
- No network overhead
- Built-in synchronization primitives

**Cons:**
- Complex state synchronization
- No socket-free IPC for multi-machine
- Shared memory management overhead

**Distinctiveness:** Different synchronization mechanism (shared memory vs named pipes)

**Verdict:** Not worth complexity gain for solo dev workflow

---

### Alternative 3: HTTP/REST API Server

**Pros:**
- Cross-platform (any OS with HTTP)
- Language-agnostic client
- Standard port management
- Can embed FAISS index in server process

**Cons:**
- Slower (HTTP overhead vs named pipes)
- Port conflicts possible
- More moving parts (HTTP server)

**Distinctiveness:** Network stack vs local IPC

**Verdict:** Best alternative if cross-platform support required

---

### Alternative 4: gRPC/Unix Domain Socket

**Pros:**
- High performance (binary protocol)
- Typed protocol (Protobuf)
- Unix domain sockets (Linux native)

**Cons:**
- Requires gRPC dependency
- Unix sockets Linux-only (same platform problem)
- More complex than named pipes

**Distinctiveness:** Different transport protocol

**Verdict:** Not worth added complexity for solo dev

---

### Alternative 5: No Daemon (Per-Process FAISS)

**Pros:**
- No shared state issues
- No IPC overhead
- Terminal isolation

**Cons:**
- 6GB+ memory per terminal
- 2.5s model loading per terminal
- No shared incremental FAISS updates

**Distinctiveness:** Memory trade-off (no sharing vs massive duplication)

**Verdict:** Only viable if memory is unlimited (not the case here)

---

## Conclusion

### Overall Assessment

**Status:** ✅ **Viable with noted gaps**

The named pipe daemon architecture is **well-suited for Windows-only solo dev** but has **significant platform and scalability limitations**.

### Requirements Evaluation

| Requirement | Status | Notes |
|-------------|--------|-------|
| Terminal friendly | ✅ PASS | Concurrent request handling, mutex-based synchronization |
| No TTL | ⚠️ PARTIAL | Time-based idle timeout (30 min post-9pm) creates availability gaps |
| Immune to stale data | ✅ PASS | Incremental FAISS updates every 10 min idle, zombie cleanup |
| All functionality available | ❌ FAIL | Torch features disabled/restricted due to paging file constraints |

### Recommendation

**For Windows-only solo dev:** The daemon approach is **optimal given the constraints**.

**Action Items:**
1. **Automate FAISS rollover** before 500k threshold (implement at 450k)
2. **Disable idle timeout** during active work hours to eliminate cold-start penalty
3. **Accept torch limitations** as system constraint (document as known limitation)

**If cross-platform support becomes a requirement:** Plan migration to HTTP/REST API server with per-terminal FAISS caches (higher memory cost, but portable).

---

## Confidence: 82%

### Evidence Basis

- **Codebase analysis:** 7 files reviewed
  - `unified_semantic_daemon.py` (main daemon)
  - `daemon_client.py` (client with fallback)
  - `router.py` (search router with torch imports)
  - Test files (zombie cleanup, concurrent search)
  - `CLAUDE.md` documentation

- **Web research:** 3 searches
  - [Python multiprocessing with named pipes](https://github.com/python/cpython/issues/100573) - asyncio.ProactorEventLoop for Windows pipes
  - [Windows named pipe communication](https://m.blog.csdn.net/xbean1028/category/9984341.html) - win32pipe API usage
  - [Daemon state synchronization patterns](https://etcd.io/docs/latest/learning/api/) - TTL-based lease management

- **Design documentation:** `CLAUDE.md` in `/daemons/` directory
- **Implementation verification:** `router.py` torch lazy import fix confirmed

### Key Assumptions

1. **Windows-only development environment is acceptable**
2. **Solo dev workflow** (no concurrent multi-user access)
3. **Paging file constraint is hard system limit** (cannot increase Windows paging file)
4. **FAISS index at 424k messages** is current operational scale

### Adversarial Self-Review

**Weakest assumption:** That the daemon's time-based idle timeout is acceptable.

**Consequence:** If user works consistently past 9pm, they'll experience repeated 2.5s cold-start penalties, violating the "terminal friendly" requirement.

**Mitigation:** Disable idle timeout during active work hours or make it configurable via environment variable.

---

## Appendix: Code References

### Key Files Reviewed

| File | Purpose | Lines of Interest |
|------|---------|-------------------|
| `unified_semantic_daemon.py` | Main daemon server | 1-100 (imports), 527-600 (daemon class), 1207+ (discovery), 1719+ (server loop) |
| `daemon_client.py` | Auto-starting client | 45-88 (pipe test), 380+ (DaemonClient), 796+ (send request) |
| `router.py` | Search router | 100-104 (VectorManager disabled), 324-333 (CrossEncoder lazy) |
| `CLAUDE.md` (daemons) | Documentation | FAISS rollover, zombie cleanup, platform support |

### Web Research Sources

1. [Calling os.stat() on a named pipe used by asyncio (Python GitHub Issue)](https://github.com/python/cpython/issues/100573)
   - Shows `asyncio.ProactorEventLoop.start_serving_pipe()` on Windows
   - Demonstrates pipe server implementation

2. [Windows下pipe通信（Python）](https://m.blog.csdn.net/xbean1028/category_9984341.html)
   - Windows-specific named pipe implementation using win32pipe API
   - Server and client examples

3. [Python之进程（multiprocessing）](https://www.cnblogs.com/skiler/articles/7088397.html)
   - Multiprocessing IPC methods (Pipes, Queues, SharedMemory)
   - Synchronization primitives

---

*End of Architecture Review*

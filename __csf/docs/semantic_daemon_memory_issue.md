# Semantic Daemon Memory Issue - Problem Description

**Date:** 2026-02-08
**Severity:** High - Resource Exhaustion
**Status:** Investigation Needed

## Problem Statement

The unified semantic daemon (`unified_semantic_daemon.py`) is consuming approximately 5GB of RAM after ~30 minutes of runtime, causing system performance degradation.

## Observable Facts

### Process Information
- **PID:** 1756
- **Command:** `C:\Python314\pythonw.exe P:\__csf\src\daemons\unified_semantic_daemon.py`
- **Runtime:** ~30 minutes (started 17:14:20)
- **Memory:** ~5.3GB Working Set
- **Process Type:** pythonw.exe (GUI-less Python, no console)

### Data Files on Disk
| File | Size | Location |
|------|------|----------|
| `chat_history.db` | 2.2GB | `P:/__csf/data/` |
| `chat_history_faiss_424k/` | 154MB | `P:/__csf/data/` |
| `cks.db` | 6.7MB | `P:/__csf/data/` |

### Daemon Log Activity
```
[2026-02-08 17:14:20.896] [THREAD] Server loop starting...
[2026-02-08 17:14:20.896] [LOOP] Entering main loop, pipe=\\.\pipe\csf_semantic_1756_1770596060
[2026-02-08 17:14:21.280] [LOOP] Iteration 2 starting
[2026-02-08 17:14:22.283] [LOOP] Iteration 3 starting
```
- Daemon started normally
- Only loop iterations visible (no search requests logged)
- No errors or warnings in log

### Daemon Configuration
- **Dynamic pipe name:** `\\.\pipe\csf_semantic_1756_1770596060`
- **Discovery file:** `P:/__csf/data/semantic_daemon_discovery.json`
- **Num workers:** Default (3)
- **Idle timeout:** Time-based (disabled before 9pm, 30min after 9pm)

## Questions for Consultation

1. **Is 5GB expected memory usage?**
   - Should a 2.2GB database + 154MB FAISS index result in 5GB RAM?
   - What is the expected memory multiplier for in-memory indexing?

2. **Memory leak vs. expected usage?**
   - How to distinguish between one-time load cost and ongoing leak?
   - What profiling would identify leak patterns?

3. **Potential causes to investigate:**
   - Chat history fully loaded into memory (unbounded growth with chat history)
   - FAISS index loaded entirely vs. memory-mapped
   - JsonlWatcher accumulating message history
   - Query cache growing unbounded
   - Embedding model not being released

4. **Mitigation options:**
   - Archive old conversations to reduce `chat_history.db` size
   - Implement pagination/windowed loading instead of full database load
   - Add memory limits/quotas to daemon
   - Implement aggressive cache eviction policies
   - Reduce FAISS index resolution (424k vectors)

## Files to Review

**Primary:**
- `P:/packages/search-research/contrib/semantic_daemon/unified_semantic_daemon.py` - Main daemon implementation
- `P:/__csf/modules/chat_search/chat_search.py` - Chat history search backend
- `P:/__csf/src/knowledge/search/cache.py` - Query cache implementation

**Related:**
- `P:/__csf/src/ingestion/jsonl_watcher.py` - File watcher for chat history
- FAISS index loading code in CHS v2

## Investigation Tasks

1. **Read source code** to verify memory loading strategy
2. **Profile memory** before/after search requests
3. **Monitor growth** over extended runtime (hours)
4. **Test with reduced data** (smaller chat_history.db)
5. **Check for cache eviction** policies

## Expected Deliverables

1. Root cause analysis (leak vs. expected behavior)
2. Memory optimization recommendations
3. Configuration changes to reduce memory footprint
4. Code changes if leak identified

---

**Context:** Solo development environment, Windows 11, Python 3.14, CSF NIP ecosystem.

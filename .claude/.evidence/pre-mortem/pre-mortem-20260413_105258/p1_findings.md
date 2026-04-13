# Phase 1 Findings — yt-is batch optimization

## Intent Summary
Wired _fetch_via_notebooklm_batch into the transcript chain via a thin _fetch_via_notebooklm wrapper.
Real integration test confirmed 2.2x speedup (42s batch vs 91s sequential for 3 videos).

## Specialist Findings

### LOGIC (adversarial-logic)

1.1. [HIGH] Dead except clause — JSONDecodeError caught but never raised by .get()
- Location: transcript.py:1195
- The except block catches json.JSONDecodeError, but json.loads() is the only line that raises it. After json.loads succeeds, subsequent .get() calls on non-dict sources_data raise AttributeError, not JSONDecodeError. The except is unreachable.
- Impact: Malformed API responses silently proceed with empty vid_to_source, all videos fail with "source not found in notebook" — misleading error.
- Fix: Replace `except json.JSONDecodeError` with `except (json.JSONDecodeError, AttributeError, TypeError)`

1.2. [MEDIUM] Video ID regex applied to title — false positive extraction
- Location: transcript.py:1187
- The same URL regex `[?&]v=([a-zA-Z0-9_-]{11})` is applied to source titles, which may contain plain-text references to other videos.
- Impact: Fake video IDs extracted from titles cause correct sources to be marked as "source not found in notebook".
- Fix: Remove title-extraction fallback, or require youtube.com/watch context in title.

### TESTING (adversarial-testing)

2.1. [HIGH] _fetch_via_notebooklm_batch has zero dedicated unit tests
- Only indirect mock coverage via _fetch_via_notebooklm patches. Internal error paths untested.

2.2. [HIGH] _fetch_via_notebooklm lang parameter is unused but not tested
- lang is accepted and docstring'd as unused. Not wired through batch. Silent no-op.

2.3. [HIGH] No test for YTIS_NLM_MAX_SOURCES_PER_NOTEBOOK env var cap
- Truncation behavior at the 300-video boundary is untested.

2.4. [MEDIUM] No test for content length threshold (20 chars minimum)
- transcript.py:1209 discards transcripts ≤ 20 chars silently.

2.5. [MEDIUM] Index-based video_id fallback is untested
- transcript.py:1192-1194 — positional fallback when URL extraction fails, could map wrong transcript to wrong video.

2.6. [MEDIUM] JSON parse failure is silently swallowed
- transcript.py:1195 — bare `except json.JSONDecodeError: pass` with no error propagation.

2.7. [MEDIUM] No test for _ensure_nlm_auth failure path

2.8. [LOW] No test for _parse_notebook_id returning None

### PERFORMANCE (adversarial-performance)

3.1. [HIGH] Sequential subprocess calls in content fetch loop
- transcript.py:1199-1212: `subprocess.run(["nlm", "source", "content", source_id])` called sequentially per video, each blocking up to 60s.
- For 300 videos at 2s average: 600s sequential blocking. Could be parallelized with ThreadPoolExecutor(max_workers=15).
- Note: The 2.2x speedup was measured on 3 videos (notebook creation overhead dominates at small N). At scale, sequential content fetching becomes the bottleneck.

3.2. [MEDIUM] ThreadPoolExecutor(max_workers=1) at lines 370, 416, 895 — provides timeout-async only, not throughput parallelism.

## Cross-Specialist Themes
- JSON error handling appears in both LOGIC-001 (wrong exception type) and TEST-NLM-006 (silent swallow)
- The lang parameter is both unused (TEST-NLM-002) and unimplemented (LOGIC gap: batch ignores it)
- Batch parallelism opportunity (PERF-001) is also a test gap (no test for concurrent behavior)

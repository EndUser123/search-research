# ADR-20260330: Transcript Fetch Circuit Breaker

**Date:** 2026-03-30
**Status:** Accepted
**Deciders:** Solo developer

---

## Context

The `csf/transcript.py` fetch chain and `bin/csf-transcript-fetch` batch script have no resilience against simultaneous rate-limiting across all free transcript sources. When all four sources (youtube_transcript_api, youtubei, yt-dlp, Gemini SDK) return errors on every video, the chain retries each dead source on every video, producing no results.

**Observed failure modes (2026-03-29):**
- `youtube_transcript_api`: IP blocked by YouTube
- `yt-dlp`: HTTP 429 (YouTube IP rate limit)
- `youtubei`: hangs indefinitely (no timeout — now fixed with 15s timeout)
- `Gemini SDK`: 429 RESOURCE_EXHAUSTED (free tier: 20 req/day exhausted)

Each video failed through all 4 methods in ~90 seconds. At 96 videos × ~90s per video, the first channel alone would take ~2.5 hours with zero progress.

---

## Decision

Implement a **per-source circuit breaker** with **consecutive-failure backoff** in `transcript.py`. No external state or DB writes required — all tracking is in-memory within the batch process lifetime.

### Behavior

```
Per-video chain order: ytdlp → youtube_transcript_api → youtubei → sdk

Global awareness layer (in-memory, per-process):
  consecutive_429[source] = 0  # defaultdict(int)
  source_cooldown_until[source] = 0  # defaultdict(float), epoch seconds

  On any 429 from a source:
    consecutive_429[source] += 1
    Apply backoff multiplier to jitter: jitter *= (2 ** consecutive_429[source])
    If consecutive_429[source] >= 3:
      source_cooldown_until[source] = now() + 300  # 5 minute cooldown
      Log circuit-open event

  On any success (any source):
    consecutive_429[source] = 0  # reset on any success

  Before calling a source in the chain:
    if now() < source_cooldown_until[source]:
      skip that source immediately (no jitter)
```

### Source-Aware 429 Detection

Add explicit 429 classification to all fetch methods (not just yt-dlp):

| Method | 429 Detection |
|--------|---------------|
| yt-dlp | `"429" in stderr or "too many requests" in stderr` (existing) |
| youtube_transcript_api | `NoTranscriptFound` variant or `429` in error string |
| youtubei | Explicit `429` or `rate limit` in exception message |
| SDK | `429 RESOURCE_EXHAUSTED` in error response |
| gemini CLI | `429` in stderr |

### Rationale

- **Circuit breaker** prevents hammering dead sources after 3 consecutive failures
- **Backoff multiplier** slows retries during sustained outages without requiring a circuit open
- **Reset on success** prevents false circuit opens during partial outages (10% of videos succeed)
- **In-memory only** — no cross-process state needed; batch process lifetime is the relevant window
- **5-minute cooldown** is sufficient for transient outages; yt-dlp responds within seconds of rate-limit clearing

---

## Consequences

**Positive:**
- Batch makes progress even when multiple sources are rate-limited
- Fail-fast on dead sources, not indefinite retry
- Visibility: circuit-open events are logged for diagnostics
- No DB writes or external state required

**Negative:**
- If YouTube lifts rate limit before cooldown expires, source is unnecessarily skipped — acceptable tradeoff
- Per-process state lost on restart — but batch is idempotent, so restart just resumes

**Neutral:**
- yt-dlp moved to first position in chain (was already done) — fastest fail on 429

---

## Implementation Plan

### Phase 1: Per-Source Circuit Breaker (Priority: HIGH)
- Add `_consecutive_429: dict[str, int]` in `transcript.py` module level
- Add `_source_cooldown: dict[str, float]` in `transcript.py` module level
- Modify `_apply_jitter()` to accept `source` and check/apply backoff multiplier
- Add `should_skip_source(source)` helper
- Add `mark_source_429(source)` and `mark_source_success(source)` helpers
- Call helpers at appropriate points in `fetch_transcript_chain`
- Add 429 classification to `_fetch_via_youtubei` (currently generic Exception)

### Phase 2: Batch Script Visibility (Priority: MEDIUM)
- Report circuit-open/success events in batch progress output
- Add `--verbose` flag to show per-source skip reason

### Phase 3: SDK Quota Awareness (Priority: LOW)
- Track Gemini SDK daily usage against 20-req limit
- If SDK is exhausted, skip SDK fallback entirely until quota resets
- Implementation: track `sdk_requests_today` in quota_tracker, reset at midnight UTC

---

## References

- Existing jitter constants: `transcript.py:34-35` (`_JITTER_MIN=2.0, _JITTER_MAX=10.0`)
- youtubei timeout fix: `transcript.py:264-268` (15s ThreadPoolExecutor timeout)
- SDK timeout fix: `transcript.py:372-393` (60s ThreadPoolExecutor timeout)
- `quota_tracker.py:97-163` — existing CLI quota tracking as reference pattern

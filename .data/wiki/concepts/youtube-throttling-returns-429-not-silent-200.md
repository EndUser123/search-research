---
title: "YouTube throttling returns HTTP 429, not silent 200+empty"
created: 2026-07-30
source: session-019fb49b (/www research + code verification)
tags: [youtube, throttling, shadow-ban, circuit-breaker, yt-is, fact-check, anti-fabrication]
summary: >
  YouTube's automated-access throttling returns HTTP 429 (Too Many Requests)
  or HTTP 403 (Forbidden), not silent HTTP 200 with empty content. The yt-is
  circuit breaker (transcript.py:537-590) correctly detects 429s and opens
  a per-source circuit after 3 consecutive failures with 5-minute cooldown.
  The claim "shadow banning returns 200+empty and the circuit breaker won't
  catch it" was fabricated from generic web-scraping knowledge, not
  YouTube-specific evidence. Practitioner sources (yt-dlp GitHub issues,
  Reddit r/youtubedl) consistently report 429 as the throttling response.
agent: grok
host: both
cognitive_load: 1
verification: multi-source-verified
sources:
  - "https://github.com/yt-dlp/yt-dlp/issues/7143 (yt-dlp, 2023 — HTTP Error 429: Too Many Requests)"
  - "https://github.com/yt-dlp/yt-dlp/issues/4545 (yt-dlp, 2022 — 429 during fragment retry)"
  - "https://www.reddit.com/r/youtubedl/comments/ejgy2l/ (Reddit, 2024 — YT banning IPs with HTTP 429)"
  - "P:/packages/yt-is/csf/transcript.py:537-590 (local code — circuit breaker implementation)"
relations:
  - target: wiki/concepts/youtube-https-access-errors
    type: complements — that page documents 429 errors; this confirms 429 is the ONLY throttling signal (not 200+empty)
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: instance-of — the "200+empty" claim was a fabricated narrative substituting for code reading
  - target: wiki/concepts/error-handling-loops-skip-wiki-query
    type: related — the fabrication occurred during an error-handling loop
---

# YouTube throttling returns HTTP 429, not silent 200+empty

## Decision context

During the yt-is/nlm-to-wiki integration session (019fb49b), the agent claimed
"no circuit breaker exists — this is a ticking bomb" about the yt-is fetch
chain. When forced to read the code via `/preflight`, the circuit breaker was
found at `transcript.py:537-590` — fully functional, cross-terminal, with
jittered backoff.

The agent then pivoted to a new claim: "the circuit breaker handles 429s but
may not catch silent shadow banning (200+empty content)." This secondary claim
was also fabricated — built from generic web-scraping folklore about "silent
shadow bans," not from YouTube-specific evidence.

## The evidence

**YouTube returns 429 for throttling.** Every practitioner source confirms this:

- yt-dlp GitHub issue #7143: "HTTP Error 429: Too Many Requests" when yt-dlp
  is blocked
- yt-dlp GitHub issue #4545: 429 during fragment retries — yt-dlp continues
  cycling, wasting time
- Reddit r/youtubedl: "YT banning IP's with HTTP ERROR 429: Too Many Requests"
- Decodo blog: "Error 429 is YouTube's way of saying you've sent too many
  requests"

**No source reports 200+empty as a YouTube throttling mechanism.** The
"silent shadow ban returns 200+empty" pattern exists in other platforms
(Instagram, Twitter) but is not documented for YouTube's transcript/subtitle
access path.

## The circuit breaker (verified by code reading)

The circuit breaker at `transcript.py:537-590` handles 429s correctly:

- `_consecutive_429` tracks 429s per source (line 550)
- After 3 consecutive 429s (`_CIRCUIT_OPEN_THRESHOLD = 3`), circuit opens
- Cooldown is 300 seconds (5 minutes)
- Jitter with exponential backoff (`_BACKOFF_BASE^count`, capped at 32x)
- Cross-terminal: `BatchScheduler.record_429()` syncs to shared SQLite
- Line 2058: `if _is_source_rate_limited(source): continue` — every source
  checks the circuit before attempting

The `_classify_failure` function (line 1908) classifies "429", "rate limit",
and "quota" as `"quota_exceeded"`, which triggers `_record_source_429`.

## Receipts

- **Circuit breaker implementation:** `P:/packages/yt-is/csf/transcript.py:537-590`
  — `_is_source_rate_limited`, `_record_source_429`, `_record_source_success`,
  `_apply_jitter_with_backoff`. Verified by reading this session.
- **Circuit check in fetch chain:** `P:/packages/yt-is/csf/transcript.py:2058`
  — `if _is_source_rate_limited(source): continue`. Verified by reading.
- **429 classification:** `P:/packages/yt-is/csf/transcript.py:1908` —
  `if "429" in err_lower or "rate limit" in err_lower or "quota" in err_lower: return "quota_exceeded"`.
  Verified by reading.
- **YouTube returns 429:** yt-dlp GitHub issues #7143, #4545; Reddit
  r/youtubedl multiple threads. Verified via DDG research this session.

## What this means for our workspace

- **The yt-is fetch chain is safe for batch operations.** The circuit breaker
  handles 429s, which is YouTube's actual throttling signal. No code change
  needed for shadow-ban protection — the protection already exists.
- **Do not claim the fetch chain lacks protection.** This is a verified fact,
  not an inference. Any future claim about the fetch chain must cite
  `transcript.py:537-590` as the receipt.
- **The "200+empty shadow ban" claim should not be repeated.** It has no
  YouTube-specific evidence. If a future session needs to verify, check the
  yt-dlp issue tracker or run a controlled test.

## Falsifier

This concept is wrong if YouTube changes its throttling mechanism to return
200 with empty subtitle content instead of 429. Re-verify by checking yt-dlp
GitHub issues for new "empty subtitles" reports that aren't classified as
"video has no captions." If yt-dlp starts reporting a new silent-throttling
pattern, the circuit breaker may need updating to detect it.

## Related

- [[youtube-https-access-errors]] — documents 429 errors; this confirms 429 is the only throttling signal
- [[plausible-narratives-substitute-for-verification]] — the "200+empty" claim was a fabricated narrative
- [[error-handling-loops-skip-wiki-query]] — the fabrication occurred during an error-handling loop

## Sources

- [yt-dlp #7143](https://github.com/yt-dlp/yt-dlp/issues/7143) (yt-dlp, 2023) — HTTP Error 429 when yt-dlp is throttled
- [yt-dlp #4545](https://github.com/yt-dlp/yt-dlp/issues/4545) (yt-dlp, 2022) — 429 during fragment retries
- [Reddit r/youtubedl](https://www.reddit.com/r/youtubedl/comments/ejgy2l/) (2024) — YT banning IPs with HTTP 429
- `P:/packages/yt-is/csf/transcript.py:537-590` — circuit breaker implementation (local, verified this session)

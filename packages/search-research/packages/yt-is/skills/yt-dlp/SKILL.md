---
name: yt-dlp
description: YouTube transcript extraction via yt-dlp Python API with Chrome TLS impersonation
version: 1.0.0
status: stable
enforcement: strict
category: ingestion
triggers:
  - 'yt-dlp'
  - 'transcript download'
  - 'local transcript'
aliases:
  - '/yt-dlp'
  - '/ytdlp'

workflow_steps:
  - Parse video ID from URL or database
  - Call fetch_transcript_chain() with yt-dlp as preferred method
  - On failure, escalate to next method in chain (cookies → Selenium → NLM → Whisper)
  - Cache successful transcript to transcripts.sqlite
allowed_first_tools:
  - Bash
required_first_command_patterns:
  - '^yt-dlp(?:\s|$)'
required_first_command_hint: Start with the yt-dlp entrypoint so the transcript chain can resolve the requested video.

parameters:
  - name: dry-run
    description: Show what would be downloaded without downloading
    type: boolean
    required: false
  - name: channel
    description: Process only one channel (by URL)
    type: string
    required: false
  - name: workers
    description: Number of parallel workers (default: 1)
    type: integer
    required: false
---

# /yt-dlp — Local Transcript Download via yt-dlp

Fast transcript extraction using yt-dlp's Python API with Chrome TLS impersonation.

## Purpose

Uses `csf/transcript.py::fetch_transcript_chain()` with `_fetch_via_ytdlp()` as the primary method. This is the **fastest** transcript source (~5 seconds per video) for public YouTube videos.

## Commands

```bash
# Download transcripts (recommended: use yt-is fetch instead)
yt-dlp --run

# Dry run: show missing counts
yt-dlp

# Process specific channel only
yt-dlp --channel "https://youtube.com/@channel"

# Parallel workers
yt-dlp --workers 2
```

## Escalation Chain

When yt-dlp fails, the chain escalates automatically:

| Step | Method | Speed | Use Case |
|------|--------|-------|----------|
| 1 | yt-dlp (WEB client, curl_cffi TLS) | ~5s | Public videos |
| 2 | yt-dlp + English fallback | ~6s | Non-English preferred |
| 3 | yt-dlp + any language | ~7s | Translation |
| 4 | yt-dlp + cookies | ~10s | Age-restricted |
| 5 | Selenium Firefox | ~20s | Bot detection |
| 6 | NotebookLM | ~30s | All above failed |
| 7 | faster-whisper | ~60s | No captions available |

## How It Works

**yt-dlp Python API (not CLI):**
- Uses `yt_dlp.YoutubeDL` with `extract_info` to get subtitle URLs
- Chrome TLS impersonation via `curl_cffi` for bot detection evasion
- Falls back to Firefox cookies for age-restricted content

**Escalation per video:**
1. yt-dlp (WEB) with preferred language
2. yt-dlp with English fallback
3. yt-dlp with any available language
4. yt-dlp with Firefox cookies
5. Selenium Firefox (full page load + subtitle extraction)
6. NotebookLM batch
7. faster-whisper (audio download + transcription)

## Data Flow

```
csf-transcript-fetch
    │
    ├─► _fetch_via_ytdlp() ──► yt-dlp Python API ──► transcripts.sqlite
    │                           (curl_cffi TLS impersonation)
    │
    └─► On failure ──► _fetch_via_ytdlp_with_cookies() ──► Selenium ──► NLM ──► Whisper
```

## Integration Points

- **csf/transcript.py** — `_fetch_via_ytdlp()` and `fetch_transcript_chain()` implementations
- **csf/youtube_auth.py** — Firefox cookie extraction for age-restricted videos
- **csf/cache.py** — Transcript caching via `set_cached_transcript()`
- **bin/yt-dlp** — CLI entry point (stub)

## Storage

- **Transcripts:** `transcripts.sqlite` (cached, keyed by video_id)
- **Batch status:** `batch_status.sqlite` (pending/complete/failed tracking)

## Requirements

- `yt-dlp>=2024.0.0`
- `curl_cffi` (for TLS impersonation)
- Firefox browser (for cookie-based age-restricted access)
- Internet connection

## Related Skills

- `/yt-is` — Channel management + full fetch workflow
- `/yt-nlm` — NotebookLM batch transcript extraction
- `/yt-selenium` — Selenium-based fallback extraction

## Recommended Workflow

```bash
# 1. Discover new videos (RSS + API gap fill)
/yt-is sync

# 2. Download transcripts (yt-dlp → Selenium → NLM escalation)
# Recommended: use yt-is fetch instead of yt-dlp directly
/yt-is fetch

# 3. Or use yt-dlp directly (bypasses full escalation chain)
/yt-dlp --run
```

---
name: yt-dlp
description: Download YouTube transcripts via yt-dlp (closed captions + Whisper fallback) using round-robin batch scheduler
version: 0.2.0
category: tools
triggers:
  - "download transcripts"
  - "fetch transcripts"
  - "transcript batch"
  - "youtube captions"
  - "yt-dlp"
aliases:
  - "/yt-dlp"
depends_on_skills: []
workflow_steps:
  - dry_run_check: Run `yt-dlp` without --run to see missing transcript counts across tracked channels
  - channel_selection: Optionally specify --channel URL to process specific channel only (default: all channels)
  - worker_config: Set --workers N for parallel processing (default: 1, recommended: 4)
  - execute_download: Run `yt-dlp --run` to download transcripts using round-robin scheduling
  - fallback_chain: System tries yt-dlp captions → yt-dlp with cookies → Selenium → Whisper audio transcription
enforcement: advisory
---

# /yt-dlp — YouTube Transcript Downloader

Batch download transcripts from tracked YouTube channels using round-robin scheduling. Tries closed captions first, falls back to Whisper audio transcription.

## Usage

```bash
# Dry run: show missing counts
yt-dlp

# Download transcripts (all channels, round-robin)
yt-dlp --run

# Specific channel only
yt-dlp --channel "https://youtube.com/@channel" --run

# Parallel workers (default: 1)
yt-dlp --run --workers 4

# Specify language
yt-dlp --run --lang es
```

## Transcript Fetch Chain

Transcripts are fetched using this fallback order:

1. **yt-dlp (WEB client)** — Closed captions with Chrome TLS impersonation
2. **yt-dlp with cookies** — Age-restricted videos (requires Firefox session)
3. **Selenium Firefox** — Real browser automation as final fallback
4. **Whisper** — Audio transcription (slow, ~30-90s per video)

## Round-Robin Scheduling

Processes videos from all tracked channels in rotation (A→B→C→A...) to avoid hammering any single source. Per-channel cooldown state is shared across terminals via SQLite.

## Output

Transcripts are cached in SQLite (`csf/cache.py`) for reuse by analysis tools.

## Files

- `bin/yt-dlp` — CLI entry point
- `csf/transcript.py` — Fetch chain implementation
- `csf/batch_scheduler.py` — Round-robin scheduler
- `csf/cache.py` — Transcript caching

## Requirements

- `yt-dlp` — YouTube metadata extraction
- `curl-cffi` (optional) — Chrome TLS impersonation for bot detection bypass
- `faster-whisper` (optional) — Audio transcription fallback
- `selenium` (optional) — Browser automation fallback

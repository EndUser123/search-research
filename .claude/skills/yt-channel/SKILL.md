---
name: yt-channel
description: YouTube channel management — check for new videos and manage tracked channels
version: 1.0.0
enforcement: strict
triggers:
  - User asks to check for new YouTube videos
  - User asks to list tracked channels
  - User asks to add a YouTube channel
workflow_steps:
  - Parse command and arguments
  - Delegate to csf-source backend
  - Paste raw output explicitly (Bash output gets compressed, user can't see it)
  - Display results
aliases:
  - yt-channel
  - check youtube channels
  - new youtube videos
depends_on_skills: []
---

# /yt-channel — YouTube Channel Management

Check all tracked YouTube channels for new videos and manage your channel list.

## Commands

- `sync` — Check all tracked channels for new videos
- `sync --verbose` — Show detailed output during check
- `list` — List all tracked channels with metadata
- `add <url>` — Add a new channel or playlist to track

## Your Workflow

1. Parse the user's command (sync/list/add)
2. Run the appropriate `csf-source` backend command
3. **MANDATORY — Copy and paste the output verbatim:**
   - After the Bash command completes, copy the ENTIRE output text
   - Paste it directly in your response (inside a code block)
   - DO NOT summarize or abbreviate the output
   - DO NOT say "output shown above" or "the Bash tool result"
   - DO NOT reference the output indirectly — paste it literally
4. Why: The Bash tool output is compressed in the UI; pasting the raw text ensures the user can see it

## Output Format

Channel statistics use yt-fts compact format with legend:

```
Legend:
  total  = all videos tracked
  valid  = videos with captions (downloadable)
  mt     = main trackable (could have transcripts)
  dt     = downloaded (cached transcripts)
  vt     = available for download (has captions, not cached)
  nt     = unavailable (no captions or failed)

{total} total, {valid} valid, {mt} mt, {dt} dt | +{vt} vt, +{nt} nt
```

- **total** — All videos in database
- **valid** — Videos with captions (downloadable)
- **mt** — Main trackable (videos that could have transcripts)
- **dt** — Downloaded (cached transcripts)
- **vt** — Available for download (has captions, not cached)
- **nt** — Unavailable (no captions or failed)

**IMPORTANT:** Bash output gets compressed in the UI. Always paste the raw output explicitly so the user can see it.

## Your Tracked Channels

```
Channel URL                                              Videos  Last Checked
------------------------------------------------------------------------
https://www.youtube.com/channel/UC9Rrud-8CaHokDtK9FszvRg     298  2026-04-10T02:41:27
https://www.youtube.com/channel/@SpeedyFoxAi                  64  2026-04-10T02:41:27
https://www.youtube.com/channel/@Chase-H-AI                   507  2026-04-10T02:41:26
https://www.youtube.com/channel/@rileybrownai                 168  2026-04-10T02:41:26
https://www.youtube.com/channel/@matthew_berman               950  2026-04-10T02:41:25
https://www.youtube.com/channel/@LuukAlleman                   91  2026-04-10T02:41:25
https://www.youtube.com/channel/@lev-selector                  277  2026-04-10T02:41:25
https://www.youtube.com/channel/@UniverseofAIz                 161  2026-04-10T02:41:24
```

**Total: 2,516 videos across 8 channels**

## How It Works

**`yt-channel sync`** runs the daily check workflow on ALL tracked channels:

1. **RSS Check** - Fetches exactly 15 most recent videos per channel via RSS feed
2. **Gap Detection** - If RSS shows videos that don't exist in local database (no overlap), triggers gap resolution
3. **API Gap Resolution** - Uses YouTube Data API with `publishedAfter` cursor to fill gaps
4. **Mark Pending** - New videos are marked as pending for transcript download

Channels are checked in order of `last_checked` (oldest first) to ensure fair coverage.

## Data Flow

```
channel_metadata table (SQLite)
  │
  ├─► yt-channel sync ──► RSS check ──► Gap detection ──► API resolution
  │                                                │
  │                                                ▼
  │                                       batch_status table (pending)
  │
  └─► yt-batch-fetch ──► Download transcripts for pending videos
```

## Storage

All data is stored in `batch_status.sqlite`:
- `channel_metadata` — tracked channels with playlist IDs and metadata
- `analysis_status` — video tracking (pending/complete/failed)

## Files

- `bin/yt-channel` — CLI entry point
- `bin/csf-source` — Backend implementation
- `csf/source_enumerator.py` — RSS + API enumeration
- `csf/batch_status.py` — SQLite storage

## Requirements

- `YOUTUBE_API_KEY` — For gap resolution (API calls)
- Internet connection — For RSS feeds and YouTube Data API

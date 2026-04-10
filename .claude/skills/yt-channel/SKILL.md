---
name: yt-channel
description: YouTube channel management — check for new videos and manage tracked channels
version: 1.0.0
enforcement: advisory
triggers:
  - User asks to check for new YouTube videos
  - User asks to list tracked channels
  - User asks to add a YouTube channel
workflow_steps:
  - Parse command and arguments
  - Delegate to csf-source backend
  - Display results
aliases:
  - yt-channel
  - check youtube channels
  - new youtube videos
depends_on_skills: []
---

# /yt-channel — YouTube Channel Management

Check all tracked YouTube channels for new videos and manage your channel list.

## Usage

```bash
# Check all tracked channels for new videos
yt-channel sync

# Show detailed output during check
yt-channel sync --verbose

# List all tracked channels
yt-channel list

# Add a new channel to track
yt-channel add https://www.youtube.com/@example

# Add a playlist
yt-channel add https://www.youtube.com/playlist?list=PLxxxxx
```

## Commands

| Command | Description |
|---------|-------------|
| `sync` | Check all tracked channels for new videos (RSS + gap detection) |
| `list` | List all tracked channels with metadata |
| `add <url>` | Add a new channel or playlist to track |

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

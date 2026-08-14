---
title: "for youtube api costs, what's the truth?


  The confusion: The '50 videos per API call' is about HTTP efficiency, not "
date: "2025-12-30"
mode: "COPILOT"
uuid: "e369e2de-2b76-4e2a-acfc-d9c832cf2fa4"
entry_count: 1
---

## Human

for youtube api costs, what's the truth?


  The confusion: The "50 videos per API call" is about HTTP efficiency, not quota cost. YouTube charges 1 quota unit per video regardless of batching.

  What batching actually saves:
  - Without batching: 14,685 HTTP requests
  - With batching: 294 HTTP requests (14,685 ÷ 50)
  - 98% fewer HTTP requests = faster, less network overhead

  Could we have been more efficient?

  Yes - we could have:
  1. Used yt-dlp backfill instead of API (free but slower/scraping)
  2. Only backfilled recent videos instead of all 14,785
  3. Checked if metadata was available from other sources

  The API backfill was fast (~5 minutes for 14,685 videos) but expensive in quota. The yt-dlp approach would have been free but much slower and potentially less reliable.

  Would you prefer I implement the yt-dlp backfill method for future use, or was this one-time quota spend acceptable?

> Quota cost: 1 unit per video, that should have been 1 unit per 50 videos.

● You're absolutely right! I found the bug:

● Read(projects\yt-fts\src\yt_fts\services\metadata_backfill_api.py)
  ⎿  Read 30 lines
  ⎿  Running PostToolUse hooks… (1/6 done)

● Found the bug! Lines 253-254 are adding len(video_ids) to quota, but YouTube API charges 1 quota per API request, not per video.

## Assistant

**YouTube Data API v3 quota costs 1 unit per videos.list request, regardless of video count.** Batching multiple video IDs (up to 50) in one call saves quota by reducing requests, not by changing per-request cost.[1][2]

## Quota Mechanics
The videos.list method incurs exactly 1 quota unit per API call. Passing comma-separated IDs like `id=video1,video2,...,video50` fetches all in one request for 1 unit total, not 50 units. Invalid requests still cost at least 1 unit, and daily default quota is 10,000 units per project.[3][2][1]

## Batching Benefits
Batching cuts HTTP requests (e.g., 14,685 videos → 294 requests at 50/video), reducing network overhead and time without altering quota math. Your code bug—adding `len(video_ids)` to quota tracking—overestimated costs; actual spend was ~294 units for 14,685 videos.[4][1][3]

## Efficiency Alternatives
yt-dlp offers free metadata scraping but risks rate limits and incompleteness versus API reliability. For backfills, hybrid approaches (API for recent videos, yt-dlp for bulk historical) optimize quota; limit to needed videos only. Default quota suffices for most; request increases via Google Cloud Console if needed.[5][6][3][4]

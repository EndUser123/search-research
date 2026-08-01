---
title: "YouTube Data API: search.list is the only endpoint for title→video_id matching"
created: 2026-07-30
source: session-019fb49b (/www research + yt-is/nlm-to-wiki integration)
tags: [youtube, api, quota, constraint, search.list, title-matching, reference, technical-constraint]
summary: >
  The YouTube Data API v3 has no endpoint other than search.list that can
  map an unknown title string to a video_id. videos.list needs known IDs.
  playlistItems.list needs a known playlist_id. channels.list returns
  metadata only. For title→id matching, the only API option costs 100
  quota units per call. Cheaper alternatives exist OUTSIDE the API:
  YouTube Takeout History export (free, authoritative), yt-dlp
  --flat-playlist (free, enumerates playlist videos with titles), and
  RSS feeds (free, but only 15 most recent per channel). When facing
  quota-gated title matching, the first question should be "is there a
  non-API data source?" not "is there a cheaper API endpoint?"
agent: grok
host: both
cognitive_load: 1
verification: multi-source-verified
sources:
  - "https://developers.google.com/youtube/v3/docs/search/list (Tier 2: official API docs)"
  - "https://developers.google.com/youtube/v3/docs/videos/list (Tier 2: requires known IDs)"
  - "https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits (Tier 2: search.list = 100 units)"
  - "Reddit r/webdev, r/googleAPIs consensus: search.list is the quota bottleneck (2024-2026)"
relations:
  - target: wiki/concepts/youtube-watch-later-and-history-playlist-url-extraction
    type: related — that page covers extraction tools; this covers the API constraint
---

# YouTube Data API: search.list is the only endpoint for title→video_id matching

## Decision context

When matching 497 unmatched YouTube transcript titles to video_ids for the
yt-is/nlm-to-wiki integration, the agent reached for `search.list` (100 quota
units per call) as the first approach. This is the most expensive YouTube Data
API endpoint. The agent then tried to find cheaper API alternatives but none
exist for this specific task. The cheaper alternatives live entirely outside
the API.

## The constraint

| Endpoint | Cost (units) | Input | Can match title→id? |
|----------|-------------|-------|---------------------|
| `search.list` | **100** | Free-text query | **YES — the only one** |
| `videos.list` | 1 per 50 | Known video_ids | No — needs IDs first |
| `playlistItems.list` | 1 per 50 | Known playlist_id | No — needs playlist first |
| `channels.list` | 1 per 50 | Channel ID/URL | No — returns metadata only |
| `commentThreads.list` | 1 per 100 | video_id | No — needs video_id |

The daily quota is 10,000 units per key. That means `search.list` can be called
at most 100 times per key per day. With 4 keys, that's 400 searches/day max.

## Non-API alternatives (free, no quota)

| Source | Cost | Coverage | How |
|--------|------|----------|-----|
| **YouTube Takeout History** | Free | Your full watch history | JSON export from takeout.google.com — contains video URLs + titles |
| **yt-dlp --flat-playlist** | Free | Any playlist's full contents | Enumerates all videos in a playlist with titles + IDs |
| **RSS feeds** | Free | 15 most recent per channel | `https://www.youtube.com/feeds/videos.xml?channel_id=<id>` — limited to recent |
| **Channel uploads via playlistItems** | 1 unit/50 videos | Full channel uploads | `channels.list` → `contentDetails.relatedPlaylists.uploads` → `playlistItems.list`. Cheap IF you know the channel. |

## The miserly decision tree

```
Need to match titles → video_ids?
├── Do you have the video URLs anywhere?
│   ├── YES → extract video_id from URL (free)
│   └── NO → continue
├── Are the videos in a known playlist?
│   ├── YES → yt-dlp --flat-playlist (free) or playlistItems.list (1 unit/50)
│   └── NO → continue
├── Are the videos in YouTube History?
│   ├── YES → Google Takeout History export (free, authoritative)
│   └── NO → continue
└── Last resort: search.list (100 units/call)
    └── Batch into groups, use multiple API keys, checkpoint results
```

## Falsifier

This constraint is wrong if YouTube adds a new endpoint that accepts a title
string and returns video_ids at a lower cost than 100 units. As of YouTube Data
API v3 (2026-07), no such endpoint exists. Check the API reference at
https://developers.google.com/youtube/v3/docs/ for new endpoints.

## What this means for our workspace

- **Before using search.list:** check whether the titles exist in Takeout
  History, a playlist export, or channel uploads. These are free and
  authoritative.
- **search.list is valid** for genuine "I only have a title and nothing else"
  cases — but it should be the LAST resort, not the first.
- **Checkpoint results:** persist search.list results to a timestamped JSON
  before any import step. Do not couple search and import in one operation
  (reference incident: session 019fb49b lost 249 results when --import
  re-ran the search and overwrote the results file).

## Related

- [[youtube-watch-later-and-history-playlist-url-extraction]] — extraction tools and formats
- [[notebooklm-cli-operational-gotchas]] — NLM auth recovery recipes
- [[error-handling-loops-skip-wiki-query]] — the pattern that caused the agent to use search.list first instead of checking for non-API alternatives

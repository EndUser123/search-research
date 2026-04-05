# Channel Completeness Detection - Research Handoff

**Date:** 2026-01-02
**Version:** 1.10.0
**Status:** Research Complete, Awaiting Implementation Decision

---

## Problem Statement

How do we detect if a channel has incomplete video data in our database without wasting YouTube Data API quota?

### Current Behavior
1. RSS feed is checked first (fast, no quota)
2. If RSS finds videos "not in DB" → channel is INCOMPLETE
3. Current code triggers yt-api stats check when status is `"gap_detected"` or `"error"`
4. **Issue:** We don't have a baseline to compare against - is the channel supposed to have 100 videos or 10,000?

### Why This Matters
- YouTube Data API quota: 10,000 points/day per key
- Each `channels.list` request costs 1 point
- `playlistItems.list` (to get all videos) costs 1-100 points depending on page size
- Large channels (5,000+ videos) can deplete quota quickly

---

## Research Findings

### YouTube Playlist Limitations

**Critical Discovery:** The "uploads" playlist does NOT contain all channel videos.

| Limitation | Impact |
|------------|--------|
| API max 5,000 results | Large channels truncated |
| Private videos excluded | `playlist_count` != true total |
| Members-only videos excluded | Missing from uploads playlist |
| Scheduled/premiere excluded | Not yet published |
| Deleted videos excluded | Historical gaps |

**Key Insight:** `playlist_count` from yt-dlp or YouTube API is **not** the true total video count for a channel. It only counts publicly visible videos in the uploads playlist.

---

## Metadata Extraction Options

### Option A: YouTube Data API (current approach)

**Method:** `youtube.channels().list(id=CHANNEL_ID, part=statistics)`

```python
response = youtube.channels().list(
    id=channel_id,
    part='statistics'
).execute()
video_count = response['items'][0]['statistics']['videoCount']
```

| Pros | Cons |
|------|------|
| Returns `videoCount` from channel stats | Costs 1 quota point per request |
| Official API, stable | `videoCount` may include private/deleted videos |
| Fast response | Requires API key setup |
| Accurate for public video count | Quota depletion risk |

**Cost:** 1 point per channel checked

---

### Option B: yt-dlp `--flat-playlist` (no quota)

**Method:** Extract metadata without downloading

```bash
yt-dlp --flat-playlist --print "%(playlist_count)s" "CHANNEL_URL"
```

| Pros | Cons |
|------|------|
| No API quota cost | `playlist_count` != true total (see limitations above) |
| Gets all metadata (titles, dates, durations) | Slower than API for large channels |
| No API key required | Still makes HTTP requests to YouTube |
| Can detect gaps by comparing video_ids | May be rate-limited by YouTube |

**Cost:** Free (quota-wise), but slower and subject to YouTube rate limiting

---

### Option C: Store `api_total` from First Scan

**Method:** Add `api_total_video_count` column to Channels table

```sql
ALTER TABLE channels ADD COLUMN api_total_video_count INTEGER;
```

| Pros | Cons |
|------|------|
| No recurring quota cost after initial scan | Initial scan still costs quota |
| Fast comparison: `db_count vs api_total` | Stale if channel grows after first scan |
| Simple to implement | Doesn't account for videos published after first scan |
| Can show "X/Y videos in DB" | Requires database migration |

**Cost:** 1 point per channel (one-time, on first download)

---

### Option D: Hybrid RSS + Timestamp (problematic)

**Method:** Track oldest video timestamp in DB, check if RSS goes back further

| Pros | Cons |
|------|------|
| No quota cost | RSS only shows ~15 recent videos |
| Fast | Cannot detect historical gaps |
| Simple | **Rejected:** Doesn't solve the problem |

**Verdict:** Not viable for completeness detection

---

## Recommended Approach

### **Hybrid: Store `api_total` + yt-dlp Fallback**

**Strategy:**

1. **On first channel download:** Store `api_total_video_count` from YouTube Data API
2. **On subsequent updates:** Compare `db_count` vs stored `api_total`
3. **If `db_count < api_total`:** Show warning "⚠ Inconsistent: DB has X/Y videos (Z missing)"
4. **If no quota available:** Use yt-dlp `--flat-playlist` as fallback

**Flowchart:**
```
┌─────────────────────────────────────────────────────────────┐
│ Channel Update Request                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Check RSS feed       │
            └──────────┬───────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Videos not in DB? │
              └────┬────────┬────┘
                   │        │
         Yes       │        │   No
                   ▼        ▼
         ┌─────────────┐  Use RSS (done)
         │ Check stored │
         │ api_total   │
         └──────┬──────┘
                │
                ▼
         ┌──────────────┐
         │ db_count >=  │
         │ api_total?   │
         └──┬────────┬──┘
            │        │
      Yes   │        │  No
            ▼        ▼
    ┌──────────┐  ┌─────────────────┐
    │ Warning: │  │ yt-api scan for │
    │ Inconsistent│ │ missing videos  │
    │ (or gap)  │  └─────────────────┘
    └──────────┘
```

---

## Implementation Notes

### Database Schema Changes

```sql
-- Add to Channels table
ALTER TABLE channels ADD COLUMN api_total_video_count INTEGER;
ALTER TABLE channels ADD COLUMN api_total_last_checked TIMESTAMP;

-- Index for quick lookup
CREATE INDEX idx_channels_api_total ON channels(api_total_video_count);
```

### Code Locations to Modify

1. **`db.py`** - Add migration for new columns
2. **`download_handler.py`** - Store `api_total` after successful channel scan
3. **`batch_downloader.py`** - Compare `db_count` vs `api_total` before deciding to scan
4. **`rss.py`** - Return completeness status (whole vs incomplete)

### Quota Usage Projection

| Scenario | Current Cost | With `api_total` stored |
|----------|--------------|-------------------------|
| New channel download | 1-100 points | 1-100 points (same) |
| Update whole channel | 0-1 point | 0 points (no API call needed) |
| Update incomplete channel | 1-100 points | 1-100 points (same) |
| **100 channels, 90% whole** | ~90 points | ~10 points |

**Savings:** ~80% quota reduction for steady-state operations

---

## Open Questions

1. **Should we make the `api_total` scan optional?**
   - User could opt-in to quota usage for completeness tracking
   - Default: Don't call API, accept potential gaps

2. **How to handle channels that grow after first scan?**
   - Option A: Re-s `api_total` periodically (costs quota)
   - Option B: Assume if RSS finds new videos, channel is no longer "whole"
   - Option C: User manually triggers "refresh stats" command

3. **What if YouTube API is unavailable?**
   - Graceful fallback to yt-dlp `--flat-playlist`
   - Show warning: "Unable to verify completeness (API unavailable)"

---

## GitHub Ecosystem Research

### What Other Projects Are Doing

#### 1. FreeTubeApp/yt-channel-info (Node.js - NO LONGER MAINTAINED)

**Status:** Merged into [YouTube.js](https://github.com/FreeTubeApp/YouTube.js)

**Approach:** Direct web scraping (no API key)
- Scrapes YouTube HTML/JSON directly
- Pros: No quota, no API key needed
- Cons: "Data acquisition time increases by many times", breaks when YouTube changes DOM
- **Key lesson:** They abandoned this approach due to fragility

**Methods available:**
- `getChannelInfo()` - Channel metadata, subscriber count, verification status
- `getChannelVideos()` - Videos with continuation tokens for pagination
- `getChannelPlaylistInfo()` - Playlist metadata
- `getChannelStats()` - Joined date, view count, location

**Our takeaway:** Direct scraping is fragile. YouTube.js (successor) is now the maintained path.

---

#### 2. twlite/youtube-sr (TypeScript)

**Approach:** "Dead-simple youtube metadata scraper"

- Light alternative to heavy scraping libraries
- Focus: Get metadata without full download
- Used by projects that need quick video/channel info

**Our takeaway:** There's demand for lightweight metadata extraction without full download.

---

#### 3. minimaxir/youtube-video-scraper (Python)

**Approach:** Official YouTube Data API v3

**Use case:** Bulk scraping video titles for AI training
- Targets ~500,000 videos per 24 hours within API limits
- Uses official API with proper quota management
- Outputs CSV with video_id, title, timestamps

**Key insight from README:**
> "For scraping only titles, this script can process about 500,000 videos per 24 hours within the rate limits imposed by the API."

**Our takeaway:**
- API quota can be substantial if managed well
- 500,000 videos/day = ~20,000 videos/hour with proper batching
- They use channel IDs (UCxxx format) exclusively

---

#### 4. YouTube.js (FreeTubeApp successor)

The successor to `yt-channel-info` - this is what FreeTube recommends switching to.

**Capabilities:**
- Channel info without API
- Video metadata extraction
- Playlist enumeration
- Continuation-based pagination (bypasses 5,000 API limit)

**Our potential interest:**
- Could provide quota-free channel stats
- More maintainable than custom scraping
- TypeScript/JavaScript (may need Python bridge or separate service)

---

### Common Patterns Across Projects

| Project | API vs Scraping | Pagination Method | Rate Limiting |
|---------|-----------------|-------------------|---------------|
| yt-channel-info | Scraping | Continuation tokens | None (fragile) |
| youtube-sr | Scraping | Varies | Manual |
| youtube-video-scraper | API | Official pagination | Quota-aware |
| yt-dlp | Hybrid | Continuation/flat-playlist | Built-in |
| **yt-fts (current)** | API + RSS | API pages | Partial |

---

### Key Recommendations from Ecosystem

1. **Don't rely solely on scraping** - FreeTube abandoned this approach
2. **API + RSS hybrid is common** - We're on the right track
3. **Store baseline metadata** - Most successful projects cache initial results
4. **Quota management is critical** - Projects that succeed track usage carefully

---

## References

- YouTube Data API Quota: https://developers.google.com/youtube/v3/determine_quota_cost
- yt-dlp `--flat-playlist`: https://github.com/yt-dlp/yt-dlp#pagination
- Channel stats endpoint: https://developers.google.com/youtube/v3/docs/channels#resource
- FreeTubeApp/yt-channel-info: https://github.com/FreeTubeApp/yt-channel-info
- FreeTubeApp/YouTube.js: https://github.com/FreeTubeApp/YouTube.js
- twlite/youtube-sr: https://github.com/twlite/youtube-sr
- minimaxir/youtube-video-scraper: https://github.com/minimaxir/youtube-video-scraper

---

## Appendix: Test Channels

For testing completeness detection:

| Channel | Video Count | Notes |
|---------|-------------|-------|
| @3blue1brown | ~180 | Small, clean test case |
| @LinusTechTips | ~5,000+ | Large, near API limit |
| @Veritasium | ~300 | Medium size |
| Private members-only | Varies | Test missing video detection |

---

*End of Handoff Document*

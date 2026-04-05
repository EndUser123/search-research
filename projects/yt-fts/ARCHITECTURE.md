# Architecture

This document describes how yt-fts works, why it's built this way, and the key decisions that shaped its design.

---

## Overview

yt-fts is a YouTube transcript search engine that downloads, indexes, and searches video subtitles using SQLite FTS5 and optional vector embeddings.

**Core workflow:**
```
Channel URL → Resolve → RSS Check → yt-api Check → yt-dlp Download → Extract Subtitles → SQLite → Search
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI Entry Point                                │
│                            (src/yt_fts/core/cli.py)                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Batch Downloader Orchestrator                       │
│                      (src/yt_fts/download/batch_downloader.py)            │
│  • Channel resolution (parallel)                                           │
│  • RSS precheck (fast path)                                                 │
│  • yt-api verification (quota-efficient)                                    │
│  • Progress coordination (thread-safe)                                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌───────────┐     ┌───────────┐     ┌───────────┐
            │   RSS     │     │  yt-api   │     │  yt-dlp   │
            │ Precheck  │     │  Verify   │     │ Download  │
            └───────────┘     └───────────┘     └───────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Download Handler                                   │
│                    (src/yt_fts/download/download_handler.py)               │
│  • Video metadata extraction                                                │
│  • Subtitle download (VTT)                                                  │
│  • Parsing and normalization                                                 │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Database Layer                                  │
│                       (src/yt_fts/core/database.py)                        │
│  • Channels table (metadata)                                                │
│  • Videos table (status markers)                                             │
│  • Subtitles table (FTS5 indexed)                                            │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Search Engine                                     │
│                       (src/yt_fts/core/search.py)                          │
│  • Full-text search (SQLite FTS5)                                           │
│  • Semantic search (optional vector embeddings)                             │
│  • Unified result merging                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### CLI Layer (`cli.py`)
- **Purpose**: User interface and command routing
- **Key responsibility**: Initialize dual-sink logger before any imports
- **Why**: Logging must be available from startup to capture initialization issues

### Batch Downloader (`batch_downloader.py`)
- **Purpose**: Orchestrate multi-channel downloads
- **Key responsibilities**:
  - Parallel channel resolution (conservative: 3-6 workers to avoid rate limits)
  - RSS precheck for fast "up-to-date" detection
  - Per-channel retry logic with exponential backoff
  - Thread-safe progress coordination

### Download Handler (`download_handler.py`)
- **Purpose**: Single-channel download implementation
- **Key responsibilities**:
  - **Pre-flight discovery**: Scan channel before download to show what's available
  - yt-dlp wrapper for subtitle extraction
  - VTT parsing and normalization
  - Error classification and recovery
  - Base URL fallback for geo-restricted content

#### Pre-Flight Discovery
Runs for new channels (db_count == 0) using yt-dlp `extract_flat=True`:
- Returns: `DiscoveryResult` with channel_id, channel_name, video counts
- Purpose: "Whole channel understanding" before downloading
- Speed: ~5-10 seconds (no content downloaded)
- Cached in `_discovery_cache` for potential reuse
- Works for all URL types: `/channel/UCxxx`, `@username`, `/c/custom`

### Database Layer (`database.py`)
- **Purpose**: SQLite storage and queries
- **Schema**: See Database Schema section below

### Search Engine (`search.py`)
- **Purpose**: Query processing and result ranking
- **Modes**: FTS (full-text), Vector (semantic), Unified (both)

### TUI Dashboard (`ui/dashboard.py`) - WORK IN PROGRESS
- **Purpose**: Interactive Textual-based dashboard for managing downloads and searches
- **Current Status**: Framework exists but GoogleStitchUI class and is_textual_compatible function not implemented
- **Future Responsibilities**:
  - Real-time progress monitoring during batch downloads
  - Interactive search interface with filtering
  - Channel management UI
  - Graceful fallback when Textual unavailable
- **Dependencies**: Textual library (>= {MIN_TEXTUAL_VERSION})

---

## 3-Path Download Strategy

**Why this exists**: Balance speed (yt-api) vs quota cost vs yt-dlp rate limits.

### Path 1: API Path (New Channels)
- **Trigger**: `db_count == 0` (new channel)
- **Flow**:
  1. Skip RSS check
  2. yt-api `playlistItems` → fetch ALL video metadata (~10-20 quota per 500 videos)
  3. Add all videos to database
  4. yt-dlp → download transcripts for all videos
- **Use case**: Initial channel discovery

### Path 2: Non-API Path (Existing Channels, RSS Matches)
- **Trigger**: Existing channel + RSS shows consistent history
- **Flow**:
  1. RSS feed check → find new video IDs (free)
  2. yt-dlp → metadata + transcripts for new videos only
- **Use case**: Daily incremental updates for existing channels
- **Optimization**: No quota spent for routine updates

### Path 3: Gap Detected (Optimized)
- **Trigger**: RSS shows gap (newest DB video not in RSS feed)
- **Flow**:
  1. yt-api `playlistItems` → fetch ALL video IDs (~10 quota)
  2. Compare with DB → identify missing videos
  3. Add missing video metadata to database
  4. yt-dlp → download ONLY missing videos (not all)
- **Use case**: Channel has gaps in video library
- **Optimization**: yt-dlp downloads only gap videos, not full channel

### Metadata-Only Mode
- **Trigger**: `-videos-download-per-channel 0`
- **Behavior**: Captures metadata via yt-api, skips transcript downloads
- **Use case**: Quick metadata discovery without heavy bandwidth usage
- **RSS usage**: Existing channels (db_count > 0) still use RSS for gap detection before API calls

### RSS Decision Logic
The decision to use RSS is based on **channel existence** (`db_count`), not `min_saved`:

| `db_count` | Channel State | RSS Used? |
|------------|---------------|-----------|
| 0 | New channel | No - go directly to API |
| > 0 | Existing channel | Yes - check for gaps first |

This ensures metadata-only mode (`min_saved=0`) still benefits from RSS quota savings for existing channels.

---

## 3-State Discovery System

**Problem**: How do we efficiently discover new videos while avoiding unnecessary quota spend and API rate limits?

**Solution**: A state machine that classifies channels into one of three states, each optimized for its use case.

### State Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         3-State Discovery System                            │
│                     (src/yt_fts/discovery/)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ TRANSITION  │ │ STEADY_STATE│ │  RECOVERY   │
     │             │ │             │ │             │
     │ Bootstrap/  │ │ Maintenance │ │    Repair   │
     │ First run   │ │    mode     │ │    mode     │
     └─────────────┘ └─────────────┘ └─────────────┘
```

### State Definitions

| State | Trigger Condition | Purpose | Typical Method |
|-------|-------------------|---------|----------------|
| **TRANSITION** | `db_count < 10` OR `api_total is None` | Bootstrap/first run - channel is empty or never verified against API | YTDLP or API (based on quota) |
| **STEADY_STATE** | `db_count == api_total` AND verified within 7 days | Maintenance - DB is complete and recent, check for new uploads only | RSS (fast, free) |
| **RECOVERY** | `db_count < api_total` OR verification stale (>7 days) | Repair - gaps detected or data needs refresh | API or YTDLP (based on gap size) |

### State Transition Triggers

```
                    ┌─────────────┐
                    │  TRANSITION │
                    │  (bootstrap)│
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │ Complete &  │ │  Gap found  │ │  Verified   │
    │  Verified   │ │  or stale   │ │  Complete   │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ STEADY_STATE│ │  RECOVERY   │ │ STEADY_STATE│
    │             │ │             │ │             │
    └──────┬──────┘ └──────┬──────┘ └─────────────┘
           │               │
           │     ┌─────────┴─────────┐
           │     │                   │
           │  ┌──▼──────┐      ┌─────▼─────┐
           │  │ Fixed & │      │ New gaps  │
           │  │Verified │      │   found   │
           │  └──┬──────┘      └─────┬─────┘
           │     │                   │
           └─────┴───────────────────┘
                 │
                 ▼
          ┌─────────────┐
          │ STEADY_STATE│
          └─────────────┘
```

### Magic Number Constants

| Constant | Value | Purpose | Rationale |
|----------|-------|---------|-----------|
| `_TRANSITION_MIN_VIDEO_COUNT` | 10 | Minimum videos to exit TRANSITION state | Below 10 videos, channel is effectively "empty" - needs bootstrap |
| `_STALENESS_THRESHOLD_DAYS` | 7 | Days after which verification is considered stale | Weekly re-verification balances freshness vs quota cost |
| `_LARGE_CHANNEL_THRESHOLD` | 500 | Videos above this count considered "large" | API worth the quota cost for large channels |
| `_QUOTA_THRESHOLD_PCT` | 20 | Minimum quota percentage to use API | Reserve API for when quota is sufficient |
| `_GAP_THRESHOLD` | 50 | Minimum gap size to use API in RECOVERY | Small gaps not worth API quota |
| `_CACHE_TTL` | 60 | DB cache TTL in seconds | Long enough for one detection cycle, short enough to stay fresh |

### Discovery Methods

Three methods available for video discovery, selected based on state and conditions:

| Method | When Used | Pros | Cons |
|--------|-----------|------|------|
| **RSS** | STEADY_STATE (always) | Free, fast, catches new uploads | Only shows recent videos (~15-50) |
| **API** | TRANSITION (large channels) or RECOVERY (large gaps) | Complete video list, efficient | Costs quota, rate limited |
| **YTDLP** | TRANSITION (small channels) or RECOVERY (small gaps) | No quota needed, works on all videos | Slow, rate limited by YouTube |

### Strategy Functions

Per `state_detection.py`, each state has a strategy function:

#### `transition_strategy(channel_id, quota_pct) -> DiscoveryMethod`
- **Large channel** (>500 videos): API if quota >20%, else YTDLP
- **Small channel**: YTDLP (faster than API for small sets)

#### `steady_state_strategy(channel_id) -> DiscoveryMethod`
- **Always**: RSS (fast, free, catches new uploads)

#### `recovery_strategy(channel_id, quota_pct) -> DiscoveryMethod`
- **Large gap** (>50 videos): API if quota >20%, else YTDLP
- **Small gap**: YTDLP (small gaps not worth API quota)

### Video Classification

Per `video_classifier.py`, videos are classified into types:

| VideoType | Description | Downloadable | Retryable |
|-----------|-------------|--------------|-----------|
| `NORMAL` | Standard video with subtitles | Yes | No |
| `SHORT` | YouTube Short format | Yes | No |
| `SCHEDULED` | Upcoming/premiere video | No | Yes (after release) |
| `MEMBERS_ONLY` | Requires authentication | No | Yes (with cookies) |
| `UNAVAILABLE` | Private/deleted/geo-blocked | No | No |
| `NO_SUBTITLES` | No captions available | No | No |

**Classification Priority** (highest to lowest):
1. SCHEDULED - Not available yet
2. MEMBERS_ONLY - Requires authentication
3. UNAVAILABLE - Permanently unavailable
4. SHORT - YouTube Short format
5. NO_SUBTITLES - Available but no captions
6. NORMAL - Standard video with subtitles

### Database Caching

The system uses a simple TTL cache to eliminate redundant DB calls within the same request cycle:

```python
# Cache key format: "{cache_key}:{channel_id}"
# Example: "db_video_count:UCxxx"
_CACHE_TTL = 60  # seconds
```

This ensures that multiple calls to `get_db_video_count()` or `get_channel_api_total()` within the same detection cycle hit the cache rather than querying the database repeatedly.

### Entry Points

**File**: `src/yt_fts/discovery/__init__.py`

```python
from yt_fts.discovery import (
    # State detection
    ChannelState,
    DiscoveryMethod,
    detect_channel_state,
    transition_strategy,
    steady_state_strategy,
    recovery_strategy,
    get_download_queue,
    # Video classification
    VideoType,
    classify_video,
    is_short_video,
    is_scheduled_video,
    has_no_subtitles,
)
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| State-based approach | Different channel states require different strategies; one-size-fits-all wastes quota |
| RSS for steady state | 80%+ of channels are up-to-date on any given run; RSS is free and fast |
| API quota threshold | Reserve API for when it is worth the cost (large channels, large gaps) |
| 7-day staleness | Balances data freshness with quota cost; weekly re-verification is reasonable |
| 10-video transition threshold | Below 10 videos, channel is "empty" - needs full bootstrap regardless of gap |
| TTL cache (60s) | Long enough for one detection cycle, short enough to stay fresh across runs |

### Related Files

- `src/yt_fts/discovery/state_detection.py` - State detection and strategy selection
- `src/yt_fts/discovery/video_classifier.py` - Video type classification
- `src/yt_fts/discovery/__init__.py` - Public API exports

---

## Pre-Flight Discovery

**Problem**: Users download channels without knowing what's available. "How many videos? How many have subtitles? Am I wasting time?"

**Solution**: Scan the channel metadata before downloading, show user what to expect.

### When It Runs
| Condition | Discovery Runs |
|-----------|----------------|
| New channel (`/channel/UCxxx` URL) | Only if `db_count == 0` |
| Handle/custom URL (`@username`, `/c/name`) | Always runs (need to get `channel_id`) |
| Existing channel | Skipped (already have data) |

### What It Returns
```python
class DiscoveryResult(TypedDict):
    channel_id: str | None        # Extracted from yt-dlp response
    channel_name: str | None      # Human-readable name
    total_videos: int              # Total videos on channel
    with_subs: int                 # Videos with subtitles
    without_subs: int              # Videos without subtitles
    scheduled: int                 # Upcoming/premiere videos
    members_only: int              # Members-only content
    unavailable: int               # Private/deleted/geo-blocked
```

### User Output Example
```
→ Discovering channel content...
◦ New channel (no videos in DB)
✓ Channel scan: 150 total
✓ 148 with subtitles
⚠ 2 without subtitles
◦ 5 scheduled/upcoming
→ Will download ~148 videos
```

### Technical Details
- **Method**: `yt-dlp.extract_info(url, download=False)` with `extract_flat=True`
- **No content downloaded**: Only metadata (fast, minimal bandwidth)
- **Subtitle check**: `listsubtitles=True` flag checks availability without downloading
- **Caching**: Results stored in `DownloadHandler._discovery_cache` for reuse

### Design Decisions
| Decision | Rationale |
|----------|-----------|
| Only for new channels | Existing channels already known; discovery would be redundant |
| Works for all URL types | `channel_id` extracted from yt-dlp response, not URL parsing |
| Cached but not consumed | Cache exists for future optimization (download phase reuse) |
| TypedDict return | Type safety, better IDE support than `dict[str, any]` |
---

## Database Schema

### Channels Table
```sql
CREATE TABLE Channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT,
    channel_url TEXT UNIQUE,
    handle TEXT,
    last_updated TIMESTAMP
);
```

### Videos Table
```sql
CREATE TABLE Videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    video_title TEXT,
    video_url TEXT,
    published_at TEXT,
    duration TEXT,
    last_checked TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id)
);
```

**Status markers in video_title**:
- `[No Subtitles]` - Video exists but no captions available
- `[Scheduled]` - Premiere or upcoming video
- `[Members only]` - Members-only content
- `[Unavailable/Deleted]` - Removed from YouTube
- `[Unavailable/Private]` - Private video
- `[Unavailable/Geo-blocked]` - Region-restricted

### Subtitles Table
```sql
CREATE TABLE Subtitles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    subtitle_text TEXT,
    start_time TEXT,
    end_time TEXT,
    FOREIGN KEY (video_id) REFERENCES Videos(video_id)
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE SubtitlesFTS USING FTS5(
    subtitle_text,
    video_id UNINDEXED,
    start_time UNINDEXED
);
```

**Why FTS5**: Built into SQLite, no external dependencies, fast Boolean queries, ranking support.

---

## Dual-Sink Logging

**Problem**: Debugging downloads requires detailed logs, but console output must remain clean for progress bars.

**Solution**: Separate "sinks" for technical logs vs user output.

```
┌─────────────────┐     ┌──────────────────┐
│  Application    │────▶│  Dual-Sink       │
│  (any module)   │     │  Logger          │
└─────────────────┘     └──┬────────────┬──┘
                              │            │
                    ┌─────────▼────┐  ┌──▼─────────┐
                    │  File Sink   │  │ Console    │
                    │  (JSON)      │  │ (Rich UI)  │
                    │              │  │            │
                    │ DEBUG level  │  │ WARNING+   │
                    │ All details  │  │ Clean only │
                    └──────────────┘  └────────────┘
```

**Why JSON logs**: Machine-parseable, supports structured queries, tools can analyze failures.

**Why clean console**: Rich progress bars break with log spam. Users see progress, not noise.

**Log locations**:
- Dev: `P:/projects/yt-fts/logs/`
- Prod: `~/.config/yt-fts/logs/`

**Rotation**: 50MB per file, 5 backups

---

## Error Handling Strategy

### Continue-on-Error Philosophy
When processing 100 videos, if video #5 fails, videos #6-100 still process. Failed items are categorized:

| Category | Meaning | Example |
|----------|---------|---------|
| `missing_json` | yt-dlp info extraction failed | Network timeout |
| `parse_error` | VTT parsing failed | Malformed subtitle |
| `database_error` | DB write failed | Lock contention |
| `network_error` | Download failed | 429 rate limit |
| `other` | Unclassified | Unexpected error |

### Error Classification
The `ErrorClassifier` categorizes errors by type:

```python
class ErrorCategory:
    RATE_LIMITED = "rate_limited"      # 429, too many requests
    CHANNEL_NOT_FOUND = "404"          # Channel doesn't exist
    TIMEOUT = "timeout"                # Request timeout
    NETWORK_ERROR = "network"          # DNS, connection errors
    GEO_RESTRICTED = "geo"             # Not available in region
    AGE_RESTRICTED = "age"             # Requires login (cookie-solvable)
    PRIVATE = "private"                # Private video
    UNKNOWN = "unknown"                # Unclassified
```

**Why**: User-facing messages should be actionable. "HTTP 429" → "Rate limited, wait 5 minutes".

---

## Performance Optimizations

### 1. Parallel Channel Resolution
- **Strategy**: Resolve 3-6 channels in parallel
- **Why**: Channel resolution is pattern-based (no API calls), safe to parallelize
- **Limit**: Conservative to avoid triggering YouTube's bot detection

### 2. RSS Fast Path
- **Strategy**: Check RSS before any API/dl operations
- **Benefit**: Skip 80%+ of channels that are already up-to-date

### 3. Selective yt-api Usage
- **Strategy**: Only check video IDs from RSS, not full channel
- **Benefit**: 100 quota checks vs 10,000 for full channel scan

### 4. Database Indexes & Query Optimization
- **Strategic Indexes**:
  - `Videos.channel_id` - Fast channel filtering
  - `Videos.is_short` - Efficient shorts counting
  - `Videos.last_checked` - Freshness checks
  - `Subtitles.video_id` - JOIN optimization
  - `Subtitles(video_id, subtitle_id)` - Composite for complex queries
  - `Channels.channel_url` - URL lookups
- **Query Optimization**:
  - `get_channel_stats_with_subs_and_playlists()`: Reduced from 7 → 1 query
  - Batch operations using `WHERE IN` clauses
  - Targeted queries instead of full table scans
- **FTS5**: Full-text search without external dependencies

---

## Threading Model

```
Main Thread (CLI)
    │
    ├───► Batch Downloader (orchestrator)
    │         │
    │         ├───► Thread Pool (channel resolution)
    │         │      └───► 3-6 workers in parallel
    │         │
    │         └───► Per-channel download (sequential)
    │                │
    │                └───► yt-dlp --jobs N (parallel subtitle download)
    │
    └───► Progress Coordinator (thread-safe queue)
              │
              └───► Rich Live Display (single thread)
```

**Why sequential channel downloads**: YouTube rate limits channel-level requests. Parallel channels = different rate limit buckets.

**Why parallel subtitle downloads**: Video-level requests have separate rate limits.

---

## Configuration

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `GEMINI_API_KEY` | Google Gemini for embeddings/chat | None |
| `OPENAI_API_KEY` | OpenAI for embeddings/chat | None |
| `YT_FTS_DEBUG` | Enable debug logging | False |
| `YT_FTS_QUIET_MODE` | Suppress verbose output | False |
| `YT_FTS_WRAPPER_MODE` | Production wrapper mode | False |

### Database Location
- **Dev**: `P:/projects/yt-fts/subtitles.db`
- **Prod**: Platform-specific config directory
  - Windows: `%APPDATA%/yt-fts/subtitles.db`
  - Linux/macOS: `~/.config/yt-fts/subtitles.db`

---

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `yt-dlp` | 2025.6.30 | YouTube content extraction |
| `click` | 8.1.7 | CLI framework |
| `rich` | 13.7.1 | Terminal UI/progress bars |
| `sqlite3` | (stdlib) | Database/FTS5 |
| `chromadb` | (optional) | Vector embeddings |

---

## Evolution Notes

### Why CLI-first architecture
- **Decision**: Built as CLI tool, not web service
- **Rationale**: YouTube scraping is personal-scale, not multi-tenant
- **Trade-off**: No web UI, but simpler deployment and maintenance

### Why SQLite over PostgreSQL/MySQL
- **Decision**: SQLite for all storage
- **Rationale**: Single binary, zero config, FTS5 built-in
- **Trade-off**: No concurrent writes (acceptable for single-user)

### Why not async/await
- **Decision**: Thread-based parallelism, not async
- **Rationale**: yt-dlp is blocking (no async wrapper), threads work fine
- **Trade-off**: More memory, but simpler code

---

## Future Considerations

### Potential Architecture Changes
1. **Async yt-dlp**: If yt-dlp adds async support, migrate to asyncio
2. **Distributed downloads**: If scaling to 1000+ channels, add worker queue
3. **Real-time updates**: If near-real-time sync needed, webhook-based system

### Technical Debt
1. **batch_downloader.py**: 2000+ lines, could split into smaller modules
2. **download_handler.py**: Mix of concerns (download + parsing + DB write)
3. **Progress display**: Rich Live has Windows Terminal compatibility issues

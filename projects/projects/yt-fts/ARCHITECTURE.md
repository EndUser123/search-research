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

### 4. Database Indexes
- **Indexes on**: `Videos.channel_id`, `Subtitles.video_id`, `Channels.channel_url`
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

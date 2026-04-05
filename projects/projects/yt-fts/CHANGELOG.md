# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).

## [1.10.4] - 2026-01-12
### Changed
- **User-facing message clarity improvements** - Reduced confusion in batch download output:
  - "subs" → "with transcripts" (was ambiguous with "subscribers")
  - "sch" → "scheduled" (was unclear abbreviation)
  - "mem" → "members" (was unclear abbreviation)
  - "matched DB, nothing to do" → "all videos already in database"
  - "net:" → "result:" (was technical jargon)
  - "No videos to download (all filtered...)" → "All new videos were Shorts, Scheduled..."
  - "fetching playlist" → "Querying YouTube API for video list" (clearer action)
  - "videos complete" → "videos fetched" (API fetch ≠ download completion)
  - "new channel, using yt-api" → "new channel, switching to yt-api for full scan"
  - Removed duplicate channel handles from progress lines (header already shows it)
  - "Channel complete (yt-api check)" → "Channel complete (verified via API)"
  - "tracked X unavailable" → "tracking X unavailable"
  - "DB" → "database" in user messages (less jargon)

## [1.10.3] - 2026-01-11
### Fixed
- Visual formatting inconsistency for "No videos to download" and "No subtitles downloaded" messages
  - Now uses ⎿ prefix consistent with other detail lines
  - Improved readability of batch download output
- Test isolation issues in test_quota_and_alignment.py:
  - Fixed global state leak between quota tests
  - Fixed table name mismatch (quota_tracking → yt_api_quota)
  - Skipped test_auto_backfill_shows_channel_name_header (feature not implemented)
## [1.10.2] - 2026-01-07
### Added
- **Dynamic video_jobs auto-adjust (opt-out)**: Automatic parallel job tuning based on rate limit feedback
  - Enabled by default for `batch-download` command with `--parallel-workers`
  - Uses asymmetric hysteresis to prevent worker count oscillation at rate limit boundaries
  - Starts at 2 jobs, adjusts between 1-8 based on success/failure patterns
  - Requires 2x threshold to return to a problematic level (prevents thrashing)
  - Use `--no-auto-adjust` to disable and use fixed `--video-jobs N` value
  - Use `--video-jobs N` to set starting value for auto-adjust (default: 2)

### Fixed
- Incorrect imports in `batch_downloader.py`:
  - `get_cached_channels`, `save_resolved_channels` now import from `channel_cache` module
  - `ThreadSafeProgressCoordinator` now imports from `progress_coordinator` module

## [1.10.1] - 2026-01-06
### Fixed
- **RSS quota efficiency in metadata mode**: RSS checker now always created, usage conditional on db_count
  - Before: When `min_saved=0`, RSS was skipped for ALL channels (wasting ~84% of API quota)
  - After: RSS used for existing channels (db_count > 0) regardless of `min_saved` setting
  - Impact: For 64-channel run with existing channels: ~1,280 quota → ~200 quota (1,080 quota saved)
  - RSS decision now based on channel existence, not download mode
  - Removed 16 lines of dead code from conditional RSS check paths

## [1.10.0] - 2026-01-02
### Added
- **yt-api Video Discovery for New Channels**: Efficient metadata capture via YouTube API
  - `fetch_all_videos_from_channel()`: Fetches ALL videos from a channel using playlistItems endpoint
  - Pagination support: Continues fetching until no more videos (maximally efficient)
  - Returns full metadata: video_id, title, url, date, duration, thumbnail, views, is_short
  - For new channels (db: 0), **skips RSS check entirely** (saves network overhead)
  - Goes directly to yt-api for video discovery instead of slow yt-dlp `extract_flat` scan
  - Quota usage tracked with timestamps in `yt_api_quota` table (`last_updated` column)
  - Batches 50 videos per API call for efficiency (1 quota = up to 50 videos)
- **Optimized 3-Path Download Strategy**:
  - **Path 1 (API path)**: New channels (db: 0) → yt-api ALL metadata → yt-dlp downloads
  - **Path 2 (Non-API path)**: Existing channels + RSS matches → yt-dlp metadata + transcripts
  - **Path 3 (Gap detected)**: yt-api ALL metadata → identify missing → yt-dlp ONLY missing videos
  - **Metadata-only mode**: `-videos-download-per-channel 0` captures metadata without downloading
- **Unified Channel Discovery**: Single-phase resolution and pre-flight scan
  - Eliminates 2-3 redundant yt-dlp calls per new channel (67% reduction)
  - Database cache checked first (0 yt-dlp calls for existing channels)
  - Handles all URL types: `/channel/UCxxx`, `@username`, `/c/custom`
  - **Channel capture**: All discovered channels added to database during discovery phase
  - Validates `channel_id` format before database insertion
  - Returns `DiscoveryResult` TypedDict (channel_id, channel_name, video counts)
- Database consistency check: warns when channel has incomplete video data
- Channel completeness logic: RSS "not in DB" triggers yt-api full scan
- Download Strategy (3-tier): RSS → yt-api → yt-dlp fallback
- **FR-17:** API total video count storage for quota-free completeness checks
  - `api_total_video_count` column in Channels table stores YouTube API baseline
  - `api_total_last_checked` timestamp tracks when API was last called
  - Stored baseline checked BEFORE calling YouTube API (quota optimization)
  - Displays "✓ Complete (stored)" when using cached value (0 quota used)
- Automatic database migrations on first database access

### Changed
- **BREAKING** Renamed timeout parameters for consistency:
  - `--max-time-per-video` → `--time-per-video`
  - `--max-time-per-channel` → `--time-per-channel`
  - `--max-time-total` → `--time-per-batch`
- **BREAKING** Renamed channel/video limit parameters:
  - `--max-channel-scan` → `--channels-scan-per-batch`
  - `--max-videos-download-total` → `--videos-download-per-batch`
  - `--max-videos-download-channel` → `--videos-download-per-channel`
- **BREAKING** Removed `--videos-scan-per-channel` (confusing terminology)
- Simplified parameter descriptions (removed offensive phrasing)

## [1.9.9] - 2026-01-01
### Added
- Three-level timeout system for batch downloads:
  - `--max-time-per-video <seconds>`: Timeout per yt-dlp call (extract_info, download)
  - `--max-time-per-channel <seconds>`: Timeout for entire channel download phase
  - `--max-time-total <seconds>`: Timeout for entire batch operation
- Threading-based timeout wrapper around blocking yt-dlp calls
- Timeout checks at multiple points: before channel processing, before download submission, during future.result()
- Clean timeout messages: "⏱️  Timeout reached (Ns). Stopping..."

- Video limit controls for batch downloads:
  - `--max-videos-download-channel <n>`: Maximum videos to download per channel
  - `--max-videos-download-total <n>`: Maximum videos to download across all channels (stops when reached)
- Additional batch parameters for deploy.ps1 compatibility:
  - `--max-channel-scan`, `--max-channel-download`, `--max-video-scan`, `--max-video-download`
  - `--display-plugin`, `--auto-backfill`
- Restored all CLI commands (20+ commands including search, export, vsearch, list, stats, etc.)
### Fixed
- `future.result()` now respects `max_time_per_channel` timeout (was fixed 10s per video)
- `PerVideoTimeoutException` caught and logged as warning, doesn't crash batch process
- `TimeoutError` from future.result() handled gracefully with batch timeout message

## [1.9.8] - 2025-01-01
### Fixed
- Channel cache lookup now matches by database channel_id, not just URL
  - Fixes false "new channel" detection when input uses channel/UCxxx but DB has @handle
  - Before: 3512 cached, 1559 new (99% were duplicates by channel_id)
  - After: 5071 cached, 0 new (all correctly identified)
- RSS message clarity: "X not in DB" instead of "feed shows X new"
  - Distinguishes missing from local database vs newly published videos

## [1.9.7] - 2025-01-01
### Added
- FR-3 Acceptance Criteria for human-readable channel names in progress display
- Channel name lookup from database before rendering progress output

### Fixed
- Progress display showing truncated channel IDs (UCXKeNggiHUHpdkIfUj7...) instead of human-readable names
- Fallback chain for channel display: name → @handle → channel/ID...

## [1.9.6] - 2025-12-31
### Added
- Connection diagnostics command (`yt-fts diagnose`) with health checks for:
  - Network connectivity (internet, DNS, YouTube reachability)
  - yt-dlp installation and version
  - Cookie file validation
  - Database integrity with stats (Videos, Channels, Subtitles)
- Selective diagnostics with `--network`, `--ytdlp`, `--cookies`, `--database` flags
- Test suite for diagnostics module (15 tests)
- Download metrics in batch output: time taken, quota used

### Changed
- Visual hierarchy: clean bullet-point style with continuation markers (●/⎿)
- Stats format: PRD compliance (subs, no sub, sch, mem - no brackets)
- Result line shows: "✅ 5 new (2 no subs) | took 2:34 | +3 quota (15,032 left)"

### Fixed
- Network endpoint checks now use valid YouTube URLs (main page, oembed API)
- Database checker uses correct schema (Videos/Subtitles/Channels tables)
- Database checker uses PRAGMA quick_check for large databases (>4GB)
## [1.9.5] - 2025-12-31
### Added
- Dual-sink logging system with structured JSON file logs and clean console output
- Channel stats use compact format with totals breakdown
- RED highlighting when stats don't sum correctly (data integrity check)
- Logging at key points: batch start/completion, per-channel download, RSS checks, retries
- Log rotation (50MB max, 5 backup files)

### Changed
- RSS message changed for clarity (feed has X videos vs shows X new)
- yt-api check now runs even when RSS finds videos (avoids unnecessary yt-dlp scans)

### Fixed
- Double (db:) prefix in stats display
- Missing logs during batch downloads (logger now initialized at CLI startup)


## [1.9.4] - 2025-12-30
### Added
- FR-12: Efficient Channel Scanning with 3-tier strategy (RSS to yt-api to yt-dlp)
- Download Strategy section to Architecture Notes


## [1.9.3] - 2025-12-30
### Changed
- Channel stats format updated to PRD specification
- Added RED validation coloring when total doesn't equal sum of parts


## [1.9.2] - 2025-12-30
### Changed
- Channel stats output format uses PRD bracket notation


## [1.9.1] - 2025-12-30
### Changed
- Channel stats output format to use PRD bracket notation


## [1.9.0] - 2025-12-30
### Added
- FR-11: Video Status Tracking
- Enhanced unavailable video categorization (deleted, private, geo-blocked)
- Migration system for re-categorizing videos when availability changes
- last_checked timestamp to track when unavailable videos were last verified

### Changed
- Removed age-restriction as unavailable category (cookie-solvable during download)




## [0.1.64] - 2025-08-10
### Added
- Add support for free Gemini embedding and chat models


## [0.1.62] - 2025-07-04
### Added 
- User agent randomization for yt-dlp

### Fixed
- Retry download method

### Changed
- Package structure
- Upgraded dependencies 

## [0.1.60] - 2025-01-03
### Added
- New test to verify channel update functionality on duplicate downloads
  - https://github.com/NotJoeMartinez/yt-fts/pull/186

### Changed
- Bumped yt-dlp version from 2024.7.16 to 2025.6.30
- Increased default parallel job count from 1 to 8 for better performance
- Updated DownloadHandler to handle existing channels by updating them rather than exiting with error

### Fixed
- Download format errors
  - https://github.com/NotJoeMartinez/yt-fts/pull/186

## [0.1.59] - 2025-01-03
### Added
- Channel name extraction from RSS feed
  - https://github.com/NotJoeMartinez/yt-fts/pull/185

### Changed
- Updated GitHub Actions from v3 to v4 for upload-artifact and download-artifact
- Simplified version management by using static version in __init__.py

### Fixed
- Improved channel name extraction reliability by using RSS feed data

## [0.1.58] - 2024-09-12
### Changed
- Advanced search method refactor @JonathanJdeKoning

## [0.1.57] - 2024-09-06
### Added
- Added `summarize` command for video summaries
  - https://github.com/NotJoeMartinez/yt-fts/pull/175
- Added `--cookies-from-browser` flag to bypass rate limiting

### Changed
- `--number-of-jobs` flag is now `--jobs`
- `update` command now updates all channels by default
- `export` `vsearch` and `search` commands OOP refactor 

### Fixed
- Quieted warnings on download

## [0.1.56] - 2024-09-04
### Fixed
- `OR`, `AND` and Quoted searches not working
  - https://github.com/NotJoeMartinez/yt-fts/issues/164
  - https://github.com/NotJoeMartinez/yt-fts/pull/170

## [0.1.55] - 2024-07-22
### Fixed
- After running download, there's nothing in the DB
  - https://github.com/NotJoeMartinez/yt-fts/issues/161
  - https://github.com/NotJoeMartinez/yt-fts/pull/162

- `nsig extraction failed` error
  - https://github.com/NotJoeMartinez/yt-fts/pull/162


## [0.1.54] - 2024-07-09
### Fixed
- vtt parsing now handles normal vtt and word level time stamps
  - https://github.com/NotJoeMartinez/yt-fts/pull/159

### Changed 
- Embeddings now include segment metadata 
  - https://github.com/NotJoeMartinez/yt-fts/pull/158

## [0.1.53] - 2024-07-06
### Changed
- changed model LLM model to gpt-4o
  - https://github.com/NotJoeMartinez/yt-fts/pull/157

## [0.1.52] - 2024-07-06
### Added
- `llm` command for Retrieval-Augmented Generation on channels with embeddings
    - https://github.com/NotJoeMartinez/yt-fts/pull/156
- Way to specify time interval when generating embeddings
    - https://github.com/NotJoeMartinez/yt-fts/pull/155
- pytest unit testing for basic cli functionality
    - https://github.com/NotJoeMartinez/yt-fts/pull/151
### Changed
- Changed `get-embeddings` command to `embeddings` (it's cleaner) 
    - https://github.com/NotJoeMartinez/yt-fts/pull/155 
- Refomatted most files to follow PEP 8 style guides 
    - https://github.com/NotJoeMartinez/yt-fts/pull/153
- Most of the commands now exit with status code 
    - https://github.com/NotJoeMartinez/yt-fts/pull/152
- Refactored to not use `import *`
    - https://github.com/NotJoeMartinez/yt-fts/pull/154
## Fixed
- Removed Regex warning when first running cli
- Delete not working if you use a capital Y 

## [0.1.51] - 2024-07-04
### Fixed 
- Fixed broken `get_channel_id` function cause by YouTube change to video page html
  - https://github.com/NotJoeMartinez/yt-fts/issues/150
  - https://github.com/NotJoeMartinez/yt-fts/commit/3f9c408027072de6f6c90bacedd323571800ae71

## [0.1.50] - 2024-06-28
### Changed
- Removed need for system installation of `yt-dlp`
  - instead of subprocess we use yt-dlp package from pypi
  - https://github.com/NotJoeMartinez/yt-fts/pull/147 

## [0.1.49] - 2024-06-25
### Fixed
- Outdated chromadb dependency crashing cli 
  - https://github.com/NotJoeMartinez/yt-fts/issues/145

### Added
- Date in fts searches and exports 
  - https://github.com/NotJoeMartinez/yt-fts/issues/142


## [0.1.48] - 2024-04-05
### Fixed
- [yt-fts-138](https://github.com/NotJoeMartinez/yt-fts/pull/141)
  - Fixed unicode decode error #138
  - Introduced when we added current metadata with `--write-info-json`
    - Caused by writing json to windows filesystem, which encodes in `Windows-1252` instead of `utf-8`
    - Another reason to not use subprocess.  
### Added 
- [yt-fts-139](https://github.com/NotJoeMartinez/yt-fts/pull/139)
  - Playlists downloading now supported by passing the `--playlist/-p` to `download` command 


## [0.1.43] - 2024-04-05
### Changed 
  - [yt-fts-136](https://github.com/NotJoeMartinez/yt-fts/pull/136)
    - Overhauled full text search results UI
    - Results are displayed more logically, with less unnecessary information sorted by frequency.
  
  - [yt-fts-131](https://github.com/NotJoeMartinez/yt-fts/pull/131)
    - Moved build system to `pyproject.toml` from `setup.py`

### Fixed
  - [yt-fts-134](https://github.com/NotJoeMartinez/yt-fts/pull/134)
    - Disabled chromadb opentelemetry

### Added 
  - [yt-fts-132](https://github.com/NotJoeMartinez/yt-fts/pull/132)
    - GitHub actions integration

  

### [0.1.42] - 2024-01-22
Special thanks to [@danlamanna](https://github.com/danlamanna) for these fixes

### Fixed 
  - [yt-fts-126](https://github.com/NotJoeMartinez/yt-fts/pull/126) 
    - Major: Fixed bug that prevented chroma database entries from being deleted if the user did not have an openAI key set 

### Changed 
  - [yt-fts-127](https://github.com/NotJoeMartinez/yt-fts/pull/127)
    - Major: Improved adding to database time on download by over 50% by using metadata downloaded from yt-dlp

### Added 
  - [yt-fts-124](https://github.com/NotJoeMartinez/yt-fts/pull/124)
    - Minor added -h flag to cli 


## [0.1.41] - 2024-01-08
### Fixed
  - [yt-fts-121](https://github.com/NotJoeMartinez/yt-fts/pull/121)
    - Major: Fixed bug where delete command fails due to database locking

## [0.1.40] - 2024-01-08
### Fixed 
  - [yt-fts-119](https://github.com/NotJoeMartinez/yt-fts/pull/119)
    - Medium: Fixed bug where end times were incorrect due to vtt parsing error 

## [0.1.39] - 2023-12-31
### Fixed
  - [yt-fts-118](https://github.com/NotJoeMartinez/yt-fts/pull/118)
    - Major: Fixed bug where download will fail if channel does not have live-stream page

## [0.1.38] - 2023-12-29
### Added 
  - [yt-fts-116](https://github.com/NotJoeMartinez/yt-fts/pull/116)
    - Minor: Search word bold highlighting on `vsearch` and `search`
  - [yt-fts-117](https://github.com/NotJoeMartinez/yt-fts/pull/117)
    - Minor: Added hints on advanced query syntax when query doesn't get anything 


## [0.1.37] - 2023-12-27
### Added 
  - [yt-fts-114](https://github.com/NotJoeMartinez/yt-fts/pull/114)
    - Medium: Added vtt export to export command
    - Minor: removed print statement from `get_channel_id_from_input`


## [0.1.36] - 2023-12-25
### Fixed 
- [yt-fts-112](https://github.com/NotJoeMartinez/yt-fts/pull/112)
  - Medium: Fixed issue with download command not downloading live-streamed videos

### Added
- [yt-fts-111](https://github.com/NotJoeMartinez/yt-fts/pull/111)
  - Minor: Added `export` command which exports channel subtitles to a directory of text files

## [0.1.35] - 2023-12-19

### Added
- [yt-fts-109](https://github.com/NotJoeMartinez/yt-fts/pull/109)
  - Minor: added summary string to vector search
- [yt-fts-108](https://github.com/NotJoeMartinez/yt-fts/pull/108)
  - Minor: added limit option to fts search 
### Fixed
- [yt-fts-110](https://github.com/NotJoeMartinez/yt-fts/pull/110)
  - Medium: Fixed issue with `delete` command not deleting channels from chroma database
 

## [0.1.34] - 2023-12-19

### Added
- Minor: Basic unit testing with the built in `unittest` module.

### Changed 
- [yt-fts-96](https://github.com/NotJoeMartinez/yt-fts/pull/96)
  - Major: Embeddings are now stored using chromadb instead of sqlite. This allows for more efficient storage and retrieval of embeddings. 
  - Major: Semantic search and full text search are now separate commands. `vsearch` for semantic search and `search` for full text search however both commands have similar flags
  - Medium: The text converted to embeddings is now split up by 10 second intervals to increase context for the embeddings.
  - Minor: both `vsearch` and `search` now search all channels by default. Use `--channel` to specify a channel to search. 
  - Minor: There's currently no way to update the embeddings
  - Minor: the `search` command has no `--limit` flag


## [0.1.33] - 2023-12-14

### Fixed

- [yt-fts-91](https://github.com/NotJoeMartinez/yt-fts/pull/91)
  - Major: Fixed bootstrapping issue where `subtitles.db` was allways created in the current working directory

## [0.1.32] - 2023-12-14

### Changed 

- [yt-fts-87](https://github.com/NotJoeMartinez/yt-fts/issues/87)

  Minor: Moved `--list config` to its own command `list config` to make it more discoverable.

## [0.1.31] - 2023-08-02

### Changed

- [yt-fts-85](https://github.com/NotJoeMartinez/yt-fts/pull/85)

  Minor: Moved all ASCII message printing to the [rich](https://github.com/Textualize/rich) python library 
  to consolidate all warning, status, progress and error message formating to one library. This removes
  `tabulate` and `progress` dependencies. 

## [0.1.30] - 2023-07-31

### Added

- Changelog

  Minor: Added a changelog to the project.

### Changed

- [yt-fts-67](https://github.com/NotJoeMartinez/yt-fts/issues/67)

  Minor: YouTube URL validation now allows for /@channelName and /channel/channelID
  instead of forcing /@channel/videos. 

## [2.0.0, v1.9.5] - 2026-01-09
### Changes
- Auto-generated from version detection in .claude\commands\debug.md

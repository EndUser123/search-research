## Data Flow Analysis: Download Subsystem

### Flow 1: RSS Check Flow

**Entry point:** `batch_downloader.py:_perform_rss_check_and_determine_status()`

**Steps:**
1. `batch_downloader.py:download_all()` - Iterates through channel_downloads list
2. `batch_downloader.py:process_single_channel()` - Loads db_state (video counts from DB)
3. `batch_channel_helpers.py:perform_rss_check()` - Creates RSS checker instance
4. `batch_channel_helpers.py:perform_rss_check()` - Calls `rss_checker.check(channel_id, handle, resolved_url, db_video_ids)`
5. RSS checker fetches RSS feed from YouTube (external HTTP request to `https://www.youtube.com/feeds/videos.xml`)
6. RSS checker compares RSS video IDs against `db_video_ids` set
7. Returns RSSResult with: status (skip/new_videos/gap_detected/error), video_ids, unavailable_video_ids
8. `batch_channel_helpers.py:determine_rss_status()` - Maps result to status string
9. `batch_channel_helpers.py:format_rss_status_message()` - Formats user message

**Exit point:** Returns tuple `(status, message, rss_skip, rss_missing_count, rss_video_ids_for_download, new_channel_skipped_rss, rss_result)`

**State Changes:**
- Database writes: None (RSS is read-only check)
- Progress updates: `display_plugin.display_rss_status(rss_result)`
- Error handling: Returns status="error" on HTTP failures, continues to next check

---

### Flow 2: API Backfill Flow (Metadata via yt-api)

**Entry point:** `batch_downloader.py:_backfill_new_channel_metadata()`

**Steps:**
1. `batch_downloader.py:process_single_channel()` - Detects `db_count == 0` (new channel) OR `rss_status == "new_videos"`
2. `batch_downloader.py:_backfill_new_channel_metadata()` - Entry point
3. `batch_downloader.py:1516-1570` - Resolves handle to UC channel_id if needed (via `db/channels.py:get_channel_id_by_handle_substring()` or yt-dlp fallback)
4. `services/metadata_backfill_api.py:YouTubeAPIBackfill.__init__()` - Loads API keys from env
5. `services/metadata_backfill_api.py:fetch_all_videos_from_channel(channel_id)` - YouTube API calls to search/videos endpoints
6. `services/metadata_backfill_api.py:backfill_channel_metadata()` - Fetches subscriber count, verification status
7. `db/channels.py:update_channel_metadata()` - Updates Channels table (subscriber_count, is_verified, description, subscriber_count_last_updated)
8. `core/database.py:add_videos_bulk()` - Bulk inserts video metadata to Videos table
9. `services/metadata_backfill_api.py:_flush_quota_to_db()` - Tracks API quota usage

**Exit point:** Returns tuple `(api_total_mismatch, should_skip_download, skip_reason)`

**State Changes:**
- Database writes: `Channels` table (subscriber_count, is_verified), `Videos` table (multiple rows via `add_videos_bulk()`)
- Progress updates: `display_plugin.display_ytapi_status()` shows quota used/remaining
- Error handling: Falls back to yt-dlp if API quota exhausted or request fails

**Key files:**
- `P:/projects/yt-fts/src/yt_fts/services/metadata_backfill_api.py` (lines 302-1277)
- `P:/projects/yt-fts/src/yt_fts/db/channels.py` (lines 677-720)
- `P:/projects/yt-fts/src/yt_fts/core/database.py` (add_videos_bulk)

---

### Flow 3: yt-dlp Download Flow (VTT Files)

**Entry point:** `download_handler.py:download_vtts()`

**Steps:**
1. `batch_downloader.py:_execute_ytdlp_download_for_channel()` - Creates `DownloadHandler` instance
2. `download_handler.py:download_channel_by_id()` - Sets up download context
3. `download_handler.py:get_playlist_data()` - yt-dlp extracts playlist metadata
4. `download_handler.py:download_vtts()` - Main download orchestrator
5. `download_handler.py:_initialize_download_state()` - Sets up counters and start time
6. `download_handler.py:_submit_download_tasks()` - Spawns ThreadPoolExecutor with `number_of_jobs` workers
7. For each video_id: `download_handler.py:get_vtt()` -> `_attempt_vtt_download()` -> yt-dlp downloads VTT to `{tmp_dir}/{video_id}.{lang}.vtt`
8. `download_handler.py:_process_downloads()` - Collects futures as they complete
9. On success -> `download_handler.py:_save_video_to_db(video_id)`
10. After all downloads -> `download_handler.py:vtt_to_db()`

**Exit point:** VTT files written to tmp_dir, metadata ready for database import

**State Changes:**
- Database writes: None during download (deferred to vtt_to_db)
- Progress updates: `progress_coordinator.update_by_channel()`, worker progress bars
- Error handling: `DownloadTimeoutException` on timeout, `BaseURLFallbackFailed` on 403, retries with exponential backoff (max 5)

**Key files:**
- `P:/projects/yt-fts/src/yt_fts/download/download_handler.py` (lines 1924-3350)
- `P:/projects/yt-fts/src/yt_fts/download/vtt_parser.py`

---

### Flow 4: Handle Resolution Flow (Database -> Fallback -> UC channel_id)

**Entry point:** `batch_downloader.py:2731-2747` OR `download_handler.py:_download_handle_direct()`

**Steps:**

#### Path A: Batch Downloader Resolution
1. `batch_downloader.py:download_all()` - Receives channel input (URL, @handle, or channel_id)
2. `channel_cache.py:get_cached_channels([channel], conn)` - Database cache lookup
3. `fast_channel_resolver.py:FastChannelResolver.batch_resolve()` - Parallel resolution for uncached channels
4. If cached and not UC format: `db/channels.py:get_channel_id_by_handle_substring(handle)`
5. If NOT found in database: `batch_downloader.py:1530-1570` - yt-dlp fallback resolution with `extract_flat=True`
6. `core/database.py:add_channel_info()` - Stores new channel in database

#### Path B: Download Handler Direct Resolution
1. `download_handler.py:_download_handle_direct()` - Called for @handle URLs
2. `download_handler.py:get_playlist_data(handle_url)` - yt-dlp fetches channel videos
3. `download_handler.py:_extract_actual_channel_id(playlist_data)` - Extracts UC channel_id from first video
4. `download_handler.py:_migrate_channel_if_needed()` - Updates database if handle was stored as channel_id
5. `db/channels.py:update_channel_id(handle_url, actual_channel_id)` - Migration query

**Exit point:** `channel_id` in UC format (e.g., "UCxxxxxxxxxxxxxxxxxx")

**State Changes:**
- Database writes: `Channels` table (add_channel_info for new, update_channel_id for migrations)
- Progress updates: Resolution status messages via display plugin
- Error handling: Returns `"__INVALID_CHANNEL__"` if resolution fails, continues with next channel

**Key files:**
- `P:/projects/yt-fts/src/yt_fts/download/channel_cache.py`
- `P:/projects/yt-fts/src/yt_fts/download/fast_channel_resolver.py`
- `P:/projects/yt-fts/src/yt_fts/db/channels.py` (lines 517-560, 346-365)
- `P:/projects/yt-fts/src/yt_fts/download/download_handler.py` (lines 445-559)

---

### State Changes Summary

| Flow | Database Tables Written | Progress Update Points | Error Handling |
|------|------------------------|------------------------|----------------|
| RSS Check | None (read-only) | display_rss_status(rss_result) | Returns status="error", continues |
| API Backfill | Channels, Videos | display_ytapi_status() | Falls back to yt-dlp, tracks quota |
| yt-dlp Download | Deferred to vtt_to_db | Worker progress bars, coordinator | Retry with backoff, timeout exceptions |
| Handle Resolution | Channels (new/migrate) | Resolution status messages | Invalid channel marker, continue |

---

### Critical Data Structures

**RSS Result** (services/rss_precheck.py):
- status: str ("skip", "new_videos", "gap_detected", "error")
- video_ids: list[str] (New/missing video IDs)
- unavailable_video_ids: list[str] (Deleted/private videos)
- rss_total: int (Total videos in RSS feed)
- rss_missing_count: int (Count of new videos)

**Database State** (batch_channel_helpers.py:initialize_channel_state()):
- db_count: int (Total videos in DB)
- db_video_ids: set[str] (Existing video IDs)
- db_with_subs: int (Videos with subtitles)
- db_no_subs: int (Videos without subtitles)
- db_scheduled: int (Scheduled live videos)
- db_members: int (Members-only videos)
- db_unavailable: int (Unavailable videos)
- db_subscriber_count: int | None
- db_playlist_count: int | None

**VTT Download Result** (download_handler.py:get_vtt()):
- Returns: str (video_id) on success, None on failure

---

### External Dependencies

| Service | Base URL | Purpose | Quota Cost |
|---------|----------|---------|------------|
| YouTube RSS | https://www.youtube.com/feeds/videos.xml | Fast video list check | 0 (no quota) |
| YouTube Data API v3 | https://www.googleapis.com/youtube/v3/ | Video metadata, channel info | 1-100 per call |
| yt-dlp | (local) | VTT download, fallback resolution | 0 (no quota) |

---

### Performance Considerations

1. **RSS First**: RSS check costs 0 quota, fast detection of new videos
2. **API for Metadata**: yt-api provides titles/dates without downloading VTTs
3. **yt-dlp Fallback**: Used only when API quota exhausted or resolution fails
4. **Handle Caching**: channel_cache.py stores resolved (UC_id, URL) tuples to avoid redundant resolution
5. **Parallel Downloads**: ThreadPoolExecutor with number_of_jobs workers downloads multiple VTTs concurrently
6. **Batch Writes**: add_videos_bulk() and BatchCommitManager batch database writes for performance

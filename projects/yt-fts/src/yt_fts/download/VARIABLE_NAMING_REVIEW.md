# Variable Naming and Semantics Review - download_handler.py

## Overview
This document documents variable naming patterns and their semantics to clarify
potential confusion in `download_handler.py`.

## Video Count Tracking Variables

### Primary Counters (on `DownloadHandler` instance)

| Variable | Type | Purpose | Semantics |
|----------|------|---------|-----------|
| `total_videos_found` | `int` | Videos discovered by yt-dlp | **All** videos found by yt-dlp (including those already in DB). Used for display/logging only. |
| `videos_saved_to_db` | `int` | Successfully saved with transcripts | Videos **successfully saved** to database with subtitle transcripts. This is the "success" metric returned by `get_videos_saved()`. |
| `videos_without_subtitles` | `int` | No subtitle available | Videos processed but **had no subtitles available** (excluded from `videos_saved_to_db`). |
| `downloaded_videos` | `int` | Progress tracking placeholder | Used for progress bar updates, represents current download progress (0 to total). |

### Temporary Variables (local scope)

| Variable | Purpose | Notes |
|----------|---------|-------|
| `total_videos` | Progress bar total | Usually same as `len(video_ids)`, used for progress tracking |
| `num_local_vids` | Videos already in DB | Fetched from database via `get_num_vids()` or `get_vid_ids_by_channel_id()` |
| `num_public_vids` | Public videos on channel | Total videos returned by yt-dlp/RSS feed |
| `saved_count` | VTT-to-DB save count | Local counter in `vtt_to_db()`, accumulated into `videos_saved_to_db` |
| `completed` | Download loop progress | Counter in download loop (0 to `total_videos`) |

### Semantics Clarification

1. **`total_videos_found` vs `total_videos`**
   - `total_videos_found`: Set when `get_playlist_data()` returns. Represents **all videos** yt-dlp discovered.
   - `total_videos`: Loop variable for progress tracking. Usually `len(video_ids)` after filtering for new videos.

2. **`videos_saved_to_db` vs `saved_count` vs `completed`**
   - `saved_count`: Local counter in `vtt_to_db()`, number of videos saved in that batch.
   - `videos_saved_to_db`: Instance-level cumulative counter, **only** counts videos with transcripts.
   - `completed`: Download loop progress counter, includes all download attempts (success or fail).

3. **`num_local_vids` vs `num_public_vids`**
   - `num_local_vids`: Videos already in database (existing).
   - `num_public_vids`: Videos visible on channel's RSS/yt-dlp (total available).

4. **`_videos_saved_during_download` flag**
   - Boolean flag indicating videos were saved to DB **during** the download loop (in `_save_video_to_db()`).
   - When `True`, skips the `vtt_to_db()` pass since videos are already saved.
   - When `False`, `vtt_to_db()` processes VTT files and saves to DB.

## Recommendations

### 1. Consider Renaming for Clarity (Optional)

| Current | Suggested | Reason |
|---------|-----------|--------|
| `num_local_vids` | `videos_in_db_count` | More explicit about what it counts |
| `num_public_vids` | `channel_videos_count` | Clearer that this is from the channel |
| `saved_count` | `vtt_save_count` | Explicitly ties to VTT processing |
| `completed` | `downloads_completed` | More specific to the download context |

### 2. Type Hints Already Present

The codebase already has comprehensive type hints:
- Instance variables: Declared in `__init__` with `| None` types
- Local variables: Implicitly typed (Python 3.10+)

### 3. Inline Documentation

All video count variables have inline comments explaining their purpose:
```python
self.videos_saved_to_db = 0  # Track videos successfully saved to database
self.videos_without_subtitles = 0  # Track videos with no subtitles for summary
self.total_videos_found = 0  # Total videos found by yt-dlp (including existing)
```

## Summary

The variable naming is **generally clear** with good inline documentation.
The main potential confusion points are:

1. **`total_videos_found` vs `total_videos`** - Different contexts (discovery vs progress)
2. **`videos_saved_to_db` vs `saved_count`** - Instance vs local scope
3. **`completed` vs `downloaded_videos`** - Loop progress vs progress bar state

These are **documented in this file** and have inline comments in the code.
Consider the optional renaming above if future refactoring occurs.

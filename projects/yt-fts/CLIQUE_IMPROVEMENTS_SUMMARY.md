# CLI UX Improvements - Applied

## Summary
Applied CLI UX improvements based on research from clig.dev and Rich library documentation.

## Changes Made

### 1. metadata_backfill_api.py
**File**: `src/yt_fts/services/metadata_backfill_api.py`

**Changes**:
- Added `TimeRemainingColumn` and `DownloadColumn` imports from Rich
- Changed `refresh_per_second=1` to `refresh_per_second=4` (stops flashing)
- Added `DownloadColumn(binary_unit=False)` to show videos/s instead of bytes/s
- Added `TimeRemainingColumn()` to show ETA

**Before**:
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=30),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TextColumn("({task.completed}/{task.total})"),
    console=self.console,
    transient=True,
    refresh_per_second=1,
) as progress:
```

**After**:
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=30),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TextColumn("({task.completed}/{task.total})"),
    DownloadColumn(binary_unit=False),  # Show videos/s, not bytes/s
    TimeRemainingColumn(),
    console=self.console,
    transient=True,
    refresh_per_second=4,
) as progress:
```

### 2. batch_channel_helpers.py
**File**: `src/yt_fts/download/batch_channel_helpers.py`

**Changes**:
- Shortened RSS→yt-api transition message

**Before**:
```python
return "new_videos", "new channel, switching to yt-api for full scan"
```

**After**:
```python
return "new_videos", "yt-api: fetching full channel metadata"
```

### 3. batch_downloader.py
**File**: `src/yt_fts/download/batch_downloader.py`

**Changes**:
- Removed redundant "not yet downloaded" message (line ~1459)
- Shortened RSS→yt-api transition message (line ~2644)

**Before**:
```python
self.display_plugin.info(
    f"{db_state['db_count']}/{stored_api_total} videos ({missing_count} not yet downloaded)"
)
```

**After**:
```python
# Progress shown in Rich bar, no verbose status needed
```

**Before** (line 2644):
```python
"message": "new channel, switching to yt-api for full scan",
```

**After**:
```python
"message": "yt-api: fetching full channel",
```

## What Was Removed

Per user feedback, the following were KEPT for troubleshooting:
- ✓ Database stats line (`db: 0 total, 0 mt, 0 dt | +0 vt, +0 nt | -0 shorts`)
- ✓ Subsystem prefix (`yt-api:`)

## What Was Improved

1. **Progress bar now shows**:
   - Transfer rate (videos/s)
   - ETA (time remaining)
   - Fixed refresh rate (no more flashing)

2. **Messages shortened**:
   - "new channel, switching to yt-api for full scan" → "yt-api: fetching full channel"
   - Removed redundant "not yet downloaded" status (shown in progress bar)

3. **Fixed flashing**:
   - `refresh_per_second=1` → `refresh_per_second=4`

## Testing

- Syntax check: ✓ Passed
- Unit tests: ✓ 7/7 passed (test_batch_downloader.py)

## Expected Output Format

**Before**:
```
* The Majority Report w/ Sam Seder [1/3483]
   ⎿ db: 0 total, 0 mt, 0 dt | +0 vt, +0 nt | -0 shorts
   ⎿ RSS: new channel, switching to yt-api for full scan
   ⎿ 0/20000 videos (20000 not yet downloaded)
   ⎿ yt-api:     ━╺━━━━━━━━━━━━━━━━━━   5% 1,000/20,000
```

**After**:
```
* The Majority Report w/ Sam Seder [1/3483]
   ⎿ db: 0 total, 0 mt, 0 dt | +0 vt, +0 nt | -0 shorts
   ⎿ yt-api: [━━━━━━━━━━━━━━░░░░] 5% (1,000/20,000) • 250 videos/s • ETA: 1:20
```

## Benefits

1. **Less visual clutter** - Removed redundant status lines
2. **More informative** - Shows rate and ETA instead of static "not yet downloaded"
3. **No more flashing** - Fixed refresh rate
4. **Keeps troubleshooting info** - Database stats and subsystem labels preserved

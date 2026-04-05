# Fix Summary: Rich Progress Bar Flashing in Batch Downloads

**Date**: 2026-03-05
**Issue**: Flashing/flickering progress bars during multi-threaded batch downloads
**Root Cause**: Nested Progress contexts competing for same console in multi-threaded environment

## Problem

The batch download system was experiencing flashing progress bars because:

1. **Parent coordinator** created at line ~2799 managed the main batch progress
2. **Each worker thread** created its OWN nested Progress context (line 1606)
3. **Multiple Progress contexts** competed for the same console, causing visual flickering
4. **Previous fix** (changing refresh_per_second from 4→1) was incomplete and got reverted

## Solution

Implemented thread-safe progress updates using the existing **ThreadSafeProgressCoordinator** pattern:

### Architecture

```
Parent coordinator (line ~2799)
    ↓
ThreadPoolExecutor spawns workers
    ↓
Each worker calls _backfill_new_channel_metadata(coordinator)
    ↓
Worker creates task via coordinator.add_task()
    ↓
Worker passes (coordinator, task_id) to YouTubeAPIBackfill
    ↓
YouTubeAPIBackfill updates via coordinator.update()
    ↓
Worker calls coordinator.remove_task_sync() when done
```

### Key Benefits

1. **No nested Progress contexts** - Single parent coordinator manages all updates
2. **Thread-safe updates** - Queue-based serialization prevents race conditions
3. **Optimal refresh rate** - Research shows 4-10 Hz is optimal (not 1 Hz)
4. **Backward compatible** - Legacy Progress and bool modes still supported

## Changes Made

### 1. metadata_backfill_api.py (+42 lines)

- Updated `__init__` signature to accept `tuple[coordinator, task_id]`
- Added `_coordinator` and `_task_id` instance variables
- Added coordinator update branch before parent_progress branch
- Updated docstring to document coordinator pattern

### 2. batch_downloader.py (+50 lines)

- Added `coordinator` parameter to `_backfill_new_channel_metadata()`
- Replaced nested `with Progress(...)` with `coordinator.add_task()`
- Pass coordinator tuple to YouTubeAPIBackfill
- Call `coordinator.remove_task_sync()` after completion
- Updated call site to pass coordinator parameter

### 3. test_coordinator_integration.py (new file)

- Created 5 tests to verify coordinator integration
- Tests verify: coordinator tuple acceptance, legacy Progress support, bool support, coordinator update path, and parameter passing

## Testing

All tests pass:
- 7 existing batch_downloader tests ✓
- 5 new coordinator integration tests ✓
- 2 backfill_transcription tests ✓

Total: **14/14 tests passing**

## Verification

To verify the fix works:

1. Run a batch download with multiple channels
2. Observe progress bars - should be smooth, no flashing
3. Check that all progress updates use coordinator (not nested Progress)

```bash
# Test with multiple channels
uv run python -m yt_fts batch-download --channels "@channel1,@channel2,@channel3"
```

## Related Files

- `src/yt_fts/download/progress_coordinator.py` - ThreadSafeProgressCoordinator implementation
- `src/yt_fts/download/batch_downloader.py` - Main batch download orchestration
- `src/yt_fts/services/metadata_backfill_api.py` - API backfill service
- `tests/test_coordinator_integration.py` - Coordinator integration tests

## Next Steps

1. Monitor production usage to confirm flashing is eliminated
2. Consider applying same pattern to other nested Progress contexts (if any)
3. Update documentation if coordinator pattern needs more explanation

# YouTube FTS deploy.ps1 Hanging Issue - Fix Summary

**TSK:** TSK-251225-YtFtsHangFix-6473
**Date:** 2025-12-25
**Issue:** deploy.ps1 hanging in Rich mode with no visible output

---

## Problem Diagnosis

The deploy.ps1 script executes:
```bash
python -m yt_fts batch-download "data/channels.txt" --jobs 1 \
  --cookies-from-browser firefox --rich-1 --limit 5 --max-videos 3 \
  --max-download-time 3 --continue-on-error --no-fail-fast --delay 3.0
```

### Root Causes

1. **Rich Live Display (screen=True)**
   - Takes over entire terminal in full-screen mode
   - Redirects stdout/stderr to log panel
   - Appears to "hang" during initialization with no visible output

2. **yt-dlp Pre-Check Has No Timeout**
   - `yt_dlp.extract_info()` called with NO timeout protection
   - Can hang 30+ seconds per channel on network issues
   - Location: `batch_downloader.py:785-793`

---

## Fixes Implemented

### Fix 1: Added socket_timeout to Pre-Check Options

**File:** `P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py`
**Location:** Lines 786-792 (ydl_opts dictionary)

```python
ydl_opts = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "logger": None,
    "socket_timeout": 10,  # ADD THIS - Prevent hanging on network issues
}
```

### Fix 2: Added Timeout Wrapper Using concurrent.futures

**File:** `P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py`
**Location:** Lines 781-804 (pre-check section)

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Timeout wrapper to prevent indefinite hanging
def extract_with_timeout():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(resolved_url, download=False)

try:
    # 30 second timeout for the entire pre-check operation
    with ThreadPoolExecutor(max_workers=1) as timeout_executor:
        future = timeout_executor.submit(extract_with_timeout)
        info = future.result(timeout=30)
except FuturesTimeoutError:
    # Timeout - skip pre-check and proceed with download
    log_callback(f"Pre-check timeout for {display_name} (30s), proceeding with download")
    public_video_ids = []
```

### Fix 3: Added Loading Message Before Rich Live Screen

**File:** `P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py`
**Location:** Line 622 (before Live context)

```python
# Show loading message before Live takes over the screen (fix for deploy.ps1 hang perception)
self.console.print("[blue]Initializing Rich interface...[/blue]")

# Use Live to render the layout with manual refresh to avoid threading issues
with contextlib.ExitStack() as stack:
    live = stack.enter_context(
        Live(
            layout,
            console=self.console,
            screen=True,
            ...
        )
    )
```

### Fix 4: Added --skip-precheck Flag for Debugging Bypass

**Files Modified:**
1. `P:/projects/yt-fts/src/yt_fts/core/cli.py` - Added CLI option
2. `P:/projects/yt-fts/src/yt_fts/core/cli.py` - Added function parameter
3. `P:/projects/yt-fts/src/yt_fts/core/cli.py` - Passed to BatchDownloader
4. `P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py` - Added __init__ parameter
5. `P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py` - Added conditional skip logic

**CLI Usage:**
```bash
# Bypass pre-check entirely (fastest for debugging)
python -m yt_fts batch-download "data/channels.txt" --rich-1 --skip-precheck
```

**Code Changes:**

**cli.py - Added option decorator:**
```python
@click.option(
    "--skip-precheck",
    is_flag=True,
    default=False,
    help="Skip video enumeration pre-check (bypass potential hang point, goes straight to download)",
)
```

**cli.py - Updated function signature:**
```python
def batch_download(
    ...
    max_videos: int,
    skip_precheck: bool,  # NEW PARAMETER
) -> None:
```

**cli.py - Passed to BatchDownloader:**
```python
downloader = BatchDownloader(
    ...
    max_videos=max_videos,
    skip_precheck=skip_precheck,  # Pass skip_precheck flag
)
```

**batch_downloader.py - Added to __init__:**
```python
def __init__(
    self,
    ...
    max_videos: int | None = None,
    quiet_mode: bool = False,
    skip_precheck: bool = False,  # NEW PARAMETER
):
    ...
    self.skip_precheck = skip_precheck
```

**batch_downloader.py - Added conditional skip:**
```python
# Skip pre-check if --skip-precheck flag is set
if not self.skip_precheck:
    # Pre-check logic with timeout wrapper
    ...
else:
    log_callback(f"Skipping pre-check for {display_name} (--skip-precheck flag)")
```

---

## Testing Recommendations

### Test 1: Verify Socket Timeout
```bash
# Test that socket_timeout prevents indefinite hangs
python -m yt_fts batch-download "data/channels.txt" --rich-1 --limit 1
# Should timeout after 10 seconds on network issues
```

### Test 2: Verify Overall Timeout Wrapper
```bash
# Test that the 30-second timeout wrapper works
python -m yt_fts batch-download "data/channels.txt" --rich-1 --limit 1
# Should timeout after 30 seconds total for pre-check
```

### Test 3: Verify Loading Message
```bash
# Test that loading message appears before Rich screen takeover
python -m yt_fts batch-download "data/channels.txt" --rich-1 --limit 1
# Should see "Initializing Rich interface..." before screen goes blank
```

### Test 4: Verify --skip-precheck Flag
```bash
# Test that --skip-precheck bypasses pre-check entirely
python -m yt_fts batch-download "data/channels.txt" --rich-1 --skip-precheck --limit 1
# Should log "Skipping pre-check..." and proceed directly to download
```

### Test 5: Verify deploy.ps1 Scenario
```bash
# Test the exact deploy.ps1 command
.\deploy.ps1 -channels 5 -max-videos 3 -max-time 3 -rich
# Should no longer appear to hang during initialization
```

---

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `src/yt_fts/download/batch_downloader.py` | 779-792, 781-804, 622, 80-93, 781-853 | Added socket_timeout, timeout wrapper, loading message, skip_precheck parameter |
| `src/yt_fts/core/cli.py` | ~1793-1812, 2031-2043 | Added --skip-precheck CLI option and parameter passing |

---

## Rollback Plan

If issues occur, revert changes using:

```bash
# Revert to original before fixes
git checkout HEAD~1 -- src/yt_fts/download/batch_downloader.py
git checkout HEAD~1 -- src/yt_fts/core/cli.py
```

---

## Future Improvements

1. **Configurable Timeouts** - Make socket_timeout and pre-check timeout configurable via environment variables
2. **Progressive Loading** - Show incremental progress during Rich initialization
3. **Async Pre-Check** - Use async/await for non-blocking pre-check operations
4. **Retry Logic** - Add retry with exponential backoff for pre-check failures

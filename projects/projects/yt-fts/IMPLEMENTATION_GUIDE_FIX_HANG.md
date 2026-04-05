# Implementation Guide: Fix deploy.ps1 Hanging Issue

> **For LLM Implementation:** This document contains complete context and exact code changes needed to fix the hanging issue. No additional exploration required.

---

## Problem Statement

The command `.\deploy.ps1 -channels 5 -max-videos 3 -max-time 3 -rich` hangs with no visible output.

**Root Cause:** The `--rich` flag triggers `Rich.Live(screen=True)` mode which takes over the entire terminal. The video pre-check step (`yt_dlp.extract_info()`) has NO timeout protection and can hang for 30+ seconds.

---

## Fix 1: Add Timeout to yt-dlp Pre-Check

**File:** `P:\projects\yt-fts\src\yt_fts\download\batch_downloader.py`

**Location:** Lines 779-793 (inside `_download_with_rich_layout` method)

### Current Code (lines 779-793):
```python
# FAST PRE-CHECK: Enumerate videos without downloading (2-5 seconds)
import yt_dlp

try:
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "logger": None,  # Suppress all yt-dlp console output
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(resolved_url, download=False)
```

### Replace With:
```python
# FAST PRE-CHECK: Enumerate videos without downloading (2-5 seconds)
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

try:
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "logger": None,  # Suppress all yt-dlp console output
        "socket_timeout": 10,  # Network timeout per request
    }

    # Wrap in timeout to prevent indefinite hangs
    def _extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(resolved_url, download=False)

    with ThreadPoolExecutor(max_workers=1) as timeout_executor:
        future = timeout_executor.submit(_extract_info)
        try:
            info = future.result(timeout=30)  # 30 second max for pre-check
        except FuturesTimeoutError:
            log_callback(f"[yellow]Pre-check timeout for {display_name}, proceeding anyway[/yellow]")
            info = None
```

---

## Fix 2: Add Loading Message Before Rich Live Takes Over

**File:** `P:\projects\yt-fts\src\yt_fts\download\batch_downloader.py`

**Location:** Line 624-633 (just before `Live` context manager)

### Current Code (lines 624-633):
```python
# Use ExitStack to manage stdout/stderr redirection alongside Live
with contextlib.ExitStack() as stack:
    live = stack.enter_context(
        Live(
            layout,
            console=self.console,
            screen=True,
            auto_refresh=False,
            vertical_overflow="crop",  # Prevent scrolling by cropping overflow
        )
    )
```

### Add Before (insert at line 624):
```python
# Show loading message before screen takeover
self.console.print("[bold cyan]Initializing Rich display mode...[/bold cyan]")
self.console.print("[dim]Screen will be taken over in 1 second[/dim]")
import time
time.sleep(1)

# Use ExitStack to manage stdout/stderr redirection alongside Live
```

---

## Fix 3: Add --skip-precheck Flag (Optional Enhancement)

**File:** `P:\projects\yt-fts\src\yt_fts\core\cli.py`

**Location:** After line 1792 (add new option)

### Add This Option:
```python
@click.option(
    "--skip-precheck",
    is_flag=True,
    default=False,
    help="Skip video enumeration pre-check (faster startup, may process more videos)",
)
```

**Also update the function signature at line 1794:**
```python
def batch_download(
    input_file: str,
    jobs: int,
    language: str,
    cookies_from_browser: str,
    delay: float,
    max_retries: int,
    continue_on_error: bool,
    no_fail_fast: bool,
    no_skip_initial_wait: bool,
    tui: bool,
    export_report: str,
    limit: int,
    richo: bool,
    rich: bool,
    rich_1: bool,
    max_download_time: float,
    max_videos: int,
    skip_precheck: bool,  # ADD THIS
) -> None:
```

**Pass to BatchDownloader at line 2024:**
```python
downloader = BatchDownloader(
    channels=channels,
    jobs=jobs,
    language=language,
    cookies_from_browser=cookies_from_browser,
    delay_between_channels=delay,
    max_retries=max_retries,
    continue_on_error=continue_on_error,
    rich_formatter=rich_formatter,
    rich_mode=rich_mode,
    max_download_time_seconds=max_download_time,
    max_videos=max_videos,
    skip_precheck=skip_precheck,  # ADD THIS
)
```

**File:** `P:\projects\yt-fts\src\yt_fts\download\batch_downloader.py`

**Update `__init__` (line 80) to accept skip_precheck:**
```python
def __init__(
    self,
    channels: list[str],
    jobs: int = 2,
    language: str = "en",
    cookies_from_browser: str | None = None,
    delay_between_channels: float = 3.0,
    max_retries: int = 3,
    continue_on_error: bool = True,
    rich_formatter=None,
    rich_mode: str | None = None,
    max_download_time_seconds: float | None = None,
    max_videos: int | None = None,
    quiet_mode: bool = False,
    skip_precheck: bool = False,  # ADD THIS
):
    # ... existing code ...
    self.skip_precheck = skip_precheck  # ADD THIS after line 122
```

**In `_download_with_rich_layout` (around line 775), wrap the pre-check:**
```python
if not self.skip_precheck:
    # FAST PRE-CHECK: Enumerate videos without downloading
    # ... existing pre-check code ...
else:
    log_callback(f"[dim]Skipping pre-check for {display_name}[/dim]")
    new_video_count = None  # Unknown, proceed with download
```

---

## Video Transcript Processing Pipeline (Reference)

For context, here's how transcripts are processed:

1. **Channel Resolution** (`fast_channel_resolver.py:38-72`)
   - Input: `@handle` or URL
   - Output: Full YouTube URL

2. **Pre-check** (`batch_downloader.py:776-833`) ← FIX NEEDED HERE
   - Calls `yt_dlp.extract_info()` to enumerate videos
   - Compares against database
   - Determines which videos are new

3. **Download VTTs** (`download_handler.py:1177-1275`)
   - Uses ThreadPoolExecutor for parallel downloads
   - Calls `get_vtt()` for each video
   - Respects `--max-download-time` timeout

4. **Save to DB** (`download_handler.py:1629+`)
   - Parses VTT subtitle files
   - Extracts timestamps and text
   - Stores in SQLite database

---

## Testing

After implementing fixes, test with:

```powershell
# Test 1: Without Rich mode (should work immediately)
python -m yt_fts batch-download "data/channels.txt" --limit 1 --max-videos 1 --max-download-time 60

# Test 2: With Rich mode (should now show loading message)
python -m yt_fts batch-download "data/channels.txt" --limit 1 --max-videos 1 --max-download-time 60 --rich-1

# Test 3: With skip-precheck (if implemented)
python -m yt_fts batch-download "data/channels.txt" --limit 1 --max-videos 1 --rich-1 --skip-precheck
```

---

## Files Modified

| File | Changes |
|------|---------|
| `src/yt_fts/download/batch_downloader.py` | Add timeout to pre-check, add loading message, add skip_precheck support |
| `src/yt_fts/core/cli.py` | Add --skip-precheck flag (optional) |

---

## Priority Order

1. **Fix 1** (timeout): Most important - prevents indefinite hangs
2. **Fix 2** (loading message): Quick win - improves UX
3. **Fix 3** (skip flag): Optional - for power users

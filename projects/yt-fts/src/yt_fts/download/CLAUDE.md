# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Module Context

**Module**: `download` - YouTube Download Subsystem
**Location**: `projects/yt-fts/src/yt_fts/download/`
**Complexity**: HIGH (31 Python files, multi-stage pipeline)

## Purpose

The download subsystem handles:
- Multi-channel batch video downloading from YouTube
- 3-tier quota optimization (RSS → yt-api → yt-dlp)
- Parallel processing with Rich progress bars
- Error recovery and retry logic
- Cookie-based authentication
- Channel diagnostics and caching

## Architecture

### Core Components

| File | Purpose |
|------|---------|
| `batch_downloader.py` | Main orchestrator for multi-channel downloads |
| `download_handler.py` | Per-video download execution with yt-dlp |
| `progress_coordinator.py` | Thread-safe Rich progress bar coordination |
| `parallel_processor.py` | Parallel download execution |
| `progress_tracker.py` | Progress tracking for downloads |
| `channel_cache.py` | Channel metadata caching |
| `cookie_extractor.py` | Cookie extraction for authentication |
| `error_recovery.py` | Error classification and recovery |
| `batch_enhancements.py` | Enhanced batch processing features |

### Data Flow

```
User input (channel URLs, handles)
    ↓
Unified Discovery (resolve to channel IDs)
    ↓
Channel Cache (check if already known)
    ↓
Batch Config (configure download options)
    ↓
Parallel Processor (spawn workers)
    ↓
Download Handler (yt-dlp per video)
    ↓
Progress Tracker (Rich console output)
    ↓
Database (SQLite FTS5 storage)
```

### Key Dependencies

- `yt_dlp` - YouTube download backend
- `rich` - Console progress bars
- `sqlite3` - Database storage
- `requests` - HTTP operations

## Dual-Sink Logging

This subsystem uses dual-sink logging:
- **JSON file logs** - Structured logging for debugging
- **Clean console output** - User-facing messages via Rich

```python
from yt_fts.utils.dual_sink_logger import get_logger, log_operation, log_user_message

logger = get_logger(__name__)
log_user_message("Starting download...")
log_operation("download", {"video_id": "abc123"})
```

## Error Handling

Errors are classified and user-friendly messages shown:

```python
from yt_fts.utils.retry_classifier import get_user_friendly_message
from .exceptions import DownloadTimeoutException, BaseURLFallbackFailed

try:
    # download logic
except DownloadTimeoutException:
    logger.error(get_user_friendly_message(e))
```

## Working with Cookie Files

Cookie files enable authenticated downloads:

```python
from .cookie_extractor import extract_cookies

# Extract from browser
cookies = extract_cookies(browser="chrome")

# Use in download
ydl_opts = {"cookiefile": cookies}
```

## Batch Processing

Batch processing is configurable:

```python
from .batch_config import BatchConfig

config = BatchConfig(
    max_workers=4,
    timeout_per_video=300,
    continue_on_error=True,
)
```


## Progress Coordinator

The `progress_coordinator.py` module provides thread-safe Rich progress bar coordination:

```python
from .progress_coordinator import ThreadSafeProgressCoordinator

coordinator = ThreadSafeProgressCoordinator(progress)
coordinator.start()

# Add a task
coordinator.add_task("Downloading", channel_name="@channel", total=100)

# Update progress
coordinator.update_by_channel("@channel", completed=50, fields={"stats": "50%"})

# Remove task (use before printing to avoid line wrapping)
coordinator.remove_task_sync("@channel")
# Force newline to clear residual progress content
if coordinator.progress:
    coordinator.progress.console.print("")
```

**Important**: Always call `remove_task_sync()` before printing status messages to prevent
progress bar content from appearing on the same line as subsequent output.

## Common Tasks

### Adding a New Download Option

1. Add to `batch_config.py` config class
2. Update `download_handler.py` ydl_opts
3. Add CLI argument in `src/yt_fts/core/cli.py`

### Modifying Progress Display

Progress display uses Rich:
- `progress_tracker.py` - Main progress logic
- `rich_parallel_progress.py` - Parallel progress display
- `worker_progress_tracker.py` - Per-worker tracking

### Adding Error Recovery

1. Define exception in `exceptions.py`
2. Add handler in `error_recovery.py`
3. Add user-friendly message in `retry_classifier.py`

## Related Modules

- `yt_fts/core/database.py` - Database operations
- `yt_fts/db/channels.py` - Channel database operations
- `yt_fts/utils/dual_sink_logger.py` - Logging utilities

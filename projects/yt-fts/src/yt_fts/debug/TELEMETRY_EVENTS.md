# Telemetry Event Types Reference

This document defines the standard event types used across yt-fts for consistent debugging and telemetry.

## Event Levels

| Level | Usage | Persistence (basic) | Persistence (verbose) | Persistence (debug) |
|-------|-------|---------------------|----------------------|---------------------|
| ERROR | Failures, exceptions | ✅ | ✅ | ✅ |
| WARNING | Non-critical issues, degraded functionality | ✅ | ✅ | ✅ |
| INFO | Normal operations, milestones | ❌ | ✅ | ✅ |
| DEBUG | Detailed execution flow | ❌ | ❌ | ✅ |

## Standard Event Types by Component

### `download_handler` - Video Download Operations

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `function_entry` | DEBUG | Function called | `function_name` |
| `ytdlp_config` | DEBUG | yt-dlp configuration created | `format`, `subtitleslangs`, `writesubtitles` |
| `ytdlp_success` | INFO | yt-dlp download completed | `video_id`, `title` |
| `ytdlp_failed` | ERROR | yt-dlp download failed | `error`, `video_id` |
| `transcription_attempt` | INFO | Whisper transcription started | `video_id` |
| `transcription_success` | INFO | Transcription completed | `video_id`, `duration_ms` |
| `transcription_failed` | WARNING | Transcription failed | `error`, `video_id` |

### `database` - Database Operations

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `query_start` | DEBUG | Database query started | `query_type`, `table` |
| `query_complete` | DEBUG | Database query completed | `query_type`, `rows_affected`, `duration_ms` |
| `query_failed` | ERROR | Database query failed | `error`, `query_type` |
| `connection_opened` | DEBUG | Database connection opened | `path` |
| `connection_closed` | DEBUG | Database connection closed | `duration_ms` |
| `transaction_start` | DEBUG | Transaction started | `operation` |
| `transaction_commit` | DEBUG | Transaction committed | `operation`, `changes` |
| `transaction_rollback` | WARNING | Transaction rolled back | `operation`, `reason` |

### `network` - HTTP/API Operations

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `request_start` | DEBUG | HTTP request started | `method`, `url` |
| `request_complete` | DEBUG | HTTP request completed | `method`, `url`, `status_code`, `duration_ms` |
| `request_failed` | ERROR | HTTP request failed | `error`, `url`, `status_code` |
| `retry_attempt` | WARNING | Retrying failed request | `url`, `attempt`, `max_retries` |
| `rate_limit_hit` | WARNING | Rate limit encountered | `endpoint`, `retry_after` |

### `batch_processor` - Batch Download Operations

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `batch_start` | INFO | Batch operation started | `operation`, `item_count` |
| `batch_progress` | INFO | Batch progress update | `completed`, `total`, `percent` |
| `batch_complete` | INFO | Batch operation completed | `operation`, `successful`, `failed`, `duration_sec` |
| `batch_failed` | ERROR | Batch operation failed | `operation`, `error`, `failed_items` |
| `worker_started` | DEBUG | Worker process started | `worker_id`, `items_assigned` |
| `worker_completed` | DEBUG | Worker process completed | `worker_id`, `items_processed` |

### `channel_discovery` - Channel Resolution

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `resolution_start` | DEBUG | Channel resolution started | `input` |
| `resolution_success` | DEBUG | Channel resolved | `input`, `channel_id`, `handle` |
| `resolution_failed` | WARNING | Channel resolution failed | `input`, `error` |
| `cache_hit` | DEBUG | Channel data from cache | `channel_id`, `age_hours` |
| `cache_miss` | DEBUG | Channel data not cached | `channel_id` |
| `cache_updated` | INFO | Channel cache updated | `channel_id`, `video_count` |

### `embeddings` - Vector Embeddings

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `generation_start` | INFO | Embedding generation started | `video_id`, `model` |
| `generation_complete` | INFO | Embedding generation completed | `video_id`, `segment_count`, `duration_sec` |
| `generation_failed` | WARNING | Embedding generation failed | `video_id`, `error` |
| `model_loaded` | INFO | Embedding model loaded | `model`, `device` |

### `search` - Search Operations

| Event Type | Level | Description | Data Fields |
|------------|-------|-------------|-------------|
| `search_start` | DEBUG | Search started | `query`, `search_type` |
| `search_complete` | DEBUG | Search completed | `query`, `result_count`, `duration_ms` |
| `query_expansion` | DEBUG | Query terms expanded | `original`, `expanded` |
| `vector_search` | DEBUG | Vector search executed | `result_count`, `threshold` |
| `fts_search` | DEBUG | FTS search executed | `result_count` |
| `results_merged` | DEBUG | Search results merged | `fts_count`, `vector_count`, `final_count` |

## Usage Examples

### Emitting an Event

```python
from yt_fts.debug.telemetry import get_debug_session

session = get_debug_session()
session.emit(
    level="INFO",
    component="download_handler",
    event_type="ytdlp_success",
    video_id="abc123",
    title="Video Title"
)
```

### Querying Telemetry

```python
from yt_fts.debug.telemetry import get_debug_session

session = get_debug_session()

# Get all errors for a component
errors = session.query(level="ERROR", component="download_handler")

# Get specific event types
ytdlp_events = session.query(event_type="ytdlp_success")

# Get summary
summary = session.summary()
print(f"Total events: {summary['total_events']}")
print(f"By level: {summary['by_level']}")
```

## Adding New Event Types

When adding new telemetry to a component:

1. **Choose an existing event type** if it fits the pattern
2. **Create a new event type** following the naming convention: `component_verb` or `noun_state`
3. **Document here** with level, description, and data fields
4. **Use appropriate level**: ERROR for failures, WARNING for degraded operations, INFO for milestones, DEBUG for detailed flow
5. **Include context**: Always include identifying fields like `video_id`, `channel_id`, or `query`

## CLI Usage

Enable telemetry for debugging:

```bash
# Basic level (ERROR, WARNING only)
yt-fts --enable-telemetry search "my query"

# Verbose level (includes INFO)
yt-fts --enable-telemetry --telemetry-level verbose batch-download channels.txt

# Debug level (includes all events)
yt-fts --enable-telemetry --telemetry-level debug download channel-url
```

## Telemetry Data Location

- **Database**: `~/.config/yt-fts/telemetry.db` (or `data/telemetry.db` in dev)
- **Retention**: 7 days by default
- **Max size**: 100MB by default (oldest events deleted when exceeded)

## Integration with Debug/RCA Workflow

This telemetry system integrates with the broader CSF NIP debug/RCA infrastructure:

### Two-Level Telemetry

| Level | Purpose | Location |
|-------|---------|----------|
| **Application** | yt-fts runtime events (downloads, database, network) | `src/yt_fts/debug/telemetry.py` |
| **Session** | Debug session lessons and patterns | `P:/.claude/lessons/`, `/rca` command |

### When to Use Each

**Application Telemetry** (this file):
- Use during active debugging: `yt-fts --enable-telemetry download <url>`
- Captures runtime events: yt-dlp calls, database queries, network errors
- Enables post-mortem analysis of application behavior
- Query: `SELECT * FROM debug_events WHERE level='ERROR'`

**Session Meta-Telemetry** (`/rca`, `P:/.claude/lessons/`):
- Use for recurrent issues, pattern discovery
- Captures debugging process itself: what worked, what didn't
- Stores error signatures, fix patterns, cognitive modes
- Enables cross-session learning and pattern matching

### RCA Workflow Integration

When debugging complex issues:

1. **Enable telemetry**: `yt-fts --enable-telemetry --telemetry-level debug <command>`
2. **Reproduce the issue** - Events are captured to `telemetry.db`
3. **Run `/rca`** - Root Cause Analysis with session learning
4. **Register patterns** - Successful fixes stored in CKS for future lookup

### Data Flow

```
Application Event → telemetry.py (SQLite)
                     ↓
               Debug Session completes
                     ↓
         /rca extracts patterns → CKS storage
                     ↓
         Future /debug sessions retrieve patterns
```

### Related Documentation

- `P:/__csf.nip/docs/review_bundle_debug_and_rca.md` - Full debug/RCA system reference
- `P:/.claude/commands/debug.md` - Debug command workflow
- `P:/.claude/commands/rca.md` - RCA command workflow

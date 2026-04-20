# Review Bundle: yt-is
**Generated**: 2026-04-19
**Scope**: `P:/packages/yt-is` — YouTube Intelligence System
**File Count**: 32 Python files in csf/ (+ bin/ scripts, skills/, docs/)
**Execution Mode**: 2-agents (32 Python files falls in 10–50 range)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-19
- **Scope**: `P:/packages/yt-is` — YouTube channel tracking and transcript ingestion pipeline
- **File Count**: ~131 total files (32 Python modules in csf/, plus bin/, skills/, docs/)
- **Execution Mode**: 2-agents (32 Python files in csf/ falls in 10–50 range)

### Domain & Purpose
yt-is is a high-throughput YouTube transcript ingestion pipeline that tracks channels, detects new videos via RSS + API gap resolution, and fetches transcripts through an escalation chain (yt-dlp → Selenium → NotebookLM). It was recently upgraded to "Industrial Architecture" to handle a 140,000-video backlog using NotebookLM batch processing as the primary transcript source, with yt-dlp as fallback. All state is stored in SQLite (WAL mode) for multi-terminal safety.

### Scale Metrics
- **~140,000 video** backlog target (April 2026 industrial transition)
- **743 tracked channels** (from prior session context)
- **2 SQLites**: `batch_status.sqlite` (video tracking) + `transcripts.sqlite` (cached transcripts)
- **Multi-key failover**: up to 5 YouTube API keys
- **Change frequency**: Active development — AGENTS.md references April 2026 commits

### Your Environment
- **OS**: Windows 11 Pro (bash shell, Unix-style paths)
- **Primary language**: Python 3.12+
- **Package managers**: pip, uv (for yt-dlp, curl-cffi, etc.)
- **Databases**: SQLite with WAL mode, `PRAGMA busy_timeout=5000`
- **External services**: YouTube Data API v3, NotebookLM batch API, Selenium Firefox, Gemini SDK

---

## 2. ARCHITECTURE OVERVIEW

```
User/Skill
    │
    ▼
bin/yt-is ──► bin/csf-source (main CLI, ~120KB, all commands)
    │
    ├──► add ──► source_enumerator.py ──► YouTube Data API
    │                        └─► batch_status.py (channel_metadata + analysis_status)
    │
    ├──► sync/check-all ──► RSS (15 videos) ──► Gap Detection ──► API resolution
    │                                        └─► batch_status.py (mark pending)
    │
    ├──► list ──► batch_status.py (channel_metadata table)
    │
    └──► fetch ──► BACKLOG_THRESHOLD=50
                    │
                    ├─► ≥50 pending ──► Industrial Path (NotebookLM batch)
                    │                   └─► nlm_batch.py (reusable singleton)
                    │
                    └─► <50 pending ──► Surgical Path (yt-dlp → Selenium)
                                        └─► transcript.py (escalation chain)
                                            │
                                            ├─► _fetch_via_ytdlp (WEB client + curl_cffi)
                                            ├─► _fetch_via_ytdlp_with_cookies (EJS + Firefox cookies)
                                            ├─► _fetch_via_selenium_firefox
                                            ├─► _fetch_via_notebooklm (per-video)
                                            └─► _fetch_via_whisper (audio fallback)
                    │
                    ▼
transcripts.sqlite (cache_key = video_id:lang:source)
```

### Database Schema

**`P:/__csf/.data/yt-is/batch_status.sqlite`** (shared, WAL mode):
- `analysis_status`: video_id (PK), status, updated_at, source, published_at, has_captions, title, description, channel_id, thumbnail, duration, privacy_status, upload_status, is_live_content, unavailable_reason, last_stage, failure_reason, quality_metrics
- `channel_metadata`: channel_url (PK), playlist_id, last_checked, last_full_enumeration, video_count_estimate, + API fields (title, thumbnail, subscriber_count, view_count, channel_title)
- `channel_blocklist`: channel_url (PK), blocked_at
- `download_archive`: video_id (PK), status, attempted_at, error — 24-hour retry window
- `channel_cooldown`: source (PK), cooldown_until — cross-terminal rate limit
- `provider_score`: (channel_url, provider) (PK), successes, failures, last_result — failure-aware routing
- `nlm_export_state`: composite_id (PK), notebook_id, video_ids (pipe-delimited), content_hash

**`transcripts.sqlite`** (separate, shared):
- `transcript_cache`: cache_key (PK = video_id:lang:source), video_id, lang, source, transcript, cached_at, terminal_id

---

## 3. EXECUTION AND DATA FLOW

### Channel Addition (`csf-source add <url>`)
1. `parse_channel_url()` in `source_enumerator.py` — extracts channel ID, @handle, user name
2. `get_upload_playlist_id()` — tier-1 API call to get `contentDetails.relatedPlaylists.uploads` playlist ID + `snippet.customUrl` (@handle)
3. `enumerate_full()` — paginated `playlistItems.list` to get ALL video IDs
4. `set_status_batch()` — writes all video_ids as `pending` to `analysis_status`
5. **Canonical URL rule**: Prefer API-resolved `custom_url` over input format to prevent duplicates

### Daily Sync (`csf-source check-all`)
1. Channels checked in order of `last_checked` (oldest first)
2. `check_rss()` — fetches exactly 15 most recent via RSS
3. `detect_gap()` — if RSS results don't overlap with DB and batch is old → trigger gap resolution
4. `enumerate_recent(publishedAfter=last_full_enumeration)` — API cursor to fill gaps
5. New videos marked `pending`; updated `last_checked` timestamp

### Transcript Fetch
**Industrial Path** (pending ≥ 50):
- `nlm_batch.process_industrial_batch_reusable()` — singleton NotebookLM notebook reused for up to 300 sources
- `NLMBatchIngestor.add_sources_and_wait()` — batch add YouTube URLs
- `nlm source content <id>` — raw JSON extraction via Node.js subprocess
- Fallback: retry with backoff, auth auto-recovery (`nlm login --force`)

**Surgical Path** (pending < 50):
- `fetch_transcript_chain()` — sequential escalation
- Each stage: if success → `set_cached_transcript()` + `mark_complete()`; if fail → try next
- Circuit breaker: 3 consecutive 429s → 5-minute cooldown

### Multi-Terminal Safety
- All writes use `BEGIN IMMEDIATE` (TOCTOU prevention)
- `download_archive` uses `BEGIN EXCLUSIVE`
- `PRAGMA wal_checkpoint(TRUNCATE)` after schema migrations
- `PRAGMA busy_timeout=5000` for writer-writer contention
- Cross-terminal cooldown via `channel_cooldown` table (unix timestamp)

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Purpose |
|------|---------|
| `csf/batch_status.py` (1774L) | SQLite storage with 10+ schema migrations. Thread-safe, WAL mode. Functions: `mark_complete`, `mark_failed`, `set_status`, `set_status_batch`, `get_pending_by_source`, `get_channel_metadata`, `upsert_channel`, `block_channel`. |
| `csf/source_enumerator.py` (803L) | YouTube API interactions. `parse_channel_url()`, `get_upload_playlist_id()`, `enumerate_full()`, `enumerate_recent()`, `check_rss()`, `detect_gap()`. Multi-key failover (5 API keys). |
| `csf/transcript.py` (2000+L) | Transcript fetching. Full fallback chain: yt-dlp WEB → yt-dlp+EJS → Selenium → NotebookLM → Whisper → direct_api. Circuit breakers, rate limiting, cookie caching, language config, translation support. `TranscriptResult` dataclass with `source_stage` versioning. |
| `csf/batch_scheduler.py` (276L) | Round-robin video yield across channels. 24-hour retry window. Cross-terminal cooldown via SQLite. `_BatchScheduler` singleton. |
| `csf/nlm_batch.py` (2000+L) | NotebookLM industrial batch. `NLMBatchIngestor` class, reusable notebook singleton, subbatch retry with backoff, auth auto-recovery. Pro/Ultra plan detection. |

### Utilities / Helpers

| File | Purpose |
|------|---------|
| `csf/cache.py` (361L) | Shared transcript cache. `set_cached_transcript()`, `has_cached_transcript()`, `get_cached_transcript()`. WAL mode, idempotent writes, fast existence check. |
| `csf/batch.py` | Parallel video processing. `analyze_videos_parallel()`, `process_batch()`, progress callbacks. |
| `csf/orchestrator.py` | Availability routing. Tier 3 (cached) → Tier 1 (Gemini SDK) → Tier 2 (OCR/CLIP) → transcript fallback. Failure-aware per-channel routing. |
| `csf/quota_tracker.py` | Per-key YouTube API quota tracking. |
| `csf/csf_logging.py` | Structured logging via `log_action()`. |
| `csf/_categorize.py` | Multi-topic channel tagging system (`channel_tags` table). `--status`, `--score`, `--export`, `--apply` CLI. Scores channels by topic affinity. |

### Configuration

| File | Purpose |
|------|---------|
| `config/intelligence_stream.yaml` | Intelligence stream configuration |
| `.claude-plugin/plugin.json` | Minimal plugin manifest (`name`, `description`, `version`) |

### Infrastructure

| File | Purpose |
|------|---------|
| `csf/providers/lm_studio_provider.py` | LM Studio transcript provider |
| `csf/providers/ocr_clip_provider.py` | OCR/CLIP transcript provider |
| `csf/csf_selenium.py` | Selenium Firefox setup and cookie management |
| `csf/youtube_auth.py` | YouTube authentication |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Multi-terminal safety**: All SQLite uses WAL mode + BEGIN IMMEDIATE for writes
2. **Idempotent restarts**: `download_archive` with 24-hour retry window prevents duplicate processing
3. **Escalation chain**: Never give up on a video — try next method until all fail
4. **Quality tagging**: Multi-topic channel scoring via `channel_tags` table (not category/subcategory columns)
5. **No re-add**: Adding already-tracked channel errors out (use `check` to update)

### Technology Constraints
- YouTube Data API v3 for channel/video enumeration (quota-costly)
- RSS limit = 15 most recent videos (requires gap detection + API resolution)
- NotebookLM batch: ~300 sources/notebook (Pro), ~600 (Ultra)
- yt-dlp WEB client sufficient for public videos; cookies needed for age-restricted
- Firefox required for Selenium fallback path

### Things That Must NOT Change
- `channel_metadata.channel_url` as primary key — changing breaks all downstream references
- `analysis_status.video_id` as primary key — transcript cache joins on this
- WAL mode + busy_timeout on all SQLite connections — multi-terminal safety depends on it
- `BEGIN IMMEDIATE` for status writes — TOCTOU prevention
- Video count ≥ 2 for channel acceptance — noise filter

---

## 6. KNOWN ISSUES

*(Ordered by impact — from prior session context)*

1. **Transcript quality metrics not stored**: `like_rate`, `comment_rate`, `resource_link_count`, `code_marker_count`, `ai_slop_marker_count` are computed by yt-dlp during transcript fetch but discarded. No `quality_metrics` column existed prior to this session (added as JSON TEXT column to `analysis_status`). Pre-flags (`no_transcript`, `no_resource_links`, `no_code_markers`, `possible_ai_slop`, `likely_fluff`) not yet populated.

2. **CJK drift false positive**: `cjk_drift_detector` hook was flagging channel names (database data) as "model drift" because lines containing URLs were not stripped before CJK detection. Fixed by stripping entire lines matching `^.*\(.*https?://.*\).*$` before character detection.

3. **Duplicate channel URLs**: Channels added via `/channel/UCxxx` format could create duplicate entries with different URL forms. Fixed by preferring API-resolved `custom_url` (@handle) over input URL format.

4. **Scoring not run post-migration**: 743 channels migrated from `category/subcategory` columns to `channel_tags` table — all are currently "unscored" because `python bin/csf-source _categorize --score` hasn't been run since migration.

---

## 7. INTEGRATION POINTS

### Hooks (PreToolUse / PostToolUse)
- `cjk_drift_detector.py` — flags CJK characters in model output (not channel names from DB)
- Domain tool router hooks for search optimization

### External Provider Hook
- `transcript.py::register_external_transcript_provider()` — called after all built-in methods fail
- Signature: `(video_id: str, prefer_lang: str | None) -> (success: bool, transcript: str | None, error: str | None)`

### Skill Integration
- `/yt-is` skill at `skills/yt-is/SKILL.md` — channel management
- `/yt-nlm` skill at `skills/yt-nlm/SKILL.md` — NotebookLM batch extraction

### Batch Entry Contract
- `BatchEntry` dataclass: video_id, status, source, published_at, has_captions, title, description, channel_id, thumbnail, duration, privacy_status, upload_status, is_live_content, unavailable_reason, last_stage, failure_reason

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

**Phase 1: Channel Discovery**
- **Reads**: YouTube Data API (`channels.list` with `contentDetails,statistics,snippet`)
- **Writes**: `batch_status.sqlite::channel_metadata` (upsert), `batch_status.sqlite::analysis_status` (batch insert pending videos)
- **Key constraint**: Channel rejected if ≤1 video enumerated

**Phase 2: Daily Sync**
- **Reads**: RSS feeds (15 videos per channel), `batch_status.sqlite::channel_metadata` (for `last_checked` ordering)
- **Writes**: `batch_status.sqlite::analysis_status` (new pending videos), `channel_metadata.last_checked` (updated)
- **Key constraint**: Gap detection triggers only when RSS video IDs have no overlap with DB AND batch is old

**Phase 3: Transcript Fetch**
- **Reads**: `batch_status.sqlite::analysis_status` (pending videos), `transcripts.sqlite` (skip cached)
- **Writes**: `transcripts.sqlite::transcript_cache`, `batch_status.sqlite::analysis_status` (status=complete/failed), `batch_status.sqlite::download_archive` (24h retry guard)
- **Key constraint**: Industrial path selected when pending ≥ 50; Surgical otherwise

**Phase 4: Channel Categorization**
- **Reads**: `batch_status.sqlite::channel_metadata`, `transcripts.sqlite`
- **Writes**: `batch_status.sqlite::channel_tags` (multi-topic weights per channel)
- **Key constraint**: Each channel's tag weights sum to 1.0; source='migrated' for legacy, 'categorize' for scored

---

## 9. AGENT DISPATCH DEFINITIONS

This bundle uses 2 parallel agents given 32 Python files in scope.

### Agent 1: Core Reader
- **Role**: Read core logic files and extract architecture
- **What it reads**: `csf/batch_status.py`, `csf/transcript.py`, `csf/source_enumerator.py`, `csf/nlm_batch.py`
- **Output**: Component inventory, key functions, data flow

### Agent 2: Config/Dependency Scanner
- **Role**: Read config, skills, and entry point files
- **What it reads**: `bin/csf-source`, `bin/yt-is`, `skills/yt-is/SKILL.md`, `AGENTS.md`, `config/intelligence_stream.yaml`
- **Output**: CLI contract, skill integration points, configuration

**Dispatch Order**: Parallel — both agents read simultaneously.
**Falsification**: Not applicable for review bundle.

---

## 10. FAILURE SCENARIOS

### Scenario 1: API Key Exhausted Mid-Enumeration
- **Trigger**: YouTube Data API quota (10,000 units/day) exhausted during `enumerate_full()` for a large channel
- **Propagation**: `channels.list` returns 403/429 → multi-key failover tries next key → all keys exhausted → enumeration fails
- **Detection point**: `source_enumerator.py::_api_request()` catches HTTPError 403/429
- **Actual vs expected**: Partial video list stored (up to failure point); `last_full_enumeration` not updated (allows retry on next sync)
- **Root cause**: No per-channel quota budget; enumeration is all-or-nothing

### Scenario 2: NotebookLM Auth Expired Mid-Batch
- **Trigger**: NotebookLM session expires during 200-source batch ingest
- **Propagation**: `nlm source content` returns auth error → `_ingest_batch` retries with `nlm login --force` → succeeds → continues
- **Detection point**: `nlm_batch.py` checks login before commands
- **Actual vs expected**: Auto-recovery succeeds; partial batch content stored
- **Root cause**: Auth refresh is automatic; video-level idempotency via `download_archive`

### Scenario 3: yt-dlp Bot-Check on Public Video
- **Trigger**: YouTube presents bot-check page despite using WEB client + curl_cffi TLS impersonation
- **Propagation**: `_fetch_via_ytdlp` returns "sign in to confirm" → calls `_fetch_via_ytdlp_with_cookies` (EJS + Firefox) → succeeds or fails → escalation continues
- **Detection point**: Exception message contains "sign in to confirm" or "not a bot"
- **Actual vs expected**: Second method (cookies) may work; transcript ultimately fetched or marked failed
- **Root cause**: YouTube TLS fingerprinting evolving; curl_cffi may need updates

### Scenario 4: SQLite Write Contention on Multi-Terminal Fetch
- **Trigger**: Two terminals running `csf-source fetch` simultaneously on same channel
- **Propagation**: Both write `BEGIN IMMEDIATE` → one acquires lock, other waits (busy_timeout=5000ms) → both eventually succeed or one times out
- **Detection point**: `sqlite3.OperationalError: database is locked`
- **Actual vs expected**: WAL mode + busy_timeout handles this; short lock duration means contention rarely visible
- **Root cause**: WAL allows concurrent readers; IMMEDIATE ensures writer has exclusive access

---

## 11. APPENDIX: KEY SCHEMA MIGRATIONS (batch_status.py)

```python
# Migration sequence (simplified):
CREATE TABLE analysis_status (video_id, status, updated_at, source, published_at, has_captions)
+ source (tue), published_at, has_captions, title, description, channel_id, thumbnail,
  duration, privacy_status, upload_status, is_live_content, unavailable_reason,
  last_stage, failure_reason, quality_metrics (JSON TEXT — added this session)
CREATE INDEX idx_analysis_status_source_status ON analysis_status(source, status)
CREATE TABLE download_archive, channel_cooldown
DROP COLUMN consecutive_429s (channel_cooldown)
```

**ASSUMPTION**: `quality_metrics` column (JSON TEXT) added this session may be the first write in a new migration cycle. Older DBs will get the column via `ALTER TABLE` on first access.
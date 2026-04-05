---
prd_name: yt-fts
version: 1.10.0
title: YouTube Full-Text Search CLI
author: EndUser123
status: Active
last_updated: 2026-01-02
---

# Product Requirements Document (PRD) - yt-fts

## Overview

**yt-fts** is a command-line application that scrapes YouTube channel subtitles and loads them into a searchable SQLite database.

**Key Features:**
- Full-text search across video transcripts using SQLite FTS5
- Semantic search via OpenAI/Gemini embeddings or local models
- LLM/RAG chatbot for conversational content exploration
- Video summarization using AI models
- Multi-channel support with parallel downloads
- Cross-platform compatibility (Windows, Linux, macOS)

---

## Functional Requirements

### Download & Indexing

#### FR-1: Channel Video Download
The system shall download all video subtitles from a YouTube channel or playlist and store them in a searchable database.

#### FR-2: Language Support
The system shall support downloading and searching transcripts in multiple languages.

#### FR-3: Batch Channel Processing
The system shall support processing multiple channels with configurable limits, parallel downloads, and comprehensive progress tracking.

**Acceptance Criteria:**
- AC.3.1: Progress display MUST show the human-readable channel name from the Channels table
- AC.3.2: If channel_name is not available, MUST fall back to @handle format (e.g., @3blue1brown)
- AC.3.3: If handle is not available, MUST fall back to channel/ID... format (e.g., channel/UCX...)
- AC.3.4: MUST NOT display raw truncated channel IDs (e.g., UCXKeNggiHUHpdkIfUj7...) in progress output
- AC.3.5: Progress display MUST query the database for channel_name before rendering

**Download Strategy (3-tier):**
1. **RSS Check**: Fast check for new videos on channels that are "whole" (fully synced)
2. **yt-api Scan**: Used when channel is incomplete (RSS finds videos "not in DB" = missing history)
3. **yt-dlp Fallback**: Used when RSS/yt-api fail or for direct video downloads

**Channel Completeness Logic:**
- If RSS finds videos "not in DB" → channel is INCOMPLETE → use yt-api for full scan
- If RSS finds 0 "not in DB" → channel is WHOLE → use RSS result (no new videos)
- This ensures we don't miss historical videos when first adding a channel

**Database Inconsistency Detection:**
- After yt-api stats check, compare `api_total` with `db_count`
- If `api_total > db_count` → channel is INCOMPLETE → show warning
- Warning format: "⚠ Inconsistent: DB has X/Y videos (Z missing)"
- User can then decide to run a full scan to fill gaps

### Search Capabilities

#### FR-4: Full-Text Search
The system shall provide full-text search across all indexed transcripts using SQLite FTS5.

#### FR-5: Semantic Search (vsearch)
The system shall provide semantic search using vector embeddings for concept-based queries.

#### FR-6: Unified Search
The system shall combine full-text and semantic search results in a single interface.

### AI/LLM Features

#### FR-7: Video Summarization
The system shall generate summaries of individual videos or entire channels.

#### FR-8: RAG Chatbot
The system shall provide a conversational AI interface for exploring channel content.

### Data Management

#### FR-9: Export Functionality
The system shall export transcripts and search results in multiple formats.

#### FR-10: List & Inspect Commands
The system shall provide commands to inspect the library contents.

#### FR-11: Video Status Tracking (NEW in v1.9.0)
The system shall track and categorize videos that cannot be downloaded due to various availability reasons.

**Acceptance Criteria:**
- AC.11.1: Must mark videos without available subtitles with [No Subtitles] marker
- AC.11.2: Must mark scheduled/premiere videos with [Scheduled] marker
- AC.11.3: Must mark members-only videos with [Members only] marker
- AC.11.4: Must detect and categorize unavailable videos by specific reason (deleted, private, geo-blocked)

#### FR-16: Timeout Controls (NEW in v1.9.9)
The system shall provide three-level timeout controls for batch downloads to prevent indefinite hangs.

**Acceptance Criteria:**
- AC.16.1: `--time-per-video` MUST timeout individual yt-dlp calls (extract_info, download)
- AC.16.2: `--time-per-channel` MUST limit total time spent downloading each channel
- AC.16.3: `--time-per-batch` MUST limit total time for entire batch operation
- AC.16.4: Timeout MUST be enforced at multiple checkpoints: before channel, before download, during wait
- AC.16.5: Timeout exceptions MUST be caught gracefully with clear error messages
- AC.16.6: `future.result()` MUST respect remaining channel time, not fixed timeout

**Parameters:**
- `--time-per-video <seconds>`: Timeout per yt-dlp call (default: None, no limit)
- `--time-per-channel <seconds>`: Timeout per channel download (default: None, no limit)
- `--time-per-batch <seconds>`: Timeout for entire batch (default: None, no limit)

**Additional Video Limit Parameters:**
- `--videos-download-per-channel <n>`: Videos to download per channel
- `--videos-download-per-batch <n>`: Maximum videos to download across all channels (stops when reached)
- `--channels-scan-per-batch <n>`: Limit channels to process from input file
- `--channels-download-per-batch <n>`: Stop after N channels downloaded

**Example Usage:**
```bash
# Timeout individual yt-dlp calls after 10 seconds
python -m yt_fts batch-download channels.txt --time-per-video 10

# Limit each channel to 60 seconds total
python -m yt_fts batch-download channels.txt --time-per-channel 60

# Stop entire batch after 5 minutes
python -m yt_fts batch-download channels.txt --time-per-batch 300

# Combine all three
python -m yt_fts batch-download channels.txt --time-per-video 10 --time-per-channel 60 --time-per-batch 300
```
- AC.11.5: Must NOT categorize age-restricted videos as unavailable (cookie-solvable during download)
- AC.11.6: Must display breakdown of videos without transcripts in channel stats
- AC.11.7: Must support migration functions to re-categorize videos when availability changes
- AC.11.8: Must use last_checked timestamp to track when unavailable videos were last verified

#### FR-17: Database Consistency Check (NEW in v1.10.0)
The system shall detect and report database inconsistencies where a channel has partial video data.

**Acceptance Criteria:**
- AC.17.1: Must store `api_total_video_count` from first YouTube API scan in Channels table
- AC.17.2: Must store `api_total_last_checked` timestamp when API scan occurs
- AC.17.3: Must check stored `api_total` BEFORE calling YouTube API (quota optimization)
- AC.17.4: Must display "✓ Complete (stored): X/Y videos" when using stored baseline (no quota used)
- AC.17.5: Must display warning when `api_total > db_count` (incomplete channel)
- AC.17.6: Warning format: "⚠ Inconsistent: DB has X/Y videos (Z missing)"
- AC.17.7: Must allow user to decide on full scan based on warning information
- AC.17.8: Database migration must add columns safely with duplicate detection

#### FR-18: Parallel Workers (NEW in v1.10.0)
The system shall support parallel processing of channels using ThreadPoolExecutor for improved performance.

**Acceptance Criteria:**
- AC.18.1: Must support `-w, --parallel-workers <n>` parameter to set worker thread count
- AC.18.2: Default MUST be 1 (sequential processing) for backward compatibility
- AC.18.3: Recommended 4-8 workers for metadata-only mode (`--videos-download-per-channel 0`)
- AC.18.4: Must use ThreadPoolExecutor for better SQLite concurrency than multiprocessing
- AC.18.5: Each worker thread MUST have its own database connection (check_same_thread=False)
- AC.18.6: Signal handlers MUST only register from main thread (skip in worker threads)
- AC.18.7: Worker count SHOULD be conservative based on channel count to avoid resource waste

**Parameters:**
- `-w, --parallel-workers <n>`: Number of parallel worker threads (default: 1)

**Example Usage:**
```bash
# Metadata-only with 4 parallel workers
python -m yt_fts batch-download channels.txt --videos-download-per-channel 0 -w 4

# PowerShell equivalent
.\deploy.ps1 -v 0 -w 4
```

### Diagnostics

#### FR-12: Connection Diagnostics (NEW in v1.9.6)
The system shall diagnose common download issues and provide remediation steps.

**Acceptance Criteria:**
- AC.12.1: Must check internet connectivity (Google reachable)
- AC.12.2: Must check DNS resolution (www.youtube.com resolves)
- AC.12.3: Must check YouTube reachability (main page, oembed API)
- AC.12.4: Must check yt-dlp installation and version
- AC.12.5: Must check yt-dlp functionality (video info fetch)
- AC.12.6: Must validate cookie file existence and format
- AC.12.7: Must check database file existence and size
- AC.12.8: Must check database connection (SQLite accessible)
- AC.12.9: Must check database integrity (PRAGMA quick_check)
- AC.12.10: Must display database stats (Videos, Channels, Subtitles counts)
- AC.12.11: Must support selective diagnostics (--network, --ytdlp, --cookies, --database)
- AC.12.12: Must use PRAGMA quick_check for large databases (>4GB)
- AC.12.13: Must provide color-coded Rich output (✅ PASS, ⚠️ WARN, ❌ FAIL, ℹ️ INFO)
- AC.12.14: Must include remediation suggestions for failed checks
- AC.12.15: Must support --fix flag for automatic yt-dlp installation/upgrade

#### FR-13: Dual-Sink Logging (NEW in v1.9.5)
The system shall provide a dual-sink logging system that separates technical debug logs from user console output.

**Acceptance Criteria:**
- AC.13.1: Must write structured JSON logs to file for technical debugging (timestamps, levels, context)
- AC.13.2: Must display clean, user-friendly messages in console without technical noise
- AC.13.3: Must log batch download start/completion with channel counts and results
- AC.13.4: Must log per-channel download start, success, and failure with context
- AC.13.5: Must log RSS check start/complete to help diagnose hangs
- AC.13.6: Must log retry attempts with attempt number and max retries
- AC.13.7: Must log timeout errors separately from general failures
- AC.13.8: Must sanitize sensitive information (API keys, tokens, file paths) from logs
- AC.13.9: Must use log rotation (50MB max, 5 backup files)
- AC.13.10: Must store logs in platform-appropriate location (logs/ in dev, ~/.config/yt-fts/logs in prod)

#### FR-14: Stats Display Format (NEW in v1.9.5)
The system shall display channel statistics in a compact format with visual inconsistency detection.

**Acceptance Criteria:**
- AC.14.1: Must display stats in format: (db: X total | Y subs, Z no sub, W sch, V mem | S shorts)
- AC.14.2: Must color the entire stats line in RED when total \!= sum of parts (indicating database inconsistency)
- AC.14.3: Must use default color when total equals sum of parts (indicating data integrity)
- AC.14.4: Where:
  - X total = total videos in database
  - Y subs = videos with downloadable subtitles
  - Z no sub = videos without subtitles [No Subtitles]
  - W sch = scheduled/premiere videos [Scheduled]
  - V mem = members-only videos [Members only]
  - S shorts = shorts count (excluded from total in display)
- AC.14.5: Must use this format in channel list output and batch download summaries
- AC.14.6: Must calculate sum as: Y + Z + W + V (excluding shorts from total check)

---

## Non-Functional Requirements

### Performance
- NFR-1: Search Performance - Under 2 seconds for 10,000 videos
- NFR-2: Download Performance - 100 videos per 5 minutes
- NFR-3: Startup Performance - Help in under 1 second

### Reliability
- NFR-4: Graceful Degradation
- NFR-5: Data Integrity
- NFR-6: Atomic Operations

### Usability
- NFR-7: Error Messages
- NFR-8: Progress Visibility

### Compatibility
- NFR-9: Cross-Platform Support
- NFR-10: Python Version 3.10+

### Security
- NFR-11: API Key Protection
- NFR-12: Cookie Handling

### Maintainability
- NFR-13: Code Quality
- NFR-14: Test Coverage

---

## Architecture Notes

### Database Schema
- channels table: Channel metadata (id, name, handle, url)
- videos table: Video metadata (id, title, published_at, duration, last_checked)
  - Special markers: [No Subtitles], [Scheduled], [Members only], [Unavailable/Deleted], [Unavailable/Private], [Unavailable/Geo-blocked]
- subtitles table: Transcript content with FTS5 indexing

### CLI Commands

#### Download Commands
- **download**: Download subtitles from a single YouTube channel (@handle, URL, channel_id)
- **batch-download**: Download multiple channels with parallel processing and timeout controls
- **update**: Update existing channel in database with new videos
- **update-all**: Update all channels in database

#### Search Commands
- **search**: Full-text search across all transcripts using SQLite FTS5
- **vsearch**: Semantic/vector search using embeddings for concept-based queries

#### Management Commands
- **list**: List channels, videos, or configurations in the database
- **channel-stats**: Show channel statistics and download progress
- **delete**: Remove channels, videos, or data from database
- **status**: Display system status and configuration information

#### AI/LLM Commands
- **embeddings**: Generate vector embeddings for semantic search
- **embeddings-status**: Check embeddings generation status
- **summarize**: Generate AI summaries of videos or channels
- **llm**: RAG chatbot for conversational content exploration

#### Utility Commands
- **export**: Export transcripts and search results (TXT, CSV, JSON, VTT)
- **diagnose**: Connection diagnostics with health checks
- **config**: Manage configuration settings
- **clean-channels**: Clean and optimize channel data
- **preset-channels**: Manage preset channel lists
- **convert-channels**: Convert channel data formats

### Dependencies
- yt-dlp, SQLite, Click, Rich, OpenAI/Gemini APIs, ChromaDB

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.10.0 | 2026-01-03 | Added FR-18: Parallel Workers (-w/--parallel-workers), BREAKING: Renamed timeout and limit parameters |
| 1.9.8 | 2025-01-01 | Fixed channel cache lookup to match by database channel_id, RSS message clarity fix |
| 1.9.7 | 2025-01-01 | Added FR-3 AC requirements for human-readable channel names in progress display |
| 1.9.5 | 2025-12-31 | Added FR-13: Dual-Sink Logging with structured JSON file logs and clean console output |
| 1.9.1 | 2025-12-30 | Fixed channel stats output format to use PRD bracket notation [No Subtitles], [Scheduled], etc. |
| 1.9.0 | 2025-12-30 | Added Video Status Tracking (FR-11), Enhanced unavailable video categorization, Removed age-restriction as unavailable, Migration system |
| 1.8.0 | 2025-12-30 | RSS Fast Path, Thread-Safe Progress, Base URL Fallback |
| 1.7.0 | 2025-12-29 | Batch download requirements |
| 1.6.0 | 2025-12-29 | Batch download requirements |
| 1.5.0 | 2025-12-25 | Initial PRD |

#### FR-15: Test Semantic Analysis (NEW in v1.9.6)
This is a test requirement to verify semantic doc analysis detects new FRs.


---
name: yt-nlm
description: YouTube transcript extraction via NotebookLM ephemeral notebooks
version: "1.1.0"
status: stable
enforcement: advisory
category: ingestion
triggers:
  - 'notebooklm'
  - 'nlm extract'
  - 'youtube transcripts'
  - 'transcript extraction'
aliases:
  - '/nlm'
  - '/yt-nlm'

suggest: []

workflow_steps:
  - Check for pending videos in batch_status.sqlite
  - Create ephemeral notebook per video
  - Extract transcript via nlm audio report
  - Download transcript artifact
  - Write transcript to database cache (transcripts.sqlite)
  - Delete ephemeral notebook (cleanup)
  - Combine transcripts into batches for external use

parameters:
  - name: dry-run
    description: Preview what will be ingested without processing
    type: boolean
    required: false
  - name: batch-size
    description: Transcripts per combined source
    type: integer
    default: 20

---

# /yt-nlm — NotebookLM Transcript Extraction

Extract YouTube transcripts using NotebookLM's ephemeral notebook workflow.

## Purpose

Implements the ephemeral notebook pattern from ADR-20260410: create temporary notebooks, extract transcripts, download artifacts, then cleanup. This allows using NotebookLM as an extraction tool while keeping the local database as source of truth.

## Commands

```bash
# Ingest pending videos (default behavior)
yt-nlm

# Dry run: preview what will be ingested
yt-nlm --dry-run

# Specific channel only
yt-nlm --channel "https://youtube.com/@channel"

# Batch size for combined sources
yt-nlm --batch-size 20
```

## How It Works

**Ephemeral Notebook Workflow (per video):**
1. Create ephemeral notebook: `nlm notebook create "Video {id}"`
2. Add video URL: `nlm source add <nb-id> --url <url>`
3. Extract transcript: `nlm audio report create <nb-id> --confirm`
4. Download artifact: `nlm download audio <nb-id> --output file.txt`
5. Cache to database: `set_cached_transcript(video_id, "en", "notebooklm", transcript)`
6. Delete notebook: `nlm notebook delete <nb-id> --confirm`

**Batch Combination:**
- Combines N transcripts into single markdown source
- Injects structural headers (video ID, URL, separators)
- Output ready for your knowledge system (CKS, Obsidian, analysis tools)

## Integration Points

- Reads from `batch_status.sqlite` (pending videos marked by `/yt-channel`)
- Writes to `transcripts.sqlite` cache via `csf.cache.set_cached_transcript()`
- Stores combined markdown files in `P:/__csf/.data/yt-is/transcripts/`
- Reuses `/nlm` skill CLI commands
- Compatible with `/yt-dlp` (both write to same cache database, different sources)

## Data Flow

```
/yt-channel sync
    ↓
batch_status.sqlite (pending videos)
    ↓
/yt-nlm
    ↓
Ephemeral notebooks → Transcript download → transcripts.sqlite
    ↓
Combined markdown files → Your knowledge system
```

## Storage

- **Transcripts:** `P:/__csf/.data/yt-is/transcripts/transcripts.sqlite` (cache database)
- **Combined batches:** `P:/__csf/.data/yt-is/transcripts/combined_batch_1.md`, etc.
- **Database:** `batch_status.sqlite` (status updates: pending → complete/failed)

## Requirements

- `nlm` CLI (NotebookLM command-line interface)
- NotebookLM Pro/Plus account (300 source limit)
- Internet connection for NotebookLM API

## Related Skills

- `/nlm` — NotebookLM CLI operations
- `/yt-channel` — Video discovery and tracking
- `/yt-dlp` — Local transcript download via yt-dlp

## ADR Reference

See `P:/__csf/arch_decisions/ADR-20260410-notebooklm-ephemeral-notebooks.md` for architecture decision and performance characteristics.

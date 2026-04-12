---
name: yt-nlm
description: YouTube transcript ingestion via NotebookLM (ephemeral notebooks OR import from existing notebooks)
version: "2.0.0"
status: stable
category: ingestion
enforcement: advisory
triggers:
  - 'notebooklm ingest'
  - 'transcript extraction'
  - 'youtube transcripts'
  - 'import from notebooklm'

suggest:
  - /nlm
  - /yt-channel

workflow_steps:
  - Choose scenario: Ephemeral (new videos) or Import (existing notebooks)
  - Ephemeral: Create temp notebook → add URL → extract transcript → download → cleanup
  - Import: Query existing notebooks → extract transcripts → cache locally
  - Both paths: Handle authentication expiry (auto re-auth when needed)
  - Cache transcripts to transcripts.sqlite for reuse

parameters:
  - name: run
    description: Execute ingestion (dry run without flag)
    type: boolean
    required: false
  - name: batch-size
    description: Transcripts per combined source
    type: integer
    default: 20
  - name: notebook-id
    description: Target notebook for combined sources
    type: string
    required: false

---

# /yt-nlm — YouTube Transcript Ingestion via NotebookLM

Extract YouTube transcripts using NotebookLM with two scenarios: **Ephemeral** (new videos) or **Import** (existing notebooks).

## Purpose

Two ingestion workflows for getting YouTube transcripts from NotebookLM into the local database:

1. **Ephemeral Scenario**: Create temporary notebooks, add video URLs, extract transcripts, cleanup (ADR-20260410)
2. **Import Scenario**: Query EXISTING notebooks directly, extract transcripts, cache locally

Both scenarios handle authentication expiry automatically (re-auth when session expires).

## Commands

### Scenario 1: Ephemeral (New Videos)

```bash
# Dry run: show pending videos
python -m csf.csf_nlm_ingest

# Ingest pending videos
python -m csf.csf_nlm_ingest --run

# Specific channel only
python -m csf.csf_nlm_ingest --run --channel "https://youtube.com/@channel"

# Batch size for combined sources
python -m csf.csf_nlm_ingest --run --batch-size 20

# Target notebook for combined sources
python -m csf.csf_nlm_ingest --run --notebook-id <uuid>
```

### Scenario 2: Import from Existing Notebooks

```bash
# Dry run: preview import from all notebooks
python -m csf.csf_nlm_import --dry-run

# Import from specific notebook only (small notebooks <50 videos)
python -m csf.csf_nlm_import --notebook "yt-AI Stack Studio"

# Import from all notebooks (WARNING: 1,156 videos takes ~1 hour)
# Run directly in terminal, not through Claude Code:
python -m csf.csf_nlm_import
```

**Timeout Notes:**
- Rate limit: 2-second delay per video = ~10 minutes minimum per 300 videos
- Resume: Interrupted runs continue from last checkpoint (cached videos are skipped)
- Progress: Checkpoint every 10 videos shows running stats
- **For 200+ video notebooks**: Run directly in terminal, not through Claude Code CLI

## How It Works

### Scenario 1: Ephemeral Notebook Workflow (NEW videos)

For each pending video:
1. Check authentication (`nlm notebook list --quiet`)
2. Create ephemeral notebook: `nlm notebook create "Video {id}"`
3. Add video URL: `nlm source add <nb-id> --url <url>`
4. Extract transcript: `nlm notebook query <nb-id> "Extract the complete transcript..."`
5. Download artifact: `nlm download audio <nb-id> --output file.txt`
6. Delete notebook: `nlm notebook delete <nb-id> --confirm`
7. Cache transcript locally via `csf.cache.set_cached_transcript()`

**Batch Combination:**
- Combines N transcripts into single markdown source
- Injects structural headers (video ID, URL, separators)
- Prevents RAG "haystack problem" in NotebookLM queries

### Scenario 2: Import from Existing Notebooks

For each notebook with existing YouTube sources:
1. Check authentication (re-auth if expired)
2. List sources: `nlm source list <notebook-id> --json`
3. For each video source:
   - Check if already cached (`has_cached_transcript()`)
   - If cached: SKIP
   - If not cached: Query transcript `nlm notebook query <nb-id> "Extract COMPLETE FULL transcript for '{title}'..."`
   - Cache via `set_cached_transcript(video_id, "en", "notebooklm", transcript)`
4. Report: total, imported, skipped, failed

**Authentication Handling (Both Scenarios):**
- `check_auth()`: Validates session via `nlm notebook list --quiet`
- `ensure_auth()`: Re-authenticates if session expired
- Auto-retry on auth errors during transcript extraction

## Integration Points

- Reads from `batch_status.sqlite` (pending videos marked by `/yt-channel`)
- Stores transcripts in `transcripts.sqlite` via `csf.cache`
- Reuses `/nlm` skill CLI commands
- Compatible with `/yt-batch-fetch` (can run both, compare results)

## Files

| File | Purpose | Scenario |
|------|---------|----------|
| `csf/csf_nlm_ingest.py` | Ephemeral notebook workflow | Scenario 1 (new videos) |
| `csf/csf_nlm_import.py` | Import from existing notebooks | Scenario 2 (bulk import) |
| `csf/cache.py` | Transcript caching (`set_cached_transcript()`, `has_cached_transcript()`) | Both scenarios |
| `csf/transcript.py` | YouTube metadata extraction | Both scenarios |

## Data Flow

### Scenario 1: Ephemeral (New Videos)

```
/yt-channel sync
    ↓
batch_status.sqlite (pending videos)
    ↓
python -m csf.csf_nlm_ingest --run
    ↓
Ephemeral notebooks → Transcript download → Cleanup
    ↓
Combined markdown sources → Persistent notebook
```

### Scenario 2: Import (Existing Notebooks)

```
Existing NotebookLM notebooks (7 yt-* notebooks)
    ↓
python -m csf.csf_nlm_import --run
    ↓
Query each notebook → Extract transcripts → Cache to transcripts.sqlite
    ↓
Local database populated with 1,156 videos
```

## Storage

Both scenarios use the same local caching system:

- **Transcripts:** `transcripts.sqlite` (via `csf.cache`)
  - Schema: `cache_key` (video_id:lang:source), `transcript_text`, `created_at`
  - Validation: `has_cached_transcript()` checks before re-downloading
- **Ephemeral batches:** `combined_batch_1.md`, `combined_batch_2.md`, etc. (Scenario 1 only)
- **Status tracking:** `batch_status.sqlite` (Scenario 1 only)

## Notebooks Currently Tracked (Scenario 2)

| Notebook | ID | Videos |
|----------|-----|--------|
| yt-Universe of AI | 852ffa34-32b3-45ea-b9c2-47e2cc53e6a7 | ~150 |
| yt-Lev Selector | a384432c-2aff-4516-95f5-af171af10947 | ~275 |
| yt-Luuk Alleman | 5ce6601d-2262-4690-a033-7520e0641960 | 93 (✅ imported) |
| yt-AI LABS | 6f701ff1-6d50-45a7-b6ab-f4f6c0daed1d | ~80 |
| yt-Sean Kochel | b9460dae-a7cc-49a0-9a1b-364c53ef38e1 | ~60 |
| yt-AI Stack Studio | 54f48773-c623-4751-be2d-1b6289ff30ac | 116 (✅ imported) |
| yt-Chase AI | 5d95cffd-365b-4906-b3cc-f82fd4a98e06 | ~90 |

**Total: ~1,156 videos across 7 notebooks**

## Requirements

- `nlm` CLI (NotebookLM command-line interface)
- NotebookLM Pro/Plus account (300 source limit)
- Internet connection for NotebookLM API
- **Authentication**: Sessions expire after ~20 minutes; both scenarios handle auto-re-auth

## Authentication

Both scenarios include automatic authentication handling:

```python
def check_auth() -> bool:
    """Verify nlm authentication is valid."""
    result = subprocess.run(["nlm", "notebook", "list", "--quiet"], ...)
    return result.returncode == 0

def ensure_auth() -> None:
    """Re-authenticate if session expired."""
    if not check_auth():
        subprocess.run(["nlm", "login"], ...)
```

This prevents the "Authentication expired" errors that were causing import failures.

## Related Skills

- `/nlm` — NotebookLM CLI operations
- `/yt-channel` — Video discovery and tracking
- `/yt-batch-fetch` — Local transcript download via yt-dlp

## ADR Reference

See `P:/__csf/arch_decisions/ADR-20260410-notebooklm-ephemeral-notebooks.md` for architecture decision and performance characteristics.

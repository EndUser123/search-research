---
date: 2026-03-29
template: deep
query: "Design an architecture for intelligence-stream additions: (1) NotebookLM auto-import with consolidation batching to stay under 300 files/notebook and 500K words/file limits, (2) Multi-language transcript support with automatic translation to English when original language is unavailable"
domain: python
confidence: 78
research_sources: []
---

# ADR-20260329: intelligence-stream — NotebookLM Consolidation + i18n

## Status

Accepted

## Context

Intelligence-stream currently ingests and analyzes YouTube videos, storing results in CKS. Two gaps limit its utility at scale:

1. **NotebookLM scale gap**: With 10,000+ videos, importing each as a separate source exceeds NotebookLM's hard limits (300 sources/notebook, 500K words/file). Need a consolidation layer that batches transcript+analysis into composite source documents.

2. **Language gap**: The transcript pipeline hardcodes English. Many valuable channels are non-English. Need multi-language fetch + English translation fallback.

## Core Contracts

### Contract 1: NLM Export State

```python
# Stored in batch_status.sqlite — same DB as existing analysis_status
CREATE TABLE nlm_export_state (
    composite_id    TEXT PRIMARY KEY,   -- hash of (notebook_id, batch_group_key)
    notebook_id    TEXT NOT NULL,
    batch_key      TEXT NOT NULL,     -- e.g. "channel:UCxxxxx:part1"
    video_ids      TEXT NOT NULL,     -- JSON list of included video_ids
    word_count     INTEGER NOT NULL,
    nlm_source_id  TEXT,              -- set after successful import
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- Index for finding which composite a video belongs to
CREATE INDEX idx_nlm_export_video ON nlm_export_state(video_ids);
```

### Contract 2: NLM Composite Document Format

```
Title: [Channel Name] — [Date Range or Part N]

Sources:
- youtube.com/channel/UCxxxxx/videos (channel playlist)
- youtube.com/watch?v=vid1
- youtube.com/watch?v=vid2
...

=== TRANSCRIPT COLLECTION ===

[vid1] Video Title (published YYYY-MM-DD)
---
(transcript text)
---

[vid2] Video Title (published YYYY-MM-DD)
---
(transcript text)
---
```

### Contract 3: Language Parameter

```python
@dataclass
class TranscriptResult:
    video_id: str
    lang: str                    # BCP-47: "en", "ja", "de", "zh-Hans", etc.
    raw_lang: str | None        # Original language if translated
    was_translated: bool
    transcript: str
    source: str                  # Which fetcher succeeded


@dataclass
class LanguageConfig:
    prefer_lang: str = "en"      # BCP-47
    allow_translation: bool = True
    translation_provider: str = "google"  # or "libre"
```

## Architecture

### Feature 1: NotebookLM Consolidation Exporter (`csf/nlm_exporter.py`)

#### Design Decision: Composite-per-batch, not composite-per-video

**Option A: One composite per video** — REJECTED. 10,000 videos = 10,000 sources = 34 notebooks minimum, each with 1 source. Poor NotebookLM UX.

**Option B: One composite per channel, unbounded word count** — REJECTED. A popular channel with 500 videos could produce a 1M-word document, exceeding NotebookLM's 500K/file limit.

**Option C: Channel-partitioned, word-bounded composites** — SELECTED. Group by channel first (preserves topical coherence), then split into ≤500K-word chunks. Each chunk becomes one `text` source in NotebookLM.

#### Batching Algorithm

```
Input: videos where status='complete' AND NOT already exported to NLM
Group videos by source_channel
For each channel group:
  Sort videos by published_at ASC
  Split into ≤500K-word sub-batches
  For each sub-batch:
    Generate composite_id = hash(notebook_id + channel_id + batch_index)
    Build composite document (see format above)
    Check if nlm_source_id already set → idempotent skip
    Otherwise write to .nlm_exports/ composite .txt file
    Call nlm source add --text
    Record nlm_source_id in nlm_export_state
```

#### Multi-notebook Routing

- If total composites > 300: split into multiple notebooks (e.g., "IS-ChanA-part1", "IS-ChanA-part2")
- Notebook naming: `intelligence-stream-[topic-or-channel-abbr]-[YYYYMMDD]`

#### Idempotency

- Before creating composite: check `nlm_export_state` for existing `nlm_source_id`
- Uses `BEGIN IMMEDIATE` transaction (same pattern as `batch_status.py:181`)
- Safe for concurrent terminal execution

#### Storage Layout

```
P:/__csf/.data/intelligence-stream/nlm_exports/
  composites/
    {composite_id}.txt    # The composite text document
  state/
    (managed by batch_status.sqlite nlm_export_state table)
```

### Feature 2: i18n Transcript Pipeline

#### Language Detection

`youtube-transcript-api` supports 100+ languages natively. The fetch chain tries the requested language first, then falls back to any available language. After fetching, if the result is not in the requested language AND `allow_translation=True`, translate to the requested language.

#### Translation Providers

| Provider | Cost | Languages | Notes |
|----------|------|----------|-------|
| Google Translate CLI | Free (unofficial) | 100+ | `trans!` npm package (not installed); rate-limited |
| LibreTranslate | Free (self-hosted) | 40+ | Requires running server; better for high volume |
| Gemini SDK | Pay-per-char | 100+ | Already available via `GEMINI_API_KEY` |

**Decision**: Use Gemini SDK as sole translation provider (already has API key for video analysis). Google Translate CLI (`trans!`) not installed.

#### Changes to `transcript.py`

| Location | Change |
|----------|--------|
| `_fetch_via_youtube_transcript_api` (line 99) | Uses `lang` param already; extend to try `lang` → any → translate |
| `_fetch_via_youtubei` (line 117) | Add `lang` parameter; currently ignored |
| `_fetch_via_sdk` (line 138) | Add `lang` parameter; currently ignored |
| `_fetch_via_gemini_cli` (line 50) | Add `--lang` flag to CLI; currently ignored |
| New: `_translate_text(text, from_lang, to_lang)` | Gemini SDK translation; 50ms/1K chars |
| New: `fetch_transcript_chain(video_id, config: LanguageConfig)` | Returns `TranscriptResult` with full metadata |

#### Translation Fallback Chain

```
fetch_transcript_chain(video_id, prefer_lang="ja"):

1. Try youtube_transcript_api with languages=["ja"]
   → success: check if result is actually Japanese
   → not Japanese: mark was_translated=False, return as-is

2. Try youtube_transcript_api with languages=["en", "ja", any]
   → Got Japanese: mark was_translated=False, return Japanese

3. Got non-Japanese or failed:
   → If allow_translation AND GEMINI_API_KEY:
        translate original → "ja"
        mark was_translated=True

4. All failed: return (False, None, "No transcript")
```

## Data Flow

```
csf-source add <url>
  → enumerate_full() → batch_status pending
  → batch.analyze_videos_parallel()
  → csf-analyze --video-id <id>
       → fetch_transcript_chain(video_id, lang_config)
       │    ├── youtube_transcript_api (with lang)
       │    ├── youtubei (with lang)
       │    ├── Gemini SDK transcript
       │    └── Gemini SDK translate (if needed)
       → Gemini analysis → CKS append
       → mark_complete(video_id)

csf-nlm sync [--notebook <name>]
  → query completed-but-not-exported videos from batch_status
  → group_by_channel → split_into_≤500K_word_batches
  → write composite .txt files to .nlm_exports/
  → nlm source add --text for each composite
  → record nlm_source_id in nlm_export_state table
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|---------|-----------|
| Composite boundary | Channel-first, word-count-split | Preserves topical coherence; prevents 500K overflow |
| Idempotency | composite_id hash + nlm_source_id check | Safe for multi-terminal; no duplicate uploads |
| Translation trigger | Non-English result + `allow_translation=True` | Avoids translate API cost when already English |
| Translation provider | Gemini SDK (existing key) → Google Translate CLI fallback | No new API key needed; free fallback available |
| Notebook splitting | When composites > 300 | Hard limit; auto-routing prevents manual notebook management |

## Multi-Terminal Safety

- `nlm_export_state` table uses SQLite WAL mode (same as `batch_status.py:61`)
- `BEGIN IMMEDIATE` for all writes (same pattern as `batch_status.py:181`)
- Composite files in `.nlm_exports/composites/` are append-only (never modified after creation)
- `nlm_source_id` is set exactly once per `composite_id`; never overwritten

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Channel has >300 videos | Splits into multiple composites: "UCxxx-part1", "UCxxx-part2" |
| Composite word count still >500K | Further split: by date range (quarterly) or by video count (max 50 videos/composite) |
| nlm CLI auth expired | Log error; skip batch; next sync retries |
| Translation yields garbled text | Mark `was_translated=True`; user can query source language separately |
| Video already in CKS but not yet exported | Remains in pending export state; exported on next sync |
| Two terminals run sync simultaneously | `BEGIN IMMEDIATE` + composite_id uniqueness = one wins, one skips idempotently |

## Implementation Phases

### Phase 1 (Core — ~5 tasks): Transcript i18n
1. Add `LanguageConfig` dataclass to `transcript.py`
2. Plumb `lang` through all four fetch methods (youtubei, sdk, cli — currently ignored)
3. Add `_translate_text()` using Gemini SDK
4. Update `fetch_transcript_chain()` to use `LanguageConfig` and return `TranscriptResult`
5. Add integration tests for language parameterization

### Phase 2 (Core — ~4 tasks): NLM Exporter
1. Add `nlm_export_state` table to `batch_status.py`
2. Create `csf/nlm_exporter.py` with composite batching algorithm
3. Create `bin/csf-nlm` CLI: `sync`, `status`, `preview`
4. Add idempotency tests

### Phase 3 (Optional — when 300-source limit approaches)
1. Multi-notebook routing: auto-create "IS-part2" notebooks
2. Tag-based notebook organization (by topic cluster)

## Dependency Audit

| Dependency | Classification | Notes |
|------------|---------------|-------|
| `youtube-transcript-api` | MUST | Already used; supports 100+ langs |
| `gemini` CLI | MUST | Already used for analysis; add `--lang` flag |
| Gemini SDK (translate) | MUST | Already have `GEMINI_API_KEY` |
| Google Translate CLI (`trans!`) | Won't use | Not installed; Gemini SDK only |
| NotebookLM MCP/CLI | MUST | Already have via nlm |
| SQLite WAL | Already present | `batch_status.py:61` |

## Confirmed Tool Versions (from codebase analysis)

- `youtube-transcript-api` — already in `requirements.txt`; `languages=[lang]` param at `transcript.py:99`
- `google-genai` — already in `requirements.txt`; client at `transcript.py:150`
- `gemini` CLI — `which("gemini")` check at `transcript.py:56`
- SQLite WAL — `batch_status.py:61` (`PRAGMA journal_mode=WAL`)

## Confidence: 78%

**Evidence basis:**
- NotebookLM API limits (300 sources, 500K words): confirmed from nlm MCP tools documentation
- youtube-transcript-api language support: from training knowledge (100+ languages)
- All other constraints derived from existing code analysis

**Key assumptions:**
1. Gemini API key is available for translation (already in environment for video analysis)
2. nlm CLI is authenticated (user will run `nlm login` once)
3. Average video transcript is ~2,000 words (used for composite sizing estimates)

## Adversarial Self-Review

**Weakest assumption:** That Gemini SDK can reliably detect language and translate. If Gemini has poor multilingual output quality for certain language pairs (e.g., Japanese technical terms), translated transcripts could be semantically degraded.

**Mitigation:** Make translation opt-in via `allow_translation=False` config. Default to `True` but allow users to set `PREFER_LANG` without translation (just fetches whatever language is available).

**Verification status:** Partially confirmed. Gemini 2.0 supports 100+ languages and has documented translation capabilities, but specific language pair quality (e.g., JA→EN for technical content) is untested in this codebase.

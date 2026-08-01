---
tags: [yt-is, notebooklm, pipeline, resilience, fallback-chain, transcript-ingestion, automation]
created: 2026-04-12
sources:
  - sources/downloads/yt-is-notebooklm-pipeline-improvements.md
summary: Analysis of yt-is NotebookLM pipeline with 6-month improvement roadmap: failure taxonomy, quota-aware behavior, non-Google fallbacks, operational UX, and codebase hygiene.
---

# yt-is NotebookLM Pipeline — 6-Month Improvement Roadmap

Analysis of the yt-is NotebookLM fallback pipeline with concrete opportunities to improve predictability, observability, and resilience over a 6-month horizon.

## Current Architecture Overview

The pipeline uses NotebookLM's **ephemeral notebook pattern** as a fallback when direct YouTube scraping (yt-dlp) fails. It leverages NotebookLM's infrastructure to extract transcripts that might be blocked at the direct scraping layer.

### Fallback Chain

```
/yt-channel sync
↓
batch_status.sqlite (pending videos)
↓
yt-dlp (primary) → yt-dlp+cookies (fallback) → Selenium (fallback) → NotebookLM (final fallback)
↓
transcripts.sqlite (cache)
```

### Two Entry Points

1. **/yt-nlm skill** — Standalone CLI for NotebookLM-only ingestion
   - Reads pending videos from batch_status.sqlite
   - Processes them via ephemeral notebook workflow
   - Stores results in transcripts.sqlite

2. **_fetch_via_notebooklm() in transcript.py** — Called automatically by the fallback chain
   - Triggered when yt-dlp and Selenium both fail
   - Single-video workflow (creates one notebook per video)

### Performance Comparison

| Metric | Old (per-video) | New (batch) |
|--------|-----------------|-------------|
| Notebooks created | 1 per video | 1 per 300 videos |
| Auth prompts | Manual (failed on expiry) | Auto-recovery |
| Transcript method | nlm notebook query (LLM) | nlm source content (raw) |
| Per-video overhead | ~45-60s | ~10-15s effective |

## Key Improvement Areas

### 1. Failure Modes, Quotas, and Resilience

#### 1.1 Explicit Failure Taxonomy & State

**Problem:** "Fallback chain" is implicit—yt-dlp → cookies → Selenium → NLM. Not clear *why* a video failed or *which step* handled it.

**Improvement:** Extend `batch_status.sqlite` schema with:
- **`last_stage`**: `yt_dlp`, `yt_dlp_cookies`, `selenium`, `nlm`, `give_up`
- **`failure_reason`**: short string/enum (e.g., `region_block`, `age_gate`, `no_transcript`, `quota_exceeded`, `captcha`, `nlm_import_failed`)
- **`attempts`** / **`next_retry_at`** for controlled backoff

**Benefits:**
- Spot systemic issues (e.g., NLM import failing for a whole channel)
- Selectively re-run only videos blocked by a *now-fixed* stage
- Avoid thrashing NLM on videos that repeatedly fail

#### 1.2 Graceful Degradation When NLM Quotas Change

**Problem:** NotebookLM source limits differ by tier and have changed:
- Standard: ~50 sources/notebook
- Pro: ~300 sources
- Ultra: ~600 sources

Currently hard-coded at **300**—brittle if Google changes tiers.

**Improvement:**
- Add **runtime-configurable `NLM_MAX_SOURCES_PER_NOTEBOOK`** (env/CLI/config)
- Add **quota-aware behavior**:
  - If `--youtube` add fails due to limits, split the batch and continue
  - Detect "source limit reached" / "Daily quota exceeded" errors:
    - Mark batch as **`nlm_deferred`** with `next_retry_at`
    - Avoid retrying within the same 24h window

### 2. Coverage: Reducing Dependence on Single External Fallback

**Problem:** "Last chance" is NotebookLM—if it fails (no transcript, import error), system gives up.

#### 2.1 Add At Least One Non-Google Fallback

**Options:**
- **YouTube Transcript API wrappers**: OSS tools that pull transcripts via YouTube's API rather than scraping
- **Custom small service**: Python service using:
  - YouTube's official **captions API** where possible
  - Last resort: headless **play-and-capture** + offline ASR (Whisper/local model) for *high-value* videos only

**Implementation:** Wire in an **optional "external transcript provider" hook** in `get_transcript()` after NLM fails:

```python
def get_transcript(video_id, url):
    # yt-dlp, cookies, selenium ...
    transcript = _fetch_via_notebooklm(...)
    if transcript:
        return transcript

    transcript = _fetch_via_external_service(video_id, url)
    if transcript:
        return transcript

    # mark final failure
```

#### 2.2 Use NLM for What Only NLM Can Do

- Use NLM only when:
  - You actually need **NLM-specific value** (e.g., cross-source synthesis)
  - Or yt-dlp + others **cannot** obtain captions
- For "just fetch transcript," invest more in:
  - yt-dlp config (sleep, rate limit, cookies, user agent)
  - A robust transcript API fallback

### 3. Operational UX: Visibility and Control

#### 3.1 Proper Logging / Telemetry

- Standardize a **structured log line** per video per stage:
  - `video_id`, `stage`, `status`, `duration_ms`, `error_code`, `attempt`
- Aggregate into a simple **terminal dashboard**:
  - Counts of `pending / processing / complete / failed` per stage
  - Per-stage median/95th-percentile wall time

**Backed by:**
- Another SQLite table summarizing batch runs, or
- Simple CSV + small CLI to render status

#### 3.2 First-class "inspect video" Command

```bash
yt-is inspect <video_id>
```

**Prints:**
- Status in `batch_status`
- Where transcript came from (yt-dlp, Selenium, NLM, external)
- Last error, timestamps, transcript length (chars/tokens)

### 4. Auth and Credentials Hardening

You already have `_ensure_nlm_auth()` with **auto-recovery** via `nlm login --force`.

**Improvements:**
- Add **rate limiting** on forced logins: if login fails N times in a window, stop trying and mark **`nlm_auth_broken`**
- Persist **last successful auth timestamp** and log when auth flaps frequently
- For **yt-dlp cookies**:
  - Track when cookies last updated
  - Add periodic check to verify they still work on a canary video

### 5. Performance and Concurrency

Currently ~**10–15s effective per video** on batch vs ~45-60s on per-video.

**Improvements:**
- **Concurrency with backpressure**: Allow **parallel `nlm source content` calls** (3–5 in flight) to respect NLM and network
- **yt-dlp worker pool**: Small pool of **concurrent yt-dlp** workers with sleep intervals to avoid bot detection
- **Prioritization**: Track **priority** in `batch_status`:
  - New uploads from favored channels
  - "Manually requested" videos from CLI
  - Schedule high-priority ones first

### 6. Data Quality, Deduplication, and Drift

#### 6.1 Transcript Versioning & Validation

YouTube captions can change; different stages may produce slightly different text.

**Improvements:**
- Add fields: **`source_stage`**, **`fetched_at`**, **`version`** (increment), **`language`**
- If re-fetched from *better* source (e.g., yt-dlp after previously using NLM), let it **supersede** older one while preserving history
- Add lightweight **checksum** (hash of normalized text) to detect changes vs re-fetching identical content

#### 6.2 Language and Missing-Caption Handling

- Store **`language_detected`** (from metadata or language-id)
- Record whether transcript is **auto-generated** vs creator uploaded
- Tag LLM-generated ASR (e.g., offline Whisper) clearly for explainability

### 7. Interface & Codebase Hygiene

#### 7.1 Normalize All Transcript Sources Behind One Interface

```python
@dataclass
class Transcript:
    video_id: str
    text: str
    source_stage: str  # 'yt_dlp', 'nlm', 'external', 'whisper'
    language: str | None
    fetched_at: datetime
    version: int
```

**Benefits:**
- Future fallbacks are one small adapter rather than "yet another custom path"
- Add cross-cutting behaviors (sanitization, trimming, segmentation) once

#### 7.2 Sunset the Old Per-Video NLM Script

`csf_nlm_ingest.py` is "old standalone script":
- Mark it **deprecated in code** and help text
- Build missing features directly into `/yt-nlm` skill
- Eventually delete to reduce cognitive load and divergence

## User-Facing Happiness in 6 Months

Implementing a subset of above gives future-you:

- **Fewer "mystery misses"**: Know exactly *why* a transcript isn't there, and whether to expect retry
- **Less fragility to Google changes**: NLM limits and auth issues become routine events, not fire drills
- **Higher overall coverage**: Additional non-NLM fallback improves total transcripts fetched
- **Safer iteration**: Normalized interface and explicit state mean adding new transcript source is low-risk and reversible

## Key Takeaways

1. Add **richer failure state** and **per-video introspection** so you always know where and why a video failed
2. Make NLM usage **quota- and tier-aware**, with configurable limits and better error handling
3. Introduce at least **one non-NotebookLM transcript provider** as final fallback
4. Normalize transcript outputs, version them, and surface **source + quality metadata**
5. Incrementally add **concurrency, prioritization, and logging** for performance and operability

## Related

- [[wiki/entities/notebooklm-exporter]]@related — NotebookLM to Markdown export tool
- [[wiki/concepts/yt-dlp-fallback-patterns]]@related — YouTube scraping fallback strategies
- [[wiki/entities/yt-is-cli]]@supersedes — Updated CLI with improvements

## Sources

- `sources/downloads/yt-is-notebooklm-pipeline-improvements.md` — Full Perplexity analysis (2026-04-12)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

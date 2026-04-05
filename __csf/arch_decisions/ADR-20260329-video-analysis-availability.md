# ADR-20260329-video-analysis-availability: Tiered Video Analysis with Graceful Degradation

**Status:** Proposed
**Date:** 2026-03-29

### Decision

Add an OCR/CLIP-based fallback pipeline as a third availability state alongside the existing Gemini video passthrough and transcript-only paths. The orchestrator routes to the best available method. Summarization is done directly by the LLM (no external API needed).

### Rationale

- Gemini 3.1 Flash-Lite Preview quota is generous but **not unlimited** (20 RPD per project on free tier)
- YouTube transcript API is **always free** and available for every video
- OCR captures **code-on-screen** that transcripts miss
- CLIP captures **any relevant visual information** (charts, diagrams, UI flows, slides, architecture drawings) that transcripts miss
- EasyOCR + CLIP run **locally** — no external API calls for OCR/image analysis
- Summarization is done **directly by the LLM** — no external LLM API needed (I process transcript + code + visual tags into structured output)
- This means **zero API cost** for the entire fallback pipeline

### Alternatives Considered

| Option | Description | Why Rejected |
|--------|-------------|--------------|
| **OCR-First** | Replace Gemini entirely with OCR pipeline | Loses Gemini multi-modal quality for visual understanding |
| **Federated Strategy** | Runtime routing between Gemini/OCR/Minimax as equal providers | Over-engineered — OCR is always second choice when Gemini works |

### Multi-Terminal Safety
- **Safe** — SQLite WAL mode + `has_cached_transcript()` pre-check handles concurrent batch workers
- Transcript cache is per-video, not shared mutable state
- `_gemini_available` flag is per-process (resets daily with quota)

### Edge Cases
- **Gemini recovers mid-batch:** Orchestrator detects quota reset at midnight PT, flips flag
- **FFmpeg not on PATH:** Falls back to `transcript-only` mode; logs warning
- **OCR fails:** Returns partial result (transcript + code_snippets=[], visual_tags=[]) — non-fatal, LLM summarization still runs
- **Local vs YouTube:** OCR pipeline works for MP4 (local) via Whisper ASR; YouTube uses transcript API

### Implementation Phases

| Phase | What | Files |
|-------|------|-------|
| 1 | Provider interface + Orchestrator | `csf/analyze.py`, `csf/providers/` |
| 2 | Video frame extraction (ffmpeg) | `csf/video_utils.py` |
| 3 | OCR client (EasyOCR/Tesseract) | `csf/ocr_client.py` |
| 4 | CLIP visual tagger | `csf/clip_client.py` |
| 5 | LLM direct summarization (transcript + code + tags → structured output) | `csf/summarize.py` |
| 6 | Batch.py integration | `analyze_videos_parallel` routes via orchestrator |

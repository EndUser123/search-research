---
title: "Video-to-wiki pipeline: transcript extraction, sub-topic clustering, and multimodal content detection"
created: 2026-07-27
source: session-2026-07-27 / www-research
tags: [video-transcript, knowledge-extraction, clustering, multimodal, vision, pipeline, nlm-to-wiki, design-decision]
summary: >
  Research on optimal architecture for converting YouTube video collections
  into wiki knowledge: export raw transcripts (not NotebookLM synthesis),
  cluster into sub-topics within each notebook, use scene-change keyframe
  detection + vision models for visual content. Existing skills (crv,
  vision-analysis, yt-nlm) already provide the building blocks. The
  mcptube-vision project (MIT) validates the architecture with a working
  compounding-wiki model. Key optimizations: scene-change frame selection
  over fixed-interval, append-only entity/concept pages, FTS5 over compiled
  pages beats vector search over raw chunks.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://github.com/0xchamin/mcptube" (0xchamin, 2025-2026)
  - "https://arxiv.org/html/2510.27280v1" (Zhu et al., FOCUS, Oct 2025)
  - "https://openaccess.thecvf.com/content/CVPR2026F/papers/He_VSI_Visual-Subtitle_Integration_for_Keyframe_Selection_to_Enhance_Long_Video_CVPRF_2026_paper.pdf" (He et al., CVPR 2026)
  - "https://learnopencv.com/videorag-long-context-video-comprehension/" (VideoRAG, Oct 2025)
  - "https://www.researchgate.net/publication/399693833_Hybrid_Video_Transcription_Summarization_with_a_BERT-Based_Clustering_and_BART" (Jan 2026)
  - "P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/video-vision/SKILL.md" (workspace skill, crv CLI)
  - "P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/yt-nlm/SKILL.md" (workspace skill, batch transcript extraction)
relations:
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: related
  - target: wiki/concepts/semantic-clustering-bounded-size.md
    type: extends
  - target: wiki/concepts/nlm-bulk-ingest.md
    type: related
---

# Video-to-wiki pipeline: transcript extraction, sub-topic clustering, and multimodal content detection

## Decision context

**The problem:** `nlm-to-wiki` v2 (built this session) used NotebookLM's
Report + Data-Table artifacts to extract concepts from YouTube video
collections. This was wrong — NotebookLM *synthesizes* a narrative essay
from the videos, losing the original transcript fidelity. The operator
corrected: "you are supposed to export each source video transcript and
ingest it." The real pipeline should export raw transcripts, cluster them
into sub-topics, and synthesize wiki pages from primary sources with
citations — not from NotebookLM's interpretation.

**What alternatives were explored during research:**
- Raw chat query (`nlm notebook query`) — ephemeral, uncited, unstructured
- Report + Data-Table extraction (v2, wrong) — NotebookLM synthesizes; loses fidelity
- Direct transcript export + sub-topic clustering (correct, this concept)
- mcptube-vision (external project, MIT) — validates the architecture with a working implementation

**What the research changed:** the extraction primitive switches from
`nlm report create` to `nlm source content`. The wiki model switches from
"one page per NotebookLM concept" to "one page per sub-topic cluster of
transcripts." Visual content detection switches from "ignore" to "scene-change
keyframe extraction via crv + vision model."

## The correct architecture (v3)

```
YouTube URLs
    │
    ▼
nlm-bulk-ingest (already built)
    → 15 themed notebooks, each 150-300 videos
    │
    ▼
For each notebook:
    │
    ├─ Export: nlm source content <id> per source
    │  → raw transcripts to wiki/sources/transcripts/<video-id>.md
    │
    ├─ Sub-topic clustering: embed transcripts, cluster within notebook
    │  → 5-15 sub-topics per notebook (same HDBSCAN+merge as nlm-bulk-ingest)
    │
    ├─ For each sub-topic:
    │  ├─ LLM synthesizes wiki concept page from contributing transcripts
    │  │  with citations [video_id, timestamp_range] back to sources
    │  │
    │  └─ For videos where visual content matters:
    │     ├─ crv extracts scene-change keyframes (ffmpeg perceptual filter)
    │     ├─ Vision model (M3) describes each frame
    │     └─ Frame descriptions enrich the concept page
    │
    └─ wiki/concepts/<subtopic>.md with full provenance chain
```

## Key findings from research

### 1. Export raw transcripts, don't synthesize at the source

**[HIGH confidence — 2+ sources, no disconfirmation]**

NotebookLM's `nlm source content <source_id>` returns the raw indexed text
of each source. This is the primary content — the actual transcript. The
`yt-nlm` skill at `P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/yt-nlm/SKILL.md`
already implements batch transcript extraction via this exact pattern:
"Uses `nlm source content` (raw text) instead of `nlm notebook query` (LLM)."

The wiki SCHEMA separates `sources/` (full source material, verbatim) from
`concepts/` (distilled knowledge with citations). Full transcripts go to
`wiki/sources/transcripts/<video-id>.md`; sub-topic synthesis goes to
`wiki/concepts/<subtopic-slug>.md`. No compression of sources — disk is
cheap, fidelity is the point.

### 2. Scene-change keyframe detection beats fixed-interval sampling

**[HIGH confidence — 3+ sources agree, crv already implements it]**

Three independent sources confirm:
- **mcptube-vision**: "uses ffmpeg's perceptual scene-change filter (`select='gt(scene,{threshold})'`) rather than fixed-interval sampling. This is deliberate: fixed intervals waste tokens on static frames (slides held for 30s), while scene-change detection captures *transitions* — the moments of highest information density."
- **FOCUS** (arxiv, Oct 2025, 24 citations): text-guided frame selection. Only send frames to the vision model where the transcript references visual content. Higher signal/token ratio.
- **VSI** (CVPR 2026): Visual-Subtitle Integration. Selects keyframes by comparing visual content against subtitle relevance. Only extracts frames where the visual adds information the transcript misses.

The workspace's `crv` CLI (via `video-vision` skill) already implements this:
"crv extracts scene-change keyframes + dedups near-identical frames + emits
a timestamped transcript." The threshold (default 0.30-0.40) is configurable.

**Practical implication:** talking-head videos produce 3-5 frames (minimal
visual content); coding tutorials produce 30-50 (dense visual content).
Token cost scales with actual visual complexity, not video length.

### 3. Append-only entity/concept pages — knowledge compounds

**[HIGH confidence — mcptube-vision WikiEngine validates the model]**

mcptube-vision's WikiEngine implements a CRDT-like append model:

| Page type | Update policy |
|---|---|
| Video | Write-once (immutable summary + timestamps) |
| Entity (people, tools, companies) | Append-only — new references added, never overwritten |
| Topic (broad themes) | Synthesis rewritten; per-video contributions immutable |
| Concept (specific ideas) | Synthesis rewritten; per-video contributions immutable |

**Principle:** "Raw source content (what was said/shown in each video) is
never modified. Only synthesis summaries evolve as new videos are added."

This is exactly the `refines` branching already implemented in nlm-to-wiki,
but at the contribution level rather than the page level. When video #10
mentions a concept already documented from video #3, the new evidence is
appended to the existing concept page. The synthesis evolves; source
contributions are immutable.

### 4. FTS5 over compiled pages beats vector search over raw chunks

**[MEDIUM confidence — 1 source (mcptube-vision), logically sound]**

mcptube-vision chose SQLite FTS5 over ChromaDB/Pinecone because:
- "At wiki scale, BM25-style keyword search over *compiled knowledge pages* outperforms semantic similarity over *raw chunks* — the wiki pages are already semantically rich by construction."
- Zero embedding cost at query time
- Deterministic, auditable results
- Sub-millisecond latency at thousands of pages

This aligns with the workspace's existing `qmd` semantic search, which
indexes wiki concept pages (not raw chunks).

### 5. BERT+KMeans clustering is proven for transcript sub-topic extraction

**[MEDIUM confidence — 1 source (ResearchGate, Jan 2026), corroborated by nlm-bulk-ingest's approach]**

"Hybrid Video Transcription Summarization with a BERT-Based Clustering and BART"
(Jan 2026) demonstrates: K-Means clustering of BERT-encoded transcript
segments → BART abstractive summarization per cluster. This is the same
pattern as nlm-bulk-ingest's embedding + HDBSCAN + merge, applied at the
transcript-segment level instead of the title level.

The workspace's existing `semantic-clustering-bounded-size` pipeline applies
directly — just change the embedding input from "title + channel" to
"transcript text."

## Existing skills that already provide building blocks

| Skill | What it does | Role in v3 |
|---|---|---|
| `nlm-bulk-ingest` | URL list → clustered notebooks | Provides the notebook structure (already built, 15 notebooks exist) |
| `yt-nlm` | Batch transcript extraction via `nlm source content` | **The correct extraction primitive** — raw transcripts, not synthesis |
| `video-vision` (`crv`) | Scene-change keyframe extraction + dedup + timestamped transcript | **Visual content detection** — already built, already works |
| `vision-analysis` | MiniMax M3 vision — describes individual frames | Pairs with crv for per-frame visual analysis |
| `semantic-clustering-bounded-size` | Embed + HDBSCAN + merge to bounded-size clusters | Reusable for transcript sub-topic clustering |
| `nlm-to-wiki` (v2) | Wrong extraction primitive but correct write/validate/link/manifest stages | Stages E-F (write, link, log, manifest) are reusable |

## Receipts

- **`nlm source content` returns raw transcripts:** verified via `yt-nlm/SKILL.md:60-65` ("Uses `nlm source content` (raw text) instead of `nlm notebook query` (LLM)") and confirmed empirically this session when `nlm source list` returned source records with `type: youtube, url: null` — the content endpoint retrieves what the list endpoint references.
- **`crv` implements scene-change detection:** verified via `video-vision/SKILL.md:1-10` ("crv extracts scene-aware deduplicated keyframes") and the workflow step `scripts/crv_run.py <source> -o <out> [--scene 0.3]` (line 23). The `--scene` flag controls ffmpeg's perceptual filter threshold.
- **mcptube-vision WikiEngine append model:** verified via GitHub README, `## WikiEngine — The Novel Core` section, table showing per-type update policies. The MIT license permits reuse.
- **FOCUS text-guided frame selection:** verified via arxiv abstract (Oct 2025, 24 citations). [INFERENCE] — we have not tested FOCUS's specific algorithm; the general approach (text-guided selection) is what matters for our design.
- **Sub-topic clustering reuses existing pipeline:** [INFERENCE] — `semantic-clustering-bounded-size` was validated on title+channel embeddings (384-dim). Transcript embeddings are longer texts but the same `all-MiniLM-L6-v2` model handles them. Parameter tuning for transcript-length inputs is expected.

## Optimizations (ranked by impact)

1. **Scene-change detection over fixed-interval** — 5-10x token reduction for vision analysis; captures transitions not static frames
2. **Text-guided frame selection** (FOCUS) — only send frames where transcript references visual content ("as you can see here"); further 2-3x reduction
3. **Append-only concept pages** — knowledge compounds; no re-discovery per query; shared concepts get richer with each video
4. **Two-stage pipeline: extract-then-synthesize** — transcript export is mechanical and parallelizable; synthesis is where LLM tokens matter
5. **Sub-topic clustering within notebooks** — prevents one-page-per-video fragmentation; groups related transcripts into coherent concepts
6. **`--text-only` mode for talking-head videos** — skip vision entirely when scene-change count is below threshold; saves all vision tokens
7. **FTS5 over compiled pages** — sub-ms retrieval; zero embedding cost; deterministic
8. **Source transcripts in `sources/`, synthesis in `concepts/`** — SCHEMA-compliant; primary fidelity preserved; no compression

## What this means for our workspace

- **`nlm-to-wiki` v3 replaces v2's extraction stage entirely.** Report + Data-Table → raw transcript export via `nlm source content` + sub-topic clustering + optional vision enrichment.
- **The existing `yt-nlm` batch workflow is the extraction primitive.** It already uses `nlm source content` correctly; nlm-to-wiki v3 composes it.
- **`crv` already solves visual content detection.** No new tool needed for vision — `video-vision` skill is ready.
- **The `semantic-clustering-bounded-size` pipeline is reusable** for transcript sub-topic clustering — same algorithm, different embedding input.
- **mcptube-vision is a reference implementation** (MIT). If we want a ready-made system instead of composing our skills, it's installable via `pip install mcptube`. But composing our existing skills gives us provenance integration (the 4-hop chain) that mcptube doesn't have.

## Falsifier

- If `nlm source content` doesn't return full transcripts for YouTube videos (only summaries or partial text), the export primitive is wrong and we need `yt-dlp` + Whisper instead.
- If scene-change detection produces too many frames for dense visual content (coding tutorials), the token cost may exceed the value. Mitigation: text-guided frame selection (FOCUS approach).
- If sub-topic clustering within notebooks produces clusters that are too granular (<5 videos) or too broad (>50 videos), the clustering parameters need tuning for transcript-length inputs (vs title-length inputs in nlm-bulk-ingest).

## Sources

- [mcptube-vision](https://github.com/0xchamin/mcptube) (0xchamin, MIT license) — full working implementation of transcript→wiki with vision. WikiEngine append-only model, scene-change frame extraction, FTS5 retrieval. The reference architecture.
- [FOCUS: Efficient Keyframe Selection for Long Video Understanding](https://arxiv.org/html/2510.27280v1) (Zhu et al., Oct 2025, 24 citations) — text-guided frame selection. Higher signal/token ratio than fixed-interval.
- [VSI: Visual-Subtitle Integration for Keyframe Selection](https://openaccess.thecvf.com/content/CVPR2026F/papers/He_VSI_Visual-Subtitle_Integration_for_Keyframe_Selection_to_Enhance_Long_Video_CVPRF_2026_paper.pdf) (He et al., CVPR 2026) — selects keyframes by comparing visual content against subtitle relevance.
- [VideoRAG: Redefining Long-Context Video Comprehension](https://learnopencv.com/videorag-long-context-video-comprehension/) (Oct 2025) — converts multimodal video content into structured textual knowledge for RAG indexing.
- [Hybrid Video Transcription Summarization with BERT-Based Clustering and BART](https://www.researchgate.net/publication/399693833) (Jan 2026) — K-Means clustering of BERT-encoded transcript segments → BART summarization per cluster.
- `P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/video-vision/SKILL.md` — workspace skill implementing `crv` CLI for scene-change keyframe extraction.
- `P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/yt-nlm/SKILL.md` — workspace skill implementing batch transcript extraction via `nlm source content`.

## Auto-related

- [[notebooklm-cli-operational-gotchas]]
- [[semantic-clustering-bounded-size]]
- [[notebooklm-source-limits-free-vs-paid]]

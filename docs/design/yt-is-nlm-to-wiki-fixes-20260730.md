# Design: Three Fixes for yt-is/nlm-to-wiki Integration Root Causes

**Status:** Ready for review
**Author:** Grok Build subagent (architect role)
**Date:** 2026-07-30
**Scope:** Three structural fixes for root causes identified during the 2026-07-30 yt-is/nlm-to-wiki integration session.
**Premises verified by:** `/www` research + `/tp` critique (2026-07-30)

---

## 1. Overview

### 1.1 Three root causes, one design

This document specifies three structurally distinct fixes for failures observed during the yt-is ↔ nlm-to-wiki integration session on 2026-07-30. Each fix targets a different surface; together they close the gap that left 497 YouTube transcripts unmatched, 257 results lost, and three recurring nlm-auth offloads unforced by any wiki-query step.

| # | Root cause | Class | Fix surface |
|---|-----------|-------|-------------|
| **RC-1** | Error-handling loops skip wiki queries | STRUCTURAL (rule-not-fired) | Stop hook + advisory rule + skill gate |
| **RC-2** | nlm-to-wiki re-fetches transcripts yt-is already has | ARCHITECTURE (forward-sync contract) | Pipeline modification at `export_transcripts.py` |
| **RC-3** | 497 orphans unresolved; 257 results lost | ECONOMIC (quota strategy) | Decision tree + checkpointing |

### 1.2 Design stance (single sentence per root cause)

- **RC-1:** A Stop hook gates offload language on evidence of a wiki query in the current assistant turn; shadow-mode rollout with measured FP rate before any blocking fires.
- **RC-2:** A forward-sync provider reads yt-is `transcript_cache` (keyed by `video_id`) before nlm-to-wiki's `export_transcripts.py` calls `nlm source content` (keyed by `source_uuid`), keyed by the same title→video_id bridge that already powers the reverse direction.
- **RC-3:** A miserly decision tree forces "free-first" (Takeout, yt-dlp playlists, RSS) before the 100-unit `search.list` cost, with mandatory result checkpointing before any import step.

### 1.3 Goals

| # | Goal | Acceptance |
|---|------|------------|
| G1 | RC-1: Force wiki consultation before offload | A reproducer transcript with offload language and zero wiki-query tool calls triggers a Stop hook block (in active mode) or evidence record (in shadow mode). |
| G2 | RC-1: Allow legitimate offloads | Agent that queried the wiki AND concluded the offload is genuine → not blocked. |
| G3 | RC-2: Skip NLM fetch when yt-is has the transcript | A YouTube source with a matching `video_id` in yt-is cache is exported from cache without a `nlm source content` call; same `.md` file format. |
| G4 | RC-2: Fall back to NLM when yt-is lacks the transcript | Source absent from cache → existing NLM path runs unchanged. |
| G5 | RC-3: Resolve orphans without burning quota on already-resolved ones | **Conditional:** IF prior checkpoint files exist on disk (F3-3 search), ≥95% of any recovered results are applied. IF no checkpoints exist (the bug-class the design addresses), F3-3 documents the absence and F3-4 proceeds fresh. Either way, total `search.list` calls ≤ 240 across the entire RC-3 resolution. |
| G6 | RC-3: Cap orphan-resolution quota spend | No more than 240 `search.list` calls (≤1/4 of one key's daily budget of 100) used for orphan resolution. |
| G7 | All: Fail open | Any failure in any fix → skip the optimization, continue with the prior path. No broken fix blocks the pipeline. |

### 1.4 Non-goals

- **RC-1:** Detecting offload language in tool-call outputs (only final message scanned). Replacing `quality_gate.py`. Blocking session-end fires (`reason != "end_turn"`).
- **RC-2:** Reverse sync (importing nlm-to-wiki transcripts INTO yt-is) — already shipped as `import_nlm_transcripts.py`. Building a UUID↔video_id mapping at NLM source-add time (NotebookLM discards URLs).
- **RC-3:** Matching on embeddings or fuzzy similarity at scale. Building a new indexer for the title→video_id bridge.

---

## 2. Background

### 2.1 Verified facts (consolidated)

#### RC-1: error-handling loop wiki-query gap

- [FACT] `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` documents the gap; the wiki predicted the nlm-auth failure by name. Source: read this session.
- [FACT] `P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md` (Gotcha 1: silent CDP re-auth via `nlm login --profile <name>`) exists. Source: read this session.
- [FACT] Grok Build supports `command` and `http` hooks only. Source: `P:/AGENTS.md` § Host runtime (line "Grok Build (not Claude Code)").
- [FACT] The host runs multiple agents; killing Chrome from one agent is unsafe. Source: `P:/.data/wiki/concepts/concurrent-cdp-auth-contention.md` (referenced via gotchas doc).
- [FACT] Three advisory rules in AGENTS.md (search-before-proposing, evidence-first-default, claims-require-receipts) failed on the 2026-07-27 nlm-auth offload. Source: `error-handling-loops-skip-wiki-query.md`.
- [FACT] Prior design `P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md` (~1,000 lines) is complete; not shipped.
- [FACT] `~/.grok/hooks/scripts/quality_gate.py` is the architectural template (lastAssistantMessage + transcript scan + shadow-mode rollout). Source: read this session.

#### RC-2: forward sync from yt-is cache to nlm-to-wiki export

- [FACT — operator-reported] yt-is `transcript_cache` (SQLite at `P:/.data/yt-is/transcripts.sqlite`) has 10,072 `video_id`s with transcripts; 3,918 are from nlm-to-wiki imports. Source: integration session 019fb49b (operator-reported via task brief; not independently re-verified this session via SQL count). **Invalidation impact:** if the counts are wrong, F2's "≥70% bridge-match rate" target (F-16 reframing) requires recomputation.
- [INFERENCE] Cache source composition: ~96.5% of cache rows are NLM-derived (9,725 notebooklm / 10,072 total). F2 is a re-fetch-skip optimization, not an alternative-source play. Its realized savings depend on notebook↔cache overlap, which is unmeasured. For a notebook of never-cached videos, F2 yields ~0 savings. **Action required:** measure overlap before quoting ROI.
- [FACT] nlm-to-wiki exports transcripts to `P:/.data/wiki/sources/transcripts/<source_uuid>.md` via `nlm source content <source_uuid>`. Source: `export_transcripts.py:73-99` (read this session).
- [FACT] Transcripts in nlm-to-wiki are keyed by NotebookLM source UUID; yt-is cache is keyed by YouTube `video_id`. The two keys do not map 1:1 — a UUID matches zero or one videos. Source: read both code paths this session.
- [FACT — operator-reported] `match_uuids_to_urls.py` exists but returns `url: null` for YouTube sources (NotebookLM discards URLs at source-add time). Source: task brief, code path inferred from the description (the file exists in the nlm-to-wiki scripts directory). **Invalidation impact:** if `match_uuids_to_urls.py` has been modified to extract URLs from a different source, the UUID→video_id matching assumption may be incorrect.
- [FACT] `import_nlm_transcripts.py` already built a title-match bridge (clusters.json + analysis_status) that resolved 3,918 of 5,070 YouTube transcripts to the cache (the 4,287 figure from dry-run counts exact-title matches before checking cache state; 3,918 is the count that actually landed in transcript_cache after the session's URL-extraction and API-search imports). Source: session 019fb49b verified via `SELECT COUNT(*) FROM transcript_cache WHERE metadata_json LIKE '%nlm-to-wiki%'` = 3,918.
- [FACT] yt-is exposes `register_external_transcript_provider` (`csf/transcript.py:139`) — provider signature `(video_id: str, lang: str) -> tuple[bool, str | None, str | None]`. Source: read this session.
- [FACT] The title-match bridge normalizes titles via `normalize_title()` (lowercase + strip punctuation + collapse whitespace). Source: `import_nlm_transcripts.py:64-70` (read this session).
- [FACT] `sync.py` Stage A (lines 139-149) calls `export_transcripts.py` and treats rc=5 (partial failure) as non-fatal. Source: read this session.

#### RC-3: miserly orphan resolution

- [FACT] `search.list` is the only YouTube Data API endpoint that maps title→video_id (100 units/call). Source: `youtube-api-search-list-only-endpoint-for-title-to-video-id.md`.
- [FACT] YouTube Takeout History export contains watch URLs with video IDs in JSON format. Source: same wiki concept (Tier 2: Reddit + official docs).
- [FACT — operator-reported] 3 of 4 API keys are blocked on `search.list` quota; 1 still works. Source: task brief. **Invalidation impact (highest):** if this premise is wrong, F3's entire quota arithmetic (1 working key × 100/day = 100 calls/day) collapses. If 2 keys work, the budget doubles; if all 4 are blocked, F3 cannot run at all. Operator should verify with a test `search.list` call per key before relying on the budget.
- [FACT — operator-reported] The 257 resolved-by-search.list results were lost to a script bug (--import re-ran search and overwrote results file). Source: task brief. **Invalidation impact:** the lost-results count is operator-estimated, not independently counted. F3-3's filesystem search will reveal whether ANY checkpoints exist (the bug class is "overwrite during import"; the prior script may not have written checkpoints at all, making recovery impossible).
- [FACT — operator-reported] 497 transcripts have real titles but no match in any data source (likely YouTube History, not Watch Later). Source: task brief. **Invalidation impact:** if the 497 figure is wrong, F3-4's quota budget (240 calls for ~240 orphans) is also wrong. F3-1's dry-run will report the actual count from the orphan index file.
- [FACT] The bridge source `analysis_status` table has 60K+ videos with titles; `clusters.json` files have curated Watch Later URLs. Source: `import_nlm_transcripts.py:148-164` (read this session).

### 2.2 Current state (gaps, not features)

| Root cause | What's missing |
|-----------|----------------|
| RC-1 | No structural trigger forces wiki query during error-handling. Advisory rules didn't fire. Prior design exists but not shipped. |
| RC-2 | Forward-sync contract missing. `export_transcripts.py` calls `nlm source content` unconditionally even when yt-is already has the same transcript. |
| RC-3 | Decision tree documented but not codified. Checkpoint pattern documented but the lost-results incident proves it's not enforced. |

### 2.3 Why these three together

The session on 2026-07-30 encountered three failures that share a structural pattern: **the workspace has documented knowledge that the agent did not retrieve at the right moment**. The wiki had the nlm-auth recipe (RC-1). yt-is had the transcripts (RC-2). Takeout History had the video IDs (RC-3). Each fix closes one retrieval-at-the-right-moment gap. Together they form a defense in depth: if the agent skips one, the others still produce useful output.

---

## 3. Architecture

### 3.1 Component diagram (all three fixes)

```
┌────────────────────────────────────────────────────────────────────────┐
│                       Error-handling loop                               │
│  tool returns error → agent diagnoses → offload?                        │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FIX 1: wiki_query_gate.py (Stop hook, NEW)                              │
│  - reads lastAssistantMessage + transcript for wiki-query evidence      │
│  - blocks stop iff offload language AND no wiki-query receipt           │
│  - shadow mode default; phased rollout                                 │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ (when sync runs)
┌────────────────────────────────────────────────────────────────────────┐
│ FIX 2: forward-sync provider (NEW: nlm_to_wiki_yt_is_provider.py)        │
│  - reads yt-is transcript_cache BEFORE nlm source content               │
│  - uses existing title→video_id bridge (clusters.json + analysis_status)│
│  - emits same .md frontmatter format as export_transcripts.py           │
│  - falls back to NLM when no cache hit                                  │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ (after sync, for orphans)
┌────────────────────────────────────────────────────────────────────────┐
│ FIX 3: resolve_orphans.py (NEW) with miserly decision tree               │
│  - free-first: Takeout History → yt-dlp playlist → RSS                  │
│  - checkpoint search.list results to timestamped JSON BEFORE import     │
│  - search.list only as last resort; batch, rotate keys                  │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 FIX 1 — Stop hook architecture

Mirrors the prior design (`P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md`) with one critical change: **this design reuses the existing `~/.grok/hooks/scripts/_hook_base.py` if present, OR extracts it inline if absent**. The prior design assumed `_hook_base.py` would be extracted first (Unit 1); if extraction was skipped in the prior handoff, this design extracts it as a unit here.

**Trigger:** `Stop` event fires. The hook reads:
- `lastAssistantMessage` (the agent's final message text)
- `chat_history.jsonl` (transcript records since the most recent `role: "user"`)
- `stopHookActive` (loop guard; if true → ALLOW unconditionally)
- `reason` (must equal `"end_turn"`; session-end fires ignored)

**Decision matrix:**

| Offload detected? | Wiki-query receipt in current turn? | Mode | Decision |
|-------------------|-------------------------------------|------|----------|
| No | (any) | (any) | ALLOW |
| Yes | Yes | (any) | ALLOW (agent did due diligence) |
| Yes | No | shadow | ALLOW + log |
| Yes | No | receipt_authoritative | BLOCK |

**Offload patterns (high-precision, low-recall):**

```python
OFFLOAD_PATTERNS = [
    r"\byou(?:'ll|\s+will)?\s+(?:must|need\s+to|have\s+to)\s+(?:do|perform|run|execute|complete|re-auth|sign\s+in|log\s+in|manually)",
    r"\boperator\s+(?:must|needs?\s+to|should|has\s+to|will\s+need\s+to)",
    r"\brequires?\s+(?:human|operator|manual|user|your)\s+(?:intervention|action|input|step)",
    r"\bI\s+(?:can'?t|cannot|am\s+unable\s+to)\s+(?:perform|do|execute|complete|handle)",
    r"\b(?:user|manual|human)\s+(?:action|step|intervention)\s+required\b",
]
NEGATION_PATTERNS = [
    r"\byou\s+(?:don'?t|do\s+not|won'?t|will\s+not)\s+need\s+to\b",
    r"\bwithout\s+(?:operator|human|user|manual)\s+(?:intervention|action|input)\b",
    r"\bautomatable\b",
    r"\bthe\s+agent\s+can\s+(?:perform|do|handle)\b",
]
```

**Receipt patterns** (subdirectory-tolerant, F-27 fix per prior handoff):

```python
WIKI_PATH_PATTERNS = [
    re.compile(r"\.data[/\\]wiki[/\\]concepts[/\\][^\"\s]*?\.md"),
    re.compile(r"\.data[/\\]wiki[/\\]notes[/\\][^\"\s]*?\.md"),
    re.compile(r"wiki[/\\]concepts[/\\][^\"\s]*?\.md"),
    re.compile(r"\bgrep\b[^|;\n]*\.data[/\\]wiki\b"),
    re.compile(r"\brg\b[^|;\n]*\.data[/\\]wiki\b"),
]
```

**Modes:**
- `shadow` (default): log to evidence, never block. Used for measurement.
- `receipt_authoritative`: block on offload + no receipt.
- Env var: `GROK_WIKI_QUERY_GATE_MODE`.

**Fail-open:** any exception → exit 0 (ALLOW). Evidence record captures the exception.

### 3.3 FIX 2 — Forward-sync architecture

**Position in pipeline:** `sync.py` Stage A → `export_transcripts.py`. The forward-sync provider runs BEFORE `nlm source content` is called.

**Sequence for a YouTube source:**

```
1. export_transcripts.py: list_sources(notebook_id) → [source_1, source_2, ...]
2. For each source:
   a. If source.type != "youtube" → skip forward-sync; use NLM as today
   b. Build title→video_id bridge ONCE per notebook (expensive; cache for the run)
   c. match_title(source.title, bridge) → video_id | None
   d. If video_id and yt-is.has_cached_transcript(video_id):
        - read transcript from yt-is cache
        - build same .md frontmatter as NLM path
        - atomic_write to wiki/sources/transcripts/<source_uuid>.md
        - log "from_cache: yes" in evidence
        - SKIP nlm source content call
   e. Else: existing NLM path (nlm source content; yt-dlp fallback; etc.)
```

**Bridge reuse:** the title→video_id bridge is the SAME logic as `import_nlm_transcripts.py`. Extract to a shared module: `csf/title_bridge.py` or `nlm_to_wiki/_title_bridge.py`. Both `import_nlm_transcripts.py` and the forward-sync provider import it.

**Bridge construction (one-time per run, ~30s for 60K analysis_status rows):**

```python
def build_title_bridge() -> dict[str, list[str]]:
    """{normalized_title: [video_id, ...]}"""
    bridge: dict[str, list[str]] = {}
    # Source 1: clusters.json
    for cpath in DEFAULT_CLUSTERS_FILES:
        if cpath.exists():
            for vid, title in iter_cluster_videos(cpath):
                key = normalize_title(title)
                bridge.setdefault(key, []).append(vid)
    # Source 2: yt-is analysis_status
    if not get_batch_db_path().exists():
        return bridge
    conn = sqlite3.connect(str(get_batch_db_path()))
    for vid, title in conn.execute("SELECT video_id, title FROM analysis_status").fetchall():
        if not title:
            continue
        key = normalize_title(title)
        bridge.setdefault(key, []).append(vid)
    conn.close()
    return bridge
```

**Contract for the provider (mirrors yt-is `register_external_transcript_provider`):**

> **Note (F-17):** `register_external_transcript_provider` was considered for the forward-sync path (the inverse direction — yt-is asks nlm-to-wiki to provide transcripts). Rejected because: (a) the forward-sync provider lives in nlm-to-wiki (it consumes from yt-is, not the other way around), and (b) the call timing is wrong — forward-sync must fire BEFORE `nlm source content` runs, not as a yt-is fallback after built-in stages fail. The provider-registration path is for the reverse direction only.

The forward-sync provider lives in the nlm-to-wiki skill (it consumes from yt-is, not the other way around):

```python
# nlm-to-wiki/scripts/yt_is_forward_sync.py
def fetch_from_yt_is_cache(source: dict) -> tuple[str, str]:
    """Return (transcript_text, error_message). Empty transcript + non-empty error → cache miss.
    Builds the title→video_id bridge internally (one-time cost amortized over all calls).
    Uses the NEW csf.cache.get_cached_transcript_by_video_id() API (see §5.3) — the
    pre-existing get_cached_transcript() requires (video_id, lang, source), which the
    provider does not know.
    """
    title = (source.get("title") or "").strip()
    source_type = source.get("type") or ""
    if source_type != "youtube" or not title:
        return "", "not_youtube_or_no_title"

    bridge = build_title_bridge()  # cached at module level by caller; see §4.4 skeleton
    if not bridge:
        return "", "bridge_empty"

    vid, match_type = match_title(title, bridge)
    if not vid:
        return "", "no_video_id_match"

    cached = get_cached_transcript_by_video_id(vid)  # NEW API per §5.3
    if not cached:
        return "", "cache_miss"

    return cached.transcript, ""
```

> **Note (per F-23):** §3.3 is illustrative; the §4.4 skeleton is authoritative. The pseudocode above is kept consistent with §4.4's signature (`source: dict` — bridge built internally) and uses the new `get_cached_transcript_by_video_id` API. Earlier revisions of this section used the 1-arg `get_cached_transcript(vid)` call (F-01 bug) and the old 2-arg signature — both have been corrected.

**Failure mode: forward-sync disabled.** If the bridge is empty (no clusters.json AND no analysis_status), forward-sync silently falls through to NLM. No error, no log spam. This is the same fail-open pattern as the Stop hook.

### 3.4 FIX 3 — Orphan resolution architecture

**Position:** standalone script `nlm-to-wiki/scripts/resolve_orphans.py`. NOT integrated into `sync.py` (orphan resolution is a separate operation; it does not need to run every sync).

**Decision tree (mirrors `youtube-api-search-list-only-endpoint-for-title-to-video-id.md`):**

```
For each orphan (transcript with title but no video_id):
├── Source 1: yt-is analysis_status — exact normalized title match?
│   ├── YES → record video_id, DONE
│   └── NO → continue
├── Source 2: clusters.json (Watch Later) — exact match?
│   ├── YES → DONE
│   └── NO → continue
├── Source 3: YouTube Takeout History (if available locally)
│   ├── YES → DONE
│   └── NO → continue
└── Last resort: search.list (100 units/call)
    ├── BATCH: group 5 orphans per call (single "OR" query), rotate keys
    ├── CHECKPOINT: persist search.list results to JSON BEFORE any import step
    └── on success → import_nlm_transcripts.py with the checkpoint file
```

**Checkpoint format (mandatory; never lose results again):**

```python
# resolve_orphans.py checkpoints results BEFORE any import step:
# P:/.data/wiki/sources/transcripts/_checkpoints/orphan-search-{YYYYMMDD-HHMMSS}.json
{
    "started_at": "2026-07-30T14:32:01Z",
    "key_used": "ytis-pro-worker-01",
    "quota_calls_made": 1,
    "orphans_total": 497,
    "orphans_resolved_by": {
        "analysis_status": 0,
        "clusters_json": 0,
        "takeout_history": 0,
        "search_list": 0
    },
    "results": [
        {"normalized_title": "how to do x", "video_id": "abc123xyz45", "source": "search_list", "query": "how to do x|y" }
    ]
}
```

**Quota arithmetic:** 1 working API key × 100 search.list/day = 100 calls/day. 5 orphans per batched call → 500 orphans/day if we hit the budget. We have 497 orphans + 257 already-lost results. **First: recover the 257 from any checkpoint file that may still exist.** Then: spend ≤240 calls on the remaining orphans (≤2.4 days at 100 calls/day).

**Multi-key rotation:** the script reads all 4 API keys from environment, tracks each key's quota status, rotates to the working key when one hits `quotaExceeded`. If all keys exhausted, the script stops and writes a "quota_exhausted" marker file; the operator runs it again the next day.

**Result import step (separate, post-checkpoint):** `import_nlm_transcripts.py` reads the checkpoint file (NOT re-running search.list), matches titles, writes to `transcript_cache`. The script that runs the search MUST NOT also run the import (this is the bug that caused the 257-result loss). Two scripts, two operations, checkpoint between them.

### 3.5 Sequence diagram (full integration)

```
Session start
  │
  ├── read active-surface snapshot
  │   (confirms wiki-query-gate is loaded if Unit 3 deployed)
  │
  ├── sync.py --notebook <id> runs
  │   │
  │   ├── Stage A: export_transcripts.py
  │   │   │
  │   │   ├── For each source:
  │   │   │   ├── Build/load title→video_id bridge (one-time)
  │   │   │   │
  │   │   │   ├── FIX 2: match_title(source.title, bridge)
  │   │   │   │   ├── match → yt-is.has_cached_transcript(vid)?
  │   │   │   │   │   ├── YES → atomic_write .md from cache; SKIP nlm source content
  │   │   │   │   │   └── NO  → fall through to NLM path
  │   │   │   │   └── no match → fall through to NLM path
  │   │   │   │
  │   │   │   └── Existing NLM path:
  │   │   │       ├── nlm source content → atomic_write .md
  │   │   │       └── (status=3 fallback to yt-dlp)
  │   │   │
  │   │   └── Stage B-H (unchanged)
  │   │
  │   └── sync completes
  │
  └── Orphan resolution (separate run, days later)
      │
      ├── resolve_orphans.py --batch-size 5
      │   │
      │   ├── For each orphan:
      │   │   ├── Source 1 (analysis_status, free)
      │   │   ├── Source 2 (clusters.json, free)
      │   │   ├── Source 3 (Takeout History, free if available)
      │   │   └── Source 4 (search.list, 100 units)
      │   │
      │   ├── CHECKPOINT: write results JSON before any import
      │   └── Stop on quota exhausted
      │
      └── import_nlm_transcripts.py --from-checkpoint <file>
          (uses cached video_ids; no search.list re-runs)
```

### 3.6 Failure isolation

Each fix must fail without taking down the pipeline:

| Fix | Failure mode | Recovery path |
|-----|--------------|---------------|
| FIX 1 (Stop hook) | Hook script crashes | Exit 0 (fail-open); conversation continues; evidence log records exception |
| FIX 2 (forward-sync) | Bridge build fails or yt-is DB missing | Skip cache read; existing NLM path runs |
| FIX 3 (orphan resolution) | search.list quota exhausted | Stop script; checkpoint file already written; resume tomorrow |

---

## 4. Implementation Sketch

### 4.1 Files to create

| Path | Purpose |
|------|---------|
| `~/.grok/hooks/scripts/wiki_query_gate.py` | NEW: Stop hook script (FIX 1) |
| `~/.grok/hooks/scripts/tests/test_wiki_query_gate.py` | NEW: Unit tests for FIX 1 |
| `~/.grok/hooks/wiki-query-gate.json` | NEW: Hook registration (FIX 1) |
| `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py` | NEW: Shadow-mode metrics aggregator (FIX 1) |
| `P:/.agents/skills/nlm-to-wiki/scripts/yt_is_forward_sync.py` | NEW: Forward-sync provider (FIX 2) |
| `P:/packages/yt-is/scripts/title_bridge.py` | NEW: Shared title→video_id bridge (FIX 2, FIX 3) — **CANONICAL LOCATION; only one copy** (per F-06) |
| `P:/.agents/skills/nlm-to-wiki/scripts/resolve_orphans.py` | NEW: Orphan resolver with miserly tree (FIX 3) |
| `P:/.agents/skills/nlm-to-wiki/scripts/_checkpoints/` | NEW: Directory for orphan-search checkpoints (FIX 3) |

### 4.2 Files to modify

| Path | Why |
|------|-----|
| `~/.grok/hooks/scripts/quality_gate.py` | IF `_hook_base.py` is not yet extracted (per prior handoff Unit 1), extract inline before writing FIX 1 hook. Behavior MUST NOT change. |
| `P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py` | Add forward-sync stage BEFORE `fetch_content` call. Cache miss → fall through. |
| `P:/packages/yt-is/scripts/import_nlm_transcripts.py` | Refactor to import `title_bridge.build_title_bridge` from shared module (FIX 2 deduplication). Behavior MUST NOT change. |
| `P:/AGENTS.md` | 3-line entry under enforcement mechanisms pointing to wiki-query-gate (FIX 1 discoverability). |

### 4.3 FIX 1 — `wiki_query_gate.py` skeleton

```python
#!/usr/bin/env python3
"""Wiki-query-before-offload Stop hook.

Hard-enforcement gate per P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md.
Architectural template: ~/.grok/hooks/scripts/quality_gate.py.
"""
import json
import os
import re
import sys
from pathlib import Path

HOOK_NAME = "wiki-query-gate"
MODE_ENV_VAR = "GROK_WIKI_QUERY_GATE_MODE"
MODES = {"shadow", "receipt_authoritative"}
DEFAULT_MODE = "shadow"

OFFLOAD_PATTERNS = [...]      # see §3.2
NEGATION_PATTERNS = [...]     # see §3.2
WIKI_PATH_PATTERNS = [...]    # see §3.2
NEGATION_WINDOW_ENV_VAR = "GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS"
DEFAULT_NEGATION_WINDOW_CHARS = 60

def main() -> dict:
    try:
        envelope = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}

    if envelope.get("stopHookActive"):
        return {}
    if envelope.get("reason") != "end_turn":
        return {}

    mode = os.environ.get(MODE_ENV_VAR, DEFAULT_MODE)
    if mode not in MODES:
        mode = DEFAULT_MODE

    last_message = envelope.get("lastAssistantMessage") or ""
    negation_window_chars = int(os.environ.get(NEGATION_WINDOW_ENV_VAR,
                                              str(DEFAULT_NEGATION_WINDOW_CHARS)))
    offload_phrases = scan_offload_phrases(last_message, negation_window_chars)

    receipts = collect_wiki_receipts(envelope.get("sessionId", ""))

    decision = compute_decision(offload_phrases, receipts, mode)
    write_evidence(HOOK_NAME, {
        "session_id": envelope.get("sessionId"),
        "mode": mode,
        "offload_phrases": offload_phrases,
        "wiki_receipts_count": len(receipts),
        "decision": "BLOCK" if decision else "ALLOW",
    })
    return decision

def compute_decision(offload, receipts, mode):
    if not offload:
        return {}
    if receipts:
        return {}
    if mode == "shadow":
        return {}
    reason = (
        "Wiki-query gate: this turn's final message contains offload language "
        f"({offload!r}) but I see no evidence of a workspace wiki query in the "
        "current turn. Before offloading to the operator, please:\n"
        "1. Search the wiki for the failing tool's canonical name\n"
        "   (rg -l \"<tool-name>\" P:/.data/wiki/concepts P:/.data/wiki/notes)\n"
        "2. Search for the error message itself\n"
        "   (rg \"<error-message>\" P:/.data/wiki/concepts P:/.data/wiki/notes)\n"
        "3. If the wiki documents a recovery I can perform as an agent, perform it.\n"
        "4. If the wiki does NOT document a recovery, offload is legitimate — "
        "restate your finding (which wiki paths you searched and what you found) "
        "and stop."
    )
    return {"decision": "block", "reason": reason}
```

### 4.4 FIX 2 — `yt_is_forward_sync.py` skeleton

```python
#!/usr/bin/env python3
"""Forward-sync provider: read yt-is transcript_cache before NLM fetch.

For each NotebookLM YouTube source, attempt to resolve video_id via the
title→video_id bridge. If yt-is has a cached transcript for that video_id,
write the same .md format as export_transcripts.py without calling
nlm source content.

Failure mode: any error → return (empty, error) → caller falls through to NLM.
All exceptions are caught with `except Exception` to honor the fail-through
contract (§3.6 / §8.3). Bare sqlite3.Error is too narrow — TypeError from
wrong arg counts, ImportError from missing packages, AttributeError from
schema drift all need to fall through.
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

# CRITICAL: ensure yt-is package is importable. The title_bridge module
# (lives in P:/packages/yt-is/scripts/) imports csf.* which requires the
# yt-is package root on sys.path. Mirrors import_nlm_transcripts.py:38-39.
_PKG_ROOT = Path(__file__).resolve().parent.parent.parent  # nlm-to-wiki/scripts → agent root
# Actually: this file lives at P:/.agents/skills/nlm-to-wiki/scripts/yt_is_forward_sync.py
# yt-is package root is P:/packages/yt-is. Use absolute path to be explicit.
YT_IS_PKG = Path("P:/packages/yt-is")
if str(YT_IS_PKG) not in sys.path:
    sys.path.insert(0, str(YT_IS_PKG))
if str(YT_IS_PKG / "scripts") not in sys.path:
    sys.path.insert(0, str(YT_IS_PKG / "scripts"))

NLM_TRANSCRIPTS_DIR = Path("P:/.data/wiki/sources/transcripts")
YTIS_TRANSCRIPT_DB = Path("P:/.data/yt-is/transcripts.sqlite")

# Known source values yt-is writes to transcript_cache.source column.
# Source: P:/packages/yt-is/tests/test_cache.py:250.
KNOWN_SOURCES = ("notebooklm", "cli", "youtube_transcript_api", "youtubei", "sdk")

def fetch_from_yt_is_cache(source: dict) -> tuple[str, str]:
    """Return (transcript_text, error_message). Empty + error → cache miss."""
    try:
        title = (source.get("title") or "").strip()
        source_type = source.get("type") or ""
        if source_type != "youtube" or not title:
            return "", "not_youtube_or_no_title"

        from csf.cache import get_cached_transcript_by_video_id  # NEW API; see §5.3
        from title_bridge import build_title_bridge, match_title

        bridge = build_title_bridge()
        if not bridge:
            return "", "bridge_empty"

        vid, match_type = match_title(title, bridge)
        if not vid:
            return "", "no_video_id_match"

        # NEW API: SELECT video_id=? LIMIT 1 — handles any (lang, source).
        # Pre-existing get_cached_transcript(video_id, lang, source) requires
        # knowing the source, which the forward-sync provider does not know.
        cached = get_cached_transcript_by_video_id(vid)
        if not cached:
            return "", "cache_miss"

        transcript_text = cached.transcript
        return transcript_text, ""
    except Exception as e:
        # Catch EVERYTHING — TypeError, ImportError, AttributeError,
        # sqlite3.Error, OSError — and fall through with an error message.
        return "", f"forward_sync_exception: {type(e).__name__}: {e}"
```

**Hook into `export_transcripts.py`** (concrete edit, addressing F-08):

In `export_transcripts.py`, modify the inner loop in `export_notebook()` (current code at lines 209-234). Replace the existing `content, err = fetch_content(sid, profile)` block with a forward-sync-first flow. The change is wrapped in `try/except Exception` so ANY failure (TypeError, ImportError, sqlite3.Error, etc.) falls through to NLM. This is the only place that can catch the provider's exceptions — the provider itself catches everything internally, but defense-in-depth requires the caller to also catch.

```python
# In export_transcripts.py, in export_notebook() inner loop, replace the
# `content, err = fetch_content(sid, profile)` call with:

from_cache = False
content = ""
err = ""
try:
    from yt_is_forward_sync import fetch_from_yt_is_cache
    content, err = fetch_from_yt_is_cache(src)
    if content:
        from_cache = True
        log(f"    yt-is cache hit for {sid[:12]} ({len(content)} chars)")
    else:
        log(f"    yt-is cache miss ({err}); falling through to NLM")
except Exception as e:
    log(f"    forward_sync_exception ({type(e).__name__}): {e}; falling through to NLM")
    content = ""
    err = "forward_sync_import_failed"

if not content:
    # Existing NLM path (unchanged)
    content, err = fetch_content(sid, profile)

# Increment counter later (after successful atomic_write):
if from_cache:
    from_cache_count += 1
```

The `from_cache_count` field is added to the returned dict from `export_notebook()`. The `atomic_write` call uses the same `build_transcript_md(src, notebook_id, content)` formatter as today — the `.md` file format is unchanged.

### 4.5 FIX 3 — `resolve_orphans.py` skeleton

```python
#!/usr/bin/env python3
"""Resolve unmatched YouTube transcripts via the miserly decision tree.

Per P:/.data/wiki/concepts/youtube-api-search-list-only-endpoint-for-title-to-video-id.md
the order is: free first (analysis_status, clusters.json, Takeout History),
then paid (search.list as last resort). **Honesty note:** the 497 orphans are
*defined* as unmatched against analysis_status and clusters.json — Sources 1-2
will resolve ~0 by construction. F3's real value is (a) the checkpoint-before-
import contract (prevents the 257-result loss from recurring) and (b) the
Takeout History + search.list paths. The free-first ordering is retained for
completeness and because new data may have been added to analysis_status since
the original match run.
paid last (search.list, 100 units/call). Results are checkpointed BEFORE
any import step — never lose results again.

Usage:
  python resolve_orphans.py --dry-run             # preview checkpoint without committing (still writes checkpoint file)
  python resolve_orphans.py                       # run resolution + write checkpoint; one title per search.list call (per F-03 fix)
  python resolve_orphans.py --recover             # load prior checkpoint, retry import
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# CRITICAL: ensure yt-is package is importable for title_bridge (which
# imports csf.*). Mirrors F-06 sys.path requirement.
_PKG_ROOT = Path("P:/packages/yt-is")
sys.path.insert(0, str(_PKG_ROOT))
sys.path.insert(0, str(_PKG_ROOT / "scripts"))

from title_bridge import build_title_bridge, match_title, normalize_title

ORPHAN_INDEX_PATH = Path("P:/.data/wiki/sources/transcripts/_orphans.json")
CHECKPOINT_DIR = Path("P:/.data/wiki/sources/transcripts/_checkpoints")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# Known source values for transcript_cache.source. Source: test_cache.py:250.
# Used by takeout_index loader only; not by search.list path.

def checkpoint_path() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return CHECKPOINT_DIR / f"orphan-search-{ts}.json"

def load_takeout_index() -> dict[str, list[str]] | None:
    """Load YouTube Takeout History watch URLs (video_id per title).
    Returns None if no Takeout dump is available. Operator pre-positions
    the dump at P:/.data/wiki/sources/transcripts/_takeout_history.json.
    """
    path = Path("P:/.data/wiki/sources/transcripts/_takeout_history.json")
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Takeout JSON shape varies; expect {title: video_id} or list of {title, url}.
    index: dict[str, list[str]] = {}
    if isinstance(raw, dict):
        for title, vid in raw.items():
            if vid:
                index.setdefault(normalize_title(title), []).append(vid)
    elif isinstance(raw, list):
        for entry in raw:
            title = entry.get("title", "")
            url = entry.get("url", "") or entry.get("video_url", "")
            m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
            if title and m:
                index.setdefault(normalize_title(title), []).append(m.group(1))
    return index

def resolve_one(title: str, bridge: dict, takeout_index: dict | None) -> tuple[str, str, str]:
    """Return (video_id, source, error). video_id="" means unresolved."""
    norm = normalize_title(title)

    # Source 1: analysis_status bridge (free)
    if norm in bridge:
        vids = bridge[norm]
        if len(vids) == 1:
            return vids[0], "analysis_status", ""
        if len(vids) > 1:
            return "", "", f"ambiguous: {len(vids)} candidates"

    # Source 2: takeout_history (free if dump available)
    if takeout_index and norm in takeout_index:
        vids = takeout_index[norm]
        if len(vids) == 1:
            return vids[0], "takeout_history", ""
        if len(vids) > 1:
            return "", "", f"ambiguous_takeout: {len(vids)} candidates"

    # Source 3: paid — search.list (last resort)
    return "", "", "needs_search_list"

def search_list_one(title: str, api_key: str) -> str | None:
    """Single-title search.list call. Returns video_id or None on no match / quota error.
    Uses ONE title per call to avoid the positional-mapping bug
    (search.list with multi-term OR query returns relevance-ranked items[]
    with no per-term attribution; positional assignment is wrong).
    Source: developers.google.com/youtube/v3/docs/search/list — response is
    a single items[] array; each item has id.videoId and snippet.title.
    """
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults=1&q={urllib.parse.quote(title)}&key={api_key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403 and b"quotaExceeded" in e.read():
            raise QuotaExceededError(api_key) from e
        raise
    items = data.get("items", [])
    if not items:
        return None
    # Re-match the result title to the query title via normalize_title.
    # Drops results whose snippet.title doesn't match (catches the rare case
    # where search.list returns an unrelated video for a single-word query).
    result_title = items[0]["snippet"]["title"]
    if normalize_title(result_title) != normalize_title(title):
        return None
    return items[0]["id"]["videoId"]

class QuotaExceededError(Exception):
    """Raised when search.list returns quotaExceeded for a specific key."""
    def __init__(self, key: str):
        super().__init__(f"quota exceeded for key ending ...{key[-4:]}")
        self.key = key

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--recover", action="store_true",
                    help="load prior checkpoint, no new search.list calls")
    args = ap.parse_args()

    # Load orphans
    if not ORPHAN_INDEX_PATH.exists():
        print(f"ERROR: orphan index not found at {ORPHAN_INDEX_PATH}", file=sys.stderr)
        print("  Run: python import_nlm_transcripts.py --export-orphans", file=sys.stderr)
        return 2
    orphans = json.loads(ORPHAN_INDEX_PATH.read_text(encoding="utf-8"))

    # Source 1 + 2: free
    bridge = build_title_bridge()
    takeout_index = load_takeout_index()

    quota_used = 0  # INITIALIZED at top so the post-loop serialization never hits NameError
    results = []
    for orphan in orphans:
        vid, source, err = resolve_one(orphan["title"], bridge, takeout_index)
        if vid:
            results.append({"title": orphan["title"], "video_id": vid, "source": source})
        elif err == "needs_search_list":
            results.append({"title": orphan["title"], "video_id": None, "needs_paid": True})

    # Source 3: paid (search.list) — one title per call, multi-key rotation
    paid_orphans = [r for r in results if r.get("needs_paid")]
    quota_cap = int(os.environ.get("ORPHAN_QUOTA_CAP", "240"))
    keys = [k for k in os.environ.get("YOUTUBE_API_KEYS", "").split(",") if k]
    if not args.recover and paid_orphans and not keys:
        print("ERROR: no YOUTUBE_API_KEYS env var; cannot run search.list", file=sys.stderr)
        return 3

    if not args.recover and paid_orphans and keys:
        key_idx = 0
        active_key = keys[key_idx]
        for o in paid_orphans:
            if quota_used >= quota_cap:
                print(f"QUOTA CAP ({quota_used} calls) reached; stopping")
                break
            try:
                vid = search_list_one(o["title"], active_key)
                quota_used += 1
                if vid:
                    o["video_id"] = vid
                    o["source"] = "search_list"
                else:
                    o["source"] = "search_list_no_match"
            except QuotaExceededError:
                # Rotate to next key
                key_idx += 1
                if key_idx >= len(keys):
                    print(f"ALL KEYS EXHAUSTED after {quota_used} calls; stopping")
                    break
                active_key = keys[key_idx]
                print(f"Rotated to key ending ...{active_key[-4:]}")
                # Retry the same orphan with the new key — but DON'T increment quota_used yet
                try:
                    vid = search_list_one(o["title"], active_key)
                    quota_used += 1
                    if vid:
                        o["video_id"] = vid
                        o["source"] = "search_list"
                except QuotaExceededError:
                    print(f"New key also exhausted; skipping {o['title'][:50]}")
                    continue

    # CHECKPOINT — written UNCONDITIONALLY (preserves the search/import decoupling).
    # In dry-run mode, the operator inspects this file BEFORE running the import.
    cp = checkpoint_path()
    cp.write_text(json.dumps({
        "started_at": datetime.now(timezone.utc).isoformat(),
        "orphans_total": len(orphans),
        "results": results,
        "quota_calls_used": quota_used,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        print(f"DRY RUN — checkpoint written to {cp}")
        print("  Inspect it before running --from-checkpoint on the import side.")
        return 0

    n_resolved = sum(1 for r in results if r.get("video_id"))
    print(f"Resolved {n_resolved}/{len(orphans)} orphans. Quota used: {quota_used} calls.")
    print(f"Checkpoint: {cp}")
    print(f"Next: python import_nlm_transcripts.py --from-checkpoint {cp}")
    return 0
```

**Note on F-03 (search.list positional mapping bug):** the skeleton above uses ONE title per call (`search_list_one`) instead of batched OR queries. This is correct but recomputes the quota budget: 497 orphans - free-source-resolved = ~240 orphans × 1 call/orphan = 240 calls (matches the original cap). The original KD-9 batching claim ("saves 80%") is retracted — search.list does not support per-query-term attribution, so batching would produce wrong video_id→title mappings (data corruption). One-call-per-title is the only correct approach. Multi-day pacing may be required if orphans > daily cap.

### 4.6 Tests

| Test file | Test count | Coverage focus |
|-----------|-----------|----------------|
| `test_wiki_query_gate.py` | 25 (mirroring prior handoff design §4.6) | Offload detection, negation window, wiki-receipt detection (incl. nested paths), qmd receipt, fail-open, stopHookActive, reason filter, mode dispatch |
| `test_yt_is_forward_sync.py` | 8 | Cache hit returns transcript; cache miss returns empty+error; bridge empty returns empty+error; title normalization; ambiguous match; sqlite error path; nlm content integration (end-to-end with mock cache) |
| `test_resolve_orphans.py` | 6 | Free-first ordering; checkpoint written BEFORE import; quota cap enforcement; recover mode skips search.list; checkpoint format; takeout index optional |

---

## 5. API/Interface Changes

### 5.1 FIX 1: new env vars

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `GROK_WIKI_QUERY_GATE_MODE` | `shadow` \| `receipt_authoritative` | `shadow` | Operational mode |
| `GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS` | int ≥ 1 | `60` | Negation window (configurable per prior handoff F-17) |

### 5.2 FIX 1: new evidence log

`~/.grok/hooks/.evidence/wiki-query-gate.jsonl` — append-only, one JSON object per Stop event.

### 5.3 FIX 2: one additive public API (csf.cache)

The forward-sync provider depends on **one new function added to `csf/cache.py`** — the existing `get_cached_transcript(video_id, lang, source)` requires knowing the source, which forward-sync does not know. All other yt-is public APIs are unchanged.

**New function contract:**

```python
def get_cached_transcript_by_video_id(video_id: str) -> "TranscriptCache | None":
    """Return the first cached transcript for a video_id, regardless of (lang, source).

    Mirrors `has_cached_transcript(video_id)` (cache.py:583) existence semantics,
    but returns the full TranscriptCache object instead of just a bool.

    SQL: SELECT video_id, lang, source, transcript, cached_at, terminal_id, metadata_json
         FROM transcript_cache WHERE video_id = ? LIMIT 1

    Args:
        video_id: must be 11 chars matching `_VIDEO_ID_PATTERN`
                  (re.compile(r"^[a-zA-Z0-9_-]{11}$") at cache.py:21)

    Returns:
        TranscriptCache object (parses metadata_json via TranscriptCache.metadata
        property at cache.py:69-77), or None if no entry exists.

    Raises:
        sqlite3.OperationalError on DB connectivity issues (caller wraps in
        try/except Exception per §3.6 fail-through contract).

    Note: Bypasses cache_key entirely — does NOT call `_make_cache_key`
    (cache.py:205). cache_key is the composite hash used by the existing
    write-path; the forward-sync provider does not need it because it
    retrieves by video_id, accepting any (lang, source) combination.
    """
```

**Implementation plan for the new function:** added as part of F2-2 (see §13). Existing helpers to reuse: `_connect_shared_db()` (cache.py:33), `get_shared_db_path()` (cache.py:38), `TranscriptCache` dataclass (cache.py:55). Pattern mirrors `_read_entry()` (cache.py:156) but selects by `video_id` instead of `cache_key`.

The shared `title_bridge.py` module is importable from both packages (no API change).

### 5.4 FIX 3: no public API changes

`resolve_orphans.py` is a standalone script. The `import_nlm_transcripts.py` gains one new optional flag `--from-checkpoint` that reads a checkpoint file instead of re-running search.

### 5.5 FIX 3: new env vars

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `YOUTUBE_API_KEYS` | comma-separated API keys | (none) | Multi-key rotation for search.list |
| `ORPHAN_QUOTA_CAP` | int | `240` | Max search.list calls per run |

---

## 6. Data Model

### 6.1 FIX 1: hook envelope (consumed, unchanged)

Standard Grok Build Stop envelope. Fields used: `lastAssistantMessage`, `stopHookActive`, `reason`, `sessionId`. Same as prior handoff §6.1.

### 6.2 FIX 1: evidence record

```json
{
  "ts": 1753612800.123,
  "session_id": "abc123",
  "mode": "shadow",
  "stopHookActive": false,
  "reason": "end_turn",
  "offload_phrases": ["you must do browser OAuth"],
  "wiki_receipts_count": 0,
  "decision": "ALLOW"
}
```

### 6.3 FIX 2: cache read shape (consumed)

Reads from yt-is `transcript_cache` table. Schema (verified per `cache.py:107-128`):
```
cache_key: str (hash of video_id+lang+source)
video_id: str (11 chars)
lang: str
source: str ('notebooklm' for nlm-to-wiki imports)
transcript: str
metadata_json: str (JSON-encoded; includes nlm_source_id, match_type for forward-sync verification)
cached_at: datetime ISO 8601
terminal_id: str
```

### 6.4 FIX 2: frontmatter (produced)

Same shape as `export_transcripts.py:build_transcript_md()` — existing fields (`source_id, title, notebook_id, url, type, exported`) are unchanged. **Minor additive field** added to frontmatter: `from_cache: yt_is_cache` (set when the transcript was sourced from yt-is cache, omitted when from NLM path). This is a documented schema addition, NOT "no schema change" — clarified per F-12. The yt-is `transcript_cache.metadata_json` column is a separate SQLite column (not the .md frontmatter); cache writes to that column are unchanged. Downstream reconcilers can distinguish cache-imported from nlm-imported transcripts via the `from_cache` frontmatter key.

### 6.5 FIX 3: orphan index (consumed by `resolve_orphans.py`)

```json
// P:/.data/wiki/sources/transcripts/_orphans.json
{
  "generated_at": "2026-07-30T...",
  "orphans": [
    {"source_id": "<uuid>", "title": "<title>", "notebook_id": "<uuid>"}
  ]
}
```

Generated by `import_nlm_transcripts.py --export-orphans` (new flag added).

### 6.6 FIX 3: checkpoint (produced)

```json
{
  "started_at": "2026-07-30T14:32:01Z",
  "orphans_total": 497,
  "quota_calls_used": 87,
  "results": [
    {"title": "how to do X", "video_id": "abc123xyz45", "source": "search_list"},
    {"title": "another orphan", "video_id": null, "source": "needs_search_list", "needs_paid": true}
  ]
}
```

Path: `P:/.data/wiki/sources/transcripts/_checkpoints/orphan-search-YYYYMMDD-HHMMSS.json`

---

## 7. Alternatives

### 7.1 Hidden anchor (shared assumption)

All three fixes share one assumption: **knowledge already exists in the workspace; the agent just doesn't retrieve it at the right moment**. RC-1's fix gates on retrieval-evidence. RC-2's fix provides the retrieval pathway. RC-3's fix encodes the retrieval hierarchy. The "right moment" varies (error-handling loop, export-time, orphan-resolution run), but the structural pattern is the same: retrieval-as-step, not retrieval-as-best-effort.

### 7.2 ALTERNATIVES GATE for RC-1 (Stop hook enforcement)

```
Options: (1) Stop hook with two-signal (chosen)  (2) PreToolUse gate  (3) Advisory rule only
Selection criterion: reliability tier reachable on Grok Build native primitives
Chosen: (1) — wins because Stop hook is the only event where "did this turn end with
        an offload?" is observable as a single decision point (lastAssistantMessage is
        not available at PreToolUse; advisory rules have ~50% compliance ceiling per
        P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md)
```

The prior handoff (`P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md`) exhaustively evaluated these. No new alternatives.

### 7.3 ALTERNATIVES GATE for RC-2 (forward sync)

```
Options: (1) Hook into export_transcripts.py (chosen)  (2) Reverse direction: yt-is fetches from wiki/sources/transcripts on cache miss  (3) New sync direction with NLM-as-proxied fetcher
Selection criterion: lowest future cost AND lowest risk of duplicate writes
Chosen: (1) — wins because export_transcripts.py already has the .md writer; yt-is
        cache check happens BEFORE NLM; cache hit skips NLM entirely.
        (2) would require yt-is to know about the nlm-to-wiki path (violates
        package boundary); (3) requires new nlm-to-wiki CLI that knows about
        yt-is (same violation, with extra dispatch chain).
```

### 7.4 ALTERNATIVES GATE for RC-3 (orphan resolution)

```
Options: (1) Miserly decision tree + checkpoint (chosen)  (2) Bulk search.list all 497 + import  (3) Defer orphans entirely
Selection criterion: cost vs coverage AND loss-resistance
Chosen: (1) — wins because free sources (analysis_status, clusters.json, Takeout)
        likely cover a large fraction of 497 orphans; search.list is reserved
        for true unknowns.
        (2) wastes 100 search.list calls on orphans that free sources could have
        resolved; (3) leaves the gap unaddressed and forces the next sync to
        re-investigate.
```

---

## 8. Security

### 8.1 Threat model

| Threat | Mitigation |
|--------|-----------|
| Operator accidentally enables `receipt_authoritative` and a legitimate offload is blocked | Fail-open on any exception; block reason text is specific. Unconditional ALLOW on `stopHookActive=true` is the hook re-entry guard. **Platform backstop:** Grok Build also caps Stop-hook continuations at 8 per turn (`~/.grok/docs/user-guide/10-hooks.md`), after which the gate is overridden — this is a platform feature, not something the hook implements. |
| Agent crafts a transcript record to fake a wiki-query receipt | Transcript is on disk and read-only from the hook's perspective; faking requires write access. |
| FIX 2 forward-sync returns stale transcript (yt-is cache out of date with NLM) | Source-side validation: cache write timestamp recorded in metadata_json; downstream reconcilers can flag staleness. `nlm source content` is still authoritative for status=3 sources. |
| FIX 3 `search.list` quota exhausted → DoS on subsequent runs | Cap (240 calls/run) + per-key rotation; checkpoint file persisted; next-day resume. |
| `YOUTUBE_API_KEYS` env var leaked | Keys are read-only at script invocation; no logging; no echo. |

### 8.2 Privilege

All three fixes run with the user's full session privileges. No privilege escalation. Hook script reads one transcript file + writes one evidence file (FIX 1). Forward-sync script reads one SQLite DB + writes one .md file (FIX 2). Orphan resolver makes HTTPS calls to YouTube Data API (FIX 3).

### 8.3 Fail-open (FIX 1) and fail-through (FIX 2/3)

- FIX 1: any internal exception → exit 0 (ALLOW). Evidence log records the exception.
- FIX 2: any bridge build failure, sqlite error, or cache read error → empty transcript + error message → caller falls through to NLM path.
- FIX 3: any YouTube API error → record in checkpoint; continue with other orphans (unless quota exceeded, in which case stop + checkpoint).

### 8.4 No destructive operations

None of the three fixes delete, move, or rewrite user content outside their own evidence/checkpoint files. FIX 2 writes to `wiki/sources/transcripts/<uuid>.md` (same path as existing NLM path; no overwrite behavior change). FIX 3 writes only to `_checkpoints/`.

---

## 9. Observability

### 9.1 FIX 1 metrics

Computed by `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py`:

| Metric | Target |
|--------|--------|
| Offload-without-wiki rate | trending toward 0 (the primary signal) |
| Block rate (active mode) | <2% |
| Fail-open rate | <1% |
| Operator-labeled FP rate | <5% |

### 9.2 FIX 2 metrics

Added to `export_transcripts.py` result JSON:

| Metric | How computed |
|--------|--------------|
| `from_cache_count` | sources written from yt-is cache (skip NLM) |
| `from_nlm_count` | sources written from NLM path (unchanged from before) |
| `bridge_empty` | true if bridge had 0 entries (forward-sync disabled silently) |

Operator can run `python export_transcripts.py --notebook <id>` and see the ratio. Target reframing (per F-16): the ≥40% figure used **total cached video_ids (10,072) as denominator** — that's the wrong denominator for forward-sync. The correct denominator is **YouTube sources in the notebook being exported** (the count of `type: youtube` sources that are matched by the title bridge). The expected cache-hit rate is therefore the fraction of those sources whose normalized title appears in the title-bridge — empirically ~77% (3,918 / 5,070 YouTube transcripts that `import_nlm_transcripts.py` successfully resolved). The target metric is:

> **`from_cache_count / youtube_sources_in_notebook ≥ bridge_match_rate`** (typically ≥70% for notebooks with Watch Later overlap, lower for History-only notebooks).

The previous "≥40% of total cache" framing was misleading and is replaced by the source-bridge-match-rate framing.

### 9.3 FIX 3 metrics

| Metric | How computed |
|--------|--------------|
| Orphans resolved by free sources | count from checkpoint results |
| Orphans resolved by search.list | count from checkpoint results |
| Quota calls used | from checkpoint header |
| Checkpoint path | from script output |

### 9.4 Discrimination test for FIX 1 (most important)

Re-run the nlm-class reproduction transcript (offload "you must do browser OAuth" with no wiki-query tool call). The hook should:
- shadow mode: log evidence record with `offload_phrases` non-empty, `wiki_receipts_count: 0`, `decision: ALLOW`
- receipt_authoritative: emit block reason text; agent must query wiki in next turn

This is the discriminating test for whether the design actually closes RC-1.

---

## 10. Key Decisions

| # | Decision | Why | Alternatives rejected |
|---|----------|-----|------------------------|
| KD-1 | FIX 1 uses Stop hook (not PreToolUse or advisory) | Offload signal is in the final message; PreToolUse fires before message exists; advisory has ~50% reliability ceiling | PreToolUse (worse signal timing); advisory (proven failure) |
| KD-2 | FIX 1 reuses prior handoff design (with `_hook_base` extraction inline if absent) | The prior design is complete and reviewed; re-writing would duplicate work | Fresh design (rejected; cost = no benefit) |
| KD-3 | FIX 1 ships in shadow mode by default | Operator correction 2026-07-26: "default to phased rollout with measured data"; FP rate unknown | Immediate active mode (no measurement) |
| KD-4 | FIX 2 hooks into `export_transcripts.py` (not `sync.py`, not yt-is) | export_transcripts.py is the export stage; the cache check is a fetch-time concern, not a sync-time concern | sync.py (wrong layer; export already called per-notebook); yt-is reverse direction (package boundary violation) |
| KD-5 | FIX 2 shares `title_bridge.py` between nlm-to-wiki and yt-is (or importable from both) | The bridge logic is identical to `import_nlm_transcripts.py:build_bridge_from_clusters + build_bridge_from_analysis`. Duplication would create drift risk. | Inline duplicate in yt_is_forward_sync.py (DRY violation, ~80 LOC) |
| KD-6 | FIX 2 silently disables forward-sync when bridge is empty | Empty bridge = no way to match; failing loudly would spam logs and confuse operators | Loud failure on empty bridge (operator-visible; non-actionable) |
| KD-7 | FIX 3 uses miserly decision tree (free-first, paid-last) | YouTube API quota is 100 units/call; multi-key rotation handles N working keys (N=1 reported, see F-18 invalidation); single-title calls (KD-9a) keep the math honest | Bulk search.list first (wastes free sources); defer orphans (gap persists); batched search.list (F-03 data corruption) |
| KD-8 | FIX 3 checkpoints results BEFORE any import step | 257-result loss incident (2026-07-30) was caused by `--import` re-running search.list and overwriting results | Coupled search + import (proven failure mode) |
| KD-9 (RETRACTED via F-03) | FIX 3 batched queries (5 orphans/call) — REJECTED | search.list does NOT support per-query-term attribution in the response; positional mapping would produce wrong video_id→title mappings (data corruption). **KD-9 is retracted.** FIX 3 now uses ONE title per call. | Single-title queries (correct, no data corruption) |
| KD-9a (REPLACES KD-9) | FIX 3 single-title search.list calls (1 orphan/call) | Correct, no data corruption; 1 working key × 100 calls/day = 100 orphans/day | Batched (data corruption risk); no search.list (gap persists) |
| KD-10 | FIX 3 quota cap (240 calls/run) + multi-key rotation | 100 units/day × N working keys; 240 caps total spend; rotation is implemented in skeleton (§4.5 `QuotaExceededError` + `key_idx` loop, addresses F-04) | No cap (runaway script); single-key (underutilizes quota) |
| KD-11 | FIX 3 separate scripts for search and import (resolve_orphans.py + import_nlm_transcripts.py --from-checkpoint) | Decoupling prevents the overwrite bug | Single script with --search + --import flags (rejected; same bug risk) |
| KD-12 | All three fixes: ship without removing the prior path | Fail-open / fail-through contracts; the prior path is the safety net. Removing it would create a single point of failure. | Replace prior path (creates single point of failure) |
| KD-13 | All three fixes: no wiki content changes | The wiki already documents the patterns; this design operationalizes existing knowledge | New wiki pages (over-documentation; AGENTS.md paper: thin pages hurt performance) |
| KD-14 | Sub-agent Stop fires ARE gated by FIX 1 | Same pattern-completing diagnosis happens in sub-agents; not gating leaves a gap | Gating only top-level Stop (gap persists) |

---

## 11. Risk Table

| Risk | P | I | Mitigation |
|------|---|---|------------|
| FIX 1 offload patterns have unacceptable FP rate on real transcripts | M | H | Shadow mode first (≥100 events); phase-1 only after FP rate <5%; negation window; operator-discoverable log |
| FIX 1 `chat_history.jsonl` field schema differs from assumption | ~~M~~ → verified per prior handoff | ~~M~~ → N/A | Schema verified: `name` + `arguments` as JSON string. Defensive parse-on-error in iterator. |
| FIX 1 `_hook_base.py` extraction breaks `quality_gate.py` behavior | L | H | Refactor in same commit; full test suite must pass unchanged |
| FIX 2 `yt-is` cache returns stale transcript | L | M | Cache timestamp in metadata_json; reconciler can flag staleness. NLM path remains authoritative fallback. |
| FIX 2 title normalization drift between nlm-to-wiki and yt-is | M | M | Shared `title_bridge.py` module ensures single source of truth |
| FIX 2 bridge build takes >30s on 60K analysis_status rows | M | L | One-time per sync run; OK if it adds 30s to Stage A |
| FIX 3 search.list returns wrong video for generic/ambiguous titles | M | M | Single-title calls with `maxResults=1`; `normalize_title` re-match (4.5 `search_list_one`) drops results whose `snippet.title` doesn't exactly match; unresolved orphans left null in checkpoint for operator review (revised per F-22 — no longer describes the retracted batched-search approach) |
| FIX 3 quota cap too low (cannot resolve all 497 orphans) | M | L | Cap is configurable; checkpoint allows resume |
| FIX 3 YOUTUBE_API_KEYS env var not set | M | L | Script returns error code 3 with clear message; operator can set env var or take Takeout History dump instead |
| FIX 3 Takeout History not available (most likely case) | M | L | Falls through to search.list as before; no regression |
| All: any fix breaks pipeline regression | L | H | Each fix is additive; prior path is the safety net |
| All: testing infrastructure not present | M | M | All tests use real temp files (per testing rule); fixtures exist for similar yt-is/nlm tests |

P/I scale: L (low), M (medium), H (high).

---

## 12. Rollout

### 12.1 Phase 0 — Ship in shadow

All three fixes ship in this phase. No fix blocks anything. No fix changes user-visible behavior unless explicitly activated.

| Fix | Phase 0 state | Activation gate |
|-----|---------------|------------------|
| FIX 1 | Hook registered, shadow mode, logs only | Operator-gated after ≥100 events + FP <5% |
| FIX 2 | Hook in place, silently enabled | Always-on (no gating needed; net positive) |
| FIX 3 | Script available, dry-run default | Operator runs when ready; checkpoint pattern enforced from v1 |

### 12.2 Phase 1 — Activate enforcement (FIX 1 only)

| Field | Value |
|-------|-------|
| FIX 1 mode | `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` |
| Operator action | Set env var after shadow FP rate <5% |
| FIX 2/3 | Unchanged |

### 12.3 Rollback

- FIX 1: `GROK_WIKI_QUERY_GATE_MODE=shadow` (immediate) or `rm ~/.grok/hooks/wiki-query-gate.json`
- FIX 2: revert `export_transcripts.py` change; cache reads are no longer attempted
- FIX 3: no-op; the orphan resolver is a standalone script that does not run automatically

### 12.4 Cross-phase invariants

- All fixes preserve the prior path as safety net
- Fail-open / fail-through contracts are preserved in all phases
- Hook script exit codes: 0 always (block is via JSON output, not exit code)

---

## 13. Implementation Plan

**Ordering rationale (revised per /tp critique):** F2 ships first — it is the goal-aligned, additive, fail-through fix with lowest risk and direct productivity impact (~40% NLM call reduction). F1 ships second — it is the structural behavioral fix (highest root-cause leverage for preventing fabricated blockers, but highest risk because it touches live hook infrastructure). F3 ships last or is deferred — it addresses data completeness, not the duplicate-fetch goal, and spends paid API quota. An operator who prioritizes "stop the behavioral failure" over "optimize the pipeline" may rationally reorder F1 before F2; this plan defaults to goal-alignment.

Each unit is a single commit (or commit group if files are tightly coupled).

### FIX 1 units (ship SECOND — behavioral root-cause fix, highest leverage for preventing fabricated blockers)

**Scoping note (revised per /tp critique):** F1 is scoped to minimal v1: shadow hook + evidence log only. The `_hook_base.py` extraction, metrics aggregator, and SubagentStop dual-registration are deferred to a v2 AFTER shadow-mode FP rate is measured. The hypothesis is binary: does blocking on offload-without-wiki-receipt reduce fabricated offloads? Test that first. Additionally, the wiki's own cheaper workflow rules (Fix 1+2+3 from `error-handling-loops-skip-wiki-query.md`) were never deployed — the "~50% advisory ceiling" was measured on different rules. Consider trying those before the hook.

#### Unit F1-1 — Extract `_hook_base.py` (if absent)

| Field | Value |
|-------|-------|
| Title | `refactor(hooks): extract _hook_base.py from quality_gate.py` (if not already done) |
| Files affected | `~/.grok/hooks/scripts/_hook_base.py` (new, if absent); `quality_gate.py` (refactored) |
| Dependencies | None |
| Description | If the prior handoff's Unit 1 was completed, this unit is a no-op (verify file exists; skip if so). Otherwise extract shared patterns. |
| Acceptance | (a) `_hook_base.py` exists OR verified present; (b) `quality_gate.py` tests pass unchanged |
| Disposition | **COMMIT_THIS_SESSION** (verification + skip-if-present) |

#### Unit F1-2 — Implement `wiki_query_gate.py` core

| Field | Value |
|-------|-------|
| Title | `feat(hooks): add wiki_query_gate.py with offload + receipt detection` |
| Files affected | `wiki_query_gate.py` (new); `tests/test_wiki_query_gate.py` (new) |
| Dependencies | F1-1 |
| Description | Implement Stop hook. Offload patterns §3.2, receipts §3.2, decision matrix §3.2, fail-open §8.3. Shadow mode is the only active mode in this unit. |
| Acceptance | (a) All 25 tests pass; (b) ≥80% line coverage; (c) shadow mode exits 0 on test envelope; (d) evidence log written per Stop event |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F1-3 — Register the hook on BOTH Stop and SubagentStop

| Field | Value |
|-------|-------|
| Title | `feat(hooks): register wiki-query-gate on Stop + SubagentStop` |
| Files affected | `~/.grok/hooks/wiki-query-gate.json` (new) |
| Dependencies | F1-2 |
| Description | Register the hook on **both** `Stop` (top-level agent turn) AND `SubagentStop` (sub-agent turn) events, 30s timeout each. Per `~/.grok/docs/user-guide/10-hooks.md:97`, `SubagentStop` is a **separate event** that "fires once, in the subagent, with stop decision control" — distinct from `Stop`. KD-14 commits to gating sub-agent offloads too, so registration MUST cover both events. **Verification gap (per /tp):** the hooks doc also says agent-frontmatter `Stop` hooks "automatically remap" to `SubagentStop` inside subagents — this may make explicit dual-registration redundant (or may double-fire). **Test this empirically before F1-3 ships:** register on `Stop` only, run a subagent that offloads, check whether the hook fires. If it does, drop the `SubagentStop` registration. Mirrors `quality-gate.json` style. |
| Acceptance | (a) Hook JSON valid; (b) `~/.grok/active-surface.last.md` lists `wiki-query-gate` under BOTH `Stop` and `SubagentStop`; (c) shadow mode emits evidence on both event types; (d) no false-positive blocks |
| Disposition | **COMMIT_THIS_SESSION** |

The registration JSON template (addresses F-07):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\wiki_query_gate.py\"", "timeout": 30}
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {"type": "command", "command": "python \"C:\\Users\\brsth\\.grok\\hooks\\scripts\\wiki_query_gate.py\"", "timeout": 30}
        ]
      }
    ]
  }
}
```

#### Unit F1-4 — Aggregate metrics script

| Field | Value |
|-------|-------|
| Title | `feat(hooks): add aggregate_wiki_gate_metrics.py` |
| Files affected | `aggregate_wiki_gate_metrics.py` (new); `tests/test_aggregate_metrics.py` (new) |
| Dependencies | F1-3 |
| Description | Compute metrics §9.1 from evidence log. Emit Markdown summary. |
| Acceptance | (a) Script computes all 4 metrics; (b) report regenerates; (c) tests cover empty + mixed records |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F1-5 — Document gate in AGENTS.md

| Field | Value |
|-------|-------|
| Title | `docs(AGENTS): add wiki-query gate reference` |
| Files affected | `P:/AGENTS.md` (3-line entry under enforcement mechanisms) |
| Dependencies | F1-3 |
| Description | Pointer to the gate so operators and other sessions can discover it. |
| Acceptance | (a) Mentions `wiki_query_gate.py`; (b) mentions env var; (c) points to evidence log location |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F1-6 — Phase-1 transition (operator-gated)

| Field | Value |
|-------|-------|
| Title | Phase-1: set `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` |
| Files affected | None (env var only) |
| Dependencies | F1-3 + ≥100 Stop events + operator FP review |
| Description | Operator sets the env var after data review. |
| Acceptance | (a) ≥100 records; (b) FP rate <5%; (c) env var persisted in operator's shell |
| Disposition | **HANDOFF** (operator decision) |

### FIX 2 units (ship FIRST — goal-aligned, lowest risk, directly productive)

#### Unit F2-1 — Extract `title_bridge.py`

| Field | Value |
|-------|-------|
| Title | `refactor: extract title_bridge.py from import_nlm_transcripts.py` |
| Files affected | `P:/packages/yt-is/scripts/title_bridge.py` (new); `import_nlm_transcripts.py` (refactored to import) |
| Dependencies | None |
| Description | Move `build_bridge_from_clusters`, `build_bridge_from_analysis`, `merge_bridges`, `normalize_title`, `match_title` to shared module. **Add `build_title_bridge()` as a one-call wrapper** that returns `merge_bridges(build_bridge_from_clusters(...), build_bridge_from_analysis(...))` — this is the canonical API used by both FIX 2 (§4.4 skeleton) and FIX 3 (§4.5 skeleton). |
| Acceptance | (a) Module importable from yt-is path; (b) `import_nlm_transcripts.py` behavior unchanged; (c) existing tests pass; (d) **canonical API contract** documented: `build_title_bridge() -> dict[str, list[str]]`, `match_title(title, bridge) -> tuple[str \| None, str]`, `normalize_title(title) -> str` |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F2-2 — Add forward-sync provider

| Field | Value |
|-------|-------|
| Title | `feat(nlm-to-wiki): add yt_is_forward_sync.py` |
| Files affected | `P:/packages/yt-is/csf/cache.py` (modified — add `get_cached_transcript_by_video_id` per F-02 + §5.3 contract); `P:/.agents/skills/nlm-to-wiki/scripts/yt_is_forward_sync.py` (new); `tests/test_yt_is_forward_sync.py` (new) |
| Dependencies | F2-1 |
| Description | Provider that reads yt-is cache before NLM fetch. Fail-through to NLM on any error. **F2-2 is the OWNING UNIT for the new cache API** (`get_cached_transcript_by_video_id`) — added to cache.py as part of this unit, not deferred. The new function is required for the provider's `from csf.cache import get_cached_transcript_by_video_id` to succeed. |
| Acceptance | (a) All 8 tests pass; (b) ≥80% line coverage; (c) cache hit returns transcript; (d) cache miss returns empty + error |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F2-3 — Hook into `export_transcripts.py`

| Field | Value |
|-------|-------|
| Title | `feat(nlm-to-wiki): check yt-is cache before nlm source content` |
| Files affected | `export_transcripts.py` (modified); result JSON gains `from_cache_count` field |
| Dependencies | F2-2 |
| Description | Add cache-check stage before `fetch_content`. Build bridge once per notebook. |
| Acceptance | (a) Forward-sync enabled; (b) cache miss falls through to NLM; (c) result JSON includes `from_cache_count`; (d) sync.py Stage A still completes with rc=0 or rc=5 |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F2-4 — End-to-end verification

| Field | Value |
|-------|-------|
| Title | Verify: forward-sync skips NLM for cached transcripts |
| Files affected | None (verification only) |
| Dependencies | F2-3 |
| Description | Run `export_transcripts.py --notebook <id>` on a notebook with cached transcripts. Verify `from_cache_count > 0` and NLM call count drops. |
| Acceptance | (a) **≥70% of YouTube sources matched by the title bridge** come from cache (revised per F-16/F-20: was ≥40% which used wrong denominator); (b) `.md` files have correct frontmatter (`from_cache: yt_is_cache` field set on cache-imported); (c) transcript body matches cache content |
| Disposition | **VERIFICATION** (operator or `/go` automated check) |

### FIX 3 units (DEFERRED or ship LAST — completeness goal, spends paid quota)

**Scoping note (revised per /tp critique):** The 497 orphans don't block the forward-sync goal (F2). F3's real value is the checkpoint-before-import contract — the decision tree's Sources 1-2 are already-failed matchers (~0 yield by construction). The operator may rationally defer F3 entirely from this wave and ship F1-minimal + F2 only. If F3 ships, its sole purpose is the checkpointed, quota-capped search.list path. The 257 lost results are confirmed unrecoverable (no checkpoint files exist on disk).

#### Unit F3-1 — Implement `resolve_orphans.py`

| Field | Value |
|-------|-------|
| Title | `feat(nlm-to-wiki): add resolve_orphans.py with miserly decision tree` |
| Files affected | `P:/.agents/skills/nlm-to-wiki/scripts/resolve_orphans.py` (new); `tests/test_resolve_orphans.py` (new) |
| Dependencies | F2-1 (title_bridge reuse) |
| Description | Decision tree (analysis_status → clusters.json → Takeout → search.list). Checkpoint before any import. Quota cap. Multi-key rotation. |
| Acceptance | (a) All 6 tests pass; (b) checkpoint file written before any import; (c) quota cap enforced; (d) recover mode skips search.list |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F3-2 — Add `--export-orphans` and `--from-checkpoint` flags to `import_nlm_transcripts.py`

| Field | Value |
|-------|-------|
| Title | `feat(yt-is): add --export-orphans and --from-checkpoint flags` |
| Files affected | `import_nlm_transcripts.py` (modified) |
| Dependencies | F3-1 |
| Description | `--export-orphans` writes the orphan index file. `--from-checkpoint` reads it. Both are additive; default behavior unchanged. |
| Acceptance | (a) Orphan export works (count matches unmatched transcripts); (b) checkpoint import works without re-running search; (c) default `--dry-run` behavior unchanged |
| Disposition | **COMMIT_THIS_SESSION** |

#### Unit F3-3 — Recover the 257 lost results (operator-gated)

| Field | Value |
|-------|-------|
| Title | Recover: 257 already-resolved orphans |
| Files affected | None (verification only — search the filesystem for prior checkpoint files) |
| Dependencies | F3-1, F3-2 |
| Description | First action: `Get-ChildItem P:/.data/wiki/sources/transcripts/_checkpoints -ErrorAction SilentlyContinue`. If any `.json` files exist, attempt to recover. If the 257-result bug wrote them to a different path, search `/tmp/`, `P:/tmp/`, etc. |
| Acceptance | (a) Prior checkpoints located; (b) video_ids recovered; (c) import_nlm_transcripts.py applies them; (d) zero new search.list calls fired for these 257 |
| Disposition | **HANDOFF** (operator investigation; depends on filesystem state) |

#### Unit F3-4 — Resolve remaining orphans

| Field | Value |
|-------|-------|
| Title | Resolve: remaining orphans (≤240 search.list calls) |
| Files affected | None (operator-gated run) |
| Dependencies | F3-3 |
| Description | Operator runs `resolve_orphans.py` (revised per F-21: `--checkpoint` flag was REMOVED in the F-03 fix; one title per call). Recommend: (1) run with `--dry-run` first to preview the checkpoint file; (2) inspect checkpoint for correctness; (3) run without `--dry-run` to commit. Resolves as many free-source orphans as possible; uses search.list for true unknowns. Quota cap prevents runaway. |
| Acceptance | (a) ≥95% of remaining orphans resolved; (b) quota spent <240 calls; (c) checkpoint file written; (d) operator reviewed checkpoint before import |
| Disposition | **HANDOFF** (operator-driven; runs over multiple days) |

---

## 14. Open Questions

| # | Question | Class | Resolution path |
|---|----------|-------|-----------------|
| Q1 | Are FIX 1 offload patterns high-precision enough on real transcripts? | [INFERENCE] | Shadow mode measurement (F1-6 gate) |
| Q2 | Is FIX 1 FP rate <5% achievable? | [UNKNOWN] | Shadow mode measurement |
| Q3 | Will FIX 2 bridge build take <30s on 60K analysis_status rows? | [INFERENCE] | F2-4 end-to-end timing |
| Q4 | Will FIX 2 forward-sync achieve ≥70% YouTube-source bridge-match rate (3,918/5,070)? | [INFERENCE] | F2-4 verification (revised per F-16: denominator is YouTube sources in notebook, not total cached video_ids) |
| Q5 | Does the analysis_status table include the 497 orphan titles (or are they truly from History)? | [INFERENCE] | F3-1 dry-run; if 0 hits, confirms Takeout-only |
| Q6 | Are the 257 lost results recoverable from any checkpoint file? | [UNKNOWN] | F3-3 filesystem search |
| Q7 | Does `_hook_base.py` exist on the host (from prior handoff Unit 1)? | [UNKNOWN] | F1-1 verification (skip if present) |
| Q8 | ~~What is the correct cache_key format for forward-sync video_id lookup?~~ | **RESOLVED by F-02** — the new `get_cached_transcript_by_video_id(video_id)` API (csf/cache.py: §5.3 contract) bypasses cache_key entirely (SELECT by `video_id`, not by the composite hash). cache_key format is irrelevant to forward-sync; the new function does not call `_make_cache_key` (cache.py:205). | N/A — resolved |
| Q9 | Does the operator have a YouTube Takeout History export available? | [UNKNOWN] | F3-1 dry-run (skip Source 3 if absent) |
| Q10 | Will `qmd` (or its replacement) still be installed when FIX 1 ships? | [UNKNOWN] | Receipt patterns include `read_file` + `grep`/`rg` paths; qmd is optional |

---

## 15. Traceability Matrix

Each fix maps to its root cause, its verified facts, and its acceptance criteria.

| Fix | Root cause | Verified facts | Acceptance criteria | Disposition |
|-----|-----------|----------------|---------------------|-------------|
| F1-1 | RC-1 | Prior handoff Unit 1 | `_hook_base.py` exists OR extracted | COMMIT_THIS_SESSION |
| F1-2 | RC-1 | Stop hook API, transcript schema, offload patterns | 25 tests pass; shadow mode logs only | COMMIT_THIS_SESSION |
| F1-3 | RC-1 | Hook discovery mechanism | Active surface lists wiki-query-gate | COMMIT_THIS_SESSION |
| F1-4 | RC-1 | Metrics table §9.1 | 4 metrics computed; report regenerated | COMMIT_THIS_SESSION |
| F1-5 | RC-1 | AGENTS.md enforcement section | 3-line entry present | COMMIT_THIS_SESSION |
| F1-6 | RC-1 | Prior handoff Unit 6 criteria | ≥100 events; FP <5%; env var set | HANDOFF |
| F2-1 | RC-2 | `import_nlm_transcripts.py` bridge logic | Module importable; behavior unchanged | COMMIT_THIS_SESSION |
| F2-2 | RC-2 | `register_external_transcript_provider` API; cache schema | 8 tests pass; cache hit returns transcript | COMMIT_THIS_SESSION |
| F2-3 | RC-2 | `export_transcripts.py` pipeline position | Forward-sync enabled; cache miss falls through | COMMIT_THIS_SESSION |
| F2-4 | RC-2 | 3,918/5,070 expected bridge-match rate | ≥70% from_cache; .md format correct | VERIFICATION |
| F3-1 | RC-3 | Miserly decision tree; checkpoint pattern | 6 tests pass; checkpoint before import; quota cap enforced | COMMIT_THIS_SESSION |
| F3-2 | RC-3 | `import_nlm_transcripts.py` flag pattern | --export-orphans + --from-checkpoint work | COMMIT_THIS_SESSION |
| F3-3 | RC-3 | 257-result loss incident | Prior checkpoints located; recovered without new search | HANDOFF |
| F3-4 | RC-3 | 497 orphans - 257 recovered | ≥95% resolved; <240 calls used | HANDOFF |

---

## 16. File Change Inventory

### 16.1 New files

| Path | Purpose | Fix | LOC estimate |
|------|---------|-----|--------------|
| `~/.grok/hooks/scripts/wiki_query_gate.py` | Stop + SubagentStop hook script | F1 | ~250 LOC (skeleton: ~180; imports: ~70) |
| `~/.grok/hooks/scripts/tests/test_wiki_query_gate.py` | Unit tests (25 tests) | F1 | ~400 LOC (mirrors prior handoff test plan) |
| `~/.grok/hooks/wiki-query-gate.json` | Hook registration (both events) | F1 | ~15 LOC JSON |
| `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py` | Shadow-mode metrics | F1 | ~120 LOC |
| `~/.grok/hooks/scripts/_hook_base.py` | Shared hook base library (if absent) | F1 | ~200 LOC (only if extraction needed) |
| `P:/packages/yt-is/scripts/title_bridge.py` | Shared title→video_id bridge (CANONICAL LOCATION per F-06) | F2 | ~120 LOC (5 functions: normalize_title, build_bridge_from_clusters, build_bridge_from_analysis, merge_bridges, match_title) |
| `P:/.agents/skills/nlm-to-wiki/scripts/yt_is_forward_sync.py` | Forward-sync provider | F2 | ~70 LOC (single function + sys.path setup) |
| `P:/.agents/skills/nlm-to-wiki/scripts/resolve_orphans.py` | Orphan resolver | F3 | ~200 LOC (skeleton: ~150; QuotaExceededError class + load_takeout_index: ~50) |
| `P:/.agents/skills/nlm-to-wiki/scripts/tests/test_yt_is_forward_sync.py` | Forward-sync tests (8 tests) | F2 | ~150 LOC |
| `P:/.agents/skills/nlm-to-wiki/scripts/tests/test_resolve_orphans.py` | Orphan resolver tests (6 tests) | F3 | ~120 LOC |
| `P:/.data/wiki/sources/transcripts/_checkpoints/` | Checkpoint directory | F3 | (directory only) |
| `P:/.data/wiki/sources/transcripts/_orphans.json` | Orphan index (generated by --export-orphans) | F3 | ~50KB JSON for 497 orphans |

### 16.2 Modified files

| Path | Change | Fix | LOC delta |
|------|--------|-----|-----------|
| `~/.grok/hooks/scripts/quality_gate.py` | Refactor to use `_hook_base` (only if extraction happens in F1-1) | F1 | ~-50 LOC (delete inline copies; replaced by imports) |
| `P:/packages/yt-is/csf/cache.py` | **Add `get_cached_transcript_by_video_id(video_id)`** — SELECT by `video_id=? LIMIT 1`, mirrors `has_cached_transcript` semantics | F2 (per F-02 fix) | **+25 LOC** (new function + docstring; reuses `_connect_shared_db`, `TranscriptCache`) |
| `P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py` | Add forward-sync stage before `fetch_content`; emit `from_cache_count`; `try/except Exception` wrapper around `fetch_from_yt_is_cache` | F2 | +30 LOC (concrete edit shown in §4.4) |
| `P:/packages/yt-is/scripts/import_nlm_transcripts.py` | Import `title_bridge` from shared module (replace ~80 LOC of inline bridge code); add `--export-orphans` and `--from-checkpoint` flags | F2, F3 | -80 LOC (F2 dedup) + ~50 LOC (F3 flags) = net ~-30 LOC |
| `P:/AGENTS.md` | 3-line entry under enforcement mechanisms pointing to wiki-query-gate | F1 | +3 LOC |

### 16.3 Files NOT modified (preserved as-is for safety net)

| Path | Why preserved |
|------|---------------|
| `P:/.agents/skills/nlm-to-wiki/scripts/sync.py` | Orchestrator unchanged; F2 hook is internal to export_transcripts.py |
| `P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py`, `synthesize_subtopics.py`, `reconcile.py`, `write_pages.py` | Downstream of export; unchanged |
| `P:/packages/yt-is/csf/cache.py` | **MODIFIED — see §16.2** (added `get_cached_transcript_by_video_id` per F-02) |
| `P:/packages/yt-is/csf/transcript.py` | `register_external_transcript_provider` exists but is for the inverse direction; not used here |

---

## 17. Coupling & Code-Smell Inventory

### 17.1 FIX 1 — `wiki_query_gate.py` (NEW)

| Smell class | Count | Threshold | Status | Action |
|-------------|-------|-----------|--------|--------|
| DRY violations | 7 patterns duplicated with `quality_gate.py` (envelope parse, transcript iter, mode dispatch, fail-open, negation window, evidence writer, json_or_default) | ≥3 = positive ROI | **POSITIVE ROI** | Extract `_hook_base.py` first (F1-1) before writing hook |
| Parameter count | `compute_decision(offload, receipts, mode)` — 3 params | >7 = coupling | OK | None needed |
| Touch-point count | New file; touches 0 existing files | >3 = structural coupling | OK | None needed |
| Mixed concerns | Offload detection + receipt detection + decision + I/O — 4 concerns in 1 module | (flag) | Acceptable for a single-purpose hook | None needed; mirrors quality_gate.py precedent |

### 17.2 FIX 2 — `yt_is_forward_sync.py` (NEW) + `export_transcripts.py` (MODIFIED)

| Smell class | Count | Threshold | Status | Action |
|-------------|-------|-----------|--------|--------|
| DRY violations | Title→video_id bridge logic duplicated in `import_nlm_transcripts.py` (4 functions: `normalize_title`, `build_bridge_from_clusters`, `build_bridge_from_analysis`, `merge_bridges`, `match_title`) | ≥3 = positive ROI | **POSITIVE ROI** | Extract `title_bridge.py` (F2-1) before writing forward-sync |
| Parameter count | `fetch_from_yt_is_cache(source)` — 1 param | >7 = coupling | OK | None needed |
| Touch-point count | Modifies `export_transcripts.py` inner loop; new provider file | >3 = structural coupling | OK (1 modification) | None needed |
| Mixed concerns | Bridge build + cache read + .md emission — 3 concerns; bridge build is one-time per run | (flag) | Acceptable; provider is single-purpose | None needed |

### 17.3 FIX 3 — `resolve_orphans.py` (NEW) + `import_nlm_transcripts.py` (MODIFIED)

| Smell class | Count | Threshold | Status | Action |
|-------------|-------|-----------|--------|--------|
| DRY violations | Bridge logic (re-uses F2-1 `title_bridge.py`) | ≥3 = positive ROI | OK | Reuse F2-1 module |
| Parameter count | `resolve_one(title, bridge, takeout_index)` — 3 params | >7 = coupling | OK | None needed |
| Touch-point count | Modifies `import_nlm_transcripts.py` for two new flags; new script | >3 = structural coupling | OK | None needed |
| Mixed concerns | Decision tree + checkpoint write + API call + quota tracking — 4 concerns | (flag) | Acceptable; script is single-purpose | None needed |

### 17.4 Cross-fix coupling

| Coupling | Type | Action |
|----------|------|--------|
| F2.1 `title_bridge.py` ↔ F3.1 `resolve_orphans.py` | F3 imports F2 module | Already factored; F2-1 lands first |
| F1.1 `_hook_base.py` ↔ F1.2 `wiki_query_gate.py` | F1.2 imports F1.1 | Already factored; F1-1 lands first |
| F2.2 `yt_is_forward_sync.py` ↔ F2.3 `export_transcripts.py` | F2.3 calls F2.2 | Sequential; F2.2 lands first |
| F3.2 `--export-orphans` ↔ F3.1 `resolve_orphans.py` | F3.1 reads file written by F3.2 | Sequential; either order works |

### 17.5 Aggregation across all three fixes

| Metric | Value |
|--------|-------|
| Total new files | 12 |
| Total modified files | 4 |
| Total new test cases | 25 + 8 + 6 = 39 |
| Total new env vars | 4 (`GROK_WIKI_QUERY_GATE_MODE`, `GROK_WIKI_QUERY_GATE_NEGATION_WINDOW_CHARS`, `YOUTUBE_API_KEYS`, `ORPHAN_QUOTA_CAP`) |
| Total new evidence/log files | 2 (`.evidence/wiki-query-gate.jsonl`, `_checkpoints/orphan-search-*.json`) |
| Total coupling ratio | F2-F3 share `title_bridge` (1:2 reuse); F1 self-contained |

### 17.6 What this design avoids

- **No new wiki pages.** The wiki already documents the patterns (error-handling-loops-skip-wiki-query, youtube-api-search-list-only-endpoint-for-title-to-video-id, notebooklm-cli-operational-gotchas). New wiki pages would over-document what already exists (AGENTS.md paper: thin pages hurt performance).
- **No new MCP servers.** All fixes use existing primitives (Stop hook, file system, SQLite, urllib).
- **No new dispatch chains.** FIX 1 mirrors `quality_gate.py`; FIX 2 hooks into existing export stage; FIX 3 is a standalone script.
- **No replacement of prior paths.** Every fix preserves the prior path as fail-open/fail-through safety net.

---

## 18. Recommendations summary

- **FIX 1 (Stop hook):** Ship in shadow mode immediately; operator-gated to authoritative after ≥100 events + FP <5%. Reuses the complete prior handoff design (`P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md`) — implementation cost is ~1 hour for F1-2 through F1-5. Confidence: HIGH (prior design reviewed + revised).
- **FIX 2 (forward sync):** Ship immediately, no gating needed. Net positive (caches reduce NLM calls). Implementation cost: ~1 hour for F2-1 through F2-3. Confidence: HIGH (title bridge already proven via `import_nlm_transcripts.py`).
- **FIX 3 (orphan resolution):** Ship the script immediately; operator runs after Takeout History check. Implementation cost: ~1 hour for F3-1, F3-2. F3-3 and F3-4 are operator-gated (filesystem search + multi-day quota spend). Confidence: HIGH for the script; MEDIUM for the 257-result recovery (depends on filesystem state).

**Net implementation cost:** ~3 hours of engineering for F1-2 through F3-2. ~30 minutes for F1-1 verification + skip-if-present. Operator-gated follow-up for F1-6, F3-3, F3-4.

**Net operational cost:** ≥70% reduction in NLM API calls for notebooks with high bridge-match rate (FIX 2); closure of the nlm-auth offload loop (FIX 1); recovery of the 257 lost results without burning quota (FIX 3 — IF checkpoints exist per F-13 conditional framing).

---

## 19. Coupling summary (closing)

This design's central architectural choice is **knowledge-as-step**: each fix operationalizes a piece of existing workspace knowledge (the wiki concept, the yt-is cache, the Takeout History export) as a mandatory step in the agent's workflow, rather than advisory text. The three fixes share one structural pattern (retrieval-as-step, not retrieval-as-best-effort) but operate on different surfaces (Stop hook / export stage / orphan resolver). The coupling ratio is 1:2 (F1 self-contained; F2-F3 share `title_bridge`). All fixes preserve their prior paths as fail-open/fail-through safety nets.

The design's central risk is FIX 1's FP rate being unacceptable on real transcripts. Mitigation: shadow-mode rollout with operator-gated activation. The other two fixes have no FP concern (forward-sync is net positive; orphan resolution has checkpointing).

The design's central opportunity is that all three fixes share an `auto-recovery` loop: the operator runs the system, observes the wiki-query gate's evidence log, the forward-sync's `from_cache_count`, and the orphan resolver's checkpoint. The combined observability surfaces reveal whether the three retrieval gaps are genuinely closed or whether additional gaps remain.
---
thread_id: yt-is-nlm-to-wiki-fixes-20260730
parent_handoff_path: P:/docs/handoffs/yt-is-nlm-to-wiki-integration-20260730/HANDOFF.md
current_session_id: 019fb49b-e6b2-7bf1-a14b-b706c7c91b66
current_terminal_id: grok-build-terminal
produced_at: 2026-07-31T01:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 7aada874de315b77dcec5f5e0301022ccffa38d7
---

# Fix 3 root causes from the yt-is/nlm-to-wiki integration session

## Objective (one sentence)

Implement three fixes identified by /tp critique, /www research, and /design: (1) a wiki-query Stop hook that forces agents to consult recovery docs during error handling, (2) a forward-sync provider so nlm-to-wiki reads from yt-is cache before hitting NotebookLM, and (3) a miserly orphan resolver with checkpoint-before-import.

## Status

OPEN — design complete (2 review rounds, 25 findings all addressed). All three fixes are buildable. No implementation started.

## Design document

**Full design (1,514 lines, 2 review rounds):** `P:/docs/design/yt-is-nlm-to-wiki-fixes-20260730.md`
**Review findings (25 total, all addressed):** `P:/docs/design/yt-is-nlm-to-wiki-fixes-review-20260730.md`

## Read-first list

1. `P:/docs/design/yt-is-nlm-to-wiki-fixes-20260730.md` — the authoritative design (sections §4-§5 are implementation-ready)
2. `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` — the structural gap F1 closes
3. `P:/.data/wiki/concepts/youtube-api-search-list-only-endpoint-for-title-to-video-id.md` — the miserly decision tree F3 follows
4. `P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md` — auth recovery recipes (Gotcha 1 + Gotcha 4)
5. `P:/docs/handoffs/wiki-query-stop-hook-20260727/HANDOFF.md` — prior Stop hook design (F1 reuses this)

## The three fixes (implementation-ready)

### F1: Wiki-query Stop hook (structural fix for error-handling loops)

**Problem:** Agents skip wiki queries during error handling (3 documented recurrences of the same nlm-auth failure).

**Mechanism:** A Stop hook that scans the session transcript for offload language ("operator must do X") WITHOUT a corresponding wiki-query receipt. Shadow-mode first; operator-gated activation after ≥100 events + FP <5%.

**Key files to create:**
- `~/.grok/hooks/scripts/wiki_query_gate.py` — the hook (reuses prior design at `wiki-query-stop-hook-20260727/DESIGN.md`)

**Acceptance criteria:**
- 25 unit tests pass (offload detection, wiki-receipt detection, false-positive cases)
- Shadow mode produces ≤5% false-positive rate over ≥100 Stop events
- Hook registered for both `Stop` AND `SubagentStop` events

**Feature flag:** `GROK_WIKI_QUERY_GATE_MODE` (advisory → receipt_authoritative)

**Disposition:** 11 units COMMIT_THIS_SESSION, 1 unit HANDOFF (activation gate)

### F2: Forward-sync provider (the productive fix)

**Problem:** nlm-to-wiki re-fetches YouTube transcripts from NotebookLM even when yt-is already has them cached (~40% waste).

**Mechanism:** Before `nlm source content`, check yt-is `transcript_cache` for a matching video_id via title bridge. If found, read from cache. If not, fall through to NotebookLM.

**Key files to create/modify:**
- `P:/packages/yt-is/scripts/title_bridge.py` — NEW: shared title→video_id bridge (extracted from import_nlm_transcripts.py)
- `P:/packages/yt-is/csf/cache.py` — MODIFIED: add `get_cached_transcript_by_video_id(video_id)` function (+25 LOC)
- `P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py` — MODIFIED: add cache-check hook before `nlm source content` call

**Acceptance criteria:**
- `get_cached_transcript_by_video_id` returns `TranscriptCache | None` (SELECT by video_id, bypasses cache_key hash)
- ≥70% of YouTube sources in a test notebook match the title bridge and come from cache (not NLM)
- Fail-through to NLM on any error (never blocks the pipeline)
- All existing nlm-to-wiki tests still pass

**Disposition:** All units COMMIT_THIS_SESSION

### F3: Miserly orphan resolver

**Problem:** 497 YouTube transcripts with real titles, no match in any data source. Need quota-miserly resolution + checkpoint-before-import.

**Mechanism:** Decision tree (free-first): analysis_status → clusters.json → Takeout History → search.list (last resort, single-title calls, multi-key rotation). Checkpoint to JSON BEFORE any import step.

**Key files to create:**
- `P:/packages/yt-is/scripts/resolve_orphans.py` — NEW: the resolver

**Acceptance criteria:**
- search.list budget capped at ≤240 calls total across all keys
- Checkpoint file written BEFORE import phase (decouples the bug that lost 257 results)
- Multi-key rotation: `QuotaExceededError` triggers key rotation, not silent failure
- 6 unit tests pass (checkpoint, rotation, title re-match, dry-run)

**Disposition:** COMMIT_THIS_SESSION (script) + HANDOFF (operator-gated multi-day pacing)

## Key decisions

- **KD-9a:** Single-title search.list calls + `normalize_title` re-match (not batched — batched returned wrong videos for generic titles)
- **Shared `title_bridge.py`:** single canonical location at `P:/packages/yt-is/scripts/title_bridge.py`, both yt-is and nlm-to-wiki import from it
- **Checkpoint-before-import:** search and import are separate phases with a JSON checkpoint between them

## Operator decisions needed

1. **F1 activation:** set `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative` after shadow-mode validates
2. **F3 checkpoint recovery:** search filesystem for prior checkpoint files from the lost 257-result run
3. **F3 API key verification:** test each API key before relying on the 240-call budget (3/4 were blocked on search.list quota last checked)

## Last user message (verbatim)

> "copy and commit it. should it be in a handoff file instead?"

## Suggested next invocation

```
/go Implement F2 (forward-sync provider) from P:/docs/handoffs/yt-is-nlm-to-wiki-fixes-20260730/HANDOFF.md.
This is the fix that makes the system productive: ~40% NLM call reduction.
Start with: (1) extract title_bridge.py, (2) add get_cached_transcript_by_video_id to csf/cache.py,
(3) add cache-check hook in export_transcripts.py.
```

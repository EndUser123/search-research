---
title: "pick_model.py spawn_notes freshness check — investigation + fix"
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
source_session: 019fb933-040b-7720-a257-e364f5df726f
produced_at: 2026-08-02T05:00:00Z
status: OPEN — not started
priority: MEDIUM
tags: [pick-model, stale-data, spawn-notes, freshness-check, model-routing, false-positive]
accurate_as_of_head: needs_verification
---

# Handoff: pick_model.py spawn_notes freshness check — investigation + fix

## Objective

Add a freshness-verification step to `pick_model.py`'s spawn_notes cache so that stale "spawn OK" entries (models that have since broken) don't get returned by the dispatcher. Same root-cause class as the serde-broken false-positive list (cleared 2026-08-01): inherited labels with no verification receipts.

## Status

OPEN — bug pattern identified, fix not yet implemented.

## Producing context

- Date: 2026-08-02
- Session: `019fb933-040b-7720-a257-e364f5df726f`
- Host: grok (Grok Build)

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/pick-model-stale-spawn-notes-failure-pattern.md` — wiki concept with full RCA
2. `P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md` — related false-positive class
3. `pick_model.py` — locate and read the spawn_notes handling
4. `~/.grok/skills/coding-model-pool-tier-1-tier-2/` or equivalent — find the pool consumer

## Verified facts

- [FACT] pick_model.py returned `nim-openai-gpt-oss-20b` as "spawn OK" during session 019fb933 dispatch (source: pre-packed evidence from sweep)
- [FACT] `nim-openai-gpt-oss-20b` PASSED direct spawn (41s) in the same session (source: [[serde-broken-false-positive-sweep-20260801]] § Testing methodology table)
- [FACT] The serde_broken list was cleared on 2026-08-01 after testing proved all 10 entries were false positives (source: [[serde-broken-false-positive-sweep-20260801]] § Fixes applied)
- [FACT] A wiki concept was created documenting the staleness pattern (source: P:/.data/wiki/concepts/pick-model-stale-spawn-notes-failure-pattern.md)

## Current state

- Stale-positive class identified
- Wiki concept written
- Tool-fallbacks.md has new entries calling out nim-openai-gpt-oss-20b staleness
- pick_model.py not patched

## Task packets

### T1: Locate pick_model.py and read spawn_notes handling

- **id:** PM-01
- **goal:** Find pick_model.py and identify the spawn_notes caching/dispatch path
- **in scope:** `pick_model.py` source file (search `~/.grok/`, `P:/.agents/`, `P:/packages/`)
- **out of scope:** Patching (T2)
- **acceptance:** File located, spawn_notes read/write paths identified, current logic quoted in handoff revision
- **falsifier:** pick_model.py doesn't exist (then check the model-pool consumer scripts)
- **verification level required:** STATIC_INSPECTION
- **estimate:** 15 minutes

### T2: Add TTL or verification probe to spawn_notes

- **id:** PM-02
- **goal:** Make spawn_notes either expire (TTL) or re-verify before returning
- **in scope:** spawn_notes caching logic in pick_model.py
- **out of scope:** Other pick_model.py functionality
- **acceptance:** Spawn notes older than the TTL are not returned as "spawn OK" without re-verification; OR a 1-token no-tool probe is dispatched before returning the cached note
- **falsifier:** Same stale-positive failure mode observed after patch
- **verification level required:** LIVE_BEHAVIOR (run pick_model.py with stale entries, confirm it probes or rejects)
- **proposed approach:** Add a `last_verified_at` field to spawn_notes; entries older than 24h without successful re-spawn are marked `[STALE]` and not returned as "spawn OK" by default.

### T3: Re-test nim-openai-gpt-oss-20b dispatch with fixed pick_model.py

- **id:** PM-03
- **goal:** Confirm the fix prevents the same false-positive class
- **in scope:** Re-run pick_model.py dispatch with the same fleet state as session 019fb933
- **out of scope:** Other model-routing improvements
- **acceptance:** pick_model.py either re-verifies nim-openai-gpt-oss-20b before returning, or returns a `[STALE]` warning
- **falsifier:** Stale-positive failure recurs after patch
- **verification level required:** LIVE_BEHAVIOR

## Open decisions

### OD-01: TTL value

- **Question:** What TTL should spawn_notes have before requiring re-verification?
- **Options:** (1) 1 hour [aggressive freshness, more re-verification overhead] (2) 24 hours [matches serde_broken sweep cadence] (3) 7 days [matches weekly fleet-models.json refresh]
- **Selection criterion:** freshness vs verification cost
- **Currently leads:** Option 2 (24 hours) — matches existing weekly rhythm

### OD-02: Verification probe shape

- **Question:** When stale notes need re-verification, what probe should run?
- **Options:** (1) 1-token no-tool spawn test (~5-15s) (2) Direct API call (faster, bypasses spawn path) (3) Read-only filesystem check (cheapest, no model call)
- **Selection criterion:** accuracy vs latency vs cost
- **Currently leads:** Option 1 (1-token no-tool spawn) — same access path pick_model.py will use, so probe is realistic

## Hard constraints

- Do NOT modify fleet-models.json spawn_broken list directly (serde-broken sweep cleared it; manual edits would defeat the sweep's work)
- The freshness check must be cheap (<30s) or it will slow close-check dispatch
- The patch must not break the model-pool consumer scripts that depend on pick_model.py

## Cross-reference couplings

- `P:/.data/wiki/concepts/pick-model-stale-spawn-notes-failure-pattern.md` — full RCA + receipts
- `P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md` — same false-positive class, different surface
- `P:/.data/wiki/concepts/tool-fallbacks.md` § "Session-attested new failures" — newly added entries
- `P:/.data/wiki/concepts/replacement-before-investigation-pattern.md` — verification receipts before claiming "model X works"

## Resumption protocol

1. Read this handoff + the wiki concept (read-first list)
2. Run T1 (locate pick_model.py + read spawn_notes handling)
3. Implement T2 (add TTL or verification probe)
4. Run T3 (re-test dispatch)
5. Commit with message: `fix(pick-model): add spawn_notes freshness verification`
6. Update the wiki concept with the patch SHA + add `[FIXED 2026-08-0X]` marker

## Suggested next invocation

```
/go PM-01 -- locate pick_model.py and read spawn_notes handling
```

## Last user message (verbatim)

> "Run the /capture skill. Read ~/.grok/skills/capture/SKILL.md for the workflow format, then execute it using the pre-packed evidence below."

## Epistemic labels per claim

- "pick_model.py returned nim-openai-gpt-oss-20b as spawn OK" — `[FACT]` (source: pre-packed evidence)
- "pick_model.py has stale spawn_notes" — `[INFERENCE]` (no code read yet, pattern inferred from contradiction with sweep)
- "TTL of 24 hours" — `[RECOMMENDATION]` (matches existing weekly rhythm; not yet validated)
- "1-token no-tool spawn probe" — `[RECOMMENDATION]` (matches realistic access path; not yet validated)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:00 | 019fb933... | created |
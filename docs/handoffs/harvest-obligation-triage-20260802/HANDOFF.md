---
thread_id: harvest-obligation-triage-019fa8f8
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-02T21:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: f17b724e94333b998470cd4ab888c63ac2e370b9
---

# Handoff: Harvest obligation triage — session 019fa8f8

## Objective

Triage the 27 RECOVER harvest obligations and 109 harvestable handoffs flagged by the session sweep. Determine which obligations are still active, which are stale, and which can be closed.

## Status

OPEN — 27 RECOVER obligations exceed the 5 OPEN threshold (FAIL). 109 harvestable handoffs need triage.

## Producing context

- Session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (started 2026-07-28T07:44:45)
- Harvest events: all 7/29 timestamps; no harvest activity today (last session events from 2026-07-29 18:04)
- 3 triaged files updated 2026-08-01 (aar.json, analyze_session_patterns.json, next-action-precompact-hook.json)
- Top chronic item: PostToolUse auto-verify — 10 recurrences, exposure still open
- Other chronic items: Code-output passthrough (6), Rules authored and skipped under generative load (5), Delegation waste (4), DONE-trigger fires on artifact creation not integration (4), Research applicability checking (3)
- nlm-to-wiki queue: 26 notebooks pending, workers not restarted
- Verdict-integrity: unsupported reviewer claims — 5 value/hr

## Read-first list

1. `P:/.data/harvest/events/` — harvest event files (6 files, LastWriteTime 8/2/2026 3:00-3:01 PM)
2. `P:/.data/wiki/concepts/` — wiki concepts for harvest patterns
3. `P:/docs/handoffs/postsession-20260801/HANDOFF.md` — post-session continuation handoff

## Verified facts

- [FACT] Harvest shows 27 RECOVER obligations > 5 OPEN threshold (source: sweep evidence, harvest FAIL)
- [FACT] 109 harvestable handoffs flagged by scan-handoffs (source: sweep evidence, harvest FAIL)
- [FACT] No harvest activity today (last events from 2026-07-29 18:04) (source: sweep evidence, harvest WARN)
- [FACT] 3 triaged files updated 2026-08-01 (source: sweep evidence, harvest WARN)
- [FACT] PostToolUse auto-verify is the top chronic item (10 recurrences, exposure still open) (source: sweep evidence, harvest FAIL)
- [FACT] nlm-to-wiki queue has 26 notebooks pending, workers not restarted (source: sweep evidence, harvest FAIL)

## Task packets

### T1: Triage RECOVER obligations

- **id:** HARVEST-T1
- **goal:** Review all 27 RECOVER obligations and classify each as active, stale, or closed
- **in scope:** harvest obligations from P:/.data/harvest/
- **out of scope:** implementing fixes for the obligations
- **files / anchors:** `harvest show --top 27` output
- **acceptance:** each obligation classified; stale ones marked for closure; active ones have a next step
- **falsifier:** if obligations are misclassified (e.g., active ones marked stale)
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 30 minutes

### T2: Triage harvestable handoffs

- **id:** HARVEST-T2
- **goal:** Review the 109 harvestable handoffs and identify which are still actionable vs. stale
- **in scope:** P:/docs/handoffs/ directory
- **out of scope:** implementing fixes
- **files / anchors:** `python ~/.grok/skills/handoff/__lib/list_handoffs.py` output
- **acceptance:** actionable handoffs are identified with next steps; stale handoffs are flagged for closure
- **falsifier:** if actionable handoffs are incorrectly flagged as stale
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 1 hour

### T3: Restart nlm-to-wiki workers

- **id:** HARVEST-T3
- **goal:** Restart the nlm-to-wiki workers that have been stalled with 26 notebooks pending
- **in scope:** nlm-to-wiki worker processes
- **out of scope:** notebook processing logic
- **files / anchors:** nlm-to-wiki worker scripts
- **acceptance:** workers are running and processing the 26 pending notebooks
- **falsifier:** if workers fail to start or notebooks remain unprocessed after restart
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 15 minutes

## Open decisions

1. **Obligation triage order:** Should T1 be done before T2, or in parallel? The RECOVER obligations are more urgent (exceeding the 5 OPEN threshold).
2. **Stale handoff cleanup:** Should stale handoffs from sessions 7/22-8/2 be bulk-closed or reviewed individually?

## Hard constraints

- AGENTS.md destructive-git ban: no force-push, no reset --hard, no rebase -i, no clean -fd
- AGENTS.md auto-commit: stage only files you changed; surgical git add

## Cross-reference couplings

- `P:/docs/handoffs/postsession-20260801/HANDOFF.md` — post-session continuation
- `P:/docs/handoffs/close-check-blocked-019fa8f8-20260801/HANDOFF.md` — close-check findings (harvest WARN items)
- `P:/.data/harvest/events/` — harvest event files

## Resumption protocol

1. Run `harvest show --top 27` to get the full RECOVER obligation list
2. Classify each obligation as active, stale, or closed
3. Run `/handoff list` to identify stale handoffs for closure
4. Restart nlm-to-wiki workers
5. Re-run harvest to verify counts have decreased

## Suggested next invocation

```
/go HARVEST-T1 — triage RECOVER obligations
```

## Last user message (verbatim)

> "Run the /handoff skill."

## Epistemic labels per claim

- "27 RECOVER obligations > 5 OPEN threshold" — [FACT] (source: sweep evidence, harvest FAIL)
- "109 harvestable handoffs flagged" — [FACT] (source: sweep evidence, harvest FAIL)
- "No harvest activity today" — [FACT] (source: sweep evidence, harvest WARN)
- "PostToolUse auto-verify is top chronic item" — [FACT] (source: sweep evidence, harvest FAIL)
- "nlm-to-wiki queue has 26 pending notebooks" — [FACT] (source: sweep evidence, harvest FAIL)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T21:30 | 019fa8f8... | created |

---
thread_id: work-surface-greenfield-20260802
parent_handoff_path: docs/handoffs/session-review-skill-division-20260801/HANDOFF.md
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
parent_session: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 7c38e4c0-057f-43fc-b03d-1fe3048cea80
produced_at: 2026-08-02T16:30:00Z
last_updated_by: 019fb177-e5d5-7520-92f5-0158f87639c9
last_updated_at: 2026-08-02T16:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: b920822
---

# Handoff: Greenfield work surface design — `/work` unified skill

**Status:** OPEN — design complete, implementation not started
**Created:** 2026-08-02
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9
**Related:** `session-review-skill-division-20260801`, `tp-parallel-panel-dispatch-20260801`

## Objective

Replace 8 overlapping work-discovery skills (`/todo`, `/tp session`, `/recap-grok`, `/harvest`, `/capture`, `/friction`, `/close`, `/tasks`) with one unified `/work` skill using the ENTRYPOINT+CMD pattern (one entry, mode flags override). The organic system grew skill-by-skill as problems surfaced; the result is 15+ skills touching work discovery with overlapping outputs, no impact scoring, no commitment gating, no unified entry, and 176 open handoffs that nobody triages because the triage tool is one of the 15.

## Scope bounds

Work scope: the work-discovery surface (finding, prioritizing, evaluating, reconstructing work). NOT in scope: skills that produce artifacts (`/handoff`, `/wiki`), produce research (`/www`), are quality gates (`/review`, `/check`), or are execution tools (`/go`).

## Read-first list

1. `P:/.data/wiki/concepts/skill-graph.md` — current delegation graph (who calls what)
2. `C:/Users/brsth/.grok/skills/todo/SKILL.md` — current scan engine (6 steps)
3. `P:/docs/handoffs/session-review-skill-division-20260801/HANDOFF.md` — boundary decision (3-skill division, already implemented)
4. `C:/Users/brsth/.grok/skills/close/__lib/coverage_scan.py` — current handoff scanner (reads frontmatter, sorts by age)
5. `P:/.data/wiki/concepts/adhd-friendly-unified-todo-workspace-email-scanning.md` — prior art on unified todo design

## Verified facts

- [FACT] 15+ skills match "work discovery" patterns (grep of skill SKILL.md descriptions, 2026-08-02)
- [FACT] 176 open handoffs, 134 closed (coverage_scan.py output, 2026-08-02)
- [FACT] No impact scoring exists in handoff frontmatter (read schema in references/core-fields.md)
- [FACT] `/tp session` is designed to call `/todo` but doesn't actually do so in practice (operator typed 5 commands manually this session)
- [FACT] `/capture` and `/friction` overlap with `/tp session` transcript scan (skill description comparison)
- [FACT] `/close` is deprecated by `/close-check` (already in progress)
- [FACT] `/debrief` was already absorbed into `/aar` (deleted this session)
- [FACT] `/www` research (3 parallel subagents) confirmed: NOW/NEXT/LATER + impact/effort scoring + ENTRYPOINT+CMD pattern are best practices

## Current state

### What's designed
- `/work` unified skill with 4 modes: default (action list), discover, recap, evaluate
- Scan engine: 6 mechanical steps (coverage_scan + harvest + git + FINDINGS + WIKI markers + wiki grep)
- Impact/effort fields added to handoff frontmatter schema
- NOW/NEXT/LATER mechanical assignment: H/S + H/M = NOW, H/L + M/S = NEXT, rest = LATER
- 5-phase incremental migration path (~5h total)

### What's not started
- All 5 implementation phases

## Task packets

### Task 1: Add impact/effort fields to handoff frontmatter
- id: WS-FRONTMATTER
- goal: Add `impact`, `effort`, `cost_of_inaction` to handoff YAML frontmatter schema
- files: `C:/Users/brsth/.grok/skills/handoff/references/core-fields.md`, `P:/docs/handoffs/` (update frontmatter parser)
- acceptance: coverage_scan.py reads and displays impact/effort; NOW/NEXT/LATER assignment is mechanical
- verification: `python ~/.grok/skills/close/__lib/coverage_scan.py` shows impact column
- estimate: S (30 min)

### Task 2: Build `/work` scan engine
- id: WS-SCAN
- goal: Create `/work` skill with 6-step mechanical scanner producing NOW/NEXT/LATER output
- files: `C:/Users/brsth/.grok/skills/work/SKILL.md` (new), `C:/Users/brsth/.grok/skills/work/__lib/scan.py` (new)
- acceptance: `python ~/.grok/skills/work/__lib/scan.py` produces NOW/NEXT/LATER list in <5s
- verification: compare output to `/todo` coverage_scan — same handoffs surfaced, plus impact tier
- estimate: M (2h)

### Task 3: Fold `/capture` and `/friction` into `/work evaluate`
- id: WS-FOLD
- goal: Merge transcript scanning from `/capture` and `/friction` into `/work evaluate` mode
- files: mark `/capture` and `/friction` as deprecated; fold scan logic into `/work evaluate`
- acceptance: `/work evaluate` produces FRICTION + IMPROVEMENT findings that `/capture` and `/friction` would have produced
- verification: compare finding output to a `/capture` run on the same session
- estimate: M (1h)

### Task 4: Wire `/tp session` to delegate to `/work`
- id: WS-WIRE
- goal: `/tp session` calls `/work` for the action list, adds evaluation layer on top
- files: `C:/Users/brsth/.grok/skills/tp/SKILL.md` (session review protocol section)
- acceptance: `/tp session` produces unified view without operator manually running `/todo` first
- verification: run `/tp session` and verify the output includes `/work` scan results
- estimate: S (30 min)

### Task 5: `/recap-grok` becomes `/work recap`
- id: WS-RECAP
- goal: `/work recap` mode replaces `/recap-grok` as the reconstruction entry point
- files: mark `/recap-grok` as deprecated alias; add recap mode to `/work`
- acceptance: `/work recap` produces the same reconstruction output as `/recap-grok`
- verification: compare output structure to `/recap-grok` template
- estimate: S (30 min)

## Open decisions

### Decision 1: Should `/work` be a new skill or an evolution of `/todo`?
- Option A: New skill at `~/.grok/skills/work/` — `/todo` becomes alias
- Option B: Rename `/todo` to `/work` — fewer new paths, less migration
- Recommendation: A — new skill, `/todo` stays as alias for muscle memory. The skill content is substantially different (4 modes, scan engine, evaluation layer) — renaming `/todo` would bury its current single-purpose design under mode routing.

### Decision 2: Should `/notice` stay separate?
- Option A: Keep `/notice` separate — it fires mid-conversation at a different cadence than `/work` (which fires on invocation)
- Option B: Fold `/notice` into `/work` — one fewer skill
- Recommendation: A — `/notice` is ambient (fires automatically); `/work` is operator-invoked. Different trigger mechanisms mean different skills. The ADHD research confirms ambient retrieval is the load-bearing layer; merging it with operator-invoked `/work` would break the ambient property.

## Hard constraints

- Do NOT create a JSON work store — grep on .md handoffs works; frontmatter fields are sufficient (operator corrected this design during session)
- Do NOT remove skills without marking them deprecated first — compatibility aliases for muscle memory
- Each migration phase must be independently shippable — no big-bang cutover
- `/work` scan must complete in <5s — if it's slower than manual `/todo` invocation, adoption fails

## Cross-reference couplings

- `session-review-skill-division-20260801` → boundary decisions (3-skill division) that `/work` supersedes by consolidating further
- `tp-parallel-panel-dispatch-20260801` → the tp_dispatch.py work that motivates better work discovery
- `premature-recommendation-pattern-20260801` → the AGENTS.md rule that should apply when evaluating whether to merge vs preserve skills

## Explicit non-goals

- Do NOT merge skills that produce artifacts (`/handoff`, `/wiki`) — different output type
- Do NOT merge skills that produce research (`/www`) — different output type
- Do NOT merge quality gates (`/review`, `/check`) — different lifecycle stage
- Do NOT build a discovery router for code/knowledge/patterns — separate enhancement, track separately
- Do NOT add ambient session-start hooks in this handoff — separate enhancement

## Resumption protocol

1. Read `P:/.data/wiki/concepts/skill-graph.md` for the delegation map
2. Read this handoff's Task 1-5 packets
3. Start with Task 1 (frontmatter fields) — it's the foundation everything else reads
4. Validate each phase independently before proceeding

## Suggested next invocation

```
/go execute the work-surface-greenfield-design handoff at P:/docs/handoffs/work-surface-greenfield-design-20260802/HANDOFF.md
```

## Last user message (verbatim)

> greenfield isn't a fantasy.  we have an organic system that developed in pieces and doens't align with best practices.

## Epistemic labels per claim

- [FACT] skill counts, handoff counts, overlap assessments — verified by grep/coverage_scan this session
- [FACT] research findings — sourced from 3 parallel DDG research subagents + HN Algolia + Reddit
- [INFERENCE] the ENTRYPOINT+CMD pattern is the right model — supported by research but not yet validated on our workspace
- [INFERENCE] 8 skills can be consolidated to 1 — based on overlap analysis; actual consolidation may reveal orthogonal scope that should stay separate

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T16:30 | 019fb177... | created |

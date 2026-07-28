---
thread_id: e7f2a1b3-5c8d-4e6f-9a0b-1c2d3e4f5a6b
parent_handoff_path: none
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T18:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d85f36c
---

# Implement routine skill-improvement cadence (monthly/quarterly scheduled skill health checks)

## Objective

Implement a scheduled skill-improvement cadence that uses existing workspace skills in new combinations to find and fix skill degradation before it manifests in production failures.

## Status

OPEN — research complete, wiki concept written, implementation not started.

## Producing context

- Date: 2026-07-27
- Session: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
- Source: /www research on "can /wargame and /brainstorming help our skills on a regular basis?"

## Read-first list

1. `P:/.data/wiki/concepts/routine-skill-improvement-cadence.md` — the full research-backed recommendation
2. `C:\Users\brsth\.grok\skills\skill-dev\SKILL.md` — the existing measure+improve skill
3. `C:\Users\brsth\.grok\skills\aar\SKILL.md` — the opportunity landscape that surfaces skill gaps
4. `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — the lifecycle this cadence maintains

## Verified facts

- [FACT] The workspace has 14+ skills for analysis, review, verification, and knowledge capture — receipt: skill catalog
- [FACT] No scheduled cadence exists for using these skills on EACH OTHER — receipt: no scheduler entries, no recurring tasks
- [FACT] /skill-dev exists with measure and improve modes — receipt: skill catalog lists it
- [FACT] Research converges on scheduled cadence as the key factor — receipt: 3 parallel research subagents, all found cadence > technique
- [FACT] Novel skill combinations are unexplored — the combinatorial space is large but undocumented

## Current state

**Research complete.** Wiki concept written and validated. The recommended cadence is documented. Implementation requires:
1. A scheduling mechanism (recurring task, cron, or session-start hook)
2. A skill-selection heuristic (which skills to audit monthly vs quarterly)
3. A finding-to-action tracking system (so monthly findings don't evaporate)

## Task packets

### CADENCE-01: Create the monthly skill-health-check workflow
- **goal:** Define and document the monthly workflow: /skill-dev measure → /brainstorming on top degraded skills → disposition tracking
- **in scope:** workflow documentation, skill selection heuristic
- **out of scope:** the scheduling mechanism itself (CADENCE-02)
- **files:** new reference doc at `~/.grok/skills/skill-dev/references/monthly-cadence.md` or similar
- **acceptance:** documented workflow with skill-selection criteria and disposition tracking
- **verification:** STATIC_INSPECTION

### CADENCE-02: Implement the scheduling mechanism
- **goal:** Make the monthly cadence fire automatically (recurring task, scheduler_create, or session-start reminder)
- **in scope:** the trigger mechanism
- **out of scope:** the workflow content (CADENCE-01)
- **acceptance:** the cadence fires once per month without manual invocation
- **verification:** LIVE_BEHAVIOR

### CADENCE-03: Explore novel skill combinations
- **goal:** Test 3-5 novel skill combinations from the combinatorial table in the wiki concept. Document which produce insights that standard /check+/review miss.
- **in scope:** /design on a skill, /packet+cross-model, /www+skill-dev, /tp on skill framing, /brainstorming on failure modes
- **out of scope:** implementing all combinations — test a sample first
- **acceptance:** documented assessment of which combinations add value vs which duplicate standard review
- **verification:** STATIC_INSPECTION

## Open decisions

### D-1: Which scheduling mechanism?
- **Options:** (a) scheduler_create (built-in), (b) SessionStart hook reminder, (c) recurring task in ~/.claude/tasks, (d) manual (operator invokes monthly)
- **Selection criterion:** reliability vs complexity
- **Current lead:** (a) scheduler_create — it's built-in, persistent, and fires without operator intervention

### D-2: Which skills to audit monthly vs quarterly?
- **Options:** (a) all skills monthly, (b) load-bearing skills (close, aar, why, design, go) monthly, others quarterly, (c) rotate (2-3 skills per month, all covered quarterly)
- **Selection criterion:** coverage vs cost
- **Current lead:** (b) — load-bearing skills have the highest blast radius if degraded

## Hard constraints

- The cadence must not become ceremony — every finding gets a disposition (ACT_NOW, MONITOR, INVESTIGATE, REJECT)
- Novel combinations must be explored, not just the obvious ones
- The monthly cadence should take <30 min to execute (using /skill-dev measure + targeted brainstorming)

## Cross-reference couplings

- `P:/.data/wiki/concepts/routine-skill-improvement-cadence.md` — the research backing
- `C:\Users\brsth\.grok\skills\skill-dev\SKILL.md` — the measure+improve skill to extend
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — the lifecycle this maintains

## Other outstanding streams

- **Wiki-query Stop hook** — handoff at `wiki-query-stop-hook-20260727/HANDOFF.md`. READY_FOR_REVIEW.
- **AAR non-skippable enforcement** — handoff at `aar-non-skippable-enforcement-20260726-design-blocked/HANDOFF.md`. OPEN.

## Explicit non-goals

- Do NOT implement all 8 combinations from the table — test a sample first
- Do NOT make the cadence mandatory/blocking — it should inform, not gate
- Do NOT replace existing /check+/review — the cadence is additive

## Resumption protocol

1. Read the wiki concept `routine-skill-improvement-cadence.md`
2. Decide on the scheduling mechanism (D-1)
3. Implement CADENCE-01 (workflow documentation)
4. Implement CADENCE-02 (scheduling)
5. Run the first monthly cycle as a test

## Suggested next invocation

```
/go "Implement the routine skill-improvement cadence from P:/.data/wiki/concepts/routine-skill-improvement-cadence.md. Start with CADENCE-01 (document the monthly workflow), then CADENCE-02 (scheduler_create for monthly firing). Use /skill-dev measure as the measurement primitive."
```

## Last user message (verbatim)

> "yes please. also include that we should look at other skill combinations than just /brainstorming /wargame /red-team etc."

## Epistemic labels

- [FACT] 14+ skills exist with quality mechanisms — receipt: skill catalog
- [FACT] No scheduled cadence exists — receipt: no scheduler entries found
- [FACT] Research converges on cadence as key factor — receipt: 3 parallel subagent results
- [INFERENCE] Novel combinations will surface insights standard review misses — plausible but untested; CADENCE-03 tests this
- [INFERENCE] Monthly cadence will take <30 min — estimated from /skill-dev measure runtime, not measured

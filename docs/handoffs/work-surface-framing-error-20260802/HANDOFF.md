---
thread_id: work-surface-framing-error-20260802
parent_handoff_path: docs/handoffs/work-surface-greenfield-design-20260802/HANDOFF.md
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
parent_session: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 7c38e4c0-057f-43fc-b03d-1fe3048cea80
produced_at: 2026-08-02T18:30:00Z
last_updated_by: 019fb177-e5d5-7520-92f5-0158f87639c9
last_updated_at: 2026-08-02T18:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: b08d1a8
---

# Handoff: Work-surface framing error — why the solution, red-team, and tp review all got it wrong

**Status:** OPEN — framing error diagnosed, needs best-practice domain research before redesigning
**Created:** 2026-08-02
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9

## Objective

Diagnose why three rounds of design + review (greenfield proposal → red-team → tp review) all failed to produce a correct work-surface architecture, identify the correct best-practice domains, and document the simplified solution that emerged.

## Resolution (2026-08-02 — this update)

After the framing error was diagnosed, the operator challenged the "missing domains" assumption. On inspection:

1. **Triage/clarification is NOT needed** — handoffs are pre-structured (16 fields, acceptance criteria). Intake is controlled, not a firehose.
2. **Prioritization/planning is NOT needed** — the operator decides what to do from the list. They've never said "I can't decide." They've said "the information is scattered across 5 commands."
3. **The actual gap is discovery breadth in `/todo`** — it scans handoffs + harvest + git, but misses FINDINGS.md, WIKI markers, and deferred wiki patterns.

The pain is "I have to run too many commands to see what's open." The fix is extending `/todo`'s scan sources + folding 2 overlapping skills, not adding new domains or building new skills.

## The simplified solution (3 fixes)

### Fix 1: Extend `/todo` scan to pull from all sources
Add 3 scan steps to `/todo`:
- FINDINGS.md scan (open review bugs from `.artifacts/`)
- WIKI: marker scan (uncaptured knowledge from transcript)
- Deferred wiki patterns (grep for blocked/deferred/setup-needed)

`/todo` becomes the one command that shows everything open. The operator decides what to do from the list.

### Fix 2: Fold `/capture` + `/friction` into `/tp session`
Both are transcript scans with different output routing. `/tp session` already has a transcript scan. Add `/capture`'s 7 categories and `/friction`'s 2 modes as additional scan passes. Mark both deprecated.

### Fix 3: Delete `/close` (already deprecated by `/close-check`)
Remove the deprecated skill. `/close-check` is the lifecycle gate.

### What we are NOT doing
- No new skill (`/work` is not needed)
- No JSON work store (grep on .md works)
- No impact/effort scoring (operator decides, not the system)
- No commitment gating (not a missing domain — operator makes commitments)
- No architecture redesign (the fix is scan breadth + 2 skill folds)

## The 10 domains (all served, none missing)

| Domain | Served by | Status |
|--------|-----------|--------|
| Intake / capture | `/handoff`, `/harvest` | ✅ exists |
| Organization / backlog | handoffs (flat list) | ✅ exists |
| Status / tracking | `/todo` (needs scan breadth) | ✅ exists, needs Fix 1 |
| Execution | `/go`, `/refactor` | ✅ exists |
| Delivery / completion | `/check`, `/close-check` | ✅ exists |
| Retrospective | `/tp session`, `/aar`, `/recap-grok` | ✅ exists |
| Improvement discovery | `/tp improve`, `/skill-dev` | ✅ exists |
| Knowledge capture | `/wiki`, `/handoff` | ✅ exists |
| Obligation tracking | `/harvest` | ✅ exists |
| Quality verification | `/check`, `/review`, `/trace` | ✅ exists |

## The framing error (what went wrong)

### Layer 1: The proposal was wrong
The original greenfield proposed `/work` as a new unified skill replacing 8 others. This was over-scoped (8→1 was actually 3→1) and built on a cargo-culted pattern (ENTRYPOINT+CMD from Docker).

### Layer 2: The red-team was wrong
The red-team (3 specialists, REVISE verdict) correctly identified over-scoping and the delegation failure pattern. But it **accepted the framing** that `/tp session` should be the unified entry point. Its recommendation ("fix /tp session → /todo delegation first") perpetuated the same error: making a retrospective (backward-looking) the front door for planning (forward-looking).

The red-team attacked the *mechanism* (how to build /work, whether to merge skills) but not the *purpose* (what ceremony is this skill mapping to, and is it the right one?). It checked architecture, scope, and workflow — but not **domain mapping** (does this map to a known best-practice pattern?).

### Layer 3: The tp review was wrong
The tp review integrated the red-team findings and updated the handoff. It accepted the "delegation-first" approach without questioning whether `/tp session` is the right entry point. It took the operator asking "is a sprint retro how people figure out what to do?" to surface the error.

The tp review did exactly what the red-team did: optimized the *implementation* without questioning the *framing*.

### Root cause of all three failures
**No one checked what domain of best practice this maps to.** The proposal, red-team, and tp review all treated this as a software architecture problem (skill consolidation, delegation chains, ENTRYPOINT+CMD pattern). It's actually a **work management process design** problem — and none of the three rounds queried the right domain.

The /www research surfaced NOW/NEXT/LATER, impact/effort, and ADHD external memory — but these were applied as *features to add*, not as *a domain to ground the design in*. The research was bolted onto the architecture instead of driving it.

## What the operator caught (the insight)

The operator asked: "is the sprint retro what people use to figure out what they should do?" The answer is no. Sprint retros are backward-looking (what happened). Sprint planning and backlog grooming are forward-looking (what to do next). `/tp session` is structurally a retro. Putting it as the entry point for "what should I do?" is asking the operator to use a backward-looking ceremony for forward-looking decisions.

**The correct question is not "which skill should be the entry point?" but "what work-management domains are we implementing, and which skill serves each domain?"**

## Best-practice domains for work discovery, reporting, tracking, and improvement

This is what the next session needs to research and map our skills against. The operator explicitly asked: "what domains does best practice have regarding finding work to do, reporting work to do, tracking work, work to improve the system, etc."

### Known domains (from /www research + operator's question)

| Domain | Question it answers | Best-practice ceremony | Our current skills |
|--------|--------------------|-----------------------|--------------------|
| **Backlog management** | What work exists? | Backlog grooming, issue triage | `/todo` (scan), `/harvest` (obligations), handoffs (work items) |
| **Prioritization / planning** | What should I do next? | Sprint planning, NOW/NEXT/LATER | **MISSING** — no skill does commitment gating |
| **Execution** | Do the work | — (the work itself) | `/go`, `/refactor`, `/review` |
| **Status / standup** | What am I doing? What's blocking? | Daily standup | `/todo` (partially), `/tp session` (partially) |
| **Retrospective** | What happened? What was good/bad? | Sprint retrospective, AAR | `/tp session`, `/aar`, `/recap-grok` |
| **Improvement discovery** | What could be better? | Continuous improvement, Kaizen | `/capture`, `/friction`, `/tp improve`, `/skill-dev` |
| **Knowledge capture** | What did we learn? | Documentation, ADRs | `/wiki`, `/handoff` |
| **Obligation tracking** | What's unfinished? | Issue tracking, debt tracking | `/harvest`, `/tasks` |
| **Quality verification** | Did we do it right? | Code review, testing | `/check`, `/review`, `/trace` |

### The missing domain: Prioritization / planning

No skill currently does **sprint planning**: taking the full backlog scan, applying impact/effort scoring, producing a committed NOW tier (3-5 items max), surfacing blocked items, and deferring the rest. This is the gap the operator feels as "I have to run 5 commands." The gap isn't skill overlap — it's a **missing ceremony**.

### Domains to research (next session)

The /www research covered task management and prioritization frameworks. But it didn't cover:

1. **Work intake / discovery** — how do practitioners discover work that needs doing? (Not just "scan the backlog" — where does the backlog come from? How does new work enter the system?)
2. **Commitment gating** — how do teams decide what goes in NOW vs NEXT? (RICE? MoSCoW? Velocity-based? Gut feel?)
3. **Obligation vs opportunity** — how do practitioners distinguish "must do" (obligations, debt) from "could do" (opportunities, improvements)?
4. **Improvement system design** — how do Kaizen/continuous-improvement systems organize themselves? (Daily improvement vs periodic vs event-driven)
5. **Fleet-specific** — how do multi-agent fleet operators track work across agents? (Mission Control, git-issues, Agentic Sync from HN)

## Why this is a handoff, not an implementation

The design has been wrong three times because the framing was wrong. Before redesigning, the next session needs to:

1. Research the best-practice domains above (the operator's question)
2. Map each existing skill to its correct domain (not "which to merge" but "which domain does each serve")
3. Identify which domains are missing or underserved
4. Design the missing domain (prioritization/planning) as a first-class concept
5. Only then decide what to merge, keep, or eliminate

**Do NOT start with "which skills to consolidate."** Start with "what domains does the operator need, and which are served." The skill architecture follows the domain map, not the other way around.

## Verified facts

- [FACT] Three design rounds (proposal, red-team, tp review) all accepted the framing that /tp session should be the unified entry point (session transcript, 2026-08-02)
- [FACT] The operator caught the framing error by asking "is the sprint retro what people use to figure out what they should do?" — answer: no (session transcript)
- [FACT] No skill currently does commitment-gated sprint planning (grep of all skill descriptions, 2026-08-02)
- [FACT] The red-team's 3 specialists checked architecture, scope, and workflow — but not domain mapping (red-team specialist prompts, 2026-08-02)
- [FACT] The /www research surfaced frameworks (NOW/NEXT/LATER, impact/effort) but applied them as features, not as a domain grounding (session transcript)

## Hard constraints

- Do NOT redesign the work surface until the domain map is complete
- Do NOT start with "which skills to merge" — start with "what domains does the operator need"
- Do NOT assume any existing skill is in the right domain — remap from scratch
- Research the domains the operator asked about: finding work, reporting work, tracking work, improving the system

## Cross-reference couplings

- `work-surface-greenfield-design-20260802` → the (incorrectly framed) design that this handoff supersedes
- `session-review-skill-division-20260801` → the boundary decisions that need re-examination against the domain map
- `premature-recommendation-pattern-20260801` → the pattern that caused all three rounds to ship recommendations before checking the domain

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T18:30 | 019fb177... | created — framing error diagnosis + domain research request |
| 2026-08-02T19:15 | 019fb177... | resolved — operator challenged missing-domains assumption; simplified to 3 fixes (scan breadth + 2 skill folds). No new skill, no architecture redesign. All 10 domains served. |

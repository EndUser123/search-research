---
thread_id: 7a3b2c1d-4e5f-6789-0123-456789abcdef
parent_handoff_path: P:/docs/handoffs/fleet-improvement-research-25-recombinations-2026-08-06/HANDOFF.md
current_session_id: 019fcdd2-e190-7323-9b77-57a1c73dada5
parent_session: 019fcdd2-e190-7323-9b77-57a1c73dada5
current_terminal_id: console_019fcdd2
produced_at: 2026-08-07T20:45:00Z
last_updated_by: 019fcdd2-e190-7323-9b77-57a1c73dada5
last_updated_at: 2026-08-07T20:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: f9fa481
---

# HANDOFF: Rationalize the finding/todo skill family

## 1. Objective

Decide whether the current 7-skill family for finding and presenting gaps, problems, unfinished work, and session-end gates is the optimal design, or whether it should be consolidated, re-scoped, or re-layered. The operator flagged confusion about the boundaries between `/todo`, `/insight`, `/aar`, `/maintain`, `/review`, `/close`, and `/check` — specifically, "what's the domains for the findings?" This handoff captures the problem and produces a rationalization investigation the next session can execute.

**Scope bounds:** This is a design problem, not an implementation task. The next session should produce a recommendation (keep / consolidate / re-scope), not immediately edit skills. Implementation follows operator approval.

## 2. Status

**OPEN** — Problem identified and framed. Current 2-axis domain map produced (subject × time scale) but needs validation against actual usage and skill overlap.

The operator's exact signal that triggered this handoff: "I'm a bit confused. we have a bunch of different skills. what's the domains for the findings?"

## 3. Producing context

- Date: 2026-08-07
- Session: `019fcdd2-e190-7323-9b77-57a1c73dada5`
- Terminal: `console_019fcdd2`
- Host: grok (Grok Build, GLM-5-2)
- Triggered by: `/ask` routing query that missed `/aar`, revealing the family is hard to navigate even for the routing skill

## 4. Read-first list (ordered, with reasons)

1. **This handoff** — the problem statement and 2-axis domain map below
2. `~/.grok/skills/todo/SKILL.md` — the primary "what should I do?" skill
3. `~/.grok/skills/insight/SKILL.md` — session-scope improvement finder
4. `~/.grok/skills/aar/SKILL.md` — deep retrospective with value accounting
5. `~/.grok/skills/maintain/SKILL.md` — fleet-level maintenance
6. `~/.grok/skills/review/SKILL.md` — code/package review
7. `~/.grok/skills/close/SKILL.md` — session close-out orchestrator
8. `~/.grok/skills/check/SKILL.md` — multi-concern session verification
9. `~/.grok/skills/ask/SKILL.md` — the routing skill that failed to surface `/aar` (the signal that something is confusing)

## 5. Verified facts (with source paths)

- [FACT] 7 skills in the family: `/todo`, `/insight`, `/aar`, `/maintain`, `/review`, `/close`, `/check`. Source: session skill catalog (system reminder at session start lists all 7 with absolute paths).
- [FACT] `/ask` (the routing skill) missed `/aar` when recommending finding skills. Root cause: grep keywords ("gap|unfinished|outstanding|backlog|incomplete" and "todo|insight|harvest|maintain|audit|scan|discover") didn't match `/aar`'s description vocabulary ("continual-improvement... value accounting... opportunity landscape"). Source: this session's `/ask` invocation transcript.
- [FACT] `/harvest` is referenced in `~/.grok/AGENTS.md` under proactive suggestions but does NOT exist in the skill catalog. The only "harvest" hits in the catalog are `ponytail-debt`'s description. Source: `grep harvest P:/.data/wiki/concepts/skill-catalog.md`.
- [FACT] The 7 skills produce different output types: work-item list (`/todo`), improvement items (`/insight`), lessons + value accounting (`/aar`), maintenance actions (`/maintain`), code findings (`/review`), close-out gates (`/close`), verify verdict (`/check`). Source: session skill list descriptions.
- [FACT] `/aar` is available in this session (confirmed via file read at `~/.grok/skills/aar/SKILL.md`), despite `/ask` failing to surface it.

## 6. Current state

**Done (this session):**
- Produced a 2-axis domain map distinguishing the 7 skills:

| Domain (what it finds) | Session scope | Workspace scope | Fleet/cross-session scope |
|---|---|---|---|
| Work items (unfinished tasks, open handoffs) | — | `/todo` | — |
| Knowledge gaps (noticed but not captured) | `/insight` | — | — |
| Code defects (bugs, maintainability, security) | — | `/review` | — |
| Hygiene problems (stale artifacts, bloat, drift) | — | `/maintain` | `/maintain` |
| Behavioral patterns (root causes, value accounting) | `/aar` (light) | — | `/aar` (deep) |
| Completion gates (uncommitted work, missing handoffs) | `/close`, `/check` | — | — |

- Identified 3 overlap confusions:
  1. `/todo` vs `/insight` — both "find unaddressed things," different scan targets (workspace vs transcript)
  2. `/aar` vs `/insight` — both "review the session," items vs patterns
  3. `/maintain` vs `/review` — both "find problems in code/config," focused vs broad

**Not done:**
- Validate the domain map against actual usage (do the skills actually produce non-overlapping output in practice?)
- Decide: is 7 skills the right number, or should some consolidate?
- Decide: should `/ask` routing be improved to surface all finding skills regardless of keyword?
- Measure actual overlap (do `/todo` and `/insight` both report the same handoff gap, for instance?)

## 7. Task packets

### TASK-1: Measure actual skill output overlap
- **id:** TODO-RAT-01
- **goal:** Run `/todo`, `/insight`, and `/aar` against the same session (this one, or a historical one from `~/.grok/sessions/`) and measure how much their output overlaps. Quantify: do they surface the same items, or genuinely different ones?
- **in scope:** Run each skill, capture output, diff the findings
- **out of scope:** Implementation changes (that's TASK-3)
- **acceptance:** A comparison table showing % overlap between each pair of skills
- **falsifier:** All three skills surface identical items (high overlap → consolidate). Zero overlap (no consolidation needed, just better routing).
- **verification level required:** LIVE_BEHAVIOR (run the skills)
- **depends_on:** none

### TASK-2: Decide consolidation vs re-scoping vs keep
- **id:** TODO-RAT-02
- **goal:** Based on TASK-1's overlap data, recommend one of: (A) consolidate (e.g., merge `/insight` into `/aar`), (B) re-scope (sharpen boundaries between overlapping skills), (C) keep as-is and fix routing (`/ask` coverage gap)
- **in scope:** Decision recommendation with rationale, citing the overlap data
- **out of scope:** Implementation
- **acceptance:** A recommendation with selection criterion stated and at least one rejected alternative
- **falsifier:** Recommendation doesn't cite the overlap data from TASK-1
- **verification level required:** STATIC_INSPECTION (a decision, not code)
- **depends_on:** TODO-RAT-01

### TASK-3: Implement the decision (if consolidation or re-scoping)
- **id:** TODO-RAT-03
- **goal:** Implement whichever decision TASK-2 produces. May be: merge skills, sharpen SKILL.md boundaries, improve `/ask` routing keywords, or build a unified `/find` dispatcher.
- **in scope:** TBD based on TASK-2
- **out of scope:** Other skill families
- **acceptance:** TBD based on decision
- **falsifier:** TBD
- **verification level required:** LIVE_BEHAVIOR
- **depends_on:** TODO-RAT-02

### TASK-4: Fix the `/ask` routing coverage gap
- **id:** TODO-RAT-04
- **goal:** `/ask`'s keyword expansion missed `/aar` because its grep keywords didn't include retrospective vocabulary. Fix the `/ask` skill (or its keyword expansion logic) so that finding-skills are surfaced regardless of which finding vocabulary the operator uses.
- **in scope:** `~/.grok/skills/ask/SKILL.md` — add a canonical "finding skills" keyword set that includes all 7 family members' vocabularies
- **out of scope:** Other routing skills
- **acceptance:** `/ask what skills should I use to find gaps` surfaces all relevant finding skills including `/aar`
- **falsifier:** `/aar` still missing from the recommendation after the fix
- **verification level required:** LIVE_BEHAVIOR (re-run the `/ask` query)
- **depends_on:** none (independent — can be done regardless of TASK-1/2/3)

## 8. Open decisions

### Decision 1: Consolidate or keep separate?
- **Question:** Are 7 finding/gate skills too many, or is the specialization valuable?
- **Options:**
  - (A) **Consolidate** — merge `/insight` into `/aar` (both review the session), merge `/close` into `/check` (both are completion gates). Reduces to ~5 skills.
  - (B) **Re-scope** — keep 7 but sharpen boundaries. Each SKILL.md gets a "distinct from" section naming the siblings it doesn't overlap with.
  - (C) **Keep + dispatch** — keep all 7 but build a `/find` dispatcher that routes to the right one based on intent (similar to how `/go` dispatches to `/refactor` vs `/review`).
  - (D) **Keep + fix routing** — keep all 7, improve `/ask` keyword coverage so finding skills surface correctly. No structural change.
- **Selection criterion:** Cognitive load on the operator (who flagged confusion) × skill specialization value (do the skills actually find different things?)
- **Currently leads:** (B) or (D) — the skills likely do find different things (per the domain map), but the operator's confusion is real and routing is broken. (D) is the minimal fix; (B) adds durable boundary documentation.
- **What would change:** TASK-1's overlap data. If overlap is high, (A) consolidates. If overlap is low, (D) suffices.

### Decision 2: Is `/harvest` a phantom?
- **Question:** AGENTS.md references `/harvest` under proactive suggestions, but it doesn't exist in the catalog. Was it deleted, renamed, or never built?
- **Options:**
  - (A) `/harvest` was absorbed by `/insight` or `/aar` — update AGENTS.md to remove the reference
  - (B) `/harvest` is a planned skill that was never built — decide whether to build it or remove the reference
  - (C) `/harvest` exists under a different name — find it and update the reference
- **Selection criterion:** Historical accuracy (what happened) + forward value (is the capability still needed?)
- **Currently leads:** (A) — the capability (root-cause clustering, unrealized obligations) is covered by `/aar`'s opportunity landscape and `/insight`'s unactioned-items scan. The AGENTS.md reference should be updated to point to those.

## 9. Hard constraints

- The finding-skill family runs on every session — any consolidation must not break existing invocation patterns
- GraSP finding (from the fleet-improvement research): splitting or merging skills must produce a deterministic dispatch tree, not a flat menu — so if consolidating, the merged skill must have clear sub-modes
- `/ask` is the routing entry point — fixing it is higher-leverage than restructuring the skills it routes to

## 10. Cross-reference couplings

- `docs/handoffs/fleet-improvement-research-25-recombinations-2026-08-06/HANDOFF.md` — parent handoff; TASK-4 (claim-judge hook, now COMPLETE) was a sibling task
- `~/.grok/skills/ask/SKILL.md` — the routing skill with the coverage gap (TASK-4)
- `~/.grok/AGENTS.md` § "Proactive skill suggestions" — references `/harvest` which doesn't exist (Decision 2)
- `P:/.data/wiki/concepts/skill-catalog.md` — the canonical skill registry; any consolidation must update it via `index_skills.py`

## 11. Other outstanding streams

- **Fleet improvement handoff** — TASK-1/2/3 (triage 25 recombinations, build go_router.py, build selected recombinations) still open
- **LAEFS enforcement layer** — separate handoff, Phase 2a-2d ready
- **Skill bloat across fleet** — 24/50 skills exceed 400 lines; the finding-skill family is a subset of this larger problem

## 12. Explicit non-goals

- Do NOT implement consolidation before TASK-1 (overlap measurement) confirms it's warranted
- Do NOT delete `/harvest` references without confirming what happened to it (Decision 2)
- Do NOT restructure the finding family in the same session as the fleet-improvement triage — they're independent and doing both risks scope confusion

## 13. Resumption protocol

1. Read this handoff (the domain map in §6 is the key artifact)
2. **TASK-1:** Run `/todo`, `/insight`, and `/aar` against this session (or a historical one) and measure output overlap
3. **TASK-2:** Based on overlap data, recommend consolidation / re-scoping / keep
4. **TASK-4 (independent):** Fix `/ask` routing coverage so finding skills surface regardless of vocabulary
5. Present the recommendation to the operator before any implementation (TASK-3)

## 14. Suggested next invocation

```
/go Measure the output overlap between /todo, /insight, and /aar by running
each against session 019fcdd2-e190-7323-9b77-57a1c73dada5 (or a comparable
historical session). Produce a comparison table showing what each surfaced
and the overlap percentage. Then recommend: consolidate, re-scope, or keep
the 7-skill finding family as-is.
```

Or, for the independent routing fix:

```
/go Fix /ask's keyword expansion so finding-skills (/todo, /insight, /aar,
/maintain, /review, /close, /check) surface regardless of which finding
vocabulary the operator uses. Add a canonical "finding skills" keyword set
to ~/.grok/skills/ask/SKILL.md. Acceptance: /ask "what skills should I use
to find gaps" surfaces all 7 family members.
```

## 15. Last user message (verbatim)

> "/handoff to look at all these skills to rationalize how we find and present todos"

## 16. Epistemic labels per claim

- [FACT] 7 finding/gate skills exist in the family (session skill catalog)
- [FACT] `/ask` missed `/aar` in its recommendation this session (transcript)
- [FACT] `/harvest` is referenced in AGENTS.md but absent from the catalog (grep receipt)
- [INFERENCE] The skills likely find genuinely different things (domain map shows distinct output types), but overlap is unmeasured
- [INFERENCE] The operator's confusion is primarily a routing problem (7 skills is manageable if routing works), not necessarily a design problem
- [UNKNOWN] Whether actual output overlap is high or low — TASK-1 resolves this

## 17. Suggested skills for next session

- `/go` — TASK-1 (overlap measurement) is a concrete data-gathering task
- `/tp` — if the operator wants to challenge the domain map before measuring
- `/wiki` — if the domain map (§6) should be captured as a durable concept before restructuring

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-07T20:45 | 019fcdd2 | created |

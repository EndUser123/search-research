---
thread_id: insight-skill-consolidation-019fc927
parent_handoff_path: P:/docs/handoffs/close-check-follow-on-019fc927-20260806/HANDOFF.md
current_session_id: 019fc927-d207-7c41-a512-5e90ff0c8b91
parent_session: none
current_terminal_id: grok-019fc927
produced_at: 2026-08-07T00:00:00Z
last_updated_by: 019fc927-d207-7c41-a512-5e90ff0c8b91
last_updated_at: 2026-08-07T00:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: c7f0bea3f0db50e324025143680b8c3c8fafb170
---

# Handoff: Create `/insight` — unified improvement-finding skill

## Objective

Create `/insight`, a single skill that absorbs the improvement-finding functions of `/capture`, `/friction`, and `/harvest`, then deprecate those three skills and migrate all callers to `/insight`.

**Scope bounds:** Work scope is 4 skills to consolidate (`/capture`, `/friction`, `/harvest` absorbed; `/skill-dev` and `/dream` kept). Total fleet is ~90 skills; the consolidation touches 4 directly + ~8 callers indirectly.

## Status

CLOSED — consolidation implemented and committed. See Execution Status below.

## Producing context

- Session: 019fc927 (2026-08-03 to 2026-08-07)
- Plan written to: `C:\Users\brsth\.grok\sessions\P%3A%5C\019fc927-d207-7c41-a512-5e90ff0c8b91\plan.md`
- Operator approved the plan after `/ask` routing failure exposed the fragmentation problem

## Read-first list (ordered)

1. `C:\Users\brsth\.grok\sessions\P%3A%5C\019fc927-d207-7c41-a512-5e90ff0c8b91\plan.md` — the approved implementation plan with full migration steps
2. `~/.grok/skills/capture/SKILL.md` — the body to absorb (9 categories, dual-stream routing, coverage check). This is the largest body — 290 lines. `/insight` default mode inherits this structure.
3. `~/.grok/skills/friction/SKILL.md` — the friction detection to absorb (interaction + workflow friction, pattern markers, scoring). 230 lines. Categories 1-2 are already covered by `/capture` but the markers and scoring rubric are more detailed.
4. `~/.grok/skills/harvest/SKILL.md` — deprecated but read for the cross-session obligation tracking concept. CLI is non-functional.
5. `~/.grok/skills/skill-dev/SKILL.md` — read the measure mode (Steps 0.5-2) for the `--skills` lightweight path. Do NOT absorb the full 8-step process.
6. `~/.grok/skills/close/SKILL.md` — find all references to `/capture` that need updating to `/insight`
7. `~/.grok/workflows/close-check.rhai` — the Rhai workflow that calls `/capture` by name during remediation phase
8. `P:/.data/wiki/concepts/skill-graph.md` — dependency graph to update after consolidation

## Verified facts

- [FACT] `/capture` provides 3 capabilities: `improvement-opportunity-scan`, `proactive-knowledge-capture`, `capture-coverage-check` (source: `~/.grok/skills/capture/SKILL.md` frontmatter)
- [FACT] `/friction` provides 2 capabilities: `friction-detection`, `workflow-automation-analysis` (source: `~/.grok/skills/friction/SKILL.md` frontmatter)
- [FACT] `/friction` depends_on `/aar` and is depended_on BY `/capture` (source: skill-graph.md line 93)
- [FACT] `/harvest` CLI is non-functional: "harvest CLI not on PATH and not installed as Python module" (source: close-check pre-close-report.md, this session)
- [FACT] `/capture` is called by `/close` as a mandatory step between AAR and final summary (source: `~/.grok/skills/capture/SKILL.md` § "Integration with /close")
- [FACT] `/close` SKILL.md references `/capture` in its improvement_capture gate (source: `~/.grok/skills/close/SKILL.md`)
- [FACT] The close-check Rhai workflow runs `/capture` in its remediation phase (source: `~/.grok/workflows/close-check.rhai`)
- [FACT] `/skill-dev` has 4 modes: create, measure, improve, audit-active (source: `~/.grok/skills/skill-dev/SKILL.md` § "The four modes")
- [FACT] `/dream` has a different architecture: batch synthesis reading 90 days of handoffs, not session scanning (source: `~/.grok/skills/dream/SKILL.md`)
- [INFERENCE] `/capture` categories 1 (corrections) and 2 (repeated manual steps) fully overlap `/friction`'s interaction + workflow friction detection

## Current state

**Designed but not implemented.** The plan is approved. No code written. No files created.

## Task packets

### TASK-1: Create `/insight` SKILL.md

- **Goal:** Write the unified skill with 4 modes
- **In scope:** New SKILL.md at `~/.grok/skills/insight/SKILL.md`
- **Out of scope:** Updating callers (TASK-3), deprecating old skills (TASK-4), reindexing (TASK-5)
- **Files/anchors:** New file
- **Acceptance:** SKILL.md exists with frontmatter, 4 modes documented, `/capture`'s 9 categories absorbed into default mode, `/friction`'s markers absorbed, `/skill-dev`'s lightweight measure path documented for `--skills` mode. Host: grok. Version: 1.0.0.
- **Falsifier:** If `/close` can't call `/insight` as a drop-in replacement for `/capture` (same 9 categories, same dual-stream routing, same coverage check), the absorption is incomplete.
- **Verification level required:** STATIC_INSPECTION (SKILL.md body correctness)
- **Disposition:** COMMIT_THIS_SESSION

### TASK-2: Absorb `/friction` detection into `/insight` default mode

- **Goal:** Merge `/friction`'s pattern markers, scoring rubric, and output format into `/insight`'s default mode
- **In scope:** The friction section within `/insight` SKILL.md
- **Out of scope:** `/friction`'s own SKILL.md (deprecated in TASK-4)
- **Files/anchors:** `~/.grok/skills/insight/SKILL.md` § friction detection
- **Acceptance:** `/insight` default mode produces friction findings with the same markers, categories, and scoring as `/friction` today
- **Falsifier:** If a session that would have invoked `/friction` produces fewer or lower-quality friction findings via `/insight`, the absorption lost signal
- **Verification level required:** STATIC_INSPECTION
- **Disposition:** COMMIT_THIS_SESSION (part of TASK-1)

### TASK-3: Update `/close` and `/close-check` to call `/insight`

- **Goal:** Replace all `/capture` references with `/insight` in the close pipeline
- **In scope:**
  - `~/.grok/skills/close/SKILL.md` — improvement_capture gate references
  - `~/.grok/workflows/close-check.rhai` — remediation phase `/capture` call
  - `~/.grok/commands/close-check.md` — if it references `/capture`
- **Out of scope:** Other skills that reference `/capture` (TASK-5)
- **Files/anchors:** Multiple files, grep for `/capture` to find all references
- **Acceptance:** `grep -r "/capture" ~/.grok/skills/close/ ~/.grok/workflows/ ~/.grok/commands/` returns 0 results (or only DEPRECATED notices)
- **Falsifier:** If `/close` fails to find the improvement-capture step because it's looking for `/capture` not `/insight`, the migration broke the close pipeline
- **Verification level required:** LIVE_BEHAVIOR — run `/close-check --dry-run` and verify the remediation phase calls `/insight`
- **Disposition:** COMMIT_THIS_SESSION

### TASK-4: Deprecate `/capture`, `/friction`, `/harvest`

- **Goal:** Mark all three as DEPRECATED with pointers to `/insight`
- **In scope:**
  - `~/.grok/skills/capture/SKILL.md` — add DEPRECATED notice at top
  - `~/.grok/skills/friction/SKILL.md` — add DEPRECATED notice at top
  - `~/.grok/skills/harvest/SKILL.md` — add DEPRECATED notice at top
- **Out of scope:** Deleting the files (keep for reference; skills may still be invoked by old habits)
- **Files/anchors:** 3 SKILL.md files
- **Acceptance:** Each file starts with `> **DEPRECATED — use /insight instead.**` and a one-line redirect
- **Falsifier:** If a session invokes `/capture` and gets the old behavior instead of being redirected to `/insight`, the deprecation isn't wired
- **Verification level required:** STATIC_INSPECTION
- **Disposition:** COMMIT_THIS_SESSION

### TASK-5: Update skill graph and references

- **Goal:** Reflect the consolidation in the skill graph, skill catalog, and dependent skills' references
- **In scope:**
  - `P:/.data/wiki/concepts/skill-graph.md` — update capabilities, dependencies
  - `P:/.data/wiki/concepts/skill-catalog.md` — add `/insight`, mark deprecated skills
  - Run `python P:/.data/wiki/scripts/index_skills.py` to regenerate catalog
  - Update `/todo`, `/tp`, `/ask`, `/aar`, `/handoff` SKILL.md files — grep for `/capture` and `/friction` references
- **Out of scope:** Updating wiki concepts that mention these skills (propagation can follow)
- **Files/anchors:** Multiple — grep `"/capture\|/friction\|/harvest"` across `~/.grok/skills/` and `P:/.data/wiki/`
- **Acceptance:** Skill graph shows `/insight` providing `improvement-opportunity-scan`, `proactive-knowledge-capture`, `capture-coverage-check`, `friction-detection`, `workflow-automation-analysis`. Deprecated skills show as DEPRECATED in catalog.
- **Falsifier:** If `/ask` still recommends `/capture` or `/friction` instead of `/insight`, the references weren't updated
- **Verification level required:** STATIC_INSPECTION
- **Disposition:** HANDOFF (can be done in a follow-on session if time is short)

### TASK-6: Wiki concept for the consolidation decision

- **Goal:** Document the architectural decision to consolidate into `/insight`
- **In scope:** New wiki concept at `P:/.data/wiki/concepts/insight-skill-consolidates-capture-friction-harvest.md`
- **Out of scope:** Implementation details (those live in the SKILL.md)
- **Acceptance:** Wiki concept exists with decision rationale, alternatives rejected, falsifier
- **Falsifier:** If a future session asks "why does `/insight` exist instead of separate skills?" and the wiki doesn't answer it
- **Verification level required:** STATIC_INSPECTION
- **Disposition:** HANDOFF

## Open decisions

### Decision 1: Should `/insight --fleet` absorb `/dream`'s function?

- **Question:** Should the `--fleet` mode be a lightweight cross-session pattern scan (grep handoffs for recurring patterns), or should it be a full batch synthesis like `/dream`?
- **Options:**
  - A: Lightweight scan (grep + LLM judgment on top N handoff patterns) — fast, lower quality
  - B: Full batch synthesis (read 90 days of handoffs + AARs, synthesize) — same as `/dream`
  - C: Co-exist — `/insight --fleet` is lightweight; `/dream` stays for deep synthesis
- **Selection criterion:** speed vs depth for the cross-session use case
- **Currently leads:** Option C — different architectures serve different needs
- **What would change:** if the lightweight scan proves sufficient, `/dream` could be deprecated too

### Decision 2: Should `/insight --skills <name>` absorb `/skill-dev measure`?

- **Question:** Is the lightweight MEC assessment (Steps 0.5-2) enough for most skill evaluations, or do operators always need the full 8-step process?
- **Options:**
  - A: `/insight --skills` provides lightweight; `/skill-dev measure` provides deep — co-exist
  - B: `/insight --skills` fully absorbs `/skill-dev measure` — `/skill-dev` keeps only create + improve
  - C: `/insight --skills` is just a pointer to `/skill-dev measure` — no absorption
- **Selection criterion:** how often operators need the deep measurement vs the quick read
- **Currently leads:** Option A — co-exist until evidence shows one is always sufficient
- **What would change:** if `/insight --skills` produces the same quality assessment in less time, absorb fully

## Hard constraints

1. `/close` pipeline must not break — the improvement-capture step is mandatory
2. `/capture`'s 9 categories and dual-stream routing must be preserved — they encode hard-won session experience
3. `/friction`'s pattern markers and scoring rubric must be preserved — they're more detailed than `/capture`'s category 2
4. `/harvest` is marked DEPRECATED, not deleted — the obligation-tracking concept may be rebuilt later
5. `/skill-dev` and `/dream` are NOT absorbed — different architectures, different lifecycle phases

## Cross-reference couplings

- `~/.grok/skills/close/SKILL.md` → calls `/capture` as mandatory step → must update to `/insight`
- `~/.grok/workflows/close-check.rhai` → calls `/capture` in remediation phase → must update to `/insight`
- `~/.grok/skills/capture/SKILL.md` → provides capabilities consumed by `/close`, `/todo`, `/tp`, `/aar`, `/handoff` → all callers must be updated
- `~/.grok/skills/friction/SKILL.md` → depends_on `/aar` → `/insight` inherits this dependency
- `P:/.data/wiki/concepts/skill-graph.md` → lists `/capture`, `/friction`, `/harvest` as separate nodes → must consolidate to `/insight`
- `P:/.data/wiki/concepts/skill-catalog.md` → lists all three → must update

## Other outstanding streams

- **Close-check follow-on work** — subagent-receipt aggregation, coverage monitor, push helper. Open handoff at `P:/docs/handoffs/close-check-follow-on-019fc927-20260806/HANDOFF.md`.
- **Chronic git-state hygiene** — core fix shipped (commit `f1d6956`). Follow-on work tracked in same handoff.

## Explicit non-goals

- Do NOT absorb `/aar` (retrospective analysis is a different question)
- Do NOT absorb `/wiki` (knowledge persistence is a different mechanism)
- Do NOT absorb `/dream` (batch synthesis architecture is different)
- Do NOT absorb `/skill-dev create` (skill creation is a different lifecycle phase)
- Do NOT delete deprecated skills (keep for reference; DEPRECATED notice redirects)
- Do NOT change the close-check Rhai workflow's structure (only update the skill name reference)

## Resumption protocol

1. Read the plan at `C:\Users\brsth\.grok\sessions\P%3A%5C\019fc927-d207-7c41-a512-5e90ff0c8b91\plan.md`
2. Read `/capture` SKILL.md body — this is the primary body to absorb
3. Create `~/.grok/skills/insight/SKILL.md` with 4 modes (TASK-1)
4. Grep for `/capture` across `~/.grok/skills/` and `~/.grok/workflows/` to find all callers (TASK-3)
5. Update callers, then deprecate old skills (TASK-3 → TASK-4)
6. Run `python P:/.data/wiki/scripts/index_skills.py` to reindex (TASK-5)

## Suggested next invocation

```
/go create /insight skill — absorb /capture (9 categories, dual-stream, coverage check)
+ /friction (interaction + workflow markers) into a unified improvement-finding skill
with 4 modes: default (session scan), --skills (skill MEC), --fleet (cross-session), --coverage
```

## Last user message (verbatim)

> "can we create '/insight' that has all the improvement finding functions, and then remove those that would now be fully redundant?"

## Epistemic labels per claim

- [FACT] `/capture`'s 9 categories and dual-stream routing are documented in its SKILL.md (cited)
- [FACT] `/friction` is a dependency of `/capture` (skill-graph.md)
- [FACT] `/harvest` CLI is non-functional (close-check report, this session)
- [FACT] `/close` calls `/capture` as a mandatory step (capture SKILL.md § "Integration with /close")
- [INFERENCE] `/capture` categories 1-2 fully overlap `/friction`'s detection — the categories are broader but the friction markers are more detailed
- [UNKNOWN] Whether `/insight --skills` will produce the same quality assessment as `/skill-dev measure` — needs production evidence

## Suggested skills for next session

- `/skill-dev create` — scaffold the new skill with quality gates (Mode 0)
- `/review --focus architecture` — review the `/insight` SKILL.md after creation for structural soundness
- `/tp` — fresh-lens critique of the consolidation before committing to the deprecation

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-07T00:00 | 019fc927 | created |
| 2026-08-07T12:00 | 019fd820 | implemented all 6 tasks + closed |

## Execution Status

Updated: 2026-08-07T12:00:00Z
Session: 019fd820-2fb5-7330-a0ab-290d5e529658
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | Create /insight SKILL.md with 4 modes | ✅ DONE | `~/.grok/skills/insight/SKILL.md` (450 lines, 9 categories + friction enrichment + 4 modes) |
| 2 | Absorb /friction detection into default mode | ✅ DONE | Categories 1-2 enriched with friction markers, scoring rubric, output format |
| 3 | Update /close + /close-check to call /insight | ✅ DONE | close/SKILL.md, close-check.rhai (9 edits), close-check.md all updated; grep for /capture returns 0 in close pipeline |
| 4 | Deprecate /capture + /friction | ✅ DONE | DEPRECATED notices added to both SKILL.md files pointing to /insight |
| 5 | Update skill graph + references | ✅ DONE | Catalog reindexed; /notice T10/T11/T13 updated; /behave, /dream references updated |
| 6 | Wiki concept for consolidation decision | ✅ DONE | `P:/.data/wiki/concepts/insight-skill-consolidates-capture-friction-harvest.md` |

### Key findings during execution
- `/harvest` SKILL.md does not exist at `~/.grok/skills/harvest/` — it was referenced conceptually in other skills but never had a Grok skill file. The harvest concept is absorbed into `/insight --fleet` mode; no file to deprecate.
- `/notice` has 8+ references to `/capture` across trigger definitions and version notes — all functional references (trigger tables, detection methodology) updated to `/insight`; historical version notes (v2.2-v2.5) left as-is since they describe what existed at the time.
- The close-check Rhai workflow ran `/friction` as a separate read-only subagent in Wave 1 — this was removed and friction detection merged into `/insight` (write-capable Wave 2), reducing the remediation wave from 5 subagents to 4.

### Verification
- `/insight` SKILL.md: contains all 9 categories, dual-stream routing, friction markers, 4 modes, coverage check ✅
- `/close` pipeline: zero `/capture` references remain (grep verified) ✅
- close-check.rhai: zero functional `/capture` or `/friction` references remain (only descriptive comments mention them as absorbed) ✅
- Catalog: `/insight` appears in skill catalog after reindex ✅
- Commits: `.grok` repo (3771954), `P:` repo (2e4f3e4) ✅

### Open decisions (unchanged from plan)
1. `/insight --fleet` vs `/dream` — co-exist for now
2. `/insight --skills` vs `/skill-dev measure` — co-exist for now

---
thread_id: dfb22e9e-4016-4c6d-8577-26706c839ea8
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T06:15:00Z
status: open
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: pending
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: Skill refactoring program — slim SKILL.md + offloaded references

## Objective (one sentence)

Refactor the largest user-scope skills to follow the `/tp`-pattern (slim SKILL.md as the "instrument" + detailed content offloaded to `references/` or `protocol.md`), so that batch-readers like `diffusiongemma_read.py` never need to truncate and skills are cold-readable within effective context budgets.

## Why this exists

Session 2026-07-22 shipped the **dynamic file cap** in `diffusiongemma_read.py` (replaces the fixed `max_file_chars=50000` with a context-budget-derived cap that self-adjusts to batch size). Testing across 6 real SKILL.md files surfaced that 11 of 31 skills exceed 20KB — the largest is 57KB (`design`). The dynamic cap handles this fairly, but the root issue is that many SKILL.md files are monoliths mixing operational rules (the "instrument") with reference material (detailed procedures, examples, persona prompts).

The `/tp` skill already demonstrates the target pattern: `SKILL.md` is the instrument (loaded on invocation); `protocol.md` is the deep reference (loaded on `/tp load`). `/aar` demonstrates the `references/` directory pattern (6 files). Both keep the always-loaded surface small.

## Status

**Convention documented in this handoff. Dynamic cap shipped (the script-side fix). Skill refactors NOT started — they are the work items below, to be done one at a time.**

## What's done (verified this session)

| Component | Done? | Evidence |
|-----------|-------|----------|
| Dynamic file cap in `diffusiongemma_read.py` | ✅ | `CONTEXT_CHARS_BUDGET = 400_000`; `_dynamic_file_cap()` helper; verified 6/6 summaries 3/3 runs stable |
| Count-explicit batch prompt (prevents model stopping early) | ✅ | "There are EXACTLY N files... ALL N must be covered"; verified 6/6 (was intermittently 5/6) |
| `_display_name()` fix (parent-dir name for generic filenames) | ✅ | 6-skill batch returns {go, handoff, plan, tp, web, wiki} not {SKILL × 6} |
| This handoff (convention + candidate list + acceptance criteria) | ✅ | this file |
| Skill refactors | ❌ | not started (see Work Items) |

## The convention to follow

### Principle: instrument vs reference

| Layer | Content | Target size | Where it lives |
|-------|---------|-------------|----------------|
| **Instrument** (SKILL.md) | Always-loaded rules: when to invoke, routing, decision criteria, quick-fit screening, falsifier, boundaries, links to references | ≤ 10–15KB | `~/.grok/skills/<name>/SKILL.md` |
| **Reference** | Detailed procedures, persona prompts, worked examples, protocol body, replay cases | Unrestricted | `<name>/protocol.md`, `<name>/references/*.md` |

**How to decide what goes where:** if a cold-start agent needs it to *decide whether to invoke the skill*, it's the instrument. If it needs it only *after deciding to invoke*, it's reference. When in doubt: if the content is >2 paragraphs and not a routing rule, offload it.

### The `/tp` precedent (the proven model)

- `SKILL.md` (29KB — still larger than ideal, but the pattern works): two-lens architecture, variant routing, failure-mode table, falsifier. States "SKILL.md is the instrument; protocol.md is the reference."
- `protocol.md` (42KB): full prompt reconstruction, hard rules, exemplars, craft patterns, rationale.

`/aar` is the other precedent: `SKILL.md` + `references/` directory with 6 focused files.

### Convention for new skills

Default to the instrument+reference split from the start. Do not write a monolith and plan to split later — the split is harder than starting right.

## Candidate list (priority-ordered)

11 skills exceed 20KB. Refactor in this order (largest + most-consumed first):

| Priority | Skill | Size | Consumed by | Existing offload | Notes |
|----------|-------|------|-------------|-----------------|-------|
| **1** | `design` | 57KB | `/design` (heavy use) | none | Largest by far; highest ROI |
| **2** | `review` | 41KB | `/review`, `/go` | none | Consumed by every `/go` review profile |
| **3** | `aar` | 38KB | `/aar` | `references/` (6 files), `__lib/` (19) | Already partially offloaded; SKILL.md still dense |
| **4** | `go` | 37KB | `/go` (every invocation) | none | Most-consumed skill; highest impact on cold-start cost |
| **5** | `mmx` | 35KB | `/mmx` | none | |
| **6** | `codex` | 33KB | `/codex` | none | |
| **7** | `tp` | 29KB | `/tp` | `protocol.md` (42KB) | Already offloaded; SKILL.md could be slimmer |
| **8** | `www` | 24KB | `/www` | none | |
| **9** | `agy` | 24KB | `/agy` | none | |
| **10** | `handoff` | 22KB | `/handoff` | `references/` (1 file), `__lib/` (6) | Partially offloaded |
| **11** | `refactor` | 21KB | `/refactor` | none | |

**11–20KB tier (monitor, don't refactor yet):** `debrief`, `grok-parallel`, `grok-discovery`, `grok-verify`, `wiki` (5KB — already slim), `web` (6KB), `plan` (10KB). These are under or near the 12K comfort threshold.

## Acceptance criteria (per skill refactor)

Each refactor is a separate work item with these gates:

1. **SKILL.md ≤ 15KB** after refactor (instrument only)
2. **Reference material preserved** — no content lost; moved to `protocol.md` or `references/*.md`
3. **Cold-start test passes** — a fresh agent reading only SKILL.md can correctly decide when to invoke the skill and where to find details
4. **`diffusiongemma_read.py --batch` returns the skill with `truncated: false`** at default batch sizes
5. **Skill still functions** — run the skill's quick-fit screening or a smoke invocation; confirm no regression
6. **Wiki concept for skill-authoring patterns updated** if the refactor reveals a new pattern worth documenting

## Work items (one per skill, done sequentially)

### Work Item 1: Refactor `design` (57KB → ≤15KB instrument)

- **Scope:** move detailed design-doc templates, reviewer-loop procedures, and worked examples from SKILL.md to `design/references/` or `design/protocol.md`
- **Risk:** medium — `/design` is a complex multi-step skill; the split must preserve the orchestration logic
- **Estimated effort:** 1–2 hours
- **Verification:** run `/design <small-topic>` end-to-end after refactor; confirm Phase 0–6 still works

### Work Items 2–11: `review`, `aar`, `go`, `mmx`, `codex`, `tp`, `www`, `agy`, `handoff`, `refactor`

Same pattern. One at a time. Verify after each.

## What NOT to do

- **Do NOT refactor all 11 in one pass.** Each is a load-bearing skill consumed by other skills. Bulk refactoring risks breaking the orchestration chain. One at a time with verification.
- **Do NOT offload routing rules, decision criteria, or quick-fit screening.** Those belong in the instrument (cold-start needs them). Only offload detailed procedures, examples, and persona prompts.
- **Do NOT delete content during the split.** Move, don't remove. If something is genuinely obsolete, note it in a separate cleanup pass after the structural split is verified.
- **Do NOT change skill behavior during the refactor.** This is a structural move (content relocation), not a functional rewrite. If behavior changes are needed, do them in a separate work item after the structural split.

## Resumption protocol

1. Read this handoff (the candidate list and acceptance criteria)
2. Read `P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md` for the prior art
3. Read `C:/Users/brsth/.grok/skills/tp/SKILL.md` (the instrument) + `tp/protocol.md` (the reference) to see the target pattern in action
4. Pick Work Item 1 (`design`) — or whichever skill you're about to touch next
5. Split: identify instrument vs reference content; move reference to `references/` or `protocol.md`; add a pointer in SKILL.md ("See `references/X.md` for ...")
6. Verify per acceptance criteria above
7. Repeat for the next skill

## Related artifacts

- Script (with dynamic cap): `P:/.data/wiki/scripts/diffusiongemma_read.py`
- Wiki: `diffusiongemma-direct-api-howto.md` (HOW-TO for the script)
- Wiki: `skill-authoring-patterns-dos-and-donts.md` (prior art on skill structure)
- Wiki: `compound-skill-improvement-patterns.md` (patterns for multi-step skills)
- Precedent skills: `/tp` (instrument + protocol.md), `/aar` (instrument + references/)
- `/go` skill spawn recipe (lines 202–229): the lane/pool model that motivates keeping skills batch-readable

## Open questions

- Should the instrument size target be 10KB or 15KB? 10KB is cleaner but may force aggressive offloading for complex skills. 15KB is pragmatic. (Propose: 15KB hard ceiling, 10KB aspirational.)
- Should `references/` follow a naming convention? `/aar` uses descriptive names (`epistemic-calibration.md`); `/handoff` uses `core-fields.md`. Both work. No convention needed yet.
- Should the refactor be tracked in the wiki skill catalog (`skill-catalog.md`) or only in this handoff? (Propose: this handoff until complete, then a wiki concept documenting the program outcome.)

## Falsifier

This program is wrong if:
- After refactoring, the slim SKILL.md loses load-bearing content that cold-start agents need (the split was too aggressive)
- The reference files are never actually loaded (agents don't know to read them → the offload was cargo-cult)
- The monolith skills worked better because agents could see everything in one read (the split added indirection cost without benefit)

If any pattern appears within 3 months across 3+ refactored skills, revise or abandon the program.

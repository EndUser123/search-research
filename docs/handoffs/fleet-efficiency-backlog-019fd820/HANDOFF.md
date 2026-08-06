---
thread_id: fleet-efficiency-backlog-019fd820
parent_handoff_path: P:/docs/handoffs/skill-md-structural-validator-019fd820/HANDOFF.md
current_session_id: 019fd820-2fb5-7330-a0ab-290d5e529658
parent_session: none
current_terminal_id: grok-019fd820
produced_at: 2026-08-07T00:00:00Z
last_updated_by: 019fd820-2fb5-7330-a0ab-290d5e529658
last_updated_at: 2026-08-07T00:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: HEAD
---

# Handoff: Fleet efficiency prioritized backlog

## Objective

Implement a prioritized backlog of workspace improvements that increase
efficiency, reduce token consumption, close knowledge-to-action gaps, and
reduce constraint decay across the 72-skill fleet. Each item is measured or
measurement-ready, mapped to the four improvement framings it serves, and
ordered by leverage (how many dimensions it improves simultaneously).

## Prioritization principle

[[measurement-before-addition-principle]] — each item either has measured
evidence or begins with a measurement step. No item ships without knowing
whether the problem it addresses is real.

## Backlog

### P0 — Fix broken infrastructure (blocking, no measurement needed)

#### P0-1: Fix `claim_handoff.py` (`ModuleNotFoundError: safe_io`)

- **Problem:** `python ~/.grok/skills/handoff/__lib/claim_handoff.py` fails immediately with `ModuleNotFoundError: No module named 'safe_io'`. Every session that tries to claim a handoff hits this. Fleet-wide breakage.
- **Fix:** fix the import path in `claim_handoff.py` (likely needs `sys.path.insert` for `__lib/` or the `safe_io` module is missing/mislocated).
- **Effort:** LOW (one import fix, 10 min).
- **Framings:** A (loop compression — unblocks handoff claiming).
- **Verification:** run `claim_handoff.py --help` and confirm exit 0.

### P1 — Structural validation gate (measured: 106 defects, handed off)

#### P1-1: Build `skill_validator.py` + pre-commit hook

- **Problem:** 106 structural defects across 72 skills (49 missing version, 21 missing host, 12 over 500 lines). Description-body mismatches like ERROR-1 (8 of 9 categories listed) pass undetected at write time.
- **Handoff:** `P:/docs/handoffs/skill-md-structural-validator-019fd820/HANDOFF.md` (full rule spec, acceptance criteria, falsifier).
- **Effort:** MED (extend `script_scan.py` pattern, 15 rules, pre-commit wiring).
- **Framings:** A2 (eliminates reactive review), B1 (deterministic code), D1 (forces token awareness).
- **Dependencies:** none. Measurement complete.
- **Verification:** validator catches ERROR-1 class when run against `/insight`.

### P2 — Measurement prerequisites (unlock P3-P5)

#### P2-1: Context-budget dashboard (`context_budget.py`)

- **Problem:** no one knows which skills cost the most tokens to load. Top 5 by line count (tp 1662, design 1444, model-web 1350, www 1260, review 1166) are estimated at 8,000-12,000 tokens each, but exact counts and frequency-weighted rankings don't exist.
- **What to build:** Python script that reads all SKILL.md files, computes token count (via tiktoken or chars/4 heuristic), and ranks by token cost. Optionally weight by invocation frequency (grep session transcripts for skill name mentions).
- **Effort:** LOW (30 min — 50-line script).
- **Framings:** D2 (makes invisible cost visible), B2 (identifies trim targets).
- **Dependencies:** none.
- **Verification:** script outputs a ranked table of skills by token cost.

#### P2-2: Wiki concept retrieval-rate audit (`concept_retrieval.py`)

- **Problem:** 244+ wiki concepts exist but retrieval rate is unknown. The `/tp` critique flagged: "if pickup rate is <30%, the bottleneck is signal-to-action." We haven't measured it.
- **What to build:** Python script that reads all wiki concept slugs, greps `~/.grok/sessions/` for references to each slug after its creation date, and computes retrieval rate (referenced / total).
- **Effort:** LOW (40 min — grep wrapper with date filtering).
- **Framings:** C1 (measures knowledge-to-action gap), C4 (identifies graveyard concepts), D1 (identifies pruning targets).
- **Dependencies:** none.
- **Verification:** script outputs retrieval rate per concept and overall fleet average.

#### P2-3: Handoff-to-completion tracker

- **Problem:** handoff pickup rate is unknown. How many handoffs get picked up and closed vs how many rot?
- **What to build:** script that reads handoff frontmatter (`status: open/closed`), computes: total created, total closed, average age of open handoffs, stale rate (>30 days open).
- **Effort:** LOW (20 min — frontmatter parser + date math).
- **Framings:** C2 (measures cross-session accountability), C3 (tracks whether work gets done).
- **Dependencies:** none.
- **Verification:** script outputs handoff lifecycle metrics.

### P3 — High-leverage implementations (require P2 measurements)

#### P3-1: Skill bloat trim pass

- **Problem:** skills over 500 lines are in constraint-decay territory. Enhancement-batch history, repeated rules, and ceremony consume tokens without driving action.
- **What to do:** for each skill flagged by P2-1 (context-budget dashboard) as >5000 tokens: trim enhancement-batch notes to git history, externalize repeated rules to `reference/` files, remove ceremony steps that never change outcomes.
- **Effort:** MED-HIGH (per-skill, but each is independent — can parallelize).
- **Framings:** D1 (reduces token load), B2 (reduces constraint decay), D3 (improves leverage).
- **Dependencies:** P2-1 (need to know which skills to trim and by how much).
- **Verification:** re-run context-budget dashboard; confirm token reduction. Re-run skill_validator.py; confirm no new defects introduced by trimming.

#### P3-2: Rule consolidation pass

- **Problem:** multiple skills repeat the same rules ("verify before done," "commit after logical unit," "re-read before edit"). Each duplication costs tokens.
- **What to do:** grep all SKILL.md files for repeated instruction patterns (≥3 skills share the same rule text). Externalize to `reference/workspace-rules.md`. Replace each in-skill occurrence with a one-line reference.
- **Effort:** MED (grep + manual extraction + per-skill edit).
- **Framings:** B3 (reduces duplication), D1 (token savings), D3 (improves leverage).
- **Dependencies:** none (can start independently of P2-1, but P2-1 helps prioritize).
- **Estimated savings:** 50-200 tokens per skill invocation across the fleet.
- **Verification:** grep confirms no skill body contains the full repeated rule text after consolidation.

#### P3-3: `/www` Step 3.15 as script

- **Problem:** the workspace-counterexample check I added to `/www` is prose instructions. It should be a grep script that surfaces counterexample candidates automatically.
- **What to build:** `workspace_counterexample_check.py` — takes a wiki concept's recommendation keywords, greps `P:/.data/wiki/concepts/` for failure-pattern matches, surfaces candidates.
- **Effort:** LOW (30 min — grep wrapper with keyword extraction).
- **Framings:** B1 (deterministic code), A1 (loop compression — automates a manual step).
- **Dependencies:** none.
- **Verification:** script surfaces `[[self-improving-agent-systems-techniques-and-workspace-gaps]]` when given "counterfactual reasoning" as input.

### P4 — Systemic improvements (require P2 + P3 complete)

#### P4-1: `/www` + `/tp` fusion (research-critique mode)

- **Problem:** improvement cycles require 7 phases (www → ask → tp → implement → review → www → tp). `/tp` kills 33-50% of `/www` output. If `/www` ran the counterexample check internally (Step 3.15 as script from P3-3) and the workspace-applicability gate (Round 3.25) before persisting, `/tp` becomes redundant for the findings those gates catch.
- **What to do:** wire P3-3 (counterexample script) into `/www` Phase 3 so it runs automatically before persistence. Document that `/tp` is only needed for framing-level critique, not finding-level filtering.
- **Effort:** LOW (wiring + documentation, once P3-3 exists).
- **Framings:** A1 (cuts loop from 7 to 4 phases), B4 (moves check into code).
- **Dependencies:** P3-3.
- **Verification:** a `/www` run that would have proposed a known-failure pattern gets it caught by Step 3.15 without needing `/tp`.

#### P4-2: Wiki concept lifecycle tracking (`last_retrieved`)

- **Problem:** concepts have no `last_retrieved` field. The graveyard is invisible.
- **What to do:** add `last_retrieved` to wiki concept frontmatter. A hook or script updates it when the concept slug is referenced in a session. Concepts not retrieved in 90+ days → flagged stale. 180+ → prune candidates.
- **Effort:** MED (frontmatter schema update + retrieval-tracking hook).
- **Framings:** C4 (makes graveyard visible), D1 (identifies pruning targets).
- **Dependencies:** P2-2 (retrieval-rate audit establishes the baseline).
- **Verification:** a concept referenced in a session gets its `last_retrieved` updated automatically.

#### P4-3: Wiki concept → enforcement gate pipeline

- **Problem:** documented failure patterns in wiki concepts don't become blocking gates. The hivelore pattern (capture → sensor → block) adapted to our wiki would close this loop.
- **What to do:** add optional `enforcement:` field to wiki concept frontmatter specifying a grep/AST pattern. A hook reads these and generates sensors that flag when the anti-pattern appears in session output or code.
- **Effort:** HIGH (schema change + hook + sensor generation).
- **Framings:** B4 (deterministic enforcement from knowledge), C4 (closes knowledge-to-action loop).
- **Dependencies:** P2-2 (need to know which concepts are worth instrumenting).
- **Verification:** a wiki concept with `enforcement:` field catches the anti-pattern in a test commit.

### P5 — Creative enhancements (independent, lower urgency)

#### P5-1: Cross-domain analogy injection

- **What:** when the operator is stuck, surface analogies from other domains (biology, law, manufacturing, game design). Currently `/tp` exploration mode does this on explicit invocation only.
- **Effort:** MED.
- **Framings:** D (creativity increase).

#### P5-2: "What if the opposite were true?" steelman prompt

- **What:** for any architectural decision, automatically generate the steelman of the rejected option.
- **Effort:** LOW (prompt pattern).
- **Framings:** D (creativity + decision quality).

#### P5-3: Cross-session connection surfacing

- **What:** extend `/notice` T7 trigger to surface connections across session handoffs, not just wiki concepts.
- **Effort:** MED.
- **Framings:** D (creativity + pattern detection).

#### P5-4: `propagation_check.ps1` as git hook

- **What:** automate the manual propagation check that runs after skill rename/delete.
- **Effort:** LOW (hook wiring).
- **Framings:** B1 (deterministic code), A3 (eliminates manual step).

#### P5-5: Ceremony audit

- **What:** find procedural steps in skills that never change outcomes (always skipped or always produce the same result).
- **Effort:** MED (requires session transcript analysis).
- **Framings:** D4 (removes ceremony), A3 (streamlines workflows).

## Dependency graph

```
P0-1 (fix claim_handoff.py)        → independent, do first
P1-1 (skill_validator.py)          → independent, measurement complete
P2-1 (context-budget dashboard)    → independent, unlocks P3-1
P2-2 (wiki retrieval audit)        → independent, unlocks P3-3, P4-2, P4-3
P2-3 (handoff completion tracker)  → independent
P3-1 (skill bloat trim)            → depends on P2-1
P3-2 (rule consolidation)          → independent (P2-1 helps prioritize)
P3-3 (www counterexample script)   → independent, unlocks P4-1
P4-1 (www + tp fusion)             → depends on P3-3
P4-2 (wiki lifecycle tracking)     → depends on P2-2
P4-3 (wiki → enforcement pipeline) → depends on P2-2
P5-* (creative enhancements)       → all independent
```

## Parallelization

Items with no dependencies can be done in parallel:
- **Wave 1:** P0-1, P1-1, P2-1, P2-2, P2-3, P3-2, P3-3, P5-4 (8 items, all independent)
- **Wave 2:** P3-1 (needs P2-1), P4-1 (needs P3-3), P4-2 (needs P2-2)
- **Wave 3:** P4-3 (needs P2-2 + P4-2), P5-1, P5-2, P5-3, P5-5

## Resumption protocol

1. Read this handoff — the backlog is the source of truth
2. Read [[workspace-fleet-efficiency-improvement-inventory]] for the 4-framing analysis behind the prioritization
3. Read [[measurement-before-addition-principle]] for the principle governing implementation order
4. Pick items from Wave 1 (all independent, no blockers)
5. Each item has: problem, what to build, effort, framings, dependencies, verification

## Suggested next invocation

```
/go execute P0-1 + P2-1 + P2-2 from fleet-efficiency-backlog — fix claim_handoff.py,
build context-budget dashboard, build wiki retrieval-rate audit (all independent, all measurement-first)
```

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-07 | 019fd820 | created |

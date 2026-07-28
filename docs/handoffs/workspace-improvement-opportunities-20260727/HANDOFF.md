---
thread_id: f3b4c5d6-7e8f-4a9b-0c1d-2e3f4a5b6c7d
parent_handoff_path: none
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T19:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d85f36c
---

# Workspace improvement opportunities: 8 extractions, measurements, and consolidations from fresh-lens scan

## Objective

Act on the 8 improvement opportunities identified by the /tp fresh-lens scan (glm-5-2), prioritized by leverage. The keystone is #1 (wiki-gate extraction); all other decompositions become easier once the shared-library pattern is established.

## Status

OPEN — opportunities identified and verified, implementation not started.

## Read-first list

1. `P:/.data/wiki/concepts/workspace-improvement-opportunities-20260727.md` — the full opportunity catalog with evidence
2. `P:/.data/wiki/concepts/routine-skill-improvement-cadence.md` — the cadence that would make these scans routine
3. `P:/.data/wiki/concepts/wiki-integrated-skills-query-save-pattern.md` — documents the wiki-gate pattern per-skill
4. `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` — mandates code-enforced gates

## Verified facts

- [FACT] Wiki-gate pattern appears in 15 skills — receipt: Select-String across all SKILL.md files
- [FACT] No shared `__lib/wiki_gate.py` exists — receipt: grep across all .py files → 0 matches
- [FACT] Evidence-tier system exists only in /why — receipt: grep for tier definitions across SKILL.md files
- [FACT] Step 0.5 hit rate never measured — receipt: no instrumentation code found
- [FACT] Skill line counts: tp=819, review=743, design=718, go=643 — receipt: Get-Content | Measure-Object
- [FACT] No scheduler task exists for the routine-improvement cadence — receipt: scheduler_list empty

## Task packets (ordered by dependency — #1 first)

### OPP-01: Extract wiki-gate into shared `__lib/wiki_gate.py` (KEYSTONE)
- **goal:** Create a shared Python module that implements: (a) Step 0.5 query (qmd search + grep + receipt emission), (b) mechanical gate (canonical criteria set), (c) save-or-skip decision, (d) log append. All skills import it instead of re-implementing it.
- **in scope:** new module at `~/.grok/skills/__shared/wiki_gate.py` (or similar shared location); migrate /why first (it has no `__lib` yet)
- **out of scope:** migrating all 15 skills at once — migrate /why, /aar, /review first as proof of concept
- **files:** `~/.grok/skills/__shared/wiki_gate.py` (new); modifications to why/SKILL.md, aar/SKILL.md, review/SKILL.md
- **acceptance:** /why's Step 15 uses the shared module; the gate fires on a real failure; the query emits a receipt; the log append works
- **falsifier:** if the code version is equally gameable as the prose version, the problem is model behavior, not code structure
- **verification:** UNIT_TEST + LIVE_BEHAVIOR
- **disposition:** COMMIT_THIS_SESSION for the module + /why migration; HANDOFF for remaining skill migrations

### OPP-02: Make evidence-tier system workspace-wide
- **goal:** Extract /why's four-tier system into a shared reference that /aar, /debrief, /review, /red-team cite when labeling causal claims
- **in scope:** shared reference doc or module; tier-label additions to /aar episodes and /review findings
- **out of scope:** Stop-hook enforcement (separate task after the labels are proven useful)
- **files:** shared reference + modifications to aar/SKILL.md, review/SKILL.md
- **acceptance:** /aar's typed episodes carry tier labels; /review's findings carry tier labels; 3 real runs show reduced false-positive claims
- **verification:** LIVE_BEHAVIOR
- **disposition:** HANDOFF

### OPP-03: Instrument and measure Step 0.5 hit rate
- **goal:** Add a hit/miss counter to the Step 0.5 wiki query; log query + keywords + hit count to a structured file; report after 20 invocations
- **in scope:** instrumentation in the shared wiki_gate.py module (from OPP-01) or standalone
- **acceptance:** 20 invocations logged; match rate reported; if <10%, query broadening recommended
- **verification:** STATIC_INSPECTION (the instrumentation output)
- **disposition:** HANDOFF (depends on OPP-01 for the shared module, or can be standalone)

### OPP-04: Set up routine-improvement cadence as `scheduler_create`
- **goal:** Create scheduled tasks for monthly /skill-dev measure + quarterly /red-team on load-bearing skills
- **in scope:** scheduler_create invocations
- **acceptance:** scheduled tasks fire and produce actionable findings within 3 months
- **verification:** LIVE_BEHAVIOR
- **disposition:** COMMIT_THIS_SESSION (can be done immediately)

### OPP-05: Run /review --focus maintainability on analytical skills
- **goal:** Run the maintainability lens on /tp, /review, /design, /go (the 4 largest skills)
- **in scope:** 4 /review invocations
- **acceptance:** findings documented; extraction opportunities identified for skills >700 lines
- **verification:** STATIC_INSPECTION
- **disposition:** HANDOFF

### OPP-06: Consolidate /debrief into /aar --parallel (explore)
- **goal:** Prototype /aar --parallel using /debrief's 5-lens dispatch; run both on the same session; compare coverage
- **in scope:** /aar SKILL.md modification or /debrief evaluation
- **acceptance:** documented comparison; decision on merge vs maintain separation
- **verification:** STATIC_INSPECTION
- **disposition:** NEEDS_USER_DECISION (operator preference on skill consolidation)

### OPP-07: Cluster /close↔/aar bugs as contract drift
- **goal:** Apply root-cause clustering to the 4 close/aar bugs; if ≥3 share one root cause, propose the structural fix (shared schema + integration test)
- **in scope:** /close/__lib/close_accounting.py, /aar/__lib/output_validator.py, /aar/__lib/completion_receipt.py
- **acceptance:** clustering results documented; if confirmed, shared schema proposed
- **verification:** STATIC_INSPECTION
- **disposition:** HANDOFF

### OPP-08: Name the three-layer enforcement architecture
- **goal:** Document the existing internal enforcement taxonomy (hooks=hard, AGENTS.md=soft, validators=adaptive) as a named framework in a wiki concept
- **in scope:** wiki concept only
- **acceptance:** concept written; subsequent enforcement proposals cite specific layers
- **verification:** STATIC_INSPECTION
- **disposition:** COMMIT_THIS_SESSION

## Open decisions

### D-1: Where does the shared `__lib` module live?
- **Options:** (a) `~/.grok/skills/__shared/` (new shared dir), (b) `~/.grok/__lib/` (top-level lib), (c) inside the most mature skill (e.g., /aar/__lib/) and imported by others
- **Selection criterion:** discoverability + no circular imports
- **Current lead:** (a) — new shared dir is cleanest; follows the `__lib` convention

### D-2: Should /debrief merge into /aar?
- **Options:** (a) merge as /aar --parallel, (b) extract shared retrospective-base, (c) maintain separation
- **Selection criterion:** maintenance cost vs feature independence
- **Current lead:** (b) — extract shared base; both skills extend it with their unique dispatch models
- **Needs operator decision**

## Hard constraints

- The wiki-gate extraction must not break any existing skill's Step 0.5 behavior
- The evidence-tier extension must be additive (tier labels added, not replacing existing confidence systems)
- The scheduler task must not block or gate — it informs, not enforces

## Cross-reference couplings

- `P:/.data/wiki/concepts/workspace-improvement-opportunities-20260727.md` — the opportunity catalog
- `P:/.data/wiki/concepts/routine-skill-improvement-cadence.md` — the cadence framework
- `P:/.data/wiki/concepts/wiki-integrated-skills-query-save-pattern.md` — the pattern to extract
- All 15 skills that reference the wiki-gate pattern

## Other outstanding streams

- **Wiki-query Stop hook** — handoff at `wiki-query-stop-hook-20260727/HANDOFF.md`. READY_FOR_REVIEW.
- **AAR non-skippable enforcement** — handoff at `aar-non-skippable-enforcement-20260726-design-blocked/HANDOFF.md`. OPEN.
- **Routine skill-improvement cadence** — handoff at `routine-skill-improvement-cadence-20260727/HANDOFF.md`. OPEN.

## Explicit non-goals

- Do NOT migrate all 15 skills to the shared wiki-gate in one session — migrate 3 as proof of concept
- Do NOT merge /debrief without operator decision (D-2)
- Do NOT add Stop-hook enforcement for evidence tiers until the labels are proven useful (OPP-02 → OPP-02b)

## Resumption protocol

1. Read the opportunity catalog: `P:/.data/wiki/concepts/workspace-improvement-opportunities-20260727.md`
2. Start with OPP-01 (wiki-gate extraction) — it's the keystone
3. In parallel: OPP-04 (scheduler_create) and OPP-08 (enforcement architecture naming) are independent and quick
4. After OPP-01: OPP-02 (evidence tiers) and OPP-03 (Step 0.5 measurement) extend the shared module
5. OPP-05-07 are independent explorations that can run in any order

## Suggested next invocation

```
/go "Start with OPP-01: extract the wiki-gate into a shared __lib/wiki_gate.py module. Read P:/.data/wiki/concepts/workspace-improvement-opportunities-20260727.md for the full specification. Migrate /why first (it has no __lib yet). Then OPP-04: create scheduler_create tasks for monthly /skill-dev measure + quarterly /red-team. Then OPP-08: write the three-layer enforcement architecture wiki concept."
```

## Last user message (verbatim)

> "wiki concept and handoff"

## Epistemic labels

- [FACT] 15 skills reference the wiki-gate pattern — receipt: Select-String
- [FACT] No shared __lib module exists — receipt: grep returned 0 matches
- [FACT] Evidence tiers exist only in /why — receipt: grep across SKILL.md files
- [FACT] Line counts verified by direct measurement — receipt: Get-Content
- [INFERENCE] Wiki-gate extraction is the keystone — derived from duplication count + divergence + substrate creation
- [INFERENCE] The cadence will decay without scheduler enforcement — from the session's own rule-not-fired research
- [UNKNOWN] Whether Step 0.5 hit rate is high or low — never measured; OPP-03 resolves this

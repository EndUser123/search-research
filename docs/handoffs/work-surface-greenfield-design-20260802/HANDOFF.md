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

Consolidate overlapping work-discovery skills into a unified operator experience. Original proposal was 8→1 (`/work` replacing everything); red-team review (3 specialists, REVISE verdict) corrected this to **3→1** with a delegation-first approach: fix why `/tp session` doesn't call `/todo`, then fold `/capture` + `/friction` into `/tp session`'s evaluation layer. Keep `/harvest`, `/tasks`, `/close`, `/todo`, `/recap-grok`, `/notice` as separate skills with distinct contracts.

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

### What's designed (revised after red-team)
- **Delegation-first approach:** fix /tp session → /todo delegation before building anything new
- **3→1 scope reduction:** absorb only /capture + /friction into /tp session; keep /harvest, /tasks, /close, /todo, /recap-grok separate
- Impact/effort fields in handoff frontmatter (with rubric — not "mechanical" until rubric is defined)
- NOW/NEXT/LATER tier assignment: judgment-based (LLM reads impact/effort + session context), not formula-based

### What's not started
- Phase 0: delegation diagnosis
- All implementation phases

### Red-team findings integrated (REVISE verdict, 2026-08-02)
- RC-1: 8→1 was false headline — actual coverage was 3→1. Corrected.
- RC-2: /tp session → /todo delegation failure predicts /work failure. Addressed: delegation-first approach.
- RC-3: /harvest is event-sourced infrastructure, not a scan step. Corrected: /harvest stays separate.
- RC-4: Impact scoring subjective without rubric. Accepted: need rubric definition.
- WF-02: FINDINGS.md scan is terminal-scoped. Accepted: skip or build workspace index.
- WF-05: <5s scan unbenchmarked. Accepted: measure before claiming.

## Task packets

### Task 0: Diagnose and fix /tp session → /todo delegation
- id: WS-DELEGATION
- goal: Make /tp session actually call /todo's scan engine internally instead of requiring the operator to run both
- files: `C:/Users/brsth/.grok/skills/tp/SKILL.md` (session review protocol section), `C:/Users/brsth/.grok/skills/tp/reference/session-review-protocol.md`
- root cause to investigate: the delegation is documented in SKILL.md but doesn't fire in practice. Why? Is it a skill instruction gap, a tool availability gap, or a behavioral compliance gap?
- acceptance: running `/tp session` produces the same action list that `/todo` would produce, without the operator running `/todo` separately
- verification: run `/tp session` cold and verify the output includes coverage_scan results
- estimate: S (30 min — may be a one-line instruction fix or may need a structural hook)

### Task 1: Define impact/effort rubric + add to frontmatter
- id: WS-RUBRIC
- goal: Define what H/M/L impact and S/M/L effort mean concretely, then add fields to handoff frontmatter
- files: `C:/Users/brsth/.grok/skills/handoff/references/core-fields.md`, rubric doc (wiki concept or AGENTS.md section)
- rubric draft: Impact H = blocks other work or unblocks a high-value capability; M = improves a working capability; L = nice-to-have. Effort S = <30 min; M = 30-120 min; L = >2h or multi-session
- acceptance: coverage_scan.py reads and displays impact/effort; rubric is documented and referenced
- verification: `python ~/.grok/skills/close/__lib/coverage_scan.py` shows impact column
- estimate: M (1h)

### Task 2: Fold /capture + /friction into /tp session evaluation
- id: WS-FOLD
- goal: Merge transcript scanning from /capture (7 categories) and /friction (2 modes) into /tp session's existing transcript scan
- files: `C:/Users/brsth/.grok/skills/tp/SKILL.md`, `C:/Users/brsth/.grok/skills/tp/reference/session-review-protocol.md`; mark /capture and /friction as deprecated
- in scope: /capture's 7-category routing (wiki/handoff/harvest), /friction's 2 modes (interaction problems + automation gaps)
- out of scope: /harvest (stays separate), /tasks (stays separate), /close (deprecated by /close-check)
- acceptance: `/tp session` produces FRICTION + IMPROVEMENT findings that /capture and /friction would have produced
- verification: compare finding output to a /capture run on the same session
- estimate: M (1h)
- risk: god-function if all categories are scanned in one LLM pass — decompose into sub-scans if output exceeds limits

### Task 3: Benchmark scan time
- id: WS-BENCHMARK
- goal: Measure actual scan time of coverage_scan + 6 steps on 176 handoffs; set realistic target
- files: `P:/tmp/benchmark_scan.py` (new, temporary)
- acceptance: measured wall-clock time documented; performance target is evidence-based, not aspirational
- verification: script runs and produces timing output
- estimate: S (15 min)

## Open decisions

### Decision 1: Is /work needed at all? (RESOLVED by red-team)
- Original proposal: build /work as new skill
- Red-team finding (ARCH-3): /tp session → /todo delegation already failed; /work is the same pattern
- **Revised approach:** fix the delegation first (Task 0). If /tp session successfully calls /todo, the unified view works without /work. Only build /work if the delegation fix is insufficient.
- Status: delegation-first

### Decision 2: Should /notice stay separate? (RESOLVED)
- **Answer: yes.** /notice is ambient (fires automatically); /tp session is operator-invoked. Different trigger mechanisms. Red-team confirmed.

### Decision 3: Impact rubric definition (NEW — from red-team RC-4)
- Draft rubric: H = blocks other work or unblocks high-value capability; M = improves working capability; L = nice-to-have
- Needs operator approval before implementation
- Status: pending operator input

## Hard constraints

- Do NOT create a JSON work store — grep on .md handoffs works; frontmatter fields are sufficient (operator + red-team confirmed)
- Do NOT absorb /harvest — it is event-sourced infrastructure with 81 tests, not a scan step (red-team RC-3)
- Do NOT absorb /tasks — it is a cross-tool contract serving Claude Code, Codex, and Agy (red-team F4.1)
- Do NOT claim "mechanical" NOW/NEXT/LATER without a rubric — impact scoring is subjective until defined (red-team RC-4)
- Do NOT claim <5s scan time without benchmarking — measure first (red-team WF-05)
- Do NOT remove skills without marking them deprecated first — compatibility aliases for muscle memory
- Fix the /tp session → /todo delegation BEFORE building any new skill — the delegation failure predicts the new skill's failure (red-team ARCH-3)

## Cross-reference couplings

- `session-review-skill-division-20260801` → boundary decisions (3-skill division) that `/work` supersedes by consolidating further
- `tp-parallel-panel-dispatch-20260801` → the tp_dispatch.py work that motivates better work discovery
- `premature-recommendation-pattern-20260801` → the AGENTS.md rule that should apply when evaluating whether to merge vs preserve skills

## Explicit non-goals

- Do NOT build `/work` as a new skill unless Task 0 (delegation fix) is insufficient
- Do NOT merge skills that produce artifacts (`/handoff`, `/wiki`) — different output type
- Do NOT merge skills that produce research (`/www`) — different output type
- Do NOT merge quality gates (`/review`, `/check`) — different lifecycle stage
- Do NOT absorb `/harvest` (event-sourced state machine) or `/tasks` (cross-tool contract)
- Do NOT add ambient session-start hooks in this handoff — separate enhancement

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T16:30 | 019fb177... | created — original 8→1 /work proposal |
| 2026-08-02T17:50 | 019fb177... | revised — red-team REVISE verdict integrated; 8→1 corrected to delegation-first 3→1; /harvest and /tasks kept separate; impact rubric required; /work deferred pending Task 0 |

---
thread_id: tp-deferred-opportunities-20260727
parent_handoff_path: none
current_session_id: 019fa5a1-0446-7e02-9766-bd2457ee58c3
current_terminal_id: grok-build-primary
produced_at: 2026-07-27T22:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ac63013e8a17b30995e22f887142c2046f873659
---

# Handoff — Deferred /tp prioritized opportunities (O-1, O-6, O-8, O-10)

## Objective

Act on the 4 deferred improvement opportunities from the session 019fa5a1 `/tp`
exploration pass. These are workspace-wide improvements surfaced by the /tp
critique that were intentionally deferred because each needs design work or
instrumentation that exceeds a single turn. The operator reviewed the deferral
rationale and approved handing them off rather than doing them in-session.

## Why this exists

The `/tp` exploration (session 019fa5a1) surfaced 10 opportunities (O-1 through
O-10). The session shipped O-2/O-3/O-4/O-5 (small fixes that proved the
pattern) and the wiki concepts. Five items remain deferred. This handoff
captures the 4 that have no existing handoff home (O-7/GAP-4 is already covered
by `external-llm-critique-evidentiary-discipline-20260727`).

## The 4 deferred opportunities

### O-1: Unified claim-lifecycle framework

- **What:** a workspace-wide framework that places mechanical gates at four
  claim-lifecycle stages: claim creation, verification, propagation, and
  supersession. The small fixes shipped this session (O-3/O-4/O-5) are instances
  of this pattern; the framework would generalize them.
- **Why deferred:** needs design. The instances prove the pattern before
  committing to the framework. Building the framework before the instances are
  validated risks over-abstracting.
- **Resumption trigger:** when a 3rd or 4th instance of the claim-lifecycle
  pattern is observed, the framework is justified. Count current instances:
  the receipt rule (creation), the scope-matching rule (verification), the
  subagent-synthesis gate (propagation), the wiki retirement check (supersession).
  That's 4 — the framework may already be justified.
- **Suggested approach:** `/design` or `/tp` on the framework shape, then write
  as a wiki concept + AGENTS.md rule.

### O-6: Handoff auto-supersede

- **What:** when a new handoff is created for a recurring workstream, the prior
  handoff(s) for the same topic should be automatically marked `status: superseded`
  with a `superseded_by` pointer. Currently, the `/handoff` skill creates new
  files without superseding priors — producing N files for one recurring
  workstream (documented in `P:/.data/wiki/concepts/handoff-fragmentation-under-recurrence.md`).
- **Why deferred:** skill-level change to `/handoff`. Needs its own `/go` turn
  because it touches the skill's core file-creation logic and requires a
  topic-matching heuristic (fuzzy title match? thread_id inheritance?).
- **Resumption trigger:** when handoff fragmentation causes a triage problem
  (a fresh session can't tell which of N handoffs is current). The workspace
  currently has 168 handoffs (137 open) — fragmentation is already a problem.
- **Suggested approach:** `/refine` the topic-matching heuristic, then `/go`
  implement the auto-supersede logic in `/handoff`.

### O-8: Authority-output channel unification rule

- **What:** an AGENTS.md rule: "when adding an authority/security boundary,
  audit every consumer-visible output path; all must delegate to the authority
  result, or the boundary is decorative." This is GAP-5 from the
  external-llm-critique handoff — named in the maker-checker wiki concept but
  not yet a standalone rule.
- **Why deferred:** can pair with O-1 (the unified claim-lifecycle framework).
  Not urgent as standalone because the close-authority case (CORR-002) is the
  only known instance.
- **Resumption trigger:** when a 2nd instance of the split-output anti-pattern
  is observed (JSON authoritative, text stale). Currently N=1 (CORR-002 in
  close-authority).
- **Suggested approach:** write as an AGENTS.md rule + wiki concept. Can be
  batched with O-1 if the framework design includes an output-channel audit step.

### O-10: Measure opt-in firing rates

- **What:** instrument the opt-in techniques (/tp, /wargame, /challenge, /red-team,
  AGENTS.md rules) to measure how often they actually fire under closure pressure.
  The `assumption-auditing-and-unknown-unknown-discovery` wiki concept identified
  that opt-in techniques don't fire reliably — but we have no quantitative data
  on firing rates.
- **Why deferred:** needs 5+ sessions of instrumentation data to be meaningful.
  Single-session measurement is noise.
- **Resumption trigger:** after 5 sessions with instrumentation in place. The
  instrumentation itself (a hook or log that records when an opt-in technique
  was available but not invoked) needs to be built first.
- **Suggested approach:** build a lightweight SessionEnd hook that logs
  available-but-not-fired techniques, accumulate 5 sessions, then analyze.

## O-7 cross-reference (already covered)

O-7 (production-wiring gate) is the same as GAP-4 in
`P:/docs/handoffs/external-llm-critique-evidentiary-discipline-20260727/HANDOFF.md`.
Do not create a duplicate — act on GAP-4 there. Revision 2 of that handoff
notes GAP-4 is the only gap with no partial wiki coverage.

## Read-first list

1. This handoff
2. `P:/.data/wiki/concepts/handoff-fragmentation-under-recurrence.md` — the fragmentation problem O-6 fixes
3. `P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md` — the opt-in firing problem O-10 measures
4. `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` — the enforcement-code rule O-8 extends
5. `P:/docs/handoffs/external-llm-critique-evidentiary-discipline-20260727/HANDOFF.md` — GAP-4/GAP-5 (O-7/O-8)
6. `P:/docs/handoffs/challenge-skill-design-20260727/HANDOFF.md` — the /challenge skill that would benefit from O-10 data

## Verified facts

- [FACT] The operator reviewed the 5 deferred items and approved handing them off rather than doing them in-session (verified: the turn preceding `/wiki` — operator asked "should we do any of these now or put them in handoff?").
- [FACT] O-7 and GAP-4 cover the same work (verified: both describe a production-wiring gate for enforcement claims — O-7 in the /tp prioritization, GAP-4 in the external-LLM-critique handoff).
- [FACT] The workspace has 168 handoffs with 137 open (verified: `/handoff list` output this session).
- [FACT] O-2/O-3/O-4/O-5 were shipped this session (verified: session summary — AGENTS.md commits dd4b2c4 + 71304e3, wiki concepts written).

## Dependencies

- **Requires:** nothing — each opportunity is independent
- **Blocks:** nothing — these are improvements, not blockers
- **Non-blocking to:** each other and to all other open workstreams

## Suggested priority

1. **O-6 (handoff auto-supersede)** — highest impact. The 168-handoff clutter is an active triage cost every session. The fragmentation wiki concept is already written; the implementation is the gap.
2. **O-1 (claim-lifecycle framework)** — may already be justified (4 instances observed). Worth a `/tp` exploration to validate before committing.
3. **O-8 (authority-output rule)** — can batch with O-1. Low urgency (N=1 instance).
4. **O-10 (firing-rate instrumentation)** — longest lead time (needs 5 sessions of data). Start the instrumentation early so data accumulates.

## Falsifier

This handoff would be wrong if: (a) any of these opportunities were already shipped in a different session since `ac63013` — check `git log --oneline` for commits touching `/handoff`, AGENTS.md, or the wiki; (b) the operator's priorities changed — the suggested priority order is an inference from the session's focus, not an operator directive.

## Last user message (verbatim)

> "/handoff" (auto-update mode — no specific topic named)

## Epistemic labels

- [FACT] The 4 opportunities and their deferral rationales are from the /tp exploration pass in session 019fa5a1.
- [FACT] O-7/GAP-4 overlap is verified by reading both handoffs.
- [INFERENCE] The suggested priority order (O-6 first) is based on active triage cost (168 handoffs), not operator directive. The operator may reorder.
- [INFERENCE] O-1 "may already be justified" is based on counting 4 instances of the claim-lifecycle pattern — this count should be verified before committing to the framework.

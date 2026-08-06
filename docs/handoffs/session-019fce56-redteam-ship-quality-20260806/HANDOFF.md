---
thread_id: session-019fce56-redteam-ship-quality
parent_handoff_path: P:/docs/handoffs/session-019fce56-kb-research-ship-20260805/HANDOFF.md
current_session_id: 019fce56-da32-79c3-85f1-1ff2d6677580
parent_session: 019fce56-da32-79c3-85f1-1ff2d6677580
current_terminal_id: grok-main
produced_at: 2026-08-06T01:00:00-06:00
last_updated_by: 019fce56-da32-79c3-85f1-1ff2d6677580
last_updated_at: 2026-08-06T01:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: see commits below
---

# Handoff — Session 019fce56 (part 2): /red-team cleanup, ship-py investigation, wiki quality improvements

## 1. Objective

Three work streams from the second half of session 019fce56:
1. Complete /red-team propagation cleanup (deleted skill → /risks everywhere)
2. Investigate why /ship-py was marked SUPERSEDED — RCA + field research
3. Improve wiki entry quality based on the RCA's behavioral failure analysis

## 2. Status

CLOSED — all work committed and pushed. The improvements are prose-level
(added to /www and /why SKILL.md); the structural enforcement gap (no
hook/validator for the new fields) is noted as a future workstream.

## 3. Producing context

- **Date:** 2026-08-05 to 2026-08-06
- **Session:** 019fce56-da32-79c3-85f1-1ff2d6677580
- **Host:** Grok Build

## 4. Read-first list

1. `P:/.data/wiki/concepts/ship-pipeline-enforcement-field-solutions-2026.md` — field research on pipeline enforcement
2. `P:/.data/wiki/concepts/llm-overconfidence-documentation-as-truth-bias-field-solutions-2026.md` — field research on RCA behavioral failures
3. `C:/Users/brsth/.grok/skills/www/SKILL.md` — the I-CALM + primary-source + evidence-basis additions
4. `C:/Users/brsth/.grok/skills/why/SKILL.md` — the I-CALM + Tier 3 cap additions
5. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` — root cause pattern

## 5. Verified facts

- [FACT] /red-team deleted; /risks absorbed its procedure. All 160 references across 52 wiki concepts + 13 skill files updated to /risks. Commits: 84acde7, 49468cc, ad763d3, a663cfb, 51c4993 (P:\ repo), plus .grok repo equivalents.
- [FACT] PreToolUse ship phase-state gate hook already exists (commit 5c1e1b0, `PreToolUse_ship_phase_gate.py`). The ship-py SUPERSEDED header overstates the problem — the hook covers the enforcement gap.
- [FACT] /ship is not working properly (operator statement) — the operator is testing variants. This was NOT investigated from the operator's perspective.
- [FACT] I-CALM prompting pattern (arXiv:2604.03904) added to /www and /why — zero infrastructure cost, shifts behavior toward abstention.
- [FACT] Primary-source verification rule added to /www Phase 2.5b: secondary citations capped at [INFERENCE]. To upgrade to [FACT], must read original source during the run.
- [FACT] Evidence-basis + tested fields added to /www Round 3.25 applicability table.

## 6. Current state

All work committed. Both repos have unpushed commits (see git log).

## 7. Task packets

### AC-01: Structural enforcement for wiki quality fields (FUTURE)
- **Goal:** add a validator or hook that checks wiki concepts for `primary_source`, `evidence_basis`, and `tested` fields before write is allowed
- **Files:** potentially `P:/.data/wiki/scripts/validate_wiki_entry.py` (currently missing), or a PreToolUse hook
- **Acceptance:** wiki write blocked if recommendations lack evidence_basis or tested labels
- **Falsifier:** the validator becomes theater (always passes)

## 8. Open decisions

- Whether the pipeline enforcement concept (`ship-pipeline-enforcement-field-solutions-2026`) should replace the existing `ship-pipeline-enforcement-pretooluse-phase-state-hooks` or supplement it. The newer concept has more field evidence; the older has the implementation details.

## 9. Hard constraints

- Do NOT delete the two /www research wiki concepts even though one was produced for the wrong question — both have standalone value.

## 10. Cross-reference couplings

- `P:/docs/handoffs/session-019fce56-kb-research-ship-20260805/HANDOFF.md` — part 1 of this session
- `P:/docs/handoffs/ship-py-hardening-20260805/HANDOFF.md` — prior ship-py work
- Wiki concepts: `ship-pipeline-enforcement-pretooluse-phase-state-hooks`, `ship-py-phase-fragmentation-llm-controlled-continuation`

## 11. Other outstanding streams

See the 5 dedicated handoffs from part 1 of this session:
- skill-script-defects-cleanup-20260805
- stale-handoff-cleanup-20260805
- review-findings-cleanup-20260805
- harvest-obligations-20260805
- scanner-to-handoff bridge (design doc at P:/docs/designs/2026-08-05-scanner-to-handoff-bridge-design.md)

## 12. Explicit non-goals

- Do NOT rebuild /ship without first investigating what's broken (AC-02)
- Do NOT remove the SUPERSEDED headers without correcting them (AC-03)

## 13. Resumption protocol

1. Read the two /www wiki concepts for context
2. Check what the operator wants: fix /ship, build the validator, or correct the headers
3. The I-CALM additions are live — test whether they actually improve /www and /why output quality over the next few sessions

## 14. Suggested next invocation

`/todo` to prioritize AC-01 through AC-03 against the existing backlog

## 15. Last user message (verbatim)

> "/handoff"

## 16. Epistemic labels

- [FACT] all commits listed above — verified by git log
- [FACT] PreToolUse hook exists — verified by Test-Path
- [INFERENCE] the I-CALM additions will improve quality — from one paper, untested on this workspace

## 17. Suggested skills for next session

- `/check` — verify the I-CALM + primary-source additions don't break /www or /why execution
- `/go` — implement AC-01 (structural validator) if the operator prioritizes it
- `/why` — investigate why /ship isn't working (AC-02)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-06T01:00 | 019fce56... | created — second half of session covering red-team cleanup, ship-py investigation, wiki quality improvements |

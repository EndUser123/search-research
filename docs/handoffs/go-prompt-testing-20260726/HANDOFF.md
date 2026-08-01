---
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_by: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_at: 2026-07-26T22:02:40.921048
parent_session: none
produced_at: 2026-07-26T22:02:40.921048
status: open
handoff_type: investigation
---
# Handoff: /go Prompt Testing (TDD for Prompts)

**Thread ID:** go-prompt-testing-20260726
**Created:** 2026-07-26
**Parent handoff:** none
**Status:** READY_FOR_IMPLEMENTATION

## Problem

The `/go` SKILL.md is itself a prompt. We've been optimizing it by reasoning and operator feedback, but never by building a golden dataset and scoring it. The delegation-packet classifier was data-validated via transcript scan; the prompt enhancement layer hasn't been validated the same way.

## Situation

The wiki concept [[advanced-prompting-patterns-for-ai-agents]] documents "TDD for prompts": define success criteria, build a 10-50 case golden dataset, score behavior against it, gate changes on eval scores. The "From Plan to Action" paper (Liu et al., 16,991 trajectories) applies this to agent plan compliance. We should apply it to `/go`'s routing and enhancement behavior.

## Objective

Create a 10-case golden test set of `/go` invocations covering: vague, delegation-packet, architectural, review, refactor, explore, plan-execute, ship-check, parallel-change, and single-file-change. Each case specifies expected: profile, horsepower packs, delegation-packet score, prompt-enhancement gaps detected. Score `/go`'s actual behavior against this set.

## Scope

- **In scope:** test set definition, scoring script, initial baseline run
- **Out of scope:** CI integration (defer), automated regression gating (defer)

## Acceptance criteria

1. 10 test cases defined as structured JSON with input prompt + expected behavior
2. Cases cover all 10 `/go` profiles at least once
3. Scoring script runs `/go` classification on each case and compares to expected
4. Baseline run produces a score report showing pass/fail per case
5. Cases include at least 3 delegation-packet prompts (score ≥4) and 3 vague prompts (score ≤1)

## Evidence

- Wiki: `P:/.data/wiki/concepts/advanced-prompting-patterns-for-ai-agents.md` § "Prompt testing (TDD for prompts)"
- Paper: "From Plan to Action" (arxiv 2604.12147) — plan compliance metrics
- Transcript scan: `P:/tmp/go_learning_evidence.json` — 66 `/go` invocations across 21 sessions
- Current `/go` SKILL.md: `C:/Users/brsth/.grok/skills/go/SKILL.md` (991 lines)

## Constraints

- Test cases must be realistic (derived from actual transcript patterns, not synthetic)
- Scoring must be deterministic (no LLM-in-the-loop for the scoring itself)
- Cases must be runnable without actual code changes (test the routing, not the execution)
- Do NOT add ceremony — the test set validates that ceremony IS stripped when appropriate

## Next executable action

1. Extract 10 representative prompts from `P:/tmp/go_learning_evidence.json` (the transcript scan already has them)
2. For each, manually label the expected: delegation-packet score, profile, packs, enhancement gaps
3. Write a scoring script at `P:/tmp/go_prompt_eval.py` that runs the 6-signal classifier on each case
4. Run baseline and produce a score report
5. Commit the test set to `P:/tmp/go_prompt_eval/` for future regression checking

## Open questions

- Should the prompt enhancement gap analysis be scored mechanically or via LLM? (Mechanical is more reliable but may miss subtle gaps.)
- Should this be a hook (runs on every `/go` invocation) or a standalone script? (Standalone for now.)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-26T22:02 | 019f8b39-95e... | backfilled session_id from transcript scan |

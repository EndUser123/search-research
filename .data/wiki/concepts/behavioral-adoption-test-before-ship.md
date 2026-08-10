---
title: "Behavioral adoption test before ship: test LLM behavior pre-ship, not post-ship metric"
created: 2026-08-10
source: session-2026-08-09 (AAR tacit gap #2 + /risk pre-Phase-2 gate #1)
tags: [behavioral-test, llm-behavior, pre-ship-gate, adoption-metric, design-validation, transferable-pattern, skill-design]
summary: >
  When a design's value depends on LLM behavior that's documented but not tested (e.g.,
  partner prompts reading a new sidecar file), gate ship on a behavioral test, not a
  post-ship adoption metric. A post-ship metric is a trailing indicator — by the time
  it fires, sessions have already burned on partners that ignored the change. The
  behavioral test runs one dry-run turn with the new input populated and verifies the
  LLM actually performs the expected action. Cost: ~15 min. ROI: catches the highest-
  leverage untested assumption before it ships.
agent: grok
host: grok
cognitive_load: 2
verification: observed
confidence: 0.85
half_life_days: 365
last_verified: 2026-08-10
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation.md
    type: extends
---

# Behavioral adoption test before ship: test LLM behavior pre-ship, not post-ship metric

## Decision context

The review-relay improvements design (ADR-011, session 2026-08-09) includes a finding-lifecycle tracking component where partner LLMs read a `findings.jsonl` sidecar file via a new `previous_findings_path` tick input field. The design's success metric includes "partner prompt adoption rate ≥95% within 30 days" — a post-ship metric measured AFTER Phase 2 ships.

The `/risk` assessment on the implementation plan surfaced this as the #1 MEDIUM risk: "the entire finding-lifecycle value depends on LLM behavior that's documented but not behaviorally tested before ship." The fix: a pre-Phase-2 behavioral adoption test — run one dry-run partner turn with `previous_findings_path` populated and verify the LLM actually reads the file.

This pattern generalizes: **any design whose value depends on LLM behavior** (not just code correctness) needs a behavioral test before ship, not just a post-ship adoption metric.

## The pattern

**Trigger:** a design or skill change introduces a new input, instruction, or prompt modification whose value depends on the LLM actually performing a specific behavior (reading a file, following a format, using a tool).

**Anti-pattern:** measure adoption via a post-ship metric ("≥95% of turns do X within 30 days"). The metric is trailing — by the time it fires, sessions have shipped with partners that ignore the change.

**Fix:** before ship, run one dry-run turn with the new input/instruction populated. Verify the LLM performs the expected action. If it doesn't, redesign the prompt/instruction BEFORE ship. Cost: ~15 min.

## Why post-ship metrics fail for LLM behavior

1. **Trailing indicator.** The metric fires after N sessions have already run with the broken behavior. Those sessions are lost value.

2. **Attribution ambiguity.** If the metric shows <50% adoption, was it the prompt, the input format, the model, or the context? The post-ship metric can't distinguish — it just says "adoption is low." The pre-ship test isolates the variable.

3. **Closure pressure.** Once the metric is post-ship, the ship decision is already made. The team rationalizes: "the metric will improve as we iterate on the prompt." But the iteration cycle is sessions, not minutes — each iteration costs a full session of low-adoption behavior.

## How to run the test

1. **Before the prompt/instruction change ships,** construct a minimal test case: the new input populated (e.g., `previous_findings_path` pointing to a real file), the partner prompt updated, a simple task.

2. **Run one partner turn** (dry-run, not production). The partner LLM receives the new input and the updated prompt.

3. **Verify the expected behavior:** did the LLM read the file? Did it produce the expected output format? Did it use the new instruction?

4. **If yes:** ship with confidence. The behavioral assumption is validated.

5. **If no:** redesign the prompt/instruction BEFORE ship. The post-ship metric would have caught this — but only after burning sessions.

## What this means for our workspace

1. **Any skill change that modifies partner prompts** needs a behavioral adoption test before the change ships, not just a post-ship adoption metric. This applies to `/review-relay`, `/review`, `/tp`, `/design` — any skill where LLM behavior is the value chain.

2. **The test is cheap** (~15 min) relative to the cost of a post-ship metric cycle (sessions of low-adoption behavior). The ROI is positive whenever the design's value depends on LLM behavior.

3. **This is distinct from code testing.** Code tests verify the function does what the code says. Behavioral adoption tests verify the LLM does what the prompt says. Both are needed; neither substitutes for the other.

4. **Encoding pattern:** the test should be a precondition gate in the implementation plan (not a recommendation). The review-relay handoff encodes it as "Pre-Phase-2 gate #1: behavioral adoption test must pass before U-5 ships."

## Falsifier

This finding is wrong if:

- **LLM behavior is reliably predictable from prompt design** — if reading the prompt is sufficient to know whether the LLM will follow it, the behavioral test is redundant. Evidence suggests this is NOT the case (LLM behavior under context pressure is the entire closure-pressure pattern family), but if a future study shows >95% predictability, the test is unnecessary.
- **The pre-ship test is more expensive than the post-ship metric** — if the test takes hours to construct and the metric takes minutes, the ROI inverts. For simple prompt changes (one new input field), the test is ~15 min. For complex behavior changes (new reasoning patterns), the test may be more expensive and the post-ship metric may be the better signal.
- **The post-ship metric catches the failure fast enough** — if adoption is measured per-turn (not per-session) and the first failing turn triggers a redesign, the trailing-indicator cost is bounded to one turn. For most workspace skills, the metric is per-session or per-N-sessions, so the cost is higher.

## Receipts

- **Session 2026-08-09 /risk assessment:** risk #1 "LLM partners ignore or misparse previous_findings_path" — MEDIUM severity, HIGH likelihood.
- **Review-relay handoff Pre-Phase-2 gate #1:** `P:/docs/handoffs/review-relay-improvements-impl-20260809/HANDOFF.md` — "Before U-5 lands, run one dry-run partner turn with previous_findings_path populated."
- **AAR tacit gap #2:** `P:\.artifacts\grok-aar\console_console_6e4287c5-bc0f-4955-823c-427b\20260809-143000\aar-report.md` § Uncaptured knowledge — "The 'behavioral adoption test before ship' pattern is reusable."

## Sources

- Session 2026-08-09 /risk scan + AAR tacit gap audit
- [[reactive-pattern-matching-and-closure-pressure]] — why LLM behavior under pressure is unpredictable (the closure-pressure mechanism that makes pre-ship testing necessary)
- [[evidence-first-default-and-needless-confirmation]] — the broader pattern of verifying before asserting

## Auto-related

- [[skill-catalog]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[testing-methodology-both-outcomes-informative]]
- [[good-tests-vs-coverage-tests-the-mutation-discriminator]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]


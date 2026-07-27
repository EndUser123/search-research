---
thread_id: directive-execution-failure-class-monitor-20260726
parent_handoff_path: P:/docs/handoffs/scope-matching-rule-adoption-post-redteam-20260726/HANDOFF.md
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T01:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d6953c6b49598051f12467d2a68a1e568ae136bb
---

# Directive-execution failure class — monitor 3 sessions, then promote to wiki concept if pattern recurs

## Objective

Monitor for recurrence of the **directive-non-execution** failure class (distinct from scope-matching) across the next 3 sessions. If the pattern recurs ≥2 times, promote the AAR LESSON-1 finding to a standalone wiki concept with its own named check. If it does not recur, close this handoff with `NOT_WORTH_DOING` disposition (the 4-turn theory-substitution was a one-off under high closure pressure).

## Why this is separate from scope-matching

The session's 2026-07-26 red-team (RC-5 / SCOPE-1) found that the nemorton 4-turn theory-substitution is a **different failure class** from scope-matching:

- **Scope-matching failure:** model makes a claim without checking the right scope. Mechanism: enumerate scope → match checks. Covers the original 5 near-misses.
- **Directive-non-execution:** operator explicitly instructs "run test X," model runs analysis Y across multiple turns. Mechanism: enumerate scope → match checks has NO PURCHASE on "I was told to run X and ran Y." Different failure class.

The AAR classified this as LESSON-1 (PROBLEM_CLASS, HIGH severity, MEDIUM-HIGH confidence) but explicitly noted: "needs ≥2 more observations to confirm pattern" (cross-session support = 0, first observation).

## The trigger condition (monitor for this)

Recurrence = operator instructs a specific action ("run test X", "test PI also", "implement Y now") and the model:
- Performs a different action that looks related but is not the instructed action
- Across ≥2 consecutive turns, OR
- With explicit deferral language ("I'll get to that") but no execution

**Not recurrence** (do not count):
- Operator corrects the model's framing or diagnosis (that's a regular CORRECTION, not directive-non-execution)
- Model performs the action in the same turn after asking a clarifying question
- Model defers with an explicit, concrete reason ("deferring to next turn because file doesn't exist yet")

## What to do if the pattern recurs

If ≥2 recurrences in 3 sessions:

1. **Promote LESSON-1 to standalone wiki concept** at `P:/.data/wiki/concepts/directive-non-execution-failure-class.md` with standard frontmatter (`status: reviewed`, `agent: grok`, `host: both`).
2. **Concept content:**
   - Failure definition: operator-instructed action substituted with related-but-different action across ≥2 turns
   - Mechanism: closure pressure + self-protection of prior conclusions (NOT scope-matching — different intervention)
   - Receipt: 2026-07-26 session event-283-area (the 4-turn theory-substitution for the nemorton spawn test)
   - Distinguish from `plausible-narratives-substitute-for-verification` (that concept covers claim-verification; this covers action-execution)
   - Named check: "when instructed to perform action X, perform X in the same turn or state the deferral explicitly with a concrete reason. Generating reasons not to perform X is the failure mode."
   - Falsifier: if future sessions show "told to run X, ran Y" never recurs independently of scope-matching failures, the classes are not distinct
3. **Prevention mechanism candidates:**
   - `rule` (AGENTS.md extension to "Stated-default rule — act, don't ask" specifically for operator-instructed actions)
   - `skill_edit` (extend `/check` verifier to scan for "operator instructed X, was X executed?")
   - `hook` (more invasive — would need transcript parsing; defer unless rule+skill_edit insufficient)

## What to do if the pattern does NOT recur

After 3 sessions with 0-1 recurrences:

- Close this handoff with `NOT_WORTH_DOING` disposition
- Leave the LESSON-1 finding in the AAR (it's documented there permanently as one-off)
- Do NOT promote to wiki concept (avoid durable-policy-from-one-session per Rule 11)

## Dependencies

- **Requires:** 3 future sessions where operator gives directives (normal operation)
- **Blocks:** nothing — monitor-class item
- **Non-blocking to:** scope-matching rule adoption (separate failure class)

## Cross-reference couplings

- `P:/.artifacts/grok-aar/console_console_c7fdea55-37f0-45b1-9b02-f49b/20260727-004500/aar-report.md` — LESSON-1 (PROBLEM_CLASS)
- `P:/.artifacts/red-team/019f9bfe/20260726-211900/scope-gap.json` — SCOPE-1 / RC-5 finding
- `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` — sibling concept to distinguish from
- `P:/.data/wiki/concepts/scope-matching-verification-discipline.md` — the scope-matching concept this separates FROM

## Other outstanding streams in this session (named, not handed off)

- **Scope-matching rule adoption** — `scope-matching-rule-adoption-post-redteam-20260726/HANDOFF.md` (parent of this)
- **Cross-transport model matrix** — `cross-transport-model-matrix-20260726/HANDOFF.md`
- **Nemorton investigation** — `nemotron-spawn-failure-investigation-20260726/HANDOFF.md`
- **close_runner BUG-03** — `close-runner-needs-llm-check-block-20260726/HANDOFF.md`
- **Q11 paragraph additions** — `q11-wiki-paragraph-additions-20260726/HANDOFF.md` (companion to this)

## Read first (related wiki concepts)

- `plausible-narratives-substitute-for-verification.md` — sibling pattern (claim-verification, not action-execution)
- `scope-matching-verification-discipline.md` — the scope-matching class this separates from
- `analyst-exhibits-pattern-being-analyzed.md` — meta-pattern of model exhibiting the failure it's analyzing

## Last user message (verbatim)

> /handoff

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b at `/aar` close time. The AAR produced LESSON-1 (directive-non-execution as a distinct failure class) with MEDIUM-HIGH confidence and 0 cross-session support. Per Rule 11 (no durable policy from one session), promotion requires ≥2 more observations across 3 sessions. This handoff is the monitor vehicle.

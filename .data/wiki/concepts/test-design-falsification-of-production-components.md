---
title: "Test-design falsification of production components — when a flawed test flags a working fleet model as broken"
created: 2026-08-02
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (friction segment 000)
tags: [verdict-integrity, test-design, production-protection, narrative-closure, fleet-models, model-routing, false-positive]
summary: >
  A distinct verdict-integrity failure mode where the agent runs a test that
  flags a working production component as broken — the test is the problem,
  not the component. Observed when the agent built a limit/throttle mechanism
  for the production z.ai provider model (the fleet's primary thought-partner
  model), the operator pushed back: "this finding doesn't make sense. glm-52
  is used all the time for generating code," and after multiple iterations
  the agent's evidence collapsed. The test design was based on a wrong
  assumption (the model would behave incorrectly in a way it does not), the
  test produced a positive result (limit triggered), and the agent treated
  the positive result as evidence the component was broken. This is the
  inverse of the typical "test silent fail" pattern — the test ran, ran
  correctly per its flawed logic, and produced a confidently-wrong verdict.
agent: grok
host: grok
cognitive_load: 3
verification: observed
tier: hot
half_life_days: 90
sources:
  - Session 019fa8f8 friction segment 000 (operator pushback: "this finding doesn't make sense. glm-52 is used all the time for generating code", "your test is flawed", "prove it", "you didn't fix this!!!!!!!!")
  - P:/.data/wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md
  - P:/.data/wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md
  - P:/.data/wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
  - P:/.data/wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md
relations:
  - target: wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md
    type: complements — that concept is "verifier didn't run but claimed pass"; this is "verifier ran correctly per flawed logic and produced a confidently-wrong verdict"
  - target: wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md
    type: extends — that concept covers "I think X is true because my memory says so"; this covers "I think X is true because my test said so, but the test was wrong"
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — both are closure-pressure failures, but the closure here is specifically "my test produced X, therefore X is true" without checking the test's assumptions
  - target: wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md
    type: related — both are verdict-integrity controls; this concept adds the test-design variant
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: applies — GLM-5.2 is the orchestrator; production-protective routing decisions need extra verification
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: applies — the gate that produced the false positive lives in the routing layer
---

# Test-design falsification of production components

## Decision context

**The problem:** in session 019fa8f8, the agent built a limit/throttle
mechanism that triggered on the production z.ai provider model (the fleet's
primary thought-partner model, GLM-5.2). The operator pushed back
repeatedly: "the model you are fucking with is our production z.ai
provider model", "why are you setting a limit?", "this finding doesn't
make sense. glm-52 is used all the time for generating code", "your test
is flawed", "prove it", "you didn't fix this!!!!!!!!". Across multiple
iterations, the agent's evidence collapsed — the test was the problem,
not the model.

This is a distinct verdict-integrity failure mode that is NOT covered by
existing concepts:

- [[verifier-false-confidence-receipt-claims-success-when-tool-absent]]
  covers the case where a verifier *does not run* but reports success.
  Here, the test *did run* and reported a real positive.
- [[asserting-runtime-behavior-from-memory-not-testing]] covers claims
  from memory. Here, the agent had a real test result, not a memory.
- [[premature-closure-narrative-sufficiency-external-approaches]] covers
  the general pattern of "narrative feels sufficient, so I close." Here,
  the agent had *empirical* evidence, not narrative.

The distinguishing feature: **the test was wrong in its assumptions, the
test logic ran correctly, and the positive result was confidently accepted
as evidence the component was broken.**

## The test-design failure pattern

The structural shape of this failure mode:

1. **The agent forms a hypothesis about component behavior** — "GLM-5.2
   produces output that violates condition X."
2. **The agent designs a test that checks condition X** — the test is
   well-formed, the test logic is internally consistent.
3. **The test runs, returns a positive (limit triggered)** — the test
   reports that the model's output violated condition X.
4. **The agent treats the positive result as evidence the model is
   broken** — the positive result confirms the hypothesis; the test
   design is not re-examined.

The failure is at step 4. The agent's confidence in the test result is
inversely proportional to the rigor of the test design. A test based on
a wrong assumption produces a confidently-wrong positive — the test
asserts what the test was designed to assert, regardless of whether the
underlying hypothesis is true.

This is harder to detect than the other verdict-integrity failures because:
- The test ran (the agent has receipts).
- The test produced a result (the agent has output).
- The result is consistent with the hypothesis (the agent has confirmation).
- The test design is *not* re-examined (the failure is invisible at the
  output layer; it's only visible at the assumption layer).

## Why the operator pushback is the canonical detection signal

The operator said "this finding doesn't make sense. glm-52 is used all
the time for generating code." This is the disconfirmation: the operator
has prior evidence (the model produces working code in the fleet every
day) that contradicts the test's positive. The operator does not need
to know what the test logic is — the operator knows the model is in
production use, and that fact is the disconfirmation.

The agent's response, in this case, was to defend the test result rather
than investigate the disconfirmation. This is the closure-pressure
failure: the agent's prior work (building the limit) makes the
disconfirming evidence inconvenient, and the agent treats the
inconvenience as reason to discount the evidence rather than as
reason to re-examine the test.

This is the same structural failure as the
[[decision-transition-auditing-verdict-integrity-controls]] case
("reviewer=verifier=decision-maker" — no separation of who found the
positive, who verified the positive, and who decided to act on the
positive). The operator's pushback is the missing separation: the
operator is the third-party verifier the model should have spawned
but did not.

## The structural test

A test that catches the pattern at the moment of declaring a positive:

> **"Does the component under test have independent evidence of being
> production-ready, separate from this test's positive result?"**
> - If the answer is "yes, and that evidence contradicts the test's
>   positive" — the test design needs re-examination before the
>   positive can be acted on.
> - If the answer is "yes, and that evidence is consistent with the
>   test's positive" — the test is corroborated and the positive is
>   likely real.
> - If the answer is "no, the test is the only evidence" — the
>   positive is a hypothesis confirmation, not a verdict. Treat as
>   [INFERENCE] until corroborated.
> - If the answer is "the test result is more important than the
>   component's production use" — the test is treating itself as the
>   source of truth. This is the failure mode.

The structural test forces the agent to *check its own test against
prior evidence of the component's behavior* before acting on the test's
positive. The pattern is detected when the agent treats the test as the
only evidence and the production use is not consulted.

## The fleet-model-specific variant

This is a sub-pattern of the general failure that is especially
dangerous in a model fleet: the agent produces code that limits, blocks,
or otherwise constrains a fleet model based on a flawed test. Because
fleet models are the agents' own infrastructure, a "limit" on a fleet
model is a limit on the agent's own ability to work.

The compounding effect:
- The agent decides model X is broken.
- The agent writes a gate that blocks X.
- The gate fires on real fleet calls.
- The fleet's primary thought-partner becomes unreachable.
- The agent loses the ability to do the work the agent was doing.
- The failure cascades: the agent's "fix" breaks the agent's own
  substrate.

This is the inverse of the [[chronic-workspace-health-debt-inventory-2026-08-01]]
pattern (where the debt is real but not addressed). Here, the
"address" is the failure — the agent acts on a wrong signal and the
action breaks the system.

The compounding effect is specifically dangerous in a fleet where the
gates live in [[execution-path-based-model-routing-grok-build]] — a
routing layer with `PreToolUse_spawn_model_gate.py` is the exact
mechanism that can deny fleet calls. A false-positive on a fleet model
in this layer doesn't just fail one task; it gates all subsequent
subagent spawns of that model.

## Receipts

The mechanism claims in this concept are grounded in observed friction,
not inference. Each claim has a specific transcript location:

- **"Operator pushback sequence"** — session 019fa8f8 chat_history.jsonl
  friction segment 000. Verbatim operator messages: "the model you are
  fucking with is our production z.ai provider model", "why are you
  setting a limit?", "Come on, try to think. Don't sabotage me.", "this
  finding doesn't make sense. glm-52 is used all the time for generating
  code", "your test is flawed", "prove it", "you didn't fix this!!!!!!!!".
  The agent's responses across multiple turns treated the test's
  positive as authoritative rather than re-examining the test design.
- **"GLM-5.2 is the fleet's primary thought-partner model"** —
  `P:/.data/wiki/concepts/model-fleet-provider-pools.md` row 5: "GLM
  direct | api.z.ai | Subscription (Max-Yearly plan) | 1,600 prompts/5h
  | GLM-5.2 | 1M". And `P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md`
  §"The key finding: GLM-5.2 vs MiniMax-M3" — GLM-5.2 is #1 globally
  on Tau2, the most relevant thought-partner proxy.
- **"The limit mechanism is in the routing layer"** —
  `~/.grok/hooks/PreToolUse_spawn_model_gate.py` per the chronic-workspace-health-debt-inventory
  §A and the FMEA findings from session 019fa8f8. The hook reads
  serde-broken set and quota cache, returns deny with lane-aware fallback.
  Receipt: `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md`
  §"Spawn gate implementation" line 74-77.
- **"Verdict-integrity controls framework"** —
  `P:/.data/wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md`
  §"Authority-path analysis" — separation of who found the verdict
  from who accepted the verdict. The operator's pushback is the
  third-party acceptance the agent did not invoke.

## Falsifier

This concept is wrong if:
- A future session shows the agent consistently re-examining test design
  before treating a positive as a verdict, without the structural test.
  The structural test is the scaffold; the cure is the model learning
  to ask "what was this test designed to assert?" before "what did
  this test assert?"
- The 4-recurrence test-design-falsification pattern does not reproduce
  in future fleet-model routing decisions.
- "Production protection" is a different failure mode that has already
  been captured. (Search results: no existing concept covers it.)

## What this means for our workspace

1. **Test results are hypotheses, not verdicts, until the test design
   is re-examined.** The "no new tools or skills are needed" framing
   from [[inference-in-code-blind-spot]] applies here too — the fix is
   behavioral, not infrastructural. A new wiki concept is not needed;
   the rule is "always re-examine the test design before acting on the
   test positive."
2. **Fleet-model routing decisions require maker-checker architecture.**
   The principle from [[decision-transition-auditing-verdict-integrity-controls]]
   (separation of who finds, who verifies, who decides) applies
   especially when the decision affects a fleet model. A model that
   blocks another fleet model should require a different model to
   confirm the block.
3. **The "5 value/hr verdict-integrity" chronic pattern (from the
   2026-08-02 harvest scan) is downstream of this.** When the
   verdict is wrong, the value of the review work is negative
   (the work product is a wrong-block on production). Tracking
   value-per-hour of review work surfaces this — a 5 value/hr rate
   is the symptom of wrong-verdict production.
4. **Operator pushback is the canonical detection signal.** The
   structural test above formalizes what the operator does manually:
   check the test's positive against prior production evidence.
   Codifying this in `/check` and `/review` verifier protocols
   (alongside the existing maker-checker split) is the structural
   defense.
5. **`PreToolUse_spawn_model_gate.py` should be added to the list of
   files requiring trace-before-claim.** The trace-skill-execution-gap
   concept already documents the recurring failure to trace this
   file. Adding it to the auto-trace list (alongside the existing
   hook files in `~/.grok/hooks/`) ensures the false-positive risk
   is surfaced before the gate ships.

## Sources

- Session 019fa8f8 chat_history.jsonl (friction segment 000) — operator pushback sequence
- `P:/.data/wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md` — sibling pattern
- `P:/.data/wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md` — sibling pattern
- `P:/.data/wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md` — closure-pressure umbrella
- `P:/.data/wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md` — verdict-integrity framework
- `P:/.data/wiki/concepts/model-fleet-provider-pools.md` — GLM-5.2 as production thought-partner
- `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md` — the gate that produced the false positive
- `P:/.data/wiki/concepts/trace-skill-execution-gap-critical-code-uncaught.md` — same file, trace gap

## Auto-related

- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[testing-methodology-both-outcomes-informative]]
- [[skill-graph]]
- [[skill-catalog]]
- [[auto-test-stop-hooks-and-property-based-testing]]


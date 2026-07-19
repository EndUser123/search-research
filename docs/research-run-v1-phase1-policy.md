# Phase 1 routing policy finalization

## Verdict

`PASS_PHASE1_POLICY`

Phase 1 now uses deterministic task roles. MMX and Brave are automatically
eligible within their proven bounded read-only roles; Brave is not a generic
second search engine. Parallel MMX+Brave is opt-in through a deterministic
complementary-role or omission-risk trigger.

## Policy

- Broad external, conceptual, exploratory, candidate-generation, and general
  web research → MMX.
- Implementation, authority, repository/project, maintenance, compatibility,
  and omission-sensitive discovery → Brave.
- Local workspace/history/retained context → QMD/local.
- Mixed conceptual plus implementation or omission-sensitive consequential
  research → bounded MMX+Brave parallel wave when `allow_parallel` and a
  recognized `parallel_trigger` are supplied.
- `agy` remains restricted and unchanged.

Healthy bounded read-only routing does not request per-call human approval.
Sensitive, write, production, high-cost, circuit-override, and authority-
bearing reliance outside the evidence contract still escalate.

## Quota correction

MMX state now records shared-account scope, possible concurrent consumers, known
top-level calls for the current run, and non-attributable quota deltas. Shared
before/after percentages remain visible but are interpreted as
`indeterminate_concurrent_usage`; no per-run cost is inferred. No locking,
reservation, scheduler, or cross-terminal accounting was added.

## Evidence

The policy is supported by the completed Brave evaluation:

- Brave added useful sources in 9/10 comparisons.
- Brave changed two evaluation actions from insufficient to usable.
- Brave was strongest for implementation, authority, maintenance,
  compatibility, and omission-sensitive discovery.
- Routine parallel use was not justified.

Pure routing validation uses the 15-case corpus at
`P:/tests/research_run_v1/phase1_policy_corpus.json` and does not invoke any
provider.

Phase 2 disconfirmation, inverse-query planning, additional providers,
fallbacks, brokers, production configuration, and `agy` execution remain
deferred.

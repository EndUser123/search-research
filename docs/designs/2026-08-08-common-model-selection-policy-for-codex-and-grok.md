# Common model-selection policy for Codex and Grok

**Date:** 2026-08-08  
**Status:** Proposed for cross-orchestrator review  
**Revision:** 3 — reconciles the Grok conformance review; not yet accepted for implementation  
**Audience:** Grok Build and Codex maintainers  
**Scope:** Worker-model selection, quota/capacity pacing, benchmark evidence, and the boundary between Codex and Grok orchestration.

## Executive proposal

Codex and Grok should use one common model-selection policy, implemented
natively in each host. They should not combine their benchmark or runtime
performance evidence.

The current task already belongs to the orchestrator running it:

- A Codex task is selected by the Codex selector.
- A Grok task is selected by the Grok selector.
- A handoff between them is explicit and plan-driven, not a dynamic fallback
  or live negotiation.

The shared policy is therefore a common decision contract, not a global
cross-host model picker.

```text
task classification
  -> hard eligibility gates
  -> task-fit / verified-success floor
  -> capacity and quota pacing
  -> common selection mode
  -> selection receipt
  -> independent result verification
```

The primary objective is:

> Minimize expected time to a verified result, subject to capability,
> reliability, capacity, policy, and cost constraints.

This is an evidence-based operating objective, not an observable quantity at
selection time. The selector cannot know whether the next result will verify;
it estimates that outcome from completed historical evidence and combines it
with current capacity, rate-limit, and health signals. The actual verification
result is recorded afterward and is not used to justify the decision that was
already made.

## Current conformance status

This document defines the target policy. It does not claim that either live
selector already conforms to every rule. The latest source review found these
known gaps:

- Grok's router currently consumes p50 latency in
  `C:\Users\brsth\.grok\skills\model-quota\scripts\model_router.py`, while
  this policy targets valid-result p90.
- Grok's golden-vector verifier is structural-only and marked `SKELETON` in
  `C:\Users\brsth\.grok\skills\model-quota\scripts\golden_vectors.py`;
  the Codex executable counterpart is not present yet.
- Grok's router still uses quota-class headroom heuristics rather than the
  provider-capacity adapter defined below.
- Grok quarantine records do not yet include the full orchestrator and
  invocation scope, so the shared quarantine file is not safe as a
  cross-orchestrator authority.
- Grok's normal eligibility path currently admits `candidate` lifecycle
  records; the safe-calibration boundary below is therefore a required
  implementation correction, not an existing guarantee.
- Current receipts do not yet expose every target field in both hosts;
  missing capacity, latency, evidence, or verification values must remain
  explicit unknowns rather than being synthesized.

Until these gaps are resolved and the live paths are verified, receipts and
benchmark artifacts must describe the implementation as provisional or
non-conformant where applicable. Passing unit tests alone is not acceptance.

## What is shared and what remains separate

### Shared

Codex and Grok should share or conform to:

- candidate discoverability and model metadata;
- provider aliases and canonical model identifiers;
- capability and context metadata;
- lifecycle and policy-state vocabulary;
- task-lane definitions;
- quota/capacity model semantics and adapter output contract;
- selection-mode definitions;
- verified-success definition;
- selection-receipt shape;
- golden decision fixtures and algorithm version.

The implementations may remain native: JavaScript for Codex and Python for
Grok. The shared schema and golden vectors are the compatibility boundary.

### Separate

Runtime evidence must remain separate by the complete invocation identity:

```text
provider + model + invocation_method + orchestrator
```

Evidence should additionally be segmented by task lane and cohort where
relevant. In particular, Codex/Pi measurements must not be merged with
Grok/Pi or Grok/native-spawn measurements.

The reason is not that the policy differs. The execution conditions differ:

- injected context and system instructions;
- available tools and write restrictions;
- bridge and startup overhead;
- result-contract handling;
- parent verification and worktree/scope checks.

Discoverability may be shared. Measured success, latency, timeout, and
verification outcomes are local to the exact invocation identity.

## Task groups and selection modes

There are two primary task groups and one optional modifier.

### Mechanical/routine

Includes extraction, reading, formatting, routine verification, structured
output, and bounded low-ambiguity work. Bounded coding may use this group when
the specification is complete and the work is independently verifiable.

Selection mode: `deterministic`.

Choose the fastest eligible candidate that clears the task-fit and
verified-success floor. Latency must be measured for the exact provider,
model, invocation method, and orchestrator. Use end-to-end valid-result
latency, including bridge and contract overhead, rather than raw HTTP or
token-generation speed.

### Reasoning

Includes planning, debugging, architecture, ambiguous coding, synthesis, and
a single-model critique.

Selection mode: `weighted_pool`.

Eligible candidates receive evidence-based weights using task-lane verified
success, contract/verification outcomes, latency, capacity fitness, evidence
confidence, and freshness. A faster model should not automatically beat a
materially more reliable reasoning model.

Bounded exploration is allowed only for safe tasks and only within the
configured exploration policy. Exploration is disabled for write-capable or
otherwise high-risk work.

### Independent critique modifier

Critique is not a separate intelligence tier. It is reasoning with an
additional independence requirement.

- A single critique uses the normal reasoning pool.
- A multi-model red-team or cross-check uses `diverse_panel`.
- The panel first requires distinct provider/model families, then applies the
  normal reasoning ranking within those families.
- If fewer families are available than requested, the receipt explicitly
  discloses reduced diversity.

Diversity may override speed and cost only when independent perspective is an
  explicit objective. A provider outage or rate-limit event may also require
  switching families for resilience.

## Common eligibility gates

Ranking never happens before these gates:

1. The candidate supports the required task capabilities.
2. The context window is sufficient, including a safety margin for the
   packet and expected output.
3. The exact provider/model/invocation/orchestrator binding is configured and
   verified.
4. The provider endpoint and transport are currently usable.
5. The candidate is active and not quarantined, excluded, or awaiting an
   approval that was not granted.
6. Current quota, rate-limit, and concurrency state admits the call.
7. The candidate clears the lane-specific verified-success floor, or the task
   is explicitly admitted to the bounded safe-calibration lane. A normal
   reasoning or write-capable selection may not use the calibration exception.

The quality floor is a gate, not a universal quality ranking. Internally,
verified success is rich and includes:

- intended provider, model, transport, and orchestrator were actually used;
- the worker returned the required result contract;
- no timeout, malformed output, or transport mismatch occurred;
- verification passed when verification was defined;
- write tasks stayed within worktree and scope boundaries.

The operator can see one promotion threshold per lane, while the system keeps
the richer evidence needed to enforce it.

## Evidence hierarchy and candidate onboarding

Evidence is applied at the narrowest trustworthy scope first:

1. exact provider/model/invocation/orchestrator identity in the requested lane;
2. the same exact identity in related lanes;
3. a model-family or provider prior when exact evidence is absent;
4. a neutral cold-start prior when no defensible prior exists.

Lane-specific evidence overrides broader evidence only when it has sufficient
effective sample size and confidence. There is no universal raw-call count
that proves readiness for every lane or risk class.

Broader priors do not merge Codex and Grok runtime outcomes. They are either
static capability/provider priors or evidence already collected by the same
orchestrator under a broader, explicitly labeled cohort.

The lifecycle is an onboarding path, not a quality tier:

```text
discoverable -> candidate -> safe calibration/exploration
  -> lane-specific verified evidence -> active for that lane/risk class
```

A candidate may be calibrated on low-risk mechanical work with bounded scope,
including an isolated worktree when the calibration task writes files. This is
not a read-only requirement; it is a containment requirement. A candidate is
not automatically eligible for reasoning or write-capable work. A new, free,
or statically high-priority model must not displace an evidenced candidate
without lane-appropriate evidence.

The operator-facing promotion control may remain one threshold per lane, but
the threshold is not a universal raw-call rule and need not be five. The
implementation must count only lane-appropriate verified successes and also
enforce identity, contract, verification, timeout, and scope conditions.

## Latency rules

Latency is an optimization input, not a substitute for correctness.

- Use measured p90 valid-result latency for the exact invocation identity as
  the shared target. p50 remains useful diagnostic data, but it does not
  satisfy the target on its own. Grok's current p50-only router is therefore
  non-conformant until its accumulator and selector consume p90.
- The canonical shared evidence field is `latency.p90_ms`. Host-specific
  field names must be normalized at the evidence boundary rather than
  compared as if they were interchangeable.
- Include dispatch, startup, model response, contract parsing, and result
  normalization.
- Keep timeout, malformed-result, and verification-failure rates separate;
  do not hide them inside a latency average.
- A candidate with no trustworthy latency evidence is `provisional`; it must
  not beat a measured candidate merely because it is free or has a favorable
  static priority.
- Treat a latency difference as meaningful only when the available sample,
  posterior uncertainty, and p50/p90 interval evidence support it. Overlapping
  intervals are uncertainty, not proof that two candidates are equal; when no
  candidate has a defensible advantage, use a stable documented tiebreaker and
  record that uncertainty in the receipt. A quality confidence interval is not
  evidence of a latency interval; latency uncertainty requires latency samples
  or a clearly defined latency estimator.
- Recompute latency evidence by lane and cohort; do not copy benchmark
  latency across task types or invocation identities.

For mechanical work, latency is normally the primary ranking factor after the
gates. For reasoning work, latency modulates the evidence weight because
quality and verification success matter more.

Tie-breaking is selection-mode specific. Ordinary selection does not use
diversity as a hidden tie-breaker; diversity applies only to an explicit
`diverse_panel` request. A deterministic selector may use capacity fitness,
approved cost policy, and then a stable candidate identifier when evidence is
indistinguishable. A weighted pool remains probabilistic rather than silently
becoming deterministic.

The long-term metric to monitor is time to a verified result, not raw worker
latency. This captures the cost of failures, malformed responses, and parent
rework without requiring an automatic retry or fallback.

## Cost, subscription, and quota rules

Monetary cost and quota capacity are separate dimensions.

### Subscription-backed pools

Grok, GLM, MiniMax, Luna, and other approved flat-rate or regenerating
subscription pools have effectively zero marginal monetary cost for an
individual call. They should be used when they fit the task and have adequate
live capacity. A slower free model should not automatically win merely because
it is free.

Historical operator experience that GLM, MiniMax, or Luna rarely exhausts is a
useful prior, not a permanent exemption from live monitoring.

### OpenCode Go and other renewable quotas

OpenCode Go is also zero marginal monetary cost, but its usable quota is a
capacity constraint. Use it when its quota is available and the model fits;
preserve it only when forecasted demand could exhaust the quota before reset
or when it is materially better for a task with no adequate substitute.

Do not create an arbitrary permanent “reasoning reserve” when observed usage
shows the pool is unlikely to exhaust.

### Free and rate-limited routes

Free is a tiebreaker when speed, quality, and capacity are comparable. A free
route that is materially slower or more failure-prone is not preferred merely
because its dollar cost is zero.

NVIDIA-style unlimited-but-rate-limited providers have no ordinary quota
percentage to rank. Their capacity is represented by current rate-limit,
concurrency, queue, and recent 429 health.

### Pay-per-use routes

Pay-per-use routes are allowed when they satisfy an explicit budget policy.
The initial operator preference is that a task may cost approximately one cent
if the route is materially useful.

Automatic use requires:

- a reliable provider price or bounded cost estimate;
- a bounded prompt/output envelope;
- an estimated cost at or below the configured per-task cap;
- no violation of a broader daily or monthly spending cap.

The approximately $0.01 allowance is a policy parameter, not a live claim
that a pay-per-use route is currently registered or cost-tracked. It remains
dormant until a provider has an explicit route, price/cost-reporting adapter,
and spending-limit enforcement.

Unknown cost is not treated as zero. Token and cost fields are recorded only
when actually reported or reliably estimated from bounded provider pricing.

## Provider capacity model contract

Capacity is not one universal percentage. Each provider adapter must declare
which capacity model it can observe:

This is a forward specification and an implementation gate. The current Grok
`_quota_headroom()` function is a type-based placeholder, and loading the
quota cache in `pick_model.py` does not make that cache part of router scoring.
The current Codex quota assessment also contains provider defaults, but those
defaults are not a substitute for this shared adapter contract.

- **windowed units:** tokens, requests, or another provider-defined unit with
  remaining amount and reset time;
- **monetary budget:** a spend balance or budget with a defined accounting
  period;
- **rate-limited only:** no known remaining pool, but observable rate-limit,
  concurrency, queue, or retry-after signals;
- **multi-pool:** several independently limiting windows or pools;
- **unknown:** no trustworthy remaining, reset, or rate signal is available.

The normalized adapter result should expose, when available:

```text
capacity_kind
usable_now
capacity_risk
expected_wait
retry_after
rate_limit_state
concurrency_state
remaining + unit
reset_at
projected_exhaustion
observed_at
source and freshness
unknown_reason
```

These fields preserve provider semantics; they do not make unlike units
numerically comparable. A dollar balance is not a token quota, and a 429 is
not proof that a quota is zero. If remaining or reset data is unavailable, the
selector must represent an explicit rate-limited or unknown state and must not
invent a burn rate. Unknown or stale capacity is neither unlimited nor
exhausted: it may permit an already-approved, bounded non-spend call when
current route health admits it, but it provides no pacing advantage and must
not authorize unbounded use or scarcity-sensitive spending. A confirmed
retry-after or exhaustion signal is honored until its stated expiry or a
fresh provider observation.

For `multi-pool` providers, each limiting window remains a separate record
with its own unit, remaining value, reset, and source. The selector may use the
most restrictive admissibility result for the requested task, but it must not
collapse unrelated windows into one provider-wide percentage. A depleted
browser/search pool, for example, must not be treated as proof that an
independent coding pool is depleted.

## Quota pacing and adaptive reserves

Quota pacing applies only to a capacity model that actually exposes remaining
usable capacity and a reset horizon. It is not a universal rule for
rate-limited-only or unknown providers.

For each provider quota window:

```text
allowable burn rate =
  max(0, remaining usable quota - protected reserve)
  / time until reset
```

For a seven-day quota window, 100% / 7 is approximately 14.3% per day. A
15%-per-day figure is a useful alert heuristic, not a hard routing target. A
protected reserve should normally be demand-forecast based: expected
high-priority demand until reset plus an uncertainty margin. A small fixed
buffer may be used as a temporary floor when demand evidence is absent, but it
must not become a permanent model-quality tier.

The runtime compares observed burn rate with allowable burn rate:

- below pace: subscription capacity is available for normal suitable work;
- modestly above pace: prefer substitutes for routine work when comparable;
- forecast exhaustion before reset: preserve the pool for materially better or
  irreplaceable work;
- near reset with excess quota: use suitable capacity rather than wasting it;
- exhausted or stale shared-quota state: block until refreshed.

If multiple windows exist—such as hourly, daily, and weekly—evaluate each in
its own units. The most restrictive admissibility or risk result controls the
decision; unrelated percentages must not be numerically combined. Daily
pacing does not replace short-window rate-limit and concurrency checks.

The protected reserve is adaptive. It should reflect:

- forecast high-priority demand until reset;
- uncertainty and volatility in recent consumption;
- whether adequate substitute models exist;
- whether the candidate has a unique capability or quality advantage.

It is a capacity control, not a model-quality tier.

## Selection receipts and failure behavior

Every selection receipt should record:

- task lane and selection mode;
- selected provider, model, invocation method, and orchestrator;
- eligible candidates and rejection reasons;
- capability, policy, lifecycle, and capacity decisions;
- evidence cohort, sample count, freshness, and confidence;
- latency metrics used;
- capacity model, source freshness, unknown reason when applicable, and quota
  window/pacing state used;
- cost policy decision, without invented cost values;
- alternatives considered;
- algorithm and policy version.

The current orchestrator does not dynamically hand a failed task to the
other orchestrator. A worker failure after start is recorded and returned for
parent judgment. A different provider or harness requires a new explicit task
and identity. A bounded pre-dispatch health refresh may update eligibility,
but it must not become an implicit fallback chain. The minimum refresh means
reloading the authoritative local quarantine and capacity state immediately
before selection. A live provider query is optional only when state is stale,
must have a bounded deadline, and must record its source and age. It must not
query every provider on every selection, retry a failed worker, or silently
transfer ownership to another orchestrator.

### Scoped failure feedback

Failure feedback is useful only when the cause and scope are preserved. The
common normalized classes are:

```text
context_mismatch
rate_limit_or_capacity
protocol_or_serialization
route_or_model_not_found
access_denied
provider_outage
timeout
contract_malformed
identity_mismatch
scope_violation
unknown
```

Every suppression, cooldown, or capacity update must bind to the provider,
model, invocation method, orchestrator, failure class, scope, timestamps, and
reprobe/expiry condition. A failure in Grok must not silently quarantine the
same model for Codex, and a Pi failure must not silently quarantine a native
route unless the exact binding is shared and the evidence supports that
scope.

The default reactions are deliberately narrow:

- `context_mismatch` affects the task/context shape or that binding, not the
  model globally;
- `rate_limit_or_capacity` updates provider capacity and backoff state; it
  does not set quota to zero unless the provider confirms exhaustion;
- `protocol_or_serialization` affects the exact invocation path;
- `route_or_model_not_found` blocks the exact binding; model retirement needs
  independent confirmation;
- `access_denied` blocks or surfaces the exact route/surface authorization
  problem until refreshed; it does not judge model quality and is not
  log-only;
- `provider_outage` may create a scoped temporary cooldown after correlated
  evidence;
- `timeout` and `contract_malformed` update evidence for the exact binding;
  suppression requires attribution and repetition, because the harness or
  contract parser may be the fault;
- `identity_mismatch` blocks the result, promotion, and exact binding until
  the route is corrected and re-verified; it is not log-only;
- `scope_violation` blocks the result and raises an operator-visible alert.
  It may suppress the exact binding, but the system must not call it model
  misbehavior without evidence that excludes a parent or harness defect;
- `unknown` is surfaced and logged without aggressive quarantine.

Reactive failure feedback is not permission for an implicit cross-harness
fallback. It updates the local selector's evidence and eligibility state for
future tasks, subject to scope and expiry. Existing quarantine records that
lack orchestrator or invocation scope are diagnostic-only until their origin
is proven or they expire; they must not globally suppress another
orchestrator.

## Evidence, benchmarking, and learning

Benchmark and live telemetry are evidence inputs, not policy authority.

- Codex records Codex/Pi evidence.
- Grok records Grok evidence for its actual invocation path.
- The two performance datasets remain separate.
- A shared registry or cache file does not make evidence shared. Every
  evidence writer must be named, and every record/cache group must retain the
  complete four-part identity. A reader may consume another host's discovery
  metadata, but it must not treat another host's runtime outcomes as local
  evidence.
- Discoverability and static capability metadata may be shared.
- Pre-fix, malformed, or configuration-tainted cohorts are excluded from live
  routing evidence and retained only as historical diagnostics where useful.
- Benchmark results remain sequestered until the relevant orchestrator/path
  promotion gate explicitly accepts them.
- Verified-result evidence is necessarily lagging: it describes completed
  calls. Current live capacity and health signals remain separate, real-time
  inputs to eligibility.
- Evidence freshness shrinks confidence toward a neutral prior, not toward
  zero quality and not toward an unjustified positive score.
- Selection bias is addressed with bounded exploration on safe lanes and
  lane-specific evidence coverage.

The exact cache writer, refresh command, and authority for each host must be
documented before live routing is enabled. A shared derived cache is
acceptable only when it is rebuilt from an authoritative telemetry source and
cannot be concurrently overwritten by an unrelated host. The proposal does
not assume that Codex and Grok currently share a writer; that is an
implementation fact to verify.

The selector should not learn a new policy merely because one model has been
selected often. It may update model evidence and confidence, while policy
changes remain versioned decisions subject to replay and review.

## Shared implementation contract

The common contract should be implemented by both selectors without requiring
a shared runtime library:

1. Shared registry schema and candidate identity rules.
2. Shared task-lane and selection-mode vocabulary.
3. Shared provider-capacity adapter output contract, including independent
   multi-window state.
4. Shared verified-success, scoped failure-feedback, and receipt schema.
5. Shared golden decision fixtures plus executable conformance harnesses in
   both hosts. Structural fixture validation alone is insufficient.
6. Native Codex and Grok implementations.
7. Replay and live-path tests that prove equivalent policy decisions on
   equivalent inputs without merging runtime evidence.

The orchestrator field is an input to candidate/evidence filtering, not a
branch that changes the policy priority order.

## Implementation acceptance gates

Before this policy is treated as live, both implementations must provide
evidence for all of the following:

1. **Identity and authority:** registry, evidence, quarantine, and capacity
   readers/writers are identified; every runtime record is bound to provider,
   model, invocation method, and orchestrator.
2. **Latency target:** both selectors consume the canonical valid-result p90
   field. Any p50-only path is labeled provisional and cannot claim
   conformance.
3. **Capacity:** each enabled provider has an adapter or an explicit
   rate-limited/unknown state. Static quota-class multipliers do not count as
   capacity evidence.
4. **Candidate gating:** normal reasoning and write selection require
   lane-appropriate verified evidence; safe calibration is isolated and
   bounded.
5. **Failure scope:** quarantine/cooldown records are exact-binding scoped,
   old unscoped records cannot cross-suppress orchestrators, and the normalized
   action matrix is tested against harness, provider, and model faults.
6. **Conformance:** the shared golden fixtures execute through both native
   selectors, including deterministic, weighted-pool, diverse-panel,
   capacity, cold-start, and failure-scope cases.
7. **Live path:** an actual Codex selection and an actual Grok selection emit
   receipts showing the selected identity, p90/capacity inputs, rejection
   reasons, and verification outcome. Unit tests alone do not satisfy this
   gate.

## Open decisions for review

Please challenge these points before implementation is treated as settled:

1. Is “time to verified result” the correct primary objective, or should a
   different operator cost be explicit?
2. What demand forecast and uncertainty margin should determine protected
   reserves for each quota window? A fixed percentage may be a temporary
   fallback, but is not the long-term policy.
3. Should the initial automatic pay-per-use cap be exactly $0.01 per task?
4. What canonical p90 estimator and latency-uncertainty method should both
   selectors implement, and what stable tiebreaker applies when it is not
   meaningful?
5. What effective lane-specific evidence is required before a candidate can
   be used for bounded writes, and what neutral/global prior applies at
   cold-start?
6. Which capacity model and authoritative signals are available for each
   subscription, quota, rate-limited, and multi-pool provider? What should the
   selector do when those signals are unknown or stale?
7. What failure scopes and cooldown/reprobe rules are justified by evidence,
   without turning transport defects into model-quality judgments?
8. What are the authoritative writers and refresh commands for each evidence,
   capacity, quarantine, and receipt store?
9. How should unscoped historical quarantine records be retained, expired, or
   discarded without allowing cross-orchestrator suppression?
10. Does the common policy need any further exception beyond the independent
   critique/diversity modifier?
11. Which current registry fields or selector behaviors conflict with this
   proposal and should be removed rather than compatibility-preserved?

## Review request for Grok

Review this proposal as an adversarial design review. Do not assume that
existing Grok routing behavior is correct. Return:

- contradictions or accidental priority inversions;
- quota-pacing and reset-window edge cases;
- capacity models that the common contract cannot represent, including
  unknown or stale capacity;
- cases where latency, quality, or capacity evidence can be circular or
  selection-biased;
- cold-start and lane-specific evidence sufficiency;
- provider-specific signals that should be normalized versus left opaque;
- failure modes and scope errors in Codex/Pi and Grok invocation identity
  binding;
- target-versus-current conformance gaps in p90 latency, capacity adapters,
  golden-vector execution, candidate gating, quarantine scope, and live
  receipt fields;
- whether any proposed failure action incorrectly attributes a provider or
  harness fault to model quality;
- policy fields that are unnecessary complexity;
- concrete corrections, each labeled as verified fact, inference, hypothesis,
  or open decision. Do not call a target feature implemented merely because a
  schema, structural test, or placeholder exists.

Do not merge Codex and Grok performance scores. Evaluate whether the same
policy can be applied independently to each orchestrator's evidence.

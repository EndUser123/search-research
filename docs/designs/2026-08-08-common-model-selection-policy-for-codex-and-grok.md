# Common model-selection policy for Codex and Grok

**Date:** 2026-08-08  
**Last updated:** 2026-08-09 — pool-test scope, binding identity, and lane-scoped promotion clarified; live conformance remains open
**Status:** Revision 5d — Codex red-team synthesis; Grok re-review pending; not live or conformant
**Revision:** 5d — separates provider-pool health from code-model capability testing, aligns promotion with the common verification floor, and records the remaining Codex parity gap
**Audience:** Grok Build and Codex maintainers  
**Scope:** Worker-model selection, quota/capacity pacing, benchmark evidence, and the boundary between Codex and Grok orchestration.

## Revision 5 change log

Revision 5b incorporated all 42 findings from six cross-orchestrator review
relay sessions (all converged, zero disputes). Revision 5c preserved that
baseline and added the quota-recovery contract, evidence-scope corrections,
and explicit acceptance tests. Revision 5d adds the Codex red-team synthesis
below; it is not a new conformance attestation.

**Key changes from Revision 4:**

1. Fixed weighted-pool formula: freshness decay now interpolates toward neutral
   prior (0.5), not multiplies toward zero (C-R4-01)
2. Fixed deterministic ranking: capacity is gate-only (pass/fail), not a sort
   key; p90 latency is the first sort key (C-R4-02)
3. Lane verified-success floors are operator-configurable defaults requiring
   minimum N>=10 samples; labeled as policy not evidence-derived (C-R5-01)
4. Removed bounded-coding-in-mechanical: all writes use coding lane (C-R4-04)
5. Wilson lower bound: one-sided 95% (z=1.645), exact formula in golden
   fixtures; zero weights -> BLOCKED not uniform (C-R5-02, C-R5-05)
6. Added model_family field (distinct from provider); panel quorum requires
   distinct model_family for critique independence (C-R5-06)
7. Capacity demand is provider-unit-specific (tokens, requests, money); check
   remaining > demand + reserve (C-R5-03, C-R4-10)
8. Capacity reservation: durable record with ID, owner, demand, TTL,
   release-on-dispatch, crash recovery (C-R5-08)
9. Quarantine concurrency: msvcrt.locking sentinel before read-modify-write (C-R4-08)
10. Replay snapshots: retention tied to receipt retention; expired receipts
    marked non-replayable (C-R5-07)
11. Canonical candidate ordering (sorted by ID); weights rounded to 6 dp (C-R4-09)
12. Missing-p90 fallback: p90 > p50_provisional > lane_median_provisional > BLOCKED (C-R5-09)

**Additional fixes from R5 re-review (review-78ba2723102b-f5f12c38):**

13. Fixed residual mechanical-write reference in candidate onboarding section
    — calibration writes now explicitly use coding lane, not mechanical
14. Fixed capacity decision table: all admissibility checks now compare against
    demand + reserve, not bare remaining > 0
15. Near-zero weight threshold: if total raw weight <= 1e-6 before
    normalization, return BLOCKED (not uniform fallback)

**Revision 5c hardening (2026-08-09):**

16. Added an explicit capacity-recovery state machine for temporary backoff,
    quota reset, stale post-reset observations, and confirmed route retirement.
17. Added bounded resubmission ownership, retry/reprobe timing, and receipt
    fields so a temporary capacity failure cannot become an unexplained
    permanent block or an unbounded retry loop.
18. Reconciled the evidence snapshot to distinguish targeted passing tests,
    collection-blocked suites, embedded golden vectors, and live-path evidence.

**Revision 5d red-team synthesis (2026-08-09):**

19. Split provider-pool health/recovery tests from code-model capability tests;
    neither suite is allowed to stand in for the other.
20. Reconciled the pool promotion rule with the common default of N>=10
    lane-appropriate verified successes and the authoritative
    `verification_passed` state; the current Grok N=5 default remains a gap.
21. Required full binding identity (`orchestrator`, `invocation_method`,
    provider, model, route, verifier, and quota pool/account) for pool tests;
    a model-only argument is insufficient evidence identity.
22. Made promotion lane/risk scoped and downgraded the claimed Codex pool-test
    equivalent/shared fixture from current fact to a target until executable
    source, fixture hashes, and receipts exist.
23. Corrected pool identity: shared capacity is keyed by quota pool/account and
    provider-defined scope; orchestrator and method remain route provenance and
    are only part of the pool key when the provider exposes a separate limiter.

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
task classification (authoritative, with ambiguity fallback)
  -> hard eligibility gates (including lifecycle gate)
  -> task-fit / verified-success floor (with explicit verification states)
  -> capacity and quota pacing (with decision table)
  -> common selection mode (deterministic | weighted_pool | diverse_panel)
  -> panel capacity reservation (if diverse_panel)
  -> selection receipt (with replay fields)
  -> independent result verification
```

### Primary objective

> Minimize **conditional valid-result service time** subject to capability,
> reliability, capacity, policy, and cost constraints.

The objective is **conditional service time**, not unconditional time to
verified result. The system has no automatic retry or fallback: a failed
worker returns to the parent for judgment. Therefore the selector optimizes
the expected service time of a single attempt that produces a valid result,
conditioned on that attempt succeeding. The unconditional expected time to
a verified result (including failures, retries, and rework) is a diagnostic
metric recorded after the fact, not a selection-time formula.

**Do not use `p90_latency / verified_success_probability` as a selection
formula.** That estimator assumes a retry model that the system does not
have. Instead:

- Rank by conditional valid-result p90 latency among candidates that clear
  the verified-success floor.
- Record all-attempt outcomes (success, timeout, malformed, verification
  failure, scope violation) as diagnostic evidence.
- Monitor unconditional time-to-verified-result as a lagging quality metric,
  not as a live ranking input.

This is an evidence-based operating objective. The selector cannot know
whether the next result will verify; it estimates that outcome from
completed historical evidence and combines it with current capacity,
rate-limit, and health signals. The actual verification result is recorded
afterward and is not used to justify the decision that was already made.

## Current conformance status

This document defines the target policy. It does not claim that either live
selector already conforms to every rule. The latest source review (session
019fdf47, 2026-08-09) found these gaps and shipped fixes for the Grok side.
The evidence snapshot below is a dated, scope-limited record; it is not a
standing conformance attestation.

### Grok conformance — shipped fixes (2026-08-09)

1. **p90 latency target** (commit `b6b985f`) — `_latency_p50()` replaced with
   `_latency_p90()` implementing the R5b fallback chain (`p90 > p50_provisional
   > lane_median > BLOCKED`). `compute_score()` now uses p90 for the speed
   factor. **RESOLVED.**

2. **Lifecycle gate** (commit `b6b985f`) — `evidence_eligibility()` now blocks
   `lifecycle=candidate` records. Only `active` candidates are eligible. The 12
   `candidate` records in the live registry are correctly excluded pending
   promotion via verified-success evidence. **RESOLVED.**

3. **Quarantine scope** (commit `b6b985f`) — `QuarantineRecord` gains
   `orchestrator` and `invocation_method` fields. Transport and model
   quarantine creation sites populate them from the candidate. Backward
   compatible with pre-scope records. **RESOLVED.**

4. **Golden-vector executable gate** (commit `c55646d`) — `golden_vectors.py`
   `invoke_selector()` had a one-line registry construction bug that caused
   `AttributeError` during selector invocation. Fixed: all 25 vectors pass.
   Status changed from `SKELETON` to `EXECUTABLE`. The verifier now returns
   exit code 1 on any failure. **RESOLVED.**

5. **Capacity adapter** (commit `6a6d10f`) — `capacity_adapter.py` reads the
   live fleet quota cache (7 providers: copilot, google, zai, minimax,
   opencode-go, cohere, grok), normalizes to the R5b adapter shape, and
   implements the decision table as a 5th gate alongside capability/policy/
   lifecycle/health. `_quota_headroom()` removed from `compute_score()` —
   capacity is gate-only per R5b fix #2. Live test confirms exhausted providers
   (cohere at pct=0) are correctly blocked. **PARTIALLY RESOLVED** — the gate
   is live and reads real data, but v1 limitations remain:
   - All providers mapped to `rate_limited_only` (none classified as
     `windowed_units`, `monetary_budget`, or `multi_pool` yet)
   - Demand estimation is `demand=1 request` for all lanes (token-level
     estimation deferred — needs task prompt passed into the selector)
   - Reserve is a fixed 5% floor (adaptive reserve from demand-forecast
     telemetry deferred)
   - Confirmed `0%` snapshot remains blocked even after recorded reset time;
     `deferred_until` / retry outcome not yet produced
   - Task class/spend semantics not passed into the capacity decision

6. **Evidence key matching** (commit `abee719`) — the evidence cache had 865
   groups with p90/success-rate/sample-count data, but only 5/32 candidates
   matched due to key mismatches (short names vs full IDs, `spawn` vs
   `http`/`pi`/`opencode`, provider case variation). `_lookup_evidence_in_cache()`
   now tries model name aliases, dispatch-path fallback, and case-insensitive
   matching. `compute_score()` uses `success_rate` as quality proxy when
   `quality_avg` is absent. 8 of 20 active candidates now have evidence reaching
   the scorer; evidence-backed candidates rank above cold-start candidates.
   **RESOLVED** for matched candidates; 12 candidates remain cold-start because
   their telemetry uses provider/model naming patterns not yet covered by the
   alias strategy.

### Remaining Grok gaps

- **Capacity adapter depth** — `windowed_units`, `monetary_budget`, and
  `multi_pool` capacity kinds are not yet implemented. The adapter maps all
  providers to `rate_limited_only`. Providers with token-window or spend-budget
  semantics are not correctly classified.

- **Quota recovery** — a confirmed `0%` capacity snapshot blocks even after its
  recorded reset time. The selector does not yet return `deferred_until`,
  `reprobe_at`, or a structured retry outcome, and no caller/queue ownership
  for bounded resubmission is verified. The policy now defines those states;
  implementation evidence is still missing for temporary backoff, multi-hour
  or monthly resets, post-reset refresh, and confirmed route retirement.

- **Unknown-capacity rule** — missing or stale capacity for mapped providers is
  admitted for ordinary work, but the selector does not yet pass task
  class/spend semantics into the capacity decision. This does not satisfy the
  unknown-capacity rule that limits disclosed uncertainty to non-spend work.

- **Receipt fields** — current receipts do not yet expose every target field.
  Missing capacity, latency, evidence, or verification values remain explicit
  unknowns rather than being synthesized.

- **Evidence coverage** — 12 of 20 active candidates have no matching evidence
  despite telemetry existing for them. The naming mismatch between
  `fleet-models.json` identifiers and telemetry provider/model strings needs
  further alias strategies or a canonical naming reconciliation.

- **Quality scoring** — `compute_score()` uses `success_rate` as a quality
  proxy because `quality_avg` is 0.0 in all current telemetry. The telemetry
  pipeline does not yet populate quality scores. When it does, the scorer will
  automatically prefer `quality_avg` over `success_rate`.

### Codex conformance

Codex currently enforces `lifecycle=active` in its registry health path, but
its live rank records `evidence_count` without enforcing the common
lane-specific verified-success floors or Wilson lower-bound weighting. The
current rank uses reliability/defaults, measured latency, quota preference,
and candidate priority. This is a policy-conformance gap, not evidence that
the target algorithm is live. The Codex golden-vector JS counterpart remains
absent.

### Evidence snapshot (2026-08-09, session 019fdf47)

The following results are measured, scope-limited evidence from the current
source review:

Reproduction commands (working directory
`C:\Users\brsth\.grok\skills\model-quota`):

```powershell
python -m pytest -q tests/test_model_router.py tests/test_circuit_breaker.py tests/test_golden_vectors.py tests/test_pick_model_migration.py tests/test_registry_schema.py
python -m pytest -q tests/test_benchmark_gate.py tests/test_evidence_accumulator.py tests/test_pick_model_shadow.py
python scripts/golden_vectors.py verify
```

- Grok selector/router, circuit-breaker, golden-vector, migration, and schema
  targeted tests: **249 passed**.
- Grok benchmark-gate, evidence-accumulator, and shadow-selection targeted
  tests: **101 passed**.
- `python scripts/golden_vectors.py verify`: **25/25 cases passed** with
  executable selector invocation. These fixtures use embedded mini-registries;
  they do not exercise live capacity, live evidence freshness, or the Codex
  selector.
- A clean full Grok model-quota test run is **not verified**: collection is
  blocked by the pre-existing `migrate_to_v4.py` import of missing
  `registry_views` exports. The targeted pass counts above must not be read as
  a full-suite result.
- No executable Codex counterpart or paired live Codex/Grok receipt was
  produced by this snapshot. The shared live-path conformance gate therefore
  remains open.

These results support targeted selector behavior, not live cross-host
conformance. Receipts and benchmark artifacts must describe the
implementation as provisional or non-conformant until every acceptance gate
has current, path-specific evidence. Passing unit tests alone is not
acceptance.

## Provider capacity health and code-model capability certification

There are three separate things that must not be conflated:

| What | Primary question | Identity key | Produces | May authorize |
|---|---|---|---|---|
| Provider capacity health | Can this provider's API serve requests right now? | Provider (API key + endpoint) | Capacity state (fresh/stale/exhausted/unknown) | Capacity admission only |
| Code-model capability | Can this exact model binding perform coding work? | Binding fingerprint + lane | Calibration `verification_passed` and quality evidence | Lane-scoped promotion |
| Production evidence | How well does it perform real work? | Binding fingerprint + task cohort | Routing-eligible quality, latency, verification | Runtime ranking |

Capacity health is not model quality. Capability is not capacity health.
Production evidence is neither calibration suite.

### Provider capacity health

Each provider entry in the registry corresponds to one API key and one
rate limit. In the current fleet, provider = pool — one NVIDIA key, one
Cohere key, one OpenRouter key. The capacity gate checks whether the
provider's current quota state admits the request.

Two models on the same provider share the same rate limit. Exhausting
the NVIDIA quota on one model exhausts it for all NVIDIA models. The
capacity gate treats them as one bucket.

What this covers:
- fresh vs stale capacity observations
- exhausted quota (0%) blocking
- rate-limit backoff and retry-after handling
- reset window behavior

### Code-model capability suite

This suite certifies one exact binding in one lane:

```text
orchestrator + invocation_method + provider + model + lane
```

The runner may accept a short model alias only when it resolves to exactly
one binding and records the resolved identity before telemetry is written.

The current Grok artifact (`pool_test.py`) is a HumanEval-style coding
calibration runner: 13 code generation problems, sandboxed execution,
binary pass/fail scoring. It is a valid calibration signal for initial
promotion — it proves the model can write correct standalone code.

Calibration evidence has `routing_eligible: false` and must not influence
runtime ranking. It may support promotion only when:

1. exact binding identity and lane match;
2. `success=true` and explicit `verification_passed`;
3. no timeout, malformed-output, identity, or scope error;
4. the operator-configured lane floor is met; and
5. promotion is scoped to the tested lane only.

The operator-configured default is N=5 per lane in `fleet-models.json`.
The policy recommendation is N>=10 for higher confidence. Both are valid
operator choices — the contract is that the configured floor is met.

`quality_score` is a measurement, not a substitute for `verification_passed`.

The initial promotion floor (HumanEval + N=5) establishes minimum
capability. A higher acceptance tier (repository-context coding, patch
application, tool use, independent verification) gates higher-risk work
and is future work.

### Cohort and lifecycle flow

```text
1. New binding enters the registry as lifecycle=candidate.
2. Capacity gate admits a bounded calibration request.
3. Code-model capability tests produce calibration records.
4. Only verification_passed records count toward the configured lane floor.
5. Promotion grants active eligibility for the tested lane only.
6. Production calls produce separate routing-eligible evidence for ranking.
7. Periodic re-certification repeats capability gates.
```

`active` must not be interpreted as globally eligible. Coding calibration
must not silently authorize reasoning, critic, or other lanes.

### Cross-host compatibility

Codex and Grok should use the same problem manifest (fixture hash). Until
a Codex executable counterpart and paired receipt exist, the Codex pool
test is a target contract, not a verified fact.

### Lane expansion

The current concrete artifact covers coding calibration only. The target
pattern extends to other lanes:

| Lane | Test type | Scoring |
|------|-----------|---------|
| coding | Code generation plus sandboxed execution and repository-style acceptance | Verified pass/fail plus quality metrics |
| reasoning | Analysis tasks with known-correct conclusions | Rubric score plus verification state |
| mechanical | Extraction/formatting tasks with expected output | Exact match |
| critic | Code review tasks with planted bugs | Recall plus verification state |

Each lane has a separate runner and fixture manifest, while the telemetry
pipeline, binding identity, capacity gate, and promotion-state vocabulary are
shared.

## What is shared and what remains separate

### Shared

Codex and Grok should share or conform to:

- candidate discoverability and model metadata;
- provider aliases and canonical model identifiers;
- capability and context metadata;
- lifecycle and policy-state vocabulary;
- task-lane definitions and task-classification contract;
- quota/capacity model semantics and adapter output contract;
- selection-mode definitions and v1 algorithm contract;
- verified-success definition (with explicit verification states);
- selection-receipt shape (including replay fields);
- golden decision fixtures and algorithm version;
- binding fingerprint component list and serialization rules.

The implementations may remain native: JavaScript for Codex and Python for
Grok. The shared schema and golden vectors are the compatibility boundary.

### Separate

Runtime evidence must remain separate by the complete invocation identity:

```text
provider + model + invocation_method + orchestrator + binding_fingerprint
```

The `binding_fingerprint` is a non-ranking identifier used for evidence
segmentation. It is a SHA-256 hash of the sorted JSON encoding of:

```text
{
  "provider": "<provider>",
  "model": "<model>",
  "invocation_method": "<pi|native|http|opencode>",
  "orchestrator": "<codex|grok>",
  "route": "<endpoint or alias resolution>",
  "harness_version": "<selector/harness version>",
  "prompt_contract": "<system prompt + tool policy hash>",
  "result_contract": "<result schema version>",
  "verifier": "<verification harness version>",
  "config_provenance": "<config file hash>"
}
```

When any fingerprint component changes, a new evidence cohort begins. Old
evidence is retained as diagnostic but does not merge into the new cohort.

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
verification outcomes are local to the exact binding fingerprint.

## Task-classification contract

Task classification is the first policy decision. It must be authoritative,
deterministic, and shared between both hosts to prevent divergence at the
first gate.

### Classification authority

The task lane is determined by the **dispatching skill or caller**, not by
the selector. The selector receives the lane as an input; it does not infer
the lane from the prompt content. If the caller does not specify a lane,
the default is `reasoning` (the higher-safety lane).

### Ambiguity handling

When a task straddles lanes (e.g., "read this file and summarize it" could
be mechanical or reasoning):

1. The caller declares the lane explicitly.
2. If the caller is ambiguous, the **higher-safety lane** is used.
3. For write-capable tasks, ambiguity always resolves to the lane with the
   stricter verified-success floor.
4. The receipt records the declared lane, the ambiguity resolution (if any),
   and the classifier provenance (which skill or caller assigned the lane).

### Lane definitions

| Lane | Selection mode | Exploration | Write-capable | Description |
|------|---------------|-------------|---------------|-------------|
| `mechanical` | `deterministic` | epsilon=0.05 (safe only) | **No** | Extraction, reading, formatting, routine verification, structured output, bounded low-ambiguity read-only work |
| `reasoning` | `weighted_pool` | epsilon=0.1 (safe only) | No | Planning, debugging, architecture, ambiguous coding, synthesis, single-model critique |
| `coding` | `weighted_pool` | epsilon=0.0 | Yes (worktree) | All write-capable work including bounded coding with complete specification and independent verification |
| `critic` | `diverse_panel` | epsilon=0.0 | No | Multi-model red-team or cross-check |
| `calibration` | `weighted_pool` | epsilon=0.1 | Yes (worktree, bounded scope only) | Safe onboarding for candidate-lifecycle models; bounded scope, isolated worktree, mandatory verification. Not eligible for normal routing. |

All tasks that write files — including bounded coding — must use the `coding`
lane with worktree isolation. The `mechanical` lane is strictly read-only;
no exceptions.

## V1 algorithm contract

Both selectors must implement the same algorithm for each selection mode.
This contract is versioned (`algorithm_version: "v1"`). Any change requires
a new version and replay-tested fixtures.

### Lane verified-success floors

The following floors are **operator-configurable policy defaults**, not
evidence-derived values. They require a minimum of N>=10 lane-appropriate
verified successes before a candidate is considered to have "cleared" the
floor. Candidates with fewer than 10 samples are `provisional` regardless
of their raw success rate.

| Lane | Default floor | Minimum samples |
|------|--------------|-----------------|
| `mechanical` | 80% | 10 |
| `reasoning` | 70% | 10 |
| `coding` | 75% | 10 |
| `critic` | 70% | 10 |

### Deterministic mode (mechanical lane)

```text
eligible = candidates that pass all gates (including lifecycle + verified-success floor)

# Capacity is a GATE (pass/fail), not a ranking key.
# Candidates that fail capacity admissibility are already excluded.

ranked = sort(eligible, key=lambda c: (
    p90_latency(c),                      # ASC: faster first (primary)
    verified_success_lower_bound(c),     # DESC: within 5% latency tie-band,
                                         #   prefer higher reliability
    stable_candidate_id(c),              # ASC: stable final tie-breaker
))
selected = ranked[0]
```

Exploration (epsilon=0.05 for mechanical safe lanes only): with probability
epsilon, select a random eligible candidate instead of the top-ranked one.
Exploration is disabled for write-capable or high-risk work.

### Weighted-pool mode (reasoning, coding lanes)

```text
eligible = candidates that pass all gates

For each candidate c:
    # Step 1: Effective verified-success rate with small-sample correction
    # Wilson one-sided lower bound (z=1.645 for 95% confidence)
    # Formula: (p + z^2/(2n) - z*sqrt(p*(1-p)/n + z^2/(4n^2))) / (1 + z^2/n)
    # where p = observed success rate, n = sample size
    if sample_size(c) >= 10:
        effective_success = wilson_lower_bound(
            verified_success_rate(c), sample_size(c), z=1.645
        )
    else:
        effective_success = 0.5  # neutral cold-start prior

    # Step 2: Freshness decay interpolates toward neutral prior (0.5),
    # NOT multiply toward zero.
    # staleness_factor = 0.0 (fresh) to 1.0 (fully stale at 30 days)
    staleness = min(1.0, age_days(c) / 30.0)
    effective_success = effective_success * (1 - staleness) + 0.5 * staleness

    # Step 3: Latency penalty (normalized against lane median)
    latency = p90_latency(c) if p90_available(c)
              else p50_latency(c) if p50_available(c)       # p50_provisional
              else lane_p90_median(eligible)                 # lane_median_provisional
    latency_penalty = latency / lane_p90_median(eligible)

    # Step 4: Final weight
    weight = effective_success / latency_penalty

# Normalize weights
total = sum(weight(c) for c in eligible)
if total <= 1e-6:
    # Zero or near-zero total weights: BLOCKED, not uniform fallback.
    # Zero weights can mean no usable evidence, not just rounding.
    # Near-zero (< 1e-6) is treated as zero for safety.
    return BLOCKED("all eligible candidates have zero or near-zero effective weight")
weights = [weight(c) / total for c in eligible]

# Round weights to 6 decimal places for deterministic replay
weights = [round(w, 6) for w in weights]

selected = weighted_random_choice(eligible, weights, seed=random_seed)
```

**Missing-data fallback chain (ordered):**

1. p90 available: use p90, label `latency_source: "p90"`
2. p50 available but not p90: use p50, label `latency_source: "p50_provisional"`
3. Neither available: use lane median, label `latency_source: "lane_median_provisional"`
4. Lane median unavailable: BLOCKED

**Tie-breaking:** if two candidates have weights within 5% of each other,
prefer the candidate with higher verified-success lower bound, then stable
candidate ID.

Exploration (epsilon=0.1 for reasoning safe lanes): with probability
epsilon, select a random eligible candidate. Disabled for write-capable
(`coding` lane).

### Diverse-panel mode (critic lane)

```text
# model_family is an explicit registry field (e.g., "deepseek-v4", "nemotron-3")
# DISTINCT from provider (e.g., "nvidia-nim", "zen")
# Two models sharing the same upstream model are the same model_family
families_available = distinct(model_family(c) for c in eligible)

MINIMUM_PANEL_QUORUM = 2  # distinct model_families required
if len(families_available) < MINIMUM_PANEL_QUORUM:
    if operator_preauthorized_degraded:
        return DEGRADED_PANEL(reduced_diversity_receipt)
    else:
        return BLOCKED("insufficient model_family diversity for independent critique")

panel = []
for family in sample(families_available, min(requested_size, len(families_available))):
    best_in_family = highest_weight(eligible where model_family == family)
    panel.append(best_in_family)

# Panel capacity reservation: durable record, not advisory check
reservation = CapacityReservation(
    id=unique_id(),
    owner=session_id + ":" + turn_id,
    demand=estimate_demand(panel),  # provider-unit-specific (see below)
    ttl_seconds=300,
    created_at=now(),
)
# Reservation holds until dispatch consumes it or TTL expires.
# Crash recovery: reservation auto-expires via TTL.
if not acquire_reservation(reservation):
    return BLOCKED("capacity reservation failed for panel") or
    staggered_dispatch(panel)  # sequential fallback, disclosed in receipt
```

**Capacity demand estimation:** demand is provider-unit-specific, not a
flat call count. For each panel member:

- `windowed_units` (token pools): estimate input_tokens + bounded_output_tokens
- `monetary_budget`: estimate cost from provider pricing + token envelope
- `rate_limited_only`: demand = 1 request per member
- `multi_pool`: check demand against every relevant unit independently
- `unknown`: demand estimate is advisory only; reservation is best-effort

**Minimum panel quorum:** 2 distinct model families. A single-family "panel"
is not independent critique. Panel diversity is defined by `model_family`
(lineage), not by `provider` (route). Different providers serving the same
upstream model do not provide critique independence.

**Reservation failure:** fail-closed by default. The operator may pre-authorize
degraded mode (reduced diversity, staggered dispatch, or single-model fallback)
for specific task types. Degraded mode is always disclosed in the receipt.

## Common eligibility gates

Ranking never happens before these gates:

1. The candidate supports the required task capabilities.
2. The context window is sufficient, including a safety margin for the
   packet and expected output.
3. The exact provider/model/invocation/orchestrator binding is configured and
   verified.
4. The provider endpoint and transport are currently usable.
5. **Lifecycle gate:** the candidate's lifecycle is `active` for the requested
   lane and risk class. A `candidate` lifecycle record is eligible ONLY for
   the safe-calibration lane. Normal reasoning, coding, or write-capable
   selection requires lifecycle=active. This gate is enforced by the
   selector, not by policy text alone.
6. Current quota, rate-limit, and concurrency state admits the call.
7. The candidate clears the lane-specific verified-success floor, or the task
   is explicitly admitted to the bounded safe-calibration lane. A normal
   reasoning or write-capable selection may not use the calibration exception.

### Verification states

Verified success is rich and includes explicit verification states:

```text
verification_not_applicable  # verification was not defined for this task
verification_not_run         # verification was defined but not executed
verification_failed          # verification was executed and did not pass
verification_passed          # verification was executed and passed
```

Only `verification_passed` counts toward a promotion threshold. Lane-floor
eligibility rules:

| Verification state | Counts toward promotion? | Eligible for reasoning/coding? | Eligible for calibration? |
|---|---|---|---|
| `verification_passed` | Yes | Yes (if sample sufficient) | Yes |
| `verification_not_applicable` | No | No (treat as unverified) | Yes (bounded scope only) |
| `verification_not_run` | No | No | No |
| `verification_failed` | No (counts against) | No | No |

The operator can see one promotion threshold per lane, while the system keeps
the richer evidence needed to enforce it.

## Evidence hierarchy and candidate onboarding

Evidence is applied at the narrowest trustworthy scope first:

1. exact binding fingerprint identity in the requested lane;
2. the same fingerprint identity in related lanes;
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

A candidate may be calibrated on low-risk work in the `coding` lane (the
only write-capable lane) with bounded scope and an isolated worktree. The
`mechanical` lane is strictly read-only; calibration tasks that write files
must use the `coding` lane, not `mechanical`. This is a containment
requirement. A candidate is not automatically eligible for reasoning or
write-capable work. A new, free, or statically high-priority model must not
displace an evidenced candidate without lane-appropriate evidence.

The operator-facing promotion control may remain one threshold per lane, but
the threshold is not a universal raw-call rule and need not be five. The
implementation must count only lane-appropriate verified successes and also
enforce identity, contract, verification, timeout, and scope conditions.

## Latency rules

Latency is an optimization input, not a substitute for correctness.

- Use measured p90 valid-result latency for the exact binding fingerprint as
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
  candidate has a defensible advantage, use the documented tiebreaker (v1
  algorithm contract) and record that uncertainty in the receipt.
- Recompute latency evidence by lane and cohort; do not copy benchmark
  latency across task types or invocation identities.

For mechanical work, latency is normally the primary ranking factor after the
gates. For reasoning work, latency modulates the evidence weight because
quality and verification success matter more.

The long-term metric to monitor is unconditional time to a verified result
(including failures and rework), not raw worker latency. This captures the
cost of failures, malformed responses, and parent rework without requiring
an automatic retry or fallback.

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

Do not create an arbitrary permanent "reasoning reserve" when observed usage
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
which capacity model it can observe.

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
recovery_state
recovery_reason
retryable
expected_wait
retry_after
rate_limit_state
concurrency_state
remaining + unit
reset_at
projected_exhaustion
deferred_until
reprobe_at
recovery_owner
retry_budget
observed_at
source and freshness
unknown_reason
```

### Capacity decision table

Admissibility is determined by the following table, keyed by capacity_kind
and freshness. This table is normative — the selector does not invent
defaults when the adapter output is ambiguous.

| capacity_kind | freshness | ordinary task | bounded non-spend task | scarcity-sensitive task |
|---|---|---|---|---|
| `windowed_units` | fresh (<5 min) | allow if remaining > demand + reserve, apply pacing | allow if remaining > demand | allow only if remaining > demand + reserve and not forecast-exhausted |
| `windowed_units` | stale (>5 min) | block until refreshed | allow if route health is clean | block |
| `monetary_budget` | fresh | allow if remaining > demand + reserve | allow if remaining > demand | allow only if remaining > demand + reserve |
| `monetary_budget` | stale | block until refreshed | allow | block |
| `rate_limited_only` | live (429 health checked) | allow if no active 429/backoff | allow if concurrency state admits demand | allow if concurrency state admits demand |
| `rate_limited_only` | stale | allow with disclosed uncertainty | allow | block |
| `multi_pool` | fresh | check most restrictive window against demand + reserve | allow if all relevant windows admit demand | allow only if all windows clear demand + reserve |
| `multi_pool` | stale | block until refreshed | allow if route health clean | block |
| `unknown` | n/a | allow with disclosed uncertainty (non-spend only) | allow | block |

**Confirmed exhaustion or retry-after:** always blocks until the stated expiry
or a fresh provider observation overrides it.

### Capacity recovery and resubmission contract

Capacity failure is a control outcome, not an instruction to silently retry or
fall back. The selector returns a recovery result to the caller; the caller or
an explicitly configured queue owns any later resubmission. A selector must
never invoke a substitute provider, create an implicit fallback chain, or
retry without a declared budget.

| recovery_state | Meaning | Required selector behavior | Resubmission behavior |
|---|---|---|---|
| `available` | A current observation admits this request. | Permit dispatch subject to all other gates. | No recovery action. |
| `backoff` | A temporary 429, rate-limit, queue, or provider cooldown is active. | Block the affected binding and return `retry_after`, `deferred_until`, and the scoped reason. | Caller may schedule one bounded retry no earlier than `deferred_until`, after a fresh bounded observation. |
| `quota_exhausted` | An authoritative window or budget is exhausted. | Block the affected capacity window; return its `reset_at`, `deferred_until`, unit, and source. | Caller may defer until the reset horizon, but must obtain a fresh observation before dispatch. |
| `reset_pending` | The recorded reset time has passed, but recovery has not been freshly observed. | Do not infer recovery from elapsed time; return `reprobe_at` and remain blocked for ordinary or spend-sensitive work. | Queue a bounded reprobe. A fresh positive observation is required to transition to `available`. |
| `route_retired` | Independent evidence confirms that the provider/model/route is discontinued. | Return terminal `BLOCKED` for the exact binding with `retryable=false`; do not treat it as temporary quota. | No automatic retry. Registry/operator action or a new explicit task identity is required. |
| `unknown` | No trustworthy remaining, reset, or rate signal is available. | Apply the `unknown` row of the decision table and disclose the uncertainty. | Do not retry spend-sensitive work; any bounded non-spend attempt still records the unknown reason and budget. |

`deferred_until` is a lower bound, not proof that the provider recovered. When
several independent windows or backoffs govern one request, the effective
defer time is the latest active constraint for that request, while every
underlying window remains separately recorded. `retry_after` is the provider's
earliest retry signal; `reset_at` is the capacity-window boundary; neither may
be silently substituted for the other.

Every deferred result records `recovery_owner` (parent or named queue),
`retry_budget`, the current attempt number, and the exact binding scope. If no
recovery owner or budget is supplied, the safe result is `BLOCKED` with an
operator-visible reason. This preserves the no-automatic-fallback policy while
still making a temporary failure retryable and observable.

The conformance suite must cover at least: a short 429 backoff, a multi-hour
reset, a monthly quota reset, a reset whose timestamp passes without fresh
observation, independent multi-pool exhaustion, and a confirmed discontinued
route. Each case must prove both the immediate decision and the later
transition (or terminal outcome), not merely the presence of a timestamp.

**Demand accounting:** admissibility checks remaining capacity against
this request's estimated demand plus the protected reserve, not merely
`remaining > 0`. Demand is provider-unit-specific:

- `windowed_units`: estimate input_tokens + bounded_output_tokens for this task
- `monetary_budget`: estimate cost from provider pricing + token envelope
- `rate_limited_only`: demand = 1 request
- `multi_pool`: check demand against every relevant unit independently
- `unknown`: demand estimate is advisory; admissibility is best-effort

**Stale capacity** is neither unlimited nor exhausted. It may permit an
already-approved bounded non-spend call when current route health admits it,
but it provides no pacing advantage and must not authorize scarcity-sensitive
spending.

For `multi_pool` providers, each limiting window remains a separate record
with its own unit, remaining value, reset, and source. The selector may use
the most restrictive admissibility result for the requested task, but it must
not collapse unrelated windows into one provider-wide percentage.

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
decision; unrelated percentages must not be numerically combined.

The protected reserve is adaptive. It should reflect:

- forecast high-priority demand until reset;
- uncertainty and volatility in recent consumption;
- whether adequate substitute models exist;
- whether the candidate has a unique capability or quality advantage.

It is a capacity control, not a model-quality tier.

## Selection receipts and replay fields

Every selection receipt should record:

- task lane, declared lane, ambiguity resolution (if any), and selection mode;
- selected provider, model, invocation method, orchestrator, and binding fingerprint;
- eligible candidates and rejection reasons (including lifecycle gate rejections);
- capability, policy, lifecycle, and capacity decisions;
- evidence cohort, binding fingerprint, sample count, freshness, and confidence;
- latency metrics used (including `latency_source: "p90" | "p50_provisional"`);
- capacity model, source freshness, unknown reason when applicable, and quota
  window/pacing state used;
- cost policy decision, without invented cost values;
- alternatives considered;
- **Replay fields (mandatory for weighted_pool and diverse_panel):**
  - `algorithm_version`: e.g., "v1"
  - `random_seed`: the PRNG seed used for weighted selection
  - `prng_version`: PRNG algorithm identifier
  - `normalized_weights`: the weight vector applied to eligible candidates, in canonical candidate ordering (sorted by candidate ID), rounded to 6 decimal places
  - `exploration_triggered`: boolean, whether exploration was activated
  - `exploration_draw`: the random value that determined exploration (if triggered)
  - `evidence_snapshot_hash`: hash of the evidence state used for this decision
  - `capacity_snapshot_hash`: hash of the capacity state used for this decision

**Replay snapshot retention:** evidence and capacity snapshots are retained
in `P:/.artifacts/model-routing/snapshots/` with the same retention as
receipts. Receipts older than the snapshot retention period are marked
`replayable: false` and excluded from conformance claims.

The current orchestrator does not dynamically hand a failed task to the
other orchestrator. A worker failure after start is recorded and returned for
parent judgment. A different provider or harness requires a new explicit task
and identity.

A bounded pre-dispatch health refresh is limited to one configured,
timeout-bounded evaluation of the requested route's registry, quarantine, and
capacity/health state. It may update eligibility but must not invoke a model,
try substitutes, or create an implicit fallback chain. If the refresh is
unavailable or exceeds its budget, the selector applies the capacity decision
table using explicit stale/unknown state and records `refresh_status`,
`refresh_sources`, and `refresh_duration_ms` in the receipt. Any live provider
probe must be explicitly enabled by task policy and remain within the same
budget.

### Quarantine concurrency model

Quarantine records are **per-orchestrator** to avoid cross-orchestrator
write contention:

```text
P:/.artifacts/model-routing/quarantine-{orchestrator}.json
```

Each orchestrator writes only its own quarantine file. A failure in Grok
quarantines a binding in `quarantine-grok.json`; it does not touch
`quarantine-codex.json`. The selector reads only its own orchestrator's
quarantine file for eligibility decisions.

Quarantine records within each file use atomic writes (tmp + os.replace)
with the GC pattern: expired records are pruned on every write. The
read-modify-write cycle is protected by a sentinel lock file with
`msvcrt.locking` (Windows) or `fcntl.flock` (POSIX) to prevent lost updates
from concurrent same-orchestrator processes.

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
route unless the exact binding is shared and the evidence supports that scope.

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

Existing quarantine records that lack orchestrator or invocation scope are
diagnostic-only until they expire via their `reprobe_after` TTL. Unscoped
records do not block any orchestrator.

## Evidence, benchmarking, and learning

Benchmark and live telemetry are evidence inputs, not policy authority.

- Codex records Codex/Pi evidence.
- Grok records Grok evidence for its actual invocation path.
- The two performance datasets remain separate.
- A shared registry or cache file does not make evidence shared. Every
  evidence writer must be named, and every record/cache group must retain the
  complete binding fingerprint.
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
- **All-attempt outcomes are recorded as diagnostic:** every spawn records
  success, timeout, malformed, verification_failure, or scope_violation.
  This data feeds the unconditional time-to-verified-result monitoring metric
  but is not used as a live selection formula.

## Shared implementation contract

The common contract should be implemented by both selectors without requiring
a shared runtime library:

1. Shared registry schema, candidate identity rules, and binding fingerprint
   component list.
2. Shared task-lane and selection-mode vocabulary, plus task-classification
   contract.
3. Shared v1 algorithm contract (formulas, priors, tie-breakers, exploration
   epsilon, missing-data defaults, small-sample correction).
4. Shared provider-capacity adapter output contract, including the capacity
   decision table and independent multi-window state.
5. Shared verified-success states, scoped failure-feedback, and receipt schema
   (including replay fields).
6. Shared golden decision fixtures plus executable conformance harnesses in
   both hosts. Structural fixture validation alone is insufficient.
7. Native Codex and Grok implementations.
8. Replay and live-path tests that prove equivalent policy decisions on
   equivalent inputs without merging runtime evidence.

The orchestrator field is an input to candidate/evidence filtering, not a
branch that changes the policy priority order.

## Implementation acceptance gates

Before this policy is treated as live, both implementations must provide
evidence for all of the following:

1. **Identity and authority:** registry, evidence, quarantine, and capacity
   readers/writers are identified; every runtime record is bound to provider,
   model, invocation method, orchestrator, and binding fingerprint.
2. **Latency target:** both selectors consume the canonical valid-result p90
   field. Any p50-only path is labeled provisional and cannot claim
   conformance.
3. **Capacity:** each enabled provider has an adapter or an explicit
   rate-limited/unknown state per the capacity decision table. Static
   quota-class multipliers do not count as capacity evidence.
4. **Candidate gating:** normal reasoning and write selection require
   lifecycle=active, an enforced eligible lane/risk scope, and lane-appropriate
   verified evidence with `verification_passed` state. Safe calibration is
   isolated, bounded, and the only lane that admits candidate-lifecycle
   records. The common default is N>=10 lane-appropriate verified successes;
   any lower implementation threshold is provisional and non-conformant.
5. **Failure scope:** quarantine/cooldown records are per-orchestrator,
   exact-binding scoped, old unscoped records expire via reprobe_after TTL,
   and the normalized action matrix is tested against harness, provider, and
   model faults.
6. **Conformance:** the shared golden fixtures execute through both native
   selectors, including deterministic, weighted-pool, diverse-panel,
   capacity, cold-start, lifecycle-gate, and failure-scope cases.
7. **Replay:** weighted-pool and diverse-panel receipts include all replay
   fields (algorithm_version, random_seed, normalized_weights, exploration
   flag, evidence/capacity snapshot hashes). A stored receipt plus referenced
   snapshots reproduces the selected candidate.
8. **Panel quorum:** diverse-panel selection enforces the minimum 2-family
   quorum. Reservation failure produces BLOCKED or explicitly disclosed
   DEGRADED mode, never a silent single-family panel.
9. **Live path:** an actual Codex selection and an actual Grok selection emit
   receipts showing the selected identity, binding fingerprint, p90/capacity
   inputs, rejection reasons, replay fields, and verification outcome. Unit
   tests alone do not satisfy this gate.
10. **Recovery:** temporary backoff, multi-hour reset, monthly reset,
     post-reset reprobe, independent multi-pool exhaustion, and confirmed route
     retirement are tested through the native selectors. Results expose
     `recovery_state`, `retryable`, `retry_after`, `deferred_until`,
     `reprobe_at`, recovery ownership, and bounded retry state. A retry after a
     defer horizon requires a fresh observation; elapsed time alone is not
     evidence of recovery.
11. **Pool-test separation and identity:** provider-pool health/recovery tests
    are separate from code-model capability tests and production code-lane
    evidence. Each live test records the full binding fingerprint, quota pool
    or account, capacity reservation, fixture manifest, verifier, and
    orchestrator/method identity. Pool health cannot promote a model, and
    calibration cannot rank production routing. Synthetic reset fixtures are
    used where possible; live tests are bounded by the capacity gate and retry
    budget.

## Operator acceptance

This proposal (Revision 5d) preserves the output of six cross-orchestrator
review relay sessions (all converged, zero disputes across 42 total findings),
adds the targeted recovery/evidence hardening update, and records the Codex
red-team findings on pool-test scope and promotion identity. The Revision 5d
partner re-review is pending. Relay convergence is review provenance; it is
not evidence that either live selector is conformant.

The proposal is offered for operator acceptance as an implementation-planning
contract, not as authorization to activate live routing.

**Acceptance means:** proceed to native implementation planning in both
hosts against this contract, with the acceptance gates above as the
definition of done. Live activation requires fresh source evidence for every
gate, including executable cross-host fixtures and live-path receipts.

**Non-acceptance means:** identify which finding or correction needs
further iteration before implementation begins.

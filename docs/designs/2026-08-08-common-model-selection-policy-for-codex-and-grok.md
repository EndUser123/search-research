# Common model-selection policy for Codex and Grok

**Date:** 2026-08-08  
**Last updated:** 2026-08-10 — shared effort/thinking contract added; live conformance remains open
**Status:** Revision 5g — shared effort/thinking contract added; no new cross-host relay attestation; not live or conformant
**Revision:** 5g — aligns effort levels across Grok and Codex/Pi, separates effort from orchestration packs and token limits, and defines comparable benchmark cohorts
**Audience:** Grok Build and Codex maintainers  
**Scope:** Worker-model selection, quota/capacity pacing, benchmark evidence, shared effort/thinking controls, and the boundary between Codex and Grok orchestration.

## Revision 5 change log

Revision 5b incorporated all 42 findings from six cross-orchestrator review
relay sessions (all converged, zero disputes). Revision 5c preserved that
baseline and added the quota-recovery contract, evidence-scope corrections,
and explicit acceptance tests. Revision 5d and 5e record the earlier Codex
red-team synthesis and benchmark-artifact inventory. Revision 5f applies the
latest direct red-team hardening below; it is not a new conformance attestation.

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

**Revision 5e benchmark artifact update (2026-08-09):**

24. Added a Codex-owned offline capability/difficulty manifest and receipt
    evaluator with 16 cases across capability/code_pool suites and four
    difficulty tiers. Targeted harness tests pass; live adapter, executable
    fixture/checker packs, provider-pool recovery tests, and paired cross-host
    receipts remain open.

**Revision 5f direct red-team hardening (2026-08-09):**

25. Separated task-fit dimensions (`capability`, `difficulty`) from the
    caller-supplied `risk_class` and `spend_class` gates, with explicit defaults
    and ambiguity escalation.
26. Distinguished provider, model, route, invocation method, orchestrator,
    harness, verifier, and quota-pool/account identity; a provider name is not
    allowed to stand in for a capacity pool.
27. Made tool-loop promotion require method-specific, checker-backed evidence
    with an exact method identity, complete tool trace, N>=10 samples, and a
    Wilson lower-bound floor; raw success rates and HTTP-only results do not
    transfer into tool-loop eligibility.
28. Corrected the pool-suite contract so difficulty is represented by task
    cohorts, not thresholds alone, and clarified the host-specific status of
    the Grok and Codex benchmark artifacts.
29. Made weighted-pool rounding, diverse-panel sampling, requested panel size,
    and reservation failure behavior deterministic and unambiguous.
30. Added idempotent bounded resubmission, side-effect retry protection, and
    UTC/provider-clock rules for reset and reprobe timestamps.
31. Prevented adapters from using `rate_limited_only` as a catch-all for
    unknown quota semantics; unknown capacity remains explicitly unknown.

**Revision 5g shared effort/thinking update (2026-08-10):**

32. Added a common `low|medium|high|xhigh` execution-effort vocabulary aligned
    to the Grok phase matrix and Codex/Pi native thinking controls; separated
    it from capability, difficulty, risk, spend, H0-H6 orchestration packs,
    provider quota, and token limits.
33. Added fixed primary-effort, sensitivity, and explicit no-thinking control
    cohorts so benchmark results are comparable without treating a token cap
    or a retry as a thinking-level change.
34. Required requested/effective/native effort, support/clamping, run
    condition, exact command, and watchdog evidence in benchmark receipts;
    prior off/low Codex/Pi refresh results are retained as historical
    diagnostics and are not promoted under the new common contract.

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

- **Unknown-capacity rule** — the current implementation admits missing or
  stale capacity for ordinary work, but the selector does not yet pass task
  class/spend semantics into the capacity decision. That is an implementation
  defect and does not satisfy the policy rule that limits disclosed uncertainty
  to bounded non-spend work.

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

A Codex-owned offline capability/difficulty benchmark foundation is now
present, but it is not a live conformance implementation. It provides a
deterministic manifest, receipt contract, and evaluator; it does not yet
invoke providers, execute model-produced fixtures in a live sandbox, write
fleet telemetry, or produce paired Codex/Grok receipts.

### Codex benchmark artifacts — offline foundation (2026-08-09)

The completed Codex-owned workspace artifacts are:

- `P:\packages\codex-external-delegation\benchmarks\capability-difficulty\README.md`
  — suite scope, receipt contract, offline commands, promotion rule, and
  Grok merge points.
- `P:\packages\codex-external-delegation\benchmarks\capability-difficulty\src\manifest.mjs`
  — the stable 16-case manifest spanning `capability` and `code_pool` suites
  and `easy`, `medium`, `hard`, and `expert` tiers.
- `P:\packages\codex-external-delegation\benchmarks\capability-difficulty\src\evaluate.mjs`
  — manifest/run validation, exact binding checks, quality-versus-blocked
  outcome separation, per-cell aggregation, and Wilson lower bounds.
- `P:\packages\codex-external-delegation\benchmarks\capability-difficulty\bin\capability-difficulty.mjs`
  — offline `manifest`, `evaluate`, and `aggregate` CLI commands.
- `P:\packages\codex-external-delegation\tests\capability-difficulty.test.mjs`
  — 10 targeted tests covering manifest stability, promotion floors, blocked
  quota/transport outcomes, binding scope, malformed receipts, and adversarial
  aggregation cases.

Validation recorded for this update:

- From `P:\packages\codex-external-delegation`,
  `node --test tests/capability-difficulty.test.mjs`: **10/10 passing**.
- The package-wide `npm test` result is **143/147 passing**; the four failure
  reports are in the existing `tests/review-relay.test.mjs` suite. This is not
  a clean package baseline and does not invalidate the targeted benchmark
  result.

The remaining Codex benchmark work is the live provider/model adapter,
versioned task fixtures and objective checker artifacts, native sandbox
execution, provider-pool recovery tests, cross-host manifest/checker
conformance, and paired live receipts. Until those exist, this foundation
must not authorize model promotion or be described as fleet conformance.

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
| Provider capacity health | Can this identified capacity scope serve requests right now? | `capacity_pool_id` + account + endpoint + window | Capacity state (fresh/stale/exhausted/unknown) | Capacity admission only |
| Code-model capability | Can this exact model binding perform coding work? | Binding fingerprint + capability/difficulty cohort | Calibration `verification_passed` and quality evidence | Cohort-scoped promotion |
| Production evidence | How well does it perform real work? | Binding fingerprint + task cohort | Routing-eligible quality, latency, verification | Runtime ranking |

Capacity health is not model quality. Capability is not capacity health.
Production evidence is neither calibration suite.

### Identity axes and capacity scope

The selector must keep four identities separate. A provider, model, method,
and orchestrator are not interchangeable labels:

| Identity | Required meaning | May be reused as evidence for |
|---|---|---|
| Task contract | `capability + difficulty + risk_class + spend_class + write_intent` | Only the same or an explicitly broader, safer task cohort |
| Execution binding | `orchestrator + invocation_method + provider + model + route + harness/prompt/result/verifier contracts` | The exact binding fingerprint only |
| Capacity scope | `capacity_pool_id + account_id + endpoint + window_id/unit` | The same independently limiting pool/window only |
| Evidence cohort | Binding fingerprint + task contract + fixture/checker manifest | Runtime ranking only when the cohort is routing-eligible |

`provider` identifies the route owner; it does not prove that all models or
accounts under that provider share one limiter. The adapter must emit a stable
`capacity_pool_id` (and, when applicable, `account_id` and `window_id`) for
each independently limiting pool. If that scope cannot be established, the
capacity state is `unknown`; it must not be silently treated as a shared pool
or as `rate_limited_only`.

The task contract is part of the selection input and receipt. A result from a
read-only reasoning task cannot silently promote a write-capable tool-loop
binding, and a capacity observation for one account cannot authorize another
account merely because the provider and model names match.

### Provider capacity health

The registry may currently configure one API key per provider, but the policy
does not infer `provider = capacity_pool`. The adapter must prove which models,
routes, accounts, and windows share a limiter and emit that scope explicitly.
The capacity gate checks the identified pool's current state against the
request's task contract and demand.

Two models share a rate limit only when their normalized `capacity_pool_id`,
account, endpoint, and limiting window establish that fact. Exhausting one
pool may affect every model in that pool, but must not quarantine unrelated
models merely because their provider names match.

What this covers:
- fresh vs stale capacity observations
- exhausted quota (0%) blocking
- rate-limit backoff and retry-after handling
- reset window behavior

### Code-model capability suite

This suite certifies one exact execution binding in one capability/difficulty
cohort:

```text
orchestrator + invocation_method + provider + model + route + harness +
verifier + capability/difficulty cohort + capacity scope
```

The runner may accept a short model alias only when it resolves to exactly
one binding and records the resolved identity before telemetry is written.

The current Grok artifact (`pool_test.py`) is a HumanEval-style coding
calibration runner: 13 code generation problems, sandboxed execution,
binary pass/fail scoring. It provides a provisional standalone-code
calibration signal; it does not by itself prove tool-loop capability or clear
the common N>=10/Wilson promotion gate.

Calibration evidence has `routing_eligible: false` and must not influence
runtime ranking. It may support promotion only when:

1. exact binding identity and lane match;
2. `success=true` and explicit `verification_passed`;
3. no timeout, malformed-output, identity, or scope error;
4. the operator-configured lane floor is met; and
5. promotion is scoped to the tested lane only.

The common policy default and promotion floor is N>=10 lane-appropriate
verified successes per cell. An implementation configured below N=10 is
provisional and non-conformant; it may be used only for exploratory
calibration and must not authorize promotion or claim common-policy
conformance.

`quality_score` is a measurement, not a substitute for `verification_passed`.

The existing HumanEval-style runner is a calibration signal, not sufficient
promotion evidence. A higher acceptance tier (repository-context coding,
patch application, tool use, independent verification) gates higher-risk work
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

`active` must not be interpreted as globally eligible. Tool-loop calibration
must not silently authorize reasoning, diverse-panel, or other capabilities.
The legacy `coding` and `critic` labels are aliases only.

### Cross-host compatibility

Codex and Grok should use the same problem manifest (fixture hash). Until
an executable Codex counterpart with native task execution and a paired
receipt exist, the Codex capability/difficulty suite remains a target
contract, not a verified fact. The Codex artifacts listed above currently
provide the manifest and receipt/evaluator foundation only.

### Capability/difficulty suites and provider-pool suites

There are two different test families, and the names must not be collapsed:

1. **Capability/difficulty suites** evaluate an exact execution binding on
   labeled task cohorts. They can produce lane-scoped model capability
   evidence, but they do not prove quota or provider capacity.
2. **Provider-pool health/recovery suites** evaluate an identified capacity
   scope (`capacity_pool_id`, account, endpoint, and window). They can prove
   admission, backoff, reset, reprobe, and retirement behavior, but they do
   not promote a model or prove task quality.

Capability/difficulty suites need distinct task cohorts and objective checkers.
Difficulty must not be represented only by changing a pass threshold over the
same easy cases. A suite may reuse explicit anchor cases for regression
coverage, but those cases do not count as independent evidence for multiple
difficulty tiers.

| Suite | Capability | Difficulty | What it tests | Scoring | Current status |
|---|---|---|---|---|---|
| Coding capability calibration | tool-loop | trivial + standard | Standalone code generation plus sandboxed execution | Objective pass/fail with `verification_passed`; floor is lane policy, not a substitute for evidence | Grok HTTP-only runner built (13 cases); Codex offline 16-case manifest/evaluator only |
| Coding acceptance test | tool-loop | hard | Repository context, multi-file patches, tool use, and independent verification | Verified pass/fail plus quality metrics and tool trace | Future work |
| Mechanical capability calibration | mechanical | trivial + standard | Extraction, formatting, and structured output with expected output | Exact match plus verifier receipt | Future work |
| Reasoning capability calibration | reasoning | trivial + standard | Analysis tasks with known-correct conclusions | Rubric score plus verification state | Future work |
| Reasoning deep/panel test | reasoning | hard | Architecture and root-cause analysis from ambiguous symptoms | Rubric score, verification state, and family-diversity receipt where panelized | Future work |
| Provider-pool admission and recovery | capacity health | n/a | Current admission, reserve accounting, temporary backoff, and bounded retry | Immediate decision plus scoped capacity receipt | Future work; separate from capability suites |
| Provider-pool reset/reprobe | capacity health | n/a | Multi-hour/monthly reset, post-reset reprobe, stale observation, and unknown scope | State transition receipt plus fresh-observation proof | Future work; separate from capability suites |
| Provider-pool retirement/multi-pool | capacity health | n/a | Independent window exhaustion and confirmed route retirement | Per-pool decision plus terminal/non-terminal outcome | Future work; separate from capability suites |

Each host may use native runner infrastructure, but the shared receipt must
retain the fixture-manifest hash, task/difficulty cohort, exact binding
fingerprint, verifier/checker version, and explicit verification state.
Grok's `pool_test.py`/`telemetry.log_call()` path and Codex's JS evaluator are
not interchangeable evidence merely because their case IDs look similar.

The trivial/standard tiers require distinct, labeled task cohorts with
objective differences in context, ambiguity, tool interaction, or verification
burden. The hard tier needs genuinely different problems (multi-file,
ambiguous, real repository work) and is a separate suite. Threshold changes
alone never turn a trivial fixture into standard or hard evidence.

**Codex target:** same problem manifests (fixture hash), native JS sandbox per
suite, and the same calibration-cohort telemetry pattern. The current Codex
artifacts provide the offline manifest and evaluator only; native sandbox,
live adapter, and telemetry integration remain future work.

### Method-aware testing

The invocation method changes quality, not just speed. Production
telemetry shows dramatic success-rate variation across methods for the
same model:

| Model | HTTP success | PI success | opencode success |
|---|---|---|---|
| `nim-openai-gpt-oss-20b` | 0.980 | 0.918 | 0.233 |
| `cohere-command-a-reasoning` | 0.960 | 0.680 | 0.600 |
| `zen-deepseek-v4-flash-free` | 0.943 | 0.374 | 0.741 |

**Evidence status:** these values are illustrative historical observations,
not current promotion evidence. This document does not attach the raw receipt
paths, sample/cohort definitions, dates, verifier versions, or binding hashes
needed to audit them. They must not set a policy floor or authorize routing
until method-specific receipts with that evidence are available.

A model that writes correct code via direct HTTP can fail via opencode
because the agent harness adds tool schemas, system prompts, and context
management that change the model's behavior. This is the "tool-calling
reliability is not predicted by general quality" finding from production
practice (Inferbase 2026).

**Implication for pool testing:** the binding fingerprint includes
`invocation_method`. Pool test evidence is only valid for the method
tested. A model that passes the HTTP pool test has not proven it can
perform via spawn, PI, or opencode.

**Test the primary method.** Each candidate's `dispatch_paths` declares
the runtime method order (e.g., `["spawn", "pi", "http"]`). The capability
suite should run through the primary method — the one the runtime will try
first — and record that exact binding. Testing only via HTTP (as the v1 runner
does) proves HTTP capability but not spawn/PI/opencode capability. A fallback
method is a new execution binding: evidence from the primary method must not
silently authorize it.

**Method-specific failure modes:**
- HTTP: raw model output, no wrapper — tests model quality directly
- PI: subprocess with system prompt injection — tests model + prompt compat
- opencode: full agent scaffolding with tool schemas — tests tool-call format reliability
- spawn: full Grok Build agent loop with tools, worktree, hooks — tests the complete binding

The v1 pool test runner uses HTTP for speed and simplicity. The v2
runner adds method-aware testing: run the same labeled task cohorts through the
candidate's primary dispatch path, not just HTTP. Method-aware testing
is more expensive (spawn requires the full agent infrastructure) but
produces evidence that matches how the model is actually used.

### Effort-stratified benchmark method

Method and effort are independent axes. A benchmark must identify both: the
same model may behave differently through HTTP, Pi, opencode, or spawn, and it
may behave differently at `low`, `medium`, `high`, or `xhigh` effort. Neither
axis may be omitted from a promotion cohort.

For the primary benchmark cohort, use one policy-selected effort per case and
hold it constant for every candidate in that comparison:

| Case class | Primary effort | Separate sensitivity runs |
|---|---|---|
| Mechanical / extraction / routine verification | `low` | `medium` only when quality is borderline or the policy explicitly asks |
| Normal coding / tool-loop / tests | `medium` | `low` and `high` when measuring cost-quality tradeoffs |
| Reasoning / planning / debugging / critique | `high` | `medium` and `xhigh` when supported and explicitly authorized |
| Hard security / regression / architecture / consequential review | `high` | `xhigh` as an explicit sensitivity or acceptance condition |

Each sensitivity run receives a new run ID and remains a separate evidence
cell. Do not pool `off`, `low`, `medium`, `high`, or `xhigh` results, and do
not label a different effort level as a retry. An `off` run is useful only as
an explicit no-thinking control to quantify the effect of effort; it cannot
clear a thinking-enabled quality gate.

The minimum receipt fields for this method are:

```text
fixture_manifest_hash
case_id / capability / difficulty
provider / model / invocation_method / orchestrator / binding_fingerprint
requested_effort / effective_effort / native_effort
effort_support / effort_source / run_condition
native_command_or_args_hash
native_command_or_args_ref
watchdog_timeout_ms / latency.p90_ms / time_to_verified_result_ms
verification_passed / checker_version / tool_trace_complete
attempt / retry_class / failure_class
```

The exact native command or argument hash and a redacted command/argument
reference matter because a packet can omit a field while the runner supplies a
default. Receipt review must therefore
compare the requested value, the effective value observed by the host, and
the native control actually passed to the provider or model runtime. If the
host cannot prove the effective level, the result is `unknown` and remains
diagnostic rather than promotion evidence.

The benchmark must distinguish three timing concepts:

- `latency.p90_ms`: valid-result latency for ranking within the exact cohort;
- `time_to_verified_result_ms`: unconditional operational outcome, including
  failures and any authorized rework; and
- `watchdog_timeout_ms`: a process-safety ceiling whose expiry is recorded as
  a timeout, not converted into a quality or effort score.

The evaluation envelope may include `max_latency_ms` for reporting or a
checker, but it must not be confused with a provider kill timer or a token
budget. If a run exceeds the envelope, record the outcome and keep the raw
receipt; do not silently alter the effort cohort. The watchdog must be long
enough to cover the declared effort and method or the cohort is
method/runner-invalid, not evidence that the model is intrinsically poor.

**Current Codex/Pi comparability note (2026-08-10):** the refresh under
`P:\tmp\codex-pi-capability-benchmark-20260809-refresh` is retained for
harness diagnostics but is not promotion evidence under this contract. Its
representative generated packets used `--thinking off` for read-only runs and
`--thinking low` for coding runs; explicit token-cap fields were null, and the
process watchdog was 120 seconds. Those settings do not form the shared
mechanical/reasoning/coding primary cohort (`low`/`high`/`medium`) and must not
be ranked against a conformant run.

**Grok-side conformance note (2026-08-10):** the Grok pool test harness
(`~/.grok/skills/model-benchmark/scripts/pool_test.py`) implements the R5g
effort contract as of commit `96cd88c`:

- Capability-to-effort mapping: `mechanical`→`low`, `tool-loop`→`medium`,
  `reasoning`→`high`. Override via `--effort` for sensitivity runs.
- HTTP method: sends `reasoning_effort` field in the OpenAI-compatible
  payload where the provider supports it. `max_tokens` is a non-constraining
  safety ceiling (floor 4096), not an effort control.
- PI method: passes `--thinking <effort>` per the capability default.
- Telemetry: every pool-test record encodes `effort=<level> method=<method>`
  in the notes field, enabling cohort segmentation by requested effort.
- Pool tests launched before this commit (NVIDIA reasoning run
  `019fee02`, ZAI tool-loop `019fee05`, OpenRouter free-tier `019fee11`)
  did not send or record effort parameters. Their results are retained as
  pre-conformance diagnostics and must be re-run or re-labeled with the
  policy-default effort before they can serve as promotion evidence.
  Specifically: NVIDIA reasoning = `high` (was: no effort sent),
  ZAI tool-loop = `medium` (was: no effort sent),
  OpenRouter free-tier tool-loop = `medium` (was: no effort sent).

### Tool-evidence requirement for tool-loop capability

A model that passes the coding pool test via HTTP has proven it can
write standalone code. It has NOT proven it can make tool calls under
an agent harness. Production telemetry confirms the gap: a model can
score 98% success via direct HTTP but 23% via opencode because the
agent harness adds tool schemas that the model cannot reliably format.

**The rule:** tool-loop capability requires method-specific, checker-backed
evidence. A candidate is excluded from tool-loop tasks unless it has either:

1. **Calibration evidence from the exact tool-carrying method** used by the
   route (for example, a pool test run via `--method opencode`, `--method pi`,
   or `--method spawn`), OR
2. **Production evidence** from that exact method with at least N>=10 valid
   verified attempts and a Wilson lower bound at or above the configured
   tool-loop floor (default: 75% policy default).

For either path, the receipt must include the exact binding fingerprint,
`fixture_manifest_hash` or production cohort ID, `checker_version`,
`method_contract_hash`, `tool_trace_complete`, and `verification_passed`.
For cases whose contract requires a tool action, `tool_trace_complete` must
also prove the expected tool action occurred in the declared sandbox or
worktree. A raw success rate, an HTTP-only receipt, or a result without a
complete tool trace cannot clear this gate.

Models with only HTTP evidence may serve `mechanical` and `reasoning`
capabilities (no tools), but are restricted from `tool-loop` until
they accumulate tool-carrying-method evidence.

**Implementation:** the gate reads the evidence cache for the candidate's
exact tool-carrying-method binding. If no qualifying cohort exists, if its
Wilson lower bound is below the floor, or if the tool trace/checker evidence is
incomplete, the `tool-loop` capability is gated out. Existing production
receipts may satisfy the rule only when they already contain the required
fields; otherwise a method-aware calibration suite is required. A method-aware
pool test is the certification mechanism for the calibration path: run the
coding problems through the route's primary tool-carrying method and retain
the resolved method, checker, trace, and sandbox identity.

### Grok-side test runner — shared infrastructure (2026-08-11)

The pool test infrastructure is Grok-owned Python that both orchestrators
can invoke. Codex does NOT need to reimplement these — it can call the
same scripts. This section documents the exact commands, shared modules,
and normalization tables Codex needs.

**Pool test commands:**

```bash
# Provider-wide discovery + probe + test (RECOMMENDED — tests all alive models)
python ~/.grok/skills/model-benchmark/scripts/pool_test.py \
  --provider nvidia --capability tool-loop --probe

# Free-tier only (OpenRouter — filters by API pricing field, not :free label)
python ~/.grok/skills/model-benchmark/scripts/pool_test.py \
  --provider openrouter --free-only --capability tool-loop --probe

# Single model (requires registry ID that matches config.toml slug)
python ~/.grok/skills/model-benchmark/scripts/pool_test.py \
  --model nvidia-nemotron-3-super-120b --capability reasoning

# Method-specific (HTTP, PI, or opencode — for tool-evidence requirement)
python ~/.grok/skills/model-benchmark/scripts/pool_test.py \
  --provider nvidia --capability tool-loop --method pi --probe

# Capability options: tool-loop (coding), reasoning, mechanical
# Method options: http (default), pi (agent harness), opencode

# Auto-promote models that pass the evidence threshold
python ~/.grok/skills/model-quota/scripts/promote_models.py [--dry-run] [--verbose]
```

**Shared PI dispatch module** (`~/.grok/skills/model-quota/scripts/pi_dispatch.py`):

Both orchestrators should use this module for PI-based dispatch. It
absorbs binary resolution, provider mapping, transient-fail retry,
telemetry logging, and concurrency tracking. Codex's own Pi bridge
(`P:\packages\codex-external-delegation\src\commands.mjs`) may wrap this
or replicate the interface contract:

```python
from pi_dispatch import dispatch
result = dispatch(
    prompt="...",
    lane="critic",          # coding, reasoning, mechanical, critic
    effort="medium",        # R5g effort level
    max_retries=2,          # re-select different model on transient failure
    timeout=600,            # PI needs more than HTTP (10 min)
    model_override={"model": "glm-4.7", "provider": "z.ai"},  # force specific model
)
# result.success, result.content, result.model_used, result.retries, result.warnings
```

**Provider name normalization table** (telemetry ↔ registry mapping):

| Provider in telemetry | Registry provider | Config.toml prefix | PI provider |
|----------------------|-------------------|-------------------|-------------|
| `nvidia` | `nvidia` / `nim` | `nvidia-` / `nim-` | `nvidia-nim` |
| `z.ai` | `zai` | `glm-` | `zai` |
| `openrouter` | `openrouter` / `or-` | `or-` | `openrouter` |
| `cohere` | `cohere` | `cohere-` | `cohere` |
| `minimax` | `minimax` | `minimax-` | `minimax` |
| `opencode` | `opencode` / `zen` | `zen-` | `opencode` |

Model names use dots in API/telemetry (`glm-4.7`) but dashes in registry
IDs (`zai-glm-4-7`). The promotion script normalizes this; direct
telemetry queries must account for it.

**Concurrency limits per provider** (from `concurrency_probe.py`, 2026-08-11):

| Provider | Cross-model ceiling | Shared pool? | Implication |
|----------|-------------------|-------------|-------------|
| MiniMax | 2 | Yes | Cap total parallel at 2 |
| NVIDIA | 7 | Yes (high ceiling) | ~7 parallel OK |
| ZAI | 7 | No | Full cross-model parallelism |
| OpenRouter | 8 | No | Best for parallel dispatch |

The concurrency gate (`concurrency_gate.py`) enforces these at spawn time.
Codex's parallel worktree benchmark must respect these limits — exceeding
them produces 429 cascades that corrupt evidence.

**Test runner capabilities (3 suites × 3 methods):**

| Capability | Problems | Scoring | Effort (R5g) | What it certifies |
|-----------|----------|---------|-------------|-------------------|
| `tool-loop` | 18 (HumanEval + harder) | Sandboxed execution | `medium` | Can write correct code |
| `reasoning` | 8 (GSM8K + logic) | Exact-match answer | `high` | Can reason step-by-step |
| `mechanical` | 8 (extraction + formatting) | Exact-match output | `low` | Can follow format instructions |

**Evidence pipeline:**

```
pool_test.py → usage.db (telemetry)
                          ↓
promote_models.py → fleet-models.json (lifecycle updates)
                          ↓
pick_model.py → gate_results() (6 gates: capability, policy, lifecycle,
                                  health, capacity, concurrency)
                          ↓
PreToolUse_spawn_model_gate.py → enforce at spawn time
```

**Promotion threshold:** 5 verified successes per lane. A model with
18/18 tool-loop + 8/8 reasoning + 6/8 mechanical gets promoted to active
for all 3 lanes automatically. Run `promote_models.py` after each test
batch to update the registry.

The safety rule is simple: a model with no qualifying tool-use measurement is
excluded from tool traffic even when its general scores are excellent. A
generalist cannot vouch for a capability that nobody measured under the
actual method and verifier.

### Grok acceptance of R5f hardening (session 019fdf47, 2026-08-09)

Grok accepts the R5f hardening with three operational clarifications:

1. **Identity shorthand.** The 12-field identity contract is correct for
   the policy. In practice, most fields are constant across the fleet
   (same orchestrator, same harness version, same verifier). The
   implementation may use shorthand (omitting constant fields from
   per-record telemetry) as long as the constant values are declared
   once in the registry and the receipt can reconstruct the full
   identity. The discriminating fields for evidence segmentation are
   provider + model + invocation_method + capability cohort.

2. **Provisional fallback.** "A fallback method is a new execution
   binding" is architecturally correct. Operationally, when the
   primary method is temporarily unavailable and a fallback method
   lacks independent certification, the selector should allow
   provisional fallback with an uncertainty disclosure in the receipt
   — not hard-block the task. The provisionally-selected model is
   flagged as `method_fallback_unverified` and the production telemetry
   from that call feeds the fallback method's evidence cohort. Hard-
   blocking creates an availability failure that the operator did not
   intend.

3. **Difficulty cohort sizing.** "Difficulty must be represented by
   distinct task cohorts" requires enough problems per tier to reach
   the N>=10 floor. The current suites have 5 trivial + 3 standard
   mechanical problems and 4 trivial + 4 standard reasoning problems.
   These are insufficient for independent per-tier promotion. The
   implementation will use combined-tier promotion (trivial+standard
   pooled) until each tier has >=10 problems, at which point per-tier
   promotion activates. This is labeled as provisional.

These are operational allowances, not policy changes. The target
contract remains as R5f specifies; the implementation converges
toward it as the problem banks grow.

## What is shared and what remains separate

### Shared

Codex and Grok should share or conform to:

- candidate discoverability and model metadata;
- provider aliases and canonical model identifiers;
- capability and context metadata;
- lifecycle and policy-state vocabulary;
- task-lane definitions and task-classification contract;
- common execution-effort vocabulary, run conditions, and effort receipt
  fields;
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

### Task-fit dimensions and policy gates

Capability and difficulty are the two task-fit dimensions. Earlier revisions
conflated them into fixed "lanes" (coding, reasoning, mechanical, critic),
which broke down when task complexity varied within a single lane. The caller
also supplies two non-interchangeable policy gates—execution risk and spend
sensitivity—because the capacity table cannot safely infer either one from
capability alone.

**Dimension 1: Capability required** — what kind of work is this?

| Capability | What it means | Carries tools? | Write-capable? | Selection strategy |
|---|---|---|---|---|
| `tool-loop` | The main agent loop: reads context, calls tools, writes code, modifies files | Yes | Yes (worktree) | Pin or vetted pool (behavioral stability matters) |
| `reasoning` | Analysis, planning, debugging, synthesis, single-model critique | No | No | Weighted pool (quality matters) |
| `mechanical` | Extraction, formatting, structured output, routine verification | No | No | Cheapest capable model (cost matters most) |

The tool-loop vs no-tool split is the highest-leverage distinction: it
determines whether the model is pinned (for behavioral stability) or
pooled (for cost/quality optimization). A model that writes code under
a tool schema has different requirements than one summarizing output.

**Dimension 2: Difficulty** — how hard is this within its capability band?

| Difficulty | What it means | Routing effect |
|---|---|---|
| `trivial` | One-step, well-defined, low ambiguity | Cheapest model in the band |
| `standard` | Multi-step but clear scope | Standard pool |
| `hard` | Ambiguous, multi-system, high stakes | Best available model |

Difficulty is applied within a capability band. A trivial coding task
(add an import) and a hard coding task (debug a race condition) are both
`tool-loop` capability, but the former can use a cheap model and the
latter needs the best available.

**Policy gate 1: execution risk and write intent**

| `risk_class` | Meaning | Required control |
|---|---|---|
| `safe_read` | Read-only, reversible, low-impact work | Normal gates and bounded exploration may apply |
| `isolated_write` | Writes confined to an authorized isolated worktree or sandbox | Exact tool-loop evidence and worktree identity required |
| `high_impact` | Production, credential, destructive, or otherwise consequential work | No exploration; explicit operator/task authorization and strongest evidence |

**Policy gate 2: spend/capacity sensitivity**

| `spend_class` | Meaning | Capacity implication |
|---|---|---|
| `non_spend` | No monetary charge and no protected scarce pool is consumed | Bounded non-spend rules may apply |
| `bounded_spend` | Automatic use is allowed under a declared per-task and aggregate budget | Require a current budget/capacity decision |
| `scarcity_sensitive` | Consumes a protected, unique, or reset-bound pool | Require reserve-aware admission; no exploration or silent retry |

### Legacy lane mapping

The v1 lanes map to the new two-dimensional classification:

| Legacy lane | New capability | Default difficulty |
|---|---|---|
| `coding` | `tool-loop` | `standard` |
| `reasoning` | `reasoning` | `standard` |
| `mechanical` | `mechanical` | `trivial` |
| `critic` | `reasoning` + diverse-panel constraint | `hard` |
| `calibration` | (lifecycle state, not a capability) | n/a |

The `critic` lane becomes `reasoning` capability with a `diverse_panel`
selection constraint, not a separate capability. The `calibration` lane
is a lifecycle state (candidate onboarding), not a task classification.

### Classification authority

The task classification is determined by the **dispatching skill or
caller**, not by the selector. The selector receives capability, difficulty,
risk, write intent, and spend class as inputs; it does not infer them from the
prompt content. If the caller does not specify, the safe default is
`reasoning` / `standard` / `safe_read` / `non_spend`. Any declared write intent
escalates capability to `tool-loop` and risk to at least `isolated_write`.
Unknown spend sensitivity escalates to `scarcity_sensitive`; it must not be
silently treated as `non_spend`.

### Ambiguity handling

When a task straddles capabilities (e.g., "read this file and summarize
it" could be mechanical or reasoning):

1. The caller declares the classification explicitly.
2. If the caller is ambiguous, the **higher-capability** classification
   is used (reasoning over mechanical, tool-loop over reasoning).
3. For write-capable tasks, ambiguity always resolves to `tool-loop`.
4. If risk or spend sensitivity is ambiguous, resolve upward to
   `high_impact` or `scarcity_sensitive` respectively.
5. The receipt records the declared classification, the ambiguity resolution
   (if any), and the classifier provenance.

All tasks that write files must use the `tool-loop` capability with worktree
isolation and `risk_class=isolated_write` or higher. The `mechanical`
capability is strictly read-only; no exceptions.

### Shared execution-effort contract

`effort` is a cross-host request and evidence dimension. It is not a
capability, difficulty, risk, spend class, quota tier, token budget, or
orchestration pack. The selector must not infer effort from model price or
provider name, and an effort value must not be used to bypass any capability,
capacity, or verification gate.

The common vocabulary is intentionally smaller than any one host's native
controls:

| Common effort | Default use | Policy meaning |
|---|---|---|
| `low` | Mechanical extraction, formatting, inventory, and other routine read-only work | Minimum thinking effort that is expected to be sufficient |
| `medium` | Normal coding/tool-loop work, tests, and routine verification | Standard production effort |
| `high` | Reasoning, planning, debugging, critique, security/regression work, architecture, and consequential review | Higher-quality effort is required before ranking or acceptance |
| `xhigh` | Explicit deep/ultrathink work or an operator-approved high-consequence sensitivity run | Deliberately expensive sensitivity/control condition, not a default |

`off` is not a common effort level. It is an explicit no-thinking control
condition and must be represented as a separate `run_condition`, never merged
with `low` or with any thinking-enabled result. A host may expose additional
native levels (for example `minimal` or `max`) or an intermediate
`medium-high`; those values remain host-specific and must be normalized to the
nearest common policy level with the exact native value retained in the
receipt. The normalization must be declared, not silently inferred.

The default mapping follows the shared Grok phase policy—discovery low,
coding/tests medium, plan/think/debug/critic high, and verify medium-high—and
the supported Pi thinking vocabulary. In the common discrete vocabulary,
routine verify/test work is `medium`, while evidence-critical review or
ship-check work is `high`. Grok H0-H6 packs (Safety, Think, Plan, Discover,
Parallel, Goal, Verify) are orchestration procedures, not replacements for
the worker `effort` field; their pack ID may be recorded as host provenance.

Every effort-controlled run must record at least:

```text
requested_effort: low | medium | high | xhigh
effective_effort: low | medium | high | xhigh | unknown
native_effort: <host/provider value, if exposed>
effort_support: supported | clamped | unsupported | unknown
effort_source: policy_default | caller_override | model_native | control
run_condition: primary | sensitivity | no_thinking_control
```

The following rules are normative:

1. The lane-to-effort mapping is a default. A caller may override it only
   explicitly; the receipt records the override and rationale.
2. Candidate comparisons use the same case, binding fingerprint, requested
   effort, run condition, and verification contract. Different effort levels
   are different benchmark cells, not pooled repetitions.
3. Unsupported or clamped effort is disclosed and segmented. It cannot clear
   a gate for the requested level, and it cannot be silently relabeled as a
   supported result.
4. `max_tokens`, `max_output_tokens`, and `reasoning_tokens` are not common
   effort controls and must not be sent as test-set request caps. If a host
   reports actual token usage, it may be retained as diagnostic telemetry, not
   used as a substitute for effort. Existing case-budget fields such as
   `max_latency_ms` are evaluation metadata unless a runner explicitly proves
   enforcement; they are not provider request parameters.
5. A process watchdog is a safety ceiling, not the target latency. It must be
   recorded separately from valid-result latency, timeout outcome, and
   `time_to_verified_result_ms`. Runs at `high` or `xhigh` must not be killed
   by an undisclosed effort-specific shortcut.
6. An alternate effort run is a sensitivity experiment, not an automatic
   retry. Retries are only for a declared transient failure policy and retain
   the same effort and case identity.

This contract is a compatibility boundary, not a claim that either native
runner currently enforces it. A host is non-conformant until its receipt
proves the requested-to-effective translation and its benchmark harness keeps
effort cohorts separate.

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

| Capability/cohort | Default floor | Minimum samples |
|------|--------------|-----------------|
| `mechanical` | 80% | 10 |
| `reasoning` | 70% | 10 |
| `tool-loop` | 75% | 10 |
| `reasoning + diverse_panel` | 70% | 10 |

The floor is compared against the one-sided Wilson lower bound, not the raw
success rate. A candidate clears promotion only when it has at least N>=10
lane/cohort-appropriate `verification_passed` samples, the lower bound meets
the configured floor, and no identity, scope, timeout, malformed-output, or
verification gate is violated. Legacy `coding` and `critic` field names may be
retained for compatibility, but they map to `tool-loop` and
`reasoning + diverse_panel` and must not create a second evidence cohort.

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

### Weighted-pool mode (reasoning, tool-loop lanes)

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

# Round weights to 6 decimal places for deterministic replay. Use a canonical
# largest-remainder adjustment in sorted candidate-ID order so the final
# vector is non-negative and sums exactly to 1.0 after serialization.
weights = largest_remainder_round(weights, decimals=6, order=stable_candidate_id)

selected = weighted_random_choice(eligible, weights, seed=random_seed)
```

**Missing-data fallback chain (ordered):**

1. p90 available: use p90, label `latency_source: "p90"`
2. p50 available but not p90: use p50, label `latency_source: "p50_provisional"`
3. Neither available: use lane median, label `latency_source: "lane_median_provisional"`
4. Lane median unavailable: BLOCKED

**Tie-breaking:** weighted selection remains random; a near-equal weight does
not silently become deterministic selection. The higher verified-success lower
bound and stable candidate ID are tie-breakers only for deterministic ranking
or `highest_weight` selection (such as panel member choice). Candidate order
is still canonical for serialization and replay.

Exploration (epsilon=0.1 for reasoning safe lanes): with probability
   epsilon, select a random eligible candidate. Disabled for write-capable
   (`tool-loop` capability).

### Diverse-panel mode (reasoning panel)

```text
# model_family is an explicit registry field (e.g., "deepseek-v4", "nemotron-3")
# DISTINCT from provider (e.g., "nvidia-nim", "zen")
# Two models sharing the same upstream model are the same model_family
families_available = distinct(model_family(c) for c in eligible)

MINIMUM_PANEL_QUORUM = 2  # distinct model_families required
if requested_size < MINIMUM_PANEL_QUORUM:
    return BLOCKED("requested panel size cannot satisfy independent quorum")
if len(families_available) < MINIMUM_PANEL_QUORUM:
    if operator_preauthorized_degraded:
        return DEGRADED_PANEL(reduced_diversity_receipt)
    else:
        return BLOCKED("insufficient model_family diversity for independent critique")

panel = []
panel_size = min(requested_size, len(families_available))
for family in sample(sorted(families_available), panel_size, seed=random_seed):
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
    if operator_preauthorized_degraded:
        return DEGRADED_PANEL(
            panel,
            mode="staggered_dispatch",
            reason="capacity reservation failed",
        )
    return BLOCKED("capacity reservation failed for panel")
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
for specific task types. `operator_preauthorized_degraded` must name the task
policy and permitted degradation; it is never inferred from provider failure.
Degraded mode is always disclosed in the receipt and cannot be used to claim
full panel-quorum evidence.

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
   the safe-calibration lane. Normal reasoning, tool-loop, or write-capable
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

| Verification state | Counts toward promotion? | Eligible for reasoning/tool-loop? | Eligible for calibration? |
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

A candidate may be calibrated on low-risk work in the `tool-loop` capability
(the only write-capable capability) with bounded scope and an isolated
worktree. The `mechanical` capability is strictly read-only; calibration tasks
that write files must use `tool-loop`, not `mechanical`. This is a containment
requirement. A candidate is not automatically eligible for reasoning or
write-capable work. A new, free, or statically high-priority model must not
displace an evidenced candidate without capability- and cohort-appropriate
evidence.

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

An adapter may report `rate_limited_only` only when it can observe live
rate-limit, concurrency, queue, or retry-after behavior and has evidence that
no remaining-window or monetary-budget semantics are being omitted. Missing
quota data is not proof of rate-limited-only capacity; when the limiter kind
or scope is uncertain, report `unknown` and disclose the missing signal.

The normalized adapter result should expose, when available:

```text
capacity_kind
capacity_pool_id + account_id + window_id
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
provider_observed_at + provider_clock_skew
source and freshness
unknown_reason
```

### Capacity decision table

Admissibility is determined by the following table, keyed by capacity_kind
and freshness. This table is normative — the selector does not invent
defaults when the adapter output is ambiguous.

`ordinary_auto_dispatch` means an automatically dispatched task whose declared
spend and risk policy permits normal capacity use. `bounded_non_spend` means no
monetary charge is incurred and the task is within the caller's bounded
non-spend budget. `scarcity_sensitive` covers protected, unique, reset-bound,
or otherwise reserved capacity. The caller must provide this class; the
selector must not infer it from the model name.

| capacity_kind | freshness | ordinary_auto_dispatch | bounded_non_spend | scarcity-sensitive task |
|---|---|---|---|---|
| `windowed_units` | fresh (<5 min) | allow if remaining > demand + reserve, apply pacing | allow if remaining > demand | allow only if remaining > demand + reserve and not forecast-exhausted |
| `windowed_units` | stale (>5 min) | block until refreshed | allow if route health is clean | block |
| `monetary_budget` | fresh | allow if remaining > demand + reserve | allow if remaining > demand | allow only if remaining > demand + reserve |
| `monetary_budget` | stale | block until refreshed | allow | block |
| `rate_limited_only` | live (429 health checked) | allow if no active 429/backoff | allow if concurrency state admits demand | allow if concurrency state admits demand |
| `rate_limited_only` | stale | block until refreshed | allow only if current route health admits demand and the caller's policy is bounded non-spend | block |
| `multi_pool` | fresh | check most restrictive window against demand + reserve | allow if all relevant windows admit demand | allow only if all windows clear demand + reserve |
| `multi_pool` | stale | block until refreshed | allow if route health clean | block |
| `unknown` | n/a | block unless the caller explicitly classifies the task as bounded non-spend | allow only with current route health and a bounded non-spend policy | block |

**Confirmed exhaustion or retry-after:** always blocks until the stated expiry
or an explicit fresh provider observation supersedes it. Elapsed time alone is
never evidence that the route recovered.

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

Each resubmission also records a new `dispatch_attempt_id`, the original
`task_id`, a stable idempotency key (when the provider supports one), and any
`reservation_id`. The original attempt is immutable. A side-effecting
tool-loop task must not be retried unless the caller proves the
previous dispatch did not start or supplies an idempotent operation key;
otherwise the result is `BLOCKED` for operator judgment. Queue ownership must
deduplicate the same task/binding/recovery window and consume one retry budget
atomically, so a crashed worker or two pollers cannot create duplicate writes.

All `observed_at`, `reset_at`, `deferred_until`, and `reprobe_at` values are
RFC3339 UTC timestamps. Adapters should retain the provider-reported timestamp
and local receipt time, plus a clock-skew estimate where available. An invalid,
ambiguous, or materially skewed reset timestamp produces `unknown` or
`reset_pending`, not an immediate retry. If the reset horizon has already
passed, the selector must still return `reprobe_at` until a fresh observation
proves `available`.

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

If `time until reset <= 0`, do not divide by zero or infer that quota is
available. Transition the window to `reset_pending`, return `reprobe_at`, and
require a fresh provider observation before ordinary or scarcity-sensitive
dispatch.

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

- task contract (`capability`, `difficulty`, `risk_class`, `spend_class`, and
  write intent), ambiguity resolution (if any), classifier provenance, and
  selection mode, plus a canonical `task_contract_hash`;
- selected provider, model, invocation method, orchestrator, and binding fingerprint;
- resolved route, harness/prompt/result/verifier contract hashes,
  `method_contract_hash`, and the `capacity_pool_id`/account/window scope used
  for admission;
- eligible candidates and rejection reasons (including lifecycle gate rejections);
- capability, policy, lifecycle, and capacity decisions;
- evidence cohort, binding fingerprint, sample count, freshness, and confidence;
- latency metrics used (including `latency_source: "p90" | "p50_provisional"`);
- capacity model, source freshness, unknown reason when applicable, and quota
  window/pacing state used;
- cost policy decision, without invented cost values;
- alternatives considered;
- `task_id`, `dispatch_attempt_id`, and `reservation_id` when capacity was
  reserved; recovery owner and retry budget when dispatch was deferred;
- **Replay fields (mandatory for weighted_pool and diverse_panel):**
  - `algorithm_version`: e.g., "v1"
  - `random_seed`: the PRNG seed used for weighted selection
  - `prng_version`: PRNG algorithm identifier
  - `normalized_weights`: the weight vector applied to eligible candidates, in canonical candidate ordering (sorted by candidate ID), rounded to 6 decimal places and required to sum exactly to 1.0 after largest-remainder rounding
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
- Effort-stratified results remain sequestered by requested/effective/native
  effort and run condition; no thinking-disabled, clamped, or unsupported
  result may clear a thinking-enabled cohort.
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
2. Shared task-lane, selection-mode, execution-effort, and run-condition
   vocabulary, plus the task-classification contract.
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
     are separate from capability/difficulty tests and production tool-loop
    evidence. Each live test records the full binding fingerprint, quota pool
    or account, capacity reservation, fixture manifest, verifier, and
    orchestrator/method identity. Pool health cannot promote a model, and
    calibration cannot rank production routing. Synthetic reset fixtures are
    used where possible; live tests are bounded by the capacity gate and retry
    budget.
12. **Effort and run-condition conformance:** both implementations accept the
    common effort vocabulary, record requested/effective/native values and
    support or clamping state, preserve primary/sensitivity/no-thinking
    cohorts, keep token fields out of the effort control path, and expose the
    native command/argument and watchdog evidence needed to reproduce the
    result. Unsupported or unknown effective effort is non-promotable.

## Operator acceptance

This proposal (Revision 5g) preserves the output of six cross-orchestrator
review relay sessions (all converged, zero disputes across 42 total findings),
adds the targeted recovery/evidence hardening update, and records the direct
red-team findings on pool-test scope, promotion identity, evidence cohorts,
recovery semantics, and cross-host effort comparability. No new cross-host
relay re-review has been performed for Revision 5g. Review convergence is
provenance; it is not evidence that either live selector is conformant.

The proposal is offered for operator acceptance as an implementation-planning
contract, not as authorization to activate live routing.

**Acceptance means:** proceed to native implementation planning in both
hosts against this contract, with the acceptance gates above as the
definition of done. Live activation requires fresh source evidence for every
gate, including executable cross-host fixtures and live-path receipts.

**Non-acceptance means:** identify which finding or correction needs
further iteration before implementation begins.

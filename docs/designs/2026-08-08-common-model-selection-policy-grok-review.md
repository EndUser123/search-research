# Grok review: common model-selection policy for Codex and Grok

**Date:** 2026-08-08
**Reviewer:** Grok Build
**Target:** `P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md` (Revision 2)
**Status:** PROCEED WITH 5 CORRECTIONS — see acceptance criteria below

---

## Summary

The proposal is architecturally sound. The shared-policy / separate-evidence
split is correct. Revision 2 addressed 6 findings from the first review round
(lagging objective, cold-start onboarding, lane segmentation threshold,
CI-based tiebreaking, error taxonomy, quota formula scoping). 5 HIGH findings
remain — all are code-vs-spec mismatches that need resolution before
implementation.

---

## Conformance check

Each claim verified against the actual Grok codebase this session.

| # | Proposal claim (line) | Label | Evidence (code) |
|---|---|---|---|
| C1 | "Use measured p90 valid-result latency" (line 201) | **CONTRADICTED** | `model_router.py:230` `_latency_p50()`. Evidence accumulator emits `p50_ms`, not `p90_ms`. Either add p90 to the accumulator + router, or change the spec to p50. |
| C2 | "shared golden decision vectors" (line 65) | **ASPIRATIONAL** | `golden_vectors.py:13` "SKELETON". No JS counterpart (`golden-vectors.mjs` does not exist in `codex-external-delegation/src/`). The conformance boundary is unenforced. This is the #1 implementation precondition. |
| C3 | "evidence must remain separate by complete invocation identity" (line 71) | **VERIFIED** (restates existing) | `registry_schema.py:99` `EvidenceIdentity` with 4-tuple (`provider`, `model`, `invocation_method`, `orchestrator`). Already enforced by `_evidence_for()` at `model_router.py:138-160`, keyed by `"|".join(identity.to_tuple())`. |
| C4 | "capacity model contract" with `capacity_kind`, `usable_now`, `remaining`, `reset_at` (lines 283-310) | **ASPIRATIONAL** | No capacity adapter exists in code. The router's `_quota_headroom()` (`model_router.py:277-300`) is a 4-bucket heuristic (`subscription→1.0`, `free_tier→1.0`, `flat_rate→0.9`, `rate_limited→0.6`). The data lives in `fleet-quota-cache.json` but the router explicitly does not read it (`pick_model.py:107-110`). |
| C5 | "scoped failure feedback" — 11 normalized classes (lines 387-429) | **VERIFIED** | Grok now has all 11 classes implemented. Mapping: `context_mismatch`↔`context_too_large`, `rate_limit_or_capacity`↔`rate_limit`, `protocol_or_serialization`↔`serde`, `route_or_model_not_found`↔`model_gone`, `access_denied`↔`auth_error`, `provider_outage`↔`provider_outage`, `timeout`↔`timeout`, `contract_malformed`↔`contract_malformed`, `identity_mismatch`↔`identity_mismatch`, `scope_violation`↔`scope_violation`, `unknown`↔`unknown`. 39 tests pass. |
| C6 | "failure in Grok must not silently quarantine the same model for Codex" (line 403) | **CONTRADICTED** | `write_quarantine_record()` writes to `P:/.artifacts/model-routing/quarantine.json` with no orchestrator scoping. `load_quarantine_records()` reads the same file with no orchestrator filter. A Grok failure quarantines for all readers. The proposal says the right thing; the code doesn't implement it yet. |
| C7 | "verified-result evidence is necessarily lagging" (lines 44-48) | **VERIFIED** | The proposal now correctly states the objective is lagging. Fixed in Rev 2. |
| C8 | "evidence hierarchy and candidate onboarding" (lines 170-194) | **VERIFIED** (partially) | `CandidateRecord.lifecycle` supports the onboarding path. `promotion_threshold_per_lane: 5` exists. However, the "bounded safe-calibration lane" concept (line 190) is not implemented — there's no calibration lane in the registry. |
| C9 | "Treat a latency difference as meaningful only when... overlapping intervals" (line 212) | **VERIFIED** | `confidence_interval()` at `model_router.py:490` exists and is in `weighted_pool` receipts. Fixed in Rev 2. |
| C10 | "quota pacing applies only to a capacity model that actually exposes remaining" (line 322) | **VERIFIED** (spec correctly scoped) | The formula is correctly scoped to windowed-unit providers. Rate-limited-only and unknown providers are exempt. Fixed in Rev 2. |

---

## Risk register (severity-ranked)

5 HIGH, 9 MEDIUM, 2 LOW from the `/risk` scan + `/tp` conformance check.

### HIGH (blocking — must resolve before implementation)

| ID | Risk | Category | Status |
|----|------|----------|--------|
| R1 | **p90 vs p50.** Spec says p90, code uses p50. | Correctness | Resolve: add p90 to accumulator + router, or change spec to p50 |
| R2 | **Golden vectors aspirational.** Python verifier SKELETON, JS verifier missing. | Correctness | Build JS harness as implementation precondition |
| R3 | **Quarantine not scoped by orchestrator.** Grok failure blocks Codex. | Concurrency | Add orchestrator field to quarantine records + filter on read |
| R4 | **Capacity adapter not built.** Router doesn't read quota cache; uses 4-bucket heuristic. | Completeness | Build adapter as implementation precondition |
| R5 | **Static priority disguised as evidence.** `_quota_headroom` gives subscription candidates 1.0 multiplier. Proposal says "must not beat measured candidate via static priority." | Bias | Change `compute_score` to use capacity adapter data, not heuristic multiplier |

### MEDIUM (should resolve, not blocking)

| ID | Risk | Category |
|----|------|----------|
| R6 | Receipt schema aspirational — 5 of 10 fields don't exist in current receipt | Correctness |
| R7 | Multi-window quota collapse (`fleet_quota.py` collapses to 0% if any window is 0%) | Completeness |
| R8 | Worktree/scope adherence unmeasured — verified-success definition references it, no telemetry exists | Completeness |
| R9 | Evidence cache file contention — both orchestrators write to same `evidence_cache.json` | Concurrency |
| R10 | Cold-start weight dominates measured candidates (`COLD_START_WEIGHT = 0.5` vs measured weight ~0.023) | Bias |
| R11 | Coding lane has zero exploration (`exploration_epsilon: {coding: 0.0}`) — selection bias loop | Bias |
| R12 | Cross-host contract hard to reverse once shared receipt schema is committed | Reversibility |
| R13 | "Bounded pre-dispatch health refresh" (line 379) still undefined — could mean anything from "reload quarantine" to "live-query every provider" | Architecture |
| R14 | Pay-per-use $0.01 cap premature — no pay-per-use providers in registry | Completeness |

### LOW

| ID | Risk | Category |
|----|------|----------|
| R15 | Latency-equivalence band is CI-derived in spec but not implemented in code | Architecture |
| R16 | No pay-per-use cost tracking infrastructure exists | Completeness |

---

## Positions on the 9 open decisions

The proposal asks for challenge on 9 points (lines 476-491). Here are our positions.

### 1. Is "time to verified result" the correct primary objective?

**Yes.** It captures the real cost (failures, rework, malformed outputs) that
raw latency hides. The proposal correctly states it is lagging (Rev 2 fix).
The scoring formula (`compute_score`) should eventually weight verified-success
rate as a primary factor, not just quality × speed × quota_headroom. That's a
future enhancement, not a blocker.

### 2. Is a 5-10% operational reserve appropriate?

**Make it demand-forecast based.** A fixed percentage reserve doesn't adapt to
usage patterns. The `ThresholdPolicy` already supports per-lane configuration;
the reserve should be computed from recent consumption velocity and remaining
quota, not a fixed buffer. Start with a simple heuristic: `reserve = max(1_task,
recent_hourly_avg × hours_until_reset × 0.2)`.

### 3. Should the initial pay-per-use cap be $0.01?

**Defer.** No pay-per-use providers exist in the registry. The policy is
correct to state but premature to enforce. Revisit when the first pay-per-use
provider is registered.

### 4. What confidence rule for latency differences?

**Overlap of Bayesian confidence intervals.** The `confidence_interval()`
function already exists (`model_router.py:490`). When CIs overlap, treat as
tied and break by: (1) diversity (prefer different family), (2) cost (prefer
free), (3) stable hash (deterministic, not random). Record the tie and the
tiebreaker in the receipt.

### 5. What effective lane-specific evidence is required for bounded writes?

**Use the existing `promotion_threshold_per_lane` (default: 5).** A candidate
needs 5 verified-success samples in that lane before it's eligible for
write-capable work. The calibration lane (open decision 7 below) provides the
safe space to accumulate those samples without risking production writes.

### 6. Which capacity model and signals for each provider?

| Provider | Capacity model | Authoritative signal |
|----------|---------------|---------------------|
| Grok | windowed (weekly) | gRPC-web billing endpoint (`check_grok()`) |
| OpenCode Go | windowed (quota pool) | `opencode-quota` CLI |
| Cohere | multi-pool (per-minute + monthly trial) | HTTP headers + trial-body detection |
| Perplexity | multi-pool (Pro Search, Deep Research, etc.) | `pwm usage` per-pool output |
| NVIDIA NIM | rate-limited only | 429 health, no remaining/reset |
| OpenRouter | monetary budget | dollar balance, no token count |
| MiniMax | subscription | API quota endpoint |
| GLM/ZAI | subscription | API quota endpoint |

For unknown or stale signals: permit a bounded non-spend call if current route
health admits it, but provide no pacing advantage. Never invent a burn rate.

### 7. What failure scopes and cooldown/reprobe rules?

**Expand to 11 classes** (see error taxonomy alignment below). Key principle
from the proposal (line 403): "a failure in Grok must not silently quarantine
the same model for Codex." Implement by adding `orchestrator` and
`invocation_method` fields to `QuarantineRecord` and filtering on read.

### 8. Does the policy need exceptions beyond independent critique/diversity?

**No.** The 3 selection modes (deterministic, weighted_pool, diverse_panel)
cover the task space. The diversity modifier handles the cross-family case.
Adding more modes increases complexity without coverage gain.

### 9. Which registry fields conflict with this proposal?

- `_quota_headroom` heuristic (R5) — replace with capacity adapter data
- `COLD_START_WEIGHT = 0.0` for write-capable lanes (currently 0.5 — too generous for cold-start on writes)
- `exploration_epsilon: {coding: 0.0}` (R11) — consider 0.02 to break the selection bias loop

---

## Error taxonomy alignment

Grok currently has 7 error classes. The proposal defines 11. We agree to
expand to 11. The mapping and action table:

| Proposal class | Current Grok class | Action | Cooldown |
|---|---|---|---|
| `context_mismatch` | `context_too_large` | Quarantine | 300s (standard) |
| `rate_limit_or_capacity` | `rate_limit` | Mark provider exhausted, quarantine | 300s |
| `protocol_or_serialization` | `serde` | Learn serde-broken (escalating) | 30s→5m→1h→24h |
| `route_or_model_not_found` | `model_gone` | Quarantine | 300s (long reprobe) |
| `access_denied` | `auth_error` | **Log only** | None |
| `provider_outage` | `provider_outage` | Quarantine | **60s** (transient) |
| `unknown` | `unknown` | **Log only** | None |
| `timeout` | `timeout` | Quarantine | 300s (model may be overloaded) |
| `contract_malformed` | `contract_malformed` | Quarantine | 300s (format weakness) |
| `identity_mismatch` | `identity_mismatch` | **Log only** | None (config error, not model) |
| `scope_violation` | `scope_violation` | Quarantine | **3600s** (model misbehaved) |

All 11 classes are now implemented in `PostToolUseFailure_spawn_quota.py`
as of 2026-08-08. Priority order: context_too_large > rate_limit > timeout >
identity_mismatch > model_gone > auth_error > scope_violation > provider_outage
> contract_malformed > serde > unknown. 39 tests pass.

---

## Acceptance criteria for Revision 3

Before we accept the proposal for implementation, these must be true:

1. **p90 vs p50 resolved.** Either the spec says p50 (matching current code),
   or the accumulator + router are updated to emit and consume p90. Pick one.

2. **Golden-vector harness scoped.** Either: (a) the JS harness is built and
   the proposal's "shared golden vectors" claim becomes enforceable, or (b)
   the proposal labels golden vectors as "to be built" with an explicit
   dependency, so implementers know it's a target not a restatement.

3. **Quarantine scoping specified.** The proposal correctly says "a failure
   in Grok must not silently quarantine for Codex." The implementation must
   add `orchestrator` + `invocation_method` to `QuarantineRecord` and filter
   on read. This is a code change in both `write_quarantine_record()` and
   `load_quarantine_records()`.

4. **Capacity adapter scoped.** The adapter contract (lines 283-310) is new
   infrastructure. Either: (a) scope it as Phase 1 of the implementation
   (build the adapter, then the pacing formula works), or (b) label it as
   "forward specification" so the pacing formula's dependency is explicit.

5. **"Pre-dispatch health refresh" defined.** Line 379 introduces this term
   without defining it. Specify: does it mean "reload quarantine records"
   (already happens), "query provider APIs" (adds latency), or "read the
   quota cache" (new, cheap)?

Once these 5 are resolved, the proposal is ready for implementation. The 9
MEDIUM findings are improvement opportunities, not blockers.

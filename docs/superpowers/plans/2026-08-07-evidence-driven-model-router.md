# Evidence-driven model router: implementation plan (revised)

**Created:** 2026-08-07
**Revised:** 2026-08-07 (Codex plan review — 9 corrections applied)
**Status:** EXECUTED — all 11 tasks complete (2026-08-07)
**Execution:** parent-led delegation with M3 subagents, 4 parallel waves
**Test results:** 390 passed, 3 skipped
**Reversibility:** ≥1.5 (fleet-wide schema migration, 21+ skill callers)
**Plan type:** HARD

## Execution model

**Parent-led manual delegation with worktree isolation.** Not monolithic `/go`.

- **Parent-owned:** canonical schema, policy precedence, threshold decisions, selector algorithm, Codex-path benchmarking, integration, migration, final verification.
- **Pi-delegated (worktree-isolated):** schema validators, fixtures, telemetry extraction, caller inventory, mechanical test additions, isolated caller migrations.
- Every write task requires worktree isolation: `git worktree add -b router-task-N P:/worktrees/router-task-N`.

## Architecture (converged across Grok + Codex + ChatGPT)

```
task policy
→ hard capability/configuration/health gates
→ approval and quota-policy gates
→ lane-specific evidence eligibility
→ deterministic / weighted_pool / diverse_panel
→ safe transport resolution
→ selection receipt
```

**Key decisions (from design dialogue):**
- No tiers. Flat pool per lane.
- Three selection modes: `deterministic` (mechanical/coding/routine), `weighted_pool` (reasoning), `diverse_panel` (critique)
- Weights computed at call time from evidence (quality_scores + sample-size-adjusted + Bayesian freshness shrinkage)
- Lifecycle states: `active` / `candidate` / `quarantined` / `retired`
- Hierarchical circuit breakers: transport-level first, then provider-level on correlated failures
- Policy states (`use_freely`, `explicit_approval`, `excluded`) are hard gates BEFORE weighting, not quality tiers
- `pick_diverse()` stays as separate constraint-based selector
- Bounded exploration per-lane (epsilon-greedy, operator-configurable, gated by task policy)
- Shared registry schema + native selectors (Python for Grok, JS for Codex) + golden test vectors in CI
- Versioned routing snapshots + append-only evidence for rollback without data loss

**Evidence identity (4 fields — revised):** every evidence record is identified by `provider + model + invocation_method + orchestrator`. The same model via different transports under different orchestrators produces separate evidence. A model that works under Grok's spawn contract but fails under Codex's runner → Pi chain has distinct evidence for each.

**Threshold policy (revised):** all thresholds are policy inputs defined in the registry, not hardcoded defaults:
- `promotion_threshold_per_lane`: number of verified successes required (operator sets per lane)
- `quarantine_failure_count`: consecutive failures before quarantine (operator sets)
- `provider_outage_threshold`: correlated failures before provider-level quarantine (operator sets)
- `provider_cooldown_seconds`: auto-unquarantine cooldown (operator sets)
- `exploration_epsilon_per_lane`: bounded exploration rate (operator sets per lane, 0 for writes)

## Files (anchored to exact repository paths)

### Grok tree: `C:/Users/brsth/.grok/skills/model-quota/scripts/`

| File | Action | Owner | Responsibility |
|------|--------|-------|----------------|
| `model_router.py` | **CREATE** | Parent | Core: candidate filtering, weight computation, three selection modes, receipt generation |
| `evidence_accumulator.py` | **CREATE** | Parent | Reads usage.jsonl, computes evidence with sample-size + Bayesian shrinkage. Caches derived weights. |
| `circuit_breaker.py` | **CREATE** | Parent | Hierarchical health: transport → model → provider quarantine with cooldown + auto-reprobe |
| `registry_schema.py` | **CREATE** | Parent | Schema definition + validation for flat-pool registry format |
| `golden_vectors.py` | **CREATE** | Parent | Test fixtures + verifier for Grok/Codex conformance |
| `pick_model.py` | **MIGRATE** | Parent | Remove tier1/tier2 iteration. Delegate to model_router.py. Final API has no tier fields. |
| `fleet-models.json` | **EVOLVE IN PLACE** | Parent | Add schema_version field, flatten tiers into pools, add lifecycle/policy/evidence fields |

### Codex tree: `P:/packages/codex-external-delegation/src/`

| File | Action | Owner | Responsibility |
|------|--------|-------|----------------|
| `model-selector.mjs` | **MIGRATE** | Parent | Remove JS-side tier logic. Read evolved fleet-models.json. Implement same gate chain + modes. |
| `golden-vectors.mjs` | **CREATE** | Parent | JS golden vector verifier (`--verify-golden <path>`) |

### Shared paths

| File | Action | Owner | Responsibility |
|------|--------|-------|----------------|
| `fleet-models.json` (Grok: `~/.grok/skills/model-quota/scripts/`) | **EVOLVE** | Parent | One canonical registry. No second file. Schema_version field controls format detection. |
| `golden_vectors.json` | **CREATE** | Parent | Shared golden test cases. Both selectors verify against this. |
| `P:/packages/codex-external-deployment/tests/golden_vectors.json` | **SYMLINK** or **COPY** | Parent | Codex CI reads the same golden vectors |

### Tests (Grok tree)

| File | Action | Owner |
|------|--------|-------|
| `~/.grok/skills/model-quota/tests/test_model_router.py` | **CREATE** | Parent |
| `~/.grok/skills/model-quota/tests/test_evidence_accumulator.py` | **CREATE** | Parent |
| `~/.grok/skills/model-quota/tests/test_circuit_breaker.py` | **CREATE** | Parent |
| `~/.grok/skills/model-quota/tests/test_golden_vectors.py` | **CREATE** | Parent |
| `~/.grok/skills/model-quota/tests/test_registry_schema.py` | **CREATE** | Parent |
| `~/.grok/skills/model-quota/tests/fixtures/registry_sample.json` | **CREATE** | Parent |

## Decomposition checkpoint

1. **Is registry_schema.py necessary?** Yes — shared contract between Grok (Python) and Codex (JS). Without it, both sides invent their own format.
2. **Could evidence_accumulator merge with model_router?** No — evidence computation is batch (periodic), selection is real-time (per-call). Different lifecycles.
3. **Could circuit_breaker merge with model_router?** No — circuit breaking is passive health monitoring; selection is active routing. Separation prevents the selector from being responsible for its own health checks.
4. **Is golden_vectors.py necessary?** Yes — without it, the two native selectors drift silently. CI enforcement is the contract.
5. **Should fleet-registry.json exist as a separate file?** **NO (corrected).** Evolve `fleet-models.json` in place with a `schema_version` field. One canonical registry. No parallel file.

No workstream drops. Proceeding to tasks.

## Tasks

### Task 1: Define the registry/evidence schema

**Owner:** Parent · **Isolation:** worktree `router-task-1`

**Goal:** create `registry_schema.py` defining the canonical candidate record format.

**Success observation:** `registry_schema.py` imports cleanly and `validate_candidate()` passes on a test fixture.

**Failure observation:** import error or validation fails on valid input.

**Failure signal:** selector code tries to read a field that doesn't exist in the schema.

**Countermove:** add the field to schema + validator.

**Steps:**
- [ ] Define `CandidateRecord` dataclass with: id, model, provider, transport, orchestrator, lanes[], capabilities{}, quota{}, lifecycle, policy, evidence_refs{}
- [ ] Define `EvidenceIdentity`: `provider + model + invocation_method + orchestrator` (4-tuple — every evidence record is keyed by all four)
- [ ] Define `EvidenceBlock` with: quality_scores{}, sample_counts{}, latency{p50,p90}, success_rate{overall,per_transport,per_orchestrator}, last_updated, cohort_tag
- [ ] Define `PolicyState` enum: `USE_FREELY`, `REASONING_POOL`, `EXPLICIT_APPROVAL`, `EXCLUDED`
- [ ] Define `LifecycleState` enum: `ACTIVE`, `CANDIDATE`, `QUARANTINED`, `RETIRED`
- [ ] Define `ThresholdPolicy`: `promotion_threshold_per_lane`, `quarantine_failure_count`, `provider_outage_threshold`, `provider_cooldown_seconds`, `exploration_epsilon_per_lane` — all as configurable fields, NOT hardcoded
- [ ] Write `validate_candidate(record)` that checks required fields, enum values, type consistency, 4-tuple evidence identity
- [ ] Write `validate_registry(path)` that loads JSON and validates every entry including threshold policy
- [ ] Test: create fixture `tests/fixtures/registry_sample.json` with 5 candidates covering all lifecycle + policy states + threshold policy section
- [ ] Test: `test_registry_schema.py` — validate_candidate passes on fixture, fails on malformed input
- [ ] Commit in worktree, merge to main

### Task 2: Define the evidence accumulator

**Owner:** Parent · **Isolation:** worktree `router-task-2` (depends on Task 1)

**Goal:** create `evidence_accumulator.py` that reads telemetry and produces cached evidence blocks.

**Success observation:** `evidence_accumulator.py --compute --lane reasoning` produces evidence blocks for all reasoning-lane candidates with quality scores and sample counts, keyed by the 4-tuple identity.

**Failure observation:** empty evidence blocks or crash on malformed telemetry.

**Failure signal:** `pick()` returns weight=1.0 for all models (no evidence differentiation).

**Countermove:** check telemetry format compatibility, add fallback for missing fields.

**Steps:**
- [ ] Read `P:/.artifacts/model-telemetry/usage.jsonl` (append-only JSONL)
- [ ] Group by the 4-tuple: `model + provider + invocation_method + orchestrator`
- [ ] Compute per-group: success_rate, avg_quality (from quality_score field), sample_count, p50/p90 latency
- [ ] Apply sample-size adjustment: effective_n = min(n, cap) where small samples shrink weight
- [ ] Apply Bayesian freshness shrinkage: old evidence → wider posterior → lower confidence → lower weight contribution. Posterior mean stays; confidence interval widens. NOT decay toward zero or toward own average.
- [ ] Tag calibration probes: records with `task_domain: "calibration"` are cohort-tagged separately. They DO contribute to promotion stats (clearly marked as calibration cohort). They are NOT discarded.
- [ ] **Sequester benchmark evidence:** records from calibration runs are tagged `cohort: "benchmark"`. No routing changes written during calibration — benchmark evidence is read-only for the router until explicitly promoted.
- [ ] Cache results to `P:/.artifacts/model-evidence/evidence_cache.json` with timestamp
- [ ] CLI: `evidence_accumulator.py --compute [--lane <name>] [--json]`
- [ ] Test: `test_evidence_accumulator.py` — feed fixture telemetry, verify sample-size adjustment, Bayesian shrinkage, 4-tuple grouping, calibration cohort tagging
- [ ] Commit in worktree, merge to main

### Task 3: Define verified success + lifecycle automation

**Owner:** Parent · **Isolation:** worktree `router-task-3` (depends on Tasks 1-2)

**Goal:** create `circuit_breaker.py` with lifecycle transitions and hierarchical health monitoring.

**Success observation:** a candidate with threshold-satisfied verified successes in the coding lane promotes to `active`; a model with threshold consecutive failures quarantines; correlated provider failures trigger provider-level quarantine, not individual model quarantine.

**Failure observation:** promotion on unverified calls, or quarantine on transient provider outage.

**Failure signal:** new models stuck in `candidate` forever, or entire providers quarantined on a single outage.

**Countermove:** adjust thresholds (which are policy inputs); verify provider-scoped outage detection.

**Steps:**
- [ ] Define `VerifiedSuccess` check: (1) used intended provider+transport+orchestrator, (2) response satisfied contract, (3) verification passed where exists, (4) no timeout/malformation
- [ ] Read `promotion_threshold_per_lane` from the registry's ThresholdPolicy (NOT hardcoded)
- [ ] Implement `check_promotion(candidate, lane)` → promotes candidate→active when verified success count ≥ threshold for that lane
- [ ] Read `quarantine_failure_count` from ThresholdPolicy → quarantines on N consecutive failures
- [ ] Implement **hierarchical circuit breaker**:
  - Transport-level: if a specific transport (spawn, PI, HTTP) fails, quarantine that transport for the model (try alternate transport)
  - Model-level: if all transports fail, quarantine the model
  - Provider-level: read `provider_outage_threshold` from ThresholdPolicy — if ≥N models from same provider fail in same time window, quarantine the PROVIDER. Auto-unquarantine after `provider_cooldown_seconds`.
- [ ] Implement `check_retirement(candidate)` → retires when all probes return 404/model-not-found
- [ ] Implement auto-reprobe: quarantined models get periodic reprobe after `provider_cooldown_seconds`; success → unquarantine
- [ ] Test: `test_circuit_breaker.py` — promotion on verified success, quarantine on failure, hierarchical cascade prevention (transport → model → provider), auto-reprobe, threshold values read from policy not hardcoded
- [ ] Commit in worktree, merge to main

### Task 4: Implement the three selectors

**Owner:** Parent · **Isolation:** worktree `router-task-4` (depends on Tasks 1-3)

**Goal:** create `model_router.py` with `deterministic()`, `weighted_pool()`, and `diverse_panel()` selectors.

**Success observation:** all three selectors return valid candidates + selection receipts on a test registry.

**Failure observation:** selector returns None, crashes, or produces a receipt missing required fields.

**Failure signal:** calling skills report "no model available" when models ARE available.

**Countermove:** debug the gate chain (which gate filtered the candidate?).

**Steps:**
- [ ] Implement gate chain: `capability_gates → policy_gates → evidence_eligibility → health_gates`
- [ ] Each gate returns (passed: bool, reason: str) for the receipt
- [ ] **`deterministic(lane, requirements)`**: filter via gates → rank by evidence quality + speed + quota headroom → return top candidate + receipt
- [ ] **`weighted_pool(lane, requirements)`**: filter via gates → compute weights from cached evidence → weighted random → return selected + receipt
- [ ] **`diverse_panel(lane, requirements, count)`**: filter via gates → constraint satisfaction (maximize provider family diversity) → if fewer families than requested, return reduced-diversity receipt with explicit disclosure
- [ ] Implement **bounded exploration**: read `exploration_epsilon_per_lane` from ThresholdPolicy. `deterministic` mode: epsilon% of calls select a random eligible candidate instead of the top-ranked. `weighted_pool`: no additional exploration needed. `diverse_panel`: no exploration. Exploration disabled when epsilon=0 (default for write-capable lanes).
- [ ] Selection receipt includes: selected model, selection_mode, eligible candidates, weights/ranking, gates passed/failed, diversity adjustment, random seed, algorithm version, quota snapshot, selected transport, timestamp
- [ ] Test: `test_model_router.py` — each mode returns valid candidate + receipt; gates filter correctly; exploration fires at configured epsilon; diverse_panel degrades gracefully; epsilon=0 disables exploration
- [ ] Commit in worktree, merge to main

### Task 5: Codex → Pi benchmark promotion gate

**Owner:** Parent · **Isolation:** worktree `router-task-5` (depends on Tasks 1-4)

**Goal:** define and implement the actual dispatch-path benchmark as a promotion requirement. A model must pass the full Codex → runner → Pi path (not just raw Pi) before promotion to `active` for Codex-orchestrated work.

**Success observation:** a candidate that passes raw Pi but fails the full Codex → runner → Pi path is NOT promoted to `active` for Codex-orchestrated lanes.

**Failure observation:** model promoted based on raw Pi success but fails in production via the full Codex dispatch chain.

**Failure signal:** Codex-orchestrated tasks fail with transport errors on a model that "passed" promotion.

**Steps:**
- [ ] Define two benchmark paths: (1) raw Pi (`pi --model <m>` direct), (2) full Codex → runner → Pi chain
- [ ] Define benchmark suite: N prompts covering the lane's task types (reasoning, code, mechanical)
- [ ] Benchmark evidence is sequestered (cohort: "benchmark") — no routing changes during calibration
- [ ] Promotion to `active` for an orchestrator+lane requires: verified successes on BOTH benchmark paths for that orchestrator
- [ ] A model can be `active` for Grok-orchestrated work but `candidate` for Codex-orchestrated work (different evidence per 4-tuple)
- [ ] Write benchmark runner: `benchmark_runner.py --model <m> --path raw_pi|codex_runner_pi --lane <l> --count N`
- [ ] Benchmark results feed evidence_accumulator with cohort tag "benchmark"
- [ ] Test: `test_benchmark_gate.py` — model with raw-Pi-only success does NOT promote for Codex lanes
- [ ] Commit in worktree, merge to main

### Task 6: Create golden test vectors

**Owner:** Parent · **Isolation:** worktree `router-task-6` (depends on Task 4)

**Goal:** create golden vectors proving Grok and Codex selectors return equivalent decisions on identical inputs.

**Success observation:** golden vectors pass for both Python and JS selectors.

**Failure observation:** selectors disagree on a test case.

**Failure signal:** CI fails on golden vector divergence after a selector change.

**Steps:**
- [ ] Define 20+ test cases: each selection mode, each gate type, edge cases (0 eligible, 1 eligible, all quarantined, reduced diversity, cold-start candidate, epsilon=0, provider-level quarantine)
- [ ] Each test case: input (registry fixture + evidence fixture + lane + requirements) → expected output (selected model OR deterministic rank order)
- [ ] Golden vectors stored as JSON: `golden_vectors.json` in a shared path both repos can read
- [ ] Python: `golden_vectors.py --verify` runs all vectors against model_router.py
- [ ] JS: Codex's `golden-vectors.mjs --verify-golden <path>` runs all vectors against model-selector.mjs
- [ ] **CI: golden vectors run continuously on every change to either selector** (Grok pre-commit hook + Codex CI). Not just at initial write.
- [ ] Test: `test_golden_vectors.py` — all 20+ vectors pass
- [ ] Commit in worktree, merge to main

### Task 7: Evolve fleet-models.json in place

**Owner:** Parent · **Isolation:** worktree `router-task-7` (depends on Task 1)

**Goal:** evolve `fleet-models.json` from tiered format to flat-pool format. No second registry file.

**Success observation:** `validate_registry()` passes on the evolved file. All models represented. `schema_version: 5` field present.

**Failure observation:** missing models, invalid schema, or policy/lifecycle states not set.

**Steps:**
- [ ] Add `schema_version: 5` to fleet-models.json (current is 4.0)
- [ ] Flatten tier1/tier2 arrays into single `candidates` array per lane
- [ ] For each candidate, populate: id, model, provider, transport, orchestrator, lanes, capabilities, quota, lifecycle (`active` for existing, `candidate` for new this session), policy (from Go usage policy), evidence_refs
- [ ] Add `threshold_policy` section with operator-configurable defaults (to be confirmed by operator)
- [ ] Remove tier1/tier2 arrays entirely — no tier fields remain
- [ ] Keep quality_scores block as-is (evidence_accumulator will read it)
- [ ] Validate: `registry_schema.validate_registry()` passes
- [ ] Commit in worktree, merge to main
- [ ] Write versioned snapshot of the pre-evolution file for rollback

### Task 8: Migrate pick_model.py

**Owner:** Parent · **Isolation:** worktree `router-task-8` (depends on Tasks 4, 7)

**Goal:** `pick_model.py` delegates to `model_router.py`. The function signature evolves — no tier fields in output.

**Success observation:** `pick_model.py coding` returns a model selected via the new deterministic mode, with a receipt.

**Failure observation:** crash, or old first-available behavior still present.

**Failure signal:** same model always selected (deterministic without evidence differentiation = first-available in disguise).

**Steps:**
- [ ] Refactor `pick(lane)` to call `model_router.deterministic(lane, requirements)` by default
- [ ] Add `pick(lane, selection_mode="weighted_pool")` for reasoning pool
- [ ] Add `pick(lane, selection_mode="diverse_panel", count=N)` delegating to `diverse_panel()`
- [ ] Return `result["receipt"]`, `result["selection_mode"]`
- [ ] **Do NOT return `result["tier"]`** — no tier field. The final API contains no tier fields or tier ordering.
- [ ] Keep `result["provider"]`, `result["free"]`, `result["dispatch_path"]` for transport info
- [ ] **Shadow comparison (mandatory before live cutover):** run the new router alongside the old first-available logic for a comparison period. Log both selections to `P:/.artifacts/model-routing/shadow_comparison.jsonl`. Verify the new router produces sane selections before switching callers.
- [ ] Test: existing `test_discover.py` tests pass
- [ ] Test: `test_model_router.py` passes when called via pick_model.py
- [ ] Commit in worktree, merge to main

### Task 9: Migrate callers (21+ skills)

**Owner:** Pi-delegated per skill (worktree-isolated) · **Parent reviews each merge**

**Goal:** all skill files that read `pick_model.py` output are updated to not read tier fields.

**Success observation:** `rg 'result\["tier"\]|\.tier' skills/` returns zero results.

**Failure observation:** KeyError in a skill that still reads tier.

**Failure signal:** skill crash with "KeyError: 'tier'" or "AttributeError: 'tier'" in logs.

**Countermove:** the caller should use `.get("selection_mode")` if it needs mode info. No tier shims.

**Steps:**
- [ ] Find all callers: `rg 'pick_model\.py|result\["tier"\]|result\[.tier.\]|\.tier' skills/`
- [ ] For each caller (worktree-isolated per skill):
  - Remove `result["tier"]` reads
  - If the skill uses tier for display/routing, use `result["selection_mode"]` or `result["receipt"]`
  - If the skill passes `--exclude-self`, verify the exclude logic still works
  - Test the skill's own test suite
  - Commit in worktree, parent reviews, merge
- [ ] **Live-path acceptance gate:** after all callers migrated, run a fleet exercise: each lane (coding, reasoning, mechanical, critic) dispatched via `pick_model.py` and verified to produce valid selections with receipts. No KeyError, no crash, no empty result.

### Task 10: Remove tier/first-available semantics completely

**Owner:** Parent · **Isolation:** worktree `router-task-10` (depends on Task 9)

**Goal:** no code anywhere references tier1, tier2, or first-available ordering.

**Success observation:** `rg 'tier1|tier2|first.available' ~/.grok/skills/` returns zero results.

**Failure observation:** stale references cause crashes.

**Steps:**
- [ ] Remove tier1/tier2 arrays from fleet-models.json (already done in Task 7 — verify no stale refs)
- [ ] Remove tier iteration logic from pick_model.py (already done in Task 8 — verify)
- [ ] Remove `is_available()` tier-checking code paths
- [ ] Grep for any remaining tier references: `rg 'tier1|tier2|first.available' ~/.grok/skills/`
- [ ] Grep Codex side: `rg 'tier1|tier2|first.available' P:/packages/codex-external-delegation/`
- [ ] Test: full test suite passes on both Grok and Codex sides
- [ ] Commit in worktree, merge to main

### Task 11: Versioned routing snapshots + rollback

**Owner:** Parent · **Isolation:** worktree `router-task-11` (depends on Task 7)

**Goal:** the registry supports versioned snapshots so routing config can roll back without losing evidence history.

**Success observation:** `model_router.py --snapshot` writes a timestamped snapshot; `--rollback <snapshot>` restores it. Evidence history in usage.jsonl is unaffected by rollback.

**Failure observation:** rollback fails or loses accumulated evidence.

**Steps:**
- [ ] On registry write (lifecycle change, policy change): write versioned snapshot to `P:/.artifacts/model-routing/snapshots/YYYYMMDD-HHMMSS.json`
- [ ] Evidence history stays in `usage.jsonl` (append-only) — snapshots are routing config only
- [ ] `--rollback <snapshot>` restores routing config from that timestamp; evidence is not affected
- [ ] `--diff <snapshot1> <snapshot2>` shows what changed between two snapshots
- [ ] Test: snapshot + rollback preserves evidence while restoring routing config
- [ ] Commit in worktree, merge to main

## Rejected alternatives

| Alternative | Rejected because |
|---|---|
| Static hand-tuned weights | Drift from reality; reinvents what quality_scores already provides |
| Universal weighted random (original proposal) | Makes routine work nondeterministic for no benefit |
| Shared Python library for Codex | Codex is Node-based; can't import Python without subprocess |
| External CLI router | 200ms overhead per selection; unnecessary for in-process call |
| Tier adapter (fake tier:1 in output) | Preserves the exact semantics we're removing |
| Decay evidence toward prior or own average | Artificially reduces confidence in proven models |
| Big-bang cutover | 21+ callers break simultaneously if new router has a bug |
| Second registry file (fleet-registry.json) | Unjustified; fleet-models.json is already shared. Evolve in place. |
| Hardcoded thresholds | Must be policy inputs; operator-configurable per lane |
| Raw-Pi-only promotion gate | Must benchmark full Codex → runner → Pi path; raw Pi ≠ production dispatch |
| Monolithic /go execution | Multi-week, multi-repo, shared worktree — needs parent-led delegation with isolation |

## Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Evidence self-reinforcement lockout | HIGH | Bounded exploration epsilon per lane (disabled for writes) |
| Quarantine cascade on provider outage | HIGH | Hierarchical circuit breakers (provider-scoped quarantine + cooldown) |
| Policy vs evidence precedence undefined | HIGH | Hard gate ordering: policy filters BEFORE weighting |
| Schema migration breaks callers | MEDIUM | Staged migration (Task 9), no fake tier fields, shadow comparison |
| Golden vector drift between Python/JS | MEDIUM | CI gate on every selector change (continuous, not one-time) |
| Freshness punishes proven models | MEDIUM | Bayesian posterior shrinkage (confidence widens, mean preserved) |
| Weight computation latency | LOW | Cached derived weights; evidence accumulator runs periodically |
| No rollback path | MEDIUM | Versioned routing snapshots (Task 11) |
| Calibration evidence contamination | MEDIUM | Benchmark evidence sequestered (cohort tag); no routing changes during calibration |
| Cross-orchestrator evidence contamination | MEDIUM | 4-tuple identity (provider+model+method+orchestrator) keeps evidence separate |
| Shared worktree write contention | MEDIUM | Worktree isolation for every write task |

## Verification

- [ ] `pytest tests/test_model_router.py tests/test_evidence_accumulator.py tests/test_circuit_breaker.py tests/test_golden_vectors.py tests/test_registry_schema.py tests/test_benchmark_gate.py` — all pass
- [ ] `python golden_vectors.py --verify` — all 20+ vectors pass
- [ ] Codex side: `node golden-vectors.mjs --verify-golden <path>` — same vectors pass
- [ ] `rg 'tier1|tier2|first.available' ~/.grok/skills/` — zero results
- [ ] `rg 'tier1|tier2|first.available' P:/packages/codex-external-delegation/` — zero results
- [ ] `rg 'result\["tier"\]|\.tier' ~/.grok/skills/` — zero results
- [ ] `registry_schema.validate_registry()` on evolved fleet-models.json — passes
- [ ] Shadow comparison: new router selections are sane (not random, not always-first)
- [ ] Snapshot + rollback: routing config restores, evidence history preserved
- [ ] Live-path acceptance: each lane dispatched and verified with receipt
- [ ] Codex → Pi benchmark: at least one model benchmarked through full Codex → runner → Pi path
- [ ] Manual: quarantine a model, verify exclusion + auto-reprobe restoration
- [ ] Manual: `pick_model.py --lane reasoning --mode weighted_pool` returns weighted-random selections across multiple calls

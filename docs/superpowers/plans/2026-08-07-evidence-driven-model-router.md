# Evidence-driven model router: implementation plan

**Created:** 2026-08-07
**Status:** draft (pending adversarial review)
**Reversibility:** ≥1.5 (fleet-wide schema migration, 21+ skill callers)
**Plan type:** HARD

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

**Risk gate (passed):** `/risk` found 12 risks (3 HIGH, 5 MEDIUM, 2 new from critique). All addressed:
- Self-reinforcement → bounded exploration (epsilon per lane)
- Quarantine cascade → hierarchical circuit breakers (provider-scoped)
- Policy vs evidence → hard gate ordering (policy filters before weighting)
- Freshness decay → Bayesian posterior shrinkage (not decay toward prior or own average)
- Tier adapter → rejected (no fake tier fields; staged caller migration instead)

## Files

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/model_router.py` | **CREATE** | Core: candidate filtering, weight computation, three selection modes, receipt generation |
| `scripts/evidence_accumulator.py` | **CREATE** | Reads usage.jsonl, computes per-model per-lane evidence with sample-size adjustment + Bayesian shrinkage. Caches derived weights. |
| `scripts/circuit_breaker.py` | **CREATE** | Hierarchical health monitoring: transport-level → model-level → provider-level quarantine with cooldown + auto-reprobe |
| `scripts/registry_schema.py` | **CREATE** | Schema definition + validation for the new flat-pool fleet registry format |
| `scripts/golden_vectors.py` | **CREATE** | Test fixtures proving Grok and Codex selectors return equivalent decisions |
| `fleet-registry.json` | **CREATE** (successor to fleet-models.json) | Canonical flat-pool registry with lifecycle states, policy states, evidence refs |
| `scripts/pick_model.py` | **MIGRATE** | Remove tier1/tier2 iteration. Delegate to model_router.py. Keep function signature for callers. |
| `scripts/pick_model.py` callers (21+) | **MIGRATE** | Remove `result["tier"]` reads. Read `result["selection_mode"]` and `result["receipt"]` instead. |
| `tests/test_model_router.py` | **CREATE** | Unit tests for all three selection modes + circuit breaker + evidence computation |
| `tests/test_golden_vectors.py` | **CREATE** | Golden vector conformance tests |
| `fleet-models.json` | **DEPRECATE** | Keep as backup during migration, remove after all callers verified |

## Decomposition checkpoint

1. **Is registry_schema.py necessary?** Yes — shared contract between Grok (Python) and Codex (JS). Without it, both sides invent their own format.
2. **Could evidence_accumulator merge with model_router?** No — evidence computation is batch (periodic), selection is real-time (per-call). Different lifecycles, different performance profiles.
3. **Could circuit_breaker merge with model_router?** No — circuit breaking is health monitoring (passive), not selection logic (active). Separation prevents the selector from being responsible for its own health checks.
4. **Is golden_vectors.py necessary?** Yes — without it, the two native selectors drift silently. CI enforcement is the contract.
5. **Simpler decomposition?** Could merge registry_schema into model_router (it's just a dataclass). But separating it makes the schema the shared contract, which is the architectural point. Keep separate.

No workstream drops. Proceeding to tasks.

## Tasks (sequential — each builds on the prior)

### Task 1: Define the registry/evidence schema

**Goal:** create `registry_schema.py` defining the canonical candidate record format.

**Success observation:** `registry_schema.py` imports cleanly and `validate_candidate()` passes on a test fixture.

**Failure observation:** import error or validation fails on valid input.

**Most likely failure mode:** schema doesn't cover all fields needed by selectors (missing policy state, missing transport info).

**Failure signal:** selector code tries to read a field that doesn't exist in the schema.

**Countermove:** add the field to schema + validator.

**Branch trigger:** none (foundation task).

**Abort condition:** none.

**Steps:**
- [ ] Define `CandidateRecord` dataclass with: id, model, provider, transport, lanes[], capabilities{}, quota{}, lifecycle, policy, evidence_refs{}
- [ ] Define `EvidenceBlock` with: quality_scores{}, sample_counts{}, latency{p50,p90}, success_rate{overall,per_transport}, last_updated, cohort_tag
- [ ] Define `PolicyState` enum: `USE_FREELY`, `REASONING_POOL`, `EXPLICIT_APPROVAL`, `EXCLUDED`
- [ ] Define `LifecycleState` enum: `ACTIVE`, `CANDIDATE`, `QUARANTINED`, `RETIRED`
- [ ] Write `validate_candidate(record)` that checks required fields, enum values, and type consistency
- [ ] Write `validate_registry(path)` that loads JSON and validates every entry
- [ ] Test: create fixture `tests/fixtures/registry_sample.json` with 5 candidates covering all lifecycle + policy states
- [ ] Test: `test_registry_schema.py` — validate_candidate passes on fixture, fails on malformed input
- [ ] Commit: `registry_schema.py + tests + fixture`

### Task 2: Define the evidence accumulator

**Goal:** create `evidence_accumulator.py` that reads telemetry and produces cached evidence blocks.

**Success observation:** `evidence_accumulator.py --compute --lane reasoning` produces evidence blocks for all reasoning-lane candidates with quality scores and sample counts.

**Failure observation:** empty evidence blocks or crash on malformed telemetry.

**Failure signal:** `pick()` returns weight=1.0 for all models (no evidence differentiation).

**Countermove:** check telemetry format compatibility, add fallback for missing fields.

**Steps:**
- [ ] Read `P:/.artifacts/model-telemetry/usage.jsonl` (append-only JSONL)
- [ ] Group by model + lane + task_domain
- [ ] Compute per-group: success_rate, avg_quality (from quality_score field), sample_count, p50/p90 latency
- [ ] Apply sample-size adjustment: effective_n = min(n, cap) where small samples shrink weight
- [ ] Apply Bayesian freshness shrinkage: old evidence → wider posterior → lower confidence → lower weight contribution. NOT decay toward zero or toward own average. Posterior mean stays; confidence interval widens.
- [ ] Tag calibration probes: records with `task_domain: "calibration"` are cohort-tagged separately but still contribute to promotion stats
- [ ] Cache results to `P:/.artifacts/model-evidence/evidence_cache.json` with timestamp
- [ ] CLI: `evidence_accumulator.py --compute [--lane <name>] [--json]`
- [ ] Test: `test_evidence_accumulator.py` — feed fixture telemetry, verify sample-size adjustment + Bayesian shrinkage
- [ ] Commit: `evidence_accumulator.py + tests`

### Task 3: Define verified success + promotion thresholds

**Goal:** create the promotion logic in `circuit_breaker.py` (lifecycle transitions).

**Success observation:** a candidate with 5 verified successes in the coding lane promotes to `active`; a model with 3 consecutive failures quarantines.

**Failure observation:** promotion on unverified calls, or quarantine on transient provider outage.

**Failure signal:** new models stuck in `candidate` forever, or entire providers quarantined on a single outage.

**Countermove:** adjust thresholds; add provider-scoped outage detection.

**Steps:**
- [ ] Define `VerifiedSuccess` check: (1) used intended provider+transport, (2) response satisfied contract, (3) verification passed where exists, (4) no timeout/malformation
- [ ] Define lane-specific promotion thresholds (operator-configurable, default: 5 verified successes in that lane)
- [ ] Implement `check_promotion(candidate, lane)` → promotes candidate→active when threshold met
- [ ] Implement `check_quarantine(candidate)` → quarantines on N consecutive failures (default: 3)
- [ ] Implement **hierarchical circuit breaker**: if >2 models from same provider fail in same time window, quarantine the PROVIDER (not individual models). Auto-unquarantine after provider cooldown (default: 5 min).
- [ ] Implement `check_retirement(candidate)` → retires when all probes return 404/model-not-found
- [ ] Implement auto-reprobe: quarantined models get periodic reprobe (default: every 5 min); success → unquarantine
- [ ] Test: `test_circuit_breaker.py` — promotion on verified success, quarantine on failure, provider-scoped cascade prevention, auto-reprobe
- [ ] Commit: `circuit_breaker.py + tests`

### Task 4: Implement the three selectors

**Goal:** create `model_router.py` with `deterministic()`, `weighted_pool()`, and `diverse_panel()` selectors.

**Success observation:** all three selectors return valid candidates + selection receipts on a test registry.

**Failure observation:** selector returns None, crashes, or produces a receipt missing required fields.

**Failure signal:** calling skills report "no model available" when models ARE available.

**Countermove:** debug the gate chain (which gate filtered the candidate?).

**Steps:**
- [ ] Implement gate chain: `capability_gates → policy_gates → evidence_eligibility → health_gates`
- [ ] Each gate returns (passed: bool, reason: str) for the receipt
- [ ] **`deterministic(lane, requirements)`**: filter via gates → rank by evidence quality + speed + quota headroom → return top candidate + receipt
- [ ] **`weighted_pool(lane, requirements)`**: filter via gates → compute weights from cached evidence → weighted random → return selected + receipt (include random seed, weights, quota snapshot)
- [ ] **`diverse_panel(lane, requirements, count)`**: filter via gates → constraint satisfaction (maximize provider family diversity) → if fewer families than requested, return reduced-diversity receipt with disclosure
- [ ] Implement **bounded exploration**: epsilon-greedy per lane. `deterministic` mode: epsilon% of calls select a random eligible candidate instead of the top-ranked. `weighted_pool`: no additional exploration needed (weighted random IS exploration). `diverse_panel`: no exploration (constraint satisfaction).
- [ ] Exploration gated by task policy: disabled for writes, enabled for reads/mechanical/calibration
- [ ] Selection receipt includes: selected model, selection_mode, eligible candidates, weights/-ranking, gates passed/failed, diversity adjustment, random seed, quota snapshot, timestamp
- [ ] Test: `test_model_router.py` — each mode returns valid candidate + receipt; gates filter correctly; exploration fires at configured epsilon; diverse_panel degrades gracefully
- [ ] Commit: `model_router.py + tests`

### Task 5: Create golden test vectors

**Goal:** create `golden_vectors.py` proving Grok and Codex selectors return equivalent decisions.

**Success observation:** golden vectors pass for both Python and JS selectors on identical registry + evidence inputs.

**Failure observation:** selectors disagree on a test case.

**Failure signal:** CI fails on golden vector divergence after a selector change.

**Steps:**
- [ ] Define 20+ test cases covering: each selection mode, each gate type, edge cases (0 eligible, 1 eligible, all quarantined, reduced diversity, cold-start candidate)
- [ ] Each test case: input (registry fixture + evidence fixture + lane + requirements) → expected output (selected model OR deterministic rank order)
- [ ] Golden vectors stored as JSON: `tests/golden_vectors.json`
- [ ] Python: `golden_vectors.py --verify` runs all vectors against model_router.py
- [ ] JS: Codex's model-selector.mjs gains a `--verify-golden <path>` flag
- [ ] CI: golden vectors run on every change to either selector (Grok pre-commit hook + Codex CI)
- [ ] Test: `test_golden_vectors.py` — all 20+ vectors pass
- [ ] Commit: `golden_vectors.py + golden_vectors.json + tests`

### Task 6: Build the new fleet registry

**Goal:** create `fleet-registry.json` (successor to fleet-models.json) in the new flat-pool format.

**Success observation:** `validate_registry()` passes on the new file. All models from fleet-models.json are represented.

**Failure observation:** missing models, invalid schema, or policy/lifecycle states not set.

**Steps:**
- [ ] Read current `fleet-models.json` — extract all models, their providers, transports, capabilities
- [ ] For each model, create a CandidateRecord with:
  - Lanes (inferred from current tier1/tier2 placement)
  - Capabilities (from config.toml + existing metadata)
  - Policy state (from Go usage policy: use_freely/reasoning_pool/explicit_approval/excluded)
  - Lifecycle: `active` for existing models, `candidate` for newly added this session
  - Evidence refs (from existing quality_scores if present)
- [ ] Include the 11 models added this session as `candidate` lifecycle
- [ ] Include Go models with their usage tier policy states
- [ ] Validate: `registry_schema.validate_registry("fleet-registry.json")` passes
- [ ] Commit: `fleet-registry.json + migration script`

### Task 7: Migrate pick_model.py to delegate to model_router

**Goal:** `pick_model.py` delegates to `model_router.py` internally. Callers see the same function signature but get the new behavior.

**Success observation:** `pick_model.py coding` returns a model selected via the new deterministic mode, with a receipt.

**Failure observation:** crash, or old first-available behavior still present.

**Failure signal:** same model always selected (deterministic without evidence differentiation = first-available in disguise).

**Countermove:** verify evidence accumulator ran; verify gates aren't over-filtering.

**Steps:**
- [ ] Refactor `pick(lane)` to call `model_router.deterministic(lane, requirements)` by default
- [ ] Add `pick(lane, selection_mode="weighted_pool")` for reasoning pool
- [ ] Add `pick(lane, selection_mode="diverse_panel", count=N)` delegating to `diverse_panel()`
- [ ] Return `result["receipt"]` alongside `result["model"]`
- [ ] Do NOT return `result["tier"]` — no tier fields in the output
- [ ] Keep `result["provider"]`, `result["free"]`, `result["dispatch_path"]` for backward compat
- [ ] Test: existing `test_discover.py` tests still pass (they don't test pick() internals)
- [ ] Test: `test_model_router.py` tests pass when called via pick_model.py
- [ ] Commit: migrated pick_model.py

### Task 8: Migrate callers (21+ skills)

**Goal:** all skill files that call `pick_model.py` are updated to not read `result["tier"]`.

**Success observation:** `grep -r 'result\["tier"\]' skills/` returns zero results.

**Failure observation:** KeyError in a skill that still reads tier.

**Failure signal:** skill crash with "KeyError: 'tier'" in logs.

**Countermove:** add `result.get("tier", None)` as a temporary shim for any missed callers.

**Steps:**
- [ ] Find all callers: `rg 'pick_model\.py|result\["tier"\]|result\[.tier.\]' skills/`
- [ ] For each caller: remove `result["tier"]` reads; if the skill uses tier for display, use `result["selection_mode"]` instead
- [ ] For skills that pass `--exclude-self`, verify the exclude logic still works with the new router
- [ ] Test: run each modified skill's test suite (if it has one)
- [ ] Commit: caller migration batch

### Task 9: Remove tier/first-available semantics

**Goal:** fleet-models.json tier arrays are gone. No code references tier1/tier2.

**Success observation:** `rg 'tier1|tier2|first.available' scripts/` returns zero results.

**Failure observation:** stale references cause crashes.

**Steps:**
- [ ] Remove tier1/tier2 arrays from fleet-models.json (keep file as `.bak`)
- [ ] Remove tier iteration logic from pick_model.py
- [ ] Remove `is_available()` tier-checking code
- [ ] Grep for any remaining tier references: `rg 'tier1|tier2' scripts/ tests/`
- [ ] Test: full test suite passes
- [ ] Commit: tier removal

### Task 10: Versioned routing snapshots + rollback

**Goal:** the registry supports versioned snapshots so routing config can roll back without losing evidence history.

**Success observation:** `model_router.py --snapshot` writes a timestamped snapshot; `--rollback <snapshot>` restores it.

**Failure observation:** rollback fails or loses accumulated evidence.

**Steps:**
- [ ] On registry write (lifecycle change, policy change): write versioned snapshot to `P:/.artifacts/model-routing/snapshots/YYYYMMDD-HHMMSS.json`
- [ ] Evidence history stays in `usage.jsonl` (append-only) — snapshots are routing config only, not evidence
- [ ] `--rollback <snapshot>` restores the routing config from that timestamp; evidence is not affected
- [ ] Test: snapshot + rollback preserves evidence while restoring routing config
- [ ] Commit: snapshot/rollback feature

## Rejected alternatives

| Alternative | Rejected because |
|---|---|
| Static hand-tuned weights | Drift from reality; reinvents what quality_scores already provides |
| Universal weighted random (my original proposal) | Makes routine work nondeterministic for no benefit |
| Shared Python library for Codex | Codex is Node-based; can't import Python without subprocess |
| External CLI router | 200ms overhead per selection; unnecessary for in-process call |
| Tier adapter (fake tier:1 in output) | Preserves the exact semantics we're removing |
| Decay evidence toward prior or own average | Artificially reduces confidence in proven models |
| Big-bang cutover | 21+ callers break simultaneously if new router has a bug |

## Risks and mitigations (from /risk assessment)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Evidence self-reinforcement lockout | HIGH | Bounded exploration epsilon per lane (disabled for writes) |
| Quarantine cascade on provider outage | HIGH | Hierarchical circuit breakers (provider-scoped quarantine + cooldown) |
| Policy vs evidence precedence undefined | HIGH | Hard gate ordering: policy filters BEFORE weighting |
| Schema migration breaks callers | MEDIUM | Staged migration (Task 8), no fake tier fields |
| Golden vector drift between Python/JS | MEDIUM | CI gate on every selector change |
| Freshness punishes proven models | MEDIUM | Bayesian posterior shrinkage (confidence widens, mean preserved) |
| Weight computation latency | LOW | Cached derived weights; evidence accumulator runs periodically |
| No rollback path | MEDIUM | Versioned routing snapshots (Task 10) |

## Verification

- [ ] `pytest tests/test_model_router.py tests/test_evidence_accumulator.py tests/test_circuit_breaker.py tests/test_golden_vectors.py` — all pass
- [ ] `python golden_vectors.py --verify` — all 20+ vectors pass
- [ ] `rg 'tier1|tier2' scripts/ tests/` — zero results
- [ ] `rg 'result\["tier"\]' skills/` — zero results
- [ ] `registry_schema.validate_registry("fleet-registry.json")` — passes
- [ ] Manual: `pick_model.py coding` returns different models across calls (deterministic with evidence differentiation, not first-available)
- [ ] Manual: `pick_model.py --lane reasoning --mode weighted_pool` returns weighted-random selections
- [ ] Manual: quarantine a model, verify it's excluded, verify auto-reprobe restores it

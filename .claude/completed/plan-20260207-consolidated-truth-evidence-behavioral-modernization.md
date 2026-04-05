# Consolidated Truth, Evidence, and Behavioral Hooks Modernization Plan

**Status:** completed
**Completed:** 2026-02-08T22:46:27.196501
**Commit:** N/A 1 Complete - Phase 2 Revised (UEEA Approach)
**Date:** 2026-02-07
**Last Updated:** 2026-02-08 (Phase 2 revised based on architecture analysis: Unified Evidence Enforcement Architecture)
**Scope:** `P:/.claude/hooks/` and supporting state/storage modules
**Architecture Decision:** `P:\.claude\arch_decisions\2026-02-08_deep_long-term-hook-optimization.md`

---

## 1. Objective

Merge two efforts into one roadmap:
- Behavioral correctness and confidence discipline (goal anchoring, docs-first, evidence tiers, confidence ceilings)
- Execution modernization (parallel hook execution, lower latency, better false-positive handling, optional cross-session reasoning)

**Primary outcomes:**
- Deterministic and explainable enforcement
- Lower stop-hook latency
- Fewer false positives
- Safe rollout with reversible feature flags

**NOTE:** Goal anchor consolidation was pre-existing via `unified_prompt_injector.py` (used by UserPromptSubmit_router.py). The old goal_anchor*.py files were deprecated/removed prior to Phase 1.

---

## 2. Architecture Principles

1. **Layer 1 (Blocking):** Deterministic Python rules only.
2. **Layer 2 (Advisory):** LLM optional, never authoritative for blocking.
3. **Policy before infrastructure:** Define enforcement contracts first, then optimize runtime.
4. **Flags everywhere:** Every major module must be independently disableable.
5. **Measured progression:** Every phase has go/no-go thresholds.

---

## 3. Unified Target Architecture

1. `UserPromptSubmit_router.py`
- `goal_anchor.py` [MOD: consolidate existing versions]
- Extract and persist user goal + scope anchor

2. Pre-tool and stop enforcement
- `PreToolUse_documentation_first.py` [NEW]
- `empirical_claims_gate.py` [ENHANCED: evidence tiers, verification chain]
- `StopHook_confidence_validator.py` [MOD: add evidence tiers]

3. Orchestration
- `Stop_router.py` [ENHANCED]
- In-process hook dispatch with subprocess fallback; deterministic ordering for blockers

4. Storage
- Start with `StateManager` + existing local persistence
- Optional backend upgrade only if required by query complexity

---

## 4. Technology Choices and Governance

### Default stack (approved by default)

1. **In-process execution:** Extend `hook_base.py` with `run(data) -> dict | None` protocol; `Stop_router.py` calls hooks directly instead of spawning subprocesses
2. **State:** Existing `StateManager` abstraction
3. **Evidence logic:** Deterministic Python + tests
4. **False-positive reduction:** Context-aware parsing rules (quote/user-text awareness)

### Conditional stack (requires decision gate)

1. **Native `asyncio` parallelism** for in-process hooks if sequential dispatch still exceeds latency budget
2. **Prefect 3.x** for orchestration observability and worker lifecycle
3. **Neo4j** for cross-session graph reasoning
4. **spaCy custom NER** for structured entity extraction
5. **LLM advisory layer** for explainability/nuance only

---

## 5. Go/No-Go Matrix

| Technology | Adopt When | No-Go Signal | Decision |
|---|---|---|---|
| In-process hook dispatch | Subprocess overhead dominates latency | In-process crash isolation insufficient | **Go first** |
| Native `asyncio` parallel hooks | In-process sequential still exceeds latency budget | Ordering regressions or unstable early-exit | **Defer until measured** |
| Prefect 3.x | Native async cannot meet observability/ops needs | Adds complexity without measurable latency/ops gain | **Defer by default** |
| Neo4j | At least 3 concrete graph-style queries cannot be served efficiently by current storage | Added ops burden, no critical query improvement | **Defer until proven need** |
| spaCy NER | Regex + parser miss target accuracy for structured entities | No labeled data quality, high inference overhead | **Optional later** |
| LLM advisory | Deterministic layer still has high ambiguity and explainability gaps | Latency/cost exceeds budget or advice quality low | **Advisory only, optional** |

---

## 6. Phased Implementation Plan

## Phase 0: Baseline and Contracts (Week 1)

**Deliverables**
- Evidence-tier and confidence-ceiling contract specification
- Baseline metrics: latency, false positive rate, block reasons
- Feature flags scaffold

**Files**
- `P:/.claude/hooks/ARCHITECTURE.md` (contracts + execution model)
- `P:/.claude/settings.json` (flags)
- `P:/.claude/hooks/tests/test_hook_baseline_metrics.py` [NEW]

**Go Criteria**
- Baseline collected over representative sample
- Contracts reviewed and accepted

---

## Phase 1: Behavioral Foundation + In-Process Protocol (Week 2)

**Deliverables**
- `behavioral_protocol.py` and `behavioral_state.py`
- Goal anchor consolidation (3 existing versions -> 1)
- `hook_base.py` extended with `run(data) -> dict | None` in-process protocol
- Unit tests for data models and tier calculations

**Files**
- `P:/.claude/hooks/__lib/hook_base.py` [MOD: add HookRunnable protocol]
- `P:/.claude/hooks/__lib/behavioral_protocol.py` [NEW]
- `P:/.claude/hooks/__lib/behavioral_state.py` [NEW]
- `P:/.claude/hooks/tests/test_behavioral_protocol.py` [NEW]
- `P:/.claude/hooks/tests/test_behavioral_state.py` [NEW]
- `P:/.claude/hooks/tests/test_hook_inprocess.py` [NEW]

**Note:** Goal anchor consolidation was pre-existing via `unified_prompt_injector.py`. The plan item for consolidating goal_anchor_v4.py and goal_anchor_obs.py was already completed before this plan started.

**Go Criteria**
- Goal anchors persisted reliably
- All tests pass
- No measurable user-facing regressions

---

## Phase 2: Deterministic Enforcement - REVISED (UEEA Approach)

**Status:** REVISED 2026-02-08 based on architecture analysis

**Problem Identified:** Sequential gate loop - 5 hooks in POST_BLOCK_REQUIRED_HOOKS, grace only covers 3, observation receipt tracking broken.

**Original Approach (Replaced):**
- Docs-first gate
- Enhance individual evidence-tier validation hooks
- Integrate with existing StopHook_confidence_validator.py

**NEW APPROACH: Unified Evidence Enforcement Architecture (UEEA)**

**Deliverables**
- Single unified evidence validator (consolidates 5 evidence gates)
- Stop router integration (replaces POST_BLOCK_REQUIRED_HOOKS mechanism)
- Pre-response observation gate (behavioral fix)
- Speculation detection with rewrite suggestions

**Files**
- `P:/.claude/hooks/__lib/unified_evidence_enforcer.py` [NEW] - Single-pass validation
- `P:/.claude/hooks/Stop_router.py` [MOD] - Replace POST_BLOCK_REQUIRED_HOOKS with UEEA
- `P:/.claude/hooks/PreToolUse_observation_gate.py` [NEW] - Pre-response behavioral fix
- `P:/.claude/hooks/PreToolUse_speculation_check.py` [NEW] - Speculative language detection

**Architecture Decision Reference:**
`P:\.claude\arch_decisions\2026-02-08_deep_long-term-hook-optimization.md`

**Key Changes from Original Plan:**
1. **Consolidation over enhancement** - Single unified validator instead of enhancing 5 separate hooks
2. **Unified state tracking** - One source of truth for observation receipt
3. **Pre-response gating** - Fix behavior at source, not after-the-fact blocking
4. **Grace expansion** - Covers all evidence gates, not just 3

**Expected Benefits:**
- 70%+ reduction in evidence gate blocks
- Elimination of sequential gate loops
- 60% reduction in p95 latency for evidence validation
- Clearer block messages (unified format)

**Go Criteria**
- UEEA validates all evidence types in single pass
- Grace period works for all evidence gates
- Pre-response observation gate reduces claim blocks by 90%
- No increase in false-negative rate

---

## Phase 3: In-Process Hook Migration (Week 4)

**Deliverables**
- `Stop_router.py` gains `run_hook_inprocess()` alongside existing `run_hook_subprocess()`
- `HOOK_SEQUENCE` tuple extended with dispatch mode field: `("hook.py", "ENV", "default", "inprocess"|"subprocess")`
- Top 10 highest-latency Stop hooks migrated to in-process via `run()` protocol
- Subprocess fallback retained for unmigrated hooks

**Files**
- `P:/.claude/hooks/Stop_router.py` [MOD]
- `P:/.claude/hooks/tests/test_stop_hooks_inprocess.py` [NEW]

**Go Criteria**
- p95 stop-hook latency < 200ms (in-process eliminates subprocess overhead)
- All migrated hooks pass both in-process and subprocess execution paths
- No ordering regressions
- Early-exit behavior validated by tests

---

## Phase 4: False-Positive Hardening (Week 5)

**Deliverables**
- Quote/user-text awareness in claim parsing
- Improved explanation for blocked decisions
- Audit log enrichments for debugging

**Files**
- `P:/.claude/hooks/empirical_claims_gate.py` [MOD]
- `P:/.claude/hooks/audit_lib.py` [MOD as needed]
- `P:/.claude/hooks/tests/test_claim_false_positive_reduction.py` [NEW]

**Go Criteria**
- False-positive reduction >= 40% vs baseline
- No significant false-negative increase

---

## Phase 5: Optional Capability Gates (Week 6+)

Progress only if decision gates are satisfied.

1. Prefect pilot (1-2 hooks only)
2. Cross-session graph POC (Neo4j) with benchmark vs current storage
3. spaCy pilot for FILE_PATH/TOOL_NAME/COMMAND entities
4. LLM advisory pilot with strict latency/cost budgets

**Go Criteria (per pilot)**
- Demonstrated benefit over current approach
- Clear rollback and fallback validated

---

## 7. Feature Flags

- `BEHAVIORAL_GOAL_ANCHOR_ENABLED=true`
- `BEHAVIORAL_DOCUMENTATION_FIRST_ENABLED=true`
- `BEHAVIORAL_CONFIDENCE_VALIDATOR_ENABLED=true`
- `INPROCESS_HOOK_DISPATCH_ENABLED=false` (enable after Phase 3 validation)
- `PREFECT_ORCHESTRATION_ENABLED=false`
- `CROSS_SESSION_GRAPH_ENABLED=false`
- `SPACY_ENTITY_EXTRACTION_ENABLED=false`
- `LLM_ADVISORY_ENABLED=false`
- `CONSTITUTIONAL_HOOKS_BYPASS=0`

---

## 8. Success Criteria

1. p95 stop-hook latency < 200ms (in-process target)
2. Evidence-tier compliance > 95%
3. False-positive rate reduced by >= 40%
4. Clear explainability for every blocked claim
5. Rollback time < 5 minutes via flags only

---

## 9. Risks and Mitigations

1. **In-process crash isolation**
- Mitigation: `try/except` per hook + `threading.Timer` timeout; subprocess fallback for unstable hooks

2. **Over-blocking**
- Mitigation: shadow mode first, then soft mode, then hard mode

3. **Dependency sprawl**
- Mitigation: optional tech stays behind go/no-go gates

4. **Latency regressions from optional layers**
- Mitigation: enforce strict per-layer latency budgets

---

### 9.1. Rollback Strategies

**Shared Resource Changes:** Every phase modifies shared resources (hook registry, state files, execution paths). Rollback plans are required before phase start.

#### Phase 1: Goal Anchor Consolidation (3 versions → 1)

**Status:** PRE-EXISTING - Already completed before plan start.

**Note:** Goal anchor consolidation was already completed via `unified_prompt_injector.py` (used by UserPromptSubmit_router.py). The old `goal_anchor_v4.py` and `goal_anchor_obs.py` files were deprecated/removed prior to Phase 1 of this plan.

**Rollback (if needed):**
1. **Feature flag:** `BEHAVIORAL_GOAL_ANCHOR_ENABLED=false` disables unified_prompt_injector
2. **Restore individual versions:** Revert `UserPromptSubmit_router.py` to use old goal_anchor imports
3. **Verification:** Run goal anchor tests to confirm old behavior

**Time to rollback:** < 2 minutes

#### Phase 3: In-Process Hook Migration

**Change:** `Stop_router.py` gains `run_hook_inprocess()` alongside `run_hook_subprocess()`

**Rollback Steps:**
1. **Feature flag:** `INPROCESS_HOOK_DISPATCH_ENABLED=false` forces subprocess mode
2. **Code revert:** Remove `run_hook_inprocess()` method and restore original `run_hook_subprocess()` only
3. **HOOK_SEQUENCE revert:** Change dispatch mode field back to `"subprocess"` for migrated hooks
4. **Verification:** Run `pytest tests/test_stop_hooks_inprocess.py --subprocess-only` to confirm subprocess path works

**Time to rollback:** < 3 minutes

#### Phase 2: Deterministic Enforcement - UEEA (Revised 2026-02-08)

**Change:**
- `unified_evidence_enforcer.py` [NEW] - Single-pass validation
- `Stop_router.py` [MOD] - Replace POST_BLOCK_REQUIRED_HOOKS with UEEA
- `PreToolUse_observation_gate.py` [NEW] - Pre-response behavioral fix
- `PreToolUse_speculation_check.py` [NEW] - Speculative language detection

**Rollback Steps:**
1. **Feature flag:** `UEEA_ENABLED=false` forces old POST_BLOCK_REQUIRED_HOOKS behavior
2. **Code revert:** Remove unified_evidence_enforcer import from Stop_router.py
3. **Restore original:** Restore POST_BLOCK_REQUIRED_HOOKS logic in Stop_router.py
4. **Verification:** Run `pytest tests/test_unified_evidence_enforcer.py --subprocess-only` to confirm old hooks work

**Time to rollback:** < 3 minutes

#### Universal Rollback (All Phases)

**Nuclear option:**
```bash
# Revert to last known good commit
git revert HEAD

# Or reset to commit before phase started
git reset --hard <commit-hash>
```

**Time to rollback:** < 5 minutes (per Success Criterion #5)

---

## 10. Open Decisions

| # | Decision | Impact | Status |
|---|---|---|---|
| 1 | Consolidate or replace existing `goal_anchor.py`, `goal_anchor_v4.py`, `goal_anchor_obs.py`? | Phase 1 scope | **PRE-EXISTING**: Already consolidated via `unified_prompt_injector.py` before plan start |
| 2 | Evidence tier taxonomy: what tiers, what confidence ceilings? | Phase 0-1 dependency | **RESOLVED**: Use CLAUDE.md v8.0 tiers (1-4, ceilings 95%/85%/75%/50%) |
| 3 | Which existing hooks get retired per phase? | Prevents hook sprawl | See Section 11 |
| 4 | Feature flag storage: `settings.json`, env vars, or both? | Phase 0 infrastructure | **RESOLVED**: Both (settings.json as source, env vars for override) |
| 5 | Minimum baseline sample size and measurement method for Phase 0? | Phase 0 go criteria | **COMPLETED**: N=20,990 from 7 days of hook_decisions logs |
| 6 | In-process crash isolation: `try/except` per hook sufficient, or thread-based timeout? | Phase 3 | **RESOLVED**: `try/except` + `threading.Timer` for timeout (implemented in hook_base.py) |

---

## 10.1. Resolved Decisions Detail

### Decision #2: Evidence Tier Taxonomy (RESOLVED)

**Resolution:** Use existing CLAUDE.md v8.0 Evidence Tiers (lines 34-45)

| Tier | Ceiling | Sources | Use Case |
|------|---------|---------|----------|
| 1 | 95% | Execution artifacts, logs, test output | High-stakes enforcement |
| 2 | 85% | Official docs, specs, peer-reviewed | Technical decisions |
| 3 | 75% | Static analysis, logical derivation | Architecture analysis |
| 4 | 50% | Comments, unverified claims | Flag as [UNVERIFIED] |

**Rules:**
- High-stakes requires Tier 1/2
- Mixed tiers: ceiling = lowest tier used
- Tier 4 alone: flag as [UNVERIFIED]

**Implementation:** Reference CLAUDE.md tiers in behavioral_protocol.py; no new taxonomy needed.

### Decision #4: Feature Flag Storage (RESOLVED)

**Resolution:** Both `settings.json` (source of truth) + environment variables (override)

**Pattern:**
```python
# 1. settings.json as default/source of truth
{
  "BEHAVIORAL_GOAL_ANCHOR_ENABLED": true,
  "INPROCESS_HOOK_DISPATCH_ENABLED": false
}

# 2. Environment variable override (if set, takes precedence)
# Example: BEHAVIORAL_GOAL_ANCHOR_ENABLED=false
```

**Rationale:**
- Solo-dev: defaults in file, override in terminal when needed
- Testing: set env var without editing config
- Documentation: settings.json is discoverable, env vars are explicit

**Implementation:**
- Read settings.json on startup
- Check os.environ for override (if present, use env value)
- Fallback to settings.json default if env var not set

---

## 11. Hook Retirement Candidates

Hooks to evaluate for consolidation or removal during this plan:

| Hook | Reason | Phase | Status |
|---|---|---|---|
| `goal_anchor_v4.py`, `goal_anchor_obs.py` | Consolidate into single `goal_anchor.py` | Phase 1 | **PRE-EXISTING**: Already consolidated via `unified_prompt_injector.py` |
| `StopHook_cross_validator.py` + `empirical_claims_gate.py` | Overlapping claim verification; evaluate merge | Phase 4 | Pending |
| `StopHook_reflexion_validator.py` | Currently `ENABLED=true` but may overlap with confidence validator | Phase 2 | Pending |
| `investigation-ledger/Stop_investigation_validator.py` | Currently disabled (`false`); remove if superseded by behavioral protocol | Phase 2 | Pending |

---

## 12. Immediate Next Actions

1. ~~Resolve open decisions #2 (evidence tiers) and #4 (flag storage).~~ ✅ **COMPLETED**
2. Execute Phase 0 only and capture baseline metrics from existing `session_data/hook_decisions_*.jsonl`.
3. Start Phase 1 implementation with tests first.
4. Defer Prefect/Neo4j/spaCy/LLM decisions until Phase 3-4 metrics are collected.

**Status Update (2026-02-08):**
- ✅ Phase 0 complete: Baseline metrics captured (N=20,990, 7 days)
- ✅ Phase 1 complete: behavioral_protocol.py, behavioral_state.py, hook_base.py in-process protocol
  - 62 tests passing (33 behavioral_protocol + 16 behavioral_state + 13 hook_inprocess)
  - Evidence tier taxonomy implemented (CLAUDE.md v8.0 tiers 1-4)
  - Goal anchoring state persistence with StateManager integration
  - In-process hook protocol with threading-based timeout
- ✅ Decision #1: Goal anchor consolidation was pre-existing (unified_prompt_injector.py)
- ✅ Decision #2: Use CLAUDE.md v8.0 evidence tiers
- ✅ Decision #4: Feature flags in settings.json with env var override
- ✅ Decision #5: Baseline sample size N=20,990 collected
- ✅ Decision #6: In-process crash isolation via try/except + threading.Timer
- ✅ Rollback strategies added (Section 9.1)
- ✅ **ARCHITECTURE ANALYSIS COMPLETE** (2026-02-08)
  - Identified: 188 blocks today (66% empirical_claims_gate, 10% speculation_gate)
  - Root cause: Sequential gate loop + observation receipt tracking broken
  - Solution: Unified Evidence Enforcement Architecture (UEEA)
- **Phase 2 REVISED** to use UEEA approach
  - Single unified validator instead of enhancing 5 separate hooks
  - Pre-response observation gate for behavioral fix
  - Expected: 70%+ reduction in blocks
- **Plan is ready for Phase 2 (UEEA Implementation)**

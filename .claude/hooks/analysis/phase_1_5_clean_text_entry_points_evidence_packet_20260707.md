# Phase 1.5 — Clean-text entry points for 3 tool_events gates — Evidence Packet

**Date:** 2026-07-07
**Scope:** Wire pure-text predicates for deletion_verification_guard,
perf_attribution, unverified_stance into `replay_eval.py` so their fixtures
get LIVE replay (was structural-only). Resolve e1960aff dead reference.
**Program:** Close-the-Loop telemetry reliability (Phase 1.5)
**Status:** GREEN. STRUCTURAL 6/6, LIVE 6/6 (was 3/3), corrupt-test 5/5
(was 4/4).

---

## 1. Deliverables

| Path | Role |
|------|------|
| `evals/replay_eval.py` | runner — added `LIVE_GATES` registry (gate_name → module, fn, shape) + `_load_predicate()` helper. Replaces hardcoded `live_gate == "epistemic_contract"` branch with a generic shape dispatch |
| `evals/gold/a07ff025.json` | `live_gate: "deletion_verification_guard"` + `live_expected_claim_count: 1` |
| `evals/gold/0f183615.json` | `live_gate: "perf_attribution"` + `live_expected_bool: false` (regression test for #1089 FP fix) |
| `evals/gold/b2014a6e.json` | `live_gate: "unverified_stance"` + `live_expected_phrase: null` |
| `evals/test_replay_eval_corrupt.py` | added `test_corrupt_text_predicate_detected` (5th corruption mode: flips `live_expected_bool` on 0f183615) |
| `evals/misses.jsonl` | unchanged — e1960aff seed confirmed (see §5) |

---

## 2. Per-site table

| Fixture | live_gate | Predicate (plugin source) | Expected | Shape | Rationale |
|---------|-----------|---------------------------|----------|-------|-----------|
| a07ff025 | deletion_verification_guard | `_detect_deletion_claims` at `cc-aca-epistemic/hooks/stop/Stop_deletion_verification_guard.py` | `claim_count == 1` | `claims_list` (count-based) | The fixture's text contains "removed \|" → 1 matched claim. Path extraction is noisy (markdown backticks, table commas); count-based assertion detects regressions without conflating path-extraction improvements with behavioral changes |
| 0f183615 | perf_attribution | `_detect_perf_claims` at `cc-aca-epistemic/hooks/stop/StopHook_perf_attribution_gate.py` | `False` | `bool` | **Regression test for #1089** — qualitative-ROI prose ("dominant factor") must NOT trip the gate post-fix. If this flips to True, #1089 regressed |
| b2014a6e | unverified_stance | `_check_unfounded_system_claims` at `cc-aca-epistemic/hooks/stop/StopHook_unverified_stance.py` | `None` | `phrase_or_none` | The recorded BLOCK ("MULTIPLE VERIFICATION VIOLATIONS: Phase 2 Protocol Adherence") came from a different detector branch (multi-violation counter), not the unfounded-system-claim branch. live_expected_phrase=null confirms the unfounded-system-claim detector is silent on this text |

---

## 3. Raw test output

### 3a. `replay_eval.py` — GREEN (LIVE 6/6, was 3/3)

```
$ python P:/.data/evals/replay_eval.py

=== 0f183615 (perf_attribution_unverified) ===
  turn1 STRUCTURAL hash=8df1127b98b1527c OK
  turn1 LIVE       perf_attribution OK (bool want=False got=False)

=== 4897f5bd (epistemic_triple_fire_recovery) ===
  turn1 STRUCTURAL hash=6b7ea9c477bc42c3 OK
  turn1 LIVE       decision=allow types=[] OK
  turn2 STRUCTURAL hash=719b6e27d83ba381 OK
  turn2 LIVE       decision=allow types=['format'] OK
  turn3 STRUCTURAL hash=eba5d4a28d54cb44 OK
  turn3 LIVE       decision=warn types=['unsupported_fact'] OK

=== a07ff025 (deletion_verification_unverified_claim) ===
  turn1 STRUCTURAL hash=c9e18d3c12e4c087 OK
  turn1 LIVE       deletion_verification_guard OK (claim_count want=1 got=1)

=== b2014a6e (unverified_stance_empty_hedge) ===
  turn1 STRUCTURAL hash=e03bca2cdfce5b05 OK
  turn1 LIVE       unverified_stance OK (phrase want=None got=None)

--- SUMMARY ---
STRUCTURAL 6/6 ok
LIVE       6/6 ok  (of 6 live-eligible turns)
DRIFT findings: 3
  4897f5bd turn1: recorded={'decision': 'block', 'types': ['format']} -> live={'decision': 'allow', 'types': []}
  4897f5bd turn2: recorded={'decision': 'block', 'types': ['format']} -> live={'decision': 'allow', 'types': ['format']}
  4897f5bd turn3: recorded={'decision': 'block', 'types': ['unsupported_fact']} -> live={'decision': 'warn', 'types': ['unsupported_fact']}

RESULT: GREEN
```

LIVE coverage went from **3/3 (1 fixture eligible)** to **6/6 (all 4 fixtures eligible)**. The 3 previously structural-only fixtures now exercise their pure-text predicate against the exact recorded assistant text — catching future regressions in the text-detection layer of those gates.

### 3b. `test_replay_eval_corrupt.py` — mismatch detection (5/5, was 4/4)

```
$ python -m pytest P:/.data/evals/test_replay_eval_corrupt.py -v
collected 5 items

evals/test_replay_eval_corrupt.py::test_baseline_green PASSED                       [ 20%]
evals/test_replay_eval_corrupt.py::test_corrupt_assistant_text_detected PASSED       [ 40%]
evals/test_replay_eval_corrupt.py::test_corrupt_response_hash_detected PASSED        [ 60%]
evals/test_replay_eval_corrupt.py::test_corrupt_live_expected_detected PASSED        [ 80%]
evals/test_replay_eval_corrupt.py::test_corrupt_text_predicate_detected PASSED      [100%]

============================== 5 passed in 0.27s ==============================
```

New corruption mode (`test_corrupt_text_predicate_detected`): flips
`live_expected_bool` on 0f183615.json from False → True; runner must report
LIVE [**FAIL**] with `perf_attribution` in the detail line (proves the registry
path catches mismatch, not just the hardcoded epistemic_contract branch).

---

## 4. Registry design (Ponytail: minimal diff)

`replay_eval.py` now has a single `LIVE_GATES` mapping at module top:

```python
LIVE_GATES = {
    "epistemic_contract": ("", "validate", "epistemic"),
    "deletion_verification_guard": (
        "Stop_deletion_verification_guard.py", "_detect_deletion_claims", "claims_list"
    ),
    "perf_attribution": (
        "StopHook_perf_attribution_gate.py", "_detect_perf_claims", "bool"
    ),
    "unverified_stance": (
        "StopHook_unverified_stance.py", "_check_unfounded_system_claims", "phrase_or_none"
    ),
}
```

Per-turn dispatch: `spec = LIVE_GATES.get(gate)` → branch on shape. Shapes
supported: `epistemic` (validate + verdict), `claims_list` (count OR exact),
`bool` (direct), `phrase_or_none` (matched-phrase OR null).

The 3 new predicates are loaded from the **plugin source** (cc-aca-epistemic's
`hooks/stop/` dir), not from `P:/.claude/hooks/` compat_loaders — same
holdout discipline as Phase 1 (single source of truth, no hand-copied
prompts, no compat-layer drift).

---

## 5. e1960aff dead reference resolution

**Confirmed: seed stands.** `P:/.data/evals/misses.jsonl` contains:

```json
{"missed_fixture_id": "e1960aff", "intended_behavior_class":
 "lazy_workaround_self_referential_fp", "session_id":
 "e1960aff-ee1d-412c-92ae-cb742f971217", "discovered": "2026-07-07",
 "reason": "Plan named e1960aff as lazy_workaround self-referential FP
 fixture, but stop_blocks.jsonl has 0 rows for this session (any prefix).
 Fix #1214 removed the producing code path; historical blocks rotated out
 of the log. No extant corpus evidence to pin the fixture to. self_referen
 rows that do exist are unverified_stance gate (72769f32, a07ff025), a
 different behavior class.",
 "program_phase": "Phase 1",
 "resolution": "Recorded as misses-ledger seed; re-locate a real
 lazy_workaround FP block if stop_blocks history is recovered, else retire
 the behavior class."}
```

Confirmed against this session's stop_blocks.jsonl tally:
- e1960aff prefix: **0 rows** (corpus evidence absent — confirms "dead
  reference")
- self_referen rows that DO exist: unverified_stance gate (a07ff025
  fixture, 72769f32 session) — different behavior class
- lazy_workaround rows: **62** — different sessions, different
  proximity-FP patterns (e.g. "duplicate" near "acceptable"), NOT the
  self-referential pattern of #1214. These are Phase 5 promotion leads for
  the lazy_workaround gate itself, not Phase 1.5 fixtures.

Rule 7 forbids substituting a different behavior class without replay
evidence. Shipped-as-seed stands; resolution will be re-attempted at
Phase 5 when stop_blocks history is recoverable (or the behavior class is
retired).

---

## 6. Unresolved items

- **#906 auto-commit hook**: Phase 1.5 work NOT auto-committed. `git status
  --short` shows nothing under `P:/.data/evals/` (entire dir remains
  untracked, same as Phase 1). No new SHA to record this phase. Tracked
  under task #1256.
- **dead `has_live` var** removed from Phase 1 packet's flagged leftover
  (cleaned up in this rewrite).
- **Path-extraction noise** on a07ff025 (markdown backticks, table commas):
  count-based assertion accepted as the regression-detection signal;
  exact-match remains available via `live_expected_claims` for future
  fixtures with cleaner text. Documented in `live_note` field.
- **b2014a6e live_expected_phrase=null**: this asserts the
  unfounded-system-claim sub-detector is silent on the text; the recorded
  BLOCK was a different sub-detector. Phase 5 (misses ledger) may add a
  separate fixture for the multi-violation branch.

---

## 7. Gate criteria satisfied (Phase 1.5 verify bar)

- ✅ Pure-text entry points wired for all 3 deferred gates
  (deletion_verification_guard, perf_attribution, unverified_stance)
- ✅ LIVE coverage doubled: 3/3 → **6/6** of all corpus turns
- ✅ All 4 fixtures now exercise live gate predicates (was 1/4)
- ✅ 0f183615 fixture functions as #1089 regression test
- ✅ Corruption detection extended to text-predicate path (5/5)
- ✅ e1960aff resolution confirmed (misses.jsonl seed stands, Rule 7)
- ✅ No regression on existing 4 tests
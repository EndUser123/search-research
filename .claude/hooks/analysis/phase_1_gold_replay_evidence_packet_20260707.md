# Phase 1 — Gold Replay Corpus + Runner — Evidence Packet

**Date:** 2026-07-07
**Scope:** Build `evals/gold/` fixtures for 4 real gate-block transcripts +
`replay_eval.py` mirroring `cc-aca-epistemic/.eval/judge_eval.py` holdout
discipline. Prove: green on expected; corrupt-one-fixture mismatch detection.
**Program:** Close-the-Loop telemetry reliability (Phase 1 of 6)
**Status:** GREEN. STRUCTURAL 6/6, LIVE 3/3, corrupt-test 4/4.

---

## 1. Deliverables

| Path | Role |
|------|------|
| `evals/gold/4897f5bd.json` | epistemic triple-fire + partial recovery (3 turns, live gate) |
| `evals/gold/a07ff025.json` | deletion_verification unverified claim (structural-only) |
| `evals/gold/0f183615.json` | perf_attribution re-fire (structural-only) |
| `evals/gold/b2014a6e.json` | unverified_stance empty-hedge (structural-only) |
| `evals/extract_fixtures.py` | provenance tool — pulls assistant_text by response_hash from transcripts, verifies hash, overlays expectations |
| `evals/replay_eval.py` | runner — single-source live `validate()` import; STRUCTURAL + LIVE + DRIFT layers |
| `evals/test_replay_eval_corrupt.py` | mismatch-detection test (baseline + 3 corruption modes) |
| `evals/misses.jsonl` | seed entry: e1960aff dead reference (Phase 5 ledger) |

---

## 2. Fixture provenance + check paths (per-fixture table)

| Fixture | behavior_class | session_id | turns | live_gate | STRUCTURAL path | LIVE path |
|---------|----------------|------------|-------|-----------|-----------------|-----------|
| 4897f5bd | epistemic_triple_fire_recovery | 4897f5bd-86c4-4c1a-92cc-ee340a178a72 | 3 | epistemic_contract | re-hash(text)==response_hash | `validate(text)` vs live_expected_* |
| a07ff025 | deletion_verification_unverified_claim | a07ff025-ea44-41fa-b2c2-deaa913037e3 | 1 | None (needs tool_events) | re-hash + recorded-gate pin | skip |
| 0f183615 | perf_attribution_unverified | 0f183615-e030-4cf6-8d90-fc2e68400ce | 1 | None | re-hash + recorded-gate pin | skip |
| b2014a6e | unverified_stance_empty_hedge | b2014a6e-622f-4bf1-9c07-8e09a45f9abd | 1 | None | re-hash + recorded-gate pin | skip |

`response_hash` algorithm (reverse-engineered from
`stop_block_log._response_fingerprint`): `sha256(concat(message.content[*].text
where type=='text') of last assistant msg with text)[:16]`. Verified by
`extract_fixtures.py` asserting the rebuilt hash matches the recorded
`response_hash` for every fixture before writing — all 6 turns resolved to exact
transcript turns.

**Two-layer corpus design (drift-aware).** Each fixture encodes BOTH the
historical intent (what the block record says happened) AND the live expected
(current `validate()` output). `replay_eval` asserts only the STRUCTURAL hash +
the LIVE expected; the recorded-vs-live DELTA is REPORTED as a finding, never
asserted against. This is the exact telemetry-reliability gap the program
exists to surface — a gate that drifted post-#1215 should not make the corpus
silently rewrite history.

---

## 3. Raw test output

### 3a. `replay_eval.py` — GREEN

```
$ python P:/.claude/hooks/evals/replay_eval.py

=== 4897f5bd (epistemic_triple_fire_recovery) ===
  turn1 STRUCTURAL hash=6b7ea9c477bc42c3 OK
  turn1 LIVE       decision=allow types=[] OK
  turn2 STRUCTURAL hash=719b6e27d83ba381 OK
  turn2 LIVE       decision=allow types=['format'] OK
  turn3 STRUCTURAL hash=eba5d4a28d54cb44 OK
  turn3 LIVE       decision=warn types=['unsupported_fact'] OK

=== a07ff025 (deletion_verification_unverified_claim) ===
  turn1 STRUCTURAL hash=c9e18d3c12e4c087 OK
  turn1 LIVE       skip (no clean-text gate; structural-only)

=== b2014a6e (unverified_stance_empty_hedge) ===
  turn1 STRUCTURAL hash=e03bca2cdfce5b05 OK
  turn1 LIVE       skip (no clean-text gate; structural-only)

=== 0f183615 (perf_attribution_unverified) ===
  turn1 STRUCTURAL hash=8df1127b98b1527c OK
  turn1 LIVE       skip (no clean-text gate; structural-only)

--- SUMMARY ---
STRUCTURAL 6/6 ok
LIVE       3/3 ok  (of 3 live-eligible turns)
DRIFT findings: 3
  4897f5bd turn1: recorded={'decision': 'block', 'types': ['format']} -> live={'decision': 'allow', 'types': []}
      ANALYSIS plain-prose format block removed post-#1215; turn no longer fires. Historical block was real.
  4897f5bd turn2: recorded={'decision': 'block', 'types': ['format']} -> live={'decision': 'allow', 'types': ['format']}
      format issue still detected; decision downgraded block->allow (ANALYSIS format-only -> warn/allow post-#1215).
  4897f5bd turn3: recorded={'decision': 'block', 'types': ['unsupported_fact']} -> live={'decision': 'warn', 'types': ['unsupported_fact']}
      unsupported_fact still detected; decision downgraded block->warn.

RESULT: GREEN
```

### 3b. `test_replay_eval_corrupt.py` — mismatch detection (4/4)

```
$ python -m pytest P:/.claude/hooks/evals/test_replay_eval_corrupt.py -v
collected 4 items

evals/test_replay_eval_corrupt.py::test_baseline_green PASSED            [ 25%]
evals/test_replay_eval_corrupt.py::test_corrupt_assistant_text_detected PASSED [ 50%]
evals/test_replay_eval_corrupt.py::test_corrupt_response_hash_detected PASSED [ 75%]
evals/test_replay_eval_corrupt.py::test_corrupt_live_expected_detected PASSED [100%]

============================== 4 passed in 0.23s ==============================
```

Three corruption modes each detected (run() returns 1 with the matching FAIL
marker in output): assistant_text tamper → STRUCTURAL FAIL; response_hash
tamper → STRUCTURAL FAIL; live_expected_issue_types flip → LIVE FAIL.

---

## 4. Unresolved items

- **#906 (auto-commit hook)**: Phase 1 work was NOT auto-committed (whole
  `evals/` dir remains untracked: `?? .claude/hooks/evals/`). No new SHA to
  record this phase. The Phase 0.5 plan-edit sweep recorded earlier is
  `2a4f156` (per the pre-compaction directive). Tracked under task #1256.
- **e1960aff dead reference**: plan named it the lazy_workaround
  self-referential-FP fixture, but `stop_blocks.jsonl` has 0 rows for this
  session (any prefix). Fix #1214 removed the producing code path; historical
  blocks rotated out of the log. The only `self_referen` rows that exist are
  the `unverified_stance` gate (72769f32, a07ff025) — a different behavior
  class. Shipped as `misses.jsonl` seed rather than substituting a different
  class (Rule 7 + the plan's own gap mechanism). 4 fixtures shipped, not 5.
- **3 DRIFT findings (4897f5bd, all turns)**: post-#1215 downgrades of the
  epistemic_contract gate (block→allow/warn). This is the program working as
  designed — drift surfaced, not asserted against. Phase 6 yield review will
  decide whether these are intentional tuning or regression.
- **Dead `has_live` var** in `replay_eval.py:108-110`: computed but unused (the
  denominator `live_ok + live_fail` already encodes it). Harmless; left to keep
  the summary line honest. Remove if touched again.
- **Phase 1.5 (clean-text entry points for the 3 structural-only gates)**:
  deletion_verification / perf_attribution / unverified_stance all need
  tool_events + filesystem/git state, not text alone. Their fixtures pin
  provenance structurally today; live replay deferred.

---

## 5. Gate criteria satisfied (plan Phase 1 verify bar)

- ✅ `evals/gold/` fixtures built (excerpt, expected behavior_type classes,
  earliest-cause turn, disallowed conclusions, expected destination) — 4 real
  gate-block transcripts, not imported chat
- ✅ `replay_eval.py` mirrors `judge_eval.py` holdout discipline: single-source
  live import (no hand-copied prompt), small-N, BLOCK cases read back first as
  liveness control
- ✅ Green on expected (STRUCTURAL 6/6, LIVE 3/3)
- ✅ Corrupt-one-fixture test shows mismatch detection (4/4, three modes)

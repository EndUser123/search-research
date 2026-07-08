# Phase 3 Evidence Packet — External-Fact Detector (SHADOW)

**Program:** Close-the-Loop telemetry reliability (6 phases)
**Phase:** 3a (predicate + offline calibration) DONE 2026-07-07;
**Phase:** 3b (integration + evidence join + live SHADOW + re-calibration) DONE 2026-07-07
**Date:** 2026-07-07
**Status:** 3a DELIVERED as **SHADOW / advisory** (non-blocking); 3b DELIVERED — predicate integrated, evidence join live, emitter wired.
**Auth context:** All checks ran against the gold replay corpus at `P:/.data/evals/`.

---

## 0. Phase 3b — Integration + Evidence Join + Live SHADOW (DONE 2026-07-07)

3a (§1–§8 below) shipped only the standalone predicate + offline calibration.
3b closes the gap by making the predicate the single source, gating which
detections become verdicts, and turning offline calibration into runtime
telemetry.

### 0.1 Single source (no drift)

- Predicate moved into `P:/.claude/hooks/verification/claims.py`:
  `_detect_external_fact_claims`, `EXTERNAL_FACT` in `_CLASSIFICATION_MAP`,
  `extract_claims` extended.
- `P:/.data/evals/external_fact_detector.py` is now a thin re-export
  (`from verification.claims import detect, PATTERNS, ...`).
- Anti_sycophancy `hypothesis_as_fact_detector` import made optional
  (`_HAS_HYPOTHESIS_DETECTOR` flag, try/except). The source file is missing
  (only `.pyc` exists) — pre-existing breakage, fixed in-scope so the live
  emitter doesn't fail-open silently forever.

### 0.2 Evidence join (`verification/engine.py`)

- `_verify_external_fact_claim(claim, events)`:
  - SUPPORTED if a WebSearch / WebFetch / `mcp__*api*` event's output mentions
    a claim target;
  - else SUPPORTED if an unexpired runtime-ground-truth row matches;
  - else SILENT.
- Stale detection is date-based (a past YYYY-MM in `expiry_trigger`); event-
  based triggers are treated as fresh.
- Wired in `match_claim_to_events` BEFORE the path-oriented target pre-filter
  (WebSearch events have no path target and would otherwise be filtered out).

### 0.3 Live SHADOW emitter (`Stop.py`)

- `_run_external_fact_shadow(data)` appends one row per SILENT EXTERNAL_FACT
  verdict to `logs/diagnostics/external_fact_shadow.jsonl` via
  `append_jsonl_safe`. Non-blocking, no stderr, no additionalContext; gated
  by `EXTERNAL_FACT_SHADOW_ENABLED` (default true); fail-open. Called from
  `main()` after the gate sweep.
- Smoke test: synthetic ungrounded response → 2 rows landed
  (`numpy 2.1`, `React 19 supports`), Stop exit 0 (no block).
- Bug caught in smoke: the emitter initially passed `str(log_path)` to
  `append_jsonl_safe`, but `append_jsonl` does `log_path.parent.mkdir(...)`
  (requires `Path`). The `except Exception: return` swallowed the
  `AttributeError` — the "returned clean" with no row written. Fixed: pass
  `log_path` directly. Other call sites already use the Path form.

### 0.4 Re-calibration through the integrated path

```
[shadow] corpus hits: {'gold': 1}
[shadow] seed eval: {'seed_cases': 12, 'tp': 4, 'fp': 0, 'fn': 1,
                     'precision': 1.0, 'recall': 0.8}
```
Numbers identical to 3a — the move + evidence join did not change detection
shape. Test gates:
- `test_external_fact_detector.py` → 13/13 PASS (shape unchanged).
- `test_external_fact_evidence_join.py` → 3/3 PASS (SILENT no grounding;
  SUPPORTED with WebSearch; STALE never SUPPORTS — anti-mock, real
  `extract_claims`+`build_verdicts`).
- `tests/test_verification_engine.py` → 29 passed, 1 skipped (no regression
  in ABSENCE/RULE/OUTCOME_ATTRIBUTION/FOLDER_CREATE verdicts).

### 0.5 Promotion criteria unchanged

3b stays SHADOW. The corpus has 0 known real TPs (external-fact claims are a
false-negative surface). Promotion to blocking still requires Phase 6
real-corpus TP reseeding + the lone FN fix + `measured_tp_on_corpus` re-stamped
with real numbers (§5 below).

### 0.6 Plan deviation logged

Phase 3 was initially marked "DELIVERED" when only 3a had landed. Staging
3a-then-3b was reasonable, but shipping staged work under DELIVERED without
reporting the fork is the same bounded-branch deviation class as the
renderer-cap omission (`misses.jsonl` row 2). Corrective action: plan +
packet split into 3a/3b; deviation row
`phase_3a_shipped_as_phase_3_under_delivered_20260707` appended to
`P:/.data/evals/misses.jsonl`.

---

## 1. Phase 3a deliverables (predicate + offline calibration)

## 1. Deliverables

| Artifact | Path | Purpose |
|----------|------|---------|
| Detector (pure-text predicate) | `P:/.data/evals/external_fact_detector.py` | Zero-IO, zero-model classifier for external-world claims |
| SHADOW runner | `P:/.data/evals/shadow_eval.py` | Non-blocking JSONL emitter; scans gold + `stop_blocks.jsonl` + seed |
| Labeled seed | `P:/.data/evals/external_fact_seed_cases.jsonl` | 12 hand-authored cases (5 TP, 7 FP guards) |
| Pytest suite | `P:/.data/evals/test_external_fact_detector.py` | 13 tests: 4 TP shapes, 7 FP guards, 1 invariant, 1 SHADOW smoke |
| Generated hits | `P:/.data/evals/shadow_hits.jsonl` | Per-match rows from the SHADOW run |
| Generated summary | `P:/.data/evals/shadow_summary.txt` | Counts + measured_tp_on_corpus line |

This phase addresses **task #1127** (the external-world-fact gap distinct from
`claim_classifier.external_fact`, which covers claims about the agent's OWN
code). The detector is a pure-text predicate — no IO, no model calls — so it is
unit-testable in isolation and trivially cloneable into a Stop gate in Phase 5.

## 2. Design — what the detector flags

`ExternalFactKind = {version_assertion, api_behavior_claim, entity_existence, ecosystem_fact}`.

| Kind | Canonical shape | Example |
|------|-----------------|---------|
| `version_assertion` | `<name> (version )?<dotted/v>` or `<dotted/v> of <name>` | "numpy 2.1", "v2.3 of the framework" |
| `api_behavior_claim` | `<CapName> [bare-major] (supports\|requires\|exposes\|provides\|ships with)`, lowercase requires dotted/v; plus `X's API …` | "React 19 supports", "Tailwind v4 requires" |
| `entity_existence` | `<name> (was\|is) (released\|deprecated\|announced\|launched)`, `new <name> (framework\|library\|package)`, `the latest <name>` | "new Deno framework" |
| `ecosystem_fact` | `(npm\|pip\|cargo) install <name>`, `<name> (package\|crate\|module) (is\|does\|has)` | "npm install axios" |

**Two name classes** (the precision lever): `_CAP_NAME` allows a bare-major
version ONLY inside `api_behavior_claim`, where the trailing verb
("supports") disambiguates. `_LOW_NAME` requires a dotted/v version. This
split exists because the dominant FP shape on real prose is
`<Capitalized-English-word> <bare-integer>` — "Phase 2", "Found 6", "Deleted 3",
"All 5" — which a single-name-class regex cannot distinguish from "React 19".

**Exclusions:** HEDGE (`might`/`could`/`likely`, unless a firm assertive verb
also appears), OWN_CODE (`the fix`/`all tests`/`this hook`, unless an external
entity outside the repo is also named), `_REPO_PATH`-shaped spans, and spans
whose every alphabetic token is in `_GENERIC_WORDS`.

## 3. Calibration — raw output

### 3.1 Pytest (13/13 PASS)

```
test_external_fact_detector.py::test_tp_library_plus_api_behavior PASSED
test_external_fact_detector.py::test_tp_versioned_deprecation      PASSED
test_external_fact_detector.py::test_version_of                    PASSED
test_external_fact_detector.py::test_versioned_dependency_requirement PASSED
test_external_fact_detector.py::test_fp_phase_n_not_a_version      PASSED
test_external_fact_detector.py::test_fp_found_n_not_a_version      PASSED
test_external_fact_detector.py::test_fp_deleted_n_not_a_version    PASSED
test_external_fact_detector.py::test_fp_claim_requires_not_api_behavior PASSED
test_external_fact_detector.py::test_fp_own_code_claim             PASSED
test_external_fact_detector.py::test_fp_hedged_hypothetical        PASSED
test_external_fact_detector.py::test_fp_repo_path                  PASSED
test_external_fact_detector.py::test_names_only_generic_filter     PASSED
test_external_fact_detector.py::test_shadow_eval_runs_and_emits_jsonl PASSED
============================= 13 passed in 0.19s ==============================
```

### 3.2 SHADOW corpus + seed eval

```
[shadow] corpus hits: {'gold': 1}
[shadow] seed eval: {'seed_cases': 12, 'tp': 4, 'fp': 0, 'fn': 1,
                     'precision': 1.0, 'recall': 0.8}
[shadow] measured_tp_on_corpus: precision=1.0 recall=0.8 (tp=4 fp=0 fn=1 n=12)
        — SYNTHETIC seed, not held-out; real-transcript TP reseeding deferred to Phase 6
```

### 3.3 FP-reduction trajectory (stop_blocks.jsonl)

| Calibration round | Change | stop_blocks FP | Seed precision |
|-------------------|--------|----------------|----------------|
| 0 (naive) | single name-class, bare-major everywhere | 171 | 0.625 |
| 1 | split `_CAP_NAME`/`_LOW_NAME`; lowercase requires dotted/v | 90 | 0.875 |
| 2 | `version_assertion` requires `_VERSION_FULL` for ALL names | 14 | 1.0 |
| 3 | `_GENERIC_WORDS` denylist + `_names_only_generic` post-filter | 0 | 1.0 |
| 4 (final) | api_behavior verbs folded into `_GENERIC_WORDS` | 0 | 1.0 |

Round 4 fixes the "claim requires" FP (14× in stop_blocks): the verbs
(`supports`/`requires`/`exposes`/…) are present in every `api_behavior_claim`
span, so listing them in `_GENERIC_WORDS` makes the `all()` check meaningful —
"claim requires" filters (both generic) while "React requires" survives (React
non-generic).

## 4. measured_tp_on_corpus

```
precision = 1.0   (0 FP on 247 stop_blocks rows + 7 seed FP guards)
recall    = 0.8   (4/5 seed TPs; 1 FN: "The latest Deno release ships with built-in Node compat.")
gold      = 1 hit (GSM8K 51.7 — defensible benchmark citation in fixture 0f183615)
stop_blocks = 0 hits
```

**Per the CLAUDE.md gate-discrimination rule** ("a gate that fires 0 real
positives stays advisory"), this detector ships as **SHADOW — observe + log,
never block**. The corpus at `P:/.data/evals/` provides FP measurement (real
assistant prose to NOT flag), not TP signal, because external-fact claims are
a **false-negative surface**: they were never caught by any existing gate, so
they are absent from `stop_blocks.jsonl`. Zero real TPs in the corpus is itself
a valid Phase 3 outcome — it is the discrimination evidence the rule requires
before any future promotion to blocking.

The seed is SYNTHETIC (hand-authored), not held-out. Real-transcript TP
reseeding is deferred to Phase 6 (yield review), per the rule's intent that
blocking promotion requires real-corpus signal.

## 5. Gate criteria (promotion to blocking — Phase 5+)

The detector MAY be cloned into a Stop gate only after ALL hold:

1. **Real-corpus TP reseeding** (Phase 6): re-run SHADOW against fresh
   transcripts; confirm ≥5 real external-fact claims surfaced and were
   adjudicated as true positives by hand review.
2. **FN fix on the entity-noun+verb shape** (see §6): the lone FN ("The latest
   Deno release ships with…") is a real recall gap, not a seed artifact.
3. **`measured_tp_on_corpus` re-stamped** with the real-corpus numbers, not the
   synthetic-seed numbers in this packet.
4. **Stop-payload integration check**: confirm the gate reads
   `transcript_path` (not `data["tool_events"]`, per memory
   `stop_payload_no_tool_events`).

Until then the detector stays advisory. Promoting it on synthetic-seed
precision alone would violate the rule.

## 6. Unresolved items

- **`tp_entity_existence` recall gap (the lone FN).** "The latest Deno release
  ships with built-in Node compat." does not fire. Diagnosis: no current
  pattern covers `<CapName> <release/framework/library> <ships/exposes/…>` —
  the noun ("release") sits between the name and the verb, defeating
  `api_behavior_claim`, and `entity_existence`'s `the latest <name>` requires
  the name immediately after "latest". A targeted pattern
  (`r"\b({_CAP_NAME})\s+(?:release|framework|library|package)\s+(?:ships\s+with|exposes|provides|requires|supports)\b"`)
  would close it. **Not added this phase** to avoid over-tuning against a
  seed I authored myself (per `feedback_gate_discrimination_rule`:
  synthetic seed is not independent verification). Acceptable for SHADOW;
  mandatory before any blocking promotion.
- **No router injection (this phase is detector-only).** Phase 2's router
  forwarding branch (plan `snazzy-tickling-waterfall.md`) carries the
  runtime-ground-truth injection stream; the external-fact detector does NOT
  inject at SessionStart — it is a Stop-side classifier, not an injector.
  Wiring into a Stop gate is Phase 5.
- **Phase 1.5 still open** (3 `tool_events` gates, `e1960aff` resolution) —
  tracked separately; not in Phase 3 scope.
- **Task #1284** (14 pre-existing `test_session_hooks.py` failures) — owner
  assigned, deferred; not in Phase 3 scope.

## 7. What was skipped (ponytail)

- No Stop-gate wiring (Phase 5 deliverable, not Phase 3).
- No `_GENERIC_WORDS` expansion beyond the stop_blocks-derived set — the
  denylist is empirical (every word traces to a real FP shape), not
  speculative. Add words only when a real FP appears.
- No LLM-judge layer on the detector output. The pure-text predicate is the
  whole detector; a judge would re-introduce the cost/latency the corpus
  signal doesn't yet justify.

## 8. Side-effect restoration (Phase 2 carryover, recorded here for continuity)

Not applicable to Phase 3. Phase 2's router-forwarding branch restores the
TDD-resume banner (`aca_session_verification_cleanup.py:400–404`) that the
prior router discarded; that restoration is recorded in the Phase 2 packet.

---
title: "Durable /check receipt lifecycle — manifest + mechanical derivation + close detection"
created: 2026-07-30
source: session-019fb04d (improvement-system audit + architectural correction)
tags: [check-receipt, lifecycle, manifest, finalizer, close-detection, verification, durable-evidence, broken-edge]
summary: >
  The /check receipt (check-state.md) was written by the orchestrator LLM,
  not a script — only ~3 of ~24+ runs produced one. A /check FAIL without
  the receipt was invisible to /close. The fix is a three-stage lifecycle:
  (1) start_run writes a session-bound manifest (check-run.json) at /check
  init, (2) write_verifier_result writes structured per-verifier JSON after
  each verifier returns, (3) finalize_run DERIVES the verdict mechanically
  from those results and writes the receipt atomically. /close now scans
  both check-state.md AND check-run.json, detecting RUNNING, INCOMPLETE,
  and FINALIZE_FAILED runs as needs_attention.
cognitive_load: 3
verification: local-only
host: grok
agent: grok
sources:
  - "P:/docs/improvement-system-audit-20260729.md §6 broken-edge #1, §9 Intervention 1"
relations:
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: refines
  - target: wiki/concepts/verification-receipt-systems-design-landscape.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Durable /check receipt lifecycle

## Decision context

**The problem:** `/close`'s verify gate reads `check-state.md` via regex to detect whether `/check` ran and what it found (close_accounting.py:530-587). But `check-state.md` was written by the parent LLM — no script in `check/__lib/` produced it. An audit (2026-07-29) found that only ~3 of ~24+ `/check` runs had a receipt. A `/check FAIL` without the receipt was silently invisible to `/close` — the session could be declared closed while a known verification failure sat unrecorded.

**The architectural defect:** the receipt existed, the consumer existed, but the producer was memory-dependent. The LLM had to remember to write the receipt in the exact format the consumer's regex expected. Under closure pressure, it often didn't.

**What was needed:** make the producer mechanical, and make every initialized run durable — even if the receipt write fails, even if the run is interrupted, even if no verifiers return.

## The design: three-stage lifecycle

```
START → verifier results → FINALIZE
```

### Stage 1: `start_run(session_id, run_dir)` — manifest creation

Called immediately after `$runDir` creation (SKILL.md Step 0.1). Writes `check-run.json` atomically:

```json
{"status": "RUNNING", "session_id": "<authoritative>", "started_at": "<UTC>"}
```

This is the lifecycle entry point. If this manifest exists after a `/check` run but no receipt does, `/close` detects it as an incomplete run. **No initialized run can disappear.**

### Stage 2: `write_verifier_result(run_dir, index, concern, verdict, issues)`

Called after each verifier subagent returns. Writes a structured JSON result the finalizer can read and validate. The orchestrator extracts the verdict from the verifier's output (validated by `output_validator.validate_verifier_output`) and writes it here — separating judgment (LLM) from persistence (code).

### Stage 3: `finalize_run(run_dir)` — mechanical verdict derivation

Called on EVERY terminal path. Reads the manifest + all verifier result files, DERIVES the verdict, and:

- **All PASS** → writes `check-state.md` with `CHECK PASS (N/N verifiers)`, manifest → COMPLETE
- **Any FAIL** → writes `check-state.md` with `CHECK FAIL (M/N verifiers)`, manifest → COMPLETE
- **No results** → no receipt, manifest → INCOMPLETE (with failure reason)
- **Receipt write fails** → manifest → FINALIZE_FAILED

The finalizer **never trusts an aggregate LLM-supplied verdict**. It derives PASS/FAIL/INCOMPLETE from the per-verifier result files. A contradictory input (supplied "PASS" + a failing verifier) produces a derived FAIL.

## Why the manifest is necessary (not just the receipt)

The receipt (`check-state.md`) is only written when finalization succeeds with PASS or FAIL. But the cases that need detection most are the failure cases:

| Failure case | Without manifest | With manifest |
|---|---|---|
| Run interrupted (never finalized) | invisible — no evidence exists | RUNNING manifest detected by `/close` |
| Receipt write fails (disk full, lock) | invisible — no receipt | FINALIZE_FAILED manifest detected |
| No verifiers returned (INCOMPLETE) | invisible — no receipt | INCOMPLETE manifest detected |
| All verifiers PASS | receipt written ✓ | receipt written + manifest COMPLETE ✓ |

The manifest is the **lifecycle record**; the receipt is the **consumer artifact derived from it**. They serve different purposes and must both exist.

## /close detection rules

`close_accounting.py:scan_check_receipts()` now scans both `check-state.md` (existing) AND `check-run.json` (new):

| Manifest state | Receipt state | /close verify gate |
|---|---|---|
| COMPLETE + valid receipt | parseable | consume PASS/FAIL normally |
| RUNNING | absent | needs_attention |
| INCOMPLETE | absent | needs_attention |
| FINALIZE_FAILED | absent | needs_attention |
| COMPLETE + missing receipt | absent | needs_attention (INCONSISTENT) |
| Malformed manifest | n/a | visible degraded state (MALFORMED) |
| Other session | n/a | ignored |
| No manifest + legacy receipt | parseable | existing behavior preserved |

## What is still LLM-dependent

The lifecycle calls (`check_lifecycle.py start/verifier-result/finalize`) are prompt-layer invocations — the orchestrator LLM must call them as instructed in SKILL.md. There is no code-level hook that fires them independent of LLM memory. The SKILL.md enumerates 7 terminal paths that must call finalization, but enforcement depends on the LLM following the instructions.

Reaching full `CHECK_RECEIPT_LOOP_PROVEN` requires either (a) a SessionEnd hook that calls `finalize_run` unconditionally, or (b) production evidence that the LLM reliably calls the lifecycle steps across 5+ real runs.

## What this means for our workspace

The verify gate in `/close` is now trustworthy: a `/check FAIL` cannot be invisible. Even if the receipt write fails, the manifest records the failure, and `/close` blocks a clean close. This closes the single highest-impact broken edge identified in the improvement-system audit.

This is the same principle as [[mechanical-enforcement-over-behavioral-reminder]] — a prompt instruction ("remember to write the receipt") has a ~12% compliance ceiling (3 of 24+ runs); a script invocation has 100% compliance once invoked. The manifest-at-start pattern is the structural fix that makes the lifecycle durable even when the LLM forgets to finalize.

The design pattern (manifest-at-start + mechanical-finalizer + consumer-scans-both) is transferable to any producer→consumer edge where the producer is LLM-dependent. The manifest makes the run's existence durable; the finalizer makes the outcome durable. This directly addresses the broken-edge class documented in [[close-scanner-verification-gap-stale-read]] — the prior concept identified that `/close` couldn't see `/check` results; this one provides the mechanical fix.

The finalizer's derive-verdict logic also connects to [[verification-receipt-systems-design-landscape]] — the receipt is authoritative because `/check` produced it, and the finalizer guarantees the receipt cannot contradict the verifier evidence. A supplied "PASS" with a failing verifier produces a derived "FAIL" receipt, not a contradictory one.

Related: [[trust-over-believability]] — the system trusts the derived verdict over the LLM-supplied aggregate because the derivation is mechanically grounded in per-verifier result files.

## Falsifier

This lifecycle is insufficient if:
- The LLM skips `start_run` (no manifest → run invisible from the start)
- A SessionEnd hook doesn't guarantee finalization (RUNNING manifests accumulate)
- The manifest scan in `/close` has a regex bug that misses manifests

The first two are the production-validation gap (5 real runs needed to confirm LLM compliance). The third is testable now (covered by test_check_close_integration.py).

## Receipts

- `P:/.grok/skills/check/__lib/check_lifecycle.py` — the lifecycle module (start_run, write_verifier_result, finalize_run, derive_verdict)
- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:582-632` — manifest scan in scan_check_receipts()
- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:2249-2262` — verify gate condition for incomplete_runs
- `P:/.grok/skills/check/SKILL.md` Step 0.1 (manifest), Step 4 (verifier results), Step 4.5 (finalizer with 7 terminal paths)
- `P:/.grok/skills/check/tests/test_check_close_integration.py` — 12 tests covering all close-detection scenarios
- `P:/.grok/skills/check/tests/test_check_lifecycle.py` — 28 lifecycle tests
- `P:/docs/improvement-system-audit-20260729.md` — audit that identified the gap

---
title: "Verifier false-confidence: receipts claiming success when the verifier never ran"
created: 2026-08-01
source: session-019f9a89 (/capture sweep, FMEA pass)
agent: grok
host: grok
cognitive_load: 3
verification: single-incident-verified
tags: [verification, receipt, false-confidence, fail-open, hook, posttooluse, structural-fix, receipt-system]
summary: >
  A near-miss failure mode where a verifier catches a tool-not-found
  exception, returns (True, "") as if the check passed, and the receipt
  system writes a VERIFICATION_SUCCEEDED receipt. The Stop hook then
  accepts the receipt as proof that verification ran. This is structurally
  WORSE than fail-open (A1 in [[hook-failure-mode-taxonomy]]) because it
  actively misrepresents state instead of just passing silently — the
  receipt records an exit_status of 0 and empty output when no verification
  actually occurred. Distinguishing from [[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]]
  (inverse direction: rejected vs false success) and [[cli-api-drift-in-skill-scripts]]
  (silent skip on non-zero exit vs active false-success on absent tool).
relations:
  - target: wiki/concepts/hook-failure-mode-taxonomy.md
    type: extends
    note: "Adds an A-class failure mode: fail-open + active receipt"
  - target: wiki/concepts/phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope.md
    type: complements
    note: "Inverse direction — receipts silently rejected vs receipts actively lying"
  - target: wiki/concepts/cli-api-drift-in-skill-scripts.md
    type: related
    note: "Sibling pattern: subprocess returns non-zero, treated as 'no results'"
  - target: wiki/concepts/posttooluse-auto-verify-eliminates-stop-hook-stale-receipt-blocks.md
    type: applies
    note: "The PostToolUse_auto_verify.py run_ruff() instance lives inside this concept"
  - target: wiki/concepts/verification-receipt-systems-design-landscape.md
    type: related
    note: "Receipt system must distinguish VERIFICATION_SUCCEEDED from VERIFICATION_SKIPPED"
  - target: wiki/concepts/check-receipt-lifecycle-manifest-and-mechanical-derivation.md
    type: related
    note: "Receipt truthfulness is a precondition for mechanical derivation"
---

# Verifier false-confidence: receipts claiming success when the verifier never ran

## The pattern

A verifier function (commonly a `subprocess.run(...)` wrapper inside a
PostToolUse or PreToolUse hook) calls an external tool. The tool is not
installed (`FileNotFoundError`) or fails to spawn. The verifier catches
the exception and returns `(True, "")` — pretending the check passed with
no errors. The calling hook then writes a `VERIFICATION_SUCCEEDED` receipt
with `actual_exit_status: 0` and an empty error string. The Stop hook
later accepts that receipt as proof of verification.

```python
# P:/Users/brsth/.grok/hooks/PostToolUse_auto_verify.py:98-111
def run_ruff(file_path: str) -> tuple[bool, str]:
    """Run ruff check on the file. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # If ruff isn't available, don't block — just skip
        return True, ""   # ← LIES. Receipt will record exit_status=0, no errors.
```

## Why this is worse than fail-open

[[hook-failure-mode-taxonomy]] A1 (fail-open masks bugs) describes the
baseline problem: a broken hook produces silent pass-through. The verifier
false-confidence pattern is the *escalation* of A1 — when the verifier
function explicitly returns success on a missing tool, the hook doesn't
just pass through silently, it **writes evidence that the verification
occurred**. Downstream consumers (Stop hook, close gates, `/check`
finalizer) trust that evidence and clear obligations against it.

| Failure mode | Hook behavior | Receipt written | Downstream trust |
|--------------|---------------|-----------------|------------------|
| **A1 fail-open** | Hook crashes, no receipt | None | Tool call proceeds, no false confidence |
| **A5 silent bypass** | Hook exits 0 with no output | None (or with `evidence_state: UNBOUND`) | Tool call proceeds |
| **Phase 2 format mismatch** | Receipt format wrong | Rejected by Stop hook | Obligation persists |
| **CLI drift (silent skip)** | Subprocess returns non-zero, treated as no results | May write a receipt with `result_ref: "skipped"` | Operator sees skip message |
| **Verifier false-confidence** | Verifier returns `(True, "")` on `FileNotFoundError` | `VERIFICATION_SUCCEEDED` with `actual_exit_status: 0` | **Stop hook clears obligation; verification is logged as having run** |

The last row is the structural problem: the receipt record is
*indistinguishable* from a receipt produced when ruff actually ran and
found zero issues. The Stop hook cannot distinguish "ruff ran and passed"
from "ruff was never installed."

## The reference instance (2026-08-01)

`~/.grok/hooks/PostToolUse_auto_verify.py` lines 98-111:
- `run_ruff()` catches `FileNotFoundError` and returns `(True, "")`.
- Hook caller (line 164) writes `auto-verify-ruff-check-<session>-<file>.json`
  with `actual_exit_status: 0`, `evidence_state: BOUND`.
- Stop hook (`~/.grok/hooks/quality_gate.py`) reads the receipt and clears
  the obligation for that file's coverage.
- Net effect: if `ruff` is not on PATH (e.g., on a fresh machine, after
  PATH corruption, or in a CI environment without ruff), every edit
  silently ships without lint verification.

The companion `run_py_compile()` at lines 114-135 has the same shape but
uses `ast.parse` via subprocess — if Python itself is missing the file
won't be reachable either, so the same `FileNotFoundError` failure
applies. Same fix.

## Other instances (likely)

The same anti-pattern is likely to recur wherever:
1. A PostToolUse/PreToolUse hook wraps a CLI tool (`ruff`, `pylint`,
   `pyright`, `mypy`, `semgrep`, custom validators).
2. The wrapper is written with the priority "don't block edits" rather
   than "truthful verification state."
3. The hook then writes a `VERIFICATION_SUCCEEDED` receipt without
   distinguishing "ran and passed" from "didn't run."

Audit candidates:
- `~/.grok/hooks/scripts/*.py` — grep for `return True, ""` patterns
  in verifier wrappers.
- Any hook using `try: subprocess.run(...) except FileNotFoundError:
  return success`.

## The structural fix

### 1. Add a distinct receipt type: `VERIFICATION_SKIPPED`

Receipts should distinguish three terminal states:
- `VERIFICATION_SUCCEEDED` — verifier ran, exit 0, no findings
- `VERIFICATION_FAILED` — verifier ran, non-zero exit, findings present
- `VERIFICATION_SKIPPED` — verifier did not run (tool absent, timeout,
  parse error)

The Stop hook obligation gate accepts `SUCCEEDED` to clear; `SKIPPED`
keeps the obligation pending so the operator must run verification
manually or install the missing tool.

```python
# Replacement for run_ruff
def run_ruff(file_path: str) -> tuple[str, str]:
    """Returns (status, output) where status ∈ {SUCCEEDED, FAILED, SKIPPED}."""
    try:
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return "SUCCEEDED", ""
        return "FAILED", result.stdout + result.stderr
    except FileNotFoundError:
        return "SKIPPED", "ruff binary not on PATH"
    except subprocess.TimeoutExpired:
        return "SKIPPED", "ruff timed out after 10s"
    except Exception as e:
        return "SKIPPED", f"ruff invocation error: {e}"
```

The hook caller writes `record_type: VERIFICATION_SKIPPED` with
`actual_exit_status: -1` and the skip reason in `result_ref`. Stop hook
sees `SKIPPED`, keeps obligation pending, surfaces "ruff not available"
to operator via stderr.

### 2. Path preflight at session start (companion fix)

Add a SessionStart hook that checks for required verifiers on PATH
(`ruff`, `python`, `git`, `qmd`) and warns the operator immediately if
any are missing. This makes the absence visible at session boundary
rather than only when an edit happens.

### 3. Verifier wrapper convention (document in skill authoring)

Skill authoring convention: every verifier wrapper returns a 3-state
enum, never a boolean. Document in `~/.grok/skills/<skill>/SKILL.md`
templates.

## What this means for our workspace

- **Audit existing verifier hooks** — grep `~/.grok/hooks/` and
  `~/.grok/hooks/scripts/` for `return True, ""` in subprocess wrappers.
  Fix each instance.
- **Update the `PostToolUse_auto_verify.py` receipt schema** to use the
  3-state enum (companion fix; tracked as a handoff, not a wiki change).
- **Add the 3-state receipt type to `verification_receipt_writer.py`**
  and the Stop hook obligation gate.
- **Document the convention** in `~/.grok/skills/` skill-authoring
  templates so future hooks don't reproduce the anti-pattern.

## Falsifier

This pattern is wrong if:
- A `VERIFICATION_SKIPPED` receipt type already exists in the schema
  and is honored by the Stop hook (in which case the bug is fixed and
  this concept is a historical record).
- The fail-open return is acceptable because no downstream consumer
  trusts the receipt — confirmed by reading the Stop hook code path
  and showing it ignores receipt `actual_exit_status` when verifying
  obligations. (In that case the receipt is advisory, not authoritative.)
- `ruff` is guaranteed on PATH in every workspace context (verified by
  reading the bootstrap script — currently no such guarantee exists).

## Related

- [[hook-failure-mode-taxonomy]] — A1 fail-open, A5 silent bypass (the
  baseline; this concept is the escalation).
- [[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]] —
  inverse direction (rejected vs false success).
- [[cli-api-drift-in-skill-scripts]] — sibling: silent skip on non-zero
  exit; this concept covers silent skip on absent tool.
- [[verification-receipt-systems-design-landscape]] — the broader
  receipt system design.
- [[check-receipt-lifecycle-manifest-and-mechanical-derivation]] —
  receipt truthfulness is a precondition for mechanical derivation.
- [[best-practices-enforcement-mechanism-grok-build]] — "actor-authored
  metadata" anti-pattern; this is the verifier-side equivalent.

## Receipts

- `~/.grok/hooks/PostToolUse_auto_verify.py:98-111` — the run_ruff
  false-confidence instance (lines read 2026-08-01).
- `~/.grok/hooks/PostToolUse_auto_verify.py:114-135` — run_py_compile
  has the same shape; same fix applies.
- Session 019f9a89 /capture FMEA pass: flagged as `[WARN] PostToolUse_auto_verify.py run_ruff() returns (True, '') when ruff is not found`.
---
thread_id: verifier-false-confidence-bug-20260802
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-08-02T15:35:00Z
last_updated_by: 019f9a89-d902-7930-ad3a-bab7e682830b
last_updated_at: 2026-08-02T15:35:00Z
status: open
handoff_type: investigation
accurate_as_of_head: e5575252251bf1ebdb4a1e549653e3c55463acdc
---

# Handoff: Fix verifier-false-confidence bug — PostToolUse_auto_verify.py returns success when tool is absent

## Objective

Fix the bug where `PostToolUse_auto_verify.py` returns `(True, "")` when ruff or py_compile is not found (`FileNotFoundError`), causing the receipt system to write `VERIFICATION_SUCCEEDED` receipts claiming verification ran when the verifier never executed. This is structurally worse than fail-open — it actively misrepresents state.

## Status

OPEN — design identified, implementation ready.

## Producing context

Produced 2026-08-02 by session 019f9a89. Discovered by close-check-2 /capture phase. Wiki concept written: `P:/.data/wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md`.

## Read-first list

1. `P:/.data/wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md` — the wiki concept documenting the pattern
2. `~/.grok/hooks/PostToolUse_auto_verify.py` — the buggy code (lines 98-111 for run_ruff, 114-135 for run_py_compile)
3. `~/.grok/hooks/scripts/quality_gate.py` — the Stop hook that consumes the receipts
4. `~/.grok/hooks/scripts/verification_receipt_writer.py` — the receipt writer

## Verified facts

- [FACT] `PostToolUse_auto_verify.py` line 98-111: `except (subprocess.TimeoutExpired, FileNotFoundError): return True, ""` — returns success on missing tool (source: close-check-2 /capture output)
- [FACT] Same pattern in `run_py_compile()` at lines 114-135 (source: same)
- [FACT] Receipt system writes `actual_exit_status: 0` and empty error string based on this return value (source: receipt writer behavior)
- [FACT] If ruff is absent (fresh PATH, CI environment), every .py edit silently ships without lint verification (source: wiki concept)

## Task packets

### VFC-01: Replace 2-state return with 3-state enum

- **Goal:** Change `run_ruff()` and `run_py_compile()` to return a 3-state result: `{SUCCEEDED, FAILED, SKIPPED}` instead of `(bool, str)`
- **In scope:** `~/.grok/hooks/PostToolUse_auto_verify.py` functions `run_ruff()` and `run_py_compile()`
- **Out of scope:** The receipt writer format (it should propagate the SKIPPED state, but changing the receipt format is a separate concern)
- **How:**
  1. Define an enum or constants: `VERIFIED = "succeeded"`, `FAILED = "failed"`, `SKIPPED = "skipped"`
  2. In `run_ruff()`: change `except FileNotFoundError: return True, ""` to `return "skipped", "ruff not found"`
  3. Same for `run_py_compile()`
  4. Update the caller to handle SKIPPED distinctly from SUCCEEDED
- **Acceptance:** When ruff is absent, the receipt says `SKIPPED` not `SUCCEEDED`; the Stop hook treats SKIPPED as "needs human verification"
- **Falsifier:** if the receipt format change breaks the Stop hook parser, the fix introduces a new failure mode
- **Verification level:** LIVE_BEHAVIOR — test with ruff absent (rename or PATH manipulation)

### VFC-02: Update receipt writer to propagate SKIPPED state

- **Goal:** The receipt writer should distinguish SUCCEEDED, FAILED, and SKIPPED in its output format
- **In scope:** `~/.grok/hooks/scripts/verification_receipt_writer.py`
- **Out of scope:** Stop hook consumption logic (VFC-03)
- **Acceptance:** Receipt JSON includes a `status` field with value `succeeded`, `failed`, or `skipped`

### VFC-03: Update Stop hook to treat SKIPPED as needs-verification

- **Goal:** When the Stop hook sees a SKIPPED receipt, it should not treat it as passing verification — it should prompt for manual verification
- **In scope:** `~/.grok/hooks/scripts/quality_gate.py`
- **Acceptance:** SKIPPED receipts trigger a "verification was skipped (tool absent) — verify manually" message, not a silent pass

## Open decisions

### D1: Should SKIPPED block (exit 2) or warn (exit 0 with message)?

- **Option A:** Block — treat as unverified, force manual check. Safer but adds friction.
- **Option B:** Warn — log the skip but don't block. Matches current fail-open posture for missing tools.
- **Selection criterion:** is the cost of a missed verification higher than the cost of friction?
- **Current lead:** B (warn) — consistent with the hook's advisory posture; blocking on missing ruff would break sessions without ruff installed
- **Evidence that would change this:** if an actual bug ships because SKIPPED was treated as pass

## Hard constraints

- Do NOT remove the `count_chrome_processes()` guard or any other downstream safety net
- Do NOT change the fail-open posture for parse errors (that's correct — a hook crash shouldn't block work)
- The fix must be backwards-compatible with existing receipt consumers

## Cross-reference couplings

- `~/.grok/hooks/PostToolUse_auto_verify.py` → writes receipts consumed by `quality_gate.py`
- `P:/.data/wiki/concepts/verifier-false-confidence-receipt-claims-success-when-tool-absent.md` → the wiki concept
- `P:/.data/wiki/concepts/hook-failure-mode-taxonomy.md` → A1 fail-open pattern; this bug is an escalation of A1

## Resumption protocol

1. Read the wiki concept for the full pattern analysis
2. Read `PostToolUse_auto_verify.py` lines 98-135
3. Implement VFC-01 (3-state return)
4. Implement VFC-02 (receipt writer propagation)
5. Implement VFC-03 (Stop hook handling)
6. Test with ruff absent

## Suggested next invocation

```
Pick up the verifier-false-confidence handoff at P:/docs/handoffs/verifier-false-confidence-bug-20260802/HANDOFF.md.
Fix run_ruff() and run_py_compile() to return SKIPPED instead of (True, "") on FileNotFoundError.
3 task packets, each S effort.
```

## Last user message (verbatim)

"/handoff" (auto-update mode — creating handoff for item 12 from the /tp unified list)

## Epistemic labels

- [FACT] Bug confirmed by close-check-2 /capture (receipt in wiki concept commit)
- [FACT] Both run_ruff() and run_py_compile() have the same pattern
- [INFERENCE] The 3-state enum is the correct fix (distinguishes "ran and passed" from "didn't run")

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T15:35 | 019f9a89... | created |

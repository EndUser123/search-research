---
title: "Stop hook false-positive loop: obligation nonce not propagated to verification receipts"
created: 2026-08-06
source: session-019fd8dc (/why on Stop hook loop)
tags: [hooks, stop-hook, quality-gate, false-positive, obligation, nonce, verification, bug-pattern]
summary: >
  The quality_gate.py Stop hook's continuation obligation system has a nonce
  gap: verification receipts from PostToolUse_auto_verify must carry the
  obligation's nonce to prove causal ordering, but the nonce propagation is
  unreliable. When the nonce doesn't match, the receipt is silently rejected
  (line 1129 continue) and the hook reports "NO_COVERING_RECEIPT" with a
  misleading "below the required capability" diagnostic. The actual failure
  is nonce mismatch, not verifier weakness. Agent then loops trying stronger
  verifiers, none of which help because the problem is receipt linkage, not
  capability. Root cause: the error message reports the final result without
  stating which of the 7 sequential checks actually failed.
agent: grok
host: grok
cognitive_load: 2
verification: source-inspected
relations:
  - target: wiki/concepts/self-verifying-mutations-verification-tools-modify-files.md
    type: related
  - target: wiki/concepts/grok-build-hook-exit-code-1-stderr-as-failure-signal.md
    type: related
---

# Stop hook false-positive loop: obligation nonce not propagated

## Decision context

**The problem:** after modifying 4 Python files (script_scan.py, wiki_index_builder.py,
wiki_context_injector.py, test_wiki_context_injector.py), the Stop hook blocked with
NO_COVERING_RECEIPT and created a continuation obligation. Over 5 subsequent turns,
the agent ran ruff check (static_analysis), pytest (unit_behavior, 12/12 pass),
and py_compile (syntax) against all files — all passing. The hook rejected every
receipt, reporting "below the required capability." The agent looped, unable to
satisfy the obligation. Only a session restart cleared it.

## Root cause chain

1. `_check_obligation_satisfied()` (quality_gate.py:1071) has 7 sequential checks
2. Every receipt failed at check #3: `obligation_nonce` match (line 1129)
3. The nonce check silently `continue`s — no diagnostic for nonce mismatch
4. The final return is `NO_COVERING_RECEIPT` with a capability diagnostic
5. The capability diagnostic says "below the required capability" — misleading
6. Agent interprets this as "need a stronger verifier" and loops

The actual failure: PostToolUse_auto_verify creates VERIFICATION_SUCCEEDED receipts
but doesn't reliably propagate the obligation's nonce to the receipt. Without the
matching nonce, the receipt is rejected regardless of capability.

## The misleading diagnostic

The hook builds a capability diagnostic (lines 997-1014) that lists found
capabilities and says "These are below the required capability." But this
diagnostic fires even when the actual failure is nonce mismatch — the receipts
are found (they exist in the list) but rejected at the nonce check before the
capability check is reached. The agent reads "need stronger verifier" when the
actual message should be "receipt not causally linked to obligation."

## Fix

**Error message fix (immediate):** `_check_obligation_satisfied` should return
WHICH check failed, not just the final result. Change the return signature to
include the failing check name:

```python
# Instead of:
return False, "NO_COVERING_RECEIPT", ""

# Return:
return False, "NO_COVERING_RECEIPT", "", "NONCE_MISMATCH"
# or
return False, "NO_COVERING_RECEIPT", "", "CAPABILITY_INSUFFICIENT"
```

Then the block message can say "Receipt rejected: nonce mismatch" instead of
the misleading "below the required capability."

**Nonce propagation fix (structural):** ensure PostToolUse_auto_verify reads the
current session's obligation file and propagates its nonce to the receipt. If the
obligation file exists but the nonce isn't being read, the linking is broken.

## Falsifier

This finding is wrong if the nonce WAS correctly propagated and the actual
failure was at a different check (e.g., scope_basis rejection at line 1149).
To verify: add logging to `_check_obligation_satisfied` that prints which check
failed for each receipt, then reproduce the loop.

## Receipts

- `~/.grok/hooks/scripts/quality_gate.py:1129` — nonce check (silent continue)
- `~/.grok/hooks/scripts/quality_gate.py:1071-1174` — full obligation check function
- `~/.grok/hooks/scripts/quality_gate.py:1094-1096` — CAP_HIERARCHY definition
- `~/.grok/hooks/PostToolUse_auto_verify.py:8` — exists to eliminate this loop
- Session 019fd8dc: 5-turn loop observed, cleared only by restart

---
title: "Phase 2 receipt format mismatch: Stop hook silently rejected CLAIMED_SCOPE receipts"
created: 2026-07-31
source: session-20260731
tags: [receipt-system, verification, stop-hook, phase-mismatch, false-positive, bug-fix]
summary: >
  The Stop hook's _is_valid_succeeded_receipt() required scope_type=="FILES"
  (Phase 1 format), but the PostToolUse receipt writer produces
  scope_type=="CLAIMED_SCOPE" (Phase 2 format). This meant every Phase 2
  receipt was silently rejected by the coverage check, making the entire
  receipt system non-functional in shadow mode. Additionally, the fingerprint
  comparison used scope_refs (claimed subset) instead of observed_state_refs
  (all modified files), causing mismatch when claimed scope was a subset of
  observed. Both bugs meant the Stop hook could never see valid receipts.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
sources:
  - C:/Users/brsth/.grok/hooks/scripts/quality_gate.py (Stop hook source)
  - C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py (receipt writer source)
relations:
  - target: wiki/concepts/stop-hook-scope-binding-fix-design-decisions.md
    type: complements — same receipt system, different bug class
  - target: wiki/concepts/hook-script-capability-derivation-receipt-loop-fix.md
    type: related — capability derivation in the same system
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related — format contract as mechanical enforcement
---

# Phase 2 receipt format mismatch: Stop hook silently rejected CLAIMED_SCOPE receipts

## Decision context

**Why this was investigated:** the operator reported being blocked by the Stop
hook despite running `ruff check` two turns before the block. The /tp review of
the shadow-mode fix (commit `42fc043`) identified three deeper issues: scan
window too narrow, receipt writer classification potentially broken, and no
regression test for obligation clearing. Investigation found that the receipt
writer classification was actually correct (`ruff → static_analysis`), but a
more fundamental bug made the entire receipt system non-functional: the consumer
(Stop hook) and producer (receipt writer) used incompatible format contracts.

## The three bugs

The receipt system has two phases: Phase 1 (scope_type `"FILES"`, simple
coverage) and Phase 2 (scope_type `"CLAIMED_SCOPE"`, separates observed from
claimed scope, adds capability classification and identity checks). The
[[stop-hook-scope-binding-fix-design-decisions]] concept documents the Phase 2
scope-binding design. But the consumer never accepted Phase 2 receipts.

This violates [[mechanical-enforcement-over-behavioral-reminder]]: the format
contract between producer and consumer was documented in code comments but
never mechanically verified. A contract test asserting producer/consumer format
agreement would have caught this on day one.

### Bug 1: scope_type format mismatch (the silent killer)

The receipt writer (`verification_receipt_writer.py`) produces Phase 2 receipts
with `scope_type: "CLAIMED_SCOPE"` (line 937: `"scope_type": "CLAIMED_SCOPE"
if claimed_scope else "OBSERVED_ONLY"`). But the Stop hook's
`_is_valid_succeeded_receipt()` (quality_gate.py) required
`r.get("scope_type") == "FILES"` — the Phase 1 format.

**Impact:** every Phase 2 receipt was silently rejected at the validation gate.
`_check_receipt_coverage()` never saw them, `receipt_reason` was always
`MISSING_RECEIPT`, and the shadow-mode receipt relief path never fired. The
entire receipt system — scope binding, capability classification, identity
checks — was dead code from the consumer's perspective.

**Receipt:** quality_gate.py line 471 (before fix):
`and r.get("scope_type") == "FILES"` — rejects `"CLAIMED_SCOPE"`.
verification_receipt_writer.py line 937 (producer):
`"scope_type": "CLAIMED_SCOPE" if claimed_scope else "OBSERVED_ONLY"`.

### Bug 2: fingerprint comparison used wrong field

The receipt writer fingerprints ALL modified files and stores the result in
`scope_fingerprint_at_execution`. The `scope_refs` field contains only the
claimed scope (which may be a subset of modified files). But the coverage
check compared fingerprints using `scope_refs` — guaranteeing a mismatch
whenever claimed scope ≠ modified files.

**Receipt:** quality_gate.py (before fix):
`current_fp = _compute_file_fingerprint(scope_refs)` — should use
`observed_state_refs` (all modified files the writer fingerprinted).

### Bug 3: scan window state not persisted across Stop fires

`verification_ran` and `code_modified_after_verification` reset to `False`
on every Stop hook invocation. The scan window only sees the current turn's
transcript delta. Verification from a prior turn is invisible, causing
false-positive blocks.

**Receipt:** quality_gate.py Step 6 (before fix):
`verification_ran = False` — initialized fresh each fire, not carried from
the state file.

## The fix

1. **Format compatibility:** accept `"FILES"`, `"CLAIMED_SCOPE"`, and
   `"VERIFICATION_SUCCEEDED_UNBOUND"` in `_is_valid_succeeded_receipt()`.
2. **Fingerprint field:** use `observed_state_refs` (fallback to `scope_refs`
   for Phase 1 receipts) for fingerprint comparison.
3. **Scan window persistence:** carry `verification_ran` and
   `code_modified_after_verification` in the state file across Stop fires.
4. **Shadow-mode receipt relief:** when the old gate would block in shadow
   mode but receipt coverage returns `VALID_RECEIPT_REUSE`, allow instead.

## What this means for our workspace

- **The receipt system is now functional in shadow mode.** Before this fix, it
  was dead code — every Phase 2 receipt was silently rejected. Now the Stop
  hook can use PostToolUse receipts to override false-positive blocks.
- **The scan window gap is bridged two ways:** state persistence ensures the
  old gate carries verification across turns, and receipt relief provides a
  second path when the old gate's window is still too narrow.
- **Future receipt format changes must update both producer and consumer.**
  The `_is_valid_succeeded_receipt()` function is the contract boundary. Any
  new scope_type value must be added to the accepted set in both the validator
  and the coverage check.
- **Test codification risk:** the existing test at
  `test_authoritative_receipts.py` line 244 codified the bug as intended
  behavior (`"Writer receipt is excluded from legacy shadow coverage"`). This
  masked the bug for weeks. Tests that codify integration boundaries must
  verify the boundary is intentional, not a format mismatch. This is the same
  pattern documented in [[fabricated-causal-chain-receipt-required]]: a
  plausible narrative ("Phase 2 receipts are excluded by design") was accepted
  without verifying the actual contract.

## Falsifier

If a future Phase 3 receipt format introduces another `scope_type` value, the
same silent-rejection pattern recurs unless `_is_valid_succeeded_receipt()` is
updated. The fix accepts a set of values, but the set is hardcoded — not
derived from the writer's output. A contract test that asserts "every
scope_type the writer can produce is accepted by the consumer" would falsify
this risk permanently. This connects to [[hook-script-capability-derivation-receipt-loop-fix]]
which documents a similar producer/consumer contract gap in the capability
derivation layer.

## Receipts

- `quality_gate.py:455-474` — `_is_valid_succeeded_receipt()` (fixed: accepts CLAIMED_SCOPE + UNBOUND)
- `quality_gate.py:563-570` — fingerprint comparison (fixed: uses observed_state_refs)
- `quality_gate.py:1145-1180` — state file read with verification carry (new)
- `quality_gate.py:1195-1200` — scan variables initialized from carried state (new)
- `quality_gate.py:1228-1240` — state file write with verification fields (new)
- `quality_gate.py:1326-1335` — shadow-mode receipt relief (new)
- `verification_receipt_writer.py:937` — producer writes scope_type="CLAIMED_SCOPE"
- Commit `48b6855` — all fixes + 15 new tests

## Auto-related

- [[skill-catalog]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[verification-receipt-systems-design-landscape]]
- [[claude-code-hook-system]]
- [[claude-code-hook-system-patterns]]


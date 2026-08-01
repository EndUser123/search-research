# Handoff: Quality gate receipt system fix — Phase 2 receipt format

**Status:** OPEN — scan window + format mismatch fixed, deeper receipt writer classification deferred  
**Created:** 2026-08-01  
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9  
**Supersedes:** `fleet-dispatch-improvements-20260731` (partially — the quality gate fix is new)

## Objective

The Stop hook quality gate had 3 root-cause bugs that made the receipt system non-functional in shadow mode. All 3 fixed this session. A deeper issue (receipt writer classification) is deferred.

## What was shipped (commits in ~/.grok)

- `48b6855` — Fix quality gate receipt system: scan window persistence, Phase 2 format compatibility, shadow-mode relief
  - Bug 1: scan window — verification_ran/code_modified_after_verification reset every Stop fire → persisted in state file
  - Bug 2: Phase 2 receipt format rejected — _is_valid_succeeded_receipt required scope_type=="FILES" but writer produces "CLAIMED_SCOPE" → accept both + VERIFICATION_SUCCEEDED_UNBOUND
  - Bug 3: fingerprint comparison used scope_refs (claimed subset) instead of observed_state_refs → fixed
  - Bug 4 (prior fix): shadow mode writes receipt-derived required_capability that can't be satisfied → use syntax-level capability
- 15 new tests across 3 test suites (44 + 28 + 14 = 86 total, all pass)

## Wiki concept produced

`phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope.md` — documents the 3 bugs, the fix, and the falsifier

## Open work

### Deeper issue: receipt writer classification + scan window width
The /tp review identified that the deeper issue (PostToolUse receipt writer may not classify verifier commands correctly, and the scan window width for the old gate) needs a dedicated session with /why root-cause analysis. This is deferred.

### Tests for the obligation-clearing path
A regression test was added (test simulates: block in shadow mode → run verifier → obligation clears). But the full end-to-end path (Stop hook blocks → receipt written → next Stop clears obligation) was tested only via unit tests, not live.

## Acceptance criteria

1. Quality gate stop hook no longer false-positives when verification was run 2 turns ago ✅ (fixed + tested)
2. Phase 2 receipts accepted by coverage check ✅ (fixed + tested)
3. Shadow-mode receipt relief works ✅ (fixed + tested)
4. Receipt writer correctly classifies ruff check → static_analysis (DEFERRED — was actually correct, the bug was the format mismatch)

---
thread_id: close-authority-critical-findings-20260727
parent_handoff_path: none
current_session_id: 019fa5a1-0446-7e02-9766-bd2457ee58c3
current_terminal_id: grok-build-primary
produced_at: 2026-07-27T22:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ac63013e8a17b30995e22f887142c2046f873659
---

# Handoff — Close-authority branch: 2 critical findings, DO NOT MERGE

## Objective

Fix the 2 critical integrity bypasses (INTG-1, INTG-2) and 3 high-severity bugs
(CORR-001/2/3) in the close-authority state machine on branch
`close-authority-019fa5a1`, then re-run independent review before merge
consideration. The branch implements a close-authority state machine to prevent
model-authored close-report bypasses of /close gates.

## Why this exists

Session 019fa5a1 implemented the close-authority module (state machine + AAR
receipts + close receipts + renderer authority) to structurally prevent the
model from bypassing /close gates. The implementation passed all 20 unit tests
and was declared "PROVEN_WITH_LIMITATIONS." A subsequent `/review` with
cross-model specialists found **2 critical bypasses** that defeat the target
invariant. The most severe (INTG-1) was empirically reproduced: a model can
forge an AAR receipt and obtain CLOSE COMPLETE.

The branch is at commit `d516ccc` on `close-authority-019fa5a1` in worktree
`P:/worktrees/dotgrok-close-authority`. Review verdict: **critical — DO NOT MERGE**.

## The 2 critical findings (must fix before merge)

### INTG-1 — AAR receipt provenance unverified; model can self-issue CLOSE COMPLETE

- **Severity:** critical (empirically confirmed, confidence 1.0)
- **Location:** `skills/close/__lib/close_authority.py:583-637` (`_find_and_load_aar_receipt`) + `skills/close/__lib/close_accounting.py:2702-2733`
- **Problem:** receipt discovery is purely location-based (`skills/aar/.artifacts/<session_id>/_run.json`). `validate_aar_receipt()` checks only fields the writer controls (schema version, session_id, status, mode, timestamp, report digest). No HMAC, no signature, no producer identity. The model can write a forged `_run.json` and get CLOSE COMPLETE.
- **Evidence:** forged a `_run.json` + report for a `needs_attention` session; `_enforce_close_authority()` returned CLOSE COMPLETE. Reproduced during the review run.
- **Fix direction:** the AAR receipt must carry a producer-attested field the model cannot author. Options: (a) `completion_receipt.py` writes a producer stamp (hash of AAR skill source + run timestamp) the close scanner verifies; (b) receipt written by a process whose PID is recorded and verified alive; (c) use the existing mutation-receipt system the close scanner already trusts.

### INTG-2 — validate_close_receipt never inspects resolved_gate_states

- **Severity:** critical (verified, confidence 0.95)
- **Location:** `skills/close/__lib/close_authority.py:283-302` (`validate_close_receipt`)
- **Problem:** `validate_close_receipt()` accepts a CLOSE COMPLETE receipt with `resolved_gate_states={'retrospective':'needs_attention'}` — returns `(True, "")`. The gate-content check lives only in `authorize_completion()`, not on the reload path. A fabricated receipt passes validation.
- **Evidence:** constructed a CLOSE COMPLETE receipt with needs_attention gates; `validate_close_receipt()` returned `(True, "")`.
- **Fix direction:** `validate_close_receipt()` must reject any CLOSE COMPLETE receipt where `resolved_gate_states` contains `needs_attention`. Also: make `expected_scanner_digest` mandatory for COMPLETE receipts (currently silently skipped when omitted).

## The 3 high-severity bugs (should fix before merge)

| ID | Title | Location | Fix |
|---|---|---|---|
| CORR-001 | ImportError fail-safe raises UnboundLocalError (`auth_gates` referenced before definition) | `close_accounting.py:2646-2649` | Move `auth_gates` construction before the import block, or return hardcoded empty dict in ImportError path |
| CORR-002 | `close_runner._render_compact` doesn't pass `authority_verdict` (split verdict: JSON says COMPLETE, text says INCOMPLETE) | `close_accounting.py` (close_runner path) | Wire `authority_verdict` through `close_runner._render_compact` same as `main()` |
| CORR-003 | "What's at risk" section uses raw gates not resolved_gates (internal contradiction: COMPLETE + "retrospective not completed") | `close_accounting.py:3568-3574` | Use `resolved_gates` or authority verdict for risk items |

## Read-first list

1. This handoff
2. `P:/.artifacts/console_f8a6c949-f70c-4451-9f31-6295/grok-review/close-authority/20260727-172151/FINDINGS.md` — the full review with all 13 findings, evidence, and fix directions
3. `P:/worktrees/dotgrok-close-authority/skills/close/__lib/close_authority.py` — the authority module (state machine, receipt validation)
4. `P:/worktrees/dotgrok-close-authority/skills/close/__lib/close_accounting.py` — the scanner integration (`_enforce_close_authority` at ~L2614)
5. `P:/worktrees/dotgrok-close-authority/skills/close/tests/test_close_authority.py` — the 20 tests (all pass, but don't cover INTG-1/INTG-2)
6. `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` — why self-verification missed these (three-role conflict)
7. `P:/.data/wiki/concepts/verification-claim-admissibility.md` — the verdict vocabulary and replay realism rubric

## Related wiki concepts

- `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` — documents why the 20 tests missed INTG-1/INTG-2 (the implementer-tester-threat-actor conflict)
- `P:/.data/wiki/concepts/verification-claim-admissibility.md` — defines COMPONENT_PROVEN vs LIVE_ENFORCEMENT_PROVEN and replay realism tiers
- `P:/.data/wiki/concepts/close-single-authority-renderer.md` — the original design rationale for single-authority rendering

## Verified facts

- [FACT] Branch `close-authority-019fa5a1` is at commit `d516ccc` in worktree `P:/worktrees/dotgrok-close-authority` (verified: `git log --oneline -1` on the branch).
- [FACT] All 20 tests pass on the branch (verified: pytest output during implementation).
- [FACT] INTG-1 was empirically reproduced during the review — forged receipt obtained CLOSE COMPLETE (verified: FINDINGS.md INTG-1 evidence section).
- [FACT] INTG-2 was verified by the integrity specialist — `validate_close_receipt()` returns `(True, "")` for a COMPLETE receipt with needs_attention gates (verified: FINDINGS.md INTG-2 evidence section).
- [FACT] The review verdict is "critical — DO NOT MERGE" (verified: FINDINGS.md line 12).
- [FACT] The branch is NOT wired into the production `/close` path — it exists only in the worktree (verified: `git diff --stat HEAD` on main showed zero changes to close_accounting.py).

## Suggested next

1. Fix INTG-1 first (producer attestation mechanism) — it's the most severe and blocks all merge consideration.
2. Fix INTG-2 (gate-content check on reload path) — straightforward code change.
3. Fix CORR-001/2/3 in the same pass — they're small and related.
4. Add tests that specifically probe INTG-1 and INTG-2 (the existing 20 tests didn't catch them).
5. Re-run `/review` with cross-model specialists on the fixed branch.
6. Only consider merge after the re-review passes with no critical findings.

**Important:** per the maker-checker rule (`P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md`), the implementing agent must NOT issue the final PROVEN verdict on the fixed code. Independent review is required — the agent that writes the fix shares the same blind-spot class that produced the hole.

## Dependencies

- **Requires:** nothing — can start immediately in a fresh session
- **Blocks:** the close-authority state machine cannot fulfill its purpose (preventing model bypass of /close gates) until INTG-1 is fixed
- **Non-blocking to:** the evidentiary-discipline gaps (GAP-1 through GAP-5) are workspace-wide improvements that don't depend on this branch

## Falsifier

This handoff would be wrong if: (a) the branch has already been fixed and re-reviewed since `d516ccc` — check `git log --oneline close-authority-019fa5a1` for commits after d516ccc; (b) the findings were false positives — re-read FINDINGS.md evidence and re-run the reproduction. If either is true, update or close this handoff.

## Last user message (verbatim)

> "/handoff" (auto-update mode — no specific topic named)

## Epistemic labels

- [FACT] All findings, evidence, and fix directions are cited from FINDINGS.md (review run 20260727-172151).
- [FACT] The branch state (commit, worktree path, test count) is verified from this session's tool output.
- [INFERENCE] The suggested fix order (INTG-1 first) is based on severity + empirical reproducibility, not dependency ordering — the fixes are independent.

# Phase 3 Hook Enforcement System — Design Specification

**Status:** Deployed 2026-07-26 (commit `62ae9c6` on `integration/phase3-ab`)
**Source:** `P:/worktrees/dotgrok-phase3/hooks/scripts/`
**Tests:** 468 total (455 custom-framework + 13 pytest), 0 failures

## Purpose

Phase 3 adds path-specific repository identity, mutation receipt schema v2,
candidate resolution, private-index commit engine, submodule reconciliation,
verification enforcement, and session-close coordination to the Grok Build
hook surface.

## Architecture (Workstreams A + B)

### Workstream A — Verification Enforcement

**Files:** `quality_gate.py`, `verification_receipt_writer.py`,
`verification_status_adapter.py`

**Behavior:**
- Live Stop blocking (quality_gate.py fires on Stop event)
- Same-turn re-entry (continuation obligations)
- Obligation nonce (causal ordering)
- `claimed_scope_refs` separated from `observed_state_refs`
- Path-specific repository/worktree identity in every verification receipt
- `get_verification_enforcement_status()` stable API (contract version 1.0)
- Enforcement-health states: AVAILABLE / HEALTH_UNKNOWN / UNAVAILABLE / CORRUPT / INCOMPATIBLE_VERSION
- Missing health API → INCOMPATIBLE_VERSION → close BLOCKS (fail-safe)

### Workstream B — Repository-Aware Persistence

**B1: Path Identity** (`path_identity.py`)
- Schema version, resolution status, canonical path, repository root,
  repository ID, Git common directory, worktree ID, Git-relative path,
  HEAD SHA, identity source, submodule indicators, parent repository fields
- Canonical wire statuses: RESOLVED / AMBIGUOUS / OUTSIDE_GIT / LEGACY_RECONSTRUCTED / MISMATCH
- Readers accept historical long-form aliases

**B2: Legacy Receipt Compatibility** (`legacy_receipt_compat.py`)
- Schema-v1 receipts reconstructed conservatively
- Current repository discovery ≠ historical ownership proof
- Deleted/ambiguous legacy paths block

**B3: Candidate Resolver** (`candidate_resolver.py`)
- Target-session-only candidate resolution
- Every relevant path in exactly one category: eligible / blocked / excluded
- Blocked candidates carry: reason_codes, retryability, required_next_action
- Excluded ONLY for: FAILED_OPERATION, PARTIAL_OPERATION, NO_SESSION_OWNED_CHANGE, OUTSIDE_GIT, LEGACY_IDENTITY_UNPROVEN

**B4: Private-Index Commit Engine** (`commit_coordinator.py`)
- Private temporary Git index
- read-tree from expected HEAD
- Exact-path staging
- commit-tree + atomic update-ref CAS
- Post-CAS shared-index sync with lock-contention retry (COMMITTED_INDEX_SYNC_FAILED on failure)
- No pushes, no destructive operations

**B5: Submodule Coordinator** (`submodule_coordinator.py`)
- Child commit through B4
- Parent Git-link update via private index + CAS
- Retry entry point: `skip_child_commit=True` + `child_commit_sha`
- CAS-race rejection proven (test_cas_race.py 22/22)

**B6: Close Coordinator** (`close_coordinator.py`)
- Verification gate BEFORE persistence (correct ordering)
- B3 candidate resolution → B4 ordinary commits → B5 submodule reconciliation (Design A: coordinator-owned)
- SESSION_CLOSED requires: verification accepted + no pending obligation + no blocked candidate + all B5 reconciled
- Per-path blocked evidence: session_id, canonical_path, repo/worktree identity, source receipt IDs, expected/current HEAD, fingerprints, reason codes, retryability, required_next_action

## Safety Constraints

**Never:**
- reset, clean, stash, globally stage, force checkout, overwrite unrelated files
- commit foreign-session files
- auto-push
- claim publication without proof
- infer ownership from Git dirtiness, mtime, or file proximity

**Preserve unrelated:**
- staged files, unstaged files, untracked files, repository branches, shared indexes, background processes, foreign receipts

**Session ID from runtime payload is the ownership authority.**
**Repository identity is path-specific. `workspaceRoot` is contextual metadata.**
**Verification receipts and mutation receipts are separate evidence types.**

## Enforcement-Health Contract

`/close` may proceed ONLY when:
- `enforcement_status == ENFORCEMENT_AVAILABLE`
- `obligation_reads_authoritative == True`
- `receipt_reads_authoritative == True`

Missing API → `INCOMPATIBLE_VERSION` → BLOCK. No fail-open.

## Acceptance Criteria

1. All deterministic tests pass (468 total, 0 failures)
2. True post-commit-tree CAS movement is safely rejected
3. `/close` cannot declare SESSION_CLOSED with blocked candidates
4. `/close` cannot declare SESSION_CLOSED with unreconciled parent Git-links
5. Enforcement-health unknown/incompatible states block close
6. No push or publication is falsely claimed
7. Concurrent-session isolation proven (deterministic)
8. Stale output cannot influence current evidence

## Test Entry Points

```powershell
# Run all Phase 3 tests
$files = @("test_path_identity","test_interface_acceptance","test_b2_b3",
           "test_b3_acceptance","test_b4_commit","test_b4_live",
           "test_ab_identity_compat","test_quality_gate_phase2",
           "test_scope_capability_nonce","test_continuation_obligation",
           "test_b5_submodule","test_b5_live","test_b6_close",
           "test_b6_close_expanded","test_cas_race",
           "test_concurrent_isolation","test_stale_isolation",
           "test_workstream_a_hardening","test_defect_fixes",
           "test_mixed_state_health","test_e2e_close_b5")
foreach ($f in $files) {
    python "P:\worktrees\dotgrok-phase3\hooks\scripts\tests\$f.py"
}
```

## Deployment

- **Atomic set:** all 10 files must deploy together (cross-imports)
- **Deployment script:** `Deploy-Phase3.ps1` (atomic with rollback)
- **Manifest:** `DEPLOYMENT_MANIFEST.json`
- **Rollback:** restore from backup directory (no destructive git)

## Live Acceptance (operator-run, post-deployment)

1. Start fresh session
2. Mutate one harmless path in each: P:\, ~/.grok, disposable submodule
3. Claim completion without verification → Stop hook should block
4. Verify paths one at a time → hook should block until all verified
5. Invoke `/close` → should commit each approved path, update parent Git-link
6. Verify no auto-push, no false publication claims

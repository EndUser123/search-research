---
thread_id: hook-refactor-plan-20260727
parent_handoff_path: none
current_session_id: 019fa23d-e74c-7ff2-ac51-980b5d999b87
current_terminal_id: noterm
produced_at: 2026-07-27T23:30:00Z
status: open
handoff_type: implementation
accurate_as_of_head: da6bbe0
---

# Hook refactor: shared constants, dead code, submodule cache

## Objective

Refactor the Phase 3 deployed hooks (`~/.grok/hooks/scripts/`) to eliminate
structural debt identified during the hook timeout investigation and skill
feature audit. Three seams, ordered by risk (lowest first per T42).

## Status

PLAN READY — not executed. Plan artifacts at:
- `P:/.artifacts/noterm/grok-refactor/hooks/20260727-092208/PLAN.md`
- `P:/.artifacts/noterm/grok-refactor/hooks/20260727-092208/seams.json`

**If the artifacts dir is gone**, the plan is also documented below.

## Seams (execution order: B2 → B1 → A1, lowest risk first)

### B2: Remove dead code — `_resolve_path_identities` (risk: S)
- **File:** `~/.grok/hooks/scripts/verification_receipt_writer.py` L51-86 + import L49
- **What:** Function has zero callers after the `[]` fix (commit `90aabe3`). Delete function + `path_identity as _pi` import.
- **Verify:** `cd P:/worktrees/dotgrok-phase3 && python P:/tmp/phase3_run_tests.py` (21/21)
- **Deploy:** copy to `~/.grok/hooks/scripts/`, hash-verify, smoke-test

### B1: Cache `_check_submodule_context` per session (risk: M)
- **File:** `~/.grok/hooks/scripts/path_identity.py` L313-384
- **What:** Add module-level cache dict for `(repo_root, parent_root)` pairs. The submodule relationship is static within a session. Prevents repeated `git submodule status` (4-8s/path on Windows).
- **Verify:** timing test (`python P:/tmp/time_paths.py` — cached should be faster for repeated paths)
- **Deploy:** copy to `~/.grok/hooks/scripts/`, hash-verify

### A1: Extract shared constants to `constants.py` (risk: L)
- **Files:** `quality_gate.py`, `quality_nudge.py`, `verification_receipt_writer.py`
- **What:** CODE_EXTENSIONS (duplicated in 3 files), VERIFICATION_PATTERNS (duplicated in 2 files), CAPABILITY_HIERARCHY — extract to `constants.py`, import in all consumers.
- **Pre-check:** diff the VERIFICATION_PATTERNS lists in quality_gate.py:121 and verification_receipt_writer.py:97 to confirm they're actually identical before unifying.
- **Verify:** `cd P:/worktrees/dotgrok-phase3 && python P:/tmp/phase3_run_tests.py` (21/21)
- **Deploy:** copy `constants.py` + all modified files to `~/.grok/hooks/scripts/`, hash-verify, smoke-test each hook

## Constraints

- `deployment_target: ~/.grok/hooks/scripts/` — each seam must include deployment verification (T41)
- Source worktree: `P:/worktrees/dotgrok-phase3/hooks/scripts/`
- Risk sort: B2 (S) → B1 (M) → A1 (L) — build confidence before structural change (T42)
- 21/21 deterministic suite must pass after each seam

## Resumption

```
/refactor implement the hooks plan
```

Or manually: read this handoff, read the seams above, execute B2 → B1 → A1 in order with per-seam verify + deploy.

# Handoff — Hook State Isolation & Staleness

**Date:** 2026-06-19
**Branch:** `main` (ahead of `origin/main`; not pushed)
**Related docs (same dir):** `TERMINAL_ISOLATION.md`, `SESSION_NAMESPACE_ISOLATION.md`, `T-005-completion-summary.md`
**Commits this thread:**
- `9a05ae7` — fix structural_change import path + remove dead `output` param
- `bcc98c4` — session-scope change_propagation state; harden state_paths root; add isolation ratchet

---

## What was fixed (done, verified)

1. **`change_propagation_hook` runtime import was dead** (`9a05ae7`). `from structural_change import …` resolved against `.claude/hooks/` (no such module); the real module is in `__lib/`. `except Exception` swallowed the `ImportError`, so Edit/deletion detection was silently dead in production while 16 tests passed (tests injected `__lib` into `sys.path`). Fixed to `from __lib.structural_change import …`.

2. **Multi-terminal isolation broken + stale false positives** (`bcc98c4`). The hook wrote state to `CSF_STATE_DIR/propagation_state.json` — **one file shared by all terminals** (the "terminal-scoped default" branch was dead code; `CSF_STATE_DIR` is always set to the shared root in `settings.json:12`). Migrated onto the canonical contract `__lib/state_paths.py`: state is now session-scoped at `.claude/state/sessions/{session_id}/propagation_state.json`, with `run()` resolving `session_id`. New session = fresh dir → isolation **and** cross-session staleness both closed.

3. **`state_paths.py` root was cwd-relative** (`bcc98c4`). `STATE_DIR` used `PROJECT_ROOT` env, which is **unset** at runtime, so it fell back to `"."` (cwd) — a latent isolation hazard for all 5 adopters. Now cwd-independent: `PROJECT_ROOT` else module-relative `parents[3]`.

4. **Recurrence guard** (`bcc98c4`). `tests/test_state_isolation_ratchet.py` freezes the 9 remaining `CSF_STATE_DIR` users as known debt and fails any **new** offender; a second test fails if an allowlist entry is migrated but not removed (keeps the backlog honest).

**Verification:** 34 tests pass (`test_change_propagation_hook.py` + `test_state_paths.py` + `test_state_isolation_ratchet.py`), incl. a two-session isolation regression. Production import path verified end-to-end. Both modules byte-compile.

---

## Outstanding items

### 1. Fix is not live until next session restart — HIGH (informational)
PostToolUse hooks load **in-process at session start**. The session that did this work still runs the pre-fix module, which is why the `📝 Outstanding verifications: file_deletion (…propagation_state.json)` banner kept firing. Harmless; gone after restart. **Action:** restart the CC session, then confirm new state lands under `.claude/state/sessions/{id}/` and the root `propagation_state.json` is no longer recreated.

### 2. Migrate remaining 9 hooks off `CSF_STATE_DIR` — MEDIUM → tracked as task #839
Stalled TASK-005 adoption sits at ~6% (5 of ~80 accumulate-class hooks use `state_paths`). The 9 still reading `CSF_STATE_DIR` as a literal state dir:
```
PreToolUse_git_remote_check_order_guard.py   SessionStart_memory_cks_auto.py
Stop_meta_conversation_loop.py               Stop_recommendation_gate.py
UserPromptSubmit_modules/recommendation_loop.py   __lib/enforcement_rate_limiter.py
_cks_cache.py                                csftracker.py
shared_utils.py
```
Per hook, decide **session-derivable** (prefer deriving from `__lib/hook_ledger.py`, delete the persistent file) vs **genuinely durable** (route through `get_session/terminal/shared_state_path`). Reference impl: `posttooluse/change_propagation_hook.py`. Remove each from `_ALLOWLIST` in the ratchet as it migrates; delete/repoint the ratchet when empty.

### 3. `session_id` fallback collapses to a shared dir — LOW (residual risk)
`_resolve_session_id` falls back to `"unknown"` when absent → `sessions/unknown/` is shared across any payloads lacking a session id. Strong evidence session_id **is** present at hook runtime (live `auth_gate_<uuid>_*.json` files carry real session UUIDs). **Not directly verified** for the PostToolUse payload at runtime. **Action:** after restart, confirm change_propagation state lands under the real session UUID, not `unknown/`. If `unknown/` appears, thread `terminal_id` as a secondary key.

### 4. Pre-existing test failures (NOT caused by this work) — MEDIUM
13 failures in `test_task_005_integration.py`, `test_intent_extractor_migration.py`, `test_investigation_gate_terminal_scoped.py`. Verified pre-existing: stashing the `state_paths` edit reproduced the identical 13-failed/49-passed result. Likely related to the same incomplete TASK-005 migration. Worth a dedicated triage pass — they erode trust in the state-contract test signal.

### 5. Contract has no staleness *versioning* — LOW (deliberately deferred)
`state_paths.py` scopes by session/terminal but has no `schema_version` stamp, so a detector-logic change mid-session could leave records from the old logic. Session-scoping already closes the cross-session class; versioning is belt-and-suspenders. Deferred as theoretical-risk (anti-bloat). Revisit only if an intra-session staleness case is observed.

### 6. Ratchet scope is the `CSF_STATE_DIR` vector only — LOW (known limit)
It will not catch a hook hardcoding `Path(".claude/state")/f` directly. It nails the exact pattern that recurred; broadening detection is optional future work.

### 7. Duplicate deferral debt — HOUSEKEEPING
Task #828 ("Deferral: defer that") remains with an **unknown referent** — the cc-lazy-closure-debt hook re-injects it every turn. #837/#838 (duplicates) were deleted. **Action:** identify what "defer that" referred to (originating ~16h before 2026-06-19) and close #828, or the hook will keep nagging.

---

## Architectural note (for the long-term reviewer)
The systemic root cause is not "no standard" — a scoped-state contract (`state_paths.py` + `migrate_legacy_state.py`, TASK-005) exists but stalled at ~6% adoption with **no enforcement** and **no versioning**. The durable fix is *finish + enforce + derive*: (a) the ratchet (added) makes adoption stick by default; (b) migrate durable state onto the contract; (c) for session-derivable state, prefer deriving from `hook_ledger`/transcript over persisting at all. Avoid building a new framework — both layers' infra already exists.

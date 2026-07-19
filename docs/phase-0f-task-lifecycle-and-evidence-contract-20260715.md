# Phase 0F: Task Lifecycle and Evidence Contract Design

**Date:** 2026-07-15
**Phase:** 0F — Discovery and architecture design only. No code changes.
**Status:** READY for migration planning — lifecycle contract defined.

---

## Executive Verdict

**READY FOR TASK TRACKER MIGRATION.** The lifecycle contract is defined. The only missing piece is implementing the evidence chain (completion → receipt) as a real gate.

### What changes from Phase 0E

Phase 0E determined *who writes* (plugin as authority). Phase 0F determines *what the states mean* and *what evidence is required*.

**The key unlock:** The receipt system already has correct semantics (VERIFIED/REVIEW/NO_EVIDENCE). It is already wired into the `/task` command. It is already wired into task verification and deletion. The only thing missing is the **completion gate** — the step between "agent says done" and "task state is recorded as completed." That gate is currently advisory by design (chicken-and-egg problem with TaskUpdate tool schema). Once a separate completion+receipt path exists, the gate can become blocking.

---

## 1. Task State Machine

### Official state set

```
created  ──→ pending  ──→ in_progress  ──→ completed  ──→ verified
  │                                             │              │
  └──→ cancelled                                 └──→ archived  │
       (from any state)                                (disposable)
```

### State definitions

| State | Meaning | Who creates it | Required evidence |
|-------|---------|----------------|-------------------|
| `created` | Task exists in system; not yet ready to work | TaskCreate tool | None |
| `pending` | Task is queued, not actively worked | TaskCreate (default status) or TaskUpdate | None |
| `in_progress` | Active work underway | TaskUpdate | None |
| `completed` | Work is done; completion asserted | TaskUpdate | Stated as done (see §3) |
| `verified` | Work proven done — receipt evidence passes | `/task done --verify` or completion verifier | VERIFIED receipt |
| `cancelled` | Work aborted; not done | TaskUpdate | Reason |
| `archived` | Data retained for audit; no longer actionable | `/task clean` (only VERIFIED tasks) | VERIFIED receipt |

### Current reality: states actually used

| State | In task_tracker files? | In task schema? | Effectively enforced? |
|-------|----------------------|----------------|----------------------|
| `pending` | Yes | Yes | Yes — created by TaskCreate default |
| `in_progress` | Yes | Yes | Yes — created by TaskUpdate |
| `completed` | Yes | Yes | Yes — created by TaskUpdate |
| `verified` | **No** | **No** | **No** — exists only in receipt system |
| `cancelled` | **No** | **No** | **No** — not modeled |
| `archived` | **No** | **No** | **No** — `/task clean` deletes, not archives |

**Gap:** The task tracker has no concept of `verified`. The receipt system has `VERIFIED` as an evidence measurement, but nothing in the task tracker records whether verification passed. This is the core lifecycle gap.

### Allowed transitions

```
created      → pending       (TaskCreate with status=pending)
created      → cancelled     (TaskUpdate)
pending      → in_progress   (TaskUpdate)
pending      → completed     (TaskUpdate — direct completion)
pending      → cancelled     (TaskUpdate)
in_progress  → completed     (TaskUpdate)
in_progress  → pending       (TaskUpdate — reset)
completed    → in_progress   (TaskUpdate — reopen)
completed    → verified      (/task done --verify passes)
verified     → archived      (/task clean with VERIFIED receipt)
```

### Forbidden transitions

```
pending      → verified      (skip work — evidence impossible)
in_progress  → verified      (skip completion — evidence broken)
completed    → pending       (not allowed — would lose completion signal)
created      → completed     (no work done)
verified     → completed     (verified must be terminal, not reversible)
verified     → in_progress   (cannot reopen verified tasks)
```

---

## 2. Transition Authority Model

| Transition | Producer (who requests) | Recorder (who writes) | Validator | Required evidence |
|-----------|------------------------|----------------------|-----------|-------------------|
| `pending → in_progress` | Agent (internal decision) | TaskUpdate tool → both hooks | None | None |
| `in_progress → completed` | Agent (`TaskUpdate(status=completed)`) | TaskUpdate tool → both hooks | **Advisory** — receipt gate nudges | **Desired:** Receipt (currently advisory) |
| `completed → verified` | Agent (`/task done --verify`) | `task_receipt.py write` + separate process | `task_verify.py verify` | Passed verification command + baseline + evidence files |
| `completed → in_progress` | Agent (`TaskUpdate(status=in_progress)`) | TaskUpdate tool → both hooks | None | Reopen reason |
| `verified → archived` | Agent (`/task clean --apply`) | `task_verify.py clean` | Receipt-based | VERIFIED-class receipt |

### Key insight about the current authority model

The task tracker is a **passive observer** — it records what the agent does but does not validate it. The receipt system is an **active validator** — it blocks deletion without evidence. But there is no gate that forces the receipt system to be used.

**The authority chain is broken at one point:** `in_progress → completed` has no required evidence. The evidence gate is advisory by design (TaskUpdate doesn't support evidence fields). Until completion evidence is required, the lifecycle authority model is incomplete.

---

## 3. Completion Contract

### What does "completed" mean?

**Recommendation: Option C — "The work was performed AND evidence exists."**

But Option C cannot be enforced today because TaskUpdate does not carry evidence fields. So the completion contract must be **two-phase**:

1. **Phase 1 (current):** Agent marks completed. No evidence check.
2. **Phase 2 (after completion):** Agent writes receipt via `/task done` or automation.

### Option evaluation

| Criterion | A: Agent says done | B: Work was done | C: Work + evidence |
|-----------|-------------------|-------------------|--------------------|
| Current feasibility | ✅ Works today | ⚠️ Unmeasurable | ❌ No evidence pathway in TaskUpdate |
| User trust | ❌ Low — "agent hallucinated completion" | ✅ Medium | ✅ High |
| Clean/delete safety | ❌ All tasks eligible for cleanup | ❌ Unable to determine | ✅ Only VERIFIED tasks eligible |
| Audit trail | ❌ Nothing to audit | ❌ Subjective | ✅ Receipt + evidence files |
| Migration cost | None | None | **Must fix TaskUpdate evidence gap first** |

### Two-phase completion contract

**Phase 1: Declaration** (when `TaskUpdate(status=completed)` fires)
- Task state records `status: completed`
- Receipt gate prints advisory: "Run `/task done <id>` for durable evidence"
- Plugin auto-writes a `NO_EVIDENCE` receipt as safety net

**Phase 2: Verification** (when `/task done --verify <cmd>` runs)
- Verification command executes
- If pass + evidence files + baseline → receipt becomes `VERIFIED`
- If fail → receipt stays `REVIEW` or `NO_EVIDENCE`
- Only `VERIFIED` tasks are eligible for clean/deletion

### Why two-phase is correct

The chicken-and-egg problem cannot be solved by the task tracker alone. TaskUpdate is a Claude Code built-in tool — it has no `evidence_files` or `verification_commands` fields. Any solution must either:
- Add those fields (requires changing Claude Code itself), or
- Accept a two-phase model where declaration and verification are separate steps

The two-phase model is already partially implemented (receipt system exists, `/task done` exists, evidence gate exists). The missing piece is a blocking gate between Phase 1 and Phase 2.

---

## 4. Receipt Authority Model

### Receipt evidence classes

| Class | Meaning | Who writes | Allows clean? | Current count |
|-------|---------|------------|---------------|---------------|
| `VERIFIED` | Verification command passed + baseline + evidence files exist + task fingerprint matches | `/task done --verify <cmd> <files>` | Yes | **0** |
| `REVIEW` | Final commit captured; verification incomplete or missing | `/task done` (auto-receipt with commit) | No | **0** |
| `NO_EVIDENCE` | Task completed but no verification, no evidence, no fingerprint | Auto-receipt from plugin `track_task_update()` | No | **2** |

### Current usage reality

Only 2 receipts exist across the entire system. Both are `NO_EVIDENCE` — meaning the auto-receipt from the plugin wrote them but never attempted verification. This confirms that the receipt system is a **safety net, not an active enforcement mechanism.**

### Receipt authority roles

| Artifact | Authority | Purpose | Blocking? |
|----------|-----------|---------|-----------|
| `task state (status=completed)` | TaskUpdate tool | **Assertion** — agent declares completion | No (always allowed) |
| `receipt (evidence_class=VERIFIED)` | Verification command | **Proof** — work was done correctly | Yes (only VERIFIED allows clean) |
| `receipt (evidence_class=REVIEW)` | Commit evidence | **Partial proof** — something was committed | No |
| `receipt (evidence_class=NO_EVIDENCE)` | None | **Acknowledgement** — completion was recorded | No |

### The gap

The receipt system has correct authorization semantics (only VERIFIED allows clean), but **no one is writing VERIFIED receipts** because the verification step requires explicit `/task done --verify` which depends on model discipline.

---

## 5. Completed-Without-Receipt Policy

**Policy:** `completed + no receipt = legacy accepted`

### Rationale

1. **The system was built with no enforcement.** Making `completed + no receipt` invalid now would invalidate all 75 terminals with completed tasks.
2. **The receipt system was intentionally advisory.** The evidence gate's design document explicitly says "this gate never authorizes or blocks anything."
3. **Receipt volume is near zero** (2 receipts for 75+ terminals with completed task state). Invalidating all non-receipt completions would be destructive, not corrective.
4. **A forward-looking migration is better than a retroactive ban.** Define the rules for NEW completions; accept OLD completions as-is.

### Forward-looking rule

Going forward (after migration cutover):

| Scenario | Policy |
|----------|--------|
| NEW completion with receipt | Normal path |
| NEW completion without receipt | Advisory emitted; task eligible for clean only after receipt |
| EXISTING completion without receipt | Accepted as legacy; task may be completed manually |
| EXISTING completion conflicting with receipt | Receipt wins (see §6) |

---

## 6. Conflict Resolution Semantics

| Case | Conflict | Resolution rule | Required evidence | Example |
|------|----------|----------------|-------------------|---------|
| **1** | `pending` vs `in_progress` | `in_progress` wins (forward in lifecycle) | None | Both stores disagree on whether work started |
| **2** | `in_progress` vs `completed` | `completed` wins (forward in lifecycle); check for receipt | Receipt if available | Task #867: local=in_progress, plugin=completed |
| **3** | `completed` vs `verified` | `verified` wins (receipt is stronger evidence) | VERIFIED receipt | Receipt exists and passes verification |
| **4** | Different evidence sets | **Merge** — take latest files_referenced + files from both | None (additive) | One store has files A,B; other has B,C → result has A,B,C |
| **5** | One store has data, other doesn't | **Copy** — data wins over empty | None | Task exists in local only → add to canonical store |
| **6** | Both `completed`, different timestamps | **No conflict** — both agree on status. Use higher-quality metadata. | None (cosmetic) | Same status, different `repo` or `session_id` values |

### Rule: Forward lifecycle wins

For any status disagreement, resolve by lifecycle ordering:
```
created(0) < pending(1) < in_progress(2) < completed(3) < verified(4)
```
Higher number wins. This is justified because:
- Task lifecycle is monotonic forward (work progresses, not regresses)
- The known conflict (#867: in_progress→completed) resolves to completed — the correct answer
- Newer lifecycle stages carry more information (a completed task may have been reopened, but the re-completion should be authoritative)

### Exception

Do NOT apply this if a receipt exists. A `VERIFIED` or `REVIEW` receipt overrides any status disagreement — it is the strongest evidence because it was explicitly written by the verification system, not passively observed by the task tracker hook.

---

## 7. Task Schema Recommendation

### Required fields

| Field | Required? | Purpose | In current schema? |
|-------|-----------|---------|-------------------|
| `id` | **Yes** | Unique task identifier | Yes |
| `subject` | **Yes** | Human-readable title | Yes |
| `status` | **Yes** | Current lifecycle state | Yes |
| `session_id` | **Yes** | Session provenance | Yes |
| `terminal_id` | **Yes** | Terminal isolation boundary | Yes |
| `created_at` | **Yes** | Creation timestamp | Yes |
| `description` | **Should (for context)** | Task details | Yes |
| `files_referenced` | **Should (for evidence)** | File context | Yes |

### Additions

| Field | Required? | Purpose |
|-------|-----------|---------|
| `schema_version` | **Yes** | Enables future schema evolution without breaking readers |
| `updated_at` | **Yes** | Last status change timestamp — critical for conflict resolution |
| `completed_at` | **Should** | When completion occurred (may differ from updated_at if reopened) |
| `verification_status` | **Should** | VERIFIED/REVIEW/NO_EVIDENCE from receipt system |
| `receipt_id` | **Should** | Link to receipt file for completed tasks |
| `repository_id` | **Should** | Git repo where task was performed |
| `worktree_id` | **Optional** | Worktree where task was performed |
| `evidence_refs` | **Optional** | File paths or hashes used as verification evidence |

### Fields NOT to add (with rationale)

| Field | Why not |
|-------|---------|
| `assigned_to` | Solo-dev environment — no team assignment |
| `priority` | Already in `/go` task queue (`priority` field in `tasks.json`) |
| `blocked_by` | Not needed for current lifecycle model |
| `tags` | No consumer — would be dead data |
| `estimate` | No consumer — would be dead data |
| `weight` | No consumer — would be dead data |

---

## 8. Migration Acceptance Criteria

| # | Criterion | Verification method | Current status |
|---|-----------|-------------------|----------------|
| **A1** | Exactly one writer for task state | `state_resolver.inventory()` shows 1 `task_tracker` root | ❌ 2 roots currently |
| **A2** | All watchers (plugins, hooks) read from canonical path | Grep for hardcoded task_tracker paths | ❌ task_verify.py reads local path |
| **I1** | Terminal isolation: terminal A's tasks invisible to terminal B | State file named `{terminal_id}_tasks.json` — filename is isolation boundary | ✅ Already true |
| **I2** | Session provenance: every task has `session_id` | Schema field present | ✅ Already true |
| **I3** | Worktree isolation: two worktrees cannot collide | State file uses terminal_id, not worktree path | ✅ Already true |
| **L1** | All status values conform to state machine definition | Enumerate all statuses in task_tracker files | ⚠️ Need to verify (grep all files) |
| **L2** | No `completed` task has invalid forward transition | Check receipt system consistency | ⚠️ Need to verify |
| **E1** | Completion evidence gate is no longer advisory | Evidence gate exits non-zero on missing receipt | ❌ Advisory today |
| **E2** | All NEW completions have companion receipt | Receipt count matches completion count | ❌ 2 receipts vs 75+ completions |
| **E3** | At least one VERIFIED receipt exists | Receipt with `evidence_class=VERIFIED` | ❌ 0 VERIFIED receipts |
| **M1** | Reconciliation: all 224 terminals present in canonical store | `get_all_sessions_tasks()` returns 224 terminals | ❌ Plugin has 130 terminals |
| **M2** | Conflict #867 is resolved | Task #867 has consistent status across both stores | ❌ Still diverging |

### Gate: which criteria must be met before migration

**Hard requirements** (must change before migration begins):
- A1 (single writer) — the dual-writer is the root cause
- M1 (reconciliation) — data must be complete
- M2 (resolve #867) — known conflict must be resolved

**Hard requirements** (must change during migration):
- E1 (evidence gate becomes blocking) — without this, migrating the writer just migrates untrusted data
- L1 (status conformance) — must understand what states exist in the data

**Soft requirements** (can be deferred to post-migration):
- E2 (receipts for all completions) — legacy accepted
- E3 (VERIFIED receipt) — nice-to-have
- I1/I2/I3 — already satisfied

---

## 9. Required Future Implementation Changes

### Must change (required for correctness)

| File | Change | Why |
|------|--------|-----|
| `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` | Point `get_state_dir()` to canonical `state/task_tracker/` | Stops dual-path writes (criterion A1) |
| `cc-skills-sdlc/skills/task/scripts/task_verify.py` | Update `TRACKER_DIR` to canonical path | Consumer reads from correct location (criterion A2) |
| `PreToolUse_task_done_evidence_gate.py` | Upgrade from advisory to blocking (non-zero exit when no receipt on `completed`), **but first create a separate completion-evidencing pathway that doesn't rely on TaskUpdate tool** | Evidence gate must become blocking (criterion E1) |

### Should change (quality improvement)

| File | Change | Why |
|------|--------|-----|
| Both `task_tracker_hook.py` files | Add `schema_version`, `updated_at` to task schema | Schema evolution + conflict resolution (temporal signal) |
| Plugin `task_tracker_hook.py` | Fix `_write_automatic_receipt()` to not silently swallow all errors | Currently 2 receipts instead of 75+ |
| `task_receipt.py` | Support separate "completion-verification" mode distinct from interactive `/task done` | Enables automated verification without CLI |
| Local `task_tracker_hook.py` | Remove `TaskTrackerHook` from registry; redirect to plugin | Eliminates dual-writer at source |
| `posttooluse/__init__.py` (local) | Remove `registry.register("task_tracker", TaskTrackerHook())` | Prevents accidental re-enable |

### Optional (future enhancement)

| Change | Why |
|--------|-----|
| Add `tasks.json` queue integration with receipt system | `/go` tasks flow naturally into verification |
| Auto-verify via `/go` completion verifier (STEP 6.8) | Verification becomes automatic, not model-discipline-dependent |
| Deprecate `state/task_tracker/` old path | Clean up after migration confirmed |

---

## Required Future Tests

| Test | Covers | Priority |
|------|--------|----------|
| `test_single_writer()` | Criterion A1 | P0 |
| `test_completed_task_has_receipt()` | Criterion E2 | P0 |
| `test_evidence_gate_blocks_no_receipt()` | Criterion E1 | P0 |
| `test_status_matches_state_machine()` | Criterion L1 | P1 |
| `test_forward_lifecycle_conflict_resolution()` | Conflict resolution rules | P1 |
| `test_receipt_wins_over_status()` | Receipt authority | P1 |
| `test_verified_receipt_allows_clean()` | task_verify.py clean | P1 |
| `test_no_evidence_receipt_blocks_clean()` | Clean enforcement | P2 |
| `test_schema_version_field_present()` | Schema evolution | P2 |
| `test_updated_at_has_changed_on_status()` | Temporal tracking | P2 |

---

## Claim Ledger

| Claim | Evidence | Confidence | How to falsify |
|-------|----------|-----------|----------------|
| **Receipt system has correct authority semantics but no one uses it** | 2 receipts exist; both NO_EVIDENCE; 75+ terminals with completed tasks | HIGH | Show a VERIFIED receipt exists |
| **Evidence gate is advisory by design, not by accident** | Gate docstring lines 9-16: "DESIGN — why advisory (non-blocking)" | HIGH | Find a version where the gate ever blocked |
| **TaskUpdate cannot carry evidence fields** | Gate docstring: "The native TaskUpdate tool schema does NOT support custom evidence fields" | HIGH | Find evidence_fields parameter in TaskUpdate schema |
| **Plugin auto-receipt always writes NO_EVIDENCE** | `track_task_update()` calls `_write_automatic_receipt()` with `no_verify=True` (receipt.py:230) | HIGH | Change no_verify default and show a VERIFIED receipt |
| **The two-phase completion model is partially implemented** | Phase 1 (declaration) exists; Phase 2 (verification) exists; the connecting gate is advisory | HIGH | Show that `/task done --verify` writes VERIFIED receipts (it can, so this is party verified) |
| **Conflict #867 resolves to completed** | Forward lifecycle (in_progress→completed is forward); no receipt exists to override | MEDIUM | Find a VERIFIED receipt for #867 showing in_progress was correct |
| **No `verified` status in task_tracker files** | Grep task_tracker JSON files for "verified" — only "pending", "in_progress", "completed" exist | MEDIUM | Find a task_tracker file with "verified" in its status field |

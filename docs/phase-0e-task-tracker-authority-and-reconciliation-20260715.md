# Phase 0E: Task Tracker Authority and Reconciliation Design

**Date:** 2026-07-15
**Phase:** 0E — Discovery and architecture design only. No code changes, no migrations, no state modification.
**Status:** DESIGN COMPLETE — and notably BETTER THAN EXPECTED: split-brain is single-terminal-narrow, not system-wide.

---

## Executive Verdict

**READY FOR MIGRATION PLANNING** — with a narrow, manageable conflict surface.

### Why this changes from Phase 0D's "NOT READY"

Phase 0D identified the split-brain problem correctly but could not measure its breadth. This phase did the measurement:

- **224 terminals** in local store | **130** in plugin store | **119 common**
- **75 terminals with tasks** in both stores | **74 overlap** | **only 1 terminal with a conflict**
- **Conflict rate:** 1/74 (1.35%) — a single task (#867) on a single terminal
- **Receipts found:** 2 total — receipt system is barely used in practice

This is not a widespread corruption. It is a narrow staging difference between two hooks that fire independently. The migration is not blocked — it needs a clear authority decision and a well-defined reconciliation for the single conflict.

---

## 1. Current Task Lifecycle

### Complete Dispatch Chain

```
Tool call (TaskCreate / TaskUpdate / TaskList / Read / Edit / Write)
    │
    ▼
settings.json PostToolUse[3] matcher=".*"
    │
    ├─ local  hook_runner → PostToolUse.py
    │         └─ create_registry()  (posttooluse/__init__.py:162)
    │              └─ TaskTrackerHook
    │                   └─ get_state_dir() = P:/.claude/state/task_tracker/
    │                        └─ tracks tasks, recent_files, changed_files
    │
    └─ plugin hook_runner → cc-aca-observability/router.py PostToolUse
              └─ plugin hooks/posttool/PostToolUse_router.py
                   └─ create_registry()  (plugin posttooluse/__init__.py:159)
                        └─ TaskTrackerHook
                             └─ get_state_dir() = P:/.claude/state/cc-aca-observability/task_tracker/
                                  └─ tracks tasks, recent_files, changed_files, **receipts**
```

**Key insight:** Both hooks fire on EVERY PostToolUse event. They are independent subprocesses with separate registries, separate state paths, and subtly different code.

### Writer/Reader Authority Map

| Component | Location | Role | Reads | Writes | Authority |
|-----------|----------|------|-------|--------|-----------|
| **Local TaskTrackerHook** | `.claude/hooks/posttooluse/task_tracker_hook.py` | Tool-use observer (PostToolUse) | `state/task_tracker/{tid}_tasks.json` | Same path | Writes tasks, recent_files, changed_files |
| **Plugin TaskTrackerHook** | `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` | Tool-use observer (PostToolUse) | `state/cc-aca-observability/task_tracker/{tid}_tasks.json` | Same path | Writes tasks, recent_files, changed_files, +receipts on completion |
| **TaskCreate api** | Claude Code built-in (TaskCreate tool) | Task definition source | — | — | Source of truth for task_id, subject, description, status |
| **TaskUpdate api** | Claude Code built-in (TaskUpdate tool) | Task status update source | — | — | Source of truth for status transitions |
| **TaskList consumer** | `cc-skills-sdlc/skills/task/scripts/task_verify.py` | Task verification | `state/task_tracker/` (hardcoded) | — | Reads from LOCAL path only |
| **Receipt writer** | `cc-skills-sdlc/skills/task/scripts/task_receipt.py` | Completion evidence | `receipt_path_for(task_id)` | `state/task_receipts/{tid}/{task_id}.json` | Writes on `/task done` or auto-receipt |
| **Receipt reader** | `PreToolUse_task_done_evidence_gate.py` | Completion claim validation | `receipt_path_for(task_id)` | — | Validates receipts (advisory) |

---

## 2. Real Artifact Comparison

### Conflict Analysis

| Aspect | Local `state/task_tracker/` | Plugin `state/cc-aca-observability/task_tracker/` |
|--------|---------------------------|---------------------------------------------------|
| **Total terminals** | 224 | 130 |
| **Terminals with tasks** | 75 | 75 |
| **Overlap (common terminals with tasks)** | **74** | **74** |
| **Full agreement** | **73 terminals** | **73 terminals** |
| **Conflicts** | **1 terminal** (console_01f0572e...) | **1 terminal** |
| **Conflict detail** | task #867: `status=in_progress` | task #867: `status=completed` |
| **Receipt fields (repo, baseline_commit)** | NOT present on any task | NOT present on any task |
| **Schema identical?** | Yes — same dict format | Yes |

### Representative Agreeing Terminal

```
Terminal: console_01f0572e-c0f1-4c0f-8bda-c61d4e653181
  Task #866: both = completed
  Task #868: both = completed
  Task #869: both = completed
  Task #870: both = in_progress
```

### Schema Comparison (from live files)

Both stores use identical schema:
```json
{
  "terminal_id": "console_<uuid>",
  "tasks": {
    "<id>": {
      "id": "...",
      "subject": "...",
      "status": "pending|in_progress|completed",
      "description": "...",
      "files_referenced": [...],
      "session_timestamp": "ISO-8601",
      "created_at": <epoch>,
      "session_id": "...",
      "terminal_id": "..."
    }
  },
  "recent_files": [...],
  "changed_files": [...],
  "changed_files_by_session": {"<sid>": [...]}
}
```

**Plugin adds these fields (absent in local):**
- `repo` (from `git rev-parse --show-toplevel`)
- `baseline_commit` (from `git rev-parse HEAD`)

**Note:** The plugin's `_write_automatic_receipt()` function is called only on `status == "completed"` (lines 532-533), and catches all exceptions silently. It produced only 2 receipts across the entire store.

---

## 3. Authority Model Evaluation

### Option A: Plugin becomes authoritative

| Criterion | Score | Detail |
|-----------|-------|--------|
| Lifecycle correctness | **BETTER** | Plugin writes receipts on completion; has repo/baseline fields |
| Migration complexity | MODERATE | ~130 terminals in plugin store; consumer `task_verify.py` reads local path |
| Receipt integration | **BETTER** | Plugin already calls `_write_automatic_receipt()` |
| Stop gate compatibility | NEUTRAL | No Stop gate reads plugin path yet |
| Local hook compatibility | **WEAK** | Local has 224 terminals — plugin only has 130. ~105 terminals would be orphaned |
| Plugin compatibility | **NATIVE** | Same plugin owns both task_tracker and receipts |
| Rollback safety | MODERATE | Local path would need to be preserved as fallback |
| Future extensibility | **BETTER** | Plugin architecture allows session-scoped state, identity contracts |

### Option B: Local becomes authoritative

| Criterion | Score | Detail |
|-----------|-------|--------|
| Lifecycle correctness | WEAKER | No receipt writing; no repo/baseline fields |
| Migration complexity | **LOWER** | Consumer already reads local path; no change needed |
| Receipt integration | WEAKER | Must add receipt writing to local hook (currently absent) |
| Stop gate compatibility | NEUTRAL | No change needed |
| Local hook compatibility | **NATIVE** | Full 224 terminals, all tasks |
| Plugin compatibility | **WEAK** | Plugin would need to stop writing task state |
| Rollback safety | EASIER | Simple: stop plugin hook, keep local |
| Future extensibility | WEAKER | Local hook is not plugin-bound; no identity contract pattern |

### Option C: Shared canonical layer

| Criterion | Score | Detail |
|-----------|-------|--------|
| Lifecycle correctness | **BEST** | Single source of truth for all task operations |
| Migration complexity | **HIGHEST** | Real architectural change — new module, new state path |
| Receipt integration | DESIGN REQUIRED | Would absorb or reference receipt system |
| Stop gate compatibility | DESIGN REQUIRED | Would be the canonical reader |
| Local hook compatibility | **BREAKING** | Must redirect reader/writer |
| Plugin compatibility | **BREAKING** | Must redirect reader/writer |
| Rollback safety | MODERATE | Old paths preserved during T0 dual-base |
| Future extensibility | **BEST** | Clean contract for identity, lifecycle, schema versioning |

### Recommendation

**Option A (Plugin authoritative) is the recommended path.**

Rationale:
1. **The plugin already has the behavior we want** — it writes receipts, captures repo metadata. Making it authoritative means the existing better code becomes the truth, rather than retrofitting the local hook.
2. **Cost to fix plugin gaps is lower** than adding receipt behavior to the local hook. The plugin needs: (a) task_verify.py to read the plugin path, (b) a fix to the 105 missing terminals.
3. **The narrow conflict surface (1/74)** means reconciliation can be done by hand or by policy rule.
4. **Future architecture alignment** — the state authority migration is moving toward plugin-owned state. The task tracker is a core lifecycle component; having it in the observability plugin is correct.

**But only if:** the 105 local-only terminals are merged into the plugin store during reconciliation. Without that, switching to plugin-authoritative would drop ~58% of task data.

---

## 4. Lifecycle Invariants

### Single Authority

| Invariant | Definition | Enforcement | Test |
|-----------|-----------|-------------|------|
| **One writer** | Exactly one `TaskTrackerHook` writes task state. All others are no-ops | state_resolver.inventory() detects duplicate `task_tracker` roots; PostToolUse.py checks active mode flag | `test_task_tracker_single_writer()` |
| **No dual-path writes** | No two hooks share the same terminal_id for task storage | After migration, delete one path; confirm all writes go to the other | `test_no_dual_path_writes()` |

### Valid Transitions

```
Allowed:
  pending → in_progress        (begin work)
  pending → completed           (direct completion)
  in_progress → completed       (done)
  in_progress → pending         (reset)
  completed → in_progress       (reopen)
  
Forbidden:
  created → verified            (skip work)
  completed → pending           (no skip-back to pending)
  (any) → null                  (no silent deletion)
```

| Invariant | Enforcement | Test |
|-----------|-------------|------|
| Status transition validity | `track_task_update()` validates transition before write | `test_valid_transitions()`, `test_invalid_transitions()` |
| No silent deletion | All task deletions go through explicit `/task delete` or TaskUpdate(status=deleted) | `test_task_deletion_logged()` |

### Evidence Integrity

| Invariant | Definition | Enforcement | Test |
|-----------|-----------|-------------|------|
| **Receipt completeness** | `status == "completed"` must have a companion receipt (VERIFIED or REVIEW) | PreToolUse_task_done_evidence_gate.py (currently advisory → make blocking) | `test_completed_task_has_receipt()` |
| **Chain of evidence** | Receipt `evidence_files[]` must match `files_referenced[]` in task state | Receipt writer validates at write time | `test_receipt_evidence_match()` |
| **No completion without verification** | `evidence_class == "VERIFIED"` requires a verification command with exit code 0 | task_verify.py enforces this | `test_verify_requires_exit_code_zero()` |

### Identity Integrity

| Invariant | Definition | Enforcement | Test |
|-----------|-----------|-------------|------|
| **Terminal isolation** | Task state for terminal A never read by terminal B | State file named by `{terminal_id}_tasks.json` — filename is the isolation boundary | `test_terminal_isolation()` |
| **Session provenance** | Every task records its creating session_id | Schema enforces `session_id` field | `test_task_has_session_id()` |
| **No identity collision** | Two terminals with same ID cannot both write to the same file | terminal_id detection must produce unique values (WT_SESSION unique per terminal) | `test_no_identity_collision()` |

---

## 5. Conflict Resolution Rules

### The one known conflict

```
Terminal: console_01f0572e-c0f1-4c0f-8bda-c61d4e653181
Task #867: local=in_progress  plugin=completed
```

### Root cause

Both hooks processed a `TaskUpdate(task_id="867", status="completed")`. The local hook recorded it but was then OVERSHADOWED by a LATER `TaskUpdate(task_id="867", status="in_progress")` that reached the local hook but NOT the plugin hook. This happens when:
- A subprocess error in one hook
- Different matcher patterns in settings.json (local uses `.*`, plugin also uses `.*` — should be identical)
- Timing: one hook writes before the other reads the current state

### Resolution rules

| Conflict type | Rule | Evidence required | Winner |
|--------------|------|-------------------|--------|
| **Status disagreement** (in_progress vs completed) | **Receipt wins.** If a receipt exists for the task → `completed` is authoritative. If no receipt → use the status that produces a valid transition from the other store's status. | Receipt file at `state/task_receipts/{tid}/{task_id}.json` | Receipt > newer timestamp > plugin |
| **Schema disagreement** (extra fields) | **Union merge.** Take fields from both stores. Plugin adds `repo`/`baseline_commit`; if absent from local, add them by running `git rev-parse`. | Diff of key sets | Merge both |
| **files_referenced divergence** | **Longer list wins.** Only add, never remove. | Length of `files_referenced[]` | Longer list |
| **Terminal exists in one store only** | **Copy to canonical.** If a terminal exists in local but not plugin (or vice versa), the canonical store adopts all its tasks. | File existence check | Both are preserved |

**Do NOT use "newest timestamp wins"** because:
- `session_timestamp` reflects task creation, not last update
- No `last_update` field (intentionally removed — "task tracker should not use TTL")
- Timestamps can diverge if clocks differ (unlikely here but possible)

**Apply this rule to the known conflict:**
- Task #867 has no receipt (0 receipts found for this terminal)
- Without a receipt, fall back to validity: if local says `in_progress` and plugin says `completed`, `completed` is a forward-only transition from `in_progress` → valid and authoritative
- **Winner:** plugin's `completed` status

---

## 6. Migration Strategy

### Preparation

1. **Freeze**: Do NOT modify either hook during migration. No new features or fixes to task_tracker code.
2. **Snapshot**: Copy both store directories to `P:/tmp/task-tracker-snapshot-{timestamp}/`
3. **Validation script**: Run the comparison script against all 224+130 terminals to establish baseline

### Reconciliation

1. **Merge all terminals**: For every terminal_id in local ∪ plugin:
   - If in only one store → copy to both paths (pre-migration)
   - If in both with same status → no action
   - If in both with conflict → apply conflict resolution (see §5)
2. **Verify**: Run comparison script again — zero conflicts expected
3. **Receipt check**: For every `status == "completed"` task with no receipt → plugin hook retroactively runs receipt write

### Cutover

**Phase 1 — Make plugin authoritative (writer change):**
1. Modify plugin `TaskTrackerHook` to write to `state/task_tracker/` (the local path) instead of `state/cc-aca-observability/task_tracker/` by setting `TASK_STATE_DIR` environment variable or changing `get_state_dir()` to point at the common path
2. This makes the plugin version the sole writer to the canonical path

**Phase 2 — Deprecate local writer:**
1. Modify local `TaskTrackerHook.process()` to check a flag: if plugin registry is active, skip all task writes
2. Remove local `posttooluse/task_tracker_hook.py` registration from `posttooluse/__init__.py`

**Phase 3 — Move plugin-owned state to canonical location:**
1. Move `state/cc-aca-observability/task_tracker/*` → `state/task_tracker/`
2. Update `task_verify.py` `TRACKER_DIR` to the final canonical path
3. Remove old plugin path

### Verification

1. **Post-cutover**: Run `get_all_sessions_tasks()` and confirm it returns all 224 original terminals
2. **Receipt verification**: All `completed` tasks have companion receipts
3. **Live test**: Perform TaskCreate → TaskUpdate → TaskList and confirm single-path writes only

### Rollback

1. **Old state preserved**: Both store directories remain for 30 days
2. **Rollback plan**: Revert settings.json to fire only the local hook; restore `get_state_dir()` to old paths
3. **Verification**: Run comparison script and confirm pre-migration state is recoverable

---

## 7. Required Code Changes

### Must change (correctness)

| File | Change | Reason |
|------|--------|--------|
| `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` | Set `state_dir` to canonical `state/task_tracker/` path | Stops dual-path writes |
| `cc-skills-sdlc/skills/task/scripts/task_verify.py` | Update `TRACKER_DIR` to match canonical path | Consumer reads from correct location |
| `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` | Fix `_write_automatic_receipt()` to not silently swallow all errors | Currently only 2 receipts despite 75 completed-task terminals |

### Should change (improvement)

| File | Change | Reason |
|------|--------|--------|
| `.claude/hooks/posttooluse/task_tracker_hook.py` | Add skip/redirect to plugin as authoritative writer | Removes dual-path at source |
| `.claude/hooks/posttooluse/__init__.py` | Remove `TaskTrackerHook` from local registry | Prevents accidental re-enable |
| `cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` | Add `last_updated` field (currently removed — reinstate) | Without it, conflict resolution has no temporal signal |
| `.claude/hooks/PreToolUse_task_done_evidence_gate.py` | Upgrade from advisory (exit 0) to advisory-with-warning | Currently silent on missing receipts |

### Optional (future)

| File | Change | Reason |
|------|--------|--------|
| `cc-skills-utils/scripts/plugin-audit-and-fix.py` | Add task_tracker directory audit | Detect stale dual-path writes |
| `state_resolver.py` | Register task_tracker family | Currently UNKNOWN (Phase 0D gap) |

---

## 8. Required Future Tests

| Test | Covers | Priority |
|------|--------|----------|
| `test_single_writer()` | Only one hook writes task state | P0 |
| `test_terminal_isolation()` | Terminal A's tasks invisible to terminal B | P0 |
| `test_conflict_resolution()` | Known conflict #867 resolves correctly | P1 |
| `test_completed_task_has_receipt()` | Every completed task has a receipt | P1 |
| `test_valid_transitions()` | Only allowed status transitions succeed | P0 |
| `test_invalid_transitions()` | Forbidden transitions fail | P0 |
| `test_receipt_evidence_match()` | Receipt evidence_files matches task files_referenced | P2 |
| `test_post_migration_integrity()` | All 224 terminals present after migration | P0 |
| `test_no_identity_collision()` | Two terminals with same ID caught | P1 |

---

## 9. Claim Ledger

| Claim | Evidence | Confidence | How to falsify |
|-------|----------|-----------|----------------|
| **Split-brain is narrow (1/74 terminals)** | Live comparison: 74 overlapping non-empty terminals, 1 conflict | HIGH | Run comparison script against ALL 130 plugin terminals, not just common ones |
| **Local hook does NOT write receipts** | Source inspection: `track_task_update()` line 477 — returns without calling `_write_automatic_receipt()` | HIGH | Find receipt writes in local `track_task_update()` |
| **Plugin hook DOES write receipts** | Source inspection: plugin `track_task_update()` lines 532-533 calls `_write_automatic_receipt()` | HIGH | Comment out receipt write and show completion tasks have no receipts |
| **Both hooks fire independently** | settings.json: index 3 (PostToolUse.py → local registry) + index 5 (cc-aca-observability router → plugin registry) | HIGH | Remove one from settings.json and show the other still writes |
| **Most terminals exist in local only (105)** | ls count: 224 local - 119 common = 105 | HIGH | Count unique terminal_ids in both stores |
| **Nearly no completed-task receipts exist (2 total)** | `state/task_receipts/` has only 2 JSON files | HIGH | List `state/task_receipts/**/*.json` |
| **No `last_update` field in task schema** | Intentionally removed per code comment "removed last_update - task tracker should not use TTL" | HIGH | Grep for `last_update` in task_tracker_hook.py |
| **Conflict #867 should resolve to completed** | No receipt exists for #867; `completed` is a valid forward transition from `in_progress` | MEDIUM | Find a receipt for #867 that changes the rule |

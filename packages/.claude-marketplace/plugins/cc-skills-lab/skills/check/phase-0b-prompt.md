# Phase 0B.5 — Divergence Snapshot + Phase 0C Foundation Design

---

## Part 1 — Divergence Snapshot

### Artifact inventory

| Artifact | Location | File count | Size | Latest timestamp | Writer |
|---|---|---|---|---|---|
| **task_tracker (local)** | `P:/.claude/state/task_tracker/` | 219 files | 1.9 MB | 2026-07-14T16:23 | `batch_update_tasks.py` (+ hook via plugin path) |
| **task_tracker (plugin)** | `P:/.claude/state/cc-aca-observability/task_tracker/` | 124 files | 1.0 MB | 2026-07-14T16:23 | `task_tracker_hook.py` via `_bootstrap.state_root()` |
| **task receipts** | `P:/.claude/state/task_receipts/` | 2 files | 16 KB | 2026-07-13T13:43 | `task_receipt.py` (cc-skills-sdlc) |
| **plugin observability** | `P:/.claude/state/cc-aca-observability/` | 987 files | 47 MB | 2026-07-14T16:23 | All cc-aca-observability hooks |
| **e2e telemetry** | `P:/.claude/state/` | 2 files | 307 KB | 2026-07-14T16:24 | `PostToolUse_e2e_tracker.py` |
| **skill invocations** | `P:/.claude/state/` | 1 file | 268 KB | 2026-07-14T16:19 | `skill_invocation_logger_hook.py` |
| **shared state** | `P:/.claude/state/shared/` | 7 files | 186 KB | 2026-07-14T16:20 | stop_gate_telemetry, agentic_reliability |
| **terminal-scoped** | `P:/.claude/state/terminals/` | 24 files | 2.6 KB | 2026-07-14T16:27 | state_paths-aware hooks |
| **session-scoped** | `P:/.claude/state/sessions/` | 31 files | 27 KB | 2026-07-14T16:28 | state_paths-aware hooks |
| **investigation plugin** | `P:/.claude/state/cc-aca-investigation/` | 2 files | 50 B | 2026-05-24 | cc-aca-investigation hooks |
| **auto_commit** | `P:/.claude/state/auto_commit/` | 4 files | 350 KB | 2026-07-14T16:20 | auto-commit hook |
| **error signals** | `P:/.claude/state/signals/` | 0 files | 0 B | — | write_tool_error_signal.py |
| **hooks/state/** | `P:/.claude/hooks/state/` | active | ~15 MB | 2026-07-14T16:27 | **STILL ACTIVE** — skill_context, followup_context |
| **hooks/.state/** | `P:/.claude/hooks/.state/` | active | ~30 MB | 2026-07-14T16:27 | **STILL ACTIVE** — tool_use_log |
| **hooks/session_data/** | `P:/.claude/hooks/session_data/` | active | ~157 MB | 2026-07-14T16:27 | **STILL ACTIVE** — evidence.db, verify_before_claim |

### Identity overlap analysis: task tracker

| Metric | Value |
|---|---|
| Local files (JSON) | 219 |
| Plugin files (JSON) | 124 |
| **Overlapping terminal IDs** | **114** |
| Unique to local | 105 |
| Unique to plugin | 10 |
| **Total task entries diverging** | **192** (task-level schema diffs in overlap set) |
| **Session ID diffs** | **192** (every overlapping task has different session_id) |
| Plugin newer (overlap set) | 57 of 114 |
| Local newer (overlap set) | 8 of 114 |
| Tie (<100ms) | 49 of 114 |
| Total tasks local | 1,537 |
| Total tasks plugin | 622 |

**Conflict summary:** Every overlapping terminal has task entries with different `session_id` values between the two locations. The plugin side is the newer writer overall (57 vs 8). 1,105 files exist in only one location — state is fragmented, not merely duplicated.

### Writer authority analysis

| Writer | Path | Active? | Notes |
|---|---|---|---|
| `task_tracker_hook.py` (plugin) | `.../cc-aca-observability/task_tracker/` | **YES** — 4 today | Newer on average (57:8) |
| `batch_update_tasks.py` (local) | `.../task_tracker/` | **YES** — 5 today | Larger total task count (1,537 vs 622) |
| `PostToolUse_e2e_tracker.py` (local) | `.../state/e2e_executions_*.jsonl` | **YES** — 287 lines | `session_id="unknown"` (identity loss) |
| `e2e_tracker_hook.py` (plugin wrapper) | Same as above | **YES** — via Python import | Passes through to local hook — still a reverse dependency |
| Legacy `hooks/state/`, `.state/`, `session_data/` | Under `P:/.claude/hooks/` | **STILL ACTIVE** — mtime within same session window | NOT stale — actively written paths that were never migrated |

---

## Correction: "legacy" directories are not legacy

Phase 0B incorrectly labeled `hooks/state/`, `hooks/.state/`, and `hooks/session_data/` as "legacy" or "stale." This was disproven by fresh inspection:

- mtime `2026-07-14T16:27` — same window as current session state
- `evidence.db` is 157 MB and actively appended
- `tool_use_log_*.jsonl` files are 30 MB and growing
- `skill_context/` and `followup_context/` under `hooks/state/` were written at 16:27

**This changes the migration risk materially.** These are not cold data awaiting cleanup — they are live production paths that must be incorporated into any migration plan, not bypassed.

---

## Part 2 — Corrections to Phase 0C Design

The user's review identified three problems with the initial Phase 0C proposal. These are incorporated below as Part 2.

### Correction 1: Task tracker migration needs reconciliation, not just path mapping

The original design assumed:

```
old path → new path
```

This is wrong. The divergence data shows:

- **192 task-level schema diffs** in the overlap set
- **Every overlapping task has a different session_id** between local and plugin
- **57 of 114** overlapping records have the plugin side newer
- **8 of 114** have the local side newer
- **49 of 114** are within milliseconds

A migration that silently selects one writer discards the other's history. Before any artifact move, the migration plan must include:

**Conflict resolution:**
- Duplicate detection (same terminal_id + same task_id in both paths)
- Winner criteria (newest mtime? most complete record? plugin-side default?)
- Evidence retention (loser record preserved as `.conflict-{uuid}.json`)

**Winner selection criteria (minimum):**
- For identical terminal IDs: compare per-task `session_timestamp` and `created_at`, newest wins
- For records present in only one path: include both (no discard)
- All conflict artifacts retained in a subdirectory: `{canonical_path}/.conflicts/{timestamp}/`
- Selection is deterministic and repeatable (not LLM-judged)

**Migration helper contract (dual-base, not choose-and-lose):**

```python
def reconcile_and_migrate_task_state(
    terminal_id: str,
    local_path: Path,
    plugin_path: Path,
    canonical_dir: Path,
) -> dict:
    """Reconcile divergent task state for one terminal_id.
    
    Returns:
        {merged_count, conflicts_resolved, artifacts_preserved, winner_log[]}
    
    Algorithm:
    1. Read both files.
    2. For each task_id present in BOTH:
       a. Compare session_timestamp (or created_at if one missing).
       b. Newer wins. Older preserved as .conflicts/{uuid}/loser.json.
       c. Log the decision with both timestamps.
    3. For each task_id present in ONLY ONE:
       a. Include as-is (no conflict, no discard).
    4. Write merged result to canonical_dir/{terminal_id}_tasks.json.
    5. Write conflict audit to canonical_dir/.conflicts/{timestamp}/.
    """
```

This does not run during Phase 0C — it is defined as a migration helper, ready for Phase 1.

---

### Correction 2: Plugin namespace — flat vs nested comparison

The original proposal chose `plugins/{plugin_name}/` under state root. The user correctly identified this as "another migration" from the current `cc-aca-observability/` layout.

**Current path:**
```
P:/.claude/state/cc-aca-observability/
```

**Option 1 (flat — keep current namespace shape):**
```
P:/.claude/state/cc-aca-observability/
P:/.claude/state/cc-skills-sdlc/
P:/.claude/state/cc-aca-investigation/
```

**Option 2 (nested — group under plugins/ subdir):**
```
P:/.claude/state/plugins/cc-aca-observability/
P:/.claude/state/plugins/cc-skills-sdlc/
P:/.claude/state/plugins/cc-aca-investigation/
```

Comparison:

| Criterion | Option 1 (flat) | Option 2 (nested) |
|---|---|---|
| Consumer code changes | **Minimal** — path stays same shape. `_bootstrap.state_root()` → `state_paths.get_plugin_state_dir()` = internal implementation change only, file paths unchanged | **Every path string changes** — `cc-aca-observability` → `plugins/cc-aca-observability`. All hardcoded paths break. |
| Filesystem impact | **None** — current directories stay where they are | **Copy/move required** — existing state must move under `plugins/` |
| Migration complexity | **Low** — resolver changes in code, state tree stays in place | **High** — resolver + file tree both move |
| Rollback safety | **High** — consumer can revert import; state tree untouched | **Medium** — if files move, rollback must clean up or leave ghosts |
| Clarity of ownership | **Good** — naming convention signals plugin ownership | **Better** — explicit `plugins/` namespace is unambiguous |
| Future-proofing | **Adequate** — convention-based; new plugins follow naming convention | **Strong** — structural enforcement; plugins literally live in `plugins/` |
| Collision with non-plugin subdirs | **Exists** — `signals/`, `shared/`, `shared/`, `sessions/` are at same level. Future hardcoded path to `state/<artifact>/` could collide with a plugin named "signals" | **None** — all plugins under `plugins/`, no collision with structural subdirs |

**Recommendation: Option 1 (flat) for Phase 1 migration, Option 2 (nested) as a future hardening step.**

Rationale:
- The migration from `cc-aca-observability/task_tracker/` to the canonical path is already risky (114 overlapping terminal IDs, 192 conflicting records). Adding a directory restructure on top compounds that risk.
- Phase 1 can adopt the resolver (import change) without moving files. The resolver's job is to map `plugin_name` to a path — that path can be flat or nested. The migration can flip from flat to nested in a later phase with a dual-base reader.
- Option 1 is backward-compatible with the current on-disk layout. Option 2 requires a file move — which means a migration window, potential data loss if interrupted, and a rollback plan.
- Option 1 does not preclude Option 2. The resolver abstraction makes the path structure an implementation detail.

**Phase 0C resolver API (namespace-agnostic):**

```python
def get_plugin_state_dir(plugin_name: str) -> Path:
    """Returns {STATE_ROOT}/{plugin_name}/
    
    Currently flat (no /plugins/ prefix). Future: if /plugins/ prefix
    is added, this function changes once and all consumers are unaffected.
    """
```

---

### Correction 3: e2e_tracker reverse dependency in Phase 0C acceptance criteria

The original proposal deferred e2e_tracker extraction to Phase 2. The user correctly identifies this is still an open reverse dependency from Phase 0A's incomplete extraction.

**Current state:**
```
cc-aca-observability/__lib/posttooluse/e2e_tracker_hook.py
    line 16: from PostToolUse_e2e_tracker import post_tool_use_hook
```
This is a direct Python import of a local hook module — the same pattern Phase 0A removed for artifact_access_tracker.

**Plan:** Include e2e_tracker extraction in Phase 1 (alongside resolver adoption), not deferred to Phase 2. The approach mirrors Phase 0A's artifact_access_tracker extraction: extract the shared protocol into a standalone module, import from that instead.

**Phasing update:**

| Phase | Scope | What |
|---|---|---|
| 0C | Resolver primitives | state_paths.py extensions only |
| 1 | Consumer adoption + e2e extraction | Plugin consumers adopt resolver; e2e_tracker reverse dependency removed |
| 2 | Hardened paths | Remaining hardcoded paths, legacy dir alignment |
| 3 | State reconciliation | Task tracker conflict resolution + dedup |

---

## Phase 0C Implementation Prompt

The following is the consolidated Phase 0C implementation prompt incorporating these three corrections.

```text id="b3k5q1"
Implement Phase 0C only: extend the canonical state resolver.

Do not migrate consumers yet.
Do not move existing state.
Do not change writers.
Do not delete legacy paths.

Phase 0B.5 findings:

- State divergence is confirmed (114 overlapping terminal IDs, 192 conflicting tasks).
- Legacy hooks/state, hooks/.state, and hooks/session_data are still active.
- A future migration requires a canonical resolver before moving consumers.
- The e2e_tracker_hook reverse dependency (from PostToolUse_e2e_tracker) remains unresolved.

Goal:

Create the shared resolver foundation only.

Requirements:

1. Extend the existing canonical resolver.

First verify whether P:\.claude\hooks\__lib\state_paths.py is the correct authority.
Do not create a third resolver unless proven necessary.

2. Add additive resolver capabilities:

Required:

- canonical state base resolution;
- plugin namespace support (flat by default — no /plugins/ sub-prefix);
- CSF_STATE_DIR support;
- identity validation;
- migration helper support (dual-base, not choose-and-lose).

3. Preserve existing behavior.

Existing functions must remain compatible:

- get_terminal_state_dir()
- get_session_state_dir()
- get_shared_state_dir()
- migrate_legacy_state_file()
- clear_path_cache()

4. Do not move artifacts.

The following remain untouched:

- P:\.claude\state\task_tracker\
- P:\.claude\state\cc-aca-observability\task_tracker\
- hooks/state/
- hooks/.state/
- session_data/

5. Add tests.

Must prove:

- existing callers still resolve the same paths;
- plugin callers can resolve through the canonical resolver;
- CSF_STATE_DIR precedence is deterministic;
- empty identities fail closed;
- plugin namespaces cannot collide.

6. Add migration helpers only.

If adding old/new path helpers:

They must:
- support reader fallback;
- support writer transition;
- preserve old artifacts;
- not silently select winners (future reconciliation step, not auto-merge).

7. Report:

# Phase 0C Result

- Files changed
- Resolver contract
- Existing behavior preserved
- Tests executed
- Remaining migration blockers (including unresolved e2e_tracker reverse dep and task tracker reconciliation)

Important:

Do not migrate task_tracker yet.
Do not reconcile divergent state yet.
Do not change PostToolUse ownership yet.
Do not introduce a /plugins/ subdirectory prefix.
Do not attempt to resolve the e2e_tracker reverse dependency here.
```

---

## Revised migration roadmap

| Phase | Objective | Key constraint |
|---|---|---|
| **0B.5** (complete) | Snapshot + corrections | No code changes |
| **0C** (next) | Extend state_paths.py with plugin namespace, CSF_STATE_DIR, identity validation, dual-base helpers | No consumer migration, no artifact move, flat namespace |
| **1** | Plugin consumers adopt resolver; e2e_tracker extraction | Dual-base readers; e2e dep removed; no state reconciliation yet |
| **2** | Remaining hardcoded paths; legacy dir alignment | Hardcoded `P:/.claude/state` → resolver; no dedup yet |
| **3** | Task tracker reconciliation | Conflict detection + winner selection + audit retention; this is the final and riskiest phase |

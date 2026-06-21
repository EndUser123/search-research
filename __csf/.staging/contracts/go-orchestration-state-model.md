# /go Orchestration State Model Contracts

## Contract 1: Worktree Lifecycle

**Identity**: `{worktree_path}` — absolute filesystem path to git worktree
**Ordering**: Creation timestamp (`created_at`) determines "newer" vs "older"
**Deduplication**: Two worktrees are duplicates if they share the same `git worktree list` entry path
**Freshness/invalidation**: Worktree is stale if source branch (e.g., `ai/ai-task-{timestamp}`) is deleted or merged
**Source of truth**: `git worktree list` output — authoritative list of all worktrees
**Isolation boundaries**: 
- **Private**: Worktree-specific git index, working directory
- **Shared**: Ref namespace (shared with main repo), git objects (shared via worktree ref)
**Test binding**: Acceptance scenario:
  1. Create worktree via `git worktree add -b "ai/ai-task-{TS}" "{path}" HEAD`
  2. Verify worktree appears in `git worktree list`
  3. Verify worktree has separate `.git` file pointing to `.git/worktrees/{name}`
  4. Delete worktree via `git worktree remove {path}`
  5. Verify worktree no longer appears in `git worktree list`
  6. Orphan detection: run `git worktree prune` and verify stale worktrees are removed

## Contract 2: State Directory Isolation

**Identity**: `{terminal_id}` — unique identifier per terminal session from `$TERMINAL_ID` env var
**Ordering**: Run ID timestamp (`run_id`) determines "newer" vs "older" within a terminal
**Deduplication**: Two state directories are duplicates if they share the same `{terminal_id}`
**Freshness/invalidation**: State directory is stale if terminal session ends (no TTL, manual cleanup required)
**Source of truth**: `.claude/.artifacts/{terminal_id}/go/` filesystem — authoritative location
**Isolation boundaries**:
- **Private**: All artifacts within `{terminal_id}/go/` are terminal-private
- **Shared**: Git repo state (main repo), task queue (`GO_TASKS_FILE` if shared across terminals)
**Test binding**: Acceptance scenario:
  1. Set `TERMINAL_ID=termA` and create artifacts in `.claude/.artifacts/termA/go/`
  2. Set `TERMINAL_ID=termB` and create artifacts in `.claude/.artifacts/termB/go/`
  3. Verify `termA` and `termB` directories contain separate artifacts (no crossover)
  4. Concurrent safety: spawn two terminals with same `TERMINAL_ID`, run `/go` in both, verify no artifact corruption
  5. Verify artifacts follow naming pattern: `{artifact_type}_{run_id}.{ext}` (e.g., `active-task_{run_id}.json`)

## Contract 3: Task Queue Locking

**Identity**: `tasks.json.lock` file — lock sidecar for `GO_TASKS_FILE` (usually `.claude/tasks/tasks.json`)
**Ordering**: Lock file modification time determines freshness
**Deduplication**: N/A — single lock file per queue
**Freshness/invalidation**: Lock is stale if lock file age exceeds `GO_TASK_LOCK_TTL_SECONDS` (default: 3600)
**Source of truth**: Filesystem presence and modification time of `tasks.json.lock`
**Isolation boundaries**:
- **Private**: Lock content (PID, timestamp) — write-locked via `fcntl.lockf` (POSIX) or `msvcrt.locking` (Windows)
- **Shared**: `tasks.json` file — protected by lock, but accessible to all terminals
**Test binding**: Acceptance scenario:
  1. Run two `/go` instances concurrently in separate terminals
  2. First instance acquires lock, writes `tasks.json.lock` with PID and timestamp
  3. Second instance waits for lock or recovers stale lock (TTL exceeded)
  4. Verify only one instance claims a given task at a time (no duplicate `selected` status)
  5. Stale lock recovery: manually age lock file beyond TTL, verify next `/go` invocation recovers it
  6. Crash recovery: kill `/go` process while holding lock, verify lock recovery works

## Contract 4: Task Claiming

**Identity**: `{task_id}` — unique task identifier (e.g., `TASK-001` or `task-04221-1430`)
**Ordering**: `selected_at` timestamp determines claim precedence
**Deduplication**: Two task entries are duplicates if they share the same `{task_id}`
**Freshness/invalidation**: Task claim is stale if `selected` status is not cleared after task completion or max attempts
**Source of truth**: `tasks.json` file for queued tasks, `active-task_{run_id}.json` for active task
**Isolation boundaries**:
- **Private**: `active-task_{run_id}.json` — terminal-private claim artifact
- **Shared**: `tasks.json` entries — shared across terminals, protected by lock
**Status transition invariants**:
1. `ready` → `selected` (atomic mutation under lock, sets `selected_by` and `selected_at`)
2. `selected` → `completed` (after PR artifacts, sets `completed_at`)
3. `selected` → `failed` (after blocking, sets `failed_at` and `reason`)
4. No transition from `completed` back to `ready`
**Test binding**: Acceptance scenario:
  1. Queue two tasks with same `priority: P1` in `tasks.json`
  2. Run `/go` in terminal A, verify it claims first task (status `selected`, `selected_by` = terminal A)
  3. Run `/go` in terminal B, verify it claims second task (not the same task as terminal A)
  4. Verify no two terminals have the same task in `selected` status simultaneously
  5. Atomicity: interrupt claim process mid-mutation, verify no partial state corruption

## Contract 5: Run ID Generation

**Identity**: `{run_id}` — UUID v4 string (e.g., from `uuid.uuid4()`)
**Ordering**: Timestamp embedded in artifact filenames determines chronology (not in UUID itself)
**Deduplication**: Two run IDs are duplicates if they share the same UUID string
**Freshness/invalidation**: Run ID is immutable — never becomes stale
**Source of truth**: `$RUN_ID` env var and artifact filename patterns
**Isolation boundaries**:
- **Private**: All artifacts with same `{run_id}` belong to the same `/go` invocation
- **Shared**: None — run IDs are invocation-private
**Uniqueness guarantee**: UUID v4 collision probability is negligible (≈10^-12 for 1 million IDs)
**Test binding**: Acceptance scenario:
  1. Run `/go` and capture `$RUN_ID` env var
  2. Verify all generated artifacts use same `{run_id}` in filenames
  3. Run `/go` 100 times, verify no duplicate `{run_id}` values
  4. Verify artifact naming pattern: `{artifact_type}_{run_id}.{ext}` (e.g., `dispatch-result_{run_id}.json`)
  5. Resume scenario: rerun `/go` with same `$RUN_ID`, verify artifacts are appended (not overwritten)

---

## Contract Authority

**Authoritative source**: This document is the canonical definition of state-model contracts for `/go` orchestration.
**Consumer contracts**: `scripts/orchestrate.py`, `scripts/select-task.py`, `scripts/verify-task.py`, all gate scripts
**Resolution**: Discrepancies between code behavior and this contract are bugs in the code, not contract updates.

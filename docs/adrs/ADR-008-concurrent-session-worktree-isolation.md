# ADR-008: Concurrent-Session Worktree Isolation

**Date:** 2026-07-11
**Status:** Draft (Layer 1 config + schema extension shipped; coordination layer deferred)
**Decider:** Bruce Thomson

## Context and Problem Statement

This environment runs **multiple concurrent Claude Code sessions across multiple terminals** (typically 10+) against a single repository at `P:\`. The current operational pattern is manual:

1. A human creates N git worktrees ahead of time, each at a numbered path (`P:\.worktrees\external-delegation-terminal-2`, `…-3`, …).
2. Each branch is created off a chosen commit (e.g. `ecd448f`).
3. Each terminal `Set-Location`s into its assigned slot, sets a `CLAUDE_TERMINAL_ID` by hand, and launches `claude --continue`.

This manual protocol is fragile in three ways, each observed in the session that motivated this ADR:

1. **No binding between a terminal and its slot.** Slot numbers are a wiki — people remember which are taken. Nothing enforces the mapping; two terminals can claim the same slot, or nobody claims #7.
2. **Branch names encode the slot, not the task.** `codex/external-delegation-2…10` were empty slots at `ecd448f` with no actual work and no task assignment — stale before use. A branch named for a slot cannot answer "what is this for?"
3. **Recovery state lives outside version control.** Two stashes on the delegation branch carried uncommitted work (`claim_risk_router.py` envelope-aware fix) that was on *no* branch. Sessions accumulate state the manual protocol treats as disposable.

### The core conflict surfaces

| Resource | Conflict mode |
|---|---|
| Git index / staging | Two sessions `git add` against the same index |
| Git HEAD / branch | Two sessions commit on the same branch |
| File writes | Two sessions edit the same file |
| Hook state | Caches/registries keyed by global path vs. session |
| Prompt context | Session A unaware Session B exists |
| `CLAUDE_TERMINAL_ID` | Duplicates make sessions indistinguishable |

### Distinction: git-level vs logical conflicts

The existing Git Destructive Operation Guard (`PreToolUse_destructive_git_guard.py`) and worktree cross-check (`PreToolUse_git_safety.py` + `__lib/worktree_helper.py`) govern *git subcommands* and *cross-worktree git targets* only. The write-lease gate proposed below governs `Edit`/`Write`/`MultiEdit` tool calls producing concurrent logical writes to the same repo-relative path from different worktrees — a case no existing guard covers. These are distinct non-overlapping problems.

### What an initial proposal got wrong

A first-pass design proposed building the entire lifecycle from scratch: a session registry, automatic worktree creation in `SessionStart`, a `/worktree` meta-skill. **This reinvents functionality the Claude Code platform already provides.** Per the "Orchestration Blueprint for Concurrent Claude Code Sessions" (NotebookLM source) and the official `code.claude.com/docs/en/worktrees` reference, the CLI has native worktree support (v2.1.49+):

- `claude --worktree <name>` auto-creates `.claude/worktrees/<name>/` with a `worktree-<name>` branch.
- The CLI handles directory switching, transcript relocation, and `--resume <name>` later.
- `.worktreeinclude` propagates gitignored files (`.env`, certs) into new worktrees.
- `cleanupPeriodDays` auto-prunes idle *subagent* worktrees.
- `isolation: worktree` in agent frontmatter gives ephemeral isolated worktrees to subagents, with `baseRef: fresh` (remote HEAD) or `head` (local).

The native `--worktree` flag replaces steps 2–3 of the manual protocol (worktree creation + directory switch). Steps 4 (setting `CLAUDE_TERMINAL_ID`) and 5 (`--continue` vs `--resume`) are the documented gaps. **The decisive principle: do not build what the platform already provides.** Build only the layers that fill documented capability gaps.

## Decision

Adopt a **two-layer architecture** (the write-lease gate and `/worktree` meta-skill are deferred — see Layer 2a and Rollout):

1. **Native platform layer (config only)** — use `claude --worktree <task-slug>` and `--resume` as the primary session lifecycle. Create `.worktreeinclude` at the repo root. Configure `cleanupPeriodDays`.
2. **Coordination layer (build, gated)** — one hook that fills a gap the platform does not cover:
   - **Session registry** (`SessionStart` / `SessionStop`) — a shared registry so any session can discover who else is active and in which worktree.
   - **Write-lease gate** (`PreToolUse` for `Edit`/`Write`/`MultiEdit`) — **deferred (warn-mode only)** until a real two-session corpus proves the gate is needed despite worktree isolation.

Two principles govern the build, carried over from ADR-007:

1. **Compute, never hand-maintain, with scope.** ADR-007 forbids hand-maintained registries that describe *static architectural relationships* (producer→consumer maps derivable from source). This ADR's session registry records *ephemeral runtime facts* (live session IDs, occupied worktrees) that cannot be derived from source — it is a cache of process state, reaped by heartbeat TTL, not a curated map. The two principles are consistent: never hand-curate what can be computed; do record what cannot be computed any other way.
2. **Use the platform first; extend existing tooling second.** Before building any new coordination primitive, verify that existing infrastructure (`__lib/worktree_helper.py`, `__lib/file_lock_manager.py`, `worktree_safety.py`, existing session registry at `.claude/.artifacts/session_registry.jsonl`) cannot be extended to serve the need.

### Implementation Outcome (2026-07-11)

**What shipped:**
- Layer 1 config: `.worktreeinclude` at repo root, `worktree.baseRef: fresh`, `cleanupPeriodDays: 7`
- Schema extension: `worktree` + `worktree_path` fields added to `snapshot_SessionStart_identity_capture.py` (SessionStart) and `PreCompact_snapshot_capture.py` (compaction), both appending to the existing `session_registry.jsonl`
- Auto-commit worktree guard removed from `cc-skills-utils_Stop_auto_commit.py` — `Stop` event only fires for the main session, so the `is_worktree(cwd)` guard was skipping auto-commit for all `--worktree` sessions unnecessarily

**What was evaluated and deferred (not built):**
- Write-lease PreToolUse gate — deferred to warn-mode per gate-discipline rule; likely redundant under worktree isolation
- `/worktree` meta-skill — not built; `__lib/worktree_helper.py` + `worktree_safety.py` + PowerShell scripts already cover listing and lifecycle
- SessionStop/UserPromptSubmit heartbeat / TTL staleness — removed after review concluded these solve an invented problem (the registry is a historical fact log, not a liveness dashboard)
- Active-sessions query — deferred until a consumer actually needs it
- MCP port allocator — deferred until concurrent bound servers exist

### Capability sourcing

| Capability | Native | Build/gated | Why |
|---|---|---|---|
| Worktree creation | ✅ `--worktree` | — | Already correct |
| Branch from clean baseline | ✅ `baseRef: fresh` | — | Default is `origin/HEAD` |
| Directory switching | ✅ CLI | — | Automatic |
| Transcript relocation | ✅ v2.1.198+ | — | Automatic on enter/exit |
| `--resume` by name | ✅ | — | Name is the session identity |
| Gitignored-file propagation | ✅ `.worktreeinclude` | — | File must be created first |
| Subagent isolation | ✅ `isolation: worktree` | — | Per-agent frontmatter |
| Cleanup (subagents) | ✅ `cleanupPeriodDays` | — | Idle subagent sweep |
| Worktree listing / status | ✅ `__lib/worktree_helper.py` | — | Already exists; `/worktree list` calls this |
| File-level lock primitive | ✅ `__lib/file_lock_manager.py` | — | O_EXCL + stale-reap exists; reuse |
| Worktree lifecycle CLI | ✅ `worktree_safety.py` | — | start/status/cleanup exist; extend with reclaim |
| Session discovery | ❌ | ✅ registry hook | Platform has no cross-session view |
| Write conflict prevention | ❌ | gated lease hook | Deferred to warn-mode; awaits real corpus |
| Cleanup (user worktrees) | ❌ excluded | gated `/worktree prune` | User worktrees exempt from auto-sweep; extend worktree_safety.py |

### Pre-existing infrastructure (must be reused, not duplicated)

This codebase already contains working implementations of several primitives the ADR would need. Every new build must reuse or extend these existing tools before creating a parallel store:

- **`P:/.claude/hooks/__lib/worktree_helper.py`** — `get_current_worktree`, `list_all_worktrees`, `is_cross_worktree_access`, `validate_git_command_for_worktree`.
- **`P:/.claude/hooks/__lib/file_lock_manager.py`** — O_CREAT|O_EXCL atomic claim, age-based stale-reclaim, session-namespace isolation, `cleanup_session_locks` / `cleanup_stale_locks` reapers.
- **`P:/.claude/.artifacts/session_registry.jsonl`** — 1.3MB append-only JSONL, written by `snapshot_SessionStart_identity_capture.py`, consumed by `terminal_detection`, `chs`, `gto`, `recap`, `debrief`, `wiki`. Readable via `session_registry.query_registry()`. This is the canonical session store; new fields extend it.
- **`P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py`** — CLI with `start`, `status`, `cleanup` subcommands; metadata at `{state_dir}/worktree-tasks/{task_id}.json`.
- **`P:/scripts/git/New-ClaudeWorktree.ps1`**, **`Status-AllWorktrees.ps1`**, **`Cleanup-ClaudeWorktrees.ps1`** — PowerShell automation for the worktree lifecycle.
- **`P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/using-git-worktrees/SKILL.md`** — existing skill for worktree guidance.

**Consequence:** a `/worktree` meta-skill is no longer needed. Worktree listing, status, and cleanup are already served. If a CLI gap remains, it is cheaper to extend `worktree_safety.py` with a `reclaim` subcommand than to build a parallel skill.

## Layer 1 — Native platform (one-time config)

### `.worktreeinclude` at `P:\` root

Create this file (it does not exist yet). Gitignored files to copy into every new worktree:

```
.env
.env.local
.env.test
config/ssl/local_cert.crt
```

Only files that are *both* matched and verified gitignored are copied, preventing duplication of tracked assets.

### `worktree.baseRef`

Default `fresh` (branch from `origin/HEAD`) for task-level worktrees. Reserve `head` for subagents that must inherit uncommitted local state. This closes the recovery-state gap that left the `claim_risk_router` fix stranded in a stash: new task worktrees branch from a clean upstream baseline, so uncommitted local noise cannot leak into a task.

**Note on resolution order:** `worktree.baseRef: "fresh"` is set in the global settings file (`C:/Users/brsth/.claude/settings.json`). The project-level file (`P:/.claude/settings.json`) does not have a `worktree` block. If the CLI merges project settings over global, the global `"fresh"` value is inherited. Add `"worktree": { "baseRef": "fresh" }` to `P:/.claude/settings.json` to make the project-level default explicit.

### `cleanupPeriodDays`

Set to `7`. Prunes idle *subagent* worktrees only (user-created worktrees via `--worktree` are exempt by design).

### Naming convention

`<task-slug>` — descriptive, task-oriented. Examples: `fix-login`, `delegation-contract`, `snapshot-cache`. **Not** terminal slot numbers. The slug is the resume key and the branch suffix (`worktree-<task-slug>`); it must answer "what is this for?"

### Auto-commit Stop hook interaction

The existing `cc-skills-utils_Stop_auto_commit.py` (the mechanism that prevents uncommitted-work loss — the same failure the Problem Statement cites) returned early inside worktrees (line 963: `if is_worktree(cwd): return False`). Under this ADR's `--worktree`-primary lifecycle, every task session runs inside a worktree and auto-commit was silently disabled.

**Resolution (2026-07-11):** The `is_worktree` guard was removed. The `Stop` event fires only for the main session — subagent isolation worktrees use `SubagentStop`, a separate dispatch event. There was no scenario where the guard protected against useful work while also blocking auto-commit for user `--worktree` sessions. Verified by inspection of the settings.json dispatch: `Stop` and `SubagentStop` have separate hook entries.

## Layer 2 — Coordination hooks (the build)

### Session registry

**Purpose:** any session can answer "who else is active, and where?"

**A pre-existing append-only JSONL registry** exists at `.claude/.artifacts/session_registry.jsonl` (snapshot plugin, `snapshot_SessionStart_identity_capture.py`). It records historical session appearances for cross-terminal session chaining (`ts`, `terminal_id`, `session_id`, `cwd`). The ADR's registry is a separate concern: it provides per-worktree O_EXCL atomic claim semantics (an append-only log cannot atomically detect duplicate claims). The two registries are complementary — the new one covers coordination, the existing one covers history.

**Design choice:** extend the existing registry entry schema rather than creating a second store. The per-worktree view is a derived projection computed at query time from the append-only log. If a per-worktree file is unavoidable for atomicity, make it a cache of the log with the log as canonical and a reconciliation check on every read. **Do not create a second standalone registry.**

**Extend the existing schema** (add fields to each append-only line):

```json
{
  "ts": "2026-07-11T14:46:35Z",
  "session_id": "<UUID — primary key, never recycled>",
  "terminal_id": "<WT_SESSION-derived — advisory/grouping only>",
  "worktree": "fix-login",
  "worktree_path": "P:\\.claude\\worktrees\\fix-login",
  "pid": 12345,
  "started_at": "2026-07-11T14:46:35Z",
  "last_heartbeat": "2026-07-11T15:02:11Z",
  "cwd": "P:\\.claude\\worktrees\\fix-login"
}
```

**Storage:** append to `.claude/.artifacts/session_registry.jsonl` (existing canonical path, already in `directory_policy.json` allowed subdirectories). No new directory needed.

**Key invariants:**
- **Primary key is `session_id`** (UUID, never recycled), not `terminal_id` (which is shared across concurrent sessions in one Windows Terminal window — see memory `terminal_id_not_per_session.md`). `terminal_id` remains as advisory metadata for grouping.
- **PID is advisory-only metadata.** The reaper does NOT use PID liveness (Windows recycles PIDs in seconds). Reap by heartbeat TTL only.

**`SessionStart` hook:**
1. Derive `terminal_id` from `WT_SESSION` using the existing `terminal_detection.py` library (snapshot plugin). Do not duplicate terminal-detection logic.
2. Resolve the active worktree path from `cwd`.
3. Append a registry entry (open `"a"`, matching the existing snapshot writer pattern). The entry key is `session_id`.
4. The hook must run **after** the snapshot plugin's `snapshot_SessionStart_identity_capture.py` in the SessionStart dispatch sequence (so `terminal_id` is resolved by the canonical library first). Register the hook after snapshot's router in `settings.json` or use the HookImporter ordering.

**`SessionStop` hook:** remove the registry entry. On crash (no SessionStop), the heartbeat TTL reaps it on next session's SessionStart.

**Heartbeat:** append a single JSON line containing timestamp + session_id + worktree to the registry log (append-only, no rewrite). Leave the heartbeat cadence as `UserPromptSubmit` for now; revisit if write amplification is measured to be a problem (at current volume, an append per turn is negligible).

**Crash recovery (Tier 1 — heartbeat TTL):** SessionStart reads existing entries and prunes any whose `last_heartbeat` is older than `REGISTRY_TTL` seconds (default 300). PID is NOT used as a liveness signal. `PID recycling` failure mode is eliminated by design.

**Crash recovery (Tier 2 — O_EXCL claim for the same worktree):** If two sessions try to claim the same worktree, SessionStart reads the last entry for that worktree and checks heartbeat-TTL. If still alive, a new session claiming the same worktree is blocked with a message naming the holder's session_id. If stale, the old entry is pruned and the new session claims the worktree.

### Write-lease gate — DEFERRED to warn-mode

**Status: gated rollout, not shipped block-mode.** Per the standing CLAUDE.md gate-discipline rule ("every new enforcement gate must ship with a `measured_tp_on_corpus` field — real held-out corpus TP/FP — before it can block; a gate that fires 0 real positives stays advisory"), the write-lease gate ships in warn-only mode first.

**Architectural note:** this codebase runs under worktree isolation (native `--worktree`), where each session has its own git index and HEAD. The file-index collision that motivates the write-lease gate ("two agents both rewriting `schemas.py`") is already prevented by git's per-worktree index/HEAD isolation. Under worktree isolation, the same relative path (`packages/foo/schemas.py`) resolves to different physical files in different worktrees. **The write-lease gate is likely redundant with the chosen architecture.** It serves only the narrow case where two sessions legitimately share a single directory (agent-team mode) — a case this ADR explicitly rejected (Alternative B). Until a real two-session corpus demonstrates that worktree isolation still produces logical collisions that the gate would catch, the gate must NOT ship in block mode.

**If the gate is built (warn-mode only):**

**Storage:** `.claude/.artifacts/write-leases/` (under `.artifacts/` — already in `directory_policy.json` allowed subdirectories). Add `"purpose": "Per-file write lease locks — ADR-008 concurrent session isolation"` to directory_policy.json.

**Reuse existing FileLock primitive** from `cc-aca-epistemic/__lib/file_lock.py` for the lock mechanism; layer sha256-key + TTL semantics on top. Do not introduce a second locking library.

**Lease key:** hash over the **absolute path including worktree root**, so that two worktrees editing the same relative path do NOT collide (they are editing different physical files). Under worktree isolation, collision on absolute path is extremely rare — this is intentional and correct (the gate is only needed when two sessions somehow share a directory despite worktree isolation).

**`PreToolUse` gate** (matcher `^(?:Edit|Write|MultiEdit)$` — use non-capturing group, matching settings.json convention):

1. Compute the target file path from the tool input as an **absolute path**.
2. Check for an existing lease. If held by another *live* session, emit a WARN-level log entry (do NOT block in warn mode). Record the event for calibration.
3. If no lease or lease is expired/stale, acquire one with a TTL of 300s, refreshed on each edit by the same session via heartbeat.
4. On lease acquisition, capture `sha256(file_content_at_acquisition)` and the file's `mtime+size`. On each subsequent PreToolUse, re-compare the on-disk content hash against the captured value. If changed (lost-update: another session wrote this file while the lease was held, OR the TTL expired and another session wrote), log a CORRECTNESS INCIDENT and refuse the write. This handles the crash-resume / TTL-expiry / lost-update class of failure.
5. **Reaper:** lazy reap-on-acquire (pre-flight check: unlink any lease whose `ttl_expires < now` before deciding block/allow) + eager sweep on SessionStart (remove all expired leases under `.artifacts/write-leases/`). Reuse `file_lock_manager.cleanup_stale_locks()` as the implementation — do not re-derive.

**MultiEdit handling:** pre-flight, compute the full target-file set from `tool_input.edits[]` BEFORE acquiring any lease. Check+acquire ALL leases. If any acquisition fails, release all leases acquired so far and block the whole MultiEdit with a reason naming the contested file. Never partially proceed.

**Scope:** tracked source files only. Exempt: `.claude/` state/logs/artifacts (driven by `directory_policy.json` allowlists, not duplicated in gate code), and all `__lib/` shared-helper paths (global and per-plugin) — these are coordination primitives and shared-library refactor surfaces where concurrent edits across worktrees are the intended workflow, not a conflict.

**Blocking format (warn mode only; if/when rolled to block):**

Emit on stdout, exit 0:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "lease held by session <id> in worktree <wt>; expires <ts>"
  }
}
```
Do NOT exit 2 — the `hookSpecificOutput` JSON on stdout with exit 0 is the documented PreToolUse block contract for router-hosted gates (matches `cc-skills-utils_PreToolUse_dispatch_invariant.py:53-61`). A router inspects the JSON field, not the exit code. Exit 2 is an alternative for independently-registered hooks (not under a router) but produces the legacy `{"decision":"block"}` format that drops `reason` from model visibility.

**Known failure mode (deliberately not solved in warn mode):** two sessions making *logically* conflicting changes to *different* files (A adds a field, B deletes its only consumer). This is a design-level conflict, not a write-level one. ADR-007's contract-and-value review is the answer there, not this gate.

### MCP port allocator (deferred)

Multiple worktrees running web servers or MCP servers all try to bind the same default port (e.g. 3000). The blueprint (§4 "Known Edge Cases") calls this out. Fix: derive a deterministic port offset from the worktree path hash and inject into `settings.local.json`. **Deferred** until this environment actually runs multiple bound servers concurrently — do not build ahead of need (Ponytail: YAGNI). Currently verified: zero bound MCP servers exist in any settings file. When implemented, add `settings.local.json` write permission to directory_policy.json if not already present.

## Layer 3 — not built (existing tooling covers it)

The `/worktree meta-skill` proposed in the first draft of this ADR is **not built**. The following already exist:

- **Listing:** `__lib/worktree_helper.list_all_worktrees()` — call from `/go` or any orchestrator.
- **Status:** `worktree_safety.py status` — shows active worktrees with git state.
- **Cleanup:** `worktree_safety.py cleanup` — dry-run or `--remove` stale worktrees.
- **Creation:** `claude --worktree <task-slug>` (native) or `New-ClaudeWorktree.ps1`.

If a gap is found after deployment, the cheapest fix is to extend `worktree_safety.py` with a `reclaim` subcommand (claim orphaned worktree after dead session) — not a new skill.

## Rollout

The write-lease gate follows a phased rollout, modeled on ADR-007:

**Phase 1 — Warn mode (target: immediate):**
- Ship the session registry in append-only mode (extend existing JSONL schema).
- Ship the write-lease gate in warn-only mode: log all events that *would* have blocked, emit advisory messages, never exit non-zero. No decision block.
- Run for at least 2 weeks of concurrent-session usage.
- Collect `measured_tp_on_corpus: {tp: N, fp: M, corpus: "<session-pair description>"}` — saved to the gate config source.

**Phase 2 — Calibrate (target: after Phase 1 corpus collected):**
- Measure overfire rate on shared `__lib/` and `.claude/` paths.
- Tune the `__lib/` exemption — the smallest exemption set that avoids FP on normal shared-helper edits.
- Tune the lease TTL and heartbeat cadence against observed pause durations.
- File any calibration findings against the gate-discipline corpus.

**Phase 3 — Block mode (target: contingent on Phase 2):**
- Flip to block mode only if Phase 1 corpus shows the gate would have caught at least one real collision that caused loss or rework.
- If the corpus shows the gate *never* would have blocked under worktree isolation (expected outcome — the architecture likely makes the gate redundant), leave the gate at warn mode permanently and document the finding. Do not flip to block.
- Re-verify every 6 months as the environment evolves.

**If the gate is never flipped to block:** document the negative finding in the References section. The session registry alone proves sufficient for concurrent-session ops visibility.

## Dispatch wiring

The ADR does not dictate the hook dispatch path; it must be decided before implementation. This environment has two valid paths and they are mutually exclusive per the dispatch invariant:

| Path | Registration | When |
|---|---|---|
| **Local** (`P:/.claude/hooks/`) | Direct entry in `P:/.claude/settings.json` `hooks` block | Simpler, no plugin machinery. Use for project-local hooks. |
| **Plugin** (under `packages/`) | `__lib/router.py` DISPATCH dict; `hooks.json` stays `{"hooks": {}}` | Required if hook logic is shared across projects or needs versioned releases. |

The dispatch-invariant `PreToolUse` gate (`cc-skills-utils_PreToolUse_dispatch_invariant.py`) will block any attempt to add dispatch entries to a plugin `hooks.json` whose plugin already has `__lib/router.py`. Wire new hooks by editing the router's DISPATCH dict, not hooks.json.

**Ordering for PreToolUse matcher `^(?:Edit|Write|MultiEdit)$`:** the write-lease gate must execute BEFORE any edit-content or authorization gates that run on the same matcher. Register it as the FIRST hook in that matcher group in `P:/.claude/settings.json`.

**Ordering for SessionStart:** the new registry hook must run AFTER the snapshot plugin's `snapshot_SessionStart_identity_capture.py` so that `terminal_detection.py` has resolved `terminal_id` first.

## Plugin Mutation Checklist

If any portion of Layer 2 ships as a plugin (not project-local hooks), the global Plugin Mutation Checklist applies:
1. Dispatch wiring (router.py or settings.json, not both)
2. Version bump (`plugin.json` version incremented)
3. Cache rebuild (`plugin-audit-and-fix.py --bump <plugin-name>`)
4. Enablement (new plugins only: add `"<name>@local": true` to `enabledPlugins` in `~/.claude/settings.json`)
5. Runtime /verify smoke
6. Commit-scope verification (`git status --short` before commit)

The `/worktree` meta-skill is not built (existing tooling suffices), so this checklist does not apply to Layer 3.

## Alternatives Considered

### A. Build everything from scratch (rejected)

A session registry + automatic worktree creation in `SessionStart` + a `/worktree` skill, ignoring the native `--worktree` flag. **Rejected:** reinvents platform functionality, drifts from upstream as the CLI evolves, and duplicates the transcript-relocation and `.worktreeinclude` machinery. The first-pass proposal in this session was exactly this; it was wrong.

### B. Agent teams instead of worktrees (rejected for this use case)

The blueprint's "Agent Teams" model: teammates share a single directory, coordinate via a shared mailbox, no file isolation. Faster coordination, but high collision risk. **Rejected** for this environment because the failure mode that motivated this ADR *was* file/index collision. Agent teams suit tightly-coupled subtasks; this environment runs independent parallel tasks. Worktree isolation is the correct trade-off here.

### C. GitButler / virtual worktrees (rejected)

Trigger.dev (cited in the blueprint) reports ditching worktrees for GitButler's virtual-branch model. **Rejected:** changes the VCS workflow fundamentally, adds a dependency, and the native `--worktree` flag already gives us what we need without it. Worth monitoring, not adopting.

### D. Status quo — manual protocol (rejected)

The current 5-step manual setup. **Rejected** for the three fragility reasons in the Problem Statement. This ADR exists because the status quo lost work (the stranded stash) and created empty slots with no binding.

### E. Extend existing worktree tooling (considered; replaces Layers 2b and 3)

The preferred alternative after adversarial review. Instead of building a new `/worktree` meta-skill and a write-lease gate from scratch, extend the existing `worktree_safety.py` (with a `reclaim` subcommand) and `worktree_helper.py` (with a `list_active_sessions` view that joins git worktree list + session registry). This is the default implementation path — see Layer 3 decision above.

## Consequences

**Positive:**
- One command (`claude --worktree <task>`) replaces a 5-step manual protocol per terminal.
- Task names replace slot numbers — branches answer "what is this for?"
- Session registry gives ops visibility across 10+ terminals by extending the existing store (no new infrastructure).
- Recovery state lives in worktrees (resumable by name) instead of orphaned stashes.
- The write-lease gate is deferred to warn-mode, preventing overfire damage while collecting calibration data.
- If the gate proves redundant under worktree isolation (expected), it stays in warn mode permanently rather than creating maintenance overhead from a blocking-but-never-triggered gate.
- New worktree tooling is built by extending `worktree_safety.py` and `worktree_helper.py`, not adding a parallel skill.

**Negative:**
- One new hook (registry) to maintain, test, and keep calibrated.
- The write-lease gate (if eventually flipped to block) adds a second hook with complex deployment — but this is contingent on Phase 3 evidence.
- Couples session lifecycle to the native `--worktree` flag — if Anthropic changes the flag semantics, the registry layer must track it.
- Auto-commit Stop hook (`cc-skills-utils_Stop_auto_commit.py`) worktree guard — removed 2026-07-11. `Stop` event fires only for the main session; `SubagentStop` is a separate dispatch. Guard was unnecessary.

**Neutral:**
- `.worktreeinclude` becomes a tracked file at repo root — small surface, must be reviewed when secrets/certs change.

## Open Questions

1. **Registry heartbeat cadence.** Every turn (`UserPromptSubmit`) is cheap but frequent; every N turns via `PostToolUse` is cheaper but coarser. Decide after measuring.
2. **Read-only sessions.** A terminal that only reads/runs tests doesn't need a worktree. Should the registry still track it (for ops visibility) or skip it? Lean: track, with a `read_only: true` flag.
3. **Auto-commit guard.** Resolved 2026-07-11: `is_worktree` guard removed from `cc-skills-utils_Stop_auto_commit.py`. The `Stop` event fires only for the main session; subagent isolation uses `SubagentStop` (separate dispatch).

## Verification Plan

Before declaring this shipped:

1. **Native layer:** `claude --worktree test-slug` from one terminal, confirm `.claude/worktrees/test-slug/` exists with `worktree-test-slug` branch. Confirm `--resume test-slug` restores. Confirm `cwd` seen by SessionStart hook is the worktree path.
2. **Registry extension:** launch a `--worktree` session, confirm `session_registry.jsonl` entry includes `worktree` and `worktree_path` fields.
3. **PreCompact writer:** trigger a compaction cycle, confirm the compacted entry also includes `worktree` and `worktree_path` fields.
4. **Auto-commit:** launch a `--worktree` session, make a change, `/exit`, confirm the change was committed automatically.

Per the project's test-strategy contract: the registry hook crosses persistence + concurrency boundaries, so it requires **integration tests** (two real processes) plus a **smoke proof** launching the router — unit tests alone cannot prove cross-session behavior.

**Test templates:**
- Registry concurrency: follow the `ThreadPoolExecutor` shape in `tests/test_frameguard_multi_terminal.py`.
- Write-lease cross-*process* semantics: a NEW fixture is required (existing tests prove thread-safety only) — spawn two `subprocess.Popen([sys.executable, hook_path], env={...distinct session_id...})` racing for the same lease file; assert second exits without block (warn mode) or with `permissionDecision: deny` (if eventually rolled to block).
- Smoke-launch the registry hook via `python <hook>.py < sample.json`.
- Reuse `file_lock_manager.py`'s existing tests as the baseline, do not re-test locking mechanics.

## References

- "Orchestration Blueprint for Concurrent Claude Code Sessions: Multi-Agent Worktree Isolation and Lifecycle Integration" — NotebookLM source (`afd2f1dd-…`, source `7f60d8bd-…`)
- `code.claude.com/docs/en/worktrees` — native `--worktree`, `.worktreeinclude`, `cleanupPeriodDays`, subagent isolation
- `code.claude.com/docs/en/hooks` — `WorktreeCreate` / `WorktreeRemove` / `SessionStart` / `SessionStop` / `PreToolUse`
- ADR-007 — "compute, never hand-maintain" principle; contract-and-value review for design-level conflicts
- Global CLAUDE.md — gate-discipline rule (measured_tp_on_corpus before blocking)
- `terminal_id_not_per_session.md` (memory) — WT_SESSION is shared across concurrent sessions
- `__lib/worktree_helper.py` — existing worktree listing/cross-access utilities
- `__lib/file_lock_manager.py` — existing O_EXCL + stale-reap lock primitive
- `.claude/.artifacts/session_registry.jsonl` — existing append-only session registry
- `cc-skills-utils_PreToolUse_dispatch_invariant.py` — dispatch-invariant gate + hookSpecificOutput block contract
- `cc-skills-utils_Stop_auto_commit.py` — auto-commit hook (is_worktree guard)
- `cc-skills-sdlc/skills/go/scripts/worktree_safety.py` — existing worktree lifecycle CLI
- `P:/scripts/git/` PowerShell worktree automation scripts
- Adversarial review (2026-07-11): 40 findings, 8 distinct BLOCK root causes, verdict REVISE. Telemetry at `P:/.claude/.artifacts/62924c87-a6b4-46c3-99a4-f469e78f80c8/red-team/20260711-160749/`.

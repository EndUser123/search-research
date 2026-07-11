# ADR-008: Concurrent-Session Worktree Isolation

**Date:** 2026-07-11
**Status:** Proposed
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

### What an initial proposal got wrong

A first-pass design proposed building the entire lifecycle from scratch: a session registry, automatic worktree creation in `SessionStart`, a `/worktree` meta-skill. **This reinvents functionality the Claude Code platform already provides.** Per the "Orchestration Blueprint for Concurrent Claude Code Sessions" (NotebookLM source) and the official `code.claude.com/docs/en/worktrees` reference, the CLI has native worktree support (v2.1.49+):

- `claude --worktree <name>` auto-creates `.claude/worktrees/<name>/` with a `worktree-<name>` branch.
- The CLI handles directory switching, transcript relocation, and `--resume <name>` later.
- `.worktreeinclude` propagates gitignored files (`.env`, certs) into new worktrees.
- `cleanupPeriodDays` auto-prunes idle *subagent* worktrees.
- `isolation: worktree` in agent frontmatter gives ephemeral isolated worktrees to subagents, with `baseRef: fresh` (remote HEAD) or `head` (local).

The manual 5-step protocol at the top of this ADR reimplements what `--worktree` does natively. **The decisive principle: do not build what the platform already provides.** Build only the layers that fill documented capability gaps.

## Decision

Adopt a **three-layer architecture**:

1. **Native platform layer (zero build)** — use `claude --worktree <task-slug>` and `--resume` as the primary session lifecycle. Add `.worktreeinclude` at the repo root. Configure `cleanupPeriodDays`.
2. **Coordination layer (build)** — two hooks that fill gaps the platform does not cover:
   - **Session registry** (`SessionStart` / `SessionStop`) — a shared registry so any session can discover who else is active and in which worktree.
   - **Write-lease gate** (`PreToolUse` for `Edit`/`Write`/`MultiEdit`) — a per-file lock so two sessions cannot clobber the same file.
3. **Operations layer (build, thin)** — a `/worktree` meta-skill: `list`, `prune`, `reclaim`, `status`.

Two principles govern the build, carried over from ADR-007:

1. **Compute, never hand-maintain.** The session registry is written by hooks at runtime, not curated. The write-lease set is derived from the live tool call, not a config file.
2. **Use the platform first.** Every capability in the table below was checked against the native system; only rows with no native equivalent are built.

### Capability sourcing

| Capability | Native | Built here | Why |
|---|---|---|---|
| Worktree creation | ✅ `--worktree` | — | Already correct |
| Branch from clean baseline | ✅ `baseRef: fresh` | — | Default is `origin/HEAD` |
| Directory switching | ✅ CLI | — | Automatic |
| Transcript relocation | ✅ v2.1.198+ | — | Automatic on enter/exit |
| `--resume` by name | ✅ | — | Name is the session identity |
| Gitignored-file propagation | ✅ `.worktreeinclude` | — | Pattern-matched at creation |
| Subagent isolation | ✅ `isolation: worktree` | — | Per-agent frontmatter |
| Cleanup (subagents) | ✅ `cleanupPeriodDays` | — | Idle subagent sweep |
| Session discovery | ❌ | ✅ registry hook | Platform has no cross-session view |
| Write conflict prevention | ❌ | ✅ lease hook | Platform isolates git state, not logical writes |
| Cleanup (user worktrees) | ❌ excluded | ✅ `/worktree prune` | User worktrees are exempt from auto-sweep |
| MCP port collision avoidance | ❌ | ✅ port-allocator hook | Documented anti-pattern (blueprint §4) |

## Layer 1 — Native platform (one-time config)

### `.worktreeinclude` at `P:\` root

Gitignored files to copy into every new worktree:

```
.env
.env.local
.env.test
config/ssl/local_cert.crt
```

Only files that are *both* matched and verified gitignored are copied, preventing duplication of tracked assets.

### `worktree.baseRef`

Default `fresh` (branch from `origin/HEAD`) for task-level worktrees. Reserve `head` for subagents that must inherit uncommitted local state. This closes the recovery-state gap that left the `claim_risk_router` fix stranded in a stash: new task worktrees branch from a clean upstream baseline, so uncommitted local noise cannot leak into a task.

### `cleanupPeriodDays`

Set to `7`. Prunes idle *subagent* worktrees. User-created worktrees (via `--worktree`) are exempt by design — manual cleanup only.

### Naming convention

`<task-slug>` — descriptive, task-oriented. Examples: `fix-login`, `delegation-contract`, `snapshot-cache`. **Not** terminal slot numbers. The slug is the resume key and the branch suffix (`worktree-<task-slug>`); it must answer "what is this for?"

## Layer 2 — Coordination hooks (the build)

### Session registry

**Purpose:** any session can answer "who else is active, and where?"

**Storage:** `P:\.claude\session-registry\<worktree>.json` — one file per active worktree.

```json
{
  "worktree": "fix-login",
  "worktree_path": "P:\\.claude\\worktrees\\fix-login",
  "session_id": "...",
  "terminal_id": "<WT_SESSION-derived>",
  "pid": 12345,
  "started_at": "2026-07-11T14:46:35Z",
  "last_heartbeat": "2026-07-11T15:02:11Z"
}
```

**`SessionStart` hook:**
1. Derive `terminal_id` from `WT_SESSION` (Windows Terminal) or fallback to PID — never trust a manually-set env var.
2. Resolve the active worktree path from `cwd`.
3. Atomically claim the registry file (`O_CREAT | O_EXCL`). On collision, check PID liveness; reclaim if stale.
4. Set `CLAUDE_TERMINAL_ID` for the session from the registry entry (so the manual env-var step becomes unnecessary).

**`SessionStop` hook:** remove the registry entry. On crash, the PID-liveness check on next start reaps it.

**Heartbeat:** update `last_heartbeat` every N turns (via `UserPromptSubmit` or a cheap `PostToolUse`) so stale entries are detectable.

### Write-lease gate

**Purpose:** prevent two concurrent sessions from editing the same file. The native system isolates git index/HEAD (separate worktrees) but does nothing about the *logical* waste of two agents both rewriting `schemas.py`.

**Storage:** `P:\.claude\.write-leases\<sha256(file_path)>.lock`

```json
{
  "file": "packages/.../schemas.py",
  "holder_session_id": "...",
  "holder_worktree": "fix-login",
  "acquired_at": "...",
  "ttl_expires": "..."
}
```

**`PreToolUse` gate** (matcher `^(Edit|Write|MultiEdit)$`):
1. Compute the target file path from the tool input.
2. Check for an existing lease. If held by another *live* session, block with a descriptive reason naming the holder. Exit 2 + `permissionDecision: deny` + `permissionDecisionReason` (per memory: legacy `decision:block` is deprecated).
3. If no lease or lease is expired/stale, acquire one with a TTL (60s, refreshed on subsequent edits by the same session).
4. Lease files are reaped after TTL expiry.

**Scope:** tracked source files only. `.claude/` state, logs, and artifacts are exempt — those are coordination primitives, not product code.

**Known failure mode (deliberately not solved):** two sessions making *logically* conflicting changes to *different* files (A adds a field, B deletes its only consumer). This is a design-level conflict, not a write-level one. ADR-007's contract-and-value review is the answer there, not this gate.

### MCP port allocator (deferred)

Multiple worktrees running web servers or MCP servers all try to bind the same default port (e.g. 3000). The blueprint (§4 "Known Edge Cases") calls this out. Fix: derive a deterministic port offset from the worktree path hash and inject into `settings.local.json`. **Deferred** until this environment actually runs multiple bound servers concurrently — do not build ahead of need (Ponytail: YAGNI).

## Layer 3 — `/worktree` meta-skill

Thin wrapper, no novel logic:

```
/worktree list      — git worktree list + session-registry join (who's active where)
/worktree status    — current session's worktree + lease holdings
/worktree prune     — remove worktrees with no live session and no uncommitted work
/worktree reclaim   — claim an orphaned worktree (dead session, uncommitted work present)
```

`prune` is the user-worktree complement to the native subagent sweep. `reclaim` handles the crash-recovery case the native system leaves manual.

## Alternatives Considered

### A. Build everything from scratch (rejected)

A session registry + automatic worktree creation in `SessionStart` + a `/worktree` skill, ignoring the native `--worktree` flag. **Rejected:** reinvents platform functionality, drifts from upstream as the CLI evolves, and duplicates the transcript-relocation and `.worktreeinclude` machinery. The first-pass proposal in this session was exactly this; it was wrong.

### B. Agent teams instead of worktrees (rejected for this use case)

The blueprint's "Agent Teams" model: teammates share a single directory, coordinate via a shared mailbox, no file isolation. Faster coordination, but high collision risk. **Rejected** for this environment because the failure mode that motivated this ADR *was* file/index collision. Agent teams suit tightly-coupled subtasks; this environment runs independent parallel tasks. Worktree isolation is the correct trade-off here.

### C. GitButler / virtual worktrees (rejected)

Trigger.dev (cited in the blueprint) reports ditching worktrees for GitButler's virtual-branch model. **Rejected:** changes the VCS workflow fundamentally, adds a dependency, and the native `--worktree` flag already gives us what we need without it. Worth monitoring, not adopting.

### D. Status quo — manual protocol (rejected)

The current 5-step manual setup. **Rejected** for the three fragility reasons in the Problem Statement. This ADR exists because the status quo lost work (the stranded stash) and created empty slots with no binding.

## Consequences

**Positive:**
- One command (`claude --worktree <task>`) replaces a 5-step manual protocol per terminal.
- Task names replace slot numbers — branches answer "what is this for?"
- Write-lease gate prevents the most expensive class of conflict (two agents on the same file).
- Session registry gives ops visibility across 10+ terminals for the first time.
- Recovery state lives in worktrees (resumable by name) instead of orphaned stashes.

**Negative:**
- Two new hooks (registry + lease) to maintain, test, and keep calibrated.
- Write-lease gate can overfire on legitimately-shared files (e.g. a shared `__lib` helper). Mitigation: exempt `.claude/` and shared-helper paths from the lease set, revisit if it blocks real work.
- Couples session lifecycle to the native `--worktree` flag — if Anthropic changes the flag semantics, the registry/lease layer must track it.
- Adds a platform-version dependency: features used require v2.1.198+ (transcript relocation) and v2.1.205+ (NTFS junction cleanup). Verify the installed CLI meets these before rollout.

**Neutral:**
- `.worktreeinclude` becomes a tracked file at repo root — small surface, must be reviewed when secrets/certs change.

## Open Questions

1. **Lease granularity.** Per-file is the default; is per-directory ever needed (e.g. a whole `packages/<plugin>/` refactor)? Defer until a real case appears.
2. **Registry heartbeat cadence.** Every turn (`UserPromptSubmit`) is cheap but frequent; every N turns via `PostToolUse` is cheaper but coarser. Decide after measuring.
3. **Read-only sessions.** A terminal that only reads/runs tests doesn't need a worktree. Should the registry still track it (for ops visibility) or skip it? Lean: track, with a `read_only: true` flag.
4. **Port allocator trigger.** Build only when two worktrees actually run bound servers simultaneously. Do not pre-build.

## Verification Plan

Before declaring this shipped:

1. **Native layer:** `claude --worktree test-slug` from one terminal, confirm `.claude/worktrees/test-slug/` exists with `worktree-test-slug` branch, confirm `.worktreeinclude` files copied. `claude --resume test-slug` restores.
2. **Registry hook:** launch two terminals, confirm two registry files appear, confirm `CLAUDE_TERMINAL_ID` set automatically (no manual env var), confirm `SessionStop` removes entries.
3. **Crash recovery:** kill a session, confirm next start reaps the stale entry via PID-liveness check.
4. **Write-lease gate:** two sessions target the same file, confirm the second is blocked with a descriptive reason naming the first session's holder.
5. **Stale-lease expiry:** lease expires after TTL, confirm next edit by a different session acquires cleanly.
6. **`/worktree list`:** shows all worktrees joined with registry entries — live sessions flagged, orphans visible.

Per the project's test-strategy contract: the registry and lease hooks cross persistence + concurrency boundaries, so they require **integration tests** (two real processes) plus a **smoke proof** launching the router — unit tests alone cannot prove cross-session behavior.

## References

- "Orchestration Blueprint for Concurrent Claude Code Sessions: Multi-Agent Worktree Isolation and Lifecycle Integration" — NotebookLM source (`afd2f1dd-…`, source `7f60d8bd-…`)
- `code.claude.com/docs/en/worktrees` — native `--worktree`, `.worktreeinclude`, `cleanupPeriodDays`, subagent isolation
- `code.claude.com/docs/en/hooks` — `WorktreeCreate` / `WorktreeRemove` / `SessionStart` / `SessionStop` / `PreToolUse`
- ADR-007 — "compute, never hand-maintain" principle; contract-and-value review for the design-level conflict class this ADR does *not* solve

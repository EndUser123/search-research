# Handoff: Auto-commit authority failure (multi-terminal isolation)

| Field | Value |
|---|---|
| **Topic** | Silent / cross-session git writes that mutate or capture work outside the acting session's authority |
| **Priority** | **HIGHEST** for multi-stream work on shared `P:\` main — structural second writer |
| **Status** | **OPEN — diagnosis complete; containment not applied; no code change authorized** |
| **Date** | 2026-07-19 |
| **Repo HEAD at diagnosis** | `eb3ec02` on `main` (shared worktree `P:\`) |
| **Producing session** | Grok session investigating multi-terminal git after stream handoffs (parent: wiki/streams work) |
| **Host notes** | Auto-commit is a **Claude Code Stop hook**. Grok does not fire it. Shared tree means Claude sessions still commit Grok-side dirty files. |

---

## 1. Goal (one sentence)

Make git mutation and commit **authority-bound** so no terminal/session can stage, commit, delete, or overwrite paths outside its lease — with multi-terminal isolation and stale-data immunity as hard constraints.

---

## 2. Problem statement

Multiple terminals and agents share `P:\` on `main`. A **Stop auto-commit** process (and agents using whole-tree git status) can:

1. Capture another session's **in-progress modifications and untracked files** into commits with generic messages (`feat: update files`, `chore: update files`, body *“Missing capability detected”*).
2. Historically capture **deletions** made by another session (documented 2026-07-03: 124 files under `tests/_quarantine/`).
3. Create a clean working tree that **hides** concurrent work and makes stale “status is clean / I own this” beliefs look true.

User constraint: **solutions must be multi-terminal isolated and immune to stale data.** Behavioral rules (`/grok-safe-git`, “per-file stage”) are insufficient alone because auto-commit is structural and wins.

---

## 3. Verified facts (source-backed)

### 3.1 Primary implementation

| Item | Path / value |
|---|---|
| Hook | `P:/packages/.claude-marketplace/plugins/cc-skills-utils/hooks/cc-skills-utils_Stop_auto_commit.py` (~46 KB) |
| Router registration | `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/router.py` lists `cc-skills-utils_Stop_auto_commit.py` (timeout 30s) |
| User settings wiring | `C:/Users/brsth/.claude/settings.json` → Stop → `python .../cc-skills-utils/__lib/router.py Stop` |
| State / telemetry dir | `P:/.claude/state/auto_commit/` |
| Diagnostic log (best-effort) | `P:/.claude/logs/diagnostics/hook_stderr.log` |

### 3.2 Stage / commit behavior (read from source 2026-07-19)

| Behavior | Implementation detail |
|---|---|
| Default stage (no `/go` boundary) | Whole-tree non-deletions via `git add --ignore-removal .` (see hook docstring + ~L1013 region) |
| Deletion exclusion (default path) | `_get_changed_paths` skips porcelain status with `D` in XY — **explicitly** after 2026-07-03 incident (comment at ~L473–478) |
| `/go` ownership boundary (#1256) | When Stop payload resolves session → pointer → run_id → owned set: stage/commit only `owned ∩ changed`, pathspec commit via `_commit_pathspec` |
| Fail-closed without ownership | Opt-in only: `GO_AUTO_COMMIT_FAIL_CLOSED=1` — **not default** |
| Pre-staged foreign files | Pathspec commit when boundary active leaves unrelated staged index untouched; **without** boundary, plain commit risk remains for whatever is staged |
| Worktree awareness | `is_worktree()` exists; auto-commit design still centers on fleet root / main repo |

### 3.3 Documented prior incidents (in source comments)

| Date | Incident | Lesson encoded in hook |
|---|---|---|
| 2026-07-03 | Session A deleted 124 files under `tests/_quarantine/`; Session B Stop auto-commit committed the deletions | Never auto-stage deletions by default |
| 2026-07-08 | Telemetry in `skills/go` co-committed with `skills/refactor` work | Group commits by path depth-2 key (`_commit_group_key`) — **does not** solve cross-session ownership |
| #1256 / #1332 | `/go` PreToolUse owned mutations but commit-time was tree-wide | Owned ∩ changed + pathspec when `/go` pointer resolves |

### 3.4 Live repo signals (2026-07-19 diagnosis)

| Signal | Evidence |
|---|---|
| Shared main | `git worktree list`: `P:\` @ HEAD `[main]` + 9 other worktrees under `P:/.claude/worktrees/`, `P:/.worktrees/` |
| Generic auto-style commits | Author `t <t@t>`; subjects `feat: update files` / `chore: update files`; body “Missing capability detected” e.g. `eb3ec02`, `40a74f0` |
| Explicit `auto-commit:` subjects also present | e.g. `73b4f4f`, `9a04de6`, `1f3874c`, `05c8e20` |
| Soft mitigations exist | `C:/Users/brsth/.grok/skills/grok-safe-git/SKILL.md` (incl. Step 4.5 per-file scoping); agents still share tree with Claude Stop writer |
| Ignored paths ≠ durable | `.gitignore` has `.data/` — wiki under `P:/.data/wiki/` is not git-durable by default; “written to wiki” can vanish from authority without a commit |

### 3.5 Related (not the same bug)

- **Intentional agent deletions** (e.g. skill consolidations in history) are authority *decisions*, not auto-commit accidents — still unsafe if concurrent sessions share main without leases.
- **Grok does not run this Stop hook** — but Grok dirty files on `P:\` are still eligible for Claude-side auto-commit.

---

## 4. Failure mode catalog (for forensics)

| ID | Mechanism | Isolates multi-terminal? | Stale-data immune? |
|---|---|---|---|
| **A** | Session A deletes; Session B auto-commits (historical) or stages deletions if pre-staged | No | No |
| **B** | Agent `checkout` / `reset --hard` / `clean` / `restore` on shared main using stale status | No | No |
| **C** | Auto-commit / agent captures **foreign dirty** (mods + untracked) via whole-tree status | No | No |
| **D** | Submodule pointer / auto-commit of submodule SHAs | No | Stale pointer |
| **E** | Work only on ignored/tmp paths treated as durable | N/A | No git recovery |

**Diagnosis stance:** multi-cause class. Auto-commit is the **always-on structural second writer**. Do not collapse to “agents should use per-file add” alone.

---

## 5. Hard constraints (user)

1. **Multi-terminal isolated** — session *i* may only mutate/commit its authority set (worktree or explicit lease).
2. **Immune to stale data** — authority bound at claim time (`session_id` + `run_id` + path list or worktree); not re-derived from “whatever is dirty now.” Preflight expires.

**Falsifier for soft fixes:** if after more AGENTS.md / skill text, foreign captures still appear in `git log` with generic auto messages while two terminals are dirty → soft fix failed.

---

## 6. Options already framed (selection criterion)

**Criterion:** minimize unauthorized mutation of another terminal’s authority set (not “minimize forgot-to-commit”).

| Option | Summary | Isolation | Stale immunity | Cost |
|---|---|---|---|---|
| **1. Kill / gate auto-commit on shared main** | Disable Stop auto-commit on main, or worktree-only | High | High | Low |
| **2. Fail-closed ownership always** | No `/go` (or lease) pointer → no auto-commit; never `add --ignore-removal .` as default | Medium–High | Medium (still shared tree) | Medium |
| **3. Worktree-per-stream default** | Parallel streams never edit shared main; main-owner merges | High | High if main is merge-only | Higher ops |
| **4. Lease + isolated stage** | Durable path lease file; commit only lease | High | High if lease re-bound each commit | Highest build |

**Recommended durable stack:** **1 + 3**. **2** is the best bridge while still on shared main. Reject “smarter grouping” as sole fix — grouping still starts from whole-tree dirty unless ownership is mandatory.

**Hidden false anchor:** “make auto-commit smarter” without removing whole-tree stage — same bug with better commit messages.

---

## 7. Residual work (assignable)

### 7.1 CLOSED (this diagnosis session)

| Item | Evidence |
|---|---|
| Locate hook + router + settings wiring | Paths in §3.1 |
| Read stage/commit ownership logic | §3.2 |
| Catalog failure modes A–E | §4 |
| Frame options under isolation constraints | §6 |
| Confirm no containment applied | Explicit — no settings/hook edit in this session |

### 7.2 TASK_PACKET — Containment (recommended first)

| Field | Content |
|---|---|
| **id** | `AC-CONTAIN-01` |
| **goal** | Stop auto-commit from writing whole-tree commits on shared `P:\` main |
| **in scope** | Gate or disable `cc-skills-utils_Stop_auto_commit` for non-worktree / main only; document how to reverse |
| **out of scope** | Full worktree migration; lease system; rewriting history |
| **files / anchors** | `hooks/cc-skills-utils_Stop_auto_commit.py` (`auto_commit`, `auto_commit_all`, `is_worktree`); `cc-skills-utils/__lib/router.py`; optionally env flags; `~/.claude/settings.json` Stop entry (only if removing registration) |
| **acceptance** | (1) With two dirty foreign paths on main and a Claude Stop, **no** new commit appears that includes foreign paths; (2) reverse procedure written in handoff update; (3) plugin version bump + cache if source changed |
| **falsifier** | After gate, a Stop still produces `git log -1` containing a file neither owned by that session nor in its worktree |
| **verification level required** | `LIVE_BEHAVIOR` (provoke Stop with known foreign dirty file; prove non-capture) — unit tests alone insufficient |
| **no_live_run_reason if deferred** | User must authorize shared-infra change |

### 7.3 TASK_PACKET — Fail-closed default (R1)

| Field | Content |
|---|---|
| **id** | `AC-R1-FAILCLOSED` |
| **goal** | Default path: no ownership/lease → no stage/commit; remove whole-tree `git add --ignore-removal .` as default |
| **in scope** | `auto_commit()` boundary branch; default `GO_AUTO_COMMIT_FAIL_CLOSED` behavior or equivalent code default; tests in `cc-skills-utils/tests/test_auto_commit_*.py` |
| **out of scope** | Worktree UX; Grok-side auto-commit (does not exist) |
| **acceptance** | Tests: (a) no pointer → zero commits; (b) pointer + owned files → pathspec-only commit; (c) foreign dirty left unstaged; (d) deletions still not auto-staged without explicit owned-deletion policy |
| **falsifier** | Integration test where foreign untracked file appears in auto-commit without ownership |

### 7.4 TASK_PACKET — Forensic one incident (optional R0)

| Field | Content |
|---|---|
| **id** | `AC-R0-FORENSIC` |
| **goal** | Map one user-named lost path/time to failure mode A–E with evidence |
| **inputs needed from user** | Path(s), approx time, Claude vs Grok open, uncommitted vs committed loss |
| **method** | `git log -- path`, reflog, `P:/.claude/state/auto_commit/`, `hook_stderr.log`, session transcripts |
| **acceptance** | One-page addendum: mode ID + commit SHA or “uncommitted lost” + mechanism |

### 7.5 NEEDS_COORDINATOR_DECISION

| # | Question | Why blocked |
|---|---|---|
| **D1** | Authorize **AC-CONTAIN-01** now (disable/gate main auto-commit)? | Shared infra; reverse must be explicit |
| **D2** | Preferred durable stack: **1+3** (disable + worktrees) vs **2 only** (fail-closed on shared main)? | Drives R1–R3 scope |
| **D3** | Is Grok multi-stream work allowed on shared main at all until containment? | Process rule independent of code |
| **D4** | One concrete lost path for **AC-R0-FORENSIC**? | Without it, root-cause claim stays multi-mode |

---

## 8. Explicit non-goals (this handoff)

- Do not implement containment without **D1 = yes**.
- Do not `git reset --hard` / history rewrite to “undo” auto-commits without a named recovery plan.
- Do not rely on `/grok-safe-git` text alone as the fix.
- Do not claim wiki under `.data/` is the coordination SoT until tracked + committed (or moved under tracked `docs/`).

---

## 9. Immediate read list for implementing agent

1. `P:/packages/.claude-marketplace/plugins/cc-skills-utils/hooks/cc-skills-utils_Stop_auto_commit.py` — full file; focus `_get_changed_paths`, boundary block `#1256`, `auto_commit`, `auto_commit_all`
2. `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/router.py` — Stop dispatch list
3. `P:/packages/.claude-marketplace/plugins/cc-skills-utils/tests/test_auto_commit_boundary.py` and `test_auto_commit_grouping.py`
4. `C:/Users/brsth/.grok/skills/grok-safe-git/SKILL.md` — soft guard only
5. This handoff — residual packets §7

---

## 10. Suggested `/go` invoke (after D1)

```text
/go execute P:/docs/auto-commit-authority-isolation-handoff-2026-07-19.md

Scope: AC-CONTAIN-01 only unless D2 says otherwise.
Constraints: multi-terminal isolation; stale-data immunity; no whole-tree stage default.
Do not implement AC-R1 or worktree migration in the same wave without explicit expand.
Verification: LIVE_BEHAVIOR — foreign dirty file must not appear in post-Stop commit.
Append Execution Status to this file.
```

---

## 11. Epistemic labels

| Label | Claim |
|---|---|
| **[FACT]** | Hook path, router wiring, ignore-removal default, optional fail-closed, #1256 ownership path, 2026-07-03 comment, HEAD `eb3ec02` at diagnosis |
| **[INFERENCE]** | Primary ongoing risk for multi-stream on shared main is whole-tree capture (mode C) + residual deletion risk if staging paths diverge |
| **[UNKNOWN]** | Exact mode for the user's latest “trees deleted” incident until **AC-R0** inputs provided |
| **[UNKNOWN]** | Whether `GO_AUTO_COMMIT_FAIL_CLOSED` is set in any live Claude environment (not checked in all shells) |

---

## 12. Coordinator rollup note

This handoff is the communication artifact for **assignment**. Completing **AC-CONTAIN-01** does not close multi-terminal isolation; it removes the silent whole-tree writer. Worktree-per-stream (**option 3**) remains a separate stream.

---

*Generated 2026-07-19 for durable handoff. Not a substitute for reading the hook source before editing.*

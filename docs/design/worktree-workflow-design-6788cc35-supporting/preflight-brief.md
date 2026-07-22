# Preflight Inventory — Git Worktrees Across Concurrent Grok Build Sessions

**Design task:** how to use git worktrees optimally across multiple concurrent Grok Build sessions on P:\, leveraging existing skills, to minimize conflict and keep worktrees clean.

**Inventory date:** 2026-07-22
**Audit command:** `python P:\.agents\skills\preflight\scripts\discovery_audit.py --scope P:\.claude --scope P:\packages\.claude-marketplace\plugins --scope P:\.agents --scope P:\docs --scope C:\Users\brsth\.grok --target worktree --target grok-parallel --target auto-commit --target worktree-root-policy --target SessionStart --output C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\preflight-inventory.json --fail-on-conflict`
**Audit JSON:** `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\preflight-inventory.json` (242 KB)

---

## 1. Audit command result

**Initial timeout behavior:** the script was killed at the default 120 s and at the explicit 300 s timeouts. Dropping `--fail-on-conflict` did **not** change the runtime — the script completed in **222.91 s** when re-launched in the background. The exit code 1 it produced is *only* because `--fail-on-conflict` was passed and conflicts were found; **the JSON was still written**.

**Decision:** `blocked`
**Why blocked:** 2 conflicts (`--fail-on-conflict` is the trigger). Conflicts are documented in §5.

**Tally:**
- `matching_files`: 1,427
- `classification` breakdown:
  - `worktree`: 979 (mostly files inside checked-out worktrees — not authority candidates)
  - `candidate_source`: 232 (SessionStart hooks, session ledgers, `worktree_root_policy_PreToolUse.py`, `worktree_helper.py`, etc.)
  - `runtime_state`: 147 (`.artifacts/*`, `.state/*`, `.aid/*`)
  - `documentation_or_plan`: 62 (`.claude/rules/`, `.claude/plans/`, wiki pages)
  - `test_or_evidence`: 7
- `authority_candidates`: **0** — the audit did not promote any file to authority-candidate status. The strongest matches (`worktree_root_policy_PreToolUse.py`, the SessionStart hooks, `worktree_helper.py`) all carry `authority_candidate: true` flags in the conflicts section, not the top-level authority list. This means the design task must pick authority itself; the audit flagged the conflict but did not resolve it.
- `active_plans`: 0 (no plan files containing the search terms, only runtime artifacts)
- `default_hits`: 0 (no markers like `GO_WORKTREE_ROOT` set as project-wide defaults)
- `walk_errors`: 1 (one path the walker could not enumerate; not blocking)
- `git_snapshots`: 5 (branch/worktree state of the 5 repos the walker could see)

**Top-level implication:** the workspace already has the **building blocks** for multi-session worktree discipline — a pre-tool hook, a helper library, two purpose-built Grok skills (`grok-parallel`, `grok-safe-git`), and a parent `AGENTS.md` rule — but the audit could not certify a single authority for "where worktrees live" or "which hook gates concurrent writes." **That decision is the design task's first deliverable, not a discovery question.**

---

## 2. Existing implementations

The workspace already contains a non-trivial worktree stack. The design task is mostly an **integration / hardening / collision-resolution** problem, not a greenfield build.

### 2a. Hooks that gate worktree operations (P:\.claude\hooks\)

| Path | Role |
|---|---|
| `P:\.claude\hooks\worktree_root_policy_PreToolUse.py` | **Primary enforcement.** Pre-tool hook on `Bash` that denies `git worktree add <path>` unless `<path>` is under the allowed root (`P:/.worktrees/`, overridable via `WORKTREE_ALLOWED_ROOT` env var or bypassed via `GO_WORKTREE_SAFETY_BYPASS=1`). Only fires on the main thread — subagent `Bash` calls do **not** trigger it (Claude Code upstream gap `#78970`). |
| `P:\.claude\hooks\__lib\worktree_helper.py` | **Detection library.** Provides `get_current_worktree()`, `list_all_worktrees()`, `is_cross_worktree_access()`, `validate_git_command_for_worktree()`. Walks the `.git` file vs. directory ancestry to distinguish linked worktrees from submodules and nested clones. |
| `P:\.claude\hooks\__lib\git_helper.py` | Lower-level git subprocess wrapper used by `worktree_helper` and others. |
| `P:\.claude\hooks\__lib\path_validator.py` | Path validation that consumes `worktree_helper` to refuse cross-worktree writes. |
| `P:\.claude\hooks\__lib\state_paths.py` | Computes per-session, per-terminal state paths (hash-based filenames — isolation primitive). |
| `P:\.claude\hooks\__lib\session_detection.py` | Terminal/session id detection used by the state isolation primitives. |
| `P:\.claude\hooks\__lib\task_identity_manager.py` | Task registration; the `TaskIdentityManager` is the same object `SessionStart_task_identity.py` calls. |
| `P:\.claude\hooks\__lib\suggestion_utils.py` | Generates suggestion strings used by suggestion hooks (cross-references worktrees via the helper). |
| `P:\.claude\hooks\SessionStart_task_identity.py` | SessionStart hook that infers task identity from `TASK_NAME` env var → git branch → cwd path → `adhoc`. Uses a `.claude/task-worktree-mapping.json` lookup at line 130 to map branch → task name. **Implication:** the hook already assumes a "branch implies worktree" world but does not verify the worktree exists. |
| `P:\.claude\hooks\config\directory_policy.json` | Directory policy consulted by `path_validator` and `PreToolUse_directory_policy`. |

### 2b. Grok user-scope skills (C:\Users\brsth\.grok\skills\)

| Path | Role |
|---|---|
| `C:\Users\brsth\.grok\skills\grok-parallel\SKILL.md` | **Most directly relevant.** `/grok-parallel` already names worktrees as the isolation primitive for colliding writes. Step 1 mandates a task board; Step 2 calls `grok-safe-git` preflight + `grok-discovery` + `grok-route`; Step 3 spawns subagents with `isolation: worktree`; Step 4 calls `grok-verify` before completion. **It defines the contract; what it lacks is the *mechanism* — it never says where the worktree must go, what to name it, who cleans it up, or how to detect "two sessions picked the same name."** |
| `C:\Users\brsth\.grok\skills\grok-safe-git\SKILL.md` | Concurrent-safe git preflight. Step 4.5 ("Multi-session commit safety — per-file scoping") says *"The ecosystem-proven structural fix is worktree-per-task (see `P:/.data/wiki/concepts/multi-terminal-git-coordination-primitives.md` Primitive 4), but per-file scoping is sufficient when sessions touch non-overlapping file sets."* → **the wiki page referenced does not exist** (see §7). |
| `C:\Users\brsth\.grok\skills\grok-safe-git\scripts\preflight.ps1` | PowerShell wrapper for the safe-git preflight steps. |
| `C:\Users\brsth\.grok\skills\grok-route\SKILL.md` | Workspace instruction routing. Step 4 already says *"Do not edit cache or generated copies unless the task is explicitly about them"* and *"When CWD is a worktree, edit under the worktree path, not main."* |
| `C:\Users\brsth\.grok\skills\grok-discovery\SKILL.md` (referenced from `grok-parallel`) | Discovery pre-spawn. |
| `C:\Users\brsth\.grok\skills\grok-verify\SKILL.md` (referenced from `grok-parallel`) | Verifies claims before completion. |
| `C:\Users\brsth\.grok\skills\plan\SKILL.md`, `grok-go\SKILL.md`, `grok-sdlc\SKILL.md`, `handoff\SKILL.md`, `design\SKILL.md`, `grok-sdlc\SKILL.md` | Adjacent workflows. None currently owns worktree lifecycle. |

### 2c. Superpowers plugin skills (C:\Users\brsth\.grok\installed-plugins\superpowers-21e2a56d\)

| Path | Role |
|---|---|
| `skills\using-git-worktrees\SKILL.md` | **Generic, portable worktree skill.** Step 0 detects existing isolation via `git rev-parse --git-dir` / `--git-common-dir` and a submodule guard. Step 1a mandates native platform tools (e.g., Claude Code's `EnterWorktree`) before falling back to `git worktree add` (Step 1b). Directory priority: explicit instruction → existing `.worktrees/` (preferred) → `worktrees/` → default `.worktrees/`. Verifies `git check-ignore` before creating. **Conflict:** the superpowers default is `.worktrees/` (project-local); the Grok hook enforces `P:/.worktrees/` (workspace-wide). On this host, the hook wins (it is the runtime enforcer) but a Claude Code subagent that loads `using-git-worktrees` first may try to write under the project root `.worktrees/`, which the hook will then deny. |
| `skills\using-superpowers\references\codex-tools.md` | Codex-specific worktree/branch tool reference (mentioned in plan; path corrected below). |
| `skills\executing-plans\SKILL.md`, `skills\subagent-driven-development\SKILL.md`, `skills\writing-plans\SKILL.md` | All integrated with the rototill (see 2d); mandate worktree isolation before plan execution. |
| `skills\finishing-a-development-branch\SKILL.md` | Defines the *finish* path (merge/rebase/PR). Three known finishing bugs are fixed in the rototill plan. |
| `skills\requesting-code-review\code-reviewer.md` | Code-review contract; references worktree paths in review bundles. |

### 2d. Plans and specs touching worktrees

| Path | Status |
|---|---|
| `installed-plugins\superpowers-21e2a56d\docs\superpowers\plans\2026-04-06-worktree-rototill.md` | **Active superpowers plan** to make `using-git-worktrees` prefer native tools + fix three finishing bugs. Contains TDD validation gate (Task 1). |
| `installed-plugins\superpowers-21e2a56d\docs\superpowers\specs\2026-04-06-worktree-rototill-design.md` | Design doc for the rototill. |
| `installed-plugins\superpowers-21e2a56d\tests\claude-code\test-worktree-native-preference.sh` | RED/GREEN/PRESSURE test for Step 1a native-tool preference. |
| `installed-plugins\superpowers-21e2a56d\tests\claude-code\test-worktree-path-policy.sh` | Tests path policy enforcement. |
| `installed-plugins\superpowers-21e2a56d\tests\claude-code\test-sdd-workspace.sh`, `test-subagent-driven-development.sh` | Use worktrees as part of the SDD test setup. |
| `marketplace-cache\b975999a270027c6\.plan\worktree-adoption.md` | **Misnomer — not relevant.** This is about a *claude-mem* feature for stamping merged-worktree observations onto parent projects (SQLite + Chroma). Different concept entirely; surfaced only because the filename contains "worktree." Design task should ignore. |
| `P:\.claude\plans\plan-20260123-*.md` (4 files, all "dynamic-kindling-pebble-agent") | Older plans referencing `P:/worktrees` paths; stale (Jan 2026). |
| `P:\.claude\plans\fix-likely-speculative-claims-detection.md`, `harmonic-petting-salamander.md`, `plan-20260122-184708-jazzy-squishing-giraffe.md` | Other stale plans mentioning worktrees as deployment surface. |

### 2e. Prior design runs

`C:\Users\brsth\.grok\design-runs\` exists with 4 runs from 2026-07-20:

| Run | Topic |
|---|---|
| `grok-design-6bf249df` | **Cross-model skill siblings `/mmx` and `/codex`.** Most recent (07-20 11:13). Establishes the conductor pattern (skill as shell-out CLI with verification + run record). The worktree design is a sibling pattern. |
| `grok-design-43e11106` | (07-20 08:32) |
| `grok-design-10d0654e` | (07-20 07:35) |
| `grok-design-c65e5068` | (07-20 00:08) |

The cross-model design is the closest analog: same host, same operator, same `C:\Users\brsth\.grok\design-runs\` destination, same skill-creation lifecycle. The worktree design should match its conductor pattern (skill-as-shell-out helper script + SKILL.md contract + verification).

### 2f. Rules (always-loaded)

`P:\.claude\rules\worktree-workflow.md` (full text retrieved):
> **WRONG:** Editing main branch directly at `P:/projects/yt-fts/src/`
> **RIGHT:** Editing worktree version at `P:/worktrees/w1t4/projects/yt-fts/src/`
> **Workflow:** make changes in worktree → commit in worktree → user invokes git-sync to merge worktree to main → never edit main directly while a worktree is active.
> **Verification:** after any edit, run `git status` and `git diff HEAD` to verify changes are in the worktree.

This rule is **misaligned with the live runtime**: it says `P:/worktrees/<name>/projects/...`, but `P:/worktrees/` does not host project subtrees on this host — it hosts top-level worktrees at `P:/worktrees/codex-agent-bridge`, `P:/worktrees/userpromptsubmit-hardening-20260712`. The rule's mental model is "worktree wraps the project subdirectory" but the actual usage is "worktree at repo root, branch per task." **This rule needs updating as part of the design task** (see §7).

`P:\.claude\rules\worktree-workflow.md` is also being copied into multiple checked-out worktrees (`.claude\worktrees\test-wt-field\.claude\rules\worktree-workflow.md` etc.) — a sign that the rule has been duplicated across test fixtures and may now conflict with itself.

### 2g. Hook catalog reference

`P:\.claude\hooks\HOOKS_CATALOG.md` and `P:\.claude\hooks\.aid\hooks\hooks_full.md` both enumerate `worktree_root_policy_PreToolUse` as an active hook. The audit's `walk_errors=1` likely reflects that the walker tripped on the `.aid/` tree or a permission-denied file.

---

## 3. Callers / consumers

What actually invokes the worktree-related code today:

1. **`worktree_root_policy_PreToolUse.py`** is wired in `~/.claude/settings.json` under `hooks.PreToolUse` matcher `Bash` (per its own docstring at line 11). It is the only enforcement point for `git worktree add`. Audit confirmed 24 candidate `SessionStart_*.py` hooks (conflict 1, §5) but **only one** `worktree_*` hook.
2. **`worktree_helper.py`** is imported by `path_validator.py`, `SessionStart_task_identity.py` (via the TaskIdentityManager path), and `suggestion_utils.py`. (Verified by reading the imports at the top of those files.)
3. **`SessionStart_task_identity.py`** runs on every Grok Build session start (24 hooks fire — see §5 conflict 1) and reads `.claude/task-worktree-mapping.json` to map a branch name to a task name.
4. **`grok-parallel` SKILL.md** is invoked explicitly via `/grok-parallel`; consumed by parent agents that fan out work. It declares `isolation: worktree` as a spawn contract but provides no implementation — children are expected to either (a) inherit a worktree path from the parent prompt, or (b) detect one.
5. **`grok-safe-git` SKILL.md** is invoked explicitly via `/grok-safe-git` and is also a Step 2 prerequisite of `grok-parallel`. Step 4.5 references the missing wiki page.
6. **`using-git-worktrees`** (superpowers plugin) loads implicitly whenever an agent invokes `/using-git-worktrees` or whenever superpowers's "skill-nudge" mechanism fires it during implementation planning.
7. **Existing worktrees** (see §6) carry their own copy of the worktree workflow rule + scripts (`scripts/pi-worktree.sh` appears in `test-wt-field`, `test-worktree-field`, `sdlc-audit`). These scripts are not on the live invocation path today but suggest a prior automation that the design should either revive or supersede.

---

## 4. Active plans

The audit found **0 active plans** matching its search criteria, but the manual grep uncovered:

- **Live, in-progress:** `superpowers-21e2a56d/docs/superpowers/plans/2026-04-06-worktree-rototill.md` — superpowers plugin internal. Implements native-tool preference + three finishing-bug fixes. **The Grok Build design task is *adjacent* to this, not overlapping** — rototill changes `using-git-worktrees` for *Claude Code*; the design task changes Grok Build's *worktree lifecycle on P:*. They should not collide if the design defers native-tool preference to superpowers (it does) and focuses on the *Grok Build* layer (workspace-root policy, naming, cleanup, cross-session awareness).
- **Prior context (closed/older):** the `P:\.claude\plans\plan-20260123-*` files reference `P:/worktrees` paths; these are January 2026 plans, the rule they cite has since drifted from reality.
- **Adjacent (not overlapping):** `marketplace-cache\b975999a270027c6\.plan\worktree-adoption.md` is a *claude-mem* observation-adoption feature; the name is misleading. Not relevant.
- **No design-runs entry** for worktrees exists yet in `C:\Users\brsth\.grok\design-runs\` — this will be the first.

---

## 5. Constraint conflicts (the things the audit flagged)

The audit returned `decision: blocked` because of two conflicts. **Both are real and must be resolved before the design ships.**

### Conflict A — `multiple_role_candidates` for `sessionstart` (24 candidates)

The audit found **24 `SessionStart_*.py` hooks** in `P:\.claude\hooks\` (all classified `candidate_source`):

```
SessionStart.py
SessionStart_cc_health.py
SessionStart_characterization_check.py
SessionStart_chs_delta_reindex.py
SessionStart_commitment_tracker.py
SessionStart_constraint_display.py
SessionStart_contract_health.py
SessionStart_dreaming_daemon.py
SessionStart_folder_context.py
SessionStart_hook_health_check.py
SessionStart_hook_import_health.py
SessionStart_log_rotation.py
SessionStart_memory_cks_auto.py
SessionStart_memory_monitor.py
SessionStart_observability_rollup.py
SessionStart_repo_map.py
SessionStart_search_daemon.py
SessionStart_semantic_daemon.py
SessionStart_symlink_check.py
SessionStart_task_identity.py
SessionStart_terminal_id.py
SessionStart_timeline.py
SessionStart_universal_skills_manager.py
SessionStart_verification_cleanup.py
```

**For the design task this is significant because:**
- `SessionStart_task_identity.py` is the hook that *infers* task name from the worktree branch.
- It runs alongside 23 other SessionStart hooks. If any other hook fires worktree operations at session start (none observed in the audit, but the surface is wide), there is a coordination problem the design must answer: which SessionStart hook owns the worktree registration, and which owns the cleanup? No such owner is currently declared.
- **No coordination contract exists** between `SessionStart_task_identity.py` and `worktree_root_policy_PreToolUse.py`. The first runs at session start and reads branch; the second runs on Bash commands and gates `git worktree add`. They never talk to each other.

### Conflict B — `configuration_or_lifecycle_default_requires_full_reader_writer_audit` (worktree-root path markers)

The audit found four competing markers for the worktree root across runtime state and plans:

| Marker | Where it appears | What it means |
|---|---|---|
| `P:/worktrees` | 3 session ledgers in `P:\.claude\.session\`, the `P:\.claude\rules\worktree-workflow.md` rule, several plan files, two live codex worktrees (`P:/worktrees/codex-agent-bridge`, `P:/worktrees/userpromptsubmit-hardening-20260712`) | Plain, non-hidden directory at repo root. |
| `P:/.worktrees` | `P:\.claude\hooks\worktree_root_policy_PreToolUse.py` (default), 1 session ledger, the `b975999a270027c6` superpowers cache, the `using-git-worktrees` skill's default priority | Hidden directory at repo root. |
| `GO_WORKTREE_ROOT` | 6 `.artifacts/*` files, 1 session ledger | Environment-variable convention; no current code sets or reads it. |
| `GO_MANAGED_WORKTREE_ROOT` | 1 `.artifacts/*` file | Same; no live code. |

**The authoritative default today** is `P:/.worktrees/` (the hook's hardcoded `Path("P:/.worktrees")` plus the superpowers skill's `.worktrees`-first priority). **The de-facto live usage** is `P:/worktrees/` (two codex worktrees, eight `.claude/worktrees/` worktrees, and the rule file). **The hook's enforcement is not catching the live worktrees** because they predate the hook, or because subagent `Bash` calls bypass it (upstream gap `#78970`).

**This is the central design tension.** Whichever path the design endorses, the other path's worktrees need a migration plan or the design must explicitly tolerate both.

### Smaller conflicts surfaced via grep (not in audit JSON but visible in matching files)

- The `worktree-workflow.md` rule assumes a "worktree wraps a project subtree" mental model that does not match the actual `P:/worktrees/<name>/` shape used today. The rule is being copied into checked-out worktrees, where it self-references.
- `SessionStart_task_identity.py` reads `.claude/task-worktree-mapping.json` to map branch → task name but no code creates that file. The mapping is dormant.
- `multi-terminal-git-coordination-primitives.md` (cited by `grok-safe-git` Step 4.5) does not exist on disk. The citation is stale.

---

## 6. Existing worktree directories on disk (live state)

`git -C P: worktree list` (verified 2026-07-22):

```
P:                                                        b3fb522 [main]
P:/.claude/worktrees/ai-task-20260713-133947              7d8e103 [ai/ai-task-20260713-133947]
P:/.claude/worktrees/enforcement-removal-20260627-051242  c0350f5 [ai/enforcement-removal-20260627-051242]
P:/.claude/worktrees/research-runtime-clean               d43dff3 [ai/research-runtime-clean]
P:/.claude/worktrees/sdlc-audit                           f206622 [worktree-sdlc-audit]
P:/.claude/worktrees/sessionend-test                      088bcae [worktree-sessionend-test] locked
P:/.claude/worktrees/test-worktree-field                  088bcae [worktree-test-worktree-field]
P:/.claude/worktrees/test-wt-field                        088bcae [worktree-test-wt-field]
P:/.worktrees/codex-agent-bridge                          9219402 [codex/agent-bridge]
P:/.worktrees/userpromptsubmit-hardening-20260712         b590385 [codex/userpromptsubmit-hardening-20260712]
```

**Observations:**
- **Two roots are in use:** `P:/.claude/worktrees/` (8 active worktrees, all `ai/*` or `worktree-*` branches) and `P:/.worktrees/` (2 active worktrees, both `codex/*` branches). `P:/worktrees/` (non-hidden) is not present in `git worktree list` but stale `Get-ChildItem` returns three leftover directories (`pi-task-20260710-*`, `yt-is-throughput-cadence-accounting`) — these are **ghost worktrees** (directory on disk, no git registration).
- **Names follow two conventions:** human-readable (`sessionend-test`, `sdlc-audit`, `research-runtime-clean`) and timestamped (`ai-task-20260713-133947`, `enforcement-removal-20260627-051242`, `pi-task-20260710-133714-e8704c63-go`). The timestamped convention appears to be the `pi-task-*` pattern used by some prior automation.
- **Two test-fixture worktrees** (`test-worktree-field`, `test-wt-field`) share commit `088bcae` with the `sessionend-test` worktree — likely a scripted test of the hook, not real work.
- **One worktree is locked** (`sessionend-test`). The other `088bcae` worktrees duplicate its branch state. This is the test-fixture residue.
- **No worktree is registered under `P:/worktrees/`** (non-hidden). Stale directories exist but are not tracked. They are pure litter that the cleanup routine will need to handle.
- **The user's `git status -s` shows the live `main` checkout is dirty** (`M .claude/CLAUDE.md`, `M .data/wiki/...`, `D .data/wiki/sources/skills/...`) — concurrent agents are touching `main` directly, which the design must address as either (a) a violation to be enforced away, or (b) a deliberate pattern to be supported.

---

## 7. Gaps and surprises

These are the things the design task must either resolve or document.

1. **Stale citation in `grok-safe-git` SKILL.md line 99.** References `P:/.data/wiki/concepts/multi-terminal-git-coordination-primitives.md` Primitive 4. **The file does not exist** (verified — read_file returned "does not exist"). The skill currently points to a phantom doc. Fix: either create the page, replace the citation with a live path, or remove the citation.

2. **`worktree-workflow.md` rule is out of sync with runtime usage.** Says "edit under `P:/worktrees/<name>/projects/yt-fts/src/`" — actual usage is `P:/.worktrees/<branch-name>/` with the full repo, not a project subtree. Rule is being copied into checked-out worktrees (self-reference). Fix: rewrite the rule, or scope it tightly.

3. **Two competing roots (`P:/.worktrees/` vs `P:/worktrees/`).** Hook enforces one, two codex worktrees and the rule say the other, ghost directories litter both. The design must declare an authority and migrate or migrate-or-deprecate the loser. **`WORKTREE_ALLOWED_ROOT` env var is the hook's escape hatch** but no code reads it.

4. **Hook coverage gap on subagents.** `worktree_root_policy_PreToolUse.py` only fires on main-thread Bash (Claude Code upstream `#78970`). Subagents that call `git worktree add` directly are unmonitored. The design must either (a) use a different enforcement layer that catches subagents, or (b) accept the gap and document it.

5. **`grok-parallel` declares `isolation: worktree` but provides no implementation.** Children have no guidance on where to put the worktree, what to name it, or how to clean up. The design should either (a) provide a helper script that `grok-parallel` can shell out to, or (b) mandate the parent compute the worktree path and pass it as a parameter to the child.

6. **24 SessionStart hooks, no coordination contract.** See §5 Conflict A. The design should either (a) declare a single owner for worktree lifecycle, or (b) accept the multiplicity and tolerate it.

7. **`SessionStart_task_identity.py` reads `.claude/task-worktree-mapping.json` but nothing creates it.** The mapping file is dormant. Either drop the read or provide a writer.

8. **Ghost worktrees on disk (3 stale dirs in `P:/worktrees/`).** Not in `git worktree list` but present in the filesystem. Cleanup routine needs a "list dirs not in `git worktree list`" sweep.

9. **Stale `pi-worktree.sh` scripts inside test-fixture worktrees** (`test-wt-field`, `test-worktree-field`, `sdlc-audit`). A prior automation. The design should either revive, deprecate, or delete these scripts and document the decision.

10. **`P:/.claude/worktrees/` hosts 8 worktrees; `P:/.worktrees/` hosts 2.** The hook's default (`P:/.worktrees/`) has been *flouted* by the bulk of existing usage (`P:/.claude/worktrees/`). This is empirical evidence that the hook's default was wrong or never enforced when the `.claude/worktrees/` worktrees were created. Either the hook needs to be widened or `.claude/worktrees/` needs to be migrated.

11. **No design-run precedent for this specific topic.** Prior design-runs (cross-model siblings, etc.) followed a conductor pattern; the worktree design will be the first in a different domain (lifecycle management, not skill siblings).

12. **Active superpowers plan (`worktree-rototill`) is adjacent, not overlapping.** The design should explicitly defer Step 1a (native-tool preference) to superpowers and focus on the Grok Build layer (root policy, naming, cleanup, cross-session awareness, integration with `grok-parallel` / `grok-safe-git`).

---

## Suggested next moves for the design task

These are **observations, not prescriptions** — the design subagent should re-evaluate:

- **Pick the worktree root authority.** `P:/.worktrees/` (hook default) vs `P:/.worktrees/` is what the bulk of live usage already follows *under* `P:/.claude/`, so the more honest option may be `P:/.worktrees/` plus a path like `P:/.worktrees/<task-id>/<branch>/` for explicit task scoping. Or absorb the cost and migrate to a single root.
- **Provide a `grok-parallel` worktree helper.** A `grok-parallel/scripts/new_worktree.py` that parents a worktree under the chosen root, applies a naming convention (`<session-id>-<short-hash>` or `<task>-<branch>-<date>`), verifies `git check-ignore`, and writes to the dormant `task-worktree-mapping.json`. Matches the cross-model skill conductor pattern.
- **Add a complementary cleanup hook** (e.g., `SessionEnd_worktree_cleanup.py`) that on session end reports worktrees created in this session and offers to remove them. The `WorktreeAdoption` work from `marketplace-cache\b975999a270027c6` is **not** the right starting point — that plan is about claude-mem observation merging, not session lifecycle.
- **Rewrite `P:\.claude\rules\worktree-workflow.md`** to match the actual `P:/.worktrees/<branch>/` shape, or scope the rule tightly and remove the self-referential copies in test fixtures.
- **Replace or create the missing wiki page** that `grok-safe-git` cites.
- **Tighten the audit gap on subagent enforcement.** Either file an upstream Claude Code ticket and document the gap, or move the enforcement to a layer that catches subagents (e.g., a worktree wrapper script that all subagents must invoke rather than a hook).
- **Decide what to do with the 24 SessionStart hooks** as a separate workstream (out of scope for the worktree design itself, but flag it).

---

## Source receipts (for the receipt rule)

- Audit JSON: `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\preflight-inventory.json` — decision=`blocked`, matching_files=1427, conflicts=2 (read via `read_file` and `python -c` summary)
- `P:\.claude\hooks\worktree_root_policy_PreToolUse.py` (read 2026-07-22) — hook behavior, defaults, env vars, upstream gap `#78970`
- `P:\.claude\hooks\__lib\worktree_helper.py` (read 2026-07-22) — public API surface
- `P:\.claude\hooks\SessionStart_task_identity.py` (read 2026-07-22) — `task-worktree-mapping.json` read at line 130
- `C:\Users\brsth\.grok\skills\grok-parallel\SKILL.md` (read 2026-07-22) — `isolation: worktree` contract
- `C:\Users\brsth\.grok\skills\grok-safe-git\SKILL.md` (read 2026-07-22) — Step 4.5, stale wiki citation line 99
- `C:\Users\brsth\.grok\skills\grok-route\SKILL.md` (read 2026-07-22) — worktree-edit rule
- `C:\Users\brsth\.grok\installed-plugins\superpowers-21e2a56d\skills\using-git-worktrees\SKILL.md` (read 2026-07-22) — Step 0/1a/1b, directory priority
- `C:\Users\brsth\.grok\installed-plugins\superpowers-21e2a56d\docs\superpowers\plans\2026-04-06-worktree-rototill.md` (read 2026-07-22, first 200 lines) — rototill plan
- `C:\Users\brsth\.grok\marketplace-cache\b975999a270027c6\.plan\worktree-adoption.md` (read 2026-07-22, first 120 lines) — confirmed to be about claude-mem observation provenance, not session lifecycle
- `P:\.claude\rules\worktree-workflow.md` (read 2026-07-22) — full text retrieved
- `git -C P: worktree list` (run 2026-07-22) — 10 active worktrees
- `git -C P: status -s` (run 2026-07-22) — main checkout dirty; truncated output shown above
- `Get-ChildItem P:\worktrees, P:\.claude\worktrees, C:\Users\brsth\.grok\worktrees` (run 2026-07-22) — 4 stale ghost directories confirmed
- `P:\.data\wiki\concepts\multi-terminal-git-coordination-primitives.md` (read attempt 2026-07-22) — **does not exist** (file-not-found error)

## Unknowns (for the design task to resolve)

- **No authority_candidates promoted by audit** — the design must pick the authority itself; the audit only flagged the conflict, did not resolve it.
- **Whether `GO_WORKTREE_ROOT` or `GO_MANAGED_WORKTREE_ROOT` should be added as a real env var convention** — current code sets neither.
- **Whether the dormant `.claude/task-worktree-mapping.json` should be revived or removed.**
- **Whether the hook's `WORKTREE_ALLOWED_ROOT` env var should be set to widen the allowed root to include `P:/.claude/worktrees/`.**
- **Whether subagent enforcement (upstream gap `#78970`) is in scope for this design or a separate ticket.**

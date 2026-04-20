# Review Bundle — `/go` Skill

**Generated:** 2026-04-20
**Scope:** `P:/packages/cc-skills-sdlc/skills/go`
**File Count:** 2 files
**Execution Mode:** single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name:** `/go` — Local PR-Ready Ralph Loop
- **Skill Version:** 1.0.0
- **Package:** `cc-skills-sdlc` (SDLC skills for Claude Code)
- **Category:** execution
- **Enforcement:** blocking
- **Triggers:** `/go`, `/go-local`, `/local-pr-ready`
- **Ralph-mode:** Auto-detected from `plan.md` or batch tasks; manual override via `--ralph` / `--no-ralph`

### Domain & Purpose
A Ralph loop skill that enforces git worktree isolation, drives a 7-pass review pipeline with auto-detected review depth, runs mandatory simplify quality gates, and produces local PR artifacts without remote push. Intended for solo developers working from a task plan on a feature branch.

### Scale Metrics
- LOC: ~600 (SKILL.md) + ~67 (ralph-loop.sh)
- No external dependencies; pure bash + Claude Code built-ins
- Change frequency: low (stable workflow skill)

### Environment
- **OS:** Windows 11 + Git Bash
- **Shell:** bash (set -euo pipefail)
- **Primary tooling:** git worktree, Claude Code `/simplify`, `/go` command
- **Optional:** `gh` CLI (manual PR creation only, not used by skill)

---

## 2. ARCHITECTURE OVERVIEW

```
Command Frontend (P:/.claude/commands/go.md)
    │
    ├── Entry point listed: P:/.claude/skills/go/SKILL.md  ← go_v1.0 junction, NOT "go"
    │
    └── Junction: P:/.claude/skills/go_v1.0/ → /p/packages/cc-skills-sdlc/skills/go/  ← ACTUAL SKILL

Skill Implementation (at /p/packages/cc-skills-sdlc/skills/go/)
    ├── SKILL.md          (main workflow definition, ~600 LOC)
    └── ralph-loop.sh     (bash driver for autonomous iteration)
```

### Skill Workflow (STEPs 0–6)

```
STEP 0: Worktree Enforcement
    └── Auto-create worktree if not in one → branch naming from plan.md or timestamp

STEP 1: Task Contract
    └── Create .claude-state/task-definition.md with objective, scope, acceptance criteria

STEP 1B: Auto-Detect Review Depth
    └── Compute from git diff --stat:
        <3 files / <50 lines  → quick (passes 1, 2, 7)
        <10 files / <200 lines → standard (passes 1, 2, 3, 5, 7)
        ≥10 files / ≥200 lines → full (passes 1-7)

STEP 2: Verification Commands
    └── Run literally from task-definition.md; paste output to verification-results.txt
    └── FAIL → risks.md + <promise>BLOCKED</promise>

STEP 3: Simplify (MANDATORY)
    └── /simplify on changed code files (not docs-only, not PR artifacts)
    └── PASS → continue; HIGH/CRITICAL → one corrective cycle → still HIGH → BLOCKED

STEP 4: Review Passes
    └── Execute only passes required by auto-detected depth
    └── Passes: correctness, scope, tests, simplicity, regressions, maintainability, pr-ready

STEP 5: PR Artifacts (local only)
    └── commit-message.txt, pr-title.txt, pr-body.md, pr-ready.md
    └── Emit <promise>PR_READY</promise> — NO git push, NO gh pr create

STEP 6: Loop Check
    └── If Ralph-mode active → re-read plan.md → continue or ALL_TASKS_COMPLETE
```

### Ralph Loop Driver (`ralph-loop.sh`)

```bash
# Iterates /go up to 10 times, watching for terminal tokens:
<promise>PR_READY</promise>          → exit 0
<promise>BLOCKED</promise>          → exit 1
<promise>ALL_TASKS_COMPLETE</promise> → exit 0
<promise>MORE_TASKS_IN_PLAN</promise> → continue
# Safety: max 10 iterations
```

---

## 3. EXECUTION AND DATA FLOW

### Mandatory State Files (`.claude-state/`)
| File | Purpose |
|------|---------|
| `task-definition.md` | Canonical task contract (created STEP 1) |
| `progress.txt` | Iteration log |
| `decisions.md` | Design rationale |
| `risks.md` | Open issues, blocking items |
| `verification-results.txt` | Command outputs |
| `review-passes/*.md` | Individual review pass results |
| `simplify-status.md` | Simplify gate output |

### Completion Tokens
- `<promise>PR_READY</promise>` — All gates passed, artifacts created
- `<promise>BLOCKED</promise>` — Verification failed or HIGH/CRITICAL simplify findings
- `<promise>MORE_TASKS_IN_PLAN</promise>` — Ralph loop, tasks remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — Ralph loop, plan exhausted

### Key Constraints
- Must be in a git worktree (auto-creates if not)
- No git push or remote PR creation
- Simplify must pass or be explicitly waived
- All required review passes must PASS
- No mocks as proof of integration

---

## 4. COMPONENT INVENTORY

### `SKILL.md` — Main Skill Definition
- **Path:** `P:/packages/cc-skills-sdlc/skills/go/SKILL.md`
- **Type:** Claude Code skill manifest + workflow definition
- **Key sections:** STEP 0–6, Ralph completion criteria, prohibited actions, state file spec
- **Notable:** Frontmatter defines `workflow_steps` (7 steps) matching the 7 review passes

### `ralph-loop.sh` — Bash Driver
- **Path:** `P:/packages/cc-skills-sdlc/skills/go/ralph-loop.sh`
- **Type:** Executable bash script
- **Responsibility:** Autonomous iteration calling `/go` until terminal token
- **Inputs:** Optional ticket-id arg; falls back to `git branch --show-current`
- **Outputs:** Terminal tokens + iteration progress to stdout
- **Safety:** `set -euo pipefail`, max 10 iterations

### Command Frontend
- **Path:** `P:/.claude/commands/go.md`
- **Type:** Junction/CLI frontend
- **Issue ⚠️:** References `P:/.claude/skills/go/SKILL.md` but junction is `go_v1.0`, not `go`
- **Actual junction:** `P:/.claude/skills/go_v1.0/` → `/p/packages/cc-skills-sdlc/skills/go/`

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Worktree isolation** — Every task runs on a branch in an isolated worktree
2. **Evidence-based completion** — No claims without running actual verification commands
3. **Quality gate** — Simplify must pass before PR_READY
4. **Local-only artifacts** — No automatic push or remote PR creation
5. **Ralph loop** — Autonomous iteration through plan.md tasks

### Non-Negotiables
- Verification commands MUST be run literally, not summarized
- Simplify cannot be skipped for code changes (only docs-only may skip)
- BLOCKED state must be recorded in risks.md before emitting token
- Forbidden files listed in task contract must not be modified

### Known Design Gaps
- Junction name mismatch: command frontend references `go` but the junction is `go_v1.0`
- Junction target uses Unix path `/p/packages/...` (may not resolve on Windows P:\)

---

## 6. KNOWN ISSUES

### Issue 1: Junction Name Mismatch (MEDIUM impact)
- **Scenario:** Claude Code invokes `/go` via `P:/.claude/commands/go.md`, which references `P:/.claude/skills/go/SKILL.md`
- **Expected:** Junction named `go` at `P:/.claude/skills/go/`
- **Actual:** Junction is named `go_v1.0` at `P:/.claude/skills/go_v1.0/` (points to `/p/packages/cc-skills-sdlc/skills/go/`)
- **Impact:** `/go` command likely fails because the junction `go` does not exist — the command frontend's reference is stale
- **Root Cause:** Junction was created as `go_v1.0` but command frontend still references `go`
- **Verified:** `ls -la P:/.claude/skills/ | grep go` shows `go_v1.0 -> /p/packages/cc-skills-sdlc/skills/go/`, no `go` junction

### Issue 2: ralph-loop.sh Uses Unquoted Command Substitution (LOW impact)
- **File:** `ralph-loop.sh:21` — `OUTPUT=$(/go 2>&1)` is unquoted but safe since `/go` output is trusted
- **Notably:** Other substitutions `TICKET="${1:-$(git branch ...)}"` and `LAST_ITER=$(grep ...)` are safe

### Issue 3: Ralph Loop Token Detection Depends on `/go` Output Format (MEDIUM impact)
- **File:** `ralph-loop.sh:25-46` — `grep -q '<promise>TOKEN</promise>'` against `/go` stdout
- **Risk:** If `/go` emits token to stderr instead of stdout, loop continues indefinitely
- **Impact:** Safety limit of 10 iterations prevents infinite loop, but wastes iterations

---

## 7. INTEGRATION POINTS

### Entry Points
- `/go` — Claude Code command (via `P:/.claude/commands/go.md`)
- `/go --ralph` / `/go --no-ralph` — Ralph mode override
- `./ralph-loop.sh [ticket-id]` — Autonomous bash driver

### Called Skills/Commands
| Called | When | Purpose |
|--------|------|---------|
| `/simplify` | STEP 3 | Code quality gate |
| `git worktree` | STEP 0 | Branch isolation |
| `git diff --stat` | STEP 1B | Review depth auto-detection |
| `gh` (optional) | Manual post-PR | Remote PR creation |

### State Dependencies
- `plan.md` — Read in STEP 6 (Ralph loop) to check remaining tasks
- `.claude-state/` — All state files written/read per STEP

---

## 8. INPUT/OUTPUT CONTRACT

### Phase: Skill Load
- **Reads:** `P:/.claude/commands/go.md` → junction → `P:/packages/cc-skills-sdlc/skills/go/SKILL.md`
- **Issue:** Junction path resolves to correct skill, but direct entrypoint reference is broken

### Phase: STEP 0 (Worktree Check)
- **Reads:** `git worktree list --porcelain`, `pwd`, `git branch --show-current`
- **Writes:** Potentially creates new worktree via `git worktree add`

### Phase: STEP 1 (Task Contract)
- **Reads:** Nothing (derives from conversation context)
- **Writes:** `.claude-state/task-definition.md`

### Phase: STEP 1B (Review Depth)
- **Reads:** `git diff --stat`, `git diff --shortstat`
- **Writes:** Updates `task-definition.md` Review Depth field

### Phase: STEP 2 (Verification)
- **Reads:** `.claude-state/task-definition.md` (verification commands section)
- **Writes:** `.claude-state/verification-results.txt`

### Phase: STEP 3 (Simplify)
- **Reads:** Git diff (to classify code vs docs-only)
- **Invokes:** `/simplify` skill
- **Writes:** `.claude-state/simplify-status.md`

### Phase: STEP 4 (Review Passes)
- **Reads:** Git diff, git log, staged diff
- **Writes:** `.claude-state/review-passes/{pass}.md` (7 files)

### Phase: STEP 5 (PR Artifacts)
- **Reads:** `task-definition.md`, verification results, simplify status, review passes
- **Writes:** `commit-message.txt`, `pr-title.txt`, `pr-body.md`, `pr-ready.md`

### Phase: STEP 6 (Loop Check)
- **Reads:** `plan.md`
- **Writes:** Nothing

---

## 9. AGENT DISPATCH DEFINITIONS

**Not applicable.** This skill does not dispatch parallel agents. Single-agent execution following STEP sequence.

---

## 10. FAILURE SCENARIOS

### FS-1: Junction Name Mismatch
- **Trigger:** User types `/go`; command frontend loaded, references `P:/.claude/skills/go/SKILL.md`
- **Propagation:** Junction `go` not found; `/go` command fails to resolve skill
- **Detection:** Command fails at skill resolution step
- **Actual vs Expected:** Expected `/go` to invoke `P:/.claude/skills/go_v1.0/` (the existing junction)
- **Root Cause:** Command frontend references `go` but junction is named `go_v1.0`
- **Verified:** `ls -la P:/.claude/skills/ | grep go` — junction is `go_v1.0`, not `go`

### FS-2: Verification Commands Fail Silently
- **Trigger:** STEP 2 runs verification commands; commands fail
- **Propagation:** Failure not propagated to BLOCKED state; `<promise>BLOCKED</promise>` not emitted
- **Detection:** `risks.md` not updated; skill continues to STEP 3
- **Actual vs Expected:** FAIL should BLOCK progression per skill contract
- **Root Cause:** Skill says "FAIL → risks.md + BLOCKED" but contract doesn't enforce blocking in code

### FS-3: Simplify HIGH/CRITICAL Not Blocking
- **Trigger:** `/simplify` returns HIGH/CRITICAL findings on code diff
- **Propagation:** Contract says "attempt one corrective cycle, re-run, still HIGH → BLOCKED"
- **Detection:** If corrective cycle not run, continues without blocking
- **Root Cause:** STEP 3 is a behavioral contract, not enforced by code

### FS-4: Token Detection Failure (ralph-loop.sh)
- **Trigger:** `/go` emits `<promise>PR_READY</promise>` to stderr instead of stdout
- **Propagation:** `grep -q` against stdout misses token; loop continues
- **Detection:** Safety limit of 10 iterations eventually stops it
- **Actual vs Expected:** Should exit 0 on PR_READY; continues until safety limit
- **Root Cause:** `/go` output stream destination not guaranteed; ralph-loop.sh only checks stdout

---

## APPENDIX: SOURCE FILES

### File A: `P:/packages/cc-skills-sdlc/skills/go/SKILL.md`
- Mfrontmatter: name=local-pr-ready, version=1.0.0, enforcement=blocking
- 6 workflow_steps: worktree_enforcement → task_contract → verify_end_to_end → simplify_code → seven_pass_review → create_pr_artifacts → loop_check
- ~600 LOC markdown

### File B: `P:/packages/cc-skills-sdlc/skills/go/ralph-loop.sh`
- 67 lines bash
- shebang: `#!/usr/bin/env bash`
- Safety: `set -euo pipefail`, max 10 iterations
- Terminal tokens: PR_READY, BLOCKED, ALL_TASKS_COMPLETE, MORE_TASKS_IN_PLAN

### File C: `P:/.claude/commands/go.md` (frontend/junction)
- 19 lines
- Entry point mismatch noted: references non-existent `P:/.claude/skills/go/SKILL.md`
- Junction target: `P:/packages/cc-skills-sdlc/skills/go`

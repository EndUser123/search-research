# Review Bundle: /go Skill

**Generated**: 2026-04-19
**Scope**: `/go` skill — Local PR-Ready Ralph Loop
**File Count**: 2 files
**Execution Mode**: Single agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
| Field | Value |
|-------|-------|
| Skill name | `local-pr-ready` (v0.4.0) |
| Trigger | `/go` |
| Aliases | `/go-local`, `/local-pr-ready` |
| Package | `P:/packages/cc-skills-sdlc/skills/go` |
| Command | `P:/.claude/commands/go.md` |
| Junction | `P:/.claude/skills/go` → `P:/packages/cc-skills-sdlc/skills/go` |

### Domain & Purpose
End-to-end verification skill for solo development. Runs in a git worktree, executes a structured workflow (worktree check → task contract → verify → simplify → review → PR artifacts → loop check), and emits Ralph-loop completion tokens (`<promise>PR_READY</promise>` or `<promise>BLOCKED</promise>`). Creates local PR artifacts but never pushes remotely.

### Scale Metrics
| Metric | Value |
|--------|-------|
| Files | 2 (SKILL.md + command frontend) |
| Skill LOC | ~540 lines |
| Workflow steps | 7 mandatory phases |
| State files created | 6-8 per run |

### Environment
- **OS**: Windows 11 (bash shell via Git Bash/MSYS2)
- **Primary tool**: Claude Code CLI
- **Dependencies**: `git worktree`, `/simplify` plugin (optional), `gh` CLI (optional)

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /go
        │
        ▼
┌─────────────────────────┐
│ STEP 0: Worktree Check  │ ← Blocking gate
│ git worktree list       │
│ git branch --show-curr  │
└────────┬────────────────┘
         │ PASS
         ▼
┌─────────────────────────┐
│ STEP 1: Task Contract  │
│ .claude-state/          │ ← Created in worktree root
│ task-definition.md      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ STEP 1B: Review Depth   │ ← Auto-detect from git diff --stat
│ quick/standard/full     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ STEP 2: Verification    │ ← Run actual commands from task-def
│ output → verification-  │
│ results.txt             │
└────────┬────────────────┘
         │ PASS
         ▼
┌─────────────────────────┐
│ STEP 3: Simplify        │ ← /simplify plugin (optional)
│ HIGH/CRITICAL → block   │
└────────┬────────────────┘
         │ PASS
         ▼
┌─────────────────────────┐
│ STEP 4: Review Passes   │ ← Only passes for detected depth
│ .claude-state/review-   │
│ passes/*.md             │
└────────┬────────────────┘
         │ ALL PASS
         ▼
┌─────────────────────────┐
│ STEP 5: PR Artifacts    │ ← Local only, no push
│ commit-message.txt      │
│ pr-title.txt           │
│ pr-body.md             │
│ pr-ready.md            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ STEP 6: Loop Check      │ ← Read plan.md, emit token
│ <promise>PR_READY</promise>   │
│ <promise>MORE_TASKS...</promise> │
└─────────────────────────┘
```

---

## 3. EXECUTION AND DATA FLOW

### Trigger Path
`/go` (slash command) → loads `Skill("go")` → reads `P:/.claude/skills/go/SKILL.md` (junction target) → executes steps sequentially.

### Ralph Tokens
| Token | When emitted |
|-------|-------------|
| `<promise>PR_READY</promise>` | All steps passed, artifacts created |
| `<promise>BLOCKED</promise>` | Worktree fail, verify fail, simplify HIGH/CRITICAL after 2 cycles |
| `<promise>MORE_TASKS_IN_PLAN</promise>` | Loop check finds remaining tasks |
| `<promise>ALL_TASKS_COMPLETE</promise>` | Loop check finds no remaining tasks |

### Mandatory Ordering
```
STEP 0 → STEP 1 → STEP 1B → STEP 2 → STEP 3 → STEP 4 → STEP 5 → STEP 6
```
No step can be skipped or reordered. Each is a hard gate.

### State Isolation
- All state files written to `.claude-state/` in the **worktree root** (cwd at time of invocation)
- `task-definition.md` is the canonical contract — all subsequent steps read it
- State is not shared across worktrees

---

## 4. COMPONENT INVENTORY

### `P:/packages/cc-skills-sdlc/skills/go/SKILL.md`
Core skill definition. Contains full workflow specification.

| Section | Purpose |
|---------|---------|
| Frontmatter | name, version, triggers, workflow_steps |
| STEP 0 | Worktree enforcement (blocking) |
| STEP 1 | Task contract creation template |
| STEP 1B | Review depth auto-detection |
| STEP 2 | Verification command execution |
| STEP 3 | Simplify plugin invocation |
| STEP 4 | Conditional review passes |
| STEP 5 | Local PR artifact generation |
| STEP 6 | Plan.md loop check |
| Ralph Completion Criteria | Enumeration of all PR_READY requirements |
| Prohibited Actions | 8 hard-blocked actions |

### `P:/.claude/commands/go.md`
Command frontend. Thin wrapper that loads the skill and delegates.

Key instruction: *"Do not recreate the skill's logic manually in this frontend."*

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Worktree enforcement** — Never edit on main. STEP 0 is a hard blocking gate.
2. **Evidence before assertions** — STEP 2 requires actual command output, not "should work".
3. **Local-only PR** — STEP 5 creates artifacts but never runs `git push` or `gh pr create`.
4. **Auto-detected depth** — Review passes scale with change scope (quick/standard/full).
5. **Ralph loop** — `<promise>PR_READY</promise>` signals completion; loop continues if plan.md has more tasks.

### Non-Negotiables
- `/go` must never push to remote
- `/go` must never proceed on main branch
- `/go` must never emit PR_READY without all required artifacts
- Simplify HIGH/CRITICAL requires explicit user waiver (no silent approval)

### Technology Constraints
- Windows 11 compatible (bash shell)
- Requires `git worktree` support
- `/simplify` plugin is optional (graceful skip documented)

---

## 6. KNOWN ISSUES

None currently identified. Full end-to-end test passed 2026-04-19.

| Issue | Status |
|-------|--------|
| Worktree enforcement | VERIFIED — blocks on main, passes in worktree |
| Auto-detect review depth | VERIFIED — quick detected for 1-file change |
| Simplify graceful skip | VERIFIED — SKIPPED when plugin unavailable |
| PR artifacts created | VERIFIED — commit-message.txt, pr-*.md all written |
| Loop check (plan.md) | VERIFIED — emits BLOCKED when plan.md missing, MORE_TASKS when items remain |
| `<promise>PR_READY</promise>` | VERIFIED — emitted after full quick-depth run |

---

## 7. INTEGRATION POINTS

### Invocation
- **Slash command**: `/go` or `/go-local` or `/local-pr-ready`
- **Ralph mode**: `/go --ralph` (auto-detected from plan.md presence)
- **Flags**: `--ralph` enable, `--no-ralph` disable

### State Files (created by skill, consumed by workflow)
```
.claude-state/
├── task-definition.md          # Canonical contract (STEP 1)
├── progress.txt                 # Iteration log (STEP 6)
├── decisions.md                 # Design rationale (STEP 3)
├── risks.md                     # Blocking items (STEP 2/3)
├── verification-results.txt     # Command outputs (STEP 2)
└── review-passes/              # Pass N results (STEP 4)
    ├── correctness.md
    ├── scope.md
    ├── tests.md
    ├── simplicity.md
    ├── regressions.md
    ├── maintainability.md
    └── pr-ready.md
```

### Output Artifacts (STEP 5)
```
commit-message.txt   # Ready for `git commit -F commit-message.txt`
pr-title.txt        # For `gh pr create --title`
pr-body.md          # For `gh pr create --body`
pr-ready.md         # Human-readable final status + next steps
```

### Downstream Consumers
- Human reviewer reads `pr-ready.md`, `commit-message.txt`, `pr-body.md`
- Human runs `git commit` and `gh pr create` manually
- Loop check reads `plan.md` for batch task continuation

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

| Phase | Reads | Writes | Gate Condition |
|-------|-------|--------|---------------|
| STEP 0 | `git worktree list`, `pwd`, `git branch` | — | Must be in worktree |
| STEP 1 | (none) | `.claude-state/task-definition.md` | Must create file |
| STEP 1B | `git diff --stat` | Updates task-definition.md State | Must compute depth |
| STEP 2 | task-definition.md verification commands | `.claude-state/verification-results.txt` | All commands must PASS |
| STEP 3 | `/simplify` plugin output | `.claude-state/decisions.md` (if skip) | PASS or SKIP or WAIVED |
| STEP 4 | task-definition.md Review Depth field | `.claude-state/review-passes/*.md` | All required passes PASS |
| STEP 5 | all above state files | `commit-message.txt`, `pr-title.txt`, `pr-body.md`, `pr-ready.md` | All 4 files created |
| STEP 6 | `plan.md` | — | Emits correct token |

### Quality Gates
- **STEP 0**: Hard block — no artifact creation, no continuation
- **STEP 2**: Hard block — `<promise>BLOCKED</promise>`, no continuation
- **STEP 3**: 2-cycle limit — after 2 failures, hard block
- **STEP 4**: All required passes must PASS
- **STEP 5**: All 4 artifacts must exist before PR_READY token

---

## 9. AGENT DISPATCH DEFINITIONS

This skill does not dispatch subagents. It runs sequentially in the current session.

| Agent | Role | Dispatched | Reads | Writes |
|-------|------|-----------|-------|--------|
| None | — | — | — | — |

---

## 10. FAILURE SCENARIOS

### Failure 1: On Main Branch
- **Trigger**: User runs `/go` from main checkout
- **Propagation**: STEP 0 `git worktree list` detects no worktree or wrong branch
- **Detection**: `ERROR: /go only works inside task worktrees.` emitted, execution stops
- **Actual vs expected**: Expected stop — confirmed working

### Failure 2: Missing plan.md in Ralph Mode
- **Trigger**: `/go --ralph` with no `plan.md` in worktree root
- **Propagation**: STEP 6 reads `plan.md` → file not found
- **Detection**: `<promise>BLOCKED</promise>` emitted
- **Actual vs expected**: Expected block — confirmed working

### Failure 3: Simplify Finds Critical Issues (2-Cycle Limit)
- **Trigger**: `/simplify` returns HIGH/CRITICAL issues
- **Propagation**: STEP 3 → update risks.md → `<promise>BLOCKED</promise>` → wait for user
- **Second cycle**: If still failing after user signal + re-run → hard block
- **Detection**: After 2nd cycle fail, `<promise>BLOCKED</promise>` with no override path
- **Actual vs expected**: Designed behavior — 2-cycle limit prevents infinite loop

### Failure 4: Worktree Cleanup Blocked (Windows Handle)
- **Trigger**: `git worktree remove` on Windows with open file handle
- **Detection**: `error: failed to delete 'P:/worktrees/go-test': Permission denied`
- **Impact**: Worktree directory persists until handles released
- **Mitigation**: Manual cleanup or reboot
- **Recovery**: Worktree is harmless when orphaned; git ignores it until removed

---

## 11. APPENDIX: FULL TEST LOG (2026-04-19)

### Test Setup
```
Worktree: P:/worktrees/go-test (branch: go-test-branch)
plan.md: created with one task "[ ] Add TEST.md to repo"
TEST.md: staged via `git add TEST.md`
```

### Execution Summary
| Step | Result |
|------|--------|
| STEP 0 Worktree enforcement | PASS |
| STEP 1 task-definition.md created | ✓ |
| STEP 1B auto-detect depth | quick (< 3 files, < 50 lines) |
| STEP 2 verification | PASS — `git log` proved TEST.md committed |
| STEP 3 simplify | SKIPPED — plugin unavailable |
| STEP 4 review passes | correctness ✓, scope ✓, pr-ready ✓ |
| STEP 5 artifacts | commit-message.txt ✓, pr-title.txt ✓, pr-body.md ✓, pr-ready.md ✓ |
| STEP 6 loop check | plan.md task complete → `<promise>PR_READY</promise>` ✓ |

### Artifacts Verified
```
commit-message.txt:
  chore: add TEST.md to repo
  VERIFIED: TEST.md committed to repository (12896f9)
  REVIEW DEPTH: quick
  REVIEW PASSES: correctness, scope, pr-ready
  SIMPLIFY: SKIPPED

pr-ready.md:
  Review Depth: quick
  All verification commands: PASS
  Required review passes: PASS
  Simplify: SKIPPED
```

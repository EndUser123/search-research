# Task Lifecycle Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `/task` cheap by default and prevent task deletion unless task-linked evidence is verified through the native task lifecycle.

**Architecture:** Keep the native Claude task list authoritative. Use terminal-scoped receipts as evidence metadata only. Verification produces deletion candidates; the skill performs native `TaskUpdate(status="deleted")` and confirms with `TaskList`. Use one active PostToolUse route for task tracking.

**Tech Stack:** Python 3.14, pytest, Claude Code hooks, native TaskCreate/TaskUpdate/TaskList/TaskGet.

## Global Constraints

- Do not edit generated plugin cache files directly.
- Preserve unrelated dirty workspace changes.
- Do not execute arbitrary verification commands from hooks.
- `VERIFIED` requires task-linked evidence, not a generic passing command.
- Scope all receipts and cleanup by terminal ID plus task ID.
- Run focused tests after every slice and full combined tests before completion.

### Task 1: Repair receipt identity and classification

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/scripts/task_receipt.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/scripts/task_verify.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/tests/test_task_verify.py`

- [ ] Add explicit terminal-aware receipt reads.
- [ ] Preserve same task IDs across terminals in enumeration.
- [ ] Require a baseline plus task-linked changed files or commit evidence before `VERIFIED`.
- [ ] Reject empty repository identity when current-repo verification is requested.
- [ ] Add tests for same-ID terminal collisions, explicit terminal reads, unrelated passing commands, and missing baselines.
- [ ] Run the package task tests.

### Task 2: Make cleanup produce native deletion candidates only

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/scripts/task_verify.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/references/implementation-details.md`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/tests/test_task_verify.py`

- [ ] Stop the Python verifier from deleting tracker files.
- [ ] Emit exact terminal-scoped verified IDs for the skill to pass to native `TaskUpdate(status="deleted")`.
- [ ] Update `/task clean` to call native deletion and then `TaskList` confirmation.
- [ ] Make no-ID cleanup enumerate candidates from the live task list or fail with an explicit required-input message.
- [ ] Add tests proving non-verified and cross-terminal IDs remain untouched.
- [ ] Run package tests.

### Task 3: Consolidate active PostToolUse task routing

**Files:**
- Modify: `P:/.claude/settings.json`
- Modify: `P:/.claude/hooks/posttooluse/task_unresolved_suggester_hook.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_unresolved_suggester_hook.py`
- Test: `P:/.claude/hooks/tests/test_task_hooks.py`

- [ ] Identify the one canonical PostToolUse router.
- [ ] Remove duplicate task tracking/suggester execution from the active settings path.
- [ ] Keep ordinary `TaskList` search-free.
- [ ] Make `/task scan` explicitly invoke the search path.
- [ ] Add a registered-router smoke test showing default `TaskList` does not invoke CHS/CKS.

### Task 4: Capture completion evidence without false verification

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/scripts/task_receipt.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/tests/`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/tests/test_task_verify.py`

- [ ] Capture task baseline metadata at TaskCreate.
- [ ] On completion, write only `NO_EVIDENCE` or `REVIEW` automatically unless explicit task-linked verification evidence exists.
- [ ] Keep explicit `/task done --verify` available for verified completion.
- [ ] Never run arbitrary verification commands automatically from a hook.
- [ ] Test completion without evidence, completion with unrelated passing commands, and completion with valid task-linked evidence.

### Task 5: Full verification and cache reconciliation

- [ ] Reproduce and fix the combined-suite temp-directory failure.
- [ ] Run package tests and workspace hook tests together.
- [ ] Run direct hook smoke tests for TaskCreate, TaskUpdate, TaskList, and TaskGet.
- [ ] Run registered PreToolUse/PostToolUse smoke tests.
- [ ] Verify source/cache hashes and plugin version.
- [ ] Review the final diff against unrelated dirty changes.
- [ ] Commit only task-lifecycle files in atomic commits.

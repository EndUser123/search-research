---
title: "Plan execution consolidated into /go (execute-plan + executing-plans absorbed)"
created: 2026-07-26
source: session-2026-07-26 (skill consolidation decision)
tags: [plan-execution, consolidation, go, execute-plan, executing-plans, decision]
host: both
agent: grok
verification: workspace_verified
---

# Plan execution consolidated into /go

## Decision

`execute-plan` (bundled skill: PR DAG executor) and `executing-plans` (superpowers: checkpoint-based execution) are **absorbed into `/go`'s `plan-execute` profile**. Both source skills are disabled (`SKILL.md` → `SKILL.md.disabled`). `/go` now handles all plan execution adaptively.

## Rationale

1. `/go`'s `plan-execute` profile already implemented the core capabilities: task-by-task execution, dependency-aware DAG parallelization, per-task verification, worktree isolation, execution status tracking, checkbox progress.
2. The `/www` research confirmed the industry consensus: one orchestrator handles plan → execute adaptively (Claude Code, GitHub Copilot App, oh-my-claudecode, Conductor all do this). No other orchestrator splits plan-execution into separate skills.
3. The 5 capabilities unique to `execute-plan` (PR stack assembly, review-fix loop with reviewer persona, cascade-skip, crash recovery, memory flush) were added to `/go`'s `plan-execute` profile as "adaptive execution modes" with auto-detection by plan format.
4. `executing-plans` had no unique capabilities — strictly a subset of what `/go` already does.

## What /go gained

Adaptive execution mode detection:
- **Simple TDD plan** (plan-writer output): inline task-by-task with per-task H6
- **Checkpoint plan** (STOP/ask language): review gates, route to finishing-a-development-branch
- **PR DAG plan** (### PR N: headings with Dependencies:): full orchestration — topo sort, worktree-per-PR, review-fix loop, cascade-skip, stack assembly (Graphite/plain-git), crash recovery, memory flush

## What was disabled

| Skill | Location | Status |
|---|---|---|
| `execute-plan` | `~/.grok/bundled/skills/execute-plan/SKILL.md` | `SKILL.md.disabled` |
| `executing-plans` | `~/.grok/installed-plugins/superpowers-21e2a56d/skills/executing-plans/SKILL.md` | `SKILL.md.disabled` |

## Plan-writer stays separate

`plan-writer` is the **producer** (writes plans). `/go` is the **consumer** (executes plans). `/go` SKILL.md line 103 already routes to plan-writer: "task is 'write/triage a plan' not 'execute this plan'."

## Falsifier

This decision is wrong if:
- `/go`'s `plan-execute` profile fails to properly execute PR DAG plans (the absorbed logic is too complex for inline profile instructions)
- A user needs the standalone `execute-plan` or `executing-plans` invocation and `/go` doesn't auto-route to the right mode

If either occurs, re-enable the disabled skills and route from `/go` as a delegation.

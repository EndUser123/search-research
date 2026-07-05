# red-team plugin

Multi-agent adversarial review pipeline. Invoked as `/red-team:red-team`.

## Layout

- `commands/red-team.md` — orchestrator entry. Defines run_dir, disk-backed findings schema, agent flow, verdict format.
- `agents/red-team-{role}.md` — planner, critic, and specialists (gate-reviewer, workflow-reviewer, security, performance, logic, state, failure-modes, plugin, testing).
- `__lib/orchestrator.py` — deterministic Python orchestrator (Phase 1, pending).
- `tests/test_orchestrator.py` — orchestrator tests (Phase 1, pending).
- `RED_TEAM_ORCHESTRATION.md` — persisted spec (Phase 3, pending).

## Disk-backed handoff (non-negotiable)

The orchestrator holds only file paths; specialist findings load into the critic's ephemeral context. `run_dir = P:/.claude/.artifacts/red-team/{YYYYMMDD-HHMMSS}-{session_id8}/`. Per-specialist: `{run_dir}/{specialist}.json`.

## Invocation cost

Promoting this to a plugin changed invocation from `/red-team` (standalone) to `/red-team:red-team` (namespaced). Agents resolve as `red-team:red-team-{role}`.

## Adjacent systems (do not duplicate)

- `/code-review` — routine code review (file:line shaped).
- `/pre-mortem` — 3-phase adaptive adversarial critique.
- `/adversarial-review` — parallel code review.

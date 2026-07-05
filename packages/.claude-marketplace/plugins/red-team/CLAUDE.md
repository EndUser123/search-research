# red-team plugin

Multi-agent adversarial review pipeline. Invoked as `/red-team:red-team`.

## Layout (current)

- `commands/red-team.md` — orchestrator entry. Single source of truth for `run_dir`, disk-backed findings schema, agent flow, verdict format.
- `agents/red-team-{role}.md` — planner, critic, and specialists (gate-reviewer, workflow-reviewer, security, performance, logic, state, failure-modes, plugin, testing).
- `__lib/findings_schema.py` — pure-logic schema validator (unit-tested via `tests/`).
- `tests/` — schema unit tests + enablement/smoke integration tests.

## Pending

- `__lib/orchestrator.py` — deterministic Python orchestrator (Phase 1, pending).
- `tests/test_orchestrator.py` — orchestrator tests (Phase 1, pending).
- `RED_TEAM_ORCHESTRATION.md` — persisted spec (Phase 3, pending).

## Disk-backed handoff (non-negotiable)

The orchestrator holds only file paths; specialist findings load into the critic's ephemeral context. The canonical `run_dir` spec lives in `commands/red-team.md` → "Findings handoff" — read it there rather than re-stating the path here (a stale literal in this file caused a three-way contradiction between the skill body, this file, and the runtime). Per-specialist: `{run_dir}/{specialist}.json`.

## Invocation cost

Promoting this to a plugin changed invocation from `/red-team` (standalone) to `/red-team:red-team` (namespaced). Agents resolve as `red-team:red-team-{role}`.

## Adjacent systems (do not duplicate)

- `/code-review` — routine code review (file:line shaped).
- `/pre-mortem` — 3-phase adaptive adversarial critique.
- `/adversarial-review` — parallel code review.

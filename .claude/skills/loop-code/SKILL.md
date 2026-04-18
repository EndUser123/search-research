---
name: loop-code
description: Ralph-style autonomous development loop using loop-core utilities
version: 0.4.0
status: stable
author: loop-core contributors
category: development
---

# /loop-code -- Ralph-Style Autonomous Development Loop

Autonomous AI development loop that iterates through a plan, executing tasks and tracking completion state until exit conditions are met.

## Purpose

Implements the Ralph-style autonomous loop pattern:
- Decompose plan into tasks
- Execute tasks sequentially using `/code`
- Track completion state across iterations
- Exit based on configurable policy (completion indicators, exit signals, task completion, verification)

## When to Use

Use `/loop-code` when you have:
- A markdown plan file with tasks (checkbox format `- [ ] TASK-001`)
- Multi-step feature requiring multiple iterations
- Tasks that need autonomous execution with state tracking

## Loop Iteration Workflow

Each iteration follows this sequence:

1. **Detect terminal_id** -- `get_terminal_id()` from loop-core terminal detection
2. **Read loop_state** -- `TerminalStateManager.read_state("loop_state")`; initialize if None
3. **Load config** -- `load_config()` from loop_policy; reads `.claude/loop/config.yaml`
4. **Parse plan** -- `parse_plan_with_cache()` from loop_policy; identifies incomplete tasks (`- [ ]`)
5. **Log iteration_start** -- `log_decision(terminal_id, "iteration_start", {...})` (best-effort)
6. **Execute /code for task** -- invokes `/code` skill with task description
7. **Update loop_state** -- `TerminalStateManager.write_state(..., validate_schema=True)`
8. **Update metrics** -- `update_metrics(terminal_id, {...})` (best-effort)
9. **Check should_exit** -- `should_exit(tasks, loop_state, config)` evaluates exit policy flags
10. **Log iteration_end** -- `log_decision(terminal_id, "iteration_end", {...})` (best-effort)
11. **Log loop_exit** (if should_exit) -- `log_decision(terminal_id, "loop_exit", {...})` (best-effort)

**Result Envelope contract**: `/code` writes detailed output to `.claude/state/loop/task-{task_id}.md` and returns only a small envelope:
```json
{ "status": "done" | "blocked" | "retry", "artifact": ".claude/state/loop/task-TASK-001.md", "summary": "≤3 lines" }
```
The orchestrator reads only the envelope -- full output lives in the artifact file.

**Exit policy** evaluates 4 boolean flags:
- `completion_indicators >= min_completion_indicators` (always required)
- `EXIT_SIGNAL: true` (if `require_exit_signal` is true)
- All tasks complete (if `require_all_tasks_complete` is true)
- Verification passed (if `require_verification_pass` is true)

All enabled conditions must be true for exit (AND logic).

See `references/exit-policy.md` for full configuration, enforcement modes, practical verification, and exit scenarios.

## Usage

### Basic Usage

```bash
/loop-code path/to/plan.md
```

### Example Plan File

```markdown
# Feature: User Authentication

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design database schema for users table
- [ ] TASK-002 Implement password hashing utility
- [ ] TASK-003 Create login endpoint
- [ ] TASK-004 Write unit tests for auth module
- [ ] TASK-005 Verify all tests pass and document API
```

### Loop Execution

Each iteration:
1. Detect terminal_id -> `get_terminal_id()`
2. Read loop_state -> `state_mgr.read_state("loop_state")`
3. Load config -> `load_config(".claude/loop/config.yaml")`
4. Parse plan -> `parse_plan_with_cache("plan.md")`
5. Log iteration_start -> `log_decision(terminal_id, "iteration_start", {iteration, current_task_id, total_tasks})`
6. Execute /code -> `/code TASK-001 Design database schema`
7. Update loop_state -> `state_mgr.write_state("loop_state", state, validate_schema=True)`
8. Update metrics -> `update_metrics(terminal_id, {iterations: 1, tasks_completed: 1, tasks_failed: 0})`
9. Check should_exit -> `should_exit(tasks, loop_state, config)`
10. Log iteration_end -> `log_decision(terminal_id, "iteration_end", {iteration, tasks_completed, should_exit, exit_reason})`
11. Log loop_exit (if should_exit) -> `log_decision(terminal_id, "loop_exit", {total_iterations, exit_reason, final_state})`

Continue until all enabled exit conditions are met.

## Ralph Loop Auto-Enable

The skill integrates with task type detection to auto-enable/disable the loop:
- **Implementation plans** -> Ralph Loop enabled (autonomous execution)
- **Research plans** -> Ralph Loop disabled (manual guidance)

Override flags: `--ralph-enable` (force on) or `--ralph-disable` (force off).

See `references/auto-enable.md` for detection API, configuration, logging, and exit policy interaction.

## Integration with loop-core

This skill uses loop-core utilities:

| Utility | Module | Purpose |
|---------|--------|---------|
| `load_config()` | loop_policy | Load and validate configuration |
| `should_exit()` | loop_policy | Policy-based exit decision |
| `parse_plan_with_cache()` | loop_policy | Parse plan with caching |
| `parse_plan_requirements()` | loop_policy | Extract requirements from plan.md |
| `verify_completion_against_requirements()` | loop_policy | Check requirements satisfied |
| `extract_user_concerns_from_chat()` | loop_policy | Extract user issues from chat |
| `log_decision()` | loop_observability | Log iteration events |
| `update_metrics()` | loop_observability | Update performance metrics |
| `TerminalStateManager` | state_manager | Persist loop state with schema validation |

Terminal isolation: each terminal gets its own state directory.

## Error Handling

- **Task failure**: Mark as failed, continue to next task
- **Plan file not found**: Exit with error
- **Invalid plan format**: Exit with error
- **State corruption**: Recover from backup or restart
- **Config validation error**: Exit with error and diagnostic message
- **Observability failure**: Log warning but continue (best-effort)

## Exit Conditions Quick Reference

| Condition | Purpose | Set By | Config Flag | Enforcement Mode |
|-----------|---------|--------|-------------|------------------|
| `completion_indicators >= min` | Heuristic completion | Auto-incremented | Always required | Both |
| `EXIT_SIGNAL: true` | Explicit LLM judgment | LLM in RALPH_STATUS | `require_exit_signal` | Both |
| All tasks complete | Ensure all tasks done | Checkbox completion | `require_all_tasks_complete` | Enabled only |
| Verification passed | Verification required | Verifier skill | `require_verification_pass` | Enabled only |

See `references/exit-policy.md` for detailed configuration and scenarios.

## Subagent Output Routing Rules

The loop orchestrator is the primary context overflow risk in multi-iteration runs:

- **Task outputs are artifacts, not return values** -- each `/code` writes to `.claude/state/loop/task-{task_id}.md` and returns only a Result Envelope
- **Loop state is disk-backed** -- `loop_state.json` persisted per terminal
- **Chat concern extraction is bounded** -- returns short JSON array of concern counts, not raw transcript
- **Plan is cached** -- `parse_plan_with_cache()` handles this; do not re-read full plan on each iteration
- **Negative existence claims** -- must verify via Glob/Grep before asserting

## Related Commands

- `/code` -- Feature development workflow (executed by loop for each task)
- `/refactor` -- Multi-file refactoring (can be invoked for specific tasks)
- `/verify` -- Verification orchestrator (used when verification enabled)

## Files

- **Skill**: `P:/packages/loop-core/skills/loop-code/SKILL.md`
- **Policy module**: `P:/packages/loop-core/scripts/loop_policy.py`
- **Observability module**: `P:/packages/loop-core/scripts/loop_observability.py`
- **State manager**: `P:/packages/loop-core/scripts/state_manager.py`
- **Plan parser**: `P:/packages/loop-core/scripts/plan_parser.py`
- **Config schema**: `P:/packages/loop-core/scripts/config_schema.py`

See `references/designitecture.md` for flow diagram and module dependency details.
See `references/state-management.md` for state file schema and directory layout.
See `references/observability.md` for event types, log formats, and metrics.
See `references/exit-policy.md` for full exit policy configuration and verification.
See `references/auto-enable.md` for task type detection and auto-enable integration.

## Tags

ralph-loop, autonomous-development, state-management, policy-based-exit, task-iteration, observability

---
name: loop-code
description: Ralph-style autonomous development loop using loop-core utilities
version: 0.3.0
author: loop-core contributors
---

# /loop-code — Ralph-Style Autonomous Development Loop

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

## How It Works

### Loop Iteration Workflow

Each iteration follows this exact sequence:

1. **Detect terminal_id**
   - Uses `get_terminal_id()` from loop-core terminal detection
   - Ensures multi-terminal isolation

2. **Read loop_state**
   - Uses `TerminalStateManager.read_state("loop_state")`
   - Loads: current_task_id, completed_tasks, failed_tasks, completion_indicators
   - Initialize if None

3. **Load config (fresh each iteration)**
   - Uses `load_config()` from loop_policy module
   - Reads `.claude/loop/config.yaml`
   - Validates schema and loads exit policy flags

4. **Parse plan**
   - Uses `parse_plan_with_cache()` from loop_policy module
   - Extracts tasks with caching for performance
   - Identifies incomplete tasks (`- [ ]`)

5. **Log iteration_start** (Observability hook)
   - Uses `log_decision(terminal_id, "iteration_start", {...})` from loop_observability
   - Logs: iteration number, current_task_id, total_tasks
   - Best-effort (never breaks loop on I/O errors)

6. **Execute /code for task**
   - Invokes `/code` skill with task description
   - Waits for completion
   - Captures result

7. **Update loop_state**
   - Uses `TerminalStateManager.write_state("loop_state", state, validate_schema=True)`
   - Updates: current_task_id, completed_tasks, completion_indicators
   - Validates against canonical schema

8. **Update metrics** (Observability hook)
   - Uses `update_metrics(terminal_id, {...})` from loop_observability
   - Logs: tasks_completed, tasks_failed, iterations count
   - Best-effort (never breaks loop on I/O errors)

9. **Check should_exit**
   - Uses `should_exit(tasks, loop_state, config)` from loop_policy module
   - Evaluates 4 boolean flags from exit policy:
     - `completion_indicators >= min_completion_indicators` (always required)
     - `EXIT_SIGNAL: true` (if `require_exit_signal` is true)
     - All tasks complete (if `require_all_tasks_complete` is true)
     - Verification passed (if `require_verification_pass` is true)
   - **Practical verification** (when `verification.enabled: true`):
     - Parses plan requirements from "Acceptance Criteria", "Success Metrics", or "Constraints" sections
     - Checks completed tasks against requirements using 80% fuzzy matching
     - Extracts user concerns from last 10 chat turns (blockers, issues, corrections)
     - Exit only if ALL requirements met AND NO user concerns present

10. **Log iteration_end** (Observability hook)
    - Uses `log_decision(terminal_id, "iteration_end", {...})` from loop_observability
    - Logs: iteration number, tasks_completed, tasks_failed, should_exit, exit_reason
    - Best-effort (never breaks loop on I/O errors)

11. **Log loop_exit** (if should_exit is true) (Observability hook)
    - Uses `log_decision(terminal_id, "loop_exit", {...})` from loop_observability
    - Logs: total_iterations, total_tasks_completed, exit_reason, final_state
    - Best-effort (never breaks loop on I/O errors)

### Exit Policy Configuration

Exit conditions are configured in `.claude/loop/config.yaml`:

```yaml
version: 1
enforcement:
  enabled: true                         # Full policy (default)
                                        # false = Minimal policy (EXIT_SIGNAL + indicators only)
exit_policy:
  min_completion_indicators: 2          # Minimum iterations (default: 2)
  require_exit_signal: true             # Require EXIT_SIGNAL in RALPH_STATUS
  require_all_tasks_complete: true      # Require all tasks marked complete
  require_verification_pass: false      # Require verification to pass
verification:
  enabled: true                         # Practical verification (default)
                                        # false = Disabled
  lookback_turns: 10                    # Chat lookback window for concerns
  fuzzy_match_threshold: 0.8           # Requirement matching threshold (0.0-1.0)
plans:
  default_plan: plan.md
  allow_per_terminal_plan: false
logging:
  decision_log: .claude/loop/logs/decision.log
  verifier_log: .claude/loop/logs/verifier.log
```

**Enforcement Modes (TASK-018)**:

- **`enforcement.enabled: true`** (default): Full policy enforcement
  - All exit policy flags are evaluated (EXIT_SIGNAL, task completion, verification)
  - Stricter quality control before exit
  - Use for production workflows requiring complete verification

- **`enforcement.enabled: false`**: Minimal policy enforcement
  - Only requires `completion_indicators >= min` + `EXIT_SIGNAL: true`
  - Ignores `require_all_tasks_complete` and `require_verification_pass`
  - Use for rapid prototyping or experimental development
  - Faster iteration cycle with fewer exit requirements

**Setting EXIT_SIGNAL**:

The LLM adds this to the plan file's RALPH_STATUS block when it believes all work is complete:

```markdown
## RALPH_STATUS

- EXIT_SIGNAL: true
- completion_indicators: 3
- current_task: TASK-005
```

### Practical Verification

When `verification.enabled: true` (default), the loop uses practical verification instead of formal PRD verification:

**Plan Requirement Extraction**:
- Parses these sections from plan.md (in order of priority):
  - `## Acceptance Criteria`
  - `## Success Metrics`
  - `## Constraints`
- Extracts bullet list items as requirements
- Example:
  ```markdown
  ## Acceptance Criteria
  - [ ] User can authenticate with email/password
  - [ ] Password hashing uses bcrypt
  - [ ] Login endpoint returns JWT token
  ```

**Requirement Verification**:
- Checks each completed task against plan requirements
- Uses 80% fuzzy matching threshold to match tasks to requirements
- Tracks which requirements are satisfied by completed tasks
- Exit blocked if any requirements unmatched

**Chat Concern Extraction**:
- Reads last 10 turns from conversation transcript (auto-detected)
- Looks for user-reported issues:
  - "This is wrong" → issue
  - "Not working" → issue
  - "Blocked by" → blocker
  - "Fix this" → correction
- Exit blocked if any unresolved concerns found

**Configuration**:
```yaml
verification:
  enabled: true                        # Practical verification (default)
  lookback_turns: 10                   # Chat lookback window
  fuzzy_match_threshold: 0.8          # Requirement matching threshold
```

**Policy-based exit flexibility**:

- `min_completion_indicators`: Prevents premature exit on simple tasks
- `require_exit_signal`: LLM's explicit judgment that plan is complete
- `require_all_tasks_complete`: Ensures all tasks are marked done
- `require_verification_pass`: Requires successful verification run
- All enabled conditions must be met for exit (AND logic)

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
1. Detect terminal_id → `get_terminal_id()`
2. Read loop_state → `state_mgr.read_state("loop_state")`
3. Load config → `load_config(".claude/loop/config.yaml")`
4. Parse plan → `parse_plan_with_cache("plan.md")`
5. **Log iteration_start** → `log_decision(terminal_id, "iteration_start", {iteration, current_task_id, total_tasks})`
6. Execute /code → `/code TASK-001 Design database schema`
7. Update loop_state → `state_mgr.write_state("loop_state", state, validate_schema=True)`
8. **Update metrics** → `update_metrics(terminal_id, {iterations: 1, tasks_completed: 1, tasks_failed: 0})`
9. Check should_exit → `should_exit(tasks, loop_state, config)`
10. **Log iteration_end** → `log_decision(terminal_id, "iteration_end", {iteration, tasks_completed, should_exit, exit_reason})`
11. **Log loop_exit** (if should_exit) → `log_decision(terminal_id, "loop_exit", {total_iterations, exit_reason, final_state})`

Continue until all enabled exit conditions are met.

## Integration with loop-core

This skill uses loop-core utilities:

- **`loop_policy.load_config()`**: Load and validate configuration
- **`loop_policy.should_exit()`**: Policy-based exit decision (includes practical verification)
- **`loop_policy.parse_plan_with_cache()`**: Parse plan with caching
- **`loop_policy.parse_plan_requirements()`**: Extract requirements from plan.md
- **`loop_policy.verify_completion_against_requirements()`**: Check requirements satisfied
- **`loop_policy.extract_user_concerns_from_chat()`**: Extract user issues from chat
- **`loop_observability.log_decision()`**: Log iteration events
- **`loop_observability.update_metrics()`**: Update performance metrics
- **`TerminalStateManager`**: Persist loop state with schema validation
- **Terminal isolation**: Each terminal gets its own state directory

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ /loop-code Skill                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Detect      │───→│ Read State   │───→│ Load Config  │  │
│  │ terminal_id │    │ (state_mgr)  │    │ (loop_policy)│  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         │                                      │           │
│         │         ┌──────────────┐             │           │
│         └────────→│ Parse Plan   │←────────────┘           │
│                   │ (loop_policy)│                         │
│                   └──────────────┘                         │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Execute /code│                          │
│                   └──────┬──────┘                          │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Update State│                          │
│                   │ + Log Event │                          │
│                   └──────┬──────┘                          │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Check Exit  │                          │
│                   │ (should_exit)│                         │
│                   └──────┬──────┘                          │
│                          │                                 │
│               ┌──────────┴──────────┐                      │
│               │                     │                      │
│          Exit true             Exit false                  │
│               │                     │                      │
│          ┌────┴────┐         ┌─────┴─────┐               │
│          │  EXIT   │         │  CONTINUE  │               │
│          └─────────┘         └───────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## State Management

The loop persists state to terminal-local directory:

```
~/.claude/state/terminals/<terminal_id>/
├── loop_state.json          # Current loop state (validated)
├── loop_metrics.json        # Performance metrics (best-effort)
└── logs/
    └── decision.log         # Decision log (JSON lines)
```

**State file structure** (`loop_state.json`) - Canonical Schema:

```json
{
  "current_task_id": "TASK-003",
  "completed_tasks": ["TASK-001", "TASK-002"],
  "failed_tasks": [],
  "completion_indicators": 2,
  "loop_metadata": {
    "plan_path": "/path/to/plan.md",
    "started_at": "2026-03-14T10:00:00",
    "last_update": "2026-03-14T10:15:00",
    "iterations": 3
  }
}
```

All writes to `loop_state.json` use `validate_schema=True` to ensure canonical schema compliance.

## Observability

The loop logs decision events to `decision.log` (JSON lines format) and metrics to `loop_metrics.json`:

### Decision Log Events

```json
{"terminal_id": "term_001", "event": "iteration_start", "payload": {"iteration": 1, "current_task_id": "TASK-001", "total_tasks": 5}, "timestamp": "2026-03-14T10:00:00"}
{"terminal_id": "term_001", "event": "iteration_end", "payload": {"iteration": 1, "tasks_completed": ["TASK-001"], "tasks_failed": [], "should_exit": false, "exit_reason": null}, "timestamp": "2026-03-14T10:05:31"}
{"terminal_id": "term_001", "event": "iteration_start", "payload": {"iteration": 2, "current_task_id": "TASK-002", "total_tasks": 5}, "timestamp": "2026-03-14T10:05:32"}
{"terminal_id": "term_001", "event": "iteration_end", "payload": {"iteration": 2, "tasks_completed": ["TASK-001", "TASK-002"], "tasks_failed": [], "should_exit": true, "exit_reason": "all_tasks_complete"}, "timestamp": "2026-03-14T10:10:45"}
{"terminal_id": "term_001", "event": "loop_exit", "payload": {"total_iterations": 2, "total_tasks_completed": 2, "exit_reason": "all_tasks_complete", "final_state": {...}}, "timestamp": "2026-03-14T10:10:46"}
{"terminal_id": "term_001", "event": "error", "payload": {"error_type": "PlanParseError", "error_message": "Plan file not found", "iteration": 3, "current_task_id": "TASK-003"}, "timestamp": "2026-03-14T10:15:00"}
```

### Event Types

- **iteration_start**: Logged at the beginning of each iteration
  - Payload: `iteration`, `current_task_id`, `total_tasks`

- **iteration_end**: Logged at the end of each iteration
  - Payload: `iteration`, `tasks_completed` (array), `tasks_failed` (array), `should_exit`, `exit_reason`

- **loop_exit**: Logged when the loop exits (after final iteration)
  - Payload: `total_iterations`, `total_tasks_completed`, `exit_reason`, `final_state`

- **error**: Logged when an error occurs during iteration
  - Payload: `error_type`, `error_message`, `iteration`, `current_task_id`, `traceback` (optional)

### Loop Metrics File

`loop_metrics.json` contains aggregated metrics:

```json
{
  "iterations": 5,
  "tasks_completed": 5,
  "tasks_failed": 0,
  "last_update": "2026-03-14T10:10:46"
}
```

Best-effort logging: I/O errors never break loop execution.

## Error Handling

- **Task failure**: Mark as failed, continue to next task
- **Plan file not found**: Exit with error
- **Invalid plan format**: Exit with error
- **State corruption**: Recover from backup or restart
- **Config validation error**: Exit with error and diagnostic message
- **Observability failure**: Log warning but continue (best-effort)
- **Error event logging**: Use `log_decision(terminal_id, "error", {...})` to log errors with details:
  - `error_type`: Exception class name
  - `error_message`: Error message
  - `iteration`: Current iteration number
  - `current_task_id`: Task being executed when error occurred
  - `traceback`: Optional traceback string for debugging

## Exit Conditions Reference

| Condition | Purpose | Set By | Config Flag | Enforcement Mode |
|-----------|---------|--------|-------------|------------------|
| `completion_indicators >= min` | Heuristic completion | Auto-incremented | Always required | Both |
| `EXIT_SIGNAL: true` | Explicit LLM judgment | LLM in RALPH_STATUS | `require_exit_signal` | Both |
| All tasks complete | Ensure all tasks done | Checkbox completion | `require_all_tasks_complete` | Enabled only |
| Verification passed | Verification required | Verifier skill | `require_verification_pass` | Enabled only |

**Exit logic**: ALL enabled conditions must be true (AND logic).

**Enforcement modes**:
- **`enforcement.enabled: true`**: All conditions apply (full policy)
- **`enforcement.enabled: false`**: Only `completion_indicators >= min` + `EXIT_SIGNAL: true` (minimal policy)

**Example scenarios**:
- If `completion_indicators = 0` and `EXIT_SIGNAL: true` → Continue (min not met)
- If `completion_indicators = 5` and `EXIT_SIGNAL: false` → Continue (signal not set)
- If all tasks complete but `verification_status.passed = false` → Continue (enforcement enabled, verification required and failed)
- If `enforcement.enabled: false`, incomplete tasks, but `EXIT_SIGNAL: true` → Exit (minimal policy, ignores task completion)
- If all conditions met → Exit (all enabled conditions satisfied)

## Related Commands

- `/code` — Feature development workflow (executed by loop for each task)
- `/refactor` — Multi-file refactoring (can be invoked for specific tasks)
- `/verify` — Verification orchestrator (used when verification enabled)

## Files

- **Skill**: `P:/packages/loop-core/skills/loop-code/SKILL.md`
- **Policy module**: `P:/packages/loop-core/scripts/loop_policy.py`
- **Observability module**: `P:/packages/loop-core/scripts/loop_observability.py`
- **State manager**: `P:/packages/loop-core/scripts/state_manager.py`
- **Plan parser**: `P:/packages/loop-core/scripts/plan_parser.py`
- **Config schema**: `P:/packages/loop-core/scripts/config_schema.py`
- **Documentation**: `P:/packages/loop-core/README.md`, `P:/packages/loop-core/ARCHITECTURE.md`

## Tags

ralph-loop, autonomous-development, state-management, policy-based-exit, task-iteration, observability

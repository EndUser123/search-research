# Observability

The loop logs decision events to `decision.log` (JSON lines format) and metrics to `loop_metrics.json`.

## Decision Log Events

```json
{"terminal_id": "term_001", "event": "iteration_start", "payload": {"iteration": 1, "current_task_id": "TASK-001", "total_tasks": 5}, "timestamp": "2026-03-14T10:00:00"}
{"terminal_id": "term_001", "event": "iteration_end", "payload": {"iteration": 1, "tasks_completed": ["TASK-001"], "tasks_failed": [], "should_exit": false, "exit_reason": null}, "timestamp": "2026-03-14T10:05:31"}
{"terminal_id": "term_001", "event": "iteration_start", "payload": {"iteration": 2, "current_task_id": "TASK-002", "total_tasks": 5}, "timestamp": "2026-03-14T10:05:32"}
{"terminal_id": "term_001", "event": "iteration_end", "payload": {"iteration": 2, "tasks_completed": ["TASK-001", "TASK-002"], "tasks_failed": [], "should_exit": true, "exit_reason": "all_tasks_complete"}, "timestamp": "2026-03-14T10:10:45"}
{"terminal_id": "term_001", "event": "loop_exit", "payload": {"total_iterations": 2, "total_tasks_completed": 2, "exit_reason": "all_tasks_complete", "final_state": {...}}, "timestamp": "2026-03-14T10:10:46"}
{"terminal_id": "term_001", "event": "error", "payload": {"error_type": "PlanParseError", "error_message": "Plan file not found", "iteration": 3, "current_task_id": "TASK-003"}, "timestamp": "2026-03-14T10:15:00"}
```

## Event Types

- **iteration_start**: Logged at the beginning of each iteration
  - Payload: `iteration`, `current_task_id`, `total_tasks`

- **iteration_end**: Logged at the end of each iteration
  - Payload: `iteration`, `tasks_completed` (array), `tasks_failed` (array), `should_exit`, `exit_reason`

- **loop_exit**: Logged when the loop exits (after final iteration)
  - Payload: `total_iterations`, `total_tasks_completed`, `exit_reason`, `final_state`

- **error**: Logged when an error occurs during iteration
  - Payload: `error_type`, `error_message`, `iteration`, `current_task_id`, `traceback` (optional)

## Loop Metrics File

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

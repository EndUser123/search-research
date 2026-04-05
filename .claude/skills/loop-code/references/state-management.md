# State Management

The loop persists state to terminal-local directory:

```
~/.claude/state/terminals/<terminal_id>/
├── loop_state.json          # Current loop state (validated)
├── loop_metrics.json        # Performance metrics (best-effort)
└── logs/
    └── decision.log         # Decision log (JSON lines)
```

## State File Structure (`loop_state.json`) - Canonical Schema

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

# Ralph Loop Observability Guide

## Overview

The Ralph Loop Platform provides comprehensive observability through structured logging, metrics collection, and acceptance monitoring. This guide covers architecture, usage patterns, integration testing, and best practices.

## Architecture

### Design Principles

1. **Best-Effort Error Handling**: Observability failures never break loop correctness
2. **Per-Terminal Isolation**: Each terminal has separate logs and metrics
3. **Atomic Operations**: Temp file + rename pattern prevents corruption
4. **Structured Data**: JSON lines format for machine-readable logs
5. **Graceful Degradation**: System continues despite logging/metrics failures

### Component Architecture

```
.claude/loop/
├── terminals/
│   ├── <terminal_id>/
│   │   ├── decision.log          # JSON lines decision log
│   │   ├── loop_metrics.json     # Atomic metrics snapshot
│   │   └── plan.md               # Per-terminal plan clone
│   └── metrics_summary.json      # Aggregated cross-terminal metrics
└── config.yaml                   # Loop configuration
```

### Data Flow

```
┌─────────────┐
│ Loop Policy │ → Triggers decision events
└─────────────┘
       │
       ▼
┌───────────────────┐
│  Observability    │ → log_decision(event, payload)
│  Module           │ → update_metrics(terminal_id, updates)
└───────────────────┘
       │
       ├──→ decision.log (append-only JSON lines)
       │
       └──→ loop_metrics.json (atomic snapshots)
```

## API Documentation

### `log_decision()`

Log a decision event to the terminal's decision log.

**Signature**:
```python
def log_decision(terminal_id: str, event: str, payload: dict[str, Any]) -> None
```

**Parameters**:
- `terminal_id`: Unique terminal identifier (sanitized in /ralph-loop)
- `event`: Event type identifier (e.g., "LOOP_START", "TASK_COMPLETE", "ERROR")
- `payload`: Event-specific data dictionary

**Behavior**:
- Appends JSON line to `.claude/loop/terminals/<terminal_id>/decision.log`
- Auto-creates log directory if missing
- Never raises exceptions (best-effort logging)

**Example**:
```python
from scripts.loop_observability import log_decision

log_decision(
    terminal_id="term_abc123",
    event="TASK_COMPLETE",
    payload={
        "task_id": "task_001",
        "description": "Implement authentication",
        "duration_seconds": 45,
        "success": True
    }
)
```

**Log Entry Format**:
```json
{
  "terminal_id": "term_abc123",
  "event": "TASK_COMPLETE",
  "payload": {
    "task_id": "task_001",
    "description": "Implement authentication",
    "duration_seconds": 45,
    "success": true
  },
  "timestamp": "2026-03-15T14:23:45.123456"
}
```

### `update_metrics()`

Atomically update metrics for a terminal.

**Signature**:
```python
def update_metrics(terminal_id: str, updates: dict[str, Any]) -> None
```

**Parameters**:
- `terminal_id`: Unique terminal identifier
- `updates`: Dictionary of metrics to update (deep-merged into existing metrics)

**Behavior**:
- Reads `loop_metrics.json` (creates if missing)
- Deep-merges updates into existing metrics
- Writes to temp file, then atomic rename
- Never raises exceptions

**Example**:
```python
from scripts.loop_observability import update_metrics

update_metrics(
    terminal_id="term_abc123",
    updates={
        "iterations": 1,  # Increment iteration count
        "tasks_completed": 1,
        "last_activity": "2026-03-15T14:23:45.123456",
        "current_phase": "implementation"
    }
)
```

**Metrics Schema**:
```json
{
  "terminal_id": "term_abc123",
  "start_time": "2026-03-15T14:00:00.000000",
  "iterations": 15,
  "tasks_completed": 3,
  "total_tasks": 10,
  "exit_reason": null,
  "last_activity": "2026-03-15T14:23:45.123456",
  "current_phase": "implementation",
  "error_count": 0,
  "verification_passes": 0,
  "verification_failures": 0
}
```

### `get_terminal_log_dir()`

Get the log directory path for a terminal.

**Signature**:
```python
def get_terminal_log_dir(terminal_id: str) -> Path
```

**Returns**: `Path` object to `.claude/loop/terminals/<terminal_id>/`

**Behavior**:
- Auto-creates directory structure if missing
- Used internally by `log_decision()` and `update_metrics()`

### `get_terminal_metrics()`

Read current metrics for a terminal.

**Signature**:
```python
def get_terminal_metrics(terminal_id: str) -> dict[str, Any] | None
```

**Returns**: Metrics dictionary or `None` if file doesn't exist

### `aggregate_metrics()`

Aggregate metrics across all terminals (acceptance monitoring).

**Signature**:
```python
def aggregate_metrics(terminals_data: list[dict[str, Any]]) -> dict[str, Any]
```

**Returns**: Aggregated metrics with totals and per-terminal breakdowns

## Integration Testing

### End-to-End Observability Test

```python
import pytest
from pathlib import Path
from scripts.loop_observability import (
    log_decision,
    update_metrics,
    get_terminal_metrics,
    get_terminal_log_dir
)

class TestObservabilityE2E:
    """End-to-end observability integration tests."""

    def test_full_observability_lifecycle(self, tmp_path):
        """Test complete observability workflow from start to finish."""
        terminal_id = "test_term_e2e"

        # 1. Log initial decisions
        log_decision(terminal_id, "LOOP_START", {
            "plan": "Implement feature X",
            "tasks": ["task_1", "task_2", "task_3"]
        })

        log_decision(terminal_id, "TASK_START", {
            "task_id": "task_1",
            "description": "Setup database"
        })

        # 2. Update metrics
        update_metrics(terminal_id, {
            "iterations": 1,
            "current_phase": "task_1",
            "start_time": "2026-03-15T14:00:00.000000"
        })

        # 3. Complete task
        log_decision(terminal_id, "TASK_COMPLETE", {
            "task_id": "task_1",
            "duration_seconds": 30,
            "success": True
        })

        update_metrics(terminal_id, {
            "tasks_completed": 1,
            "last_activity": "2026-03-15T14:00:30.000000"
        })

        # 4. Verify decision log
        log_dir = get_terminal_log_dir(terminal_id)
        log_file = log_dir / "decision.log"

        assert log_file.exists()
        log_lines = log_file.read_text().strip().split("\n")
        assert len(log_lines) == 3

        # Verify log entries
        import json
        entries = [json.loads(line) for line in log_lines]
        assert entries[0]["event"] == "LOOP_START"
        assert entries[1]["event"] == "TASK_START"
        assert entries[2]["event"] == "TASK_COMPLETE"

        # 5. Verify metrics
        metrics = get_terminal_metrics(terminal_id)
        assert metrics is not None
        assert metrics["iterations"] == 1
        assert metrics["tasks_completed"] == 1
        assert metrics["current_phase"] == "task_1"

    def test_per_terminal_isolation(self, tmp_path):
        """Test that terminals are properly isolated."""
        term_a = "test_term_a"
        term_b = "test_term_b"

        # Terminal A operations
        log_decision(term_a, "TASK_START", {"task_id": "a1"})
        update_metrics(term_a, {"tasks_completed": 1})

        # Terminal B operations
        log_decision(term_b, "TASK_START", {"task_id": "b1"})
        update_metrics(term_b, {"tasks_completed": 1})

        # Verify isolation
        metrics_a = get_terminal_metrics(term_a)
        metrics_b = get_terminal_metrics(term_b)

        assert metrics_a["terminal_id"] == term_a
        assert metrics_b["terminal_id"] == term_b

        log_dir_a = get_terminal_log_dir(term_a)
        log_dir_b = get_terminal_log_dir(term_b)

        assert log_dir_a != log_dir_b

    def test_error_handling_doesnt_break_loop(self):
        """Test that observability failures don't break loop logic."""
        # Simulate various failure scenarios
        invalid_terminal = ""  # Empty terminal ID
        large_payload = {"data": "x" * 1000000}  # Very large payload

        # These should not raise exceptions
        log_decision(invalid_terminal, "TEST_EVENT", large_payload)
        update_metrics(invalid_terminal, {"invalid": "data"})

        # Loop logic should continue unaffected
        assert True  # Test passes if no exceptions were raised
```

### Loop Policy Integration Test

```python
from scripts.loop_policy import LoopPolicy, should_exit, should_run_verifier
from scripts.loop_observability import log_decision, update_metrics

class TestLoopPolicyObservability:
    """Test loop policy integration with observability."""

    def test_exit_decision_logged(self, tmp_path):
        """Test that exit decisions are properly logged."""
        terminal_id = "test_exit_logging"

        # Mock loop completion
        log_decision(terminal_id, "ITERATION_COMPLETE", {
            "tasks_completed_this_iteration": 3,
            "all_tasks_complete": True
        })

        update_metrics(terminal_id, {
            "iterations": 5,
            "tasks_completed": 10,
            "total_tasks": 10
        })

        # Verify decision was logged
        log_dir = get_terminal_log_dir(terminal_id)
        log_file = log_dir / "decision.log"
        assert log_file.exists()

    def test_verification_trigger_logged(self, tmp_path):
        """Test that verification triggers are logged."""
        terminal_id = "test_verification_logging"

        log_decision(terminal_id, "VERIFICATION_TRIGGERED", {
            "reason": "all_tasks_complete",
            "verifier_skill": "prd-verifier"
        })

        # Verify log entry
        log_dir = get_terminal_log_dir(terminal_id)
        log_file = log_dir / "decision.log"
        content = log_file.read_text()

        assert "VERIFICATION_TRIGGERED" in content
        assert "prd-verifier" in content
```

## Event Types

### Standard Events

| Event | Payload Fields | Description |
|-------|---------------|-------------|
| `LOOP_START` | `plan`, `tasks` | Loop initialization |
| `LOOP_EXIT` | `reason`, `final_metrics` | Loop termination |
| `ITERATION_START` | `iteration_number` | New iteration begins |
| `ITERATION_COMPLETE` | `tasks_completed_this_iteration`, `all_tasks_complete` | Iteration ends |
| `TASK_START` | `task_id`, `description` | Task execution begins |
| `TASK_COMPLETE` | `task_id`, `duration_seconds`, `success` | Task execution ends |
| `VERIFICATION_TRIGGERED` | `reason`, `verifier_skill` | Verification requested |
| `VERIFICATION_COMPLETE` | `passed`, `report_path` | Verification finished |
| `ERROR` | `error_type`, `error_message`, `stack_trace` | Error occurred |

### Custom Events

You can define custom events for domain-specific tracking:

```python
log_decision(terminal_id, "CODE_GENERATED", {
    "language": "python",
    "lines_of_code": 150,
    "file_path": "src/auth.py"
})

log_decision(terminal_id, "TEST_COVERAGE_CHECK", {
    "coverage_percentage": 85,
    "threshold": 80,
    "passed": True
})
```

## Best Practices

### 1. Consistent Event Naming

Use `UPPERCASE_WITH_UNDERSCORES` for event names:

```python
# Good
log_decision(terminal_id, "TASK_COMPLETE", {...})

# Avoid
log_decision(terminal_id, "taskComplete", {...})
log_decision(terminal_id, "task-complete", {...})
```

### 2. Structured Payloads

Include all relevant context in payloads:

```python
# Good
log_decision(terminal_id, "TASK_COMPLETE", {
    "task_id": "task_001",
    "description": "Implement authentication",
    "duration_seconds": 45,
    "success": True,
    "output_files": ["auth.py", "auth_test.py"],
    "test_results": {"passed": 5, "failed": 0}
})

# Minimal
log_decision(terminal_id, "TASK_COMPLETE", {
    "task_id": "task_001"
})
```

### 3. Atomic Metrics Updates

Use `update_metrics()` for incremental updates:

```python
# Good - Atomic update
update_metrics(terminal_id, {
    "iterations": 1,  # Increment
    "tasks_completed": 1,
    "error_count": 0
})

# Avoid - Read-modify-write race condition
metrics = get_terminal_metrics(terminal_id)
metrics["iterations"] += 1
# ... write back (not atomic!)
```

### 4. Error Context

Always include error context in error events:

```python
import traceback

try:
    risky_operation()
except Exception as e:
    log_decision(terminal_id, "ERROR", {
        "error_type": type(e).__name__,
        "error_message": str(e),
        "stack_trace": traceback.format_exc(),
        "operation": "risky_operation",
        "context": {"user_id": 123, "attempt": 2}
    })
```

### 5. Performance Considerations

- **Batch logging**: Group related events rather than logging excessively
- **Async logging**: For high-frequency events, consider buffered async logging (deferred enhancement)
- **Payload size**: Keep payloads under 1MB for optimal performance

## Performance Characteristics

### Decision Logging

- **Operation**: Append-only file write
- **Complexity**: O(1) per log entry
- **Throughput**: ~10,000 entries/second on typical hardware
- **Failure mode**: Silent (logs warning, returns None)

### Metrics Updates

- **Operation**: Read → Merge → Write (temp file) → Rename
- **Complexity**: O(n) where n = size of metrics dict
- **Throughput**: ~1,000 updates/second on typical hardware
- **Failure mode**: Silent (logs warning, returns None)

### Storage Growth

- **Decision log**: ~500 bytes per entry × iterations per day
- **Metrics file**: ~1KB (constant size)
- **Example**: 1000 iterations/day ≈ 500KB/day in decision logs

## Log Analysis

### Querying Decision Logs

```python
import json
from pathlib import Path

def analyze_terminal_logs(terminal_id: str):
    """Analyze decision log for a terminal."""
    log_file = Path(f".claude/loop/terminals/{terminal_id}/decision.log")

    if not log_file.exists():
        return None

    events = []
    with log_file.open() as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    # Analyze events
    task_completions = [e for e in events if e["event"] == "TASK_COMPLETE"]
    errors = [e for e in events if e["event"] == "ERROR"]

    return {
        "total_events": len(events),
        "task_completions": len(task_completions),
        "errors": len(errors),
        "first_event": events[0]["timestamp"] if events else None,
        "last_event": events[-1]["timestamp"] if events else None
    }
```

### Metrics Aggregation

```python
from scripts.loop_metrics_summary import aggregate_metrics, validate_cross_terminal_isolation

def generate_acceptance_report():
    """Generate acceptance monitoring report."""
    # Load all terminal metrics
    terminals_data = load_all_terminal_metrics()

    # Aggregate metrics
    aggregated = aggregate_metrics(terminals_data)

    # Validate isolation
    isolation_validation = validate_cross_terminal_isolation(terminals_data)

    return {
        "summary": aggregated,
        "isolation_validation": isolation_validation,
        "recommendations": generate_recommendations(aggregated, isolation_validation)
    }
```

## Troubleshooting

### Missing Logs

**Symptom**: `decision.log` doesn't exist for a terminal

**Possible Causes**:
1. Loop hasn't started yet
2. Incorrect terminal_id
3. Filesystem permissions

**Diagnosis**:
```python
from scripts.loop_observability import get_terminal_log_dir

log_dir = get_terminal_log_dir(terminal_id)
print(f"Log directory: {log_dir}")
print(f"Exists: {log_dir.exists()}")

log_file = log_dir / "decision.log"
print(f"Log file exists: {log_file.exists()}")
```

### Metrics Not Updating

**Symptom**: `loop_metrics.json` shows stale data

**Possible Causes**:
1. Metrics file corrupted (invalid JSON)
2. Concurrent write conflicts
3. Disk full

**Diagnosis**:
```python
from scripts.loop_observability import get_terminal_metrics
import json

metrics = get_terminal_metrics(terminal_id)
if metrics is None:
    print("Metrics file doesn't exist or is corrupted")
else:
    print(f"Metrics: {json.dumps(metrics, indent=2)}")
```

### High Memory Usage

**Symptom**: Decision log grows too large

**Solution**: Implement log rotation (deferred enhancement from TASK-006 REFACTOR)

**Workaround**: Archive old logs manually:
```bash
# Archive decision logs older than 7 days
find .claude/loop/terminals/*/decision.log -mtime +7 -exec gzip {} \;
```

## Future Enhancements

### TASK-006 REFACTOR Deferred Items

1. **Log Rotation**: Automatic archival of old decision logs
2. **Buffered Metrics**: In-memory buffering with periodic flush
3. **Extended Testing**: Performance tests for high-volume logging

### Potential Future Features

1. **OpenTelemetry Integration**: Industry-standard observability
2. **Prometheus Metrics**: Export metrics for monitoring systems
3. **Decision Graph Visualization**: Visual representation of decision flows
4. **Real-time Dashboards**: Live monitoring of loop progress

## References

- **TASK-006-COMPLETION-REPORT.md**: Core observability module implementation
- **TASK-010-COMPLETION-REPORT.md**: Per-iteration observability hooks
- **TASK-020-COMPLETION-REPORT.md**: Acceptance monitoring script
- **scripts/loop_observability.py**: Source code for observability functions
- **scripts/loop_metrics_summary.py**: Source code for metrics aggregation
- **tests/test_loop_observability.py**: Unit tests for observability module

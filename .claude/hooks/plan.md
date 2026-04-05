# Enhanced UPS Logging Implementation Plan

## Overview
Add comprehensive execution tracing to UserPromptSubmit hooks to diagnose why Claude Code displays "hook error" messages when hooks succeed. Current logs show no errors, but we need to capture what hooks actually return and correlate with UI error timestamps.

## Architecture
**Module**: `UserPromptSubmit_modules/registry.py`
**New log file**: `logs/diagnostics/ups_execution_trace.jsonl`

### Components
1. **Execution Tracing**: Log every hook run (success/failure)
2. **Stdout/Stderr Capture**: Capture what each hook module writes
3. **Final Results Logging**: Log summary of what registry.py returns
4. **Session Correlation**: Include session_id and terminal_id in all entries

## Data Flow

```
UserPromptSubmit event
    ↓
registry.py:run_hooks()
    ↓
For each hook:
    1. Capture stdout/stderr
    2. Execute hook
    3. Log execution trace (hook, result, stdout, stderr)
    ↓
After all hooks:
    Log final results summary (num_hooks, num_results, result types)
```

## Error Handling
- Logging failures are silent (don't break hooks)
- Use try/except around all log writes
- Fallback to existing ups_module_errors.jsonl for exceptions

## Test Strategy

### Unit Tests
1. Test execution trace logging (verify JSON structure)
2. Test stdout/stderr capture (verify captured content)
3. Test final results logging (verify summary accuracy)
4. Test logging failure graceful degradation

### Integration Tests
1. Run actual hooks and verify trace log created
2. Verify session_id/terminal_id propagated correctly
3. Verify trace log correlates with timestamps

### Edge Cases
- Empty results list (all hooks returned empty)
- Hook writes to stdout (should be captured)
- Hook writes to stderr (should be captured, marked as error)
- Logging to non-existent directory (create directory)

## Standards Compliance
- **Python 3.12+** patterns: type hints, dataclasses, pathlib
- **Testing**: pytest, fixtures for log file cleanup
- **Code quality**: ruff linting, mypy type checking

## Ramifications
- **New log file**: ups_execution_trace.jsonl (needs log rotation integration)
- **Performance**: Minimal overhead (string buffering, async write not needed)
- **Backwards compatibility**: No changes to hook API, only adds logging

---

## Pre-Mortem (5 minutes)

**Scenario**: "It's 6 months later and this logging system failed. Why?"

### Failure Mode 1: Log file grows unbounded, fills disk
- **Root cause**: No log rotation for ups_execution_trace.jsonl
- **Prevention**: Add to unified log rotation system (__lib/log_rotation.py)
- **Detection**: Monitor file size, alert > 10MB
- **Observation**: Check log rotation stats in Stop hook health summary

### Failure Mode 2: Session ID mismatch, can't correlate errors
- **Root cause**: Claude Code doesn't pass session_id in event data
- **Prevention**: Fall back to "unknown" for missing session_id, still log execution
- **Detection**: Count logs with session_id="unknown" vs actual IDs
- **Observation**: Query logs by timestamp range when session_id unknown

### Failure Mode 3: Stdout capture causes hook to fail
- **Root cause**: Redirecting stdout interferes with hook that expects direct output
- **Prevention**: Use StringIO buffer, only capture during hook execution, restore immediately after
- **Detection**: Hook suddenly fails after logging added, check for stdout-dependent code
- **Observation**: Compare hook exit codes before/after logging in test suite

---

## Implementation Tasks

### Task 1: Add execution trace logging to registry.py
- Add _log_execution_trace() function
- Log before/after each hook execution
- Include session_id, terminal_id, hook name, result summary

### Task 2: Add stdout/stderr capture per hook
- Wrap hook execution with StringIO buffers
- Capture stdout/stderr during execution
- Log captured content in trace entry

### Task 3: Add final results logging
- After all hooks complete, log summary
- Include: num_hooks_run, num_results, result types
- Log to ups_execution_trace.jsonl

### Task 4: Add to unified log rotation
- Add ups_execution_trace.jsonl to rotation policy
- Configure: 1000 entries max, 10MB file size max
- Test rotation works correctly

### Task 5: Write tests
- Test execution trace structure
- Test stdout/stderr capture
- Test final results summary
- Test log rotation integration

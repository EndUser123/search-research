# Plan: Sequential Thinking Hook System

## Overview
Implement automatic sequential thinking trigger detection using hook-orchestrated pipeline (UserPromptSubmit → PreToolUse → Stop) based on validated research blueprint.

## Architecture
**Hook Pipeline:**
```
UserPromptSubmit → Detect triggers, create state file
                    ↓
PreToolUse → Inject system-message for mode, enforce switching
                    ↓
Stop → Read output, save to state, increment counter, loop or cleanup
```

**State File Schema:**
```json
{
  "session_id": "uuid",
  "trigger_phrase": "string",
  "current_iteration": 0,
  "max_iterations": 2,
  "mode": "initial|critique|improvement",
  "intermediate_answers": [],
  "final_answer": null,
  "active": true,
  "terminal_id": "identifier"
}
```

**State Location:** `P:/.claude/state/sequential-thinking/`

**Trigger Patterns:**
- `\bthink\s+step[- ]?by[- ]?step\b`
- `\bcritically\s+analyze\b`
- `\bimprove\s+your\s+reasoning\b`
- `\biterate\s+on\s+your\s+answer\b`

## Implementation Tasks

### TASK-001: Create state management module
- Create `P:/.claude/hooks/__lib/sequential_state.py`
- State file CRUD with terminal_id isolation
- Session UUID generation
- File locking for multi-terminal safety

### TASK-002: Create UserPromptSubmit hook
- Create `P:/.claude/hooks/UserPromptSubmit_sequential_thinking.py`
- Detect trigger patterns in user prompt
- Create state file with current_iteration=0
- Multi-terminal safety: terminal_id in state path

### TASK-003: Create PreToolUse hook
- Create `P:/.claude/hooks/PreToolUse_sequential_thinking.py`
- Check for active sequential thinking state
- Inject system-message based on iteration count
- Mode enforcement: initial → critique → improvement

### TASK-004: Create Stop hook
- Create `P:/.claude/hooks/Stop_sequential_thinking.py`
- Read response output
- Save to state file
- Increment iteration counter
- Loop back if < 2 iterations, cleanup if complete

### TASK-005: Windows-specific considerations
- Use CREATE_NO_WINDOW flag for subprocess calls
- Terminal isolation via terminal_id field
- State path with terminal identifier

### TASK-006: Testing
- Unit tests for state management
- Hook execution tests
- Multi-terminal concurrency tests
- Integration test: full pipeline

## Error Handling
- Missing state file → graceful degradation
- Concurrent writes → file locking
- Invalid terminal_id → generate new UUID
- Max iterations exceeded → forced cleanup

## Rollback
- Remove hooks from settings.json
- Delete state files from `P:/.claude/state/sequential-thinking/`
- No database migrations (file-based only)

## Success Criteria
- [ ] Trigger detection works
- [ ] 2-iteration loop completes
- [ ] Multi-terminal safe
- [ ] State cleanup after completion
- [ ] Tests pass

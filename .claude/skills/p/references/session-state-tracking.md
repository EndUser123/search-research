# Session State Tracking and Fast-Path Reference

## Session-Local State Tracking (Multi-Terminal Safe)

**CRITICAL**: Chat context is ONLY trusted if tests were run in THIS session with no subsequent file edits. This prevents trusting stale test results from previous sessions.

```python
# Initialize/reset state file for THIS terminal's current session
from pathlib import Path
from datetime import datetime
import json
from hooks.terminal_detection import detect_terminal_id

terminal_id = detect_terminal_id()
state_file = Path(f".claude/state/p-fastpath-{terminal_id}.json")
state_dir = state_file.parent
state_dir.mkdir(parents=True, exist_ok=True)

# CRITICAL: Clear stale state from previous sessions (prevents stale data bug)
state_file.unlink(missing_ok=True)

# Initialize fresh state for THIS session
state = {
    "session_start": datetime.now().isoformat(),
    "last_test_run": None,  # timestamp when tests were run
    "files_edited_after_test": []  # files edited since last test run
}
state_file.write_text(json.dumps(state, indent=2))
```

## Fast-Path Safety Check

```python
def can_trust_chat_context(state_file: Path) -> bool:
    """Only trust chat context if tests run THIS session with no subsequent edits."""
    try:
        if not state_file.exists():
            logger.debug("Fast-path: No state file -> using full detection")
            return False

        state = json.loads(state_file.read_text())

        if not state.get("last_test_run"):
            logger.debug("Fast-path: No tests run in this session -> using full detection")
            return False

        if state.get("files_edited_after_test"):
            logger.debug(f"Fast-path: {len(state['files_edited_after_test'])} files edited since tests -> using full detection")
            return False

        logger.debug("Fast-path: Tests run this session, no subsequent edits -> using fast-path")
        return True

    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Fast-path: State read failed ({e}) -> using full detection")
        return False
```

## Fast-Path Activation

If ALL of these conditions are met:
1. Step 0 (Scope Inference) found 5+ file reads
2. Chat context shows test execution results
3. Session state file confirms tests were run THIS session
4. Session state file confirms NO files edited after those tests

Then:
- Skip redundant test collection - Trust the test results from chat context
- Skip file detection - Scope is already clear from Step 0
- Jump directly to Step 2 - Determine next action from context
- Rationale: Avoid 5-10 second redundant operations when context is fresh

## Session State Tracking During Execution

```python
# When tests are run (during detection or in P1 phase):
def record_test_run(state_file: Path):
    """Record that tests were run in this session."""
    state = json.loads(state_file.read_text())
    state["last_test_run"] = datetime.now().isoformat()
    state["files_edited_after_test"] = []  # Reset edit tracking
    state_file.write_text(json.dumps(state, indent=2))

# When files are edited (via Edit/Write tools):
def record_file_edit(state_file: Path, edited_files: list[str]):
    """Record that files were edited after last test run."""
    if not state_file.exists():
        return

    state = json.loads(state_file.read_text())
    if state.get("last_test_run"):
        state["files_edited_after_test"].extend(edited_files)
        state_file.write_text(json.dumps(state, indent=2))
```

This tracking happens automatically during /p execution. When pytest is run in detection or P1, `record_test_run()` is called. When Edit/Write tools are used, `record_file_edit()` is called.

## Model Selection Guidance for Subagents

| Phase | Model | Rationale |
|-------|-------|-----------|
| P1 (Build) | `haiku` | Test collection is mechanical |
| P2 (Review) | `sonnet` | Deep analysis needs quality |
| P3 (Validate) | `haiku` | Linting is mechanical |
| P4-P5 | `sonnet` | Documentation requires reasoning |

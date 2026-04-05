# loop-core Usage Examples

This guide shows practical usage patterns for the loop-core package.

## Table of Contents

1. [Basic State Management](#1-basic-state-management)
2. [Plan File Parsing](#2-plan-file-parsing)
3. [Multi-Terminal Isolation](#3-multi-terminal-isolation)
4. [Lock File Management](#4-lock-file-management)
5. [Complete Loop Example](#5-complete-loop-example)

---

## 1. Basic State Management

### 1.1 Initialize State Manager

```python
from core import TerminalStateManager

# Auto-detect terminal ID (uses WT_SESSION, console window, or PID)
manager = TerminalStateManager()

print(f"Terminal ID: {manager.terminal_id}")
print(f"State directory: {manager.state_dir}")
# Output example:
# Terminal ID: console_a1b2c3d4
# State directory: C:\Users\you\.claude\state\terminals\console_a1b2c3d4
```

### 1.2 Write and Read State

```python
# Write state (atomic - temp file + rename)
manager.write_state("current_task", {
    "id": "TASK-001",
    "status": "in_progress",
    "started_at": "2026-03-14T10:30:00"
})

# Read state
state = manager.read_state("current_task")
print(state)
# Output: {'id': 'TASK-001', 'status': 'in_progress', 'started_at': '2026-03-14T10:30:00'}

# Read missing state returns None
missing = manager.read_state("nonexistent")
print(missing)  # Output: None
```

### 1.3 State Persistence

State is stored as JSON files in the terminal's state directory:

```
.claude/state/terminals/
└── console_a1b2c3d4/
    ├── current_task.json
    ├── loop_state.json
    └── task_history.json
```

**Key features:**
- **Atomic writes**: Uses `tempfile.NamedTemporaryFile` + `os.replace()` for crash-safe updates
- **No TTL**: State persists until explicitly deleted (no stale data from expiration)
- **Terminal-local**: Each terminal has its own directory (no conflicts)

---

## 2. Plan File Parsing

### 2.1 Parse a Plan File

```python
from core import parse_plan_tasks

# Parse plan.md
tasks = parse_plan_tasks("plan.md")

print(f"Found {len(tasks)} tasks")
for task in tasks:
    status = "✓" if task["complete"] else " "
    print(f"{status} [{task['id']}] {task['text']}")
```

### 2.2 Filter Incomplete Tasks

```python
# Get only incomplete tasks
incomplete = [t for t in tasks if not t["complete"]]
print(f"Remaining tasks: {len(incomplete)}")

# Get task metadata
for task in incomplete:
    print(f"Task: {task['text']}")
    print(f"  Tags: {task['tags']}")
    print(f"  Dependencies: {task['dependencies']}")
```

### 2.3 Plan File Format

The parser expects markdown task lists:

```markdown
# My Plan

- [ ] TASK-001 Implement state manager [tag:core] after:TASK-000
- [x] TASK-002 Write tests [tag:testing]
- [ ] TASK-003 Add documentation
```

**Syntax:**
- `- [ ]` for incomplete tasks
- `- [x]` for completed tasks
- `[tag:name]` for tags (optional)
- `after:TASK-ID` for dependencies (optional)

---

## 3. Multi-Terminal Isolation

### 3.1 How Terminal Detection Works

The terminal ID is detected with 5-priority fallback:

```python
from loop_core.terminal_detection import get_terminal_id

# Priority 1: Explicit terminal_id (from hook input)
terminal_id = get_terminal_id({"terminal_id": "my_custom_id"})

# Priority 2: Cached value (thread-local)
# Returns same ID for subsequent calls in same thread

# Priority 3: Environment variables
# CLAUDE_TERMINAL_ID > TERMINAL_ID > TERM_ID > SESSION_TERMINAL

# Priority 4: Console detection
# Windows Terminal: Extracts GUID from WT_SESSION
# Windows Console: Uses GetConsoleWindow() handle

# Priority 5: PID-based fallback
# Format: pid_{process_id}_{timestamp}
```

### 3.2 Terminal Isolation in Practice

```python
# Terminal A (Windows Terminal session A)
manager_a = TerminalStateManager(terminal_id="console_a1b2c3d4")
manager_a.write_state("current_task", {"id": "TASK-001", "terminal": "A"})

# Terminal B (Windows Terminal session B)
manager_b = TerminalStateManager(terminal_id="console_e5f6g7h8")
manager_b.write_state("current_task", {"id": "TASK-002", "terminal": "B"})

# Each terminal has isolated state
state_a = manager_a.read_state("current_task")
state_b = manager_b.read_state("current_task")

print(state_a)  # {'id': 'TASK-001', 'terminal': 'A'}
print(state_b)  # {'id': 'TASK-002', 'terminal': 'B'}

# No conflicts - separate files:
# .claude/state/terminals/console_a1b2c3d4/current_task.json
# .claude/state/terminals/console_e5f6g7h8/current_task.json
```

### 3.3 Force Specific Terminal ID

```python
# For testing or explicit control
manager = TerminalStateManager(terminal_id="test_terminal")
print(manager.state_dir)
# Output: .../terminals/test_terminal
```

---

## 4. Lock File Management

### 4.1 Acquire and Release Locks

```python
# Acquire lock (atomic PID-based ownership)
if manager.acquire_lock("plan_processing"):
    print("Lock acquired")

    try:
        # Critical section - only this terminal can run
        manager.write_state("processing", {"status": "active"})
        # ... do work ...
    finally:
        manager.release_lock("plan_processing")
        print("Lock released")
else:
    print("Lock held by another process")
```

### 4.2 Stale Lock Cleanup

Locks include automatic cleanup of stale PIDs:

```python
# If a process crashes without releasing:
# - Lock file contains PID of crashed process
# - acquire_lock() checks if PID is running
# - If PID not running, lock is automatically cleaned up
# - New lock is acquired successfully

manager.acquire_lock("cleanup_test")
# No need to manually check for stale locks
```

### 4.3 Lock File Format

Lock files contain the PID of the owning process:

```
.claude/state/terminals/console_a1b2c3d4/
└── plan_processing.lock  (contains: "12345")
```

### 4.4 Non-Blocking Lock Attempt

```python
# Try to acquire lock (returns immediately)
if manager.acquire_lock("resource", timeout_sec=0):
    # Lock acquired
    pass
else:
    # Lock held - don't wait
    print("Resource busy, try again later")
```

---

## 5. Complete Loop Example

### 5.1 Ralph-Style Autonomous Loop

```python
from core import TerminalStateManager, parse_plan_tasks
import time

def autonomous_loop(plan_path: str):
    """Run autonomous loop with terminal-local state."""

    # Initialize state manager
    manager = TerminalStateManager()
    print(f"📍 Terminal: {manager.terminal_id}")

    # Parse plan
    tasks = parse_plan_tasks(plan_path)
    print(f"📋 Found {len(tasks)} tasks")

    # Main loop
    while True:
        # Get incomplete tasks
        incomplete = [t for t in tasks if not t["complete"]]

        if not incomplete:
            print("✅ All tasks complete!")
            break

        # Acquire lock for next task
        task = incomplete[0]
        lock_name = f"task_{task['id']}"

        if not manager.acquire_lock(lock_name):
            print(f"⏳ Task {task['id']} locked by another terminal")
            time.sleep(5)
            continue

        try:
            # Update state
            manager.write_state("current_task", {
                "id": task["id"],
                "text": task["text"],
                "status": "in_progress"
            })

            print(f"🔄 Working on {task['id']}: {task['text']}")

            # Simulate work
            time.sleep(2)

            # Mark complete
            manager.write_state("current_task", {
                "id": task["id"],
                "status": "complete"
            })

            print(f"✅ Completed {task['id']}")

        finally:
            manager.release_lock(lock_name)

    print("🎉 Loop complete!")

# Run the loop
if __name__ == "__main__":
    autonomous_loop("plan.md")
```

### 5.2 Multi-Terminal Coordination

```python
# Terminal 1
manager_a = TerminalStateManager()
manager_a.write_state("terminal_role", "coordinator")

# Terminal 2
manager_b = TerminalStateManager()
manager_b.write_state("terminal_role", "worker")

# Both terminals can work on different tasks
# without state conflicts
```

### 5.3 State Recovery After Crash

```python
# State persists across crashes
manager = TerminalStateManager()

# Check previous state
last_state = manager.read_state("current_task")
if last_state:
    print(f"Resuming from: {last_state}")
else:
    print("Fresh start - no previous state")
```

---

## Error Handling

### Handle Missing State

```python
state = manager.read_state("optional_key")
if state is None:
    print("No state found - using defaults")
    state = {"default": True}
```

### Handle Lock Acquisition Failure

```python
if not manager.acquire_lock("resource"):
    # Lock held by another process
    # Options: wait, skip, or fail
    raise RuntimeError("Resource locked - try again later")
```

### Handle Parse Errors

```python
from loop_core.plan_parser import PlanParseError

try:
    tasks = parse_plan_tasks("plan.md")
except PlanParseError as e:
    print(f"Failed to parse plan: {e}")
    # Handle missing or corrupted plan file
```

---

## Testing

### Run Tests

```bash
cd P:\packages\loop-core
pytest tests/ -v --cov
```

### Test Multi-Terminal Isolation

```python
# In one terminal
manager_a = TerminalStateManager(terminal_id="test_a")
manager_a.write_state("test", {"terminal": "A"})

# In another terminal (simulated)
manager_b = TerminalStateManager(terminal_id="test_b")
manager_b.write_state("test", {"terminal": "B"})

# Verify isolation
assert manager_a.read_state("test")["terminal"] == "A"
assert manager_b.read_state("test")["terminal"] == "B"
```

---

## Best Practices

1. **Always use try/finally for locks**:
   ```python
   if manager.acquire_lock("resource"):
       try:
           # work
       finally:
           manager.release_lock("resource")
   ```

2. **Check for None when reading state**:
   ```python
   state = manager.read_state("key") or {"default": True}
   ```

3. **Use descriptive lock names**:
   ```python
   # Good
   manager.acquire_lock("plan_processing_task_001")

   # Avoid
   manager.acquire_lock("lock")
   ```

4. **Let the system detect terminal ID**:
   ```python
   # Good - auto-detects
   manager = TerminalStateManager()

   # Only override when needed
   manager = TerminalStateManager(terminal_id="custom")
   ```

5. **Parse plan once per loop iteration**:
   ```python
   # Good - parse once, then iterate
   tasks = parse_plan_tasks("plan.md")
   for task in tasks:
       # process

   # Avoid - parsing in loop
   for task in parse_plan_tasks("plan.md"):
       # process (re-parses every iteration)
   ```

---

## Architecture Benefits

### Multi-Terminal Safe
- Each terminal has its own state directory
- No Git conflicts or race conditions
- Can run multiple loops in parallel

### Crash Recovery
- State persists in files
- Lock files auto-clean stale PIDs
- Resume from last state after crash

### No Stale Data
- No TTL-based expiration
- State is current or doesn't exist
- Explicit deletion required

### Simple Integration
- Drop-in replacement for Git-based state
- Works with existing plan.md files
- No external dependencies (stdlib only)

---

## Quick Reference

| Operation | Code |
|-----------|------|
| Initialize | `manager = TerminalStateManager()` |
| Write state | `manager.write_state("key", {"data": "value"})` |
| Read state | `state = manager.read_state("key")` |
| Parse plan | `tasks = parse_plan_tasks("plan.md")` |
| Acquire lock | `if manager.acquire_lock("name"):` |
| Release lock | `manager.release_lock("name")` |

---

**See also**: [README.md](README.md) for package overview and installation instructions.

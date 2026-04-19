# `/code` Skill Improvements — Solution Document

**Date**: 2026-03-01  
**Target**: Claude Code optimization (Windows 11, skill-based hooks)  
**Scope**: Address known issues, reduce manual steps, enforce non-negotiables  

---

## OVERVIEW

This document specifies concrete improvements to the `/code` skill to:

1. **Close Known-Issues Loop**: Fix rollback detection, completion guard enforcement, multi-terminal collisions
2. **Reduce Manual Steps**: Auto-maintain ledger, normalize paths, enforce mandatory TRACE
3. **Strengthen Phase & Evidence Modeling**: First-class data structures for phases and evidence
4. **Improve UX**: Add introspection, guided recovery, better error messages

All changes follow Claude Code standards (skill-based hooks, terminal-scoped state files) and Windows-only environment.

---

## 1. STATE MANAGEMENT RATIONALIZATION

### Why Track State?

State enables enforcement of temporal guarantees across invocations, terminals, and interruptions:

- **Phase gating**: "Cannot TRACE before BUILD" requires durable proof BUILD completed
- **TDD evidence**: Track RED/GREEN/REFACTOR/VERIFY completion to enforce 4-evidence requirement
- **Multi-terminal safety**: Terminal-scoped ownership prevents collisions by construction
- **Resumability**: Know what's done, what's missing, what evidence exists after interruption

**Core principle**: State is the minimum memory needed to turn stateless chat into enforceable workflow with BUILD→TRACE→SHIP and RED→GREEN→REFACTOR→VERIFY guarantees.

### State Design Constraints

- **Claude Code standards**: Skill-based hooks (PreToolUse), skill-local state files
- **Terminal-scoped**: Use `{terminal_id}` in filenames to prevent collisions
- **Windows-only**: No WSL/Linux path translation needed
- **Minimal**: Only track what's needed to enforce non-negotiables
- **Fail-closed**: Phase order violations block; missing evidence blocks SHIP

---

## 2. IMPROVED STATE SCHEMA

### 2.1 Phase State (Global, Commit-Aware)

**File**: `.claude/state/code_phase_state.json`

**Purpose**: Track phase completion with rollback detection

**Schema**:
```json
{
  "version": "1.0",
  "last_updated": "2026-03-01T14:20:00-07:00",
  "phases": {
    "BUILD": {
      "completed": true,
      "completed_at": "2026-03-01T12:00:00-07:00",
      "commit_hash": "a1b2c3d4",
      "terminal_id": "term_abc123"
    },
    "STATIC_ANALYSIS": {
      "completed": true,
      "completed_at": "2026-03-01T13:00:00-07:00",
      "commit_hash": "a1b2c3d4",
      "terminal_id": "term_abc123",
      "blocking_issues": 0,
      "warnings": 5
    },
    "TRACE": {
      "completed": true,
      "completed_at": "2026-03-01T14:00:00-07:00",
      "commit_hash": "a1b2c3d4",
      "terminal_id": "term_abc123",
      "findings": {
        "P0": 0,
        "P1": 0,
        "P2": 2,
        "P3": 1
      }
    },
    "SHIP": {
      "completed": false
    }
  },
  "current_phase": "TRACE"
}
```

**Rollback Detection Logic**:
```python
def is_phase_valid(phase_name: str, phase_state: dict) -> bool:
    """Check if phase completion is still valid given current git state."""
    if not phase_state.get("completed"):
        return False
    
    recorded_hash = phase_state.get("commit_hash")
    if not recorded_hash:
        return False
    
    current_hash = get_git_head_hash()
    if current_hash != recorded_hash:
        # Invalidate if commit changed
        return False
    
    return True
```

**Hook Validation**:
- Before allowing STATIC_ANALYSIS/TRACE/SHIP, check `is_phase_valid()` for prerequisites
- If invalid, clear marker and block with clear message

### 2.2 Task Evidence Ledger (Terminal-Scoped)

**File**: `.claude/state/code_evidence_{terminal_id}.json`

**Purpose**: Track RED/GREEN/REFACTOR/VERIFY evidence per task, enable resume

**Schema**:
```json
{
  "version": "1.0",
  "terminal_id": "term_abc123",
  "task_list_id": "auth_feature_20260301",
  "created_at": "2026-03-01T12:00:00-07:00",
  "last_updated": "2026-03-01T14:20:00-07:00",
  "tasks": {
    "task_1": {
      "description": "Implement auth module",
      "evidence": {
        "RED": {
          "completed": true,
          "timestamp": "2026-03-01T12:15:00-07:00",
          "test_files": ["tests/test_auth.py"],
          "test_command": "pytest tests/test_auth.py",
          "failing_tests": 3
        },
        "GREEN": {
          "completed": true,
          "timestamp": "2026-03-01T12:45:00-07:00",
          "impl_files": ["src/auth.py"],
          "test_command": "pytest tests/test_auth.py",
          "passing_tests": 3
        },
        "REFACTOR": {
          "completed": true,
          "timestamp": "2026-03-01T12:50:00-07:00",
          "refactored_files": ["src/auth.py"],
          "test_command": "pytest tests/test_auth.py",
          "passing_tests": 3
        },
        "VERIFY": {
          "completed": true,
          "timestamp": "2026-03-01T12:55:00-07:00",
          "checks": {
            "spec_compliance": true,
            "code_quality": true,
            "error_handling": true
          }
        }
      },
      "status": "DONE",
      "marked_done_at": "2026-03-01T12:55:00-07:00"
    },
    "task_2": {
      "description": "Implement session module",
      "evidence": {
        "RED": {
          "completed": true,
          "timestamp": "2026-03-01T13:00:00-07:00"
        },
        "GREEN": {
          "completed": true,
          "timestamp": "2026-03-01T13:30:00-07:00"
        },
        "REFACTOR": {
          "completed": false
        },
        "VERIFY": {
          "completed": false
        }
      },
      "status": "IN_PROGRESS"
    }
  }
}
```

**Completion Guard Logic**:
```python
def can_mark_task_done(task_id: str, evidence_ledger: dict) -> tuple[bool, str]:
    """Check if task has all 4 evidence types before marking done."""
    task = evidence_ledger["tasks"].get(task_id)
    if not task:
        return False, f"Task {task_id} not found in ledger"
    
    evidence = task.get("evidence", {})
    required = ["RED", "GREEN", "REFACTOR", "VERIFY"]
    missing = [stage for stage in required if not evidence.get(stage, {}).get("completed")]
    
    if missing:
        return False, f"Cannot mark task done: missing evidence for {', '.join(missing)}"
    
    return True, "All evidence present"
```

**Auto-Maintenance**:
- Workflow automatically appends evidence when stages complete
- No manual ledger editing required
- Helper function: `append_evidence(task_id, stage, metadata)`

### 2.3 Build State (Terminal-Scoped)

**File**: `.claude/state/code_build_state_{terminal_id}.json`

**Purpose**: Track current BUILD session, prevent multi-terminal collisions

**Schema**:
```json
{
  "version": "1.0",
  "terminal_id": "term_abc123",
  "task_list_id": "auth_feature_20260301",
  "owner": "term_abc123",
  "started_at": "2026-03-01T12:00:00-07:00",
  "last_activity": "2026-03-01T14:20:00-07:00",
  "status": "ACTIVE",
  "execution_model": "standard",
  "file_count": 3,
  "current_task": "task_2"
}
```

**Multi-Terminal Collision Prevention**:
```python
def acquire_build_ownership(terminal_id: str, task_list_id: str) -> tuple[bool, str]:
    """Acquire ownership of task list, prevent collisions."""
    state_file = f".claude/state/code_build_state_{terminal_id}.json"
    
    # Check if any other terminal owns this task_list_id
    state_dir = Path(".claude/state")
    for existing_state in state_dir.glob("code_build_state_*.json"):
        if existing_state.name == f"code_build_state_{terminal_id}.json":
            continue
        
        data = json.loads(existing_state.read_text())
        if data.get("task_list_id") == task_list_id and data.get("status") == "ACTIVE":
            other_terminal = data.get("terminal_id")
            return False, f"Task list '{task_list_id}' already owned by terminal {other_terminal}"
    
    # Acquire ownership
    write_state(state_file, {
        "terminal_id": terminal_id,
        "task_list_id": task_list_id,
        "owner": terminal_id,
        "started_at": now(),
        "status": "ACTIVE"
    })
    return True, "Ownership acquired"
```

---

## 3. MANDATORY TRACE ENFORCEMENT

### 3.1 Problem

Current state: SKILL.md says TRACE is optional for trivial changes (<10 lines, documentation-only).[file:1]  
This contradicts the non-negotiables and ROI story (60-80% of logic errors caught by TRACE).[file:1]

### 3.2 Solution

Make TRACE mandatory for all code changes, with explicit modes:

**Mode 1: Full TRACE (default for code changes)**
- Required for any `.py`, `.ts`, `.js`, `.go`, etc. file changes
- Uses TRACE_TEMPLATES.md and TRACE_CHECKLIST.md
- Writes full TRACE report to `.claude/trace/report_{timestamp}.md`
- Creates `code-trace-complete.marker` with commit hash

**Mode 2: Light TRACE (for non-executable changes)**
- Allowed ONLY for `.md`, `.txt`, `.json`, `.yaml`, `.toml` config files
- Quick checklist: syntax valid, no secrets, references correct
- Writes minimal TRACE record: "Light TRACE: no executable code changed"
- Creates `code-trace-complete.marker` with commit hash

**Implementation**:

```python
# In hook: validate_code_phase_order.py
def get_trace_mode_required(changed_files: list[str]) -> str:
    """Determine if full or light TRACE is needed."""
    code_extensions = {".py", ".ts", ".js", ".go", ".rs", ".c", ".cpp", ".java"}
    doc_extensions = {".md", ".txt", ".rst"}
    config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini"}
    
    has_code = any(Path(f).suffix in code_extensions for f in changed_files)
    
    if has_code:
        return "full"
    elif any(Path(f).suffix in (doc_extensions | config_extensions) for f in changed_files):
        return "light"
    else:
        return "full"  # Default to full for unknown types
```

**Hook enforcement**:
- Phase order hook checks for `code-trace-complete.marker` before allowing SHIP
- SHIP hook validates marker has valid commit hash matching current HEAD
- No exemptions for "trivial" changes

---

## 4. PATH NORMALIZATION (Windows-Only)

### 4.1 Problem

Current: Path translation errors between Git Bash (`/p/...`) and PowerShell (`P:\...`) cause false verification failures.[file:1]

### 4.2 Solution (Windows-Only)

Create `normalize_paths.py` helper that ensures all paths use Windows native format (`P:\...`):

```python
# .claude/skills/code/utils/normalize_paths.py
from pathlib import Path, WindowsPath
import os
import re

def normalize_path(path_str: str) -> str:
    """Normalize any path format to Windows native (P:\\...)."""
    # Handle Git Bash style: /p/path/to/file -> P:/path/to/file
    if re.match(r'^/[a-z]/', path_str):
        drive_letter = path_str[1].upper()
        rest = path_str[2:]
        path_str = f"{drive_letter}:{rest}"
    
    # Convert to Path object and back to string (uses native format)
    return str(Path(path_str).resolve())

def normalize_paths_in_command(command: str) -> str:
    """Find and normalize all paths in a command string."""
    # Match common path patterns
    path_pattern = r'(?:/[a-z]/[\w/\-.]+|[A-Z]:[/\\][\w/\\\-.]+)'
    
    def replace_path(match):
        return normalize_path(match.group(0))
    
    return re.sub(path_pattern, replace_path, command)
```

**Integration points**:
- Call `normalize_paths_in_command()` before running any verification command
- Call `normalize_path()` when writing file paths to state/ledger
- Call `normalize_path()` when reading file paths from state/ledger

**Usage in workflow**:
```python
# Before running test command
test_command = normalize_paths_in_command(test_command)
result = subprocess.run(test_command, shell=True, capture_output=True)
```

---

## 5. AUTO-MAINTAINED EVIDENCE LEDGER

### 5.1 Problem

Current: Resume ledger updates described as manual, no automatic ledger creation in workflow.[file:1]

### 5.2 Solution

Create `evidence_manager.py` utility that workflow calls after each stage completion:

```python
# .claude/skills/code/utils/evidence_manager.py
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

class EvidenceManager:
    def __init__(self, terminal_id: str):
        self.terminal_id = terminal_id
        self.ledger_file = Path(f".claude/state/code_evidence_{terminal_id}.json")
        self._ensure_ledger_exists()
    
    def _ensure_ledger_exists(self):
        """Create ledger if it doesn't exist."""
        if not self.ledger_file.exists():
            self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
            self.ledger_file.write_text(json.dumps({
                "version": "1.0",
                "terminal_id": self.terminal_id,
                "task_list_id": None,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "tasks": {}
            }, indent=2))
    
    def record_red(self, task_id: str, test_files: list[str], 
                   test_command: str, failing_tests: int):
        """Record RED stage evidence."""
        self._append_evidence(task_id, "RED", {
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "test_files": test_files,
            "test_command": test_command,
            "failing_tests": failing_tests
        })
    
    def record_green(self, task_id: str, impl_files: list[str],
                     test_command: str, passing_tests: int):
        """Record GREEN stage evidence."""
        self._append_evidence(task_id, "GREEN", {
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "impl_files": impl_files,
            "test_command": test_command,
            "passing_tests": passing_tests
        })
    
    def record_refactor(self, task_id: str, refactored_files: list[str],
                        test_command: str, passing_tests: int):
        """Record REFACTOR stage evidence."""
        self._append_evidence(task_id, "REFACTOR", {
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "refactored_files": refactored_files,
            "test_command": test_command,
            "passing_tests": passing_tests
        })
    
    def record_verify(self, task_id: str, checks: dict[str, bool]):
        """Record VERIFY stage evidence."""
        self._append_evidence(task_id, "VERIFY", {
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        })
    
    def can_mark_done(self, task_id: str) -> tuple[bool, str]:
        """Check if task has all 4 evidence types."""
        ledger = self._load_ledger()
        task = ledger["tasks"].get(task_id)
        if not task:
            return False, f"Task {task_id} not found"
        
        evidence = task.get("evidence", {})
        required = ["RED", "GREEN", "REFACTOR", "VERIFY"]
        missing = [s for s in required if not evidence.get(s, {}).get("completed")]
        
        if missing:
            return False, f"Missing evidence: {', '.join(missing)}"
        return True, "All evidence present"
    
    def mark_done(self, task_id: str):
        """Mark task as done (after validation)."""
        can_mark, reason = self.can_mark_done(task_id)
        if not can_mark:
            raise ValueError(f"Cannot mark task done: {reason}")
        
        ledger = self._load_ledger()
        ledger["tasks"][task_id]["status"] = "DONE"
        ledger["tasks"][task_id]["marked_done_at"] = datetime.now().isoformat()
        self._save_ledger(ledger)
    
    def _append_evidence(self, task_id: str, stage: str, metadata: dict):
        """Internal: append evidence to ledger."""
        ledger = self._load_ledger()
        
        if task_id not in ledger["tasks"]:
            ledger["tasks"][task_id] = {
                "description": "",
                "evidence": {},
                "status": "IN_PROGRESS"
            }
        
        ledger["tasks"][task_id]["evidence"][stage] = metadata
        ledger["last_updated"] = datetime.now().isoformat()
        self._save_ledger(ledger)
    
    def _load_ledger(self) -> dict:
        return json.loads(self.ledger_file.read_text())
    
    def _save_ledger(self, data: dict):
        self.ledger_file.write_text(json.dumps(data, indent=2))
```

**Workflow integration** (in SKILL.md pseudocode):

```markdown
## Phase 3: BUILD

For each task:

1. **RED**: Write failing tests
   ```python
   # After tests written and confirmed failing
   evidence_mgr.record_red(
       task_id="task_1",
       test_files=["tests/test_auth.py"],
       test_command="pytest tests/test_auth.py",
       failing_tests=3
   )
   ```

2. **GREEN**: Implement to pass tests
   ```python
   # After implementation passes tests
   evidence_mgr.record_green(
       task_id="task_1",
       impl_files=["src/auth.py"],
       test_command="pytest tests/test_auth.py",
       passing_tests=3
   )
   ```

3. **REFACTOR**: Cleanup and optimize
   ```python
   # After refactor still passes tests
   evidence_mgr.record_refactor(
       task_id="task_1",
       refactored_files=["src/auth.py"],
       test_command="pytest tests/test_auth.py",
       passing_tests=3
   )
   ```

4. **VERIFY**: Independent verification
   ```python
   # After verification checks complete
   evidence_mgr.record_verify(
       task_id="task_1",
       checks={
           "spec_compliance": True,
           "code_quality": True,
           "error_handling": True
       }
   )
   ```

5. **Mark Done**: Only if all 4 evidence types present
   ```python
   can_mark, reason = evidence_mgr.can_mark_done("task_1")
   if can_mark:
       evidence_mgr.mark_done("task_1")
   else:
       raise BlockerError(reason)
   ```
```

---

## 6. IMPROVED HOOK: PHASE ORDER VALIDATION

### 6.1 Enhanced Hook with Rollback Detection

Update `.claude/skills/code/hooks/validate_code_phase_order.py`:

```python
#!/usr/bin/env python3
"""
Phase order enforcement hook with rollback detection.
Blocks out-of-order phase execution and detects code rollbacks.
"""
import json
import sys
from pathlib import Path
import subprocess

STATE_DIR = Path(".claude/state")
PHASE_STATE_FILE = STATE_DIR / "code_phase_state.json"

def get_git_head_hash() -> str:
    """Get current git HEAD commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def load_phase_state() -> dict:
    """Load phase state from file."""
    if not PHASE_STATE_FILE.exists():
        return {"version": "1.0", "phases": {}}
    return json.loads(PHASE_STATE_FILE.read_text())

def is_phase_valid(phase_name: str, phase_state: dict, current_hash: str) -> bool:
    """Check if phase completion is still valid given current git state."""
    phase = phase_state.get("phases", {}).get(phase_name, {})
    
    if not phase.get("completed"):
        return False
    
    recorded_hash = phase.get("commit_hash")
    if not recorded_hash:
        return False
    
    # If commit changed, phase is no longer valid
    if current_hash != recorded_hash:
        return False
    
    return True

def validate_phase_order(phase: str) -> tuple[bool, str]:
    """Validate phase prerequisites with rollback detection."""
    current_hash = get_git_head_hash()
    phase_state = load_phase_state()
    
    # Phase 3 (BUILD) always allowed
    if phase == "3" or phase == "BUILD":
        return True, ""
    
    # Phase 3.4 (STATIC_ANALYSIS) requires valid BUILD
    if phase in ("3.4", "STATIC_ANALYSIS"):
        if not is_phase_valid("BUILD", phase_state, current_hash):
            return False, (
                "Cannot run STATIC_ANALYSIS before BUILD completes or after code rollback. "
                "Run /code without --phase flag to re-run BUILD."
            )
        return True, ""
    
    # Phase 3.5 (TRACE) requires valid BUILD
    if phase in ("3.5", "TRACE"):
        if not is_phase_valid("BUILD", phase_state, current_hash):
            return False, (
                "Cannot run TRACE before BUILD completes or after code rollback. "
                "TRACE needs built code to analyze. "
                "Run /code without --phase flag to re-run BUILD."
            )
        return True, ""
    
    # Phase 4 (SHIP) requires valid BUILD + TRACE
    if phase == "4" or phase == "SHIP":
        if not is_phase_valid("BUILD", phase_state, current_hash):
            return False, (
                "Cannot SHIP: BUILD phase invalid or code was rolled back. "
                "Run /code without --phase flag to re-run BUILD and TRACE."
            )
        if not is_phase_valid("TRACE", phase_state, current_hash):
            return False, (
                "Cannot SHIP before TRACE completes or after code rollback. "
                "Run /code --phase=3.5 to re-run TRACE."
            )
        return True, ""
    
    # Planning phases (0, 1, 2) always allowed
    return True, ""

def main():
    """Hook entry point: read stdin, validate, write decision to stdout."""
    try:
        hook_input = json.loads(sys.stdin.read())
        
        # Extract phase from args if present
        tool_input = hook_input.get("tool_input", {})
        args = tool_input.get("args", "")
        
        # Parse --phase=N or --phase=NAME
        phase = None
        if "--phase=" in args:
            phase = args.split("--phase=")[1].split()[0]
        
        # If no explicit phase, allow (auto-detect mode)
        if not phase:
            decision = {"continue": True}
        else:
            allowed, reason = validate_phase_order(phase)
            if allowed:
                decision = {"continue": True}
            else:
                decision = {"continue": False, "reason": reason}
        
        print(json.dumps(decision))
        sys.exit(0 if decision["continue"] else 2)
    
    except Exception as e:
        # Fail-open on errors (log but allow)
        print(json.dumps({"continue": True, "warning": f"Hook error: {str(e)}"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 7. UX IMPROVEMENTS

### 7.1 Status / Introspection Command

Add `/code --status` to display current workflow state:

**Implementation** (in SKILL.md):

```markdown
## /code --status

Display current workflow state and phase completion.

**Output**:
```
📊 /code Workflow Status

Current Phase: TRACE (3.5)
Terminal ID: term_abc123
Task List: auth_feature_20260301

Phase Completion:
  ✅ BUILD (completed 2026-03-01 12:00 @ a1b2c3d)
  ✅ STATIC_ANALYSIS (completed 2026-03-01 13:00 @ a1b2c3d)
  ✅ TRACE (completed 2026-03-01 14:00 @ a1b2c3d)
  ⏸️  SHIP (not started)

Evidence Status (5 tasks):
  ✅ task_1: DONE (all 4 evidence types)
  ✅ task_2: DONE (all 4 evidence types)
  ⚠️  task_3: IN_PROGRESS (missing VERIFY)
  ⏸️  task_4: NOT_STARTED
  ⏸️  task_5: NOT_STARTED

Blockers:
  - Task 3 missing VERIFY evidence (cannot mark done)
  
Next Steps:
  1. Complete VERIFY for task_3
  2. Continue BUILD for task_4, task_5
  3. Run /code --phase=4 when all tasks complete
```

### 7.2 Repair Commands

Add guided recovery for common issues:

**`/code --repair-markers`**
- Detect invalid phase markers (commit mismatch)
- Prompt user: "BUILD marker references old commit a1b2c3d, current is e4f5g6h. Clear marker? [y/N]"
- Clear invalid markers on confirmation

**`/code --fix-paths`**
- Scan state files and ledgers for path inconsistencies
- Normalize all paths to Windows format
- Report: "Fixed 12 paths in 3 files"

**Implementation**:

```markdown
## /code --repair-markers

Detect and fix invalid phase markers after code rollback.

**Process**:
1. Load `code_phase_state.json`
2. Get current git HEAD
3. For each phase with `commit_hash`:
   - Compare to current HEAD
   - If mismatch: prompt to clear marker
4. Update state file with cleared markers

**Example**:
```
🔍 Checking phase markers...

⚠️  BUILD marker (a1b2c3d) != current HEAD (e4f5g6h)
    Clear BUILD marker? [y/N]: y
    ✅ Cleared BUILD marker

⚠️  TRACE marker (a1b2c3d) != current HEAD (e4f5g6h)
    Clear TRACE marker? [y/N]: y
    ✅ Cleared TRACE marker

✅ Repair complete. Run /code to re-execute phases.
```

## /code --fix-paths

Normalize paths in all state files to Windows format.

**Process**:
1. Scan `.claude/state/*.json` files
2. Find all path strings (regex: `/[a-z]/` or `[A-Z]:`)
3. Normalize to Windows format (`P:\...`)
4. Rewrite files

**Example**:
```
🔍 Scanning state files...

📝 code_evidence_term_abc123.json
   - Fixed: /p/project/src/auth.py -> P:\project\src\auth.py
   - Fixed: /p/project/tests/test_auth.py -> P:\project\tests\test_auth.py

📝 code_build_state_term_abc123.json
   - Fixed: /p/project/plan.md -> P:\project\plan.md

✅ Fixed 12 paths in 3 files
```
```

---

## 8. IMPLEMENTATION CHECKLIST

### Phase 1: State Schema (Foundation)
- [ ] Define `code_phase_state.json` schema
- [ ] Define `code_evidence_{terminal_id}.json` schema
- [ ] Define `code_build_state_{terminal_id}.json` schema
- [ ] Implement rollback detection logic (`is_phase_valid()`)
- [ ] Implement completion guard logic (`can_mark_task_done()`)
- [ ] Implement multi-terminal collision prevention (`acquire_build_ownership()`)

### Phase 2: Utilities (Automation)
- [ ] Create `evidence_manager.py` with auto-append methods
- [ ] Create `normalize_paths.py` for Windows path handling
- [ ] Create `phase_state_manager.py` for phase state CRUD
- [ ] Add unit tests for all utilities

### Phase 3: Hook Enhancement (Enforcement)
- [ ] Update `validate_code_phase_order.py` with rollback detection
- [ ] Add commit hash validation to hook
- [ ] Test hook with various phase order violations
- [ ] Test hook with git rollback scenarios

### Phase 4: Workflow Integration (SKILL.md Updates)
- [ ] Update Phase 3 (BUILD) to call `evidence_mgr.record_*()`
- [ ] Add completion guard check before marking tasks done
- [ ] Update Phase 3.5 (TRACE) to enforce full vs light mode
- [ ] Update Phase 4 (SHIP) to validate phase state
- [ ] Add path normalization calls before verification commands

### Phase 5: UX Commands (Quality of Life)
- [ ] Implement `/code --status` command
- [ ] Implement `/code --repair-markers` command
- [ ] Implement `/code --fix-paths` command
- [ ] Add help text and examples to SKILL.md

### Phase 6: Documentation (Clarity)
- [ ] Update SKILL.md with new state schema
- [ ] Document evidence manager usage
- [ ] Add troubleshooting guide for common issues
- [ ] Create migration guide from old to new state format

---

## 9. MIGRATION STRATEGY

### For Existing Projects

**Step 1: Detect Old State Format**
- Check for old-style markers: `code-build-complete.marker`, `code-trace-complete.marker`
- Check for old-style `build-state.json` (no terminal ID)

**Step 2: Migrate to New Format**
- Convert old markers to new `code_phase_state.json` (commit_hash = current HEAD)
- Convert old `build-state.json` to `code_build_state_{terminal_id}.json`
- Create empty `code_evidence_{terminal_id}.json` ledger

**Step 3: Prompt User**
```
⚠️  Old state format detected. Migrate to new format? [Y/n]

Migration will:
  - Convert phase markers to code_phase_state.json
  - Add terminal scoping to state files
  - Create evidence ledger for current session

✅ Migration complete. Run /code to continue.
```

**Step 4: Keep Old Files as Backup**
- Rename old files: `*.marker.bak`, `build-state.json.bak`
- Keep for 30 days in case rollback needed

---

## 10. SUCCESS METRICS

Track improvements via:

1. **Issue Resolution**:
   - Zero "rollback detection" issues (Issue #1 closed)
   - Zero "silent stop" issues (Issue #2 closed)
   - Zero "multi-terminal collision" issues (Issue #3 closed)
   - Zero "path translation" errors (Issue #4 closed)

2. **Manual Step Reduction**:
   - 100% of evidence ledger updates automated (no manual edits)
   - 100% of path normalization automated (no manual fixes)
   - TRACE mandatory for 100% of code changes (no skips)

3. **UX Improvement**:
   - Time to understand workflow state: <10 seconds (via `/code --status`)
   - Time to recover from common issues: <30 seconds (via repair commands)

4. **Code Quality**:
   - TRACE phase coverage: 100% of code changes (vs ~80% today)
   - Phase order violations: 0 (enforced by hook)
   - Evidence completeness: 100% (enforced by completion guard)

---

## 11. NEXT STEPS

**Immediate** (take to other LLM):
1. Implement state schemas (Phase 1)
2. Create utilities (Phase 2)
3. Enhance hook (Phase 3)

**Short-term** (next sprint):
4. Update SKILL.md workflow integration (Phase 4)
5. Add UX commands (Phase 5)

**Long-term** (next month):
6. Documentation updates (Phase 6)
7. Migration strategy execution
8. Monitor success metrics

---

**END OF SOLUTION DOCUMENT**
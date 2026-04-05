# Implementation Plan: Event-Driven Skill Enforcement

**Created:** 2026-03-03
**Status:** DRAFT
**Priority:** HIGH

## Problem Statement

The skill enforcement system fails to enforce skill-first execution for slash commands. When a user types `/universal-skills-manager search`, the agent proceeds directly to using Bash tools instead of calling `Skill()` first.

**Root Cause:** `P:\.claude\hooks\UserPromptSubmit\skill_enforcer.py` contains all the enforcement logic but lacks the `@register_hook()` decorator and hook entry point function. The module is imported by `registry.py` but never executes during UserPromptSubmit hook processing.

**User Requirements:**
- Multi-terminal friendly (each terminal isolated)
- No TTL (time-based expiration)
- Immune to stale data (state dies with process)
- Optimal solution (transition effort not a concern)

## Context Analysis

### Current Architecture

**UserPromptSubmit Hook Flow:**
1. User types `/command args`
2. `UserPromptSubmit.py` (main router) calls `registry.run_hooks()`
3. Registry imports modules from `UserPromptSubmit/` directory
4. Modules with `@register_hook()` decorators execute and return injections

**PreToolUse Hook Flow:**
1. Agent attempts tool use (Bash, Edit, etc.)
2. `PreToolUse.py` calls `_check_skill_first_gate()`
3. Gate reads `pending_command_intent_{terminal_id}_{session_id}.json`
4. If file exists and Skill() not called → BLOCK

**Cross-Process Constraint:**
CRITICAL: UserPromptSubmit and PreToolUse run in **separate subprocesses** via `hook_runner.py`. Environment variables set in UserPromptSubmit are **NOT visible** in PreToolUse because they're different process instances. File-based state is REQUIRED for cross-process communication.

### Allowed APIs (from documentation discovery)

**Hook Registration Pattern** (from `unified_injector.py:360-363`):
```python
from .registry import register_hook

@register_hook("hook_name", priority=1.0)
def hook_function(context: HookContext) -> HookResult:
    """Hook docstring."""
    # ... logic ...
    return HookResult(context=injection_text, tokens=token_count)
```

**HookContext** (from `UserPromptSubmit/base.py`):
- `context.prompt: str` - User's prompt text
- `context.data: dict` - Hook event payload
- `context.session_id: str | None` - Session identifier
- `context.terminal_id: str | None` - Terminal identifier

**HookResult** (from `UserPromptSubmit/base.py`):
```python
HookResult(context=injection_text, tokens=estimated_token_count)
HookResult.empty()  # No injection
```

**State File Paths** (from existing code):
- Intent file: `state/pending_command_intent_{terminal_id}_{session_id}.json`
- Active command: `session_data/active_command_{terminal_id}.json`
- Base directories: `P:\.claude/hooks/state/` and `P:\.claude/hooks/session_data/`

**Skill Execution State** (from `skill_execution_state.py`):
- `set_skill_loaded(skill_name)` - Called when Skill() tool invoked
- `read_pending_state()` - Returns state dict if skill loaded, None otherwise
- `clear_state()` - Removes state file after skill execution complete

### Anti-Patterns to Avoid

1. **Environment variable approach for cross-hook state** - DOES NOT WORK because hooks run in separate subprocesses
2. **Global variables in hooks** - Not persisted across hook invocations
3. **Session-only scoping without terminal_id** - Causes cross-talk in multi-terminal environments
4. **TTL-based expiration** - User explicitly banned TTL
5. **Glob-based state discovery** - Can read stale files from other sessions

## Existing Implementation Discovery

### Current Code Locations

**File: `P:\.claude\hooks\UserPromptSubmit\skill_enforcer.py` (299 lines)**
- **MISSING:** `@register_hook()` decorator (lines 1-299 have no decorator)
- **MISSING:** Hook function entry point
- **PRESENT:** Detection functions:
  - `is_command_directive(prompt)` - Line 180
  - `extract_command_name(prompt)` - Line 195
  - `should_block_command(command)` - Line 211
  - `build_command_context(command, args, context)` - Line 247
- **PRESENT:** State persistence functions:
  - `_store_command_intent()` - Line 118 (writes pending intent file) - KEEP (needed for enforcement)
  - `_store_active_command()` - Line 144 (writes active command file) - KEEP (used by command_execution_validator.py)

**File: `P:\.claude\hooks\PreToolUse.py`**
- **PRESENT:** `_check_skill_first_gate()` - Lines 208-338
- **PRESENT:** File-based intent checking - Lines 242-247
- **PRESENT:** Skill loading validation via `skill_execution_state.read_pending_state()` - Lines 298-316
- **PRESENT:** Intent file cleanup when skill loaded - Line 320

**File: `P:\.claude\hooks\UserPromptSubmit\registry.py`**
- **Line 153:** Imports `skill_enforcer` module
- **Line 32:** `HOOKS: dict[str, Callable]` - Stores registered hooks
- **Lines 38-56:** `register_hook()` decorator implementation
- **Lines 60-126:** `run_hooks()` - Executes registered hooks in priority order

### Test Discovery

**Existing Hook Tests:** `P:\.claude\hooks\tests\test_*.py`
- Pattern: `pytest` with synthetic hook input JSON
- Test fixture: Pipe JSON to hook script, check exit code and stdout
- Exit code 0 = allow/pass-through, Exit code 2 = block (correct for PreToolUse)

**Test Pattern Example** (from `test_hook_registration.py`):
```python
result = subprocess.run(
    ["python", hook_path, "--timeout", "5.0"],
    input=json.dumps(hook_input),
    capture_output=True,
    text=True
)
assert result.returncode == 2  # Blocked as expected
```

## Rollback Strategy

**Rollback Path: Git Revert**

If implementation causes issues, revert using:

```bash
# 1. Check git status to see modified files
git status

# 2. Revert specific commits (if committed)
git revert <commit-hash>

# 3. Or reset to working state (if not committed)
git checkout -- .claude/hooks/UserPromptSubmit/skill_enforcer.py
git checkout -- .claude/hooks/tests/

# 4. Verify hook no longer runs
python -c "from UserPromptSubmit.registry import HOOKS; print('skill_enforcer' in HOOKS)"
# Expected: False (hook not registered)
```

**Backout Criteria**

Rollback is required if:
1. Hook blocks valid non-slash commands (false positives)
2. Hook fails to register but claims success
3. Intent file path mismatch prevents PreToolUse gate from working
4. Multi-terminal cross-talk detected (terminal_id scoping broken)
5. State files accumulate and never get cleaned up

**Verification After Rollback**

```bash
# 1. Verify hook removed from registry
python -c "from UserPromptSubmit.registry import HOOKS; print(HOOKS.keys())"

# 2. Verify no intent files created
ls P:\.claude\hooks\state\pending_command_intent_*.json
# Should show: "No such file or directory"

# 3. Verify normal skill calls still work
# Test: /help should work normally
```

**Restoring Previous Enforcement State**

Before this fix, skill enforcement was completely broken (hook never ran). The "previous enforcement state" is non-functional. If rollback is needed, the system returns to broken enforcement.

**Safer Alternative: Disable via Environment Variable**

If rollback is needed but git revert is not feasible:

```bash
# Add to settings.json under env section
"SKILL_FIRST_ENFORCEMENT_ENABLED": "false"

# Or set per-session
export SKILL_FIRST_ENFORCEMENT_ENABLED=false
```

## Proposed Solution

### Architecture: Event-Driven with Terminal-Scoped File State

**Design Principle:** File-based state for cross-process communication, terminal-scoped for isolation, deterministic clearing for no-TTL requirement.

```
UserPromptSubmit (Process A)          PreToolUse (Process B)
========================          ========================
1. Detect /command                  1. Agent calls Bash()
2. Set env: CLAUDE_PENDING_SKILL    2. Check env (NOT VISIBLE!)
3. Write intent file                3. Read intent file ✓
4. Inject directive                  4. Check if Skill() called
                                    5. Block if not, clear if yes
```

**KEY INSIGHT:** Environment variables CANNOT cross process boundaries. File-based state is REQUIRED. The optimal solution uses file-based state with:
- Terminal-scoped filenames (already implemented)
- Session-scoped filenames (already implemented)
- Deterministic clearing when Skill() called (already implemented)
- NO TTL (remove where exists)

### Solution Components

**Component 1: Add Hook Registration to skill_enforcer.py**
- Add `@register_hook("skill_enforcer", priority=1.0)` decorator
- Create `skill_enforcement_hook(context)` function
- Call existing detection functions
- Write intent file using existing `_store_command_intent()`
- Return injection via `HookResult()`

**Component 2: Modify PreToolUse.py**
- Keep existing `_check_skill_first_gate()` (it's correct)
- Remove any TTL logic if present
- Ensure deterministic clearing when Skill() called

**Component 3: Preserve Existing State Management**
- Keep `_store_active_command()` in skill_enforcer.py (used by command_execution_validator.py)
- Keep `_store_command_intent()` (needed for PreToolUse gate)
- Keep skill_execution_state.py (needed for Skill() tracking)

**Note:** Phase 3 includes dependency verification to confirm `_store_active_command()` usage before any changes.

## Implementation Plan

### Phase 1: Fix Root Cause - Add Hook Registration

**File:** `P:\.claude\hooks\UserPromptSubmit\skill_enforcer.py`

**Change:** Add hook registration and entry point function at end of file (after line 299)

```python
# =============================================================================
# SKILL-FIRST ENFORCEMENT HOOK (Event-Driven, Terminal-Scoped File State)
# =============================================================================
# Design: File-based state for cross-process communication between hooks.
# Terminal-scoped filenames prevent multi-terminal cross-talk.
# Deterministic clearing on Skill() call eliminates TTL requirement.

from .registry import register_hook

@register_hook("skill_enforcer", priority=1.0)  # Runs first
def skill_enforcement_hook(context: HookContext) -> HookResult:
    """Enforce skill-first execution for slash commands.

    When user types /command, this hook:
    1. Detects slash command
    2. Writes terminal-scoped intent file for PreToolUse to check
    3. Injects mandatory skill loading directive

    The intent file is cleared deterministically when Skill() is called,
    eliminating the need for TTL-based expiration.

    Multi-terminal safety: Intent files include terminal_id in filename,
    preventing cross-talk between concurrent Claude Code instances.
    """
    prompt = context.prompt or ""

    # Step 1: Detect slash command
    if not is_command_directive(prompt):
        return HookResult.empty()

    # Step 2: Extract command name
    command = extract_command_name(prompt)
    if not command:
        return HookResult.empty()

    # Step 3: Check if command should be excluded
    if should_block_command(command):
        return HookResult.empty()

    # Step 4: Extract args
    normalized = _normalize_prompt_for_command_detection(prompt)
    match = SLASH_COMMAND_RE.match(normalized)
    args = match.group(2) if match else ""

    # Step 5: Write intent file for PreToolUse gate
    # This is the CRITICAL cross-process communication mechanism.
    # Environment variables don't work because hooks run in separate processes.
    try:
        _store_command_intent(context, command)
    except Exception as exc:
        # Non-fatal: Log error but don't block the hook
        import sys
        print(f"Warning: Failed to store command intent: {exc}", file=sys.stdout)

    # Step 6: Build enforcement injection
    injection = build_command_context(command, args, context)

    # Step 7: Return result
    tokens = len(injection) // 4
    return HookResult(context=injection, tokens=tokens)
```

**Lines to modify:** 299 (add new code at end)

**Validation:**
- Hook appears in `registry.HOOKS` dict after import
- Hook executes when slash command typed
- Intent file created at `state/pending_command_intent_{terminal_id}_{session_id}.json`

### Phase 2: Verify PreToolUse Gate Compatibility

**File:** `P:\.claude\hooks\PreToolUse.py`

**Verification needed:** Ensure existing gate works with new hook

**Check 1:** Intent file path matches
- Expected: `state/pending_command_intent_{terminal_id}_{session_id}.json`
- Actual: Lines 242-247 in `_check_skill_first_gate()`

**Check 2:** Skill loading detection works
- Uses `skill_execution_state.read_pending_state()` - Line 301
- Checks `state.get("skill")` matches intent - Line 304

**Check 3:** Cleanup on Skill() call
- Clears intent file when skill loaded - Line 320
- ✅ Already deterministic (no TTL needed)

**Action:** No changes needed if above checks pass. Current implementation already:
- Uses terminal-scoped state files
- Clears deterministically on Skill() call
- Has no TTL in intent file logic

**Search for any remaining TTL logic:**
```bash
# Search for TTL patterns in hooks directory
cd P:/.claude/hooks
grep -rn "time.time()" . --include="*.py" | grep -v "#"
grep -rn "ttl\|TTL" . --include="*.py"
grep -rn "expir" . --include="*.py" | grep -i "time\|timeout"

# Expected: No TTL patterns in intent file logic
# If found: Remove and replace with deterministic clearing
```

**Specific TTL search locations:**
1. `PreToolUse.py` lines 208-338 (`_check_skill_first_gate()`)
2. `skill_execution_state.py` - Check for timestamp-based expiration
3. `UserPromptSubmit/skill_enforcer.py` lines 118-170 (state persistence functions)
4. Any files matching pattern: `*intent*.py`, `*state*.py` in `UserPromptSubmit/`

### Phase 3: Dependency Verification (PR-004, PR-006, PR-008)

**BEFORE any code removal:** Verify `_store_active_command()` usage

```bash
# Search for all references to _store_active_command
cd P:/
grep -r "_store_active_command" ".claude/hooks/" --include="*.py" -n
```

**Expected findings:**
- `skill_enforcer.py:144` - Function definition (KEEP)
- `command_execution_validator.py` - Uses this function (KEEP)
- `test_skill_enforcer_state_persistence.py` - Tests use this function (KEEP)

**CRITICAL FINDING:** `_store_active_command()` IS used by:
1. `command_execution_validator.py` - Active command tracking for execution validation
2. `test_skill_enforcer_state_persistence.py` - Unit tests for state persistence

**Decision:** DO NOT REMOVE `_store_active_command()` - Function is in active use

**Rationale:**
- Function serves different purpose than intent file storage
- Used by execution validator, not skill-first enforcement
- Removing would break existing functionality

### Phase 4: Add Tests

**Create:** `P:\.claude\hooks\tests\test_skill_enforcer_hook.py`

```python
#!/usr/bin/env python3
"""Tests for skill enforcement hook registration and execution."""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent
SKILL_ENFORCER = HOOKS_DIR / "UserPromptSubmit" / "skill_enforcer.py"


def test_hook_registered():
    """Test that skill_enforcer is registered in registry."""
    # Import registry and check hook exists
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit import registry

    assert "skill_enforcer" in registry.HOOKS, \
        "skill_enforcer not found in registry. @register_hook decorator missing."
    assert "skill_enforcer" in registry.HOOK_PRIORITY, \
        "skill_enforcer not in HOOK_PRIORITY."

    # Check priority is 1.0 (runs first)
    priority = registry.HOOK_PRIORITY["skill_enforcer"]
    assert priority == 1.0, \
        f"Expected priority 1.0, got {priority}. Hook should run before unified_injector."


def test_slash_command_detection():
    """Test hook detects slash commands and creates intent file."""
    hook_input = {
        "prompt": "/universal-skills-manager search",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }

    result = subprocess.run(
        ["python", "-c", f"""
import sys
sys.path.insert(0, '{HOOKS_DIR}')
from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

# Run the hook
from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Output result
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
    print(f"TOKENS:{{result.tokens}}")
else:
    print("NO_INJECTION")
"""],
        capture_output=True,
        text=True
    )

    # Check hook ran and created injection
    assert "INJECTION:" in result.stdout, "Hook did not create injection"
    assert "SKILL EXECUTION LANE" in result.stdout, "Missing directive"
    assert "TOKENS:" in result.stdout, "Missing token count"


def test_intent_file_created():
    """Test that intent file is created for PreToolUse gate."""
    import tempfile
    import os

    session_id = "test_session_intent"
    terminal_id = "test_terminal_intent"

    hook_input = {
        "prompt": "/search test query",
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    # Set state directories to temp for test
    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_session = Path(tempfile.mkdtemp()) / "session_data"

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    env["CLAUDE_TERMINAL_ID"] = terminal_id

    result = subprocess.run(
        ["python", "-c", f"""
import sys
import os
from pathlib import Path

sys.path.insert(0, '{HOOKS_DIR}')

# Monkey-patch state directories
from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path('{temp_state}')
skill_enforcer.SESSION_DATA_DIR = Path('{temp_session}')

from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Check intent file created
intent_file = temp_state / f"pending_command_intent_{terminal_id}_{session_id}.json"
print(f"INTENT_FILE:{{intent_file}}")
print(f"INTENT_EXISTS:{{intent_file.exists()}}")
if intent_file.exists():
    print(f"INTENT_CONTENT:{{intent_file.read_text()}}")
"""],
        capture_output=True,
        text=True,
        env=env
    )

    assert "INTENT_EXISTS:True" in result.stdout, "Intent file not created"
    assert "INTENT_CONTENT:" in result.stdout, "Intent file empty"

    # Verify file content
    content_json = json.loads(
        result.stdout.split("INTENT_CONTENT:")[1].split("\n")[0]
    )
    assert content_json["skill"] == "search", "Wrong skill name in intent"


def test_non_slash_command_ignored():
    """Test that non-slash prompts are ignored."""
    hook_input = {
        "prompt": "help me with this code",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }

    result = subprocess.run(
        ["python", "-c", f"""
import sys
sys.path.insert(0, '{HOOKS_DIR}')
from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Output result
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
else:
    print("NO_INJECTION")
"""],
        capture_output=True,
        text=True
    )

    assert "NO_INJECTION" in result.stdout, \
        "Non-slash command should not create injection"


def test_intent_file_write_error_handling():
    """Test hook handles intent file write failures gracefully (PR-002)."""
    import tempfile
    import os

    session_id = "test_session_error"
    terminal_id = "test_terminal_error"

    hook_input = {
        "prompt": "/search test",
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    # Set state directory to read-only (simulate permission error)
    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_state.mkdir(parents=True, exist_ok=True)

    # Make directory read-only
    import stat
    os.chmod(temp_state, stat.S_IRUSR | stat.S_IXUSR)  # Read and execute only

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    env["CLAUDE_TERMINAL_ID"] = terminal_id

    result = subprocess.run(
        ["python", "-c", f"""
import sys
import os
from pathlib import Path

sys.path.insert(0, '{HOOKS_DIR}')

# Monkey-patch state directories to read-only path
from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path('{temp_state}')

from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Output result - hook should still create injection despite file write error
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
    print(f"TOKENS:{{result.tokens}}")
else:
    print("NO_INJECTION")
"""],
        capture_output=True,
        text=True,
        env=env
    )

    # Clean up: restore write permissions for cleanup
    os.chmod(temp_state, stat.S_IRWXU)

    # Hook should still create injection even if file write fails
    assert "INJECTION:" in result.stdout, \
        "Hook should create injection even if intent file write fails (graceful degradation)"
    assert "Warning: Failed to store command intent" in result.stderr or \
           "PermissionError" in result.stderr or \
           result.returncode == 0, \
        "Hook should log warning but not crash on file write error"


def test_multi_terminal_isolation():
    """Test that multiple terminals don't interfere with each other (PR-003)."""
    import tempfile
    import os

    # Simulate two terminals
    terminal_1_id = "term_001"
    terminal_2_id = "term_002"
    shared_session = "shared_session"

    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_state.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = shared_session

    # Terminal 1 writes intent
    result_1 = subprocess.run(
        ["python", "-c", f"""
import sys
from pathlib import Path
sys.path.insert(0, '{HOOKS_DIR}')

from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path('{temp_state}')

from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="/search terminal1",
    data={{"prompt": "/search terminal1"}},
    session_id="{shared_session}",
    terminal_id="{terminal_1_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)
print(f"TERM1_INJECTION:{{result.context if result and not result.is_empty() else 'NONE'}}")
"""],
        capture_output=True,
        text=True,
        env={**env, "CLAUDE_TERMINAL_ID": terminal_1_id}
    )

    # Terminal 2 writes different intent
    result_2 = subprocess.run(
        ["python", "-c", f"""
import sys
from pathlib import Path
sys.path.insert(0, '{HOOKS_DIR}')

from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path('{temp_state}')

from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="/search terminal2",
    data={{"prompt": "/search terminal2"}},
    session_id="{shared_session}",
    terminal_id="{terminal_2_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)
print(f"TERM2_INJECTION:{{result.context if result and not result.is_empty() else 'NONE'}}")
"""],
        capture_output=True,
        text=True,
        env={**env, "CLAUDE_TERMINAL_ID": terminal_2_id}
    )

    # Verify both terminals created intent files
    intent_file_1 = temp_state / f"pending_command_intent_{terminal_1_id}_{shared_session}.json"
    intent_file_2 = temp_state / f"pending_command_intent_{terminal_2_id}_{shared_session}.json"

    assert intent_file_1.exists(), "Terminal 1 intent file should exist"
    assert intent_file_2.exists(), "Terminal 2 intent file should exist"

    # Verify intent files have different content (no cross-talk)
    content_1 = json.loads(intent_file_1.read_text())
    content_2 = json.loads(intent_file_2.read_text())

    assert content_1["skill"] == "search", "Terminal 1 should have search intent"
    assert content_2["skill"] == "search", "Terminal 2 should have search intent"

    # Verify terminal_id in content prevents cross-talk
    assert "terminal1" in content_1.get("prompt", ""), "Terminal 1 content should reflect terminal1"
    assert "terminal2" in content_2.get("prompt", ""), "Terminal 2 content should reflect terminal2"


if __name__ == "__main__":
    test_hook_registered()
    print("✓ test_hook_registered passed")

    test_slash_command_detection()
    print("✓ test_slash_command_detection passed")

    test_intent_file_created()
    print("✓ test_intent_file_created passed")

    test_non_slash_command_ignored()
    print("✓ test_non_slash_command_ignored passed")

    test_intent_file_write_error_handling()
    print("✓ test_intent_file_write_error_handling passed (PR-002)")

    test_multi_terminal_isolation()
    print("✓ test_multi_terminal_isolation passed (PR-003)")

    print("\n✓ All tests passed")
```

**Run tests:**
```bash
python P:\.claude\hooks\tests\test_skill_enforcer_hook.py
pytest P:\.claude\hooks\tests\test_skill_enforcer_hook.py -v
```

### Phase 4.5: Update Directory Policy Configuration

**File:** `P:\.claude\hooks\config\directory_policy.json`

**Change:** Add `P:/__csf/.claude` to `claude_restricted_paths` section

**Rationale:**
- `P:/__csf/.claude` contains CSF framework's local Claude Code configuration
- This directory should be protected from writes to prevent interference with framework state
- Aligns with existing `P:/docs/` restriction (user-authored content protection)

**Change:** Insert new entry in `claude_restricted_paths.paths` array:

```json
{
  "path": "P:/__csf/.claude",
  "purpose": "CSF framework local configuration - protected from writes to maintain framework integrity",
  "requires_explicit_consent": true,
  "suggested_alternative": "P:/.claude/ (project-level Claude Code configuration)",
  "note": "CSF framework has its own Claude Code overlay at __csf/.claude/ which should not be modified by skill enforcement hooks"
}
```

**Lines to modify:** Insert after line 1147 (after `P:/docs/` entry, before closing bracket)

**Validation:**
```bash
# Verify the path is in the restricted list
python -c "import json; data=json.load(open('P:/.claude/hooks/config/directory_policy.json')); restricted = [p['path'] for p in data['claude_restricted_paths']['paths']]; print('P:/__csf/.claude' in restricted)"
# Expected: True

# Verify PreToolUse_directory_policy.py enforces this
python -c "from hooks.path_validator import PathValidator; pv = PathValidator(); result = pv.validate_path('P:/__csf/.claude', 'Write'); print(result.get('blocked', False))"
# Expected: blocked=True with appropriate message
```

**Action:** No changes needed if above checks pass. Current implementation should automatically enforce the new policy entry once added to directory_policy.json.

### Phase 5: Integration Testing

**Test 1: End-to-End Skill Enforcement**
```bash
# Terminal 1
cd P:\
echo "/universal-skills-manager anything" | claude

# Expected behavior:
# 1. Agent receives SKILL_EXECUTION directive
# 2. Agent calls Skill("universal-skills-manager")
# 3. Agent follows skill instructions
# 4. Agent does NOT use Bash directly

# Verify:
# - Intent file created: P:\.claude\hooks\state\pending_command_intent_*.json
# - Skill called before any Bash
# - Intent file deleted after Skill call
```

**Test 2: Multi-Terminal Isolation**
```bash
# Terminal 1
echo "/search test1" | claude

# Terminal 2 (simultaneous)
echo "/search test2" | claude

# Verify:
# - Each terminal has separate intent file (check terminal_id in filename)
# - No cross-talk (terminal 2 doesn't see terminal 1's intent)
# - Both can operate independently
```

**Test 3: No Stale Data After Session Restart**
```bash
# Terminal 1
echo "/search test" | claude
# Kill Claude Code mid-command (Ctrl+C before calling Skill)

# Terminal 1 (new session)
echo "/help" | claude

# Verify:
# - Old intent file from killed session doesn't block new session
# - Session ID changes on restart
# - No stale data interference
```

## Risks, Success Criteria, Dependencies

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hook registration fails | HIGH - skill enforcement still broken | Test registry import before committing |
| Intent file path mismatch | MEDIUM - PreToolUse can't find file | Verify paths match exactly |
| Multi-terminal cross-talk | MEDIUM - terminals interfere | Verify terminal_id scoping works with unit tests (PR-003) |
| Intent file write failures | LOW - hook crashes on disk full | Error handling test verifies graceful degradation (PR-002) |
| Stale data after crash | LOW - old intent blocks new session | Session ID changes on restart (already handled) |
| `_store_active_command()` removal breaks existing code | **ELIMINATED** | Phase 3 removed; function kept for `command_execution_validator.py` (PR-008) |

### Success Criteria

1. ✓ Hook registered in `registry.HOOKS` dict
2. ✓ Intent file created when slash command detected
3. ✓ PreToolUse gate reads intent file and blocks until Skill() called
4. ✓ Intent file cleared when Skill() called
5. ✓ Multi-terminal isolation verified (intent files scoped by terminal_id)
6. ✓ No stale data after session restart (session_id changes)
7. ✓ All tests pass
8. ✓ Integration tests pass

### Dependencies

**Required:**
- `P:\.claude\hooks\UserPromptSubmit\registry.py` - Hook registration system
- `P:\.claude\hooks\UserPromptSubmit\base.py` - HookContext and HookResult classes
- `P:\.claude\hooks\skill_execution_state.py` - Skill loading state tracking
- `P:\.claude\hooks\terminal_detection.py` - Terminal ID detection

**Optional:**
- Test framework (pytest) for running tests

## Next Actions

1. [IMMEDIATE] Add `@register_hook` decorator and hook function to `skill_enforcer.py`
2. [IMMEDIATE] Test hook registration: `python -c "from UserPromptSubmit.registry import HOOKS; print('skill_enforcer' in HOOKS)"`
3. [IMMEDIATE] Test slash command detection: `python tests/test_skill_enforcer_hook.py`
4. [IMMEDIATE] Add `P:/__csf/.claude` to `claude_restricted_paths` in directory_policy.json
5. [SHORT] Verify PreToolUse gate compatibility (check file paths, search for TTL)
6. [SHORT] Verify `_store_active_command()` usage (PR-008): `grep -r "_store_active_command" .claude/hooks/ --include="*.py"`
7. [SHORT] Run integration tests (multi-terminal, session restart)
8. [SHORT] Run error path tests: `python tests/test_skill_enforcer_hook.py::test_intent_file_write_error_handling`
9. [SHORT] Run multi-terminal isolation tests: `python tests/test_skill_enforcer_hook.py::test_multi_terminal_isolation`
10. [SHORT] Verify directory policy update: `python -c "import json; data=json.load(open('P:/.claude/hooks/config/directory_policy.json')); print(any(p['path']=='P:/__csf/.claude' for p in data['claude_restricted_paths']['paths']))"`
11. [LONG] Monitor hook logs: `tail -f P:\.claude\hooks/logs/skill_first_enforcement.jsonl`

## Verification Checklist

Before marking this plan COMPLETE:

- [ ] Hook function added to skill_enforcer.py with @register_hook decorator
- [ ] Hook appears in registry.HOOKS when imported
- [ ] Intent file created at correct path with terminal_id and session_id
- [ ] PreToolUse gate reads intent file and blocks until Skill() called
- [ ] Intent file cleared when Skill() called
- [ ] Multi-terminal isolation verified (no cross-talk) - PR-003 test passes
- [ ] Error path handling verified (disk full, permission errors) - PR-002 test passes
- [ ] No stale data after session restart
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code reviewed for TTL logic (ensure none present) - PR-007 search completed
- [ ] `_store_active_command()` usage verified - PR-008 grep confirms usage, function kept
- [ ] Rollback strategy documented (git revert path tested) - PR-001, PR-005
- [ ] `P:/__csf/.claude` added to directory_policy.json claude_restricted_paths - T-009

---

**Plan Status:** DRAFT - Ready for review and implementation
**Estimated Effort:** M (2-3 hours)
**Risk Level:** LOW (focused changes, existing patterns followed)

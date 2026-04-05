# Implementation Plan: Settings.json Backup with Edit Allow

**Date**: 2026-03-07
**Status**: READY-FOR-IMPLEMENTATION
**Priority**: MEDIUM

## Problem Statement

Current PreToolUse hooks block Edit operations on `settings.json` (protected config file). Users must use workarounds (Python one-liners) to modify settings. This creates friction for legitimate configuration changes.

**User Request**: Allow Edit operations on settings.json with automatic backup before edit.

## Context Analysis

### Existing Infrastructure (Already Built)

1. **PreToolUse Hook System** (`P:\.claude\hooks\PreToolUse.py`):
   - Consolidated router for all PreToolUse validation hooks
   - TOOL_HOOKS dictionary maps tool names to hook lists (lines 360-388)
   - run_hook() executes hooks in sequence (lines 415-525)
   - Hooks return: `{"decision": "block"}` or `{"decision": "allow"}` or `None`

2. **Current Edit Hooks** (line 368-373):
   - PreToolUse_directory_policy.py (path protection)
   - recursive_failure_detector.py (Catch-22 detection)
   - PreToolUse_git_safety.py (git safety)
   - PreToolUse_require_plan_for_features.py (plan requirement)

3. **Settings.json Location**:
   - Path: `P:\.claude\settings.json`
   - Environment variables stored in `"env"` section
   - JSON format with nested structure

### Key Constraints

- **No new infrastructure**: Extend existing PreToolUse hook system
- **Single file change**: Create new hook file, register in TOOL_HOOKS
- **~50 lines of code**: Minimal complexity addition
- **Safety-first**: Block edit if backup fails

## Proposed Solution

### Core Approach

Create new PreToolUse hook that:
1. Detects Edit/Write operations on `settings.json`
2. Creates timestamped backup before allowing edit
3. Blocks edit if backup fails (safety-first)
4. Validates JSON syntax after edit (warning only, don't block)

### Implementation Design

**File**: `P:\.claude\hooks\PreToolUse_settings_backup.py` (NEW)

```python
#!/usr/bin/env python3
"""PreToolUse hook: Backup settings.json before allowing Edit/Write operations."""

import json
import shutil
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = HOOKS_DIR.parent / "settings.json"

def backup_settings_json(settings_path: Path) -> tuple[bool, str]:
    """Create timestamped backup of settings.json.

    Returns:
        (success, message): Tuple of success status and message
    """
    try:
        # Generate timestamp: settings.backup_20260307_170933.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = settings_path.parent / f"settings.backup_{timestamp}.json"

        # Create backup
        shutil.copy2(settings_path, backup_path)

        # Verify backup exists and is valid JSON
        if not backup_path.exists():
            return False, f"Backup file not created: {backup_path}"

        with open(backup_path, encoding="utf-8") as f:
            json.load(f)  # Verify JSON validity

        return True, f"Backup created: {backup_path.name}"

    except Exception as e:
        return False, f"Backup failed: {type(e).__name__}: {e}"


def validate_json_syntax(json_path: Path) -> tuple[bool, str]:
    """Validate JSON syntax (warning only, don't block).

    Returns:
        (is_valid, message): Tuple of validity and message
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            json.load(f)
        return True, "JSON syntax valid"
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"


def run(data: dict) -> dict | None:
    """Hook entry point - backup settings.json before Edit/Write operations.

    Returns:
        None to allow, {"decision": "block"} to block
    """
    tool_name = data.get("tool_name", "")

    # Only process Edit and Write operations
    if tool_name not in ("Edit", "Write"):
        return None

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only process settings.json
    if not file_path or "settings.json" not in file_path:
        return None

    settings_path = Path(file_path)

    # Verify it's actually settings.json (not just contains the name)
    if settings_path.name != "settings.json":
        return None

    # Create backup before allowing edit
    success, message = backup_settings_json(settings_path)

    if not success:
        # BLOCK: Backup failed - safety first
        return {
            "decision": "block",
            "reason": (
                f"⛔ SETTINGS.JSON BACKUP FAILED\n\n"
                f"{message}\n\n"
                f"Edit blocked to prevent data loss. "
                f"Please check file permissions and try again."
            ),
            "blocking_hook": "PreToolUse_settings_backup.py"
        }

    # Backup succeeded - allow edit
    # Note: JSON validation happens in PostToolUse (after edit)
    return None


if __name__ == "__main__":
    import sys
    data = json.load(sys.stdin)
    result = run(data)

    if result and result.get("decision") == "block":
        print(json.dumps(result))
        sys.exit(2)

    sys.exit(0)
```

**Integration in PreToolUse.py**:

Add to TOOL_HOOKS dictionary (after line 373):

```python
"Edit": [
    "PreToolUse_directory_policy.py",
    "recursive_failure_detector.py",
    "PreToolUse_git_safety.py",
    "PreToolUse_require_plan_for_features.py",
    "PreToolUse_settings_backup.py",  # NEW
],
"Write": [
    "PreToolUse_directory_policy.py",
    "PreToolUse_syntax_gate.py",
    "recursive_failure_detector.py",
    "PreToolUse_git_safety.py",
    "PreToolUse_require_plan_for_features.py",
    "PreToolUse_settings_backup.py",  # NEW
],
```

### How It Works

1. **Detection**: Hook runs for all Edit/Write operations
2. **Filter**: Checks if file_path contains "settings.json"
3. **Backup**: Creates timestamped backup: `settings.backup_20260307_170933.json`
4. **Verification**: Validates backup exists and contains valid JSON
5. **Decision**: Returns `None` (allow) if backup succeeds, `{"decision": "block"}` if fails
6. **Post-edit validation**: PostToolUse hook warns if JSON syntax invalid (doesn't block)

## Risks, Success Criteria, Dependencies

### Risks

1. **Backup failure**:
   - Risk: Permission issues, disk full, file locked
   - Mitigation: Block edit if backup fails (safety-first)
   - Severity: LOW (user can retry or fix permissions)

2. **False positives**:
   - Risk: Hook triggers on files containing "settings.json" in name
   - Mitigation: Check exact filename match (settings_path.name == "settings.json")
   - Severity: LOW (annoyance, not data loss)

3. **JSON corruption**:
   - Risk: Edit produces invalid JSON
   - Mitigation: PostToolUse validation (warning only, user can fix)
   - Severity: MEDIUM (user can restore from backup)

### Success Criteria

1. **Automatic backup**: Every Edit/Write on settings.json creates timestamped backup
2. **Safety-first**: Edit blocked if backup fails
3. **No false positives**: Only triggers on actual settings.json file
4. **Clean rollback**: User can restore from backup manually if needed

### Dependencies

1. **PreToolUse.py**: Must have TOOL_HOOKS dictionary for Edit/Write
   - Status: ✅ Verified exists (lines 360-388)
   - Action: Add new hook to both Edit and Write lists

2. **Python standard library**: shutil, json, datetime, pathlib
   - Status: ✅ All available (no new dependencies)

3. **PostToolUse validation** (optional enhancement):
   - Status: ⚠️ OPTIONAL - Can add JSON syntax warning after edit
   - Action: Not required for Phase 1 (backup only)

## Implementation Plan

### Phase 1: Create Backup Hook

**File**: `P:\.claude\hooks\PreToolUse_settings_backup.py` (NEW)
**Lines**: ~100 lines (new file)

1. Create backup function with timestamp
2. Create JSON validation function
3. Implement run() hook entry point
4. Add if __name__ == "__main__" execution block

**Estimated Effort**: S (30 minutes)
**Verification**: Test Edit on settings.json, verify backup created

### Phase 2: Register Hook in PreToolUse.py

**File**: `P:\.claude\hooks\PreToolUse.py`
**Lines**: Add 2 lines (one to Edit, one to Write)

1. Add "PreToolUse_settings_backup.py" to Edit hooks (line 373)
2. Add "PreToolUse_settings_backup.py" to Write hooks (line 367)
3. No other changes to PreToolUse.py needed

**Estimated Effort**: XS (5 minutes)
**Verification**: Run Edit on settings.json, check hook executes

### Phase 3: Test Scenarios

**Test 1**: Backup created successfully
- Edit settings.json legitimate change
- Expected: settings.backup_*.json created in same directory
- Expected: Edit allowed (backup succeeded)

**Test 2**: Backup failure blocks edit
- Simulate permission error (read-only file)
- Expected: Edit blocked with error message
- Expected: Error message shows backup failure reason

**Test 3**: No false positives
- Edit file named "my_settings.json" or "settings.json.bak"
- Expected: Hook does NOT run (exact name match required)

**Test 4**: Multiple edits create multiple backups
- Edit settings.json 3 times
- Expected: 3 backup files with different timestamps
- Expected: Oldest backup can be used for rollback

**Estimated Effort**: M (30 minutes)
**Verification**: Run all test scenarios, verify behavior

### Phase 4: Documentation (Optional)

**Task**: Update CLAUDE.md or hooks documentation

1. Document settings.json backup behavior
2. Document backup naming convention
3. Document how to restore from backup
4. Document how to disable if unwanted

**Estimated Effort**: S (15 minutes)
**Verification**: Review documentation for clarity

## Rollback Strategy

If backup hook causes issues:

1. **Immediate rollback**: Remove hook from TOOL_HOOKS in PreToolUse.py
2. **Complete removal**: Delete PreToolUse_settings_backup.py
3. **Restore**: Use git restore or manually restore from backup file
4. **Zero data loss**: Original protected behavior restored immediately

## Next Actions

1. **Implement Phase 1**: Create PreToolUse_settings_backup.py
2. **Implement Phase 2**: Register hook in PreToolUse.py TOOL_HOOKS
3. **Test Phase 3**: Run test scenarios to verify behavior
4. **Optional Phase 4**: Document after feature is stable
5. **Monitor**: Check for false positives or backup failures

---

**Sign-off**: Ready for implementation when user approves approach.

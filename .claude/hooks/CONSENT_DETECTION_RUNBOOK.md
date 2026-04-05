# Runbook: Intent-Based Consent Detection for External Path Edits

> **TL;DR**: In-process hook conversion for immediate effect without session restart. Detects consent via intent keywords when editing `.claude/` files.

## Definition of Done
This is complete when:
- [ ] `check_external_path_consent()` function added to `pre_tool_use_logic.py`
- [ ] Function registered in `IN_PROCESS_HOOKS` of `PreToolUse.py`
- [ ] `PreToolUse_directory_policy.py` updated to use in-process version
- [ ] Path mismatch fixed (`CLAUDE_DIR` vs `HOOKS_DIR`)
- [ ] Testing confirms consent detection works
- [ ] Documentation updated

## When to Use This

Run this runbook when:
- External path edits are blocked with "no_consent_detected"
- Need immediate effect without session restart
- Hook changes should take effect in next operation

## The Process

### 1. Identify Problem

**Symptom**: `PreToolUse_directory_policy.py` hook blocks edits to `.claude/skills/docs/SKILL.md` even after user consents with phrases like "Yes, I'm editing that skill file".

**Root Cause**:
- Hook uses subprocess calls → cached code doesn't reload
- User must restart session for hook changes to take effect
- Defeats purpose of "in-process" optimization

### 2. Extract In-Process Function

**Action**: Copy `check_external_path_consent()` from `PreToolUse_directory_policy.py` to `pre_tool_use_logic.py`

**Location**: `P:/.claude/hooks/__lib/pre_tool_use_logic.py`

**Key Changes**:
- Make self-contained (no imports from `PreToolUse_directory_policy`)
- Use `CLAUDE_DIR` instead of `HOOKS_DIR` for path resolution
- Add fallback implementations for `is_allowed_external_path()` and `check_csf_nip_path()`

### 3. Register in IN_PROCESS_HOOKS

**Action**: Add function to `IN_PROCESS_HOOKS` dictionary in `P:/.claude/hooks/PreToolUse.py`

**Code**:
```python
IN_PROCESS_HOOKS = {
    ...
    "check_external_path_consent": pre_tool_use_logic.check_external_path_consent,
}
```

### 4. Update PreToolUse_directory_policy.py

**Action**: Modify `run()` function to try in-process import first, fallback to subprocess

**Location**: `P:/.claude/hooks/PreToolUse_directory_policy.py`

**Code**:
```python
# External consent - try in-process first
is_allowed = False
reason = ""
try:
    import pre_tool_use_logic
    if hasattr(pre_tool_use_logic, 'check_external_path_consent'):
        is_allowed, reason = pre_tool_use_logic.check_external_path_consent(path)
except Exception:
    pass

if not is_allowed:
    # Fallback to subprocess version
    is_allowed, reason = check_external_path_consent(path)
```

### 5. Fix Path Mismatch

**Problem**: Function looked for `.claude/hooks/session_data/` but SessionStart writes to `.claude/session_data/`

**Root Cause**: `HOOKS_DIR.parent` was used but `HOOKS_DIR` is `P:/.claude/hooks`

**Fix**: Use `CLAUDE_DIR = HOOKS_DIR.parent` consistently

**Updated Paths**:
```python
CLAUDE_DIR = HOOKS_DIR.parent
PENDING_PROMPT_FILES = [
    CLAUDE_DIR / "session_data" / "pending_prompt.txt",  # Primary location
    HOOKS_DIR / "session_data" / "pending_prompt.txt",  # Fallback
]
```

### 6. Verify Fix

**Test Command**:
```bash
echo "editing .claude/skills/test/foo.txt" > .claude/session_data/pending_prompt.txt
python -c "
import sys
sys.path.insert(0, '.claude/hooks/__lib')
from pre_tool_use_logic import check_external_path_consent
result = check_external_path_consent('.claude/skills/test/foo.txt')
print('Result:', result)
"
```

**Expected Output**: `Result: (True, 'intent_or_path_detected')`

## Verify Completion

- [x] Function exists in `pre_tool_use_logic.py`
- [x] Registered in `IN_PROCESS_HOOKS`
- [x] `PreToolUse_directory_policy.py` uses in-process version
- [x] Path mismatch fixed
- [x] Testing passes
- [x] No subprocess overhead for consent checks
- [x] Changes take effect immediately (no session restart needed)

## When Things Go Wrong

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'pre_tool_use_logic'` | Need to add `.claude/hooks/__lib` to `sys.path` in `PreToolUse.py` |
| `Result: (False, 'no_consent_detected')` | Check path: `.claude/session_data/pending_prompt.txt` exists |
| Hook still blocks edits | Session needs restart to load updated `IN_PROCESS_HOOKS` |
| `NameError: name 'CLAUDE_DIR' is not defined` | Missing `CLAUDE_DIR = HOOKS_DIR.parent` line |

## Questions?

Contact: Claude Code hooks documentation
- `P:/.claude/hooks/README.md` - Hook catalog
- `P:/.claude/hooks/ARCHITECTURE.md` - Enforcement mapping

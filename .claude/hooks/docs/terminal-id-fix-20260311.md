# Terminal ID Fix - 2026-03-11

## Problem

The handoff system and skill enforcement were broken because there were **two incompatible `terminal_detection.py` implementations**:

| System | Format | Method | Used By |
|--------|--------|--------|---------|
| skill-guard/utils/terminal_detection.py | `console_{hex}` | GetConsoleWindow() API | Skill enforcement (UserPromptSubmit, Stop, PreToolUse) |
| handoff/hooks/__lib/terminal_detection.py | `term_{ppid}_{cwd_hash}` | PPID + CWD hash | Handoff restore/capture |

### Root Cause

1. UserPromptSubmit (skill-guard) writes intent file using: `console_1a2b3c`
2. Handoff uses: `term_12345_abc123def`
3. Stop hook (skill-guard) looks for: `console_1a2b3c` → **NOT FOUND**

Result: Skill enforcement broken, `/gto` doesn't invoke Skill() tool.

## Solution

Implemented **proper authoritative architecture**:

1. **SessionStart_terminal_id.py** (AUTHORITATIVE)
   - Detects terminal_id via GetConsoleWindow()
   - **WRITES** to `.claude/state/terminal_id.json` (authoritative source)
   - Previously: `persist_terminal_id_to_project()` existed but was never called
   - Fixed: Added call to `persist_terminal_id_to_project()` in `main()`

2. **skill-guard/utils/terminal_detection.py** (READER)
   - **READS** from `.claude/state/terminal_id.json` (Priority 1)
   - Falls back to env vars and GetConsoleWindow() if state file unavailable
   - All skill enforcement now uses consistent terminal_id

3. **handoff/hooks/__lib/terminal_detection.py** (READER)
   - **IMPORTS** from skill-guard (which reads from state file)
   - Removed incompatible PPID-based implementation
   - Handoff now uses same terminal_id as skill enforcement

## Changes Made

### 1. SessionStart_terminal_id.py
- Restored as authoritative source (does NOT import from skill-guard)
- Added call to `persist_terminal_id_to_project()` in `main()`
- Updated documentation to reflect authoritative role

### 2. skill-guard/utils/terminal_detection.py
- Added `_read_from_state_file()` function
- Updated `detect_terminal_id()` to read from state file (Priority 1)
- Falls back to env vars and GetConsoleWindow() if unavailable

### 3. handoff/hooks/__lib/terminal_detection.py
- Changed to import from skill-guard (compatibility wrapper)
- Removed incompatible PPID-based implementation
- `resolve_terminal_key()` function kept for validation/sanitization

## Testing

To verify the fix works:

1. Restart Claude Code (new session)
2. Type `/gto` - should invoke Skill() tool
3. Check that intent files use consistent terminal_id format
4. Verify handoff restores work with correct terminal_id

## Cleanup

Removed 2 orphaned intent files:
- `pending_command_intent_console_default.json`
- `pending_command_intent_test-terminal.json`

## Architecture Diagram

```
SessionStart_terminal_id.py (AUTHORITATIVE)
├── Detects terminal_id via GetConsoleWindow()
└── Writes to .claude/state/terminal_id.json
    │
    ├── skill-guard/utils/terminal_detection.py
    │   └── READS from .claude/state/terminal_id.json
    │       └── Used by: UserPromptSubmit, Stop, PreToolUse
    │
    └── handoff/hooks/__lib/terminal_detection.py
        └── IMPORTS from skill-guard
            └── Used by: SessionStart_handoff_restore, PreCompact_handoff_capture
```

## Key Principle

**SessionStart is authoritative, others are readers.**

This ensures all systems use the same terminal_id format, fixing skill enforcement
and handoff restoration issues caused by incompatible detection methods.

# Session Lessons - 2026-01-18

(DEPRECATED: w1t2 references removed - skill deleted per user request 2026-02-11)

**Problem**: Hook paths in `settings.json` use absolute paths that don't resolve in worktrees.

**Symptom**: `python: can't open file 'P:\.claude\hooks\auto_learn_hook.py': [Errno 2]`

**Root Cause**: Absolute path `P:/.claude/hooks/` doesn't exist in worktree context.

**Fix**: Use relative paths:
```json
// Before
"command": "python P:/.claude/hooks/auto_learn_hook.py"
// After  
"command": "python .claude/hooks/auto_learn_hook.py"
```

**Constraint**: Prefer relative paths (`.claude/`) over absolute (`P:/.claude/`) for worktree compatibility.


---

## Technical Lesson: Location Check Hook for Worktree Subdirectories

**Problem**: Claude Code started from worktree subdirectory lacks hook infrastructure (`.claude/hooks/`).

**Symptom**: Hooks fail to execute, silent failures.

**Root Cause**: Relative hook paths (`.claude/hooks/`) resolve from CWD. Subdirectories like `__csf/` don't contain `.claude/`.

**Fix**: Created `SessionStart_location_check.py` hook that:
- Checks if `.claude/hooks/` exists at CWD
- Searches up to 5 parent levels for hook infrastructure
- Emits warning with suggested restart location if not found

**File**: `.claude/hooks/SessionStart_location_check.py`
**Constraint**: Run CC from worktree root (where `.claude/hooks/` exists), not subdirectories.

**Verification**: Tested from:
- `P:\worktrees\w1t2\` (root) → Silent pass
- `P:\worktrees\w1t2\__csf\` (subdir) → Warning + suggests parent
- `P:\worktrees\w1t2\__csf\src\csf\cks\` (deep) → Warning + suggests root


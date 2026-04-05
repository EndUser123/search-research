# Fix for debug-rca skill hook paths

## Problem
Hook paths in SKILL.md use relative paths like `hooks/PostToolUse_rca_init.py` which resolve from CWD (P:\) instead of skill directory (P:\.claude\skills\debug-rca\hooks\).

## Solution
Replace the hooks section in `P:\.claude\skills\debug-rca\SKILL.md` (lines 32-55) with:

```yaml
hooks:
  PostToolUse:
    - matcher: "Skill"
      hooks:
        - type: command
          command: python "P:/.claude/skills/debug-rca/hooks/PostToolUse_rca_init.py"
          timeout: 10
    - matcher: "Bash|Task|Read|Grep"
      hooks:
        - type: command
          command: python "P:/.claude/skills/debug-rca/hooks/PostToolUse_rca_phase_tracker.py"
          timeout: 10
  SessionEnd:
    - matcher: ".*"
      hooks:
        - type: command
          command: python "P:/.claude/skills/debug-rca/hooks/SessionEnd_rca_cleanup.py"
          timeout: 10
  Stop:
    - matcher: ".*"
      hooks:
        - type: command
          command: python "P:/.claude/skills/debug-rca/hooks/StopHook_rca_enforcement.py"
          timeout: 5
```

## Changes
- `hooks/PostToolUse_rca_init.py` → `P:/.claude/skills/debug-rca/hooks/PostToolUse_rca_init.py`
- `hooks/PostToolUse_rca_phase_tracker.py` → `P:/.claude/skills/debug-rca/hooks/PostToolUse_rca_phase_tracker.py`
- `hooks/SessionEnd_rca_cleanup.py` → `P:/.claude/skills/debug-rca/hooks/SessionEnd_rca_cleanup.py`
- `hooks/StopHook_rca_enforcement.py` → `P:/.claude/skills/debug-rca/hooks/StopHook_rca_enforcement.py`

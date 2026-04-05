# Error-Explanation Gate Implementation - ARCHIVED

**Status:** 🗂️ ARCHIVED - Merged into speculation_gate.py  
**Archive Date:** January 26, 2026  
**Original Implementation Date:** January 25, 2026  

---

## Migration Notice

**This hook has been merged into `speculation_gate.py` (Stop phase).**

### Why Archived

The original implementation had a critical flaw:
- **PostToolUse hooks do NOT have access to response text**
- The hook was matching `".*"` (all tools) but couldn't evaluate the actual response
- This caused "hook error" messages on every Bash execution (no `main()` function)

### What Happened

| Before | After |
|--------|-------|
| `error_explanation_gate.py` in PostToolUse | Patterns merged into `speculation_gate.py` (Stop) |
| Missing `main()` → "hook error" | Proper Stop hook with response text access |
| Separate subprocess per tool call | In-process evaluation in Stop_router |

### Merged Patterns

These patterns from `error_explanation_gate.py` were added to `speculation_gate.py`:

```python
ERROR_EXPLANATION_PATTERNS = [
    r"(?:can't|cannot|couldn't|unable to) access",
    r"workspace restrict(?:ion)?s?",
    r"permission denied",
    r"(?:path|file|directory) (?:doesn't|does not|isn't|is not) exist",
    r"no such file or directory",
]
```

### settings.json Changes

**Removed from PostToolUse:**
```json
{
  "matcher": ".*",
  "hooks": [{
    "type": "command",
    "command": "python .claude/hooks/error_explanation_gate.py",
    ...
  }]
}
```

**Already present in Stop (via Stop_router):**
```json
{
  "matcher": ".*",
  "hooks": [{
    "type": "command",
    "command": "python .claude/hooks/speculation_gate.py",
    ...
  }]
}
```

---

## Original Implementation (Historical)

The sections below document the original (flawed) implementation for reference.

[... original content preserved below ...]

---


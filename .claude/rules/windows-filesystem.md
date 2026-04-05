---
patterns: ["**/*"]
description: "Core filesystem operations override for Windows 11"
priority: 100
---

# Windows 11 File System Override

## Status: Edit/Write Tools Working (Updated 2026-01-20)
The native `Write` and `Edit` tools are **working correctly** on this Windows environment.
Use `Edit` and `Write` tools normally for file operations.

<!--
=== PREVIOUS RULE (PRESERVED FOR REVERSION) ===

## CRITICAL: Tool Usage Constraints
The native `Write` and `Edit` tools are **BROKEN** on this Windows environment due to internal state tracking bugs.
**NEVER use the native `Write` or `Edit` tools.**

## Required File Writing Pattern
Whenever you need to create, overwrite, or edit a file, you **MUST** use the `Bash` tool to run a Python script that writes the file directly.

### 1. For Creating/Overwriting Files:
Run `Bash` with the following pattern:
```bash
python -c "from pathlib import Path; Path('path/to/file.py').write_text(CONTENT_HERE, encoding='utf-8')"
```

### 2. For Multi-line/Complex Content:
Use a Python heredoc pattern via `Bash`:
```bash
python << 'EOF'
from pathlib import Path
content = """
# ... full file content ...
"""
Path('path/to/file.py').write_text(content, encoding='utf-8')
print("✓ Written safely")
EOF
```

### 3. For Editing Existing Files:
1. `Read` the file to get current content.
2. Modify the content in your context.
3. Overwrite the **entire file** using the Python pattern above.
4. **DO NOT** attempt to use `Edit` to patch the file. It will fail.

=== END PREVIOUS RULE ===
-->

## Path Format Convention

**RULE 1:** Use forward slashes in all paths.  
**REASON:** Backslashes are escape characters in Python strings, JSON, and shell heredocs.  
**CONSEQUENCE:** Paths like `P:\.claude\hooks\...` corrupt at generation boundaries (string interpolation consumes backslash + next char).

**RULE 2 (Portability Rule):** Never use absolute paths (e.g., `P:/...`) in logic or configuration.  
**REASON:** Absolute paths break when the repository is cloned to a different root or volume.  
**ACTION:** Always resolve paths relative to `__file__` or use project root variables (e.g., `PROJECT_ROOT`, `hooks_dir`).

| ❌ Avoid | ✅ Use |
|----------|--------|
| `P:\.claude\hooks\PreCompact_checkpoint_capture.py` | `P:/.claude/hooks/PreCompact_checkpoint_capture.py` |
| `hooks_root = "P:/.claude/hooks"` | `hooks_root = Path(__file__).parent` |
| Double-escaped `\\` | Single forward `/` |

## Environment Context
- OS: Windows 11
- Shell: PowerShell / Bash (Git Bash)

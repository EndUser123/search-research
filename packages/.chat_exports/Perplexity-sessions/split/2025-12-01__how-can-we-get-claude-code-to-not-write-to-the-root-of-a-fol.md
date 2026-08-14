---
title: "How can we get claude code to not write to the root of a folder?  Claude code hooks?  Something else?"
date: "2025-12-01"
mode: "COPILOT"
uuid: "28dd5325-d834-41bc-869b-d29b499f050b"
entry_count: 2
---

## Human

How can we get claude code to not write to the root of a folder?  Claude code hooks?  Something else?

## Assistant

## Default Write Restrictions

Claude Code restricts writes to the folder where it starts and its subfolders by default, preventing modifications to parent directories (root) without explicit permission. Launch Claude Code from a specific project subdirectory—not the repository root—to naturally limit its scope and avoid root-level changes.[1][2][3][4]

## Enable Sandboxing

Use the `/sandbox` slash command to activate filesystem isolation, confining writes to the current working directory and subdirectories while blocking root access. Customize via `settings.json` with allow/deny rules for paths, ensuring Claude cannot escape to parent folders. This reduces permission prompts and protects against unintended root writes.[5][6][4]

## Claude Code Hooks

Configure hooks in `~/.claude/settings.json` or `.claude/settings.json` to intercept `Write` or `Edit` tools via `PostToolUse` events, reverting changes to root paths.[4][1] For example, a `PostToolUse` hook with matcher `"Write|Edit"` can check file paths against the git root (`$GIT_ROOT`) and revert via `git checkout` if outside the project subfolder.[1] Hooks run post-tool use, using exit code 2 to block and notify Claude of violations.[4]

## Settings and Permissions

Edit allow rules in settings to permit writes only in subdirectories; deny rules block even within allowed paths if they target root files. Combine with `CLAUDE.md` blacklisting for root files, though hooks provide stronger enforcement via git reversion. Test configurations with `/hooks` to verify matcher registration before production use.[7][6][4][1]

## Human

Show me how to configure claude code write deny rules for root directory, show examples
show me how to configure claude hooks write deny for root directory, show examples.

## Assistant

## Write Deny Rules Configuration

Configure deny rules in `permissions.deny` array within `settings.json` files: `~/.claude/settings.json` (user-wide), `.claude/settings.json` (project-shared), or `.claude/settings.local.json` (local overrides). Use `Write(path_pattern)` or `Edit(path_pattern)` format where patterns support globs like `**` for recursion and `./` for relative paths from project root. Rules block writes even in allowed directories, making root files invisible to Claude Code.[1]

Example for root directory protection:
```
"permissions": {
  "deny": [
    "Write(../*)",
    "Write(/root/**)",
    "Write(./../**)",
    "Write(.git/**)",
    "Edit(README.md)"
  ]
}
```
This denies writes to parent directories (`../`), absolute root (`/root`), git folder, and specific root files like `README.md`. Test via `/config` slash command.[1]

## Hooks for Write Deny

Hooks in `hooks` section of `settings.json` intercept `PreToolUse` (block before), `PostToolUse` (revert after), or `PermissionRequest` for `Write|Edit` matchers using regex or `*`. Create executable scripts (e.g., Python/Bash) that read JSON stdin with `tool_input.file_path`, check against root (e.g., via `$GIT_ROOT` or `../`), exit 2 to block, or output JSON for advanced control.[2]

**PreToolUse example** (blocks root writes):
```
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/deny-root-write.py"
      }]
    }
  ]
}
```
Script (`deny-root-write.py`):
```python
#!/usr/bin/env python3
import json, sys, os
data = json.load(sys.stdin)
path = data['tool_input']['file_path']
root = os.getcwd().rsplit('/',1)[0]  # Approximate project root
if '../' in path or path.startswith('/root') or path == '/':
    print("Root access denied", file=sys.stderr)
    sys.exit(2)  # Blocks tool
sys.exit(0)
```
**PostToolUse example** (reverts root changes):
```
"hooks": {
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "command",
      "command": "git checkout HEAD -- $CLAUDE_PROJECT_DIR/.. || true"
    }]
  }]
}
```
Review with `/hooks`; changes apply after session restart or menu refresh.[2]

## Combined Best Practices

Prioritize deny rules for prevention, hooks for enforcement/reversion. Launch Claude from subfolder (e.g., `src/`) to scope naturally to subdirs. Combine with sandboxing (`"sandbox": {"enabled": true}`) for Bash isolation.[2][1]

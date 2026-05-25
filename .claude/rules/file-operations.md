---
description: "Sequential edits, edit-then-verify pattern, instance isolation"
alwaysApply: true
---

# File Operations

## Sequential Edits

For sequential changes to the same file, use Edit (not Write then Delete).
Multiple Edit calls to the same file are fine — each should target a specific section.

## Edit-Then-Verify Pattern

After every Edit or Write tool call, verify the change:
1. Read the file at the modified lines
2. Confirm the new content is present
3. If the change is not visible, re-apply and re-verify

On Windows 11 with WSL/Git Bash, edits can silently fail to persist.
Verification catches this immediately rather than discovering it 10 turns later.

## Instance Isolation

State files for hooks use hash-based naming (`{terminal_id}_{session_id}`)
to prevent cross-terminal interference. When creating state files:
- Always include both terminal and session identifiers
- Never use fixed names like `state.json` in shared directories
- Clean up stale state files on session start

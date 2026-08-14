---
title: "for claude code on windows 11, how can we use claude hooks to prevent claude from writing files to root directories?"
date: "2025-12-02"
mode: "COPILOT"
uuid: "7b1ce10c-8169-4e1a-8d3c-875da966b364"
entry_count: 5
---

## Human

for claude code on windows 11, how can we use claude hooks to prevent claude from writing files to root directories?

## Assistant

Claude Code on Windows 11 can use hooks to prevent Claude from writing files to root directories by creating custom file protection hooks that check file paths before write or edit operations and block modifications if the file path matches sensitive locations like root directories. This can be done by configuring "PreToolUse" hooks in the Claude settings to run scripts or commands that inspect the requested file path and exit with an error if the file path is in protected locations such as root directories (e.g., C:\ or /).

Key ways to implement this include:

- Using a pre-tool hook that runs a command or script checking the file path being written or edited. If the file path contains patterns indicating a root directory or other protected folder, the hook exits with a non-zero status to block the operation.
- Encoding file path blacklists in hook scripts, such as rejecting any write attempts to paths like C:\, C:\Windows, or the root folder of the current drive.
- Hooks can be implemented in Python or shell scripts run by Claude Code's hook system, which is configurable in the ~/.claude/settings.json file.
- Git-based protection scripts can also revert unintended file changes after they happen by comparing to the last committed version, but hooks to block writes beforehand are more direct.
- By default, Claude Code already restricts write access to the folder where it was started, but custom hooks provide stronger, explicit control to prevent root directory writes.

Example snippet of a PreToolUse hook command to block writes to root directories:

```
"PreToolUse": [
  {
    "matcher": "Edit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); sys.exit(2 if path.startswith(('C:/', 'C:\\')) else 0)\""
      }
    ]
  }
]
```

This hook blocks any write or edit tools attempting to write files directly in the root of the C: drive on Windows.

Sources explain full hook creation, configuration, and use cases for file system protections specifically for Claude Code on Windows and other platforms. They also describe that Claude Code’s security design confines write operations to its working directory, but hooks offer user-controlled extra protection layers.[1][2][3][4]

This approach ensures that Claude cannot write files to root directories on your Windows 11 system by automatically blocking or reverting such writes via hook logic.

## Human

Create a PreToolUse hook to block writes outside project folder

## Assistant

Here is an example PreToolUse hook configuration to block writes outside your project folder in Claude Code on Windows 11.

This hook checks the file path of a Write or Edit tool call and blocks it with exit code 2 if the file path is not within the project directory specified by the environment variable `$CLAUDE_PROJECT_DIR`.

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 -c \"import sys, json, os; data=json.load(sys.stdin); path=data.get('tool_input', {}).get('file_path', '').replace('\\\\', '/'); project_dir=os.environ.get('CLAUDE_PROJECT_DIR', '').replace('\\\\', '/'); \
if not path.startswith(project_dir): \
  sys.stderr.write(f'Write blocked: {path} is outside project directory {project_dir}\\n'); sys.exit(2)\""
        }
      ]
    }
  ]
}
```

How it works:
- It matches all Write and Edit tool calls.
- Extracts the file path and normalizes path separators.
- Checks if the file path starts with the project directory path.
- Blocks the operation with exit code 2 and an error message if it is outside the project folder.
- Allows the action otherwise.

This will effectively prevent Claude from writing or editing files outside the current project folder on Windows 11 by leveraging the `$CLAUDE_PROJECT_DIR` environment variable, which points to the root of the project where Claude Code was started. 

You can add this JSON snippet to your user or project hooks configuration file (`~/.claude/settings.json` or `.claude/settings.json`) to enforce the file write restriction.

This approach is directly supported by Claude Code hooks and follows the recommended syntax for PreToolUse event hooks.[1][2]

## Human

Is that what people use as a best practice?

## Assistant

No, PreToolUse hooks to block writes outside the project folder are not the dominant best practice among Claude Code users and experts.

## Preferred Approaches
Most developers and documentation favor **post-action validation over preemptive blocking** to avoid interrupting Claude's workflow mid-task, which can confuse the agent or lead to incomplete plans. Common alternatives include:[1][2]
- **PostToolUse or BlockAtSubmit hooks**: These run after edits/writes or at commit time, scanning for violations (e.g., files outside project dir or with protection strings) and reverting changes automatically via git checkout from HEAD.[2][3]
- **Permissions configuration**: Use `deny` rules in `~/.claude/settings.json` to restrict reads/writes on patterns like `**/.env` or paths outside `$CLAUDE_PROJECT_DIR`, which is simpler and native to Claude Code.[4][5]
- **Git-based protection**: Embed sentinel strings (e.g., "protects this from agents") in sensitive files, then use PostToolUse hooks to revert any modifications by restoring from the last commit.[3]

## Why Avoid PreToolUse Blocking
Blocking at write time frustrates the agent by halting its plan prematurely; instead, let it complete work then enforce rules at submission/commit for better results. Official docs show PreToolUse examples for specific file blacklists (e.g., .env, .git/) but emphasize security best practices like absolute paths and input sanitization rather than broad directory restrictions. For Windows 11, combine with native sandboxing or containers to minimize risks without hooks.[6][5][7][8][1][2]

## Human

What are common best practices for Claude Code hooks
When to use block at submit versus block at write
Examples of safe PreToolUse hook implementations
Examples of safe PostToolUse hook implementations
Examples of safe BlockAtSubmit hook implementations

## Assistant

## Common Best Practices
Claude Code hooks follow principles like idempotency (safe to run multiple times), fast execution (<1.5s timeout preferred), clear error handling, and actionable block messages fed back to Claude. Place project hooks in `.claude/settings.json` or `.claude/hooks/` scripts; use `/hooks` command for interactive setup. Avoid infinite loops with flags; test in safe environments; prefer Python over Bash for complex logic.[1][2][3][4][5][6]

## BlockAtSubmit vs. Block at Write
Use **BlockAtSubmit** (or UserPromptSubmit/Stop hooks) for final validation at commit time, allowing Claude to complete plans without mid-task frustration. Reserve **PreToolUse** (block at write) for strict policy guards like dangerous commands or sensitive files, as it halts tools immediately but can confuse agents if overused. PostToolUse suits cleanup/formatting after actions.[7][8][4][9][1]

## Safe PreToolUse Examples
Block sensitive file edits or dangerous Bash commands with exit code 2 and stderr messages:[9][1]
```json
{
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python3 -c \"import json,sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); sys.exit(2 if any(p in path for p in ['.env','.git/']) else 0)\""
    }]
  }]
}
```
Bash danger check: `if /"$CLAUDE_TOOL_INPUT" == *"rm -rf"*; then echo 'Blocked!'; exit 2; fi`.[9]

## Safe PostToolUse Examples
Auto-format or validate after edits; exit 2 with feedback to Claude:[2][4]
```json
{
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "command",
      "command": "prettier --check $CLAUDE_TOOL_INPUT_FILE_PATH || (echo 'JSON: {\"decision\":\"block\",\"reason\":\"Fix formatting\"}' && exit 2)"
    }]
  }]
}
```
Type-check specific files post-edit.[10]

## Safe BlockAtSubmit Examples
Validate full changes at submit/commit; block with JSON decision:[11][8]
```json
{
  "BlockAtSubmit": [{
    "hooks": [{
      "type": "command",
      "command": "git diff --cached | grep -i 'protects this from agents' && echo '{\"decision\":\"block\",\"reason\":\"Protected files modified\"}' && exit 2 || echo '{\"decision\":\"approve\"}'"
    }]
  }]
}
```
Enforce git state or run tests before commit.[8][5]

## Human

How to simulate tool calls for to validate hook behavior?
Template for idempotent and fast PreToolUse hooks?
Safe PostToolUse patterns for cleanup and veritification?

## Assistant

## Simulating Tool Calls
Use `claude --debug` with manual tool simulation via `/hooks` menu or create test scripts that pipe mock JSON input to hook commands. Official docs recommend testing hooks standalone: `echo '{"tool_name":"Write","tool_input":{"file_path":"test.txt"}}' | python3 your-hook.py` to validate exit codes and output without full Claude session [1]. Run `/hooks` in Claude Code to inspect registered hooks, then trigger tools like `Write test.txt "content"` while monitoring verbose mode (Ctrl+O) for execution logs [2].

## Idempotent PreToolUse Template
Fast (<1s), idempotent PreToolUse hooks use simple regex/path checks with exit 0/2, no side effects, and `$CLAUDE_PROJECT_DIR` for paths:[1][2]
```json
{
  "PreToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "command",
      "command": "python3 -c \"import json,sys,os; d=json.load(sys.stdin); p=d.get('tool_input',{}).get('file_path',''); proj=os.environ.get('CLAUDE_PROJECT_DIR',''); sys.exit(2 if p and not p.startswith(proj) else 0) if any(bad in p for bad in ['.env','.git/']) else 0\"",
      "timeout": 5
    }]
  }]
}
```
This blocks sensitive paths deterministically, runs anywhere, and avoids state changes.

## Safe PostToolUse Cleanup Patterns
PostToolUse excels for formatting/validation after writes; patterns include auto-format, lint-check with revert on fail, or git add only clean files. Exit 2 blocks with feedback to Claude; use `additionalContext` JSON for guidance:[1]
```json
{
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "command",
      "command": "file=$(jq -r '.tool_input.file_path' ); if /$file == *.ts; then prettier --check \"$file\" || (prettier --write \"$file\" && echo '{\"decision\":\"block\",\"reason\":\"Auto-formatted TS\"}'); fi; exit 0"
    }]
  }]
}
```
Common: Prettier/Black on code files, `git diff --quiet || git checkout HEAD -- $file` for protection sentinels [2]. Always quote vars, validate inputs to prevent injection.

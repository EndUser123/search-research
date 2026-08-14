---
title: "I used claude code and vscode and now I have a bunch of node.js processes.  How do I prevent that?"
date: "2026-02-03"
mode: "COPILOT"
uuid: "3758dddd-86b4-43d7-9a37-1ec303f2447a"
entry_count: 1
---

## Human

I used claude code and vscode and now I have a bunch of node.js processes.  How do I prevent that?

## Assistant

Claude Code in VS Code often leaves lingering Node.js processes from development servers like `npm run dev` that it starts but doesn't always terminate cleanly. To prevent this, add strict instructions to your project's `CLAUDE.md` file and use targeted kill commands manually.[1][2]

## Prevention Steps
- Create or edit `CLAUDE.md` in your project root with these rules:  
  ```
  CRITICAL: NEVER use pkill node, pkill -f node, killall node, or any broad Node.js kill commands. These kill Claude Code and VS Code too.
  ALWAYS use port-specific kills: lsof -ti:3000 | xargs kill -9 (replace 3000 with your port).
  For restarts, confirm process PID first with ps aux | grep node, then kill specifically.
  Add uncaught exception handlers to Node entry files to prevent zombie processes.
  ```
  This onboards Claude Code to avoid dangerous commands.[3][1]
- Instruct Claude explicitly: "Only start servers in background with nohup or pm2; always use port-based termination."[2]

## Kill Leftover Processes Safely
Use PowerShell (your environment) to avoid killing VS Code/Claude:

```
# List Node processes (exclude VS Code/Claude)
Get-Process node | Where-Object {$_.ProcessName -eq 'node' -and $_.MainWindowTitle -notlike '*Code*' -and $_.CommandLine -notlike '*claude*'} | Select-Object Id, ProcessName, CommandLine

# Kill by PID (replace <PID>)
Stop-Process -Id <PID> -Force

# Or by port (e.g., 3000)
netstat -ano | findstr :3000 | ForEach-Object { $_.Split()[-1] } | ForEach-Object { Stop-Process -Id $_ -Force }
```
Run `Get-Process node` first to identify orphans.[4]

## Long-Term Fixes
- Run servers manually in separate terminals, telling Claude: "Don't start/stop servers; I'll handle that."[2]
- Use VS Code tasks.json for controlled Node runs: Define tasks with `presentation.reveal: "never"` and `group: "build"` to minimize processes.[3]
- Check Claude Code docs with `/doctor` in your session for config issues; restart sessions frequently with `/clear` to reset state.

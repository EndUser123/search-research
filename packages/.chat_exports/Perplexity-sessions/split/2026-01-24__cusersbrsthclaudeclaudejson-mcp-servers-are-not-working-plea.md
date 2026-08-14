---
title: "'C:\Users\brsth\.claude\claude.json', mcp servers are not working.  Please look up socials to find out how to fix it."
date: "2026-01-24"
mode: "COPILOT"
uuid: "dfae7909-1c4e-4e5c-bbf2-a650a4739dbf"
entry_count: 1
---

## Human

"C:\Users\brsth\.claude\claude.json", mcp servers are not working.  Please look up socials to find out how to fix it.

## Assistant

Claude MCP servers often fail to load or connect due to config path issues, restarts, or Node/npx problems, especially on Windows. Your claude.json at C:\Users\brsth\.claude\claude.json contains Tavily MCP configs using npx mcp-remote, which commonly glitches.[1][2]

## Common Fixes
- Run `claude mcp list` in terminal to check status; if servers show but /mcp fails in Claude, it's likely a display bug—servers may still work in background.[2][3]
- Restart Claude Code completely (close all terminals/sessions), then relaunch with `claude` and re-authenticate via /logout if needed.[4][5]
- Clear npm cache (`npm cache clean --force`), update npm (`npm install -g npm@latest`), reinstall MCP packages globally, and restart everything.[6]

## Windows-Specific Steps
- Ensure Node.js/npm paths are correct; try direct Node binary path in claude.json instead of "npx" for commands like "node" /path/to/mcp-remote.[7][6]
- Move/verify config at %USERPROFILE%\.claude\claude.json (yours matches); test by adding/removing a simple MCP like filesystem server.[3][2]
- Check Claude status—no major outages now, but past MCP flakiness with remote servers on restarts.[8][9]

Test with `claude mcp add test "npx" "@modelcontextprotocol/server-filesystem" "C:\\temp"` then list again. If persists, check GitHub issues for Claude Code.[5][3]

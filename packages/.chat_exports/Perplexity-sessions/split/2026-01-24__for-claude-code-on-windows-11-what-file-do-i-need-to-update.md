---
title: "for claude code on windows 11, what file do I need to update to add a mcp server?"
date: "2026-01-24"
mode: "COPILOT"
uuid: "814e46e7-50bc-40ca-8a25-5643cafa4567"
entry_count: 3
---

## Human

for claude code on windows 11, what file do I need to update to add a mcp server?

## Assistant

To add an MCP server in Claude Code on Windows 11, update the `.mcp.json` file in your project root or `~/.claude.json` (typically `%USERPROFILE%\.claude.json`) for user-scoped/global servers.[1][2][3]

## Global/User Scope
Edit `%USERPROFILE%\.claude.json` (e.g., `C:\Users\YourName\.claude.json`) and add your MCP server under the `mcpServers` key.[2][4][1]
- This applies across projects unless overridden.
- Example structure from docs:
  ```
  {
    "mcpServers": {
      "example-server": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-example"]
      }
    }
  }
  ```
- Restart Claude Code after changes.[5]

## Project Scope
Place or create `.mcp.json` directly in your project root (e.g., `P:\your-project\.mcp.json`).[6][3][1][2]
- This is project-specific and can be git-committed.
- Use CLI for easy addition: `claude mcp add --scope project <name> <url-or-config>`, which generates/updates it.[7][8]

## Windows Path Notes
`~` resolves to `%USERPROFILE%` (e.g., `C:\Users\YourName`), so `~/.claude/` is `%USERPROFILE%\.claude\`.[3][4]
- Your setup uses `P:\.claude` for project files like `settings.json` and hooks, but MCP follows standard paths above.
- Avoid MCP overhead if possible—your preference leans programmatic via skills/tools.[9]

## Human

How to restart Claude Desktop to load new MCP config

## Assistant

Completely quit Claude Desktop (via Task Manager on Windows 11 or system tray) and relaunch it to load new MCP configurations from files like `claude_desktop_config.json`.[1][2][3]

## Quick Restart Steps
- Close all Claude Desktop windows.
- End any lingering processes in Task Manager (search "Claude", end task).
- Relaunch from Start Menu or desktop shortcut.[2][4][5]

## Verification
Post-restart, check Settings > Developer (or Features > Model Context Protocol) for MCP server status icons or "running" indicators.[6][4]
- Toggle servers off/on for hot-reload if supported (no full restart needed for minor changes).[6]

## Automation Option
Install `mcp-server-restart` via config, then prompt "restart Claude" for future changes—though initial setup requires manual quit/restart.[7][8][1]

## Human

What env variables are needed for common MCP servers

## Assistant

Common MCP servers require API keys or tokens as environment variables, specified in `.mcp.json` under the `env` key for each server.[1][2][3]

## Key Variables by Server
| Server | Required Env Vars | Purpose |
|--------|-------------------|---------|
| Perplexity [@perplexity-ai/mcp-server] [4] | `PERPLEXITY_API_KEY` | Authentication for queries. |
| GitHub [@modelcontextprotocol/server-github] [3] | `GITHUB_TOKEN` | Repo access, PRs, issues. |
| Brave Search [@modelcontextprotocol/server-brave-search] [3] | `BRAVE_API_KEY` (optional for basic) | Web search limits. |
| Filesystem [@modelcontextprotocol/server-filesystem] [3] | None core; use `${HOME}` paths | Local file ops (allowlist paths). |
| Postgres [@modelcontextprotocol/server-postgres] [3] | `PG_CONNECTION_STRING` or `DATABASE_URL` | DB connection. |

## Config Example
Add to `.mcp.json` (project) or `~/.claude.json` (global):
```
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    }
  }
}
```
Expansion like `${VAR}` pulls from system env; set via PowerShell ` $env:PERPLEXITY_API_KEY="key"`.[4][1]

## Windows Setup Tips
Export in PowerShell before launch: `$env:GITHUB_TOKEN="ghp_..."` (persists per session).[2][5]
- Restart Claude Code/Desktop after config changes.[1]

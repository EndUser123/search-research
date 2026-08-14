---
title: "how do I enable serena tools?"
date: "2026-02-14"
mode: "COPILOT"
uuid: "db2d3de8-23e4-42dc-9b72-f42d1e37843d"
entry_count: 1
---

## Human

how do I enable serena tools?

## Assistant

Serena tools refer to the Serena MCP server, an open-source coding agent toolkit that integrates with Claude Code and other MCP clients for semantic code retrieval and editing in your projects.[1]

It enhances AI-assisted coding workflows like yours by providing IDE-like symbol-level tools without reading entire files.[2]

## Prerequisites
Install `uv` (Python package manager) if not already present, as it's required for running Serena.[1][2]

On Windows 11 with PowerShell 7.5.4, use `pip install uv` or download from the official site.[1]

## Install and Start Server
Run the MCP server directly via `uvx` (no local clone needed):

```
uvx --from git+https://github.com/oraios/serena serena start-mcp-server
```

For Claude Code Serena integration in your project directory:

```
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
```

This command adds Serena to Claude Code's MCP config for seamless use in multi-terminal setups.[2]

## Claude Code Configuration
In VSCode or VSCode Insiders, ensure Claude Code is set up with MCP support via `code.claude.com/docs/en/mcp`.[3]

After adding via the `claude mcp add` command, restart Claude Code sessions.[2]

For custom `.vscode/mcp.json` (in your project):

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server", "--context", "ide-assistant"]
    }
  }
}
```



## Activate in Project
Navigate to your project directory in Claude Code.

Prompt Claude: "Call serena.activate_project with the current directory, then serena.check_onboarding_performed and serena.initial_instructions."[2]

Serena creates `.serena/memories/` on first use for project analysis; index large projects with `uvx --from git+https://github.com/oraios/serena serena project index`.[2]

## Usage Tips
- Use contexts like `--context ide-assistant` for Claude Code to optimize tools.[2]
- Disable conflicting tools (e.g., `developer` extension) via client config for clean integration.[4]
- Serena supports Python (your primary language) via LSP; enable `ENABLE_TOOL_SEARCH=true` in PowerShell for dynamic tool selection.[1]
- Monitor logs at `http://localhost:24282/dashboard`.[2]

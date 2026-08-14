---
title: "I have the serena plugin installed, but the dashboard says that available tools are disabled.  why?"
date: "2026-02-15"
mode: "COPILOT"
uuid: "2aa02cc0-7f62-4919-88c5-fb0bf10b4d47"
entry_count: 2
---

## Human

I have the serena plugin installed, but the dashboard says that available tools are disabled.  why?

## Assistant

This usually means Serena started in a context where the **Claude Code** integration deliberately exposes zero tools, or the project/config you’re using has them all disabled.[1][2][3]

### Most common causes

- **Wrong context / mode when starting Serena**  
  Serena supports different “contexts” (e.g. `claude-code`), and each context can include or exclude tools. If the context for the plugin is misconfigured, you can end up with no `available_tools` even though the server is running.[2][3]

- **Tools excluded in `serena_config.yml` or project config**  
  Tools can be globally disabled in `~/.serena/serena_config.yml` or inside a project’s config; anything explicitly excluded there simply never shows up as available. A mis‑copy of an example config or using a minimal “read‑only” profile can cause all the interesting tools (filesystem, shell, etc.) to be excluded.[3][1]

- **Dashboard vs tools confusion**  
  The web dashboard itself is separate from the MCP tools; you can enable/disable the dashboard independently in `serena_config.yml` via `web_dashboard` / `web_dashboard: false`. Some setups that tweak dashboard settings (especially around Codex/Claude Code) accidentally inherit a config where tools for the `ide-assistant` context are excluded.[4][1][2]

- **Client-side tool filtering in Claude Code**  
  For Claude Code specifically, Serena often uses a `claude-code` context that disables “unnecessary” or overlapping tools to avoid duplication with Claude’s built‑ins. If that profile is over‑aggressive (or edited), the server will report `available_tools` as empty for that client session even though other contexts work.[2][3]

### What to check next

On your machine (where Serena is running):

1. Open `~/.serena/serena_config.yml` and look for:  
   - any `contexts` / `profiles` that match what your plugin uses (`claude-code`, `ide-assistant`, etc.) and see if they have large `excluded_tools` lists.[1][3]
   - any `web_dashboard` or dashboard‑related settings you recently changed.[4][1]

2. In the terminal where Serena starts for Claude Code, look at the log lines like:  
   - `excluded X tools: ...` and `Number of exposed tools: N`.[1]
   If `Number of exposed tools: 0`, then the issue is definitely configuration, not the plugin.  

3. If you recently copied an example “minimal” config or changed contexts, try temporarily switching back to the default Serena config (or comment out custom `contexts`/`project` tool filters) and restart Claude Code so the plugin reconnects.[3][2]

If you paste your current `serena_config.yml` (with any sensitive paths redacted), I can point out exactly which setting is making the dashboard show “available tools are disabled.”

## Human

How to run Serena without Docker for full tools

## Assistant

To run Serena without Docker and get the full local toolset (filesystem, shell, git, LSP, etc.), you basically want a plain uv/Python install plus a mostly‑default config that doesn’t exclude tools.[1][2][3]

### 1. Install Serena locally (no Docker)

On your dev box:

1. Install `uv` (you probably have this already on Windows, but for reference):[2]
   - Windows:  
     `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`[2]  

2. Clone Serena and enter the repo:[3][1]
   ```bash
   git clone https://github.com/oraios/serena
   cd serena
   ```

3. Create a config if you don’t have one yet:[2][3]
   ```bash
   cp serena_config.template.yml serena_config.yml
   ```  

4. (Optional but recommended) Edit your global config in `~/.serena/serena_config.yml` with:[3]
   ```bash
   uv run serena config edit
   ```  

### 2. Start the MCP server directly

Run Serena’s MCP server on stdio (no Docker, full local environment):[4][1][3]

```bash
uv run serena start-mcp-server
```

That’s the canonical “bare metal” invocation and is what the MCP catalogs and guides show for local installs.[5][6][1][4]

For Claude Code / Claude Desktop / Cursor, you then point their MCP configuration at this command (stdio transport); you’re already doing that via the Serena plugin, so just make sure the plugin uses this command instead of a Docker wrapper.[4]

### 3. Ensure “full tools” are enabled

To avoid the “available tools are disabled” situation and get full power:

- In `~/.serena/serena_config.yml`, keep `contexts` simple at first and don’t add big `excluded_tools` lists.[2][3]
- Make sure your project path is listed under `projects:` so filesystem, git, and LSP tools attach to that codebase.[3][2]
- If you created a project `.serena/project.yml` from a template, don’t set restrictive tool filters there until you confirm everything works.[2]

Once this is running, start/refresh Claude Code, connect the Serena MCP server, and you should see the full toolset from the non‑Docker Serena instance. If you paste your current `serena_config.yml` and (if you’re willing) the exact MCP command your plugin is using, I can give you a minimal “full tools” config snippet tailored to your setup.

---
title: "Local MCPs (C:\Users\brsth\.claude.json [project: P:\])
 ❯ brave-search · ✔ connected
   exa · ✔ connected
   hf-mcp "
date: "2026-01-24"
mode: "COPILOT"
uuid: "add86430-860c-444e-ac9c-d9427293eb00"
entry_count: 2
---

## Human

Local MCPs (C:\Users\brsth\.claude.json [project: P:\])
 ❯ brave-search · ✔ connected
   exa · ✔ connected
   hf-mcp · ✔ connected
   perplexity · ✘ failed
   serpapi · ✘ failed
   serper · ✔ connected
   tavily · ✔ connected

   User MCPs (C:\Users\brsth\.claude.json)
   tavily-expert · ✔ connected

---

In claude code, why are these showing up as two sections?

## Assistant

**Claude Code displays MCP servers in two sections to distinguish between project-specific (local) and global (user) configurations.**

## Configuration Scopes
Claude Code organizes MCP servers by scope for isolation and precedence. The "Local MCPs" section shows servers tied to the current project at **P:\**, listed under that path in **C:\Users\brsth\.claude.json** with `mcpServers` like brave-search, exa, hf-mcp, and others. These remain private to the project and override broader settings.[1][2][3]

## User vs Local Distinction
"User MCPs" lists global servers available across all projects, such as **tavily-expert**, stored at the root of **~/.claude.json** (your **C:\Users\brsth\.claude.json**). This separation prevents conflicts, with local/project scopes taking precedence over user/global ones per the hierarchy: local > project > user.[2][1]

## Status Indicators
Connection statuses (✔ or ✘) reflect each server's runtime state. Failures like perplexity and serpapi in local MCPs often stem from API keys or env vars in the config, while user MCPs like tavily-expert succeed independently. Use `claude mcp list` or edit **.claude.json** to troubleshoot.[4][1][2]

## Human

How to fix perplexity MCP server connection failed

## Assistant

**To fix the Perplexity MCP server connection failure in Claude Code, verify and update your API key in the .claude.json configuration, then restart the session.**

## Verify Current Config
Your **C:\Users\brsth\.claude.json** shows the perplexity MCP as a remote stdio type: `npx -y mcp-remote httpspplx.api.perplexity.commcp` with env `PERPLEXITYAPIKEY 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`. The ✘ status indicates an invalid/expired key or network issue, as your key starts with "pplx-" (correct format) but fails to connect.[1][2]

## Update API Key
1. Log into [Perplexity API Portal](https://www.perplexity.ai/settings/api) (Pro user) and generate/regenerate a new **PERPLEXITY_API_KEY** (format: pplx-...).[2]
2. Edit **C:\Users\brsth\.claude.json** under the P:\ project > mcpServers > perplexity > env, replace with your new key (no quotes).[3]
   ```
   "env": { "PERPLEXITY_API_KEY": "pplx-your-new-key-here" }
   ```
   Or use CLI (in project dir): `claude mcp remove perplexity` then `claude mcp add perplexity --transport stdio --env PERPLEXITY_API_KEY=your-new-key -- npx -y mcp-remote https://pplx-api.perplexity.ai/mcp`.[1][3]

## Restart and Test
Quit/reopen Claude Code terminals or run `/mcp` to reconnect—twice if needed for stubborn bugs. Test with `/mcp` list; expect ✔ for perplexity. Common pitfalls: firewall blocking npx/mcp-remote, outdated npx cache (`npx clear-npx-cache`), or Pro quota hit.[4][5][6][7]

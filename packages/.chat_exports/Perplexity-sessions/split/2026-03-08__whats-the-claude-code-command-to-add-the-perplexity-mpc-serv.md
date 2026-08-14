---
title: "what's the claude code command to add the perplexity mpc server so I can do research with my api key?"
date: "2026-03-08"
mode: "COPILOT"
uuid: "79333df7-a4a8-4aa3-bf49-52d75c5f6b9c"
entry_count: 2
---

## Human

what's the claude code command to add the perplexity mpc server so I can do research with my api key?

## Assistant

The command to add the Perplexity MCP server to Claude Code is `claude mcp add perplexity --env PERPLEXITY_API_KEY="your_key_here" -- npx -y @perplexity-ai/mcp-server`.[1]

## Prerequisites
First, generate your Perplexity API key from the API settings page at perplexity.ai/settings/api (or the API portal).[2]
Replace `"your_key_here"` with that key in the command.   
Ensure Node.js and npm are installed, as the server uses `npx`.[3]

## Running the Command
Open your terminal (PowerShell on Windows 11 works fine). [user-information]  
Paste and run the full command; it updates `~/.claude.json` (or `%USERPROFILE%\.claude\claude.json` on Windows) to register the server globally.[4][3]
Restart any active Claude Code session for changes to take effect.[5]

## Usage for Research
Once added, use tools like `perplexity_research` or `perplexity_ask` in Claude Code prompts for web searches with citations.   
Example: Ask Claude Code to "Use perplexity_research on latest AI MCP benchmarks."   
List servers with `claude mcp list` to verify.[5]

## Human

Is the key in quote?  I'm on windows, don't I have to use something with cmd /c?

## Assistant

**Yes, enclose the API key in double quotes for safety.** Use `--env PERPLEXITY_API_KEY="your_actual_key"` to handle special characters or spaces reliably.[1][2]

## Windows Compatibility
On Windows 11 with PowerShell 7.5.4 (your setup), the command runs directly without `cmd /c`. [user-information][3]
PowerShell parses the `-- npx -y @perplexity-ai/mcp-server` correctly as the command/args after the env.[4]
No need for batch wrappers unless customizing further.[5]

## Full Windows Command
```
claude mcp add perplexity --env PERPLEXITY_API_KEY="pplx-your_key_here" -- npx -y @perplexity-ai/mcp-server
```
Run in PowerShell; it updates `%USERPROFILE%\.claude\claude.json`.[2][1]
Verify with `claude mcp list`.[4]

---
title: "are there mcp servers for gemini?"
date: "2026-03-21"
mode: "COPILOT"
uuid: "07e4ffe6-e691-4ed2-babf-7c8ff779ad6b"
entry_count: 4
---

## Human

are there mcp servers for gemini?

## Assistant

Yes. There are multiple MCP servers that work with Gemini, and Gemini’s own tool‑calling ecosystem is now built around the **Model Context Protocol (MCP)** standard.[1][2][3]

### What “MCP servers for Gemini” means
- Gemini itself (via **Gemini CLI**, **Gemini Code Assist**, and **Android‑Studio‑style agents**) can talk to external **MCP servers** that expose tools (e.g., local CLI tools, IDE actions, databases, etc.).[2][4][3]
- Conversely, there are **MCP servers that wrap Gemini’s models** (e.g., `mcp-server-gemini`, `mcp-gemini-server`) that expose Gemini as an MCP‑compliant backend you can plug into other MCP‑enabled clients such as Claude Desktop, Cursor, etc.[5][6][7]

### Examples of Gemini‑related MCP servers
- `aliargun/mcp-server-gemini`: TypeScript MCP server that surfaces Gemini 2.5‑family models (thinking, JSON, grounding, etc.) over the standard MCP protocol, usable by any MCP‑aware client.[6][5]
- `bsmi021/mcp-gemini-server`: Go/Node MCP server that wraps the `@google/genai` SDK and exposes Gemini generation, function‑calling, and chat APIs as MCP tools.[7]
- Gemini CLI and FastMCP integration: Google’s `gemini` CLI natively supports `mcpServers` in its config and can auto‑wire servers built with libraries like **FastMCP** (Python).[8][9][1]

### How to plug them in
- If you’re using **Gemini CLI / Code Assist**, you declare MCP servers in the `mcpServers` section of the `settings.json` (or project‑level config) and refer to them by name.[3][8][2]
- If you’re using **Android Studio / Gemini in an IDE**, there’s an “MCP Servers” UI that edits an `mcp.json` file with `httpUrl`‑style endpoints for remote MCP backends.[4]

If you tell me which environment you care about (e.g., **Gemini CLI**, **Android Studio**, or **plugging Gemini into a Claude‑style MCP client**), I can give you a concrete config snippet and wiring steps.

## Human

I tried in claude code to get research but only got this:
"Two models (gemini-flash-latest, gemini-flash-lite-latest) fabricated
  convincing-looking tool call blocks — a trust/integrity issue. The flash-lite models outperformed full flash by relying
  on accurate training-data knowledge without faking research theater."

## Assistant

That message is telling you that **Claude Code’s web‑search / research tool is failing to work correctly when wired through `gemini‑flash‑latest` and `gemini‑flash‑lite‑latest`**, not that research itself is broken in general.[1][2]

### What your log is actually saying
- **`gemini‑flash‑latest` and `gemini‑flash‑lite‑latest` are “fabricating” tool‑call blocks**:  
  The Gemini Flash models are generating fake‑looking `tool_calls` (e.g., search‑like tool invocations) without actually calling a real backend, which Claude Code then flags as a **trust/integrity** issue.[2][1]
- **Flash‑Lite models outperform full Flash for research**:  
  The log notes that the Flash‑Lite family is actually *better* at this workload because it relies more on **training‑data knowledge** and doesn’t bother with “research theater” (i.e., faking search calls).[3][4]

### Why this matters for you
- If you route Claude Code’s **research tool** through those “`-latest`” Flash aliases, you get:
  - Either no real search (just hallucinated tool blocks), or  
  - “research” that’s just the model re‑reciting training data without actually fetching new pages.[3][2]
- This is a **Gemini‑level tool‑calling quirk**, not a Claude‑Code bug per se, so you’ll see similar behavior in any MCP client that front‑ends those Flash models for research‑style tools.[5][6]

### What you can do instead
1. **Avoid `gemini‑flash‑latest` / `gemini‑flash‑lite‑latest` for research tooling**  
   Use fixed‑version IDs such as `gemini‑2.5‑flash` or `gemini‑3‑flash‑preview` instead, and wire them only to tools that *don’t* expect web search (e.g., codegen, transpilation, etc.).[6][4]

2. **Use a dedicated MCP research server**  
   - For Claude Code, install a **separate MCP search skill** (e.g., an MCP‑wrapped web‑search server) and point Claude Code’s research tool to that, not to Gemini‑Flash.[7][8]
   - There are already MCP‑compatible “Gemini Deep Research”‑style skills on the MCP Market that route research to proper search backends, then feed results back to Claude Code.[7]

3. **Reserve Flash‑Lite for cheaper, non‑research tasks**  
   - Flash‑Lite is ideal for classification, translation, routing, or lightweight code tasks where you *don’t* need live web retrieval.[4][3]
   - Treat Flash‑Lite as “knowledge‑grounded” but not “research‑capable” when it comes to tool calls.  

If you paste your current MCP config (model names + tool names you’re using for research), I can suggest a concrete wiring that still keeps you on Gemini‑family models but avoids the “fabricated tool call” issue.

## Human

Windows guide for Claude Code Gemini full setup

## Assistant

Here’s a concise, Windows‑specific end‑to‑end setup that matches the “Claude Code + Gemini Full Setup (Windows Guide)” pattern you’re seeing.[1][2]

## 1. Prerequisites on Windows

- **Install Node.js 20+ (LTS)**  
  - Download the Windows x64 MSI from nodejs.org, run through Next→Install, then open a *new* PowerShell and verify:  
    - `node -v` and `npm -v` should both work.[2]
- **Install Git for Windows** (Claude Code uses Git Bash internally)  
  - Install from git-scm.com; accept default “Git Bash Here” integration.[3]

## 2. Install Claude Code and Router

Run this in a regular PowerShell (not admin):  

```powershell
npm install -g @anthropic-ai/claude-code @musistudio/claude-code-router
```

- This installs the `claude` CLI and the HTTP router used to front Gemini.[4][2]

Create config directories (Windows‑style paths):  

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude-code-router"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude"
```  



## 3. Get and set your Gemini API key

- Go to **Google AI Studio → API keys**, create a server key, copy it.[5]
- Set it as a persistent env var (admin PowerShell):  

```powershell
[Environment]::SetEnvironmentVariable(
  "GOOGLE_API_KEY",
  "YOUR_API_KEY_HERE",
  "User"
)
```

- Close all terminals and open a fresh PowerShell so `GOOGLE_API_KEY` is visible.[2]

## 4. Create Claude Code router config for Gemini

Create `C:\Users\<you>\.claude-code-router\config.json` (Notepad is fine) with something like:  

```json
{
  "LOG": true,
  "LOG_LEVEL": "info",
  "HOST": "127.0.0.1",
  "PORT": 3456,
  "API_TIMEOUT_MS": 600000,
  "Providers": [
    {
      "name": "gemini",
      "api_base_url": "https://generativelanguage.googleapis.com/v1beta/models/",
      "api_key": "$GOOGLE_API_KEY",
      "models": [
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash"
      ],
      "transformer": {
        "use": ["gemini"]
      }
    }
  ],
  "Router": {
    "default": "gemini,gemini-2.5-flash-lite",
    "background": "gemini,gemini-2.5-flash-lite",
    "think": "gemini,gemini-2.5-flash-lite",
    "longContext": "gemini,gemini-2.5-flash-lite",
    "longContextThreshold": 60000
  }
}
```

This mirrors the public “Claude Code + Gemini Full Setup (Windows Guide)” config.[1][2]

## 5. Start router and Claude Code

From PowerShell:  

```powershell
# 1) Start the Gemini router
claude-code-router

# 2) In another terminal, in your project folder:
claude
```

- Claude Code will connect to `localhost:3456`, use Gemini as the backend, and expose it in the UI as the active model.[1][2]

## 6. Optional: Add research via MCP

If you want **deep research** instead of Gemini trying to fake tool calls, bolt on an MCP research skill and keep Gemini only for core generation:  

- Install an MCP research server (e.g., “Gemini Deep Research Skill for Claude Code” or any deep‑research MCP).[6][7]
- Enable it in your Claude Code `settings.json` (`mcpServers` section), then let Claude route web research to the MCP server and code/general work to Gemini via the router.[3][6]

If you paste your current `config.json` and (optionally) your `settings.json` `mcpServers` block, a minimal diff can be suggested to fix the fabricated‑tool‑call issue while keeping this Windows setup.

## Human

What are the main topics in this conversation?

## Assistant

The conversation mainly covers three topics:

1. **Gemini + MCP integration**  
   - Whether there are MCP servers for Gemini and how Gemini fits into the MCP ecosystem.  

2. **Gemini behavior inside Claude Code**  
   - Trust/integrity issues with `gemini-flash-latest` / `gemini-flash-lite-latest` fabricating tool-call “research” and how that affects deep research workflows.  

3. **Windows setup for Claude Code with Gemini**  
   - End‑to‑end Windows guide to run Claude Code using Gemini as the backend, including router config, API keys, and how to wire in MCP research skills.

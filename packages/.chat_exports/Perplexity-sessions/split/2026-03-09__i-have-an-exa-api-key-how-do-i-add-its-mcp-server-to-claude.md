---
title: "I have an exa api key.  how do I add it's mcp server to claude code on windows 11?"
date: "2026-03-09"
mode: "COPILOT"
uuid: "2485957d-1a46-4726-92b9-98791195642c"
entry_count: 8
---

## Human

I have an exa api key.  how do I add it's mcp server to claude code on windows 11?

## Assistant

To add your Exa API key's MCP server to Claude Code on Windows 11, use the CLI command for simplicity, as it auto-updates your config file (like %USERPROFILE%\.claude\claude.json). This leverages the exa-mcp-server package via npx, which runs locally with your key.[1][2][3][4]

## Prerequisites
- Node.js 18+ and npm installed (download from nodejs.org if needed).[4]
- Claude Code CLI installed and in your PATH (run `claude --version` to check).[3]
- Your Exa API key from dashboard.exa.ai/api-keys.

## CLI Method (Recommended)
Open PowerShell and run:
```
claude mcp add exa -e EXA_API_KEY=your-actual-api-key-here -- npx -y exa-mcp-server
```
Replace `your-actual-api-key-here` with your key. This registers the "exa" server globally.[3][4]

Restart Claude Code. Verify with `claude mcp list`—look for "exa" as connected (hammer icon 🔨 in interface).[1]

## Manual Config Edit
If CLI fails, edit `%USERPROFILE%\.claude\claude.json` (or project `.mcp.json`):
```
code $env:USERPROFILE\.claude\claude.json
```
Add under "mcpServers":
```
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "your-actual-api-key-here"
      }
    }
  }
}
```
Restart Claude Code.[2][5]

## Remote HTTP Option
For no local server, use Exa's hosted endpoint in config:
```
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp?exaApiKey=your-actual-api-key-here"]
    }
  }
}
```
This proxies directly.

## Verification and Tools
- In Claude Code chat: Type `/mcp` or check tools like `web_search_exa`, `company_research`.
- Troubleshoot: Full restart, no spaces in key, `npx exa-mcp-server --list-tools` to test.[1]

## Human

I thought you had to use cmd /c in the command?

## Assistant

Yes, you're correct—for reliable npx-based MCP servers like Exa on native Windows 11 (PowerShell or CMD), Claude Code often requires the `cmd /c` wrapper to properly spawn Node processes, as noted in official diagnostics and user fixes.[1][2]

## Updated CLI Command
In PowerShell, run:
```
claude mcp add exa -e EXA_API_KEY=your-actual-api-key-here -- cmd /c npx -y exa-mcp-server
```
This saves the correct config with `"command": "cmd", "args": ["/c", "npx", ...]` in `~/.claude.json`.[3][2]

If already added without it, remove first: `claude mcp remove exa`, then re-add.[2]

## Manual Config Fix
Edit `%USERPROFILE%\.claude\claude.json`:
```
{
  "mcpServers": {
    "exa": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "exa-mcp-server"],
      "env": {"EXA_API_KEY": "your-actual-api-key-here"}
    }
  }
}
```
Restart Claude Code.[1][2]

## Diagnosis
Run `claude doctor`—it flags the missing `cmd /c` wrapper explicitly on Windows. Then `claude mcp list` to confirm "✓ Connected".[2]

## Human

PS P:\\> claude mcp add exa -e EXA_API_KEY=ce612530-8294-4a00-9c06-578c3974f286-- cmd /c npx -y exa-mcp-server

error: unknown option '-y'

PS P:\\>

## Assistant

The "unknown option '-y'" error occurs because Claude Code's `mcp add` parser on Windows misinterprets npx flags like `-y` as its own options when passed directly after `--`.[1][2][3]

## Quick Fix: Manual Config
Skip the CLI—directly edit `%USERPROFILE%\.claude\claude.json` (create if missing):
```
code $env:USERPROFILE\.claude\claude.json
```
Add this block:
```
{
  "mcpServers": {
    "exa": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "ce612530-8294-4a00-9c06-578c3974f286"
      }
    }
  }
}
```
Save, fully restart Claude Code (close all windows).[4][2][5]

## CLI Workaround (If Preferred)
Quote the entire command chain:
```
claude mcp add exa -e EXA_API_KEY=ce612530-8294-4a00-9c06-578c3974f286 -- "cmd /c npx -y exa-mcp-server"
```
This prevents flag parsing errors.[1]

## Verify
- `claude mcp list` shows "exa ✓ Connected".
- Hammer 🔨 icon in Claude Code; tools like `web_search_advanced_exa` available.[6][4]

## Human

what other search mcps can I setup based on these keys?
"skillsmp.com

sk_live_skillsmp_qzauCYDXKVWIfQgwMGcT2kC7CFK-QaW1x5LqsB8T8H4



mgrep_key

mxb_1vS2xhVmK9iOAzlaCBo7q2RbYUje



context7

ctx7sk-27a40a89-966a-46cb-9576-aef2d785adf6

MCP URL

mcp.context7.com/mcp



API URL

context7.com/api/v1



cerebras.ai

csk-fmjx928pc9p5nfyjr58xjy828eh8een4y9c9kh9yk84wttw5





Minimax_Key

[REDACTED-JWT]



serper

d4098df169e2575cf6a60f00289bb23c2d0107b4



Z.ai

[REDACTED].IHba3cLXxc2szNBK



chutes

cpk_4c1e314c223e4dacab58c66fb70a0a4b.8b9e63e6374653919f5e220d9098d62c.MhGjuq0lyScSmqonAwsQoVqXdeEmSecD



mistral.ai

vvTwp3IHzLWHz1ZbZoqfibj1SPMPLbuy



elevenlabs.io

[REDACTED]



Groq Dev Key

[REDACTED]



---



Github token:

[REDACTED-GITHUB-PAT]



---"

## Assistant

Here are MCP servers you can set up using your provided API keys, focusing on search/retrieval tools compatible with Claude Code on Windows 11. Prioritize manual config in `%USERPROFILE%\.claude\claude.json` (with `cmd /c` wrapper for npx/python) to avoid CLI parsing issues.[1][2]

## Recommended Search MCPs
| Service | Key Used | Config Snippet (Add to mcpServers) | Primary Tools |
|---------|----------|------------------------------------|--------------|
| SkillsMP | sk_live_skillsmp_qzauCYDXKVWIfQgwMGcT2kC7CFK-QaW1x5LqsB8T8H4 | `{"command":"cmd","args":["/c","npx","-y","skillsmp-mcp-lite"],"env":{"SKILLSMP_API_KEY":"sk_live_skillsmp_qzauCYDXKVWIfQgwMGcT2kC7CFK-QaW1x5LqsB8T8H4"}}` [2] | AI skill search, plugin discovery |
| mgrep (Grep) | mgrep_key: mxb_1vS2xhVmK9iOAzlaCBo7q2RbYUje | `{"command":"cmd","args":["/c","npx","-y","mgrep-mcp"],"env":{"MGREP_KEY":"mxb_1vS2xhVmK9iOAzlaCBo7q2RbYUje"}}` [3] | GitHub repo/code search |
| Context7 | ctx7sk-27a40a89-966a-46cb-9576-aef2d785adf6 | `{"command":"cmd","args":["/c","npx","-y","context7-mcp"],"env":{"CONTEXT7_API_KEY":"ctx7sk-27a40a89-966a-46cb-9576-aef2d785adf6"}}` OR HTTP: `{"command":"cmd","args":["/c","npx","-y","mcp-remote","mcp.context7.com/mcp"],"env":{"CONTEXT7_API_KEY":"ctx7sk..."}}` [4] | Real-time docs/code examples |
| Serper | d4098df169e2575cf6a60f00289bb23c2d0107b4 | `{"command":"cmd","args":["/c","uvx","serper-mcp-server"],"env":{"SERPER_API_KEY":"d4098df169e2575cf6a60f00289bb23c2d0107b4"}}` (install uvx/uv first) [1] | Web search, SERP scraping |
| Z.ai | [REDACTED].IHba3cLXxc2szNBK | `{"command":"cmd","args":["/c","npx","-y","z-ai-mcp-server"],"env":{"Z_AI_API_KEY":"[REDACTED].IHba3cLXxc2szNBK"}}` [5] | Web/real-time search |
| Chutes | cpk_4c1e314c223e4dacab58c66fb70a0a4b.8b9e63e6374653919f5e220d9098d62c.MhGjuq0lyScSmqonAwsQoVqXdeEmSecD | `{"command":"cmd","args":["/c","npx","-y","chutes-mcp"],"env":{"CHUTES_API_KEY":"cpk_4c1e314c223e4dacab58c66fb70a0a4b..."}}` [ similar pattern] | Web/media search |

## Non-Search but Useful
- **Cerebras**: Code agents/full-stack dev. `npx -y cerebras-mcp` + `CEREBRAS_API_KEY`[6]
- **ElevenLabs**: TTS/audio. `python -m elevenlabs_mcp` + `ELEVENLABS_API_KEY=sk_77b4a263...`[7]

Restart Claude Code after edits. Run `claude mcp list` to verify connections. GitHub token enables repo MCPs like mgrep fully.[3][1]

## Human

please show the full windows claude mcp add commands for cerebras and elevenlabs

## Assistant

Here are the full Windows-compatible `claude mcp add` commands for Cerebras (code acceleration) and ElevenLabs (TTS/audio), using quoted syntax to avoid the "-y" parsing error. Run in PowerShell; they auto-update `~/.claude.json` with `cmd /c` wrapper.[1][2]

## Cerebras Code MCP
```
claude mcp add cerebras -e CEREBRAS_API_KEY=csk-fmjx928pc9p5nfyjr58xjy828eh8een4y9c9kh9yk84wttw5 -- "cmd /c cerebras-mcp"
```
- Install globally first: `npm install -g cerebras-code-mcp`[1]
- Provides fast code gen tools (20x speedup claimed).[3]

## ElevenLabs MCP
```
claude mcp add elevenlabs -e ELEVENLABS_API_KEY=[REDACTED] -- "cmd /c uvx elevenlabs-mcp"
```
- Install uv/uvx first (pipx or brew): `pipx install uv` for Python MCP runner.[2][4]
- Tools: text-to-speech, voice cloning, audio gen.

Restart Claude Code after each. Verify: `claude mcp list` (look for ✓ Connected). Test: `/mcp` in chat for tools like `generate_speech` or `code_plan`.[3][2]

## Human

What does the ElevenLabs MCP server enable in Claude, and What does the Cerebras MCP server enable in Claude

## Assistant

ElevenLabs MCP enables Claude to handle advanced audio workflows, while Cerebras MCP supercharges code generation with ultra-fast inference. Both integrate seamlessly as tools in Claude Code for agentic tasks.[1][2]

## ElevenLabs Capabilities
Lets Claude generate speech, clone voices, transcribe audio, and build voice agents directly in chats or projects. Key tools include text-to-speech (TTS), speech-to-text (STT), voice cloning from samples, and conversational AI for calls/outbound audio (e.g., "Read this PDF aloud" or "Order pizza via voice"). Ideal for podcasts, audiobooks, or voice prototypes with sub-second latency.[3][4][5][1]

## Cerebras Capabilities
Provides high-speed code execution (up to 2,100 tokens/sec or 20x GPU speedup) using models like Llama 3.1 70B or Qwen 3 Coder. Core tool: `write` for multi-file code gen/refactor with Git-style diffs, real-time file read/write, and agentic loops (Claude plans, Cerebras implements). Avoids rate limits; excels in bulk edits, precise implementation, and "cerebral coding" flow.[6][2][7][8]

## Human

How do I setup Cerebras MCP for code generation in Claude

## Assistant

To set up Cerebras MCP for code generation in Claude Code on Windows 11, install the official NPM package and run its setup wizard, which configures MCP automatically. This enables the `write` tool for 20x faster code edits with models like Llama 3.1 or Qwen 3 Coder via your API key.

## Prerequisites
- Node.js 18+ and npm (nodejs.org).
- Cerebras API key: `csk-fmjx928pc9p5nfyjr58xjy828eh8een4y9c9kh9yk84wttw5` (already have).
- Claude Code CLI.

## Step-by-Step Setup
1. Install globally (PowerShell as admin):
   ```
   npm install -g cerebras-code-mcp
   ```


2. Run config wizard:
   ```
   cerebras-mcp --config
   ```
   Enter your key when prompted; it auto-adds to Claude Code's `~/.claude.json` (uses `cmd /c` for Windows).

3. Verify:
   ```
   claude mcp list
   ```
   Expect: "cerebras-code: cerebras-mcp ✓ Connected".

4. Restart Claude Code fully.

## Usage for Code Gen
In Claude Code chat, use the `write` tool:
- "Use write to create a React login form with auth."
- Handles multi-file diffs, Git-style previews, read/write filesystem.
- Fallback to OpenRouter if rate-limited (optional key).

If issues, run `cerebras-mcp --remove` for cleanup.

## Human

Exa still won't connect.

## Assistant

Exa isn’t connecting because your config is very close but you’re likely hitting either a package-name / install issue or a Windows spawn problem. From the JSON you sent, the Exa entry itself is structurally fine.[1]

Your current Exa block (under `projects["P:/"].mcpServers`) is:
```json
"exa": {
  "type": "stdio",
  "command": "cmd",
  "args": [
    "/c",
    "npx",
    "-y",
    "@modelcontextprotocol/server-exa"
  ],
  "env": {
    "EXA_API_KEY": "ce612530-8294-4a00-9c06-578c3974f286"
  }
}
```


### What to fix / try

1. **Use the official package name and install it globally**
   - In PowerShell:
     ```powershell
     npm install -g @modelcontextprotocol/server-exa
     ```
   - This avoids npx needing to download every time and makes errors clearer.[2]

2. **Simplify the command in your config**
   In `file.claude.json` (your `%APPDATA%\Claude\claude_desktop_config.json` equivalent), under the same `exa` entry, change to:
   ```json
   "exa": {
     "type": "stdio",
     "command": "cmd",
     "args": [
       "/c",
       "server-exa"
     ],
     "env": {
       "EXA_API_KEY": "ce612530-8294-4a00-9c06-578c3974f286"
     }
   }
   ```
   This uses the installed CLI (`server-exa`) instead of going through `npx -y ...`, which is exactly what’s causing you grief on Windows with other MCPs too.[3][2]

3. **Alternative: keep npx but drop `-y`**
   If you want to stick with npx:
   ```json
   "exa": {
     "type": "stdio",
     "command": "cmd",
     "args": [
       "/c",
       "npx",
       "@modelcontextprotocol/server-exa"
     ],
     "env": {
       "EXA_API_KEY": "ce612530-8294-4a00-9c06-578c3974f286"
     }
   }
   ```
   The `-y` flag is optional and is exactly what Claude’s Windows arg parser keeps choking on.[4][5]

4. **Fully restart and then check status**
   - Quit all Claude Code/Desktop windows, make sure no background process is running.
   - Re-open Claude Code on `P:\`.
   - Run in a terminal:
     ```powershell
     claude mcp list
     ```
     and see what it says for `exa` (Connected / Failed to connect / missing command).[1]

5. **If still failing, capture the error**
   In Claude Code’s integrated terminal (inside the same project root), run manually:
   ```powershell
   cmd /c server-exa
   ```
   or, if using the npx variant:
   ```powershell
   cmd /c npx @modelcontextprotocol/server-exa
   ```
   and tell me what error you see; that will reveal whether it’s an Exa auth error, a Node path issue, or something about the binary itself.[2]

What do you see for the `exa` row when you run `claude mcp list` after making one of these changes?

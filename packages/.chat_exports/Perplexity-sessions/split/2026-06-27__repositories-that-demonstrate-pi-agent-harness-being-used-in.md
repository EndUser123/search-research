---
title: "repositories that demonstrate PI agent harness being used inside or invoked from the Claude Code CLI"
date: "2026-06-27"
mode: "COPILOT"
uuid: "dc6e34e1-59cc-4dac-a5b4-d853ca72c7b1"
entry_count: 3
---

## Human

repositories that demonstrate PI agent harness being used inside or invoked from the Claude Code CLI

## Assistant

Let me summarize what I've found and clarify the situation:

## Key Finding: No Repositories Found Demonstrating Pi Agent Harness *Inside* Claude Code CLI

Based on my search, **there are no repositories that demonstrate the Pi agent harness being used *inside* or *invoked from* the Claude Code CLI**. Here's why:

### Pi Agent Harness is a **Competitor**, Not an Integration

| Aspect | Pi Agent Harness | Claude Code CLI |
|--------|-----------------|-----------------|
| Relationship | Independent alternative coding agent [1][2] | Independent coding agent CLI [2][3] |
| Architecture | Separate CLI with 4 tools (Read, Edit, Write, Bash) [2][4] | Separate CLI with its own tool set [2][5] |
| Integration Direction | "See OpenClaw for a real-world integration" of Pi [1] | OpenClaw can invoke Claude Code as a backend [6][7] |

### What Actually Exists:

1. **`github.com/earendil-works/pi`** — The main Pi agent harness repository[1][4]
   - Standalone CLI: `@earendil-works/pi-coding-agent`
   - Not integrated *into* Claude Code

2. **`github.com/13rac1/openclaw-plugin-claude-code`** — OpenClaw plugin that executes Claude Code sessions[7]
   - This invokes Claude Code *from* OpenClaw, not Pi *inside* Claude Code

3. **`github.com/Dicklesworthstone/pi_agent_rust`** — Rust reimplementation of Pi[8][9]
   - Installs a skill for both Claude Code and Codex CLI
   - But this is a *skill* that lets Claude Code invoke Pi's tools, not Pi harness running *inside* Claude Code

4. **`github.com/DietrichGebert/ponytail`** — Has "Pi agent harness" installation command[10]
   - `pi install git:github.com/DietrichGebert/ponytail`
   - This installs *to* Pi CLI, not *into* Claude Code

### The Confusion Source:

The user's query may stem from conflating:
- **OpenClaw** (meta-agent orchestrator that can run multiple harnesses including Claude Code and Pi)[11][1]
- **Pi agent harness as a skill** that Claude Code can invoke via bash/process tools[8]
- **Pi-to-Pi communication** within the `pi-vs-claude-code` repo[12][13]

### Clarifying Question:

Are you looking for:
1. Repositories where **OpenClaw orchestrates both Pi and Claude Code** as separate agents?
2. Repositories where **Claude Code invokes Pi as a sub-agent** via bash/process tools?
3. The actual **Pi agent harness repository** itself (`earendil-works/pi`) to understand how it works independently?

## Human

strangly I found repos for using agy from claude code, and that's a competitor.

## Assistant

Excellent! Now I found the specific repositories. Let me clarify what you found and why it makes sense:

## Yes, You Found Repositories Using **agy** (Google Antigravity CLI) from Claude Code

This is actually **similar to what you were looking for with Pi**, and here's why it exists:

### Key Repositories That Integrate agy from Claude Code:

| Repository | Description | Integration Pattern |
|------------|-------------|---------------------|
| **`davdittrich/delegate-agy`** | Claude Code plugin that routes tasks to agy [1] | Routes Claude tasks to agy for Gemini 3.1/3.5, GPT-OSS 120B access [1] |
| **`AIgen-Solutions-s-r-l/agy-claude-plugin`** | Four-command suite (/agy, /agy-review, /agy-debug, /agy-panel) [2] | Fronts Gemini, Claude, GPT-OSS through Antigravity CLI for inline opinions [2] |
| **` VoltAgent/awesome-claude-code-subagents`** | Collection of 154+ Claude Code subagents [3][4] | Includes agy as a subagent pattern for delegating tasks [3] |

### How It Works (from the Reddit post):

```
"It basically has Claude work with a headless Agy terminal, 
and just reads the responses. I can even load up Agy in a 
different terminal and see..." [web:35]
```

- Claude Code spawns a headless agy terminal process
- Reads agy's responses via stdout
- Even supports running agy in a separate terminal while Claude orchestrates[5]

### Why This Makes Sense (Competitor Integration):

| Reason | Explanation |
|--------|-------------|
| **Multi-model review** | agy + Codex as independent reviewers, synthesized output [6][7] |
| **Access different models** | agy gives Gemini 3.1/3.5, GPT-OSS 120B that Claude doesn't have [1] |
| **Parallel verification** | Cross-vendor multi-agent review jury: claude, codex, agy [7] |
| **Specialized strengths** | agy for Google-stack/parallel agents, Claude for complex reasoning [8] |

### The Pattern: **Agent Orchestration Across Competitors**

This is actually the **same pattern** you'd use for Pi:

```
┌─────────────────┐
│  Claude Code    │  (main orchestrator)
│  CLI            │
└────────┬────────┘
         │ spawns headless process
         ▼
┌─────────────────┐
│  agy / Pi       │  (competitor agent)
│  terminal       │
└─────────────────┘
```

### Why Pi Is Different from agy in This Context:

| Aspect | agy (Antigravity) | Pi Agent Harness |
|--------|------------------|------------------|
| **Google official** | Yes - Google's replacement for Gemini CLI [8] | No - open-source by Mario Zechner [9][10] |
| **Claude plugin exists** | Yes - multiple agy-claude plugins [2][1] | No - Pi is standalone, not integrated into Claude |
| **Multi-agent focus** | Strong - Google's multi-agent model [8] | Minimal philosophy - 4 tools only [9][11] |

## So Your Observation Is Correct:

You found that **agy (Google's competitor)** has Claude Code integration plugins, while **Pi (another competitor)** doesn't have the same level of integration. This makes sense because:

1. **agy is Google's official CLI** - has more investment in integrations
2. **Pi is minimal/open-source** - focuses on being standalone
3. **Both follow the same pattern** - competitor agents can be invoked from Claude via headless terminal processes

The pattern is: **Claude orchestrates → spawns competitor agent as subprocess → reads output**[5]

## Human

I even found repos using codex from inside claude code.

## Assistant

**YES!** This is exactly what you found. Now I have the complete picture:

## The Official Repository: **`openai/codex-plugin-cc`**

This is the **official OpenAI plugin** that brings Codex inside Claude Code:[1][2]

```
GitHub: https://github.com/openai/codex-plugin-cc
⭐ 20k stars | 1.2k forks | Apache-2.0 license
```

### How It Works:

```
This plugin delegates through the local Codex CLI and Codex app server.
So it uses the same local auth, config, environment, and MCP setup 
you already have with Codex. That is why it feels lightweight.
It is not a separate runtime. It is Codex, just invoked from inside Claude Code.
```


### Commands You Get:

| Command | Purpose |
|---------|---------|
| `/codex:review` | Normal read-only Codex review [1][READMIT] |
| `/codex:adversarial-review` | Steerable challenge review questioning design [1][READMIT] |
| `/codex:rescue` | Delegate work to Codex as background job [1][READMIT] |
| `/codex:status` | Check running/recent Codex jobs [1][READMIT] |
| `/codex:result` | Show final Codex output for finished job [1][READMIT] |
| `/codex:cancel` | Cancel active background job [1][READMIT] |
| `/codex:setup` | Check Codex installation/authentication [1][READMIT] |

### Installation:

```bash
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

***

## Complete Pattern: **Competitor Agents Inside Claude Code**

Now you've found the full pattern:

| Agent | Repository | Official? | Integration Pattern |
|-------|------------|-----------|---------------------|
| **Codex** (OpenAI) | `openai/codex-plugin-cc` | ✅ Official OpenAI plugin [1][2] | Delegates through local Codex CLI + app server [1] |
| **agy** (Google Antigravity) | `davdittrich/delegate-agy` | ❌ Third-party | Routes tasks via headless agy terminal [3][4] |
| **agy** (Google) | `AIgen-Solutions-s-r-l/agy-claude-plugin` | ❌ Third-party | 4-command suite (/agy, /agy-review, /agy-debug, /agy-panel) [5] |
| **Pi** (Mario Zechner) | ❌ None | ❌ None | No integration - standalone CLI only [6][7] |

***

## Why Codex Has Integration But Pi Doesn't:

| Factor | Codex | Pi |
|--------|-------|-----|
| **Company backing** | OpenAI (major investment in integrations) [1] | Open-source individual (Mario Zechner) [6] |
| **Plugin ecosystem** | Official marketplace plugin [1][2] | No plugin ecosystem |
| **App server** | Codex app server (open ecosystem) [2] | No app server |
| **Official integration** | Yes - OpenAI built it directly [2] | None - standalone philosophy |
| **Use case** | "Review, challenge, delegate" to different model [1] | Minimal - 4 tools only, no multi-model focus [6][8] |

***

## The Pattern You're Seeing:

```
┌─────────────────┐
│  Claude Code    │  (main orchestrator)
│  CLI            │
└────────┬────────┘
         │
         ├─→ /codex:review        (OpenAI official plugin)
         ├─→ /agy:review          (Third-party Google plugin)
         └─→ headless Pi terminal (No plugin - manual shell)
              ℝ░░░░░░░░░░░░░░░░░ Not integrated
```

***

## So Your Observation Is Perfect:

You found **Codex inside Claude Code** (official OpenAI plugin), **agy inside Claude Code** (third-party Google plugins), but **Pi has no such integration** because:

1. **Codex is OpenAI's official product** → they built the plugin themselves
2. **agy is Google's official CLI** → has third-party plugins built for it
3. **Pi is minimal/open-source** → focuses on being standalone, no integration effort

The pattern: **Major companies (OpenAI, Google) → official integrations**. **Open-source individuals → standalone only**.

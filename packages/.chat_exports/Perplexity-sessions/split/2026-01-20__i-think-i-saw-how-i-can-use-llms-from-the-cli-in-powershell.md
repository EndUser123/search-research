---
title: "I think I saw how I can use llms from the cli in powershell.  Are there repos for that?"
date: "2026-01-20"
mode: "COPILOT"
uuid: "24377ff3-c4b5-43bb-8d8b-99cfd2920c1b"
entry_count: 4
---

## Human

I think I saw how I can use llms from the cli in powershell.  Are there repos for that?

## Assistant

Yes, several GitHub repositories provide ways to access LLMs directly from the PowerShell CLI, often integrating with tools like Ollama for local models or APIs from OpenAI and others. These are tailored for Windows/PowerShell environments, aligning with your setup.

## Key Repositories
- **Ollama PowerShell Helpers** (gist.github.com/halr9000/e95618baaee2ee25c5e1ffbc66dba98d): Utility functions to interact with Ollama's CLI and API. Dot-source the .ps1 file into your session for commands like `ask` to query local LLMs such as Llama 3.1.[1]
- **PoshLLM** (github.com/DevPossible/PoshLLM): Brings LLMs to your PowerShell REPL, with seamless support for local Ollama instances. Ideal for quick interactions without leaving the terminal.[11]
- **ShellLM** (github.com/Digit404/ShellLM): A versatile PowerShell-based terminal app for chatting with LLMs, supporting multiple providers.[10]

## Setup Tips
These often require installing Ollama via `winget install ollama.ollama`, pulling a model like `ollama pull llama3.1`, then sourcing the scripts. For your multi-terminal workflow, add them to your profile or use git worktrees for testing. Check the repos for PowerShell 7.5+ compatibility on Windows 11.[1]

## Human

I'm not using local models.  What are the most popular for stars?

## Assistant

Based on GitHub stars, the most popular CLI tools for accessing LLMs from the command line are:

## Top CLI Tools by Stars

**Simon Willison's `llm`** — The most established and popular choice. It's a Python-based CLI that works with OpenAI, Claude (Anthropic), Gemini, and dozens of other providers. It's designed as a flexible tool with an extensible plugin system, making it ideal for integrating various LLM APIs into your workflow. Widely used for quick queries and scripting.[1][2]

**`aichat` by sigoden** — ~8.4k stars. An all-in-one LLM CLI tool featuring shell assistance, chat REPL, RAG, and agent capabilities. Supports 20+ providers including OpenAI, Claude, Gemini, Ollama, Groq, and more. Built in Rust for speed.[3]

**Gemini CLI / Easy LLM CLI** — Fork variants with multi-provider support (Gemini, OpenAI, custom APIs compatible with OpenAI's format). Popular for its simplicity and wide provider compatibility.[4]

**Claude Code** — Anthropic's closed-source terminal tool, dominant in the agentic coding space. Can be extended to work with other providers via proxy tools like Claude Code Proxy.[5][6]

For PowerShell specifically, the **Claude Code Toolkit** is worth noting—it's a cross-platform toolkit for managing Claude Code installation with support for multiple Anthropic-compatible API providers, with specific PowerShell support built in.[7]

If you want a pure Python CLI that works cross-platform (including PowerShell), **`llm`** is the most starred and widely trusted choice. You'd install it with `pip install llm` and then configure your API keys for your preferred provider.

## Human

Is there a powershell based version?

## Assistant

Based on my search, there are a few PowerShell-native options, though they're less established than their Python counterparts:

## Native PowerShell LLM Tools

**PSAI** (dfinke/PSAI) — The most mature PowerShell-native LLM module. It's a direct port of the OpenAI Python SDK and works with OpenAI's API. Install via `Install-Module -Name PSAI`. Created by Doug Finke (15-time Microsoft MVP).[1][2]

**PSAISuite** (dfinke/psaisuite) — A newer unified PowerShell interface that supports multiple LLM providers (OpenAI, Anthropic Claude, Azure AI, Nebius) with a standardized interface. Released recently (Jan 2025). This is particularly useful since you work with Claude—it lets you swap between providers without changing code.[3]

**ShellLM** (Digit404/ShellLM) — A versatile PowerShell-based LLM chat interface, though it appears to have limited GitHub stars compared to others.[4]

**GenXdev.AI** — A PowerShell module with `Invoke-AIPowershellCommand` (aliased as `hint`) that generates and executes PowerShell commands from natural language queries. Available on PowerShell Gallery.[5]

## Reality Check

The plain truth: **native PowerShell LLM tools have far fewer stars than language-agnostic CLI tools** like Simon Willison's `llm` (which you can use from PowerShell via `Invoke-Expression` or direct shell invocation). Most production PowerShell LLM work is either:

1. **Using PSAI/PSAISuite** within PowerShell scripts (purpose-built but smaller community)
2. **Calling external CLI tools** like `llm` or `aichat` via `Invoke-Expression` or `&` operator
3. **Wrapping REST API calls directly** with `Invoke-RestMethod` (most flexible, most verbose)

For your agentic workflow and multi-terminal setup, **PSAISuite** might align best since it supports Claude natively alongside other providers.

## Human

so between, [llm](https://github.com/simonw/llm) [aichat](https://github.com/sigoden/aichat) [psaisuite](https://github.com/dfinke/psaisuite), there's no meaningful different for windows 11?

## Assistant

Looking at the three tools with your Windows 11 + PowerShell setup, here are the **meaningful differences**:

## Cross-Platform Viability

**`llm` (Python)** — Works on Windows 11, but you need Python installed. Install via `pip install llm`, then call it from PowerShell as a subprocess. Works fine, but adds Python as a dependency.

**`aichat` (Rust)** — **Best for Windows 11**. Pre-built Windows binary available (scoop or direct download). No dependencies—just drop the executable in PATH. Runs natively. Built-in shell integration, RAG, agents, multiple providers (OpenAI, Claude, Gemini, etc.).[1]

**`PSAISuite` (PowerShell)** — **Native to your environment**. Pure PowerShell, 100% written in PowerShell. No external dependencies. Unified interface supporting OpenAI, Anthropic, Azure AI, Groq, GitHub Models, and 10+ others. Tab completion for model names.[2]

## Meaningful Windows 11 Differences

| Factor | `llm` | `aichat` | `PSAISuite` |
|--------|-------|---------|-----------|
| **Installation** | Requires Python | Standalone binary | `Install-Module PSAISuite` |
| **Native PowerShell** | No (subprocess calls) | No (binary) | Yes—direct cmdlets |
| **Multi-terminal workflows** | Awkward with `&` or `Invoke-Expression` | Cleaner as external tool | Most integrated—cmdlet piping |
| **Context/piping** | Limited | Good shell integration | Excellent—native PowerShell piping |
| **Configuration** | Config files | YAML config | Environment variables + cmdlets |
| **GitHub stars** | ~17k+ | 8.4k | 49 (newest, least discovered) |

## The Real Trade-Off for Windows 11

**`aichat`** is the "most portable"—you get a polished, feature-rich CLI tool with no setup friction. But it's external to PowerShell.

**`PSAISuite`** is the "most integrated"—you stay in PowerShell's ecosystem with native piping, object handling, and your existing terminal workflows. For your multi-terminal, agentic workflow, this means you can pipe command output directly:

```powershell
Get-Process | Out-String | icc -Messages "analyze running processes" -Model "anthropic:claude-3-5-sonnet"
```

vs. with `aichat` you'd do:
```powershell
Get-Process | Out-String | & aichat "analyze running processes" --model claude-3-5-sonnet
```

**Bottom line:** On Windows 11, if you're already deep in PowerShell automation (which you are), **`PSAISuite` removes friction**. If you want a standalone tool that works everywhere, **`aichat`** is objectively better engineered. If you already have Python, **`llm`** is most battle-tested.[3]

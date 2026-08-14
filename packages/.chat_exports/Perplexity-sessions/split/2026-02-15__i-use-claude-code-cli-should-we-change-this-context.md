---
title: "I use claude code cli.  should we change this context?"
date: "2026-02-15"
mode: "COPILOT"
uuid: "78f0ce2b-748d-4554-9143-d3de04646404"
entry_count: 3
---

## Human

I use claude code cli.  should we change this context?

## Assistant

Yes—using a more specific context than `desktop-app` is worth doing, but you want it aligned with how you’re actually driving Claude Code.

From your screenshot, these contexts look like different “profiles” for prompting and tools. `desktop-app` sounds like a generic, GUI-focused profile, which is probably not ideal for a heavy CLI + IDE workflow. Instead:

- Use `claude-code` when you want the context optimised for coding, refactors, test generation, and file‑aware operations.
- Use `ide` if that profile is tuned for editor/LS‑style interactions (navigation, inline edits, quickfixes).
- Keep `agent`/`oaicompat-agent` for multi‑step autonomous runs or when you’re chaining tools.
- Reserve `chatgpt`/`codex` only if you’re targeting those APIs or doing compatibility testing.

A practical split that should work well for you is:
- Shell/CLI‑driven sessions: `claude-code`
- Editor‑centric sessions (VSCode/Antigravity hooks, codebase‑wide ops): `ide`
- Experimental multi‑tool runners: `agent`

If you tell me exactly how your current Claude Code CLI command is structured (flags, config, where context is referenced), I can sketch a minimal config change so you can swap contexts quickly (e.g., per‑project defaults or a shell function to toggle).

## Human

is that actually how serena works?

## Assistant

Mostly yes, but with two key clarifications.

1. What a “context” actually is  
   - In Serena, a context is a named configuration that sets the system prompt and which tools are exposed, and it is fixed for the lifetime of a session.[1][2]
   - Built‑in contexts include `desktop-app`, `agent`, `ide-assistant`, `claude-code`, `ide`, `codex`, `chatgpt`, and `oaicompat-agent`, stored as YAML definitions under `contexts/`.[3][2]

2. How you’re meant to pick one  
   - Official docs describe the intent like this: `desktop-app` is the default for Claude Desktop and similar GUI clients, `ide-assistant`/`ide` are for IDE integrations, and `agent`/`oaicompat-agent` are for more autonomous or OpenAI‑compatible agent frameworks.[4][2][1][3]
   - `claude-code` and `ide` are marked as “single-project contexts,” meaning when launched with a project they limit tools to just what that project needs, which is usually what you want when driving Serena from Claude Code CLI against one repo.[2]

So: Serena really does work by selecting one of these predefined contexts at startup (or a custom one you add in `~/.serena/contexts`), and you should choose the one that best matches your integration rather than sticking with `desktop-app` by default.[1][3][2]

## Human

i have a monorepo with many projects.

## Assistant

For a monorepo, Serena expects you to model each “project” explicitly and then decide whether you want single‑project or multi‑project behavior.[1][2][3]

### How Serena sees projects in a monorepo

- You define each logical project inside the monorepo with its own `.serena/project.yml` under the relevant subfolder.[2][3]
- You can also have one project at the monorepo root if you often do cross‑cutting work across packages/services.[4][5][6]
- `project.yml` lets you set languages, ignore rules, tools, and modes per project, so a TS frontend and Python backend can be configured differently inside the same repo.[4][2]

### Context choice with many projects

- `claude-code` and `ide` contexts are marked as `single_project: true`, which means you pass `--project <path|name>` when starting the MCP server and Serena locks onto that one project; project‑switching tools are disabled.[1][2]  
- Non‑single‑project contexts like `desktop-app` or `agent` keep project activation tools enabled, so the agent can switch between multiple configured projects during one session (useful if you hop between packages in the monorepo).[3][7][1]

### Recommended pattern for your use case

- If you usually work deeply inside one package at a time (e.g., backend today, frontend tomorrow), keep using a single‑project context such as `claude-code` and start Serena with `--project` pointing at that subfolder’s `.serena/project.yml` from your Claude Code CLI config.[1][2][3]
- If you frequently implement changes that touch multiple projects in one flow, consider a non‑single‑project context (e.g., `agent` or a custom context derived from it), list all your monorepo projects in `serena_config.yml`, and let Serena’s project‑activation tool switch between them.[2][3][1]

If you paste your monorepo layout (just folder names) and how you currently launch the Claude Code CLI + Serena, I can propose concrete context and `project.yml`/`serena_config.yml` snippets tailored to that structure.

---
title: "i have both the codex cli and the codex extension in vscode.  How can I set a default prompt like claude.md?"
date: "2026-01-13"
mode: "COPILOT"
uuid: "a695299e-8a10-4f04-b056-5b19afbeb7ce"
entry_count: 1
---

## Human

i have both the codex cli and the codex extension in vscode.  How can I set a default prompt like claude.md?

## Assistant

You can get very close to a `CLAUDE.md`-style default prompt in Codex, but it works a bit differently: instead of one magic filename, you configure defaults via Codex settings and, optionally, an `AGENTS.md` file.

## Codex CLI default “prompt”

For the CLI, the usual pattern is:

- Create an `AGENTS.md` file in your project or home directory with your persistent instructions (coding style, tools, workflows, etc.).[1]
- Use the `/init` command inside the Codex TUI to load and apply those defaults when starting a new session.[1]
- Some setups also support a global config file (similar to Claude’s `~/.claude/CLAUDE.md`) that Codex reads to seed each new agent/session, but the documented convention people are using right now is `AGENTS.md` + `/init`.[2][1]

This gives you the same effect as “always start Codex with this base prompt,” just driven by the agents file rather than a single `CLAUDE.md` name.

## VS Code Codex extension defaults

In VS Code, Codex shares configuration with the CLI and inherits its defaults rather than looking for `CLAUDE.md` specifically.  Current behavior is:[3]

- The extension does **not** yet expose user-defined prompt files in the same way as Claude Code’s `CLAUDE.md`, and the open issues around slash-command parity and custom commands suggest this is still evolving.[4][5]
- The recommended approach today is:
  - Put your persistent instructions in an `AGENTS.md` (project-level, tracked in git) and use `/init` or the equivalent agent-setup flow when you start Codex in that workspace.[2][1]
  - Use Codex’s config/settings (from the CLI side) to define default agent configuration (model, reasoning level, access mode), which the VS Code extension then reuses.[3]

In other words, Codex does not support a literal `CLAUDE.md`-style auto-read file name, but you can emulate a default prompt by:

- Storing your guidelines in `AGENTS.md` (or similar)  
- Using `/init` at the start of a session (CLI or VS Code agent) so Codex pulls those instructions into the system/user prompt each time.[1][2]

If you describe the exact behavior you want (per-workspace vs truly global, auto-applied vs triggered), it is possible to narrow this down to a specific `codex` config + `AGENTS.md` layout that behaves almost identically to your current `CLAUDE.md` workflow.

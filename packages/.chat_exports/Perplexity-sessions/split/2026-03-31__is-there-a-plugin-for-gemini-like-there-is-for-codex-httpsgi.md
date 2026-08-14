---
title: "Is there a plugin for gemini like there is for codex?  [https://github.com/openai/codex-plugin-cc](https://github.com/op"
date: "2026-03-31"
mode: "COPILOT"
uuid: "0059e017-6e32-4fbd-b9b0-02a132fc89c1"
entry_count: 1
---

## Human

Is there a plugin for gemini like there is for codex?  [https://github.com/openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)

## Assistant

No direct equivalent to OpenAI's codex-plugin-cc (a Claude Code plugin for Codex) exists specifically for Google's Gemini CLI, but Gemini CLI supports a robust native extensions system for plugins, MCP servers, custom commands, and context files via `gemini extensions install <GitHub URL>`.[1][2]

## Gemini CLI Extensions
Gemini CLI extensions package reusable capabilities like MCP servers (e.g., for tools/skills), custom prompts/commands in TOML, and context (e.g., GEMINI.md), installed one-click from GitHub repos into `~/.gemini/extensions`.  They enable workflows akin to codex-plugin-cc's bundling of skills/MCP, with conflict resolution prioritizing workspace/user configs.  Install requires `git`; update via `gemini extensions update --all`; restart CLI for changes.[2]

## Cross-Tool Plugins
Community repos like co-researcher provide plugins compatible with Gemini CLI, Claude Code, Codex, and OpenCode, installable via `gemini extension install https://github.com/poemswe/co-researcher`.  Others like cc-gemini-plugin integrate Gemini into Claude Code environments.  No official "codex-plugin-cc port" found; check Gemini CLI's extensions catalog or GitHub for equivalents.[3][4][5][2]

## Next Steps
1. Install Gemini CLI: `npm install -g @google/gemini-cli` (assumed from patterns).[6]
2. Test extensions: `gemini extensions install https://github.com/gemini-cli-extensions/security`.[2]
3. Browse: https://google-gemini.github.io/gemini-cli/docs/extensions/ or partner catalog.[4][2]

For TypeScript/Node examples of building one, query "gemini cli extension boilerplate TypeScript".

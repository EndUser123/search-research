---
title: "what are popular repos for claude code or codex, t hat use multiple external llms to consult with?"
date: "2026-06-15"
mode: "COPILOT"
uuid: "974c902b-c103-4927-ad9e-7811538a07aa"
entry_count: 1
---

## Human

what are popular repos for claude code or codex, t hat use multiple external llms to consult with?

## Assistant

Yes — the strongest matches are repos that either **route Claude Code/Codex across multiple model providers** or **coordinate multiple coding agents in parallel**. The most notable one I found is `affaan-m/everything-claude-code`, which explicitly supports Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, GitHub Copilot, and more across the same harness surface.[1]

## Good starting repos

| Repo | What it does | Why it fits |
|---|---|---|
| `affaan-m/everything-claude-code` | Cross-harness agent system with skills, hooks, rules, MCP, memory, and install targets for Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, and Copilot [1]. | Best fit if you want one repo that already spans multiple coding harnesses. |
| `hesreallyhim/awesome-claude-code` | Curated directory of Claude Code skills, hooks, slash commands, orchestrators, apps, and plugins [2]. | Best if you want discovery rather than a single framework. |
| `ypollak2/llm-router` | Universal LLM router for coding tools including Claude Code, Cursor, Codex, Gemini CLI, and Copilot [3]. | Good if your goal is consulting multiple external LLMs through routing. |
| `NadirRouter/NadirClaw` | Drop-in proxy/router that intercepts Claude Code and routes prompts to cheaper or different models, also supporting Codex and Cursor [4]. | Useful for multi-model fallback and cost optimization. |
| `ruvnet/ruflo` | Multi-agent harness for Claude Code and Codex with orchestration across many agents and providers [5]. | Better if you want many agents collaborating, not just model routing. |

## Most relevant patterns

There are really two patterns here. First is **multi-provider routing**, where one interface sends requests to Claude, GPT, Gemini, local models, or other providers depending on task complexity or cost. Second is **multi-agent orchestration**, where multiple Claude/Codex instances work in parallel, often in separate worktrees or repos, then review each other’s output.[6][3][4][5]

## Practical recommendation

For your use case, I’d start with `everything-claude-code` if you want a broad, production-style harness that already spans Claude Code and Codex-like workflows. If your main objective is “consult multiple external LLMs,” then `llm-router` and `NadirClaw` are the clearest fit because they are explicitly about routing coding-tool traffic across providers.[3][4][1]

## Slight caveat

A lot of “best repo” lists on this topic are popularity-driven but not always precise about whether they support true multi-LLM consultation versus just multiple editors or multiple agents. So I’d treat routing repos and orchestration repos as separate categories rather than assuming they solve the same problem.[2][5][6][3]

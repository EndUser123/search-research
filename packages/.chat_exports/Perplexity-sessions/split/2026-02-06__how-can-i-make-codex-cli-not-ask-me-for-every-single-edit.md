---
title: "how can I make codex cli not ask me for every single edit?"
date: "2026-02-06"
mode: "CONCISE"
uuid: "84dbc337-d743-4b5a-a28d-43b033009361"
entry_count: 1
---

## Human

how can I make codex cli not ask me for every single edit?

## Assistant

**Use CLI flags or config changes to skip Codex CLI edit approval prompts.** These control when the tool pauses for human confirmation on file edits and commands.[1][2]

## CLI Flags
Run commands with `--ask-for-approval never` (or `-a never`) to disable all prompts, paired with a suitable sandbox like `--sandbox workspace-write` (-s workspace-write) for local development.[2]

- For balanced automation: `codex --full-auto "your task"` (sets approvals to on-request and workspace-write sandbox).[3][2]
- Full no-prompts: `codex -a never -s danger-full-access "your task"` (high risk; use isolated environments).[1][3]
- Extreme bypass: `codex --dangerously-bypass-approvals-and-sandbox "your task"` (equivalent to Claude's --dangerously-skip-permissions).[2][1]

On Windows, flags may not fully work—use WSL for reliability.[1][2]

## Config File
Edit `~/.codex/config.toml` (or `%USERPROFILE%\.codex\config.toml` on Windows) to set defaults.[4][2]

```
approval_policy = "never"
sandbox_mode = "workspace-write"
```
Launch with `codex -p auto` if using profiles, or override per-run with `-c approval_policy="never"`.[4][1]

## Safety Tips
Always use Git for recovery, enable logging (`~/.codex/log/`), and start with `--full-auto` before escalating to `never` or bypass flags. For your multi-terminal workflows, alias these in PowerShell: `Set-Alias cxauto 'codex --full-auto'`.[3][1]

---
title: "what json file does claude code track the model it isusing?"
date: "2025-12-12"
mode: "COPILOT"
uuid: "28962a78-ac49-428f-b088-e45f59dac8d1"
entry_count: 1
---

## Human

what json file does claude code track the model it isusing?

## Assistant

**Claude Code tracks the model it uses primarily through configuration files and session transcripts.**

## Configuration Files
Claude Code stores model settings in `settings.json` files, with the `model` field specifying the alias (like "opus" or "sonnet") or full model name used for sessions. User-wide settings live at `~/.claude/settings.json`, while project-specific ones are in `.claude/settings.json` (shared) or `.claude/settings.local.json` (local, git-ignored). These define the default or overridden model, with precedence from enterprise policies down to command-line flags like `claude --model sonnet`.[1][2][3]

## Session Tracking
Session transcripts in `~/.claude/projects/<project>/*.jsonl` files log the exact `model` ID used per interaction, found in the first 'init' line of the latest file. A temporary status file at `/tmp/claude_code_status.json` may also expose current model context for inspection. Use `/status` or `/model` commands during sessions to view the active model directly.[4][5][1]

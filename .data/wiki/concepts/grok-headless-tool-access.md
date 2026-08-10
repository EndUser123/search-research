---
title: Grok Build headless mode has full tool access including spawn_subagent
title_short: grok-headless-tool-access
date: 2026-08-09
verified_date: 2026-08-09
tags: [grok-build, headless-mode, spawn-subagent, tool-surface, subprocess-dispatch]
host: grok
---

# Grok Build headless mode has full tool access including spawn_subagent

## The verified fact

`grok -p "prompt"` (headless mode) runs non-interactively with **full tool access**,
including `spawn_subagent`, `read_file`, `search_replace`, `run_terminal_command`,
and all other built-in tools. Headless mode is NOT a text-only API call — it's a
complete agent session that runs, produces output, and exits.

**Verification receipt:** `grok --help` output shows these flags:
- `--no-subagents` — "Disable subagent spawning" (proves spawn_subagent is ON by default)
- `--yolo` — "Auto-approve all tool executions"
- `--tools <TOOLS>` — "Built-in tools to allow (comma-separated)"
- `--max-turns N` — multi-turn agent execution

Source: file:///C:/Users/brsth/.grok/docs/user-guide/01-getting-started.md:210-230

## What this means for orchestrator-controlled dispatch

A Python subprocess CAN invoke headless grok and get full tool access:

```python
subprocess.run([
    "grok", "-p", "fix these bugs: ...",
    "--yolo",                      # auto-approve tool executions
    "--output-format", "json",     # structured output
    "--cwd", repo_path,
])
```

This means Python orchestrators (like ship-py) could dispatch tool-capable agents
via `grok -p` — not just text-in/text-out analysis via `pi --no-tools`.

## Why ship-py uses `pi --no-tools` anyway (the design choice)

The analysis phases (review, risk, check, refactor, trace) intentionally use
`pi --no-tools` because they want **analysis only, no actions**. Giving the
dispatched model tool access would put it back in the control path, which is
exactly what the orchestrator-controlled pattern was designed to prevent.

| Transport | Tool access | Use case |
|-----------|-------------|----------|
| `pi --no-tools` | None | Analysis phases (read diff, produce findings JSON) |
| `pi --tools` | read/bash/edit/write | Analysis-with-actions (not currently used) |
| `grok -p --yolo` | Full (incl. spawn_subagent) | Could be used for fix phase automation |
| `grok -p --no-subagents` | Everything except subagent spawning | Bounded autonomy |

## The fabricated claim this corrects

**Session 019fe4c1 (2026-08-09):** the agent stated as fact:

> "spawn_subagent is a Grok Build tool — it's available to the LLM during a
> conversation turn, not callable from a standalone Python process. A subprocess
> has no access to the model's tool surface."

This was **wrong**. The user challenged with "are you sure?" and the claim
collapsed under verification (`grok --help` immediately showed `--no-subagents`).
The real reason for `pi` over `grok -p` is control scope, not Python limitations.

## Reference

- [[orchestrator-controlled-ship-py-phases]] — why the analysis phases use `pi --no-tools`
- Grok docs: file:///C:/Users/brsth/.grok/docs/user-guide/01-getting-started.md
- Related: [[tool-fallbacks]] for cross-model dispatch transport options

---
title: "Hook-health scanner for /todo + close-py gate"
created: 2026-08-12
status: open
session_id: 019ff2ae-915b-70e2-99ec-ccd70f72fe2e
tags: [hook-health, scanner, todo, close-py, fleet-monitoring]
---

# Hook-health scanner for /todo + close-py gate

## Objective

Connect the existing hook state producer (hook_failures.jsonl, timing logs) to a consumer. Data exists on disk; nothing reads it. The PGM wiki concept prescribed this 13 days ago.

## Scope

1. **New /todo scanner source**: `hook_health` — reads hook_failures.jsonl (session-scoped), timing logs (error phases), and checks for silent-death (registered hooks with 0 entries across recent sessions).

2. **close-py gate**: block CLOSE COMPLETE if any registered hook has 0 entries across the last N sessions (silent death detection per `[[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]]`).

## Acceptance criteria

- `/todo` surfaces hook blocks and errors for the current session
- `/todo` warns when a registered hook has 0 entries (possible silent death)
- close-py verdict phase checks hook health as an advisory signal

## Key files

- `~/.grok/hooks/state/hook_failures.jsonl` — block/error log (write-only by hooks)
- `~/.grok/hooks/state/*timing*.jsonl` — per-hook phase timing (read for error phases)
- `~/.grok/skills/todo/__lib/scanners/` — scanner registry
- `~/.grok/skills/close-py/__lib/phases/verdict.py` — close-py verdict phase

## Design decisions needed

- Distinguish "hook blocked the agent" (expected) from "hook errored" (unexpected) in hook_failures.jsonl
- Define "registered hook" — parse config.toml? Or hardcode the list?
- Silent-death false-positive: a hook that correctly doesn't fire (e.g., close-enforcement on a non-close session) shows 0 entries but isn't dead

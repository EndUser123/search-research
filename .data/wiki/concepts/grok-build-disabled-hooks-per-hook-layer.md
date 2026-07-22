---
title: "Grok Build's `~/.grok/disabled-hooks` Per-Hook Disable Layer"
created: 2026-07-20
source: session-2026-07-20
tags: ['grok-build', 'hooks', 'disable-mechanism', 'host-grok']
summary: >
  `~/.grok/disabled-hooks` is a file (not a directory) that lists per-hook disable paths in `plugin/<name>/hooks:<event>[N].hooks[N]` format. Distinct from `[plugins] disabled` in `config.toml` which is plugin-level. Two-layer disable model: enable the plugin, disable specific hooks within it.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
---

## Summary

Grok Build has a two-layer hook disable model. The plugin-level disable is `[plugins] disabled = [...]` in `~/.grok/config.toml` (verified by `grok inspect --json`: 55 enabled, 0 disabled). The hook-level disable is `~/.grok/disabled-hooks`, a JSON-encoded list of specific hook paths within enabled plugins. This file is a file, not a directory.

## Key Findings

- **File format.** `~/.grok/disabled-hooks` contains lines like `plugin/exec-gate/hooks:session_start[0].hooks[0]` — JSON-pointer-ish paths identifying a specific hook entry within a specific plugin's `hooks/hooks.json`.
- **Current contents** (as of 2026-07-20):
  - `plugin/exec-gate/hooks:session_start[0].hooks[0]`
  - `plugin/exec-gate/hooks:user_prompt_submit[0].hooks[0]`
  - `plugin/exec-gate/hooks:pre_tool_use[0].hooks[0]`
  - `plugin/exec-gate/hooks:session_end[0].hooks[0]`
- **Effect.** exec-gate plugin is enabled (provides hooks per inspect) but its SessionStart / UserPromptSubmit / PreToolUse / SessionEnd hooks are individually disabled. Without reading `disabled-hooks`, an enforcement-surface snapshot would falsely report these hooks as firing.
- **Distinction from `[plugins] disabled`.** Plugin-level disable prevents the plugin's skills/agents/hooks/MCP from loading at all. Per-hook disable keeps the plugin and its other components active, only suppressing the specific hook entries listed.
- **M1 active-surface-snapshot.py bug.** The M1 script does not read `~/.grok/disabled-hooks`. It reads `[plugins] enabled/disabled` and reports hooks as firing if the plugin is enabled. This is why the prior conversation's "what's actually firing" output was partially wrong — see [[grok-build-active-surface-snapshot-bugs]].

## Related

- [[grok-build-cc-aca-actually-enabled]] — the cc-aca-* suite fires at plugin level without per-hook disable
- [[grok-build-active-surface-snapshot-bugs]] — M1 should be reading this file but doesn't

## Auto-related

- [[grok-build-cc-aca-actually-enabled]]
- [[grok-build-plan-mode-structured-thinking]]

## Sources

- session-2026-07-20 — direct read of `~/.grok/disabled-hooks`
- session-2026-07-20 — `grok inspect --json` output showing 55 enabled plugins

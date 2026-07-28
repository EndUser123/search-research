---
title: "Grok Build host authority — don't confabulate across hosts"
created: 2026-07-20
tags: [decision, host-authority, grok-build, claude-code, anti-pattern, confabulation]
host: grok
agent: grok
verification: local-only
cognitive_load: 2
summary: >
  Grok Build and Claude Code have different hook types, payload formats, field names,
  and feature support. Do not assume Claude Code features work identically on Grok Build.
  Verify against ~/.grok/docs/user-guide/ before proposing any mechanism.
---

# Grok Build host authority

## Rule

On this host (Grok Build), `P:/.claude/CLAUDE.md` is a compat-loaded artifact, not the governing authority. The `~/.grok/AGENTS.md` is what governs Grok Build sessions. Before proposing any hook, command, or skill mechanism, cite the Grok Build doc that confirms it works here.

## Known differences

| Area | Claude Code | Grok Build |
|------|-------------|------------|
| Hook types | `command`, `prompt`, `agent` | `command`, `http` only |
| Stop payload | `tool_response` | `lastAssistantMessage` |
| Compat flags | N/A | `compat.claude.{hooks,skills,rules,agents,mcps}` |

## Falsifier

Wrong if Grok Build converges with Claude Code on all feature names and behaviors. Check `~/.grok/docs/user-guide/10-hooks.md` for current state.

## Relations

- [[grok-build-stop-hook-payload-lastassistantmessage]] — specific instance of this rule
- [[agents-md-construction-best-practices]]

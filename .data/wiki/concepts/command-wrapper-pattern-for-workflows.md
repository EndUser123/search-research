---
title: "Command-wrapper pattern for workflows: resolve dynamic values at the skill layer"
created: 2026-08-01
source: session-2026-07-31 (close-check workflow development)
tags: [workflow, command-wrapper, architecture, session-id, model-routing, design-decision, grok-build]
host: grok
agent: grok
verification: single-source-verified
cognitive_load: 2
relations:
  - target: wiki/concepts/intent-mode-gated-auto-composition.md
    type: related
  - target: wiki/concepts/grok-build-host-authority.md
    type: related
summary: >
  Workflow scripts (Rhai) have no access to env vars, filesystem listing, or
  session context. Dynamic values that workflows need (session ID, current
  best models from pick_model.py) must be resolved by a command wrapper
  (commands/<name>.md) that runs in the parent agent's context, then passed
  to the workflow via args. This is the same layering as hooks: the layer
  with access resolves; the layer without access executes.
---

# Command-wrapper pattern for workflows

## Decision context

**Why this was needed:** the close-check workflow needed the session ID and
quota-aware model assignments. Rhai has no env var access (GROK_SESSION_ID
is not exported to shell on Grok Build — verified). Four failed approaches
were tried before the correct pattern emerged: discovery agent (wasted
spawn + race condition), env var (empty), directory listing (races on
multi-terminal), workflow run dir introspection (no API). The fix: a command
wrapper at `~/.grok/commands/close-check.md` resolves these values from
context and passes them via `args`.

## The pattern

```
Operator types: /close-check
       ↓
Command wrapper (commands/close-check.md) resolves:
  - session_id: from prompt file path / system context
  - model_a: from pick_model.py --json --lane mechanical
  - model_b: second model from different provider
       ↓
Launches: workflow(name="close-check", args={session_id, model_a, model_b})
       ↓
Workflow (workflows/close-check.rhai) executes with resolved values
```

**The principle:** skills/commands have context that workflows don't. The
command layer resolves; the workflow layer executes.

## What workflows CAN'T access

| Need | Available? | Why |
|------|-----------|-----|
| `$GROK_SESSION_ID` env var | ❌ | Not exported to shell subprocesses on Grok Build |
| Filesystem listing | ❌ | Rhai has no `ls`/`glob`/`opendir` |
| Arbitrary env vars | ❌ | Rhai has no `getenv` |
| Session context (prompt path, system reminder) | ❌ | Only the parent agent has this |
| Shell commands (pre-workflow) | ❌ | Only `agent()` calls can run shell, and that costs a spawn |

## What the command wrapper CAN access

The parent agent's full context: system reminders, prompt file paths, session
directory, shell tools (run_terminal_command, pick_model.py), and LLM judgment.

## When to use this pattern

- Any workflow that needs session-specific identity (session_id, terminal_id)
- Any workflow that needs quota-aware model selection (pick_model.py)
- Any workflow that needs values resolved from conversation context

## What this means for our workspace

1. **All future workflows that need session context should have a command
   wrapper** at `~/.grok/commands/<name>.md`, not just a workflow file.
2. **The workflow file should have hardcoded fallbacks** for direct
   `/workflow <name>` invocation without the command wrapper.
3. **The command wrapper is the integration point** for pick_model.py,
   session discovery, and any other context-dependent resolution.

## Falsifier

This pattern is wrong if:
- The workflow runner starts injecting session context automatically (making
  the command wrapper unnecessary)
- A simpler approach exists that I didn't find (e.g., a Rhai function for
  session identity)

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| GROK_SESSION_ID not in shell | `echo $env:GROK_SESSION_ID` returned empty — run this session | [OBSERVED] |
| Rhai has no env/filesystem access | create-workflow SKILL.md lists full host API — no getenv, no ls | [OBSERVED] |
| Command wrapper resolves + passes args | close-check.md launched workflow with session_id + models — worked | [OBSERVED] |

## Auto-related

- [[grok-build-workflows-rhai-orchestration]]
- [[skill-catalog]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[agent-reliability-patterns-and-production-validation]]
- [[claude-code-external-tool-integration-via-mcp]]


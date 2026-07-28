---
title: "UserPromptSubmit hooks cannot auto-invoke skills on Grok Build"
created: 2026-07-28
source: session-2026-07-28
tags: [hooks, userpromptsubmit, grok-build, hook-limitations, passive-events, auto-routing]
summary: >
  On Grok Build, UserPromptSubmit hooks are passive-only: stdout is ignored,
  no context injection, no blocking, no prompt rewrite. A hook that detects
  a slash command (e.g., /handoff) and auto-creates a file produces an orphan
  artifact because the agent still receives the original prompt and invokes
  the skill normally, creating duplicate outputs with no reconciliation
  mechanism. Auto-command routing requires context injection, which only
  Claude Code's UserPromptSubmit supports (via additionalContext).
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/grok-pretooluse-deny-contract-verified
    type: extends
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: related
---

# UserPromptSubmit hooks cannot auto-invoke skills on Grok Build

## The constraint

Grok Build's `UserPromptSubmit` hook event is **passive-only**:

| Capability | Claude Code | Grok Build | Cursor |
|-----------|-------------|------------|--------|
| Block the prompt | Yes | **No** | Yes (buggy) |
| Inject context (`additionalContext`) | Yes | **No** | Buggy |
| Rewrite the prompt | No | **No** | No |
| Write side-effect files | Yes | Yes | Yes |

Source: Grok Build docs (`docs.x.ai/build/features/hooks`): "for events like
SessionStart or PostToolUse, stdout is ignored." UserPromptSubmit is in the
same passive category — it fires, can write files, but its stdout never
reaches the model.

Wiki cross-reference: `[[grok-pretooluse-deny-contract-verified]]` — "passive
events cannot inject context. UserPromptSubmit/PostToolUse/Stop hooks fire
and can write side-effect files, but their stdout is dropped entirely."

## Why this kills auto-command routing

The proposed pattern: a UserPromptSubmit hook detects `/handoff` in the prompt
text and auto-creates a handoff file without interrupting the conversation.

What actually happens:
1. Hook fires, detects `/handoff`, writes a handoff file to disk
2. The original `/handoff` prompt arrives at the agent unchanged (stdout ignored)
3. The agent invokes the `/handoff` skill normally, producing a canonical handoff
4. **Two handoffs exist** — the hook's orphan and the skill's canonical
5. No mechanism for the hook to tell the agent "I already handled this"

The orphan file is structurally disconnected from the user's intent. This is
the same failure class as [[no-deferred-persistence]]: a side effect that
isn't wired into the next action produces an orphan.

## Where auto-command routing DOES work

- **Claude Code**: `UserPromptSubmit` can inject `additionalContext`
  (system-reminder style) and block. The ClaudeFast Skill Activation Hook
  and `disler/claude-code-hooks-mastery` repo demonstrate the pattern.
  Claude Code also has `UserPromptExpansion` — a dedicated hook for
  slash-command auto-expansion that fires before the Skill tool.

- **Inside the agent**: the `/go` skill's delegation-packet classifier already
  does auto-routing — it reads the prompt, classifies it (score 0-6), and
  strips ceremony automatically. This works because it runs *inside* the
  agent's context, not as a side-effect that can't communicate back.

## Decision

**Do not build a UserPromptSubmit hook for auto-command routing on Grok Build.**
The agent-side pattern (behavioral rules in AGENTS.md, delegation-packet
detection in `/go`) is the correct layer for this capability.

## Falsifier

This finding is wrong if a future Grok Build release adds context injection
to UserPromptSubmit (making it non-passive). Check the hook docs at
`~/.grok/docs/user-guide/10-hooks.md` before re-proposing this pattern.

## Sources

- Grok Build hook docs: `~/.grok/docs/user-guide/10-hooks.md` L89, L304
- Wiki: `[[grok-pretooluse-deny-contract-verified]]` L98-100
- Web research: Claude Code hooks (`code.claude.com/docs/en/hooks`),
  ClaudeFast Skill Activation Hook, disler/claude-code-hooks-mastery,
  Cursor forum bug reports on beforeSubmitPrompt injection

---
title: "UserPromptSubmit hooks: can run Python, cannot inject context (Grok Build)"
created: 2026-07-28
source: session-2026-07-28
tags: [hooks, userpromptsubmit, grok-build, hook-limitations, passive-events, auto-routing]
summary: >
  On Grok Build, UserPromptSubmit hooks CAN run Python and write files, but
  stdout is ignored — no context injection back to the model. A hook that
  detects a slash command (e.g., /handoff) and pre-creates a file IS viable
  as a pre-processor; the limitation is that it cannot tell the agent "I
  already handled this" via stdout. The skill must check for existing files.
  Corrected 2026-07-28 after operator pushback: initial analysis wrongly
  dismissed the entire approach when only the context-injection path is blocked.
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

## What IS possible (corrected 2026-07-28 after operator pushback)

The hook CAN run Python and write files. The limitation is narrower than
initially stated: the hook cannot *inject context back to the model* (stdout
ignored), but it CAN write side-effect files that the agent reads later.

A UserPromptSubmit hook that detects `/handoff <topic>` and pre-creates a
handoff file IS viable:
1. Hook fires, reads prompt from stdin, detects `/handoff`
2. Python script calls the handoff-creation logic directly
3. Handoff file is on disk before the agent processes the prompt
4. Agent receives `/handoff <topic>`, invokes the skill
5. Skill finds the existing handoff, updates rather than duplicates

The constraint: the hook cannot tell the agent "I already handled this" via
stdout. But it doesn't need to — the file is on disk and the agent can read
it. The "duplicate artifact" problem is solvable by having the skill check
for existing handoffs (which `/handoff` auto-update mode already does).

**What does NOT work:** using the hook to *replace* the skill invocation
entirely (the prompt still arrives at the agent, the agent still invokes
the skill). The hook is a pre-processor, not a replacement.

## Decision (corrected)

**Viable with a design constraint.** A UserPromptSubmit hook can pre-create
handoff files as a side effect. The constraint is that stdout cannot reach
the model — so the hook can't inject "I handled this" context. The skill
must check for existing files to avoid duplicates. The original analysis
over-attributed the stdout limitation to mean "the whole approach is
non-viable," when only the context-injection path is blocked.

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
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

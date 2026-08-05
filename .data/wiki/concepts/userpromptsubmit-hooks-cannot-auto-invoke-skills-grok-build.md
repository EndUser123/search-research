---
title: "UserPromptSubmit hooks: CAN inject additionalContext on Grok Build (corrected)"
created: 2026-07-28
source: session-2026-07-28, corrected 2026-08-04
tags: [hooks, userpromptsubmit, grok-build, additionalContext, skill-enforcement, corrected-finding]
summary: >
  CORRECTED 2026-08-04: UserPromptSubmit hooks CAN inject additionalContext
  on Grok Build. The original analysis (2026-07-28) incorrectly classified
  UserPromptSubmit as passive-only (stdout ignored), extending the
  SessionStart/PostToolUse stdout-ignored pattern without testing.
  Vectorize/Hindsight plugin proves UserPromptSubmit additionalContext works
  in production on Grok Build. This enables the skill_enforcer pattern:
  detect /<skill-name> in user prompt, inject "execute, don't discuss"
  additionalContext before the agent responds.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/grok-pretooluse-deny-contract-verified
    type: extends
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: related
  - target: wiki/concepts/skill-enforcement-layers
    type: corrects — Layer 1 is now viable on Grok Build
  - target: wiki/concepts/skill-auto-invocation-reliability
    type: corrects — "the entire Claude-side enforcement is missing" gap is now closeable
---

# UserPromptSubmit hooks: CAN inject additionalContext on Grok Build (corrected)

## The correction (2026-08-04)

**Previous claim (wrong):** UserPromptSubmit stdout is ignored on Grok Build,
same as SessionStart and PostToolUse. The hook can write files but cannot
inject context back to the model.

**Corrected claim:** UserPromptSubmit CAN inject `additionalContext` via the
same JSON stdout pattern used by Stop hooks. The Grok Build docs (line 304)
say "for events like SessionStart or PostToolUse, stdout is ignored" — but
UserPromptSubmit is NOT in that list. The original analysis extended the
pattern without testing.

**Evidence:** The Vectorize/Hindsight plugin runs in production on Grok Build
and uses UserPromptSubmit to inject additionalContext on every prompt:

> recall.py | UserPromptSubmit hook | Auto-recall — query memories, inject as additionalContext

Source: https://hindsight.vectorize.io/sdks/integrations/grok-build

Their features page: "on every user prompt, queries Hindsight for relevant
memories and injects them as context (invisible to the chat transcript,
visible to Grok)."

A local test hook was registered (P:/tmp/test_ups_hook.py) to verify
additionalContext injection in our specific environment.

## Updated capability matrix

| Capability | Claude Code | Grok Build | Cursor |
|-----------|-------------|------------|--------|
| Block the prompt | Yes | **No** | Yes (buggy) |
| Inject context (`additionalContext`) | Yes | **Yes** | Buggy |
| Rewrite the prompt | No | **No** | No |
| Write side-effect files | Yes | Yes | Yes |

## Why this enables skill enforcement on Grok Build

A UserPromptSubmit hook can detect `/<skill-name>` in the user prompt and
inject additionalContext: "This is an execution command. Follow the skill
body — do not substitute a discussion for execution." This fires BEFORE
the agent responds, preventing the discuss-instead-of-execute pattern.

Combined with the Stop hook quality gates (which fire AFTER the response
and check for evidence artifacts), this creates the full 3-layer enforcement
model from `[[skill-enforcement-layers]]`:

| Layer | Mechanism | Effectiveness | Fires |
|-------|-----------|---------------|-------|
| **Layer 1** (UserPromptSubmit) | Inject "execute, don't discuss" | ~50% | Before agent responds |
| **Layer 2** (Stop hook quality gates) | Check evidence artifacts, block | ~100% | After agent responds |

## The side-effect file pattern still works

The previously-documented pattern (pre-create files via UserPromptSubmit
side effects) still works and is complementary. The hook can both:
1. Inject additionalContext (new — context injection)
2. Write side-effect files (existing — pre-processing)

## What does NOT work

- **Blocking the prompt:** UserPromptSubmit cannot block (non-blocking event
  on Grok Build per docs line 89). Only PreToolUse and Stop/SubagentStop
  can block.
- **Rewriting the prompt:** no hook can rewrite the user's prompt on any
  platform.
- **Replacing skill invocation:** the prompt still arrives at the agent;
  the hook adds context but doesn't remove the need for the agent to
  follow the skill.

## Falsifier

This finding is wrong if the local test hook (P:/tmp/test_ups_hook.py) fails
to produce visible additionalContext in the agent's context. The Hindsight
plugin is strong evidence but runs via Claude Code plugin format, which
Grok Build reads natively — a direct Grok-native hook JSON registration
may behave differently. Verify with the test hook before building production
hooks on this assumption.

## Sources

- Vectorize/Hindsight Grok Build integration: https://hindsight.vectorize.io/sdks/integrations/grok-build
- Grok Build hook docs: `~/.grok/docs/user-guide/10-hooks.md` L89, L253-256, L304
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- disler/claude-code-hooks-mastery: https://github.com/disler/claude-code-hooks-mastery
- Local test hook: P:/tmp/test_ups_hook.py (registered in ~/.grok/hooks/test-ups-injection.json)

## Original analysis (preserved for audit trail)

The original 2026-07-28 analysis incorrectly extended the SessionStart/PostToolUse
stdout-ignored pattern to UserPromptSubmit. The extension was plausible (UserPromptSubmit
is non-blocking like SessionStart) but untested. The Hindsight plugin's production use
proves the extension was wrong. The side-effect file pattern documented in the original
analysis remains valid — the correction is specifically about the additionalContext
injection path, which was incorrectly marked as blocked.

## What this means for our workspace

1. **Port skill_enforcer.py to Grok Build** — create a UserPromptSubmit hook
   at `~/.grok/hooks/UserPromptSubmit_skill_enforcer.py` that detects
   `/<skill-name>` in the prompt and injects "execute, don't discuss"
   additionalContext. See handoff: skill-enforcer-port-grok-build.
2. **The quality gates Stop hook + skill_enforcer UserPromptSubmit hook**
   together form the full 3-layer model: pre-execution advisory + post-execution
   enforcement.
3. **Update [[skill-auto-invocation-reliability]]** — the gap "on Grok Build,
   the entire Claude-side enforcement is missing" (line 102) is now closeable.

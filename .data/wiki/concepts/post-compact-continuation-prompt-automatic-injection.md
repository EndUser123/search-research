---
title: "Post-compact continuation prompt: automatic injection via 4-hook pipeline"
created: 2026-08-08
source: session-2026-08-08
tags: [hook-system, compaction, context-recovery, continuation-prompt, multi-terminal-isolation, stale-immunity, architecture, decision]
host: grok
agent: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/compaction-inherited-diagnosis-unverified-propagation.md
    type: complements
  - target: wiki/concepts/context-compaction-and-resumption-continuity-in-agentic-codi.md
    type: implements
  - target: wiki/concepts/hook-block-observability-per-session-logging-escalation-path.md
    type: related
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: implements
summary: >
  A 4-hook pipeline (PreCompact capture → PostCompact arm → UserPromptSubmit inject
  → SessionEnd cleanup) automatically captures a continuation prompt before context
  compaction and re-injects it as additionalContext on the first post-compact prompt.
  Uses the two-hook arming pattern (PostCompact + UserPromptSubmit) rather than the
  single-hook SessionStart(compact) pattern, because UserPromptSubmit additionalContext
  is confirmed working on this host while SessionStart additionalContext remains
  contradicted by Grok Build docs. Multi-terminal isolated via per-session filename.
  Stale-immune via one-shot delete + mtime TTL + SessionEnd cleanup.
---

# Post-compact continuation prompt: automatic injection via 4-hook pipeline

## Decision context

When a session gets compacted, the agent loses context. The operator previously
had to manually compose a post-compact prompt to continue work — typically a
~400-word summary of open items, their status, and what to start with. For an
operator with ADHD running a fleet of AI coders, this manual meta-action is
exactly the cognitive load the system is designed to eliminate.

The goal: **store a continuation prompt during the session, inject it
post-compact automatically, then clear the storage to prevent staleness.**

This required resolving three design questions:
1. Which hook event supports context injection post-compact?
2. How is the continuation prompt captured before compaction?
3. How is stale data prevented in a multi-agent, multi-terminal fleet?

## The 4-hook pipeline

```
PreCompact  →  continuation-{sid}.md  (capture state)
                    ↓
PostCompact →  armed-{sid}.md         (rename: arm for injection)
                    ↓
UserPromptSubmit  →  additionalContext  (inject + delete: one-shot)
                    ↓
SessionEnd  →  cleanup orphans         (remove orphaned files)
```

### Hook 1: PreCompact capture (`PreCompact_continuation_capture.py`)

Fires before compaction. If the agent (or operator) has manually written a
continuation file to `~/.grok/hooks/state/continuation-{session_id}.md`, the
hook does NOT overwrite it — agent-authored content always takes priority.
If no file exists, the hook auto-generates one from session state (recent git
commits + open handoffs).

### Hook 2: PostCompact arm (`PostCompact_continuation_arm.py`)

Fires after compaction completes. Renames `continuation-{sid}.md` →
`armed-{sid}.md`. This arming step is necessary because PostCompact is
**observational-only** — it cannot inject context (confirmed by Claude Code
docs decision control table: "PostCompact → None — No decision control").

### Hook 3: UserPromptSubmit inject (`UserPromptSubmit_continuation_inject.py`)

Fires on every prompt. Checks for `armed-{sid}.md`. If found AND fresh
(mtime within 1 hour), injects its content as `additionalContext` via the
`hookSpecificOutput` pattern, then deletes the file (one-shot injection).
If stale (>1 hour), silently deletes without injecting.

**Why UserPromptSubmit is confirmed working on this host:** the existing
`UserPromptSubmit_quota_availability.py` hook uses the exact same
`hookSpecificOutput.additionalContext` pattern and has been in production
since 2026-07. This was the decisive evidence that resolved the architecture
choice — rather than betting on SessionStart(compact) which is contradicted
by Grok Build docs, we use a confirmed-working path.

### Hook 4: SessionEnd cleanup (`SessionEnd_continuation_cleanup.py`)

Fires when the session ends. Removes orphaned `continuation-{sid}.md` and
`armed-{sid}.md` files for the ending session. This handles the edge case
where a session ends without compaction (or the UserPromptSubmit hook didn't
fire after compaction).

## Why the two-hook arming pattern (not SessionStart(compact))

The /www research revealed that `SessionStart(compact)` is the canonical
post-compact injection point in Claude Code — multiple production
implementations use it (Dicklesworthstone/post_compact_reminder,
waitdeadai/no-amnesia, the Reddit "Pseudo-PostCompact Hook" thread).
Anthropic closed two feature requests (#46191, #50682) to add
`additionalContext` to PostCompact, confirming SessionStart(compact) as the
sanctioned mechanism.

**However:** the Grok Build docs at `~/.grok/docs/user-guide/10-hooks.md`
line 301 state: "For events like SessionStart or PostToolUse, stdout is
ignored." This **contradicts** the Claude Code docs, which say SessionStart
stdout IS added as context. This contradiction made SessionStart(compact)
an unverified injection path on Grok Build.

**Resolution:** rather than ship an unverified path, we use the PostCompact +
UserPromptSubmit two-hook pattern — both components are confirmed working on
this host. PostCompact is confirmed observational-only (matches both Claude
Code and Grok Build docs). UserPromptSubmit additionalContext is confirmed
working via the existing quota-availability-injector hook.

**Trade-off:** the two-hook pattern is slightly more complex (one extra hook,
one extra file rename) but uses only verified paths. The SessionStart(compact)
single-hook pattern is simpler but requires a live test to verify on Grok
Build — which we did not run because the UserPromptSubmit path was already
confirmed.

## Stale immunity

Three layers of stale prevention:

1. **One-shot delete:** UserPromptSubmit deletes the armed file immediately
   after injection. The continuation prompt is injected exactly once.
2. **mtime TTL (1 hour):** UserPromptSubmit ignores armed files older than 1
   hour. If the delete fails (file lock, permission denied), the stale file
   is silently removed on the next prompt without injection.
3. **SessionEnd cleanup:** removes orphaned files when the session ends.
   Handles the edge case where compaction fires but no post-compact prompt
   is sent.

## Multi-terminal isolation

Per-session filename: `continuation-{session_id}.md` and `armed-{session_id}.md`.
The session ID comes from the hook payload (`data.get("sessionId")`), which
Grok Build injects for every hook event. This is the same per-session file
pattern used by 6+ existing hook families (`hook-blocks-{sid}.jsonl`,
`mutation-receipts-{sid}.jsonl`, etc.).

Zero cross-session contamination: each session only reads and writes its own
files. The SessionEnd cleanup only deletes files matching the current session ID.

## The capture mechanism

The hardest design problem was not injection — it was capture. PreCompact
fires as a separate process and cannot run LLM inference to summarize the
session. Options considered:

| Trigger | What writes | Trade-off |
|---------|------------|-----------|
| Every Stop | Agent self-summarizes each turn | Latency overhead on every turn |
| PreCompact (hook) | Hook extracts from git/handoffs | Can't capture agent reasoning |
| Operator request | Manual trigger | Defeats automation purpose |
| Agent pre-write | Agent writes file when context is full | Requires agent cooperation |

**Chosen: hybrid (PreCompact auto-fallback + agent pre-write priority).** The
PreCompact hook auto-generates a fallback from recent commits and open
handoffs. If the agent has manually written a richer continuation file (e.g.,
"we were halfway through refactoring resolve_gates in the close skill"),
that content takes priority and the auto-generated fallback is not written.

This design lets the agent cooperate when it can (pre-writing a detailed
continuation) and still works when it doesn't (auto-fallback covers the basics).

## Receipts

- `~/.grok/hooks/scripts/PreCompact_continuation_capture.py` — capture hook
- `~/.grok/hooks/scripts/PostCompact_continuation_arm.py` — arm hook
- `~/.grok/hooks/scripts/UserPromptSubmit_continuation_inject.py` — inject hook
- `~/.grok/hooks/scripts/SessionEnd_continuation_cleanup.py` — cleanup hook
- `~/.grok/hooks/continuation-capture-precompact.json` — PreCompact registration
- `~/.grok/hooks/continuation-arm-postcompact.json` — PostCompact registration
- `~/.grok/hooks/continuation-inject-userprompt.json` — UserPromptSubmit registration
- `~/.grok/hooks/continuation-cleanup-sessionend.json` — SessionEnd registration
- `~/.grok/hooks/UserPromptSubmit_quota_availability.py` — existing hook proving additionalContext works on this host
- `~/.grok/AGENTS.md` § "Post-compact recovery" — static reorientation protocol
- Claude Code hooks reference: `https://code.claude.com/docs/en/hooks` — decision control table confirms PostCompact is observational-only, UserPromptSubmit supports additionalContext
- 8 integration tests pass: capture, no-overwrite, arm, inject, one-shot delete, no-op, stale deletion, session cleanup

## Falsifier

This pattern is wrong if:
- Grok Build adds SessionStart(compact) additionalContext support (then the
  two-hook arming pattern is unnecessary — simplify to one hook)
- The UserPromptSubmit injection path stops working on Grok Build (then the
  entire pipeline fails silently — need to verify after Grok Build updates)
- The continuation prompt content is consistently low-quality (auto-generated
  fallback is too thin to be useful) — then the agent pre-write path becomes
  mandatory, not optional
- Compaction frequency is so low (0-1 per session) that the hook complexity
  isn't justified — measure via session transcript compaction markers

## Auto-related

- [[compaction-inherited-diagnosis-unverified-propagation]] — compaction summaries carry unverified claims; this pipeline captures state BEFORE compaction, avoiding the summary's narrative bias
- [[context-compaction-and-resumption-continuity-in-agentic-codi]] — the "Resumption Gap" problem this pipeline solves
- [[multi-terminal-isolation-stale-data-immunity]] — the per-session file pattern
- [[hook-block-observability-per-session-logging-escalation-path]] — same per-session file pattern for a different observability purpose

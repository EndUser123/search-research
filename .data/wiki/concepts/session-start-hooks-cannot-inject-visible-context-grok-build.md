---
title: "SessionStart and UserPromptSubmit hooks cannot inject visible context on Grok Build"
created: 2026-07-29
source: session-2026-07-29
tags: [hooks, grok-build, session-start, passive-events, context-injection, agent-behavior]
summary: >
  SessionStart hooks on Grok Build are passive: stdout is ignored (docs
  line 304), stderr appears only as a hook annotation in the TUI scrollback
  (not surfaced to the operator), and there is no mechanism to inject
  visible context at session start. An AGENTS.md rule telling the LLM to
  surface hook output is unreliable (per [[llm-instruction-non-compliance-activation-gap-2026]]). The combination — passive hook + unreliable rule
  — means session-start data injection does not work with current Grok Build
  hook capabilities. This was verified empirically: a SessionStart hook was
  built, fired successfully (green ✓), but its output was invisible to the
  operator on resume.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build.md
    type: extends
  - target: wiki/concepts/grok-build-hook-exit-code-1-stderr-as-failure-signal.md
    type: related
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
  - target: wiki/concepts/narrative-as-signal.md
    type: related
---

# SessionStart and UserPromptSubmit hooks cannot inject visible context on Grok Build

## Decision context

**The problem:** the operator wanted harvest items, workspace gaps, and
email items surfaced at session start. The agent built a SessionStart hook
that ran harvest show + workspace_opportunity_scan + email scan-inbox and
printed results to stderr. The hook fired successfully (green ✓, 1463ms)
but the operator saw nothing — the output was invisible.

The agent then claimed an AGENTS.md rule would make the LLM surface the
hook output, despite the wiki documenting that AGENTS.md rules are
unreliable for this class of instruction. The operator corrected: "LLMs
are unreliable at following agents.md, that's what our wiki says."

## Key findings

### What actually happens with SessionStart hook output

1. The hook script runs and produces output to stderr
2. The TUI shows a green ✓ with timing — confirming it ran
3. The stderr output appears as a hook annotation in the scrollback
4. **The output is NOT injected as visible context the operator sees**
5. The output IS available to the LLM as part of the hook annotation
6. But the LLM does not reliably surface it without being told to
7. And AGENTS.md rules telling the LLM to surface it are themselves unreliable

### Why AGENTS.md rules don't fix this

Per [[llm-instruction-non-compliance-activation-gap-2026]]: AGENTS.md rules
fire probabilistically (~66% compliance). The wiki explicitly documents
this gap. Relying on a rule to surface hook output is relying on two
unreliable mechanisms chained together: hook output reaches LLM context
(probably) → LLM surfaces it (66% of the time).

### What would work

- A `type: "prompt"` hook (like Claude Code's feature request #37122) —
  not available on Grok Build
- A hook that writes to a file the LLM is forced to read (e.g., a
  system-reminder file) — no such mechanism exists
- A TUI dashboard panel that shows the data independently — not built
- The `active-surface.last.md` mechanism — but this is read by the LLM,
  not displayed to the operator directly

## What this means for our workspace

**Do not build SessionStart hooks expecting visible output.** SessionStart
hooks are passive — they can run scripts and write files, but cannot inject
context the operator will see. The only mechanisms for operator-visible
session-start data are:

1. The LLM choosing to surface it in its first response (unreliable)
2. A future Grok Build feature for `type: "prompt"` hooks (not available)
3. A TUI dashboard (not built)

Until one of these exists, session-start data injection should use the
file-write approach: the hook writes results to a known file, and skills
that read files at startup (like `/todo`) surface it. This is the pattern
`active_surface_snapshot.py` already uses — it writes to
`~/.grok/active-surface.last.md` and the LLM reads it.

## Falsifier

This finding is wrong if Grok Build adds `type: "prompt"` hooks or another
mechanism for SessionStart hooks to inject visible context. At that point,
the SessionStart hook pattern becomes viable and this finding should be
updated.

## Receipts

- `~/.grok/docs/user-guide/10-hooks.md:304` — "For events like SessionStart or PostToolUse, stdout is ignored."
- `~/.grok/docs/user-guide/10-hooks.md:416` — "their results appear as annotations in the TUI scrollback"
- Session 2026-07-29: SessionStart hook built, fired (green ✓), output invisible to operator
- [[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]] — UserPromptSubmit also cannot inject context
- [[llm-instruction-non-compliance-activation-gap-2026]] — AGENTS.md rules fire ~66%

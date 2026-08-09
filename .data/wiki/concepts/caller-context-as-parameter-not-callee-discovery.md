---
title: Caller context as parameter, not callee discovery
slug: caller-context-as-parameter-not-callee-discovery
created: 2026-08-09
verified: 2026-08-09
category: agent-architecture
host: both
tags: [anti-pattern, parameter-passing, over-engineering, agent-invoked-tools]
---

# Caller context as parameter, not callee discovery

## The pattern

When an LLM agent invokes a subprocess tool (CLI script, MCP tool, hook),
the agent's context often already contains data the subprocess needs
(session ID, current working directory, task scope, identity tokens). The
correct design is for the **agent to pass that data as an explicit
parameter**. The anti-pattern is to build **callee-side discovery
infrastructure** that makes the subprocess rediscover what the caller
already knew.

## One-line test

> Does the caller (the agent) already know this value in its context? If
> yes, pass it. Do not build a mechanism for the subprocess to discover it.

## Reference incident (2026-08-09)

The `/todo` scanner needed session-scoping — transcript scanners must read
only the current session's transcript. The session ID is known to the
agent (it appears in the session path in the agent's context) but is NOT
propagated to subprocesses via `GROK_SESSION_ID` on Grok Build.

**Wrong fix (built first):** a SessionStart hook that writes the session
ID to a terminal-scoped marker file (`P:/.artifacts/<terminal>/session.id`),
plus a reader in the scanner that reads the marker. This was 2 new files,
~90 lines, and introduced a **staleness hazard** — if the hook didn't fire
on the next session, the marker carried the old session ID forward,
causing exactly the cross-session contamination the fix was meant to
prevent.

**Correct fix:** the agent passes its session ID as a literal via
`--session <id>`. Zero new files. The agent's context is authoritative;
no discovery needed. The only infrastructure that stayed was the
filesystem-inference fallback (workspace-scoped, recency-gated) for the
case where the agent genuinely doesn't have the ID — a last resort, not
the primary path.

Net result of the correction: **−136 lines** (the hook was more code than
the fix it was trying to provide).

## Why the anti-pattern is attractive

1. **"Make it work without the caller cooperating"** feels more robust —
   but it's solving for a caller that doesn't exist. The caller here is an
   LLM agent that follows instructions; tell it to pass the parameter and
   it will.
2. **Discovery mechanisms are interesting to build.** Parameter passing is
   boring. The bias toward interesting work ([[minimal-fix-and-root-cause]]
   forbidden-phrases) pushes toward the hook.
3. **The env-var pattern is culturally ingrained.** Many CLI tools read
   env vars. But env vars assume a human-configured shell environment; an
   agent-invoked subprocess inherits whatever the runtime propagates, which
   on Grok Build does not include `GROK_SESSION_ID`.

## How to catch it before building

Before building any discovery/propagation mechanism, ask:

1. **Who is the caller?** If the caller is an LLM agent, it has context.
2. **Does the caller already have the value the callee needs?** Check the
   agent's context: session path, task description, referenced file paths,
   prior tool outputs.
3. **Can the caller pass it as a parameter?** If the tool has a flag/arg,
   yes. If not, add one — adding a parameter is cheaper than building
   discovery.
4. **What staleness risk does the discovery mechanism introduce?** A
   marker file, env var, or cached state can go stale. A literal
   parameter passed at invocation time cannot.

If the answer to #2 is "yes" and #3 is "yes," the discovery mechanism is
unnecessary. Build the parameter path; keep a minimal fallback for the
edge case where the caller genuinely lacks the data.

## Relationship to other patterns

- [[solution-unit-validation-before-build]]: the unit-test sub-check asks
  "is this a special case of a more general capability?" Here, the
  discovery mechanism is a special case of "the caller passes the value."
  The general case is simpler.
- [[minimal-fix-and-root-cause]]: "smallest viable" is wrong, but so is
  "most elaborate." The optimal fix is the one with lowest future cost
  and risk — a parameter has zero staleness risk; a marker file has
  nonzero staleness risk.
- [[multi-terminal-isolation-stale-data-immunity]]: the irony of this
  incident is that the fix for a stale-data bug introduced a new
  stale-data source. The marker file was a cache; caches invalidate.

## Falsifier

This concept is wrong if: passing the parameter from agent context proves
unreliable (the agent frequently doesn't have the value, or passes the
wrong one), AND the discovery mechanism proves more reliable in practice.
On Grok Build, the agent reliably has its session ID (it's in every
compaction segment path and continuation prompt), so the falsifier has
not fired.

---
title: "Pre-packed context + inlined protocol = resource burn"
created: 2026-08-07
tags: [anti-pattern, pre-packing, context-engineering, quota, dispatch, structural-fix]
host: both
agent: grok
verification: local-only
cognitive_load: 2
summary: >
  When a dispatcher pre-packs everything an agent needs into one file, then inlines a protocol
  designed for the free-tool case that says "USE TOOLS when target is a file → read it," the
  agent re-reads files already in its context. Each re-read burns the resource the pre-packer
  was trying to save. The fix is structural: replace (not override) the protocol section for
  the pre-packed dispatch path.
---

# Pre-packed context + inlined protocol = resource burn

## The pattern

A system has two components that don't know about each other:

1. **A pre-packer** — computes everything the agent needs (target, context bundle, full file source, diffs, transcript slices) into ONE file, explicitly to save the agent from making discovery tool calls.
2. **A protocol** — designed for the free-tool case (spawn_subagent, separate quota pool), instructing the agent to "use tools to read files when the target is a file path."

When the dispatcher inlines the protocol into the pre-packed context, the agent receives **contradictory instructions**: "everything you need is here" (from the pre-packer) vs. "USE TOOLS to read files" (from the protocol). Agents resolve this by following the more specific instruction — and "read the file" is more specific than "it's already here." Result: 30+ tool calls re-reading content already in context, each burning the resource (quota, tokens, latency) the pre-packer was built to save.

## Why it happens

The two components were designed for different dispatch contexts but composed without adaptation:

| Component | Designed for | Where it's correct |
|-----------|--------------|-------------------|
| Pre-packer | Paid/subscription CLI dispatch (agy, codex) — every tool call costs quota | CLI mode |
| Tool-encouraging protocol | Free spawn_subagent dispatch — tools are free and the "fresh lens" needs them | Spawn mode |

Inlining the protocol raw into the pre-packed context is the composition bug. The protocol was never adapted for the pre-packed case.

## The fix (structural, not behavioral)

Do **not** layer a "QUOTA CONSTRAINT" preamble on top of the contradiction — prose overrides have a ~50% compliance ceiling under session pressure. Instead, **remove the contradiction at the source**:

- For the pre-packed dispatch path, **replace** the tool-encouraging protocol section with a pre-packed-aware section ("everything is already here; do not re-read; make zero tool calls unless verifying content NOT in this file").
- Use **anchor-based replacement** (HTML comment markers in the protocol file), not regex on prose — regex breaks on realistic wording changes (measured 2026-08-07: 2/4 realistic edits broke the regex).

## Reference instance (2026-08-07)

`/tp` skill: `tp_dispatch.py` pre-packs 60KB of context for agy, then inlines `protocol.md` which says "USE TOOLS when: target is a file → read it." agy made **36 tool calls** re-reading files already in the context, burning Google subscription quota. Fixed by replacing the tool-access section with a CLI-specific "Context (pre-packed)" section when `--cli` mode is active. After fix: **0 tool calls** on the same 64KB context. Verified across 3 minimal tests + 1 stress test.

Commits: `5d2cfef` (initial structural fix), `58c73e6` (anchor-based replacement + terminal-scoped output + regression tests).

## Falsifier

Wrong if: pre-packed CLI agents reliably make near-zero tool calls without the section replacement (i.e., the contradiction doesn't actually cause re-reads — the pattern is theoretical). Test: dispatch the same context with and without the section replacement; compare tool-call counts. If both are near-zero, the pattern doesn't hold and the section replacement is unnecessary ceremony.

## Transferability

Applies to any skill that:
- Pre-computes context for an agent into a single file or bundle
- Then inlines instructions designed for a different dispatch context (one where tools are free or where the agent starts cold)
- Runs in an environment where the re-reads cost something (quota, tokens, latency)

Examples beyond `/tp`: `/review` cross-model dispatch, `/www` research bundles, `/risk` specialist dispatch, any `/packet`-style pre-packaging that then inlines tool-encouraging instructions. The structural fix is the same in each: adapt the protocol section to the dispatch context, don't inline it raw.

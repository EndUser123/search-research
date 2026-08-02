---
title: "Solution-first before root cause — the over-engineering failure mode"
created: 2026-08-02
source: session-019fba58
tags: [over-engineering, root-cause, solution-first, problem-first, agent-behavior, failure-mode]
summary: >
  When encountering "X doesn't happen," agents jump to "how do we build a system
  for X" before asking "is X already instructed but not followed?" The simplest
  explanation — a missing instruction — is systematically skipped in favor of
  designing enforcement infrastructure.
agent: grok
host: grok
cognitive_load: 2
verification: observed
---

# Solution-first before root cause — the over-engineering failure mode

## The failure mode

When encountering "X doesn't happen," the agent jumps to "how do we build a system for X" before asking "is X already instructed but not followed?" The simplest explanation — a missing instruction — is systematically skipped in favor of designing enforcement infrastructure.

## The investigation order that should happen

1. **Is it instructed?** Check AGENTS.md, the relevant SKILL.md, the consuming-side docs. Grep for the behavior.
2. **Is it mechanically possible?** Do the tools, fields, scripts, commands exist?
3. **Is it mechanically enforced?** Does a hook fire, does a validator block?

If step 1 is "no" — the missing instruction might itself be the root cause. Adding the instruction is the fix. Steps 2 and 3 are only needed when the instruction exists but isn't followed.

## Worked examples from session 019fba58

**Handoff lifecycle visibility:** the operator asked "how do we make handoff work visible?" The agent designed three layers of infrastructure (claim commands, progress tracking, hooks, TTL, validators) before checking whether anyone had ever told agents to update handoffs when working from them. No one had. The instruction didn't exist. The fix was one line in AGENTS.md — not a monitoring system.

**Ruff on .md files:** the agent ran `ruff check` on `.md` files repeatedly. The `/go` SKILL.md already said "never lint non-Python files." The instruction existed and was specific. The failure was not following an existing instruction, not a missing mechanism.

These are different failure classes: the handoff case was a missing instruction (step 1 = no); the ruff case was an unenforced instruction (step 1 = yes, step 3 = no). The investigation order distinguishes them.

## Why the agent does this

RLHF rewarded solution-first thinking — designing systems looks more impressive than adding a missing line. The pattern-match "make X visible" → "build a system for X" fires before "check if X is already instructed." The operator's natural first move is "isn't this just a missing rule?" — Occam's razor applied to problems. The agent's natural first move is "how do we architect this?" — solution bias.

## What catches it

The operator's correction catches it in-session. For cross-session reliability, the `/tp` and `/why` Step 0.5 wiki queries surface this concept before critiques and root cause analyses. When the wiki says "did you check whether the simplest explanation is a missing instruction?" the agent has a structural reminder at the moment it matters — before proposing architecture.

## Related

- [[asserting-runtime-behavior-from-memory-not-testing]] — same pattern: asserting from memory instead of checking
- [[minimal-fix-and-root-cause]] — the "optimal long-term" principle that should prevent over-engineering but doesn't always fire
- [[mechanical-enforcement-over-behavioral-reminder]] — why rules alone don't work
- [[replacement-before-investigation-pattern]] — same class: jumping to replacement before checking if the current thing works

## What this means for our workspace

Before designing any enforcement system, check whether the behavior is already instructed. Three-step investigation order: (1) Is it instructed? Check AGENTS.md, SKILL.md. (2) Is it mechanically possible? (3) Is it mechanically enforced? If step 1 is "no," the missing instruction is the root cause — not a missing mechanism.

## Receipts

- Session 019fba58 handoff lifecycle work: designed claim commands, hooks, TTL, validators before checking if agents were ever told to update handoffs (they weren't — the instruction was missing). Receipt: `~/.grok/AGENTS.md` "Cross-agent coordination" section — rule was added after the root cause was identified.
- Session 019fba58 ruff on .md files: the `/go` SKILL.md already said "never lint non-Python files" (line 897: "ruff on changed `.py` files only — never lint non-Python files"). Receipt: `~/.grok/skills/go/SKILL.md` line 897.

## Falsifier

This concept is wrong if agents who read it still consistently skip the "is it instructed?" step. If after 10 sessions where this concept is queried by /tp and /why, agents still jump to architecture without checking instructions first, the wiki-query approach is insufficient and a structural enforcement (hook, protocol gate) is needed.

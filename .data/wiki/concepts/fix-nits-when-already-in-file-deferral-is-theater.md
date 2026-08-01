---
title: "Fix nits when already in the file — deferral is theater"
created: 2026-07-30
tags: [behavioral-pattern, refactoring, workflow-discipline]
summary: "When you're already editing a file, fixing a known nit in the same pass is zero-cost. Deferring it to a 'future cleanup' is deferral theater — it creates a commitment to return to the same file later, which may never happen."
host: both
agent: grok
sources:
  - session-2026-07-30 (/tp do? session review)
relations:
  - [[minimal-fix-and-root-cause]]
  - [[research-quality-principle-efficiency-not-censorship]]
---

## Decision context

During a /review + /refactor cycle on yt-is scripts, the agent identified 2 nit findings (VAL-001 comment renumbering, VAL-003 em-dash spacing) in files it was already editing. The agent deferred them as "cosmetic, fix later." The operator challenged: "why defer them?"

The agent's reasoning was weak: "doesn't affect behavior" is not a reason to leave known defects in files you're already committing. A "future cleanup pass" is a commitment to return to the same file — strictly worse than fixing in the current pass.

## The pattern

**Anti-pattern:** "This is a nit, I'll defer it to a future cleanup pass."
**Correct pattern:** "I'm already in this file. The fix is 1 line. Ship it now."

## Why deferral is theater

1. **Return cost is real.** Coming back to the same file later means re-reading context, re-establishing scope, and re-running verification. That cost is always higher than fixing it in the current pass.
2. **The commitment may never fire.** "Future cleanup" has no trigger, no deadline, no owner. It's a TODO comment that rots.
3. **It signals incomplete work.** Known defects left in committed code signal to future readers (and future agents) that quality is negotiable. This erodes the codebase over time.
4. **It wastes review cycles.** The next /review will find the same nit again, costing another specialist spawn + verify pass.

## When deferral IS correct

Deferral is correct when:
- The nit is in a **different file** you're not touching this turn (fixing it means opening a new file, new context, new verification)
- The nit requires a **design decision** you can't make in this pass (e.g., naming convention debate)
- The nit is **blocked by a structural change** that hasn't landed yet

In all three cases, the deferral should be tracked (harvest item, handoff, or TODO with a trigger condition) — not silently dropped.

## What this means for our workspace

- When /review or /check surfaces nits in files you're already editing, fix them in the same commit.
- "Pre-existing" nits in migrated files are fair game — you touched the file, you own the cleanup.
- The `/refactor` skill's S-risk-first ordering supports this: nits are S-risk (pure cosmetic), so they execute first, not last.

## Falsifier

This principle is wrong if: fixing nits in-pass introduces regressions (the cosmetic fix breaks something). This would mean the nit is not actually cosmetic — it touches load-bearing code. In that case, the fix should be deferred with an explicit reason and tracked.

If no regressions occur from in-pass nit fixes across 10+ instances, the principle holds.

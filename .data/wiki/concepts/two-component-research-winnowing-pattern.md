---
title: "Two-component research winnowing pattern"
created: 2026-07-30
tags: [research-methodology, applicability-checking, workspace-grounded]
summary: "Always do both: what the workspace needs (internal observation) AND what the internet thinks is best practice (external research). Then winnow — promote only findings that pass both components. Skipping either half wastes effort."
host: both
agent: grok
cognitive_load: 2
verification: session-2026-07-30
tier: 2
sources:
  - session-2026-07-30 (/why RCA on Vale promotion failure)
relations:
  - "[[research-applicability-checking-dont-cite-without-verifying-assumptions]]"
  - "[[research-quality-principle-efficiency-not-censorship]]"
  - "[[fix-nits-when-already-in-file-deferral-is-theater]]"
---

## Decision context

During the doc-check skill design, the operator asked "what else should we have in doc-check?" I responded with a full /www research cycle producing 23 findings across 4 categories, then recommended 6 including Vale (a prose linter). When asked "do you still think Vale adds value?" I immediately retracted — Vale solves a problem this workspace doesn't have.

The operator corrected: the research wasn't the waste. The waste was skipping the internal-observation half and the winnowing gate. The correct pattern is **always do both components, then winnow**.

## The pattern

```
Component A: Internal observation (what does THIS workspace need?)
  → grep wiki, handoffs, recent failures, operator complaints
  → identify the actual problems that exist here

Component B: External research (what does the industry say?)
  → web search, best practices, tools, patterns
  → may surface ideas you hadn't thought of

Winnowing gate:
  → For each finding: does it solve a problem from Component A?
  → Promote only findings that pass both: relevant to workspace AND valid externally
  → Findings that fail either half stay informational, not actionable
```

## Why both halves are necessary

- **Skipping Component A (internal):** you research solutions to problems you don't have. The research is high quality but irrelevant. This was the Vale failure — prose quality isn't a workspace problem.

- **Skipping Component B (external):** you miss ideas you haven't encountered. The operator explicitly noted: "You might have found good ideas that you hadn't thought of that should be included. You might have found ideas that would have made you suggest removing features." Internal-only observation has a blind spot.

- **Skipping the winnowing gate:** you promote findings to recommendations without checking applicability. Research findings have conditions; recommendations commit to action. The gate enforces the distinction.

## How it maps to /www

- **Phase 1a** (workspace observation) = Component A
- **Phase 2** (web research) = Component B
- **Round 3.25** (applicability gate) = Winnowing

The steps existed before this concept — the failure was enforcement. Phase 1a was not mechanically required, and Round 3.25 was a "check" not a "gate." The fix is making Phase 1a mandatory (≥3 observations before research) and Round 3.25 a gate (recommendations must pass both the applicability table and the workspace-observation check).

## What this means for our workspace

- When the operator asks an open question ("what else should we have?"), the FIRST response is workspace observation, not web research.
- External research is always valuable — but it feeds the winnowing gate, not the recommendation list directly.
- The winnowing gate is two-sided: a finding must align with workspace needs AND be externally valid. Neither half alone is sufficient.

## Falsifier

This pattern is wrong if: the workspace observation half consistently produces no useful signal (the workspace doesn't have enough history to observe from), or the external research half consistently produces only irrelevant findings (the industry has nothing to teach). If either half is consistently empty, it's not pulling its weight and the pattern should collapse to the half that works.

## What this means for our workspace

The /www skill Phase 1a and Round 3.25 enforce this pattern structurally. Any skill that produces recommendations from research should apply the same two-component winnowing.

## Receipts

- **Phase 1a hardening**: `~/.grok/skills/www/SKILL.md` Phase 1 section — "Workspace observation (MANDATORY before any web search)"
- **Round 3.25 gate**: `~/.grok/skills/www/SKILL.md` Round 3.25 section — "Research applicability GATE" with mandatory applicability table per recommendation
- **Failure case that motivated this**: session 019fb189, Vale prose-linter recommendation — research was correct but skipped Phase 1a (no workspace observation) and Round 3.25 (no applicability gate)

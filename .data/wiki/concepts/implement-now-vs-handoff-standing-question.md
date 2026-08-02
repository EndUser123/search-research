---
title: "Implement-now-vs-handoff: mandatory disposition for every finding"
created: 2026-08-01
source: dream-2026-08-01
tags: [standing-question, disposition, DO_NOW, NEW_HANDOFF, finding-routing, tp, skill-design]
host: grok
agent: grok
verification: multi-source-verified
cognitive_load: 1
relations:
  - target: wiki/concepts/completeness-over-curation-recommendation-discipline.md
    type: complements
  - target: wiki/concepts/closure-pressure-narrative-sufficiency-is-not-verification.md
    type: related
  - target: wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md
    type: related
summary: >
  Finding-producing skills surface findings but do not always assign a
  disposition (DO_NOW vs NEW_HANDOFF). This causes findings to be silently
  dropped. The fix: a mandatory standing question that forces explicit
  disposition on every finding with positive ROI.
---

# Implement-now-vs-handoff: mandatory disposition for every finding

## Decision context

**Why this pattern was needed:** sessions consistently produced findings (friction, opportunities, obligations) that were surfaced in /tp session output but never assigned a next action. The operator had to re-derive what to do with each finding, or worse, findings evaporated entirely. Two sessions independently demonstrated the same failure: findings produced, no disposition assigned, value lost.

## The pattern

Add a mandatory standing question to every finding-producing skill:

> "From what we learned this session, what should we do better, and can we implement it now or do we need a handoff for it?"

For each finding with positive ROI, assign one disposition:
- **DO_NOW** — mechanical, <60 min, no design decisions
- **NEW_HANDOFF** — architectural, >60 min, or needs fresh lens
- **EXISTING_WORKSTREAM** — already captured (verify handoff status first)
- **NOTED** — no action needed (goes to the NOTED table, not actionable list)

## Why it works

The question bridges two gaps that NOW/NEXT/LATER alone does not cover:

1. NOW/NEXT/LATER is a time horizon, not an action disposition. A NOW finding can be DO_NOW (fix it now) or NEW_HANDOFF (write a handoff now for next session). The disposition tells you WHAT to do, not WHEN.

2. Without explicit disposition, the agent can surface 10 findings and the operator has to mentally triage each one. With disposition, the operator sees the actionable list (DO_NOW items) separate from handoffs (NEW_HANDOFF items).

## What this means for our workspace

1. **/tp SKILL.md already has this** (added 2026-08-01, line 382). It fires in CROSS-DOMAIN NOTICES and applies to ALL finding types.

2. **Other finding-producing skills should adopt it:** /aar, /friction, /capture, /harvest. Each should have the standing question in their post-output routing section.

3. **The actionable recommendations list format** (numbered items with TYPE + Disposition + Effort + Confidence + "0 - Proceed") is the output contract that makes dispositions scannable and executable.

## Falsifier

This pattern is wrong if:
- The standing question produces noise (findings get DO_NOW disposition but the operator never approves them) — would indicate the disposition criteria are too loose
- NOW/NEXT/LATER already provides sufficient disposition signal and the additional DO_NOW/NEW_HANDOFF axis adds no value
- The operator prefers to assign dispositions manually rather than have the skill do it automatically

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| Standing question produces high-quality output | Session 019fb933 /tp: 8 findings with explicit dispositions, operator approved all via "0" | [OBSERVED] |
| Prior session demonstrated the failure | Session 019f8b39: operator had to re-state each recommendation (commit history, /tp SKILL.md line 530) | [OBSERVED] |
| Question added to /tp SKILL.md | Commit `28bf9d0` — standing implement-now-vs-handoff question | [OBSERVED] |

## Cross-references

- [[completeness-over-curation-recommendation-discipline]] — show all recommendations (complementary)
- [[closure-pressure-narrative-sufficiency-is-not-verification]] — premature closure pattern
- [[asserting-runtime-behavior-from-memory-not-testing]] — verify before asserting

## Auto-related

- [[llm-handoff-best-practices]]
- [[skill-graph]]
- [[optimal-cross-session-chain-traversal-aar-handoff-grok]]
- [[skill-techniques-index]]
- [[handoff-fragmentation-under-recurrence]]


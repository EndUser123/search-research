---
title: "Discover-first prompt patterns for unbiased work-item discovery"
created: 2026-08-13
source: packages/.chat_exports/2026-08-10_-_Research_Evaluation_and_Feedback
tags: [prompt-engineering, bias-checking, discovery, todo, triage, insight, work-item-categories, continuous-improvement, anti-tunnel-vision]
agent: grok
host: both
cognitive_load: 3
verification: workspace_verified
summary: >
  When using LLMs to find work items (blockers, errors, inefficiencies,
  opportunities, risks), hard-coding categories causes category tunnel
  vision — the model force-fits findings into the provided buckets and
  overlooks items that don't match. The fix: a two-phase prompt pattern
  (freeform discovery first, categorize second, meta-review third) with
  built-in bias-checking triggers. 5 reusable templates operationalize
  this as prompt patterns the /todo and /insight skills consume.
relations:
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: source
  - target: wiki/concepts/exploration-vs-execution-intent-signals.md
    type: related
  - target: wiki/concepts/scanner-to-handoff-gap-discovered-work-not-persisted.md
    type: related
  - target: wiki/concepts/work-discovery-skill-organization-best-practices.md
    type: complements
---

# Discover-first prompt patterns for unbiased work-item discovery

## Decision context

**Why this matters:** the operator asked "when I ask an LLM to find things, what
categories should I tell it to look for? I'm concerned that giving categories
may cause things to be overlooked — is that a real concern?" The answer: **yes,
it's a real concern.** Over-specification reduces LLM generalization and causes
force-fitting into provided buckets. The fix is a prompt pattern, not a
different category set.

This research directly informed the design of `/todo` (mechanical scanner),
`/insight` (transcript-depth scanner with bias-aware categories), and the
`/todo` Step 0.5 parallel-subagent integration.

## The two-phase discovery pattern

1. **Phase 1 — unconstrained discovery.** "List every noteworthy observation
   without categorizing. Include borderline/speculative items, marked clearly."
2. **Phase 2 — categorize.** "For each finding, assign zero or more labels from:
   `blocker`, `error`, `inefficiency`, `risk`, `opportunity`, `unknown`, `other`.
   Do not drop any finding just because it doesn't match a label."
3. **Phase 3 — meta-review.** "What might have been missed because it didn't
   clearly match any category? List separately."

The meta-review is the anti-tunnel-vision gate. Without it, categories become a
filter; with it, categories become metadata on top of a maximally open search.

## The 6 categories (aligned to Lean/Six Sigma/CMMI)

| Category | Industry mapping | What it detects |
|----------|-----------------|-----------------|
| **Blocker** | TOC constraint, CMMI Managing | Stops or slows progress |
| **Error** | Six Sigma defect, Lean waste | Incorrect behavior, bug |
| **Inefficiency** | Lean TIMWOOD waste | Redundant steps, rework, waiting |
| **Risk** | Risk management, incident | Could plausibly fail later |
| **Opportunity** | Kaizen, improvement funnel | Value/speed/reliability could increase |
| **Unknown** | — | Cannot be confident due to missing info |

These map to Lean TIMWOOD (Defects, Overproduction, Waiting, Non-utilized talent,
Transportation, Inventory, Motion, Over-processing), Six Sigma 6M fishbone
(Method, Machine, Material, People, Measurement, Environment), and CMMI practice
areas (Doing, Managing, Enabling, Improving).

## The 5 reusable prompt templates with bias-checking

### Template 1: Discover-First + Evidence Anchors
- **Goal:** open discovery with speculation flags
- **Bias trigger:** `speculation: true` flags findings inferred beyond evidence
- **Output:** JSON array with `{observation, evidence, speculation, notes}`

### Template 2: Discover → Categorize + Contradiction Scan
- **Goal:** discover, tag, then hunt for counter-evidence per finding
- **Bias trigger:** `contradiction: true` flags findings with opposing evidence
- **Output:** JSON with `{finding, labels, supporting_evidence, contradiction, contradicting_evidence}`

### Template 3: Dual-Goal Hypothesis Analysis (Support + Refute)
- **Goal:** force both supporting AND challenging evidence before concluding
- **Bias trigger:** presence/richness of `challenging_evidence` indicates
  whether the model escaped confirmation bias
- **Output:** JSON with `{hypothesis, supporting_evidence[], challenging_evidence[], confidence}`

### Template 4: Multi-Perspective Discovery + Reviewer Pass
- **Goal:** discover from 4 perspectives, then reviewer checks for over-focus
- **Bias trigger:** `bias_review` block surfaces over-represented vs
  under-represented perspectives
- **Output:** JSON with `{findings[], bias_review{overrepresented, underrepresented, possible_missing_findings}}`

### Template 5: Self-Evaluation Checklist + Rewrite Loop
- **Goal:** verification checklist with mandatory self-correction
- **Bias trigger:** `revisions` count — did the model self-correct?
- **Output:** JSON with `{analysis, checklist{traceable_claims, ambiguity_marked, support_and_challenge, no_unstated_assumptions}, revisions}`

## How these map to the workspace's skills

| Skill | Template(s) used | How |
|-------|-----------------|-----|
| `/todo` Step 0 (mechanical scanner) | — | Pure regex extraction (Layer 1) |
| `/todo` Step 0.5 (`/insight` subagent) | Template 1 + 2 | Discover-first on transcript, categorize, contradiction scan |
| `/todo` Step 0.5 (`/aar` subagent) | Template 3 + 4 | Dual-goal analysis, multi-perspective review |
| `/todo` Step 1d (Layer 3 critic) | Template 5 | Fresh subagent audits drops for misclassification |
| `/triage` | Template 2 + 3 | Categorize + contradiction + dual-goal on session output |

## Falsifier

This is wrong if:
- The discover-first pattern consistently finds the same items the mechanical
  scanner already finds (redundant with scanner)
- The bias-checking triggers (speculation, contradiction, perspective balance)
  never fire in practice (over-confident models skip them)
- The categories are too broad to be useful for routing or too narrow to capture
  novel findings (the Goldilocks problem)

## Sources

- `packages/.chat_exports/2026-08-10_-_Research_Evaluation_and_Feedback/attachments/when looking at things to do, we have blockers, er.md` — the full Perplexity conversation
- Lean/Six Sigma/CMMI category taxonomies (industry standard)
- Confirmation bias reduction: arXiv:2604.02485 (dual-goal prompting), arXiv:2302.11382 (prompt pattern catalogs)
- Session 019ffc5c: the `/todo` Step 0.5 parallel subagent integration was built from this research

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-graph]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[reddit-prompt-engineering-community-discourse]]
- [[claude-code-external-tool-integration-via-mcp]]


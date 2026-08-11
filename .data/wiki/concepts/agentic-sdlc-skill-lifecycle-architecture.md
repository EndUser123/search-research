---
title: "Agentic SDLC: Our Skill Lifecycle Architecture vs Industry Standard"
created: 2026-07-23
source: session-2026-07-23 (/www research on skill domain classification)
tags: [agentic-sdlc, harness-engineering, skill-architecture, lifecycle, consolidation, industry-comparison]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf (Anthropic, 2026 — names the domain "Agentic SDLC")
  - https://www.augmentcode.com/guides/agentic-sdlc (Augment Code — 3-stage maturity model)
  - https://github.com/addyosmani/agent-skills (80k stars, 24 skills, 6-phase pipeline DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP)
  - https://www.sonarsource.com/resources/library/what-is-agentic-sdlc/ (SonarSource — Carnegie Mellon data: +30% warnings, +41% complexity from agents)
  - https://www.port.io/blog/agentic-sdlc-software-lifecycle-rebuilt-around-agents (Port.io — governance requirements)
  - https://www.coderabbit.ai/guides/agentic-sdlc (CoderRabbit — where agentic SDLC creates new problems)
  - https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents (HumanLayer — "too many tools is bad")
  - https://blog.devgenius.io/saas-bootstrapping-in-2026-building-your-harness-93e361099a36 (devgenius — "too many skills blur agent attention")
  - https://addozhang.medium.com/agent-skills-deep-dive-building-a-reusable-skills-ecosystem-for-ai-agents-ccb1507b2c0f (granularity balance)
  - https://www.linkedin.com/posts/km2011_everyones-building-specialized-agents-right-activity-7482871054441459712 (skills scale more efficiently than agents because composable)
  - https://tw93.fun/en/2026-03-21/agent.html (skills keep system prompt as index; full knowledge on-demand)
relations:
  - target: wiki/concepts/spec-driven-development-harness-engineering-ecosystem
    type: refines
  - target: wiki/concepts/skill-design-patterns-reference-overlay-search-intelligence
    type: related
  - target: wiki/concepts/check-vs-review-complementary-not-redundant
    type: related
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents
    type: related
  - target: wiki/concepts/skill-authoring-patterns-dos-and-donts
    type: related
---

# Agentic SDLC: Our Skill Lifecycle Architecture vs Industry Standard

## Decision context

**Why this research was needed:** the operator asked what domain the skill
collection (/check, /review, /refactor, /plan, /design, /go, and supporting
skills) fits into, how it compares to what others do, and whether anything
should change. The skills were built incrementally without an explicit
domain framing; the question was whether the implicit architecture is
validated by industry practice or diverges in problematic ways.

**What the research changed:** confirmed the domain is "Agentic SDLC"
(Anthropic's 2026 term), identified addyosmani/agent-skills (80k stars) as
the direct industry analog, validated our router (/go) and verification
granularity as ahead-of-standard, and flagged skill proliferation as the
primary risk.

## The domain: Agentic SDLC

The recognized industry term is **Agentic SDLC** — the software development
lifecycle reorganized around autonomous agent execution between defined
review checkpoints. Named by Anthropic's 2026 Agentic Coding Trends Report
and adopted by Augment, SonarSource, CoderRabbit, and Port.io.

The broader engineering discipline is **harness engineering** — all
infrastructure around the model (context, tools, recovery, verification,
governance). Our AGENTS.md, CLAUDE.md, skills, hooks, rules, state files,
wiki, and worktree conventions collectively ARE our harness.

## Industry-standard lifecycle (addyosmani/agent-skills, 80k stars)

The closest industry analog organizes 24 skills into 6 explicit phases:

```
DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
```

## Our lifecycle mapping

```
/design → /plan → /go → /check → /review → /close-py
  (spec)  (plan) (exec) (verify) (review) (ship)
```

Supporting infrastructure: /preflight, /grok-discovery, /grok-route,
/grok-safe-git, /www, /web, /wiki, /agy, /codex, /mmx, /handoff, /tasks,
/aar, /debrief, /tp, /risk, /refactor, /grok-verify.

## Three areas of divergence

### 1. Router: ahead of standard

Our /go auto-profiles tasks and delegates to specialized sub-procedures.
No major skill pack has an equivalent auto-router. Tradeoff: complex
routing table (10 profiles × 6 horsepower packs) creates human learning
curve.

### 2. Verification granularity: more layers than anyone

| Concern | Industry | Ours |
|---------|----------|------|
| Session verify | /verify or none | /check (transcript-grounded) |
| Code review | /review | /review (multi-lens, specialist fan-out) |
| Structure | none | /refactor (seam-based, P0-P3) |
| Inline gate | bash checklist | grok-verify (6-step) |
| Premise challenge | /risk | /tp + /review --adversarial + /risk |
| Retrospective | none | /aar + /debrief |

Validated by Carnegie Mellon data (807 projects): agents cause +30% code
warnings, +41% complexity. Our multi-layer verification is a principled
response. Risk: 6 overlapping skills create cognitive load.

### 3. Knowledge persistence: ahead (Stage 2→3)

Augment's maturity model places us at Stage 2 (Team-Scale Orchestration)
with Stage 3 patterns (org-scale knowledge via wiki + handoffs) compressed
for solo operation.

## Should we change anything?

**Do now (zero risk):**
- Remove dead aliases (check-work, code-review, grok-go, grok-sdlc)
- Deduplicate verification-before-completion (identical files in 2 locations)
- Name the domain explicitly in AGENTS.md (implicit → explicit)

**Consider (low risk, high value):**
- /design Step 5.5 should delegate to /tp instead of duplicating (SKILL.md already says so)

**Hold (the granularity is the advantage):**
- Don't merge /check + /review + /refactor — they answer different questions
- Don't merge /aar + /debrief — different depth/scope
- The verification hierarchy is validated by the +30%/+41% complexity data

## Skill proliferation data point

addyosmani (industry standard): 24 skills, 6 phases, 80k stars.
Our user-scope: 32 skills. The count is comparable; the organization is
less explicit (no phase labels in the catalog).

Industry consensus: "too many skills blur the agent's attention" but
"skills scale more efficiently than agents because composable." The
resolution: specialization is good when skills are composable and
auto-routed (our /go pattern); bad when the human must memorize which
skill for which phase.

## Falsifier

This analysis is wrong if:
- The Agentic SDLC term is superseded within 12 months (check industry sources)
- addyosmani/agent-skills adds an auto-router, eliminating our differentiator
- Carnegie Mellon's +30%/+41% finding is retracted or contradicted by larger studies
- Our verification granularity proves to create more confusion than it catches bugs (measurable: track misrouting incidents)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

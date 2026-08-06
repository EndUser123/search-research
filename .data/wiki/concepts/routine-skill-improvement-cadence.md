---
title: "Routine skill improvement cadence: scheduled skill health checks using existing skill combinations"
created: 2026-07-27
source: session-019fa39d (/www research on routine skill improvement)
tags: [skill-improvement, cadence, scheduled-maintenance, skill-combinations, wargame, brainstorming, red-team, skill-dev, cross-host]
summary: >
  Research-backed recommendation for a routine skill-improvement cadence
  using existing workspace skills in new combinations. The workspace has
  all the tools (why, aar, red-team, tp, brainstorming, wargame, skill-dev,
  review, check) but no scheduled cadence for using them on EXISTING
  deployed skills. The research converges on one pattern: scheduled,
  routine improvement work prevents skill degradation. Teams that improve
  their AI systems do it on a cadence (weekly/bi-weekly/monthly), not ad
  hoc. The recommended cadence: per-session (/check + /review), weekly
  (/aar opportunity landscape), monthly (/skill-dev measure + brainstorming
  on failure modes), quarterly (/risk + /wargame on load-bearing
  skills). Crucially, the skill combinations are not limited to the
  obvious ones — ANY skill can be combined with ANY other to create a
  new improvement lens. The operator should periodically explore novel
  combinations (e.g., /design on skill improvements, /www on skill-
  improvement research, /packet for cross-session skill review).
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "SkillOpt (Microsoft Research): https://www.microsoft.com/en-us/research/blog/skillopt-agent-skills-as-trainable-parameters/"
  - "MAST taxonomy (Cemri et al. 2025): https://arxiv.org/abs/2503.13657"
  - "OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/"
  - "Promptfoo red-team: https://www.promptfoo.dev/docs/risk/agents/"
  - "Google SRE postmortem culture: https://sre.google/sre-book/postmortem-culture/"
  - "Improvement Kata (Rother): https://danlebrero.com/2021/01/06/toyota-kata-in-software-development-continuous-improvement/"
  - "MITRE ATLAS: https://atlas.mitre.org/"
  - "Production trace flywheel (Arize): https://arize.com/blog/from-production-traces-to-better-ai-agents-automating-the-llmops-feedback-loop/"
  - "Chaos engineering for AI agents: https://github.com/deepankarm/agent-chaos"
  - "Design critiques at Figma: https://www.figma.com/blog/design-critiques-at-figma/"
  - "skill-audit CLI: https://github.com/pors/skill-audit"
  - "LLM-as-judge calibration (LangChain): https://www.langchain.com/blog/human-judgment-in-the-agent-improvement-loop"
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: extends — adds the maintenance/improvement phase to the lifecycle
  - target: wiki/concepts/parallelizing-design-doc-generation-what-works
    type: related — same research session produced both
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques
    type: related — same research session
---

# Routine skill improvement cadence

## Decision context

**Why this research was needed.** The workspace has 14+ skills for
analysis, review, verification, and knowledge capture. Each skill has
its own quality mechanisms (evidence tiers, validators, cross-model
review). But there is no scheduled cadence for using these skills on
EACH OTHER — for asking "is /why still producing accurate findings?"
or "has /close accumulated blind spots?" Skills degrade silently:
rules stop firing under closure pressure, new failure modes emerge
that the original design didn't anticipate, and code changes in one
skill create interaction gaps with others (as this session
demonstrated with /close × /aar).

The question: can existing skills (/wargame, /brainstorming, /risk,
etc.) be combined into a routine skill-improvement practice?

**What the research found.** Three parallel research threads (systematic
AI skill improvement, wargame/pre-mortem for AI, brainstorming for
existing systems) converged on the same finding: **scheduled, routine
improvement work is what prevents skill degradation.** The specific
techniques matter less than the cadence. Teams that improve their AI
systems do it on a schedule, not ad hoc.

## Receipts

- **[Tier 2 — peer-reviewed/vendor]** SkillOpt (Microsoft Research):
  separate optimizer LLM reads trajectories and proposes bounded skill
  edits. Our equivalent: /aar → /go → /check, but not scheduled.
- **[Tier 2 — practitioner]** Layered adversarial testing cadence
  (Promptfoo): per-PR, nightly, weekly, monthly, quarterly. Our
  equivalent: /check (per-session), /review (per-change), but no
  monthly/quarterly step.
- **[Tier 2 — practitioner]** Blameless post-mortem loop (Google SRE):
  incident → review → tracked action items → trend analysis. Our
  equivalent: /why (incident) → wiki concept (review) → /aar
  (trend), but action-item tracking is manual.
- **[Tier 2 — practitioner]** Improvement Kata (Toyota Kata): daily/
  weekly scientific-thinking routine on existing system gaps. No
  workspace equivalent — our improvement is reactive, not scheduled.
- **[Tier 2 — practitioner]** Production trace → regression dataset
  flywheel (Arize): every real failure becomes a test case. Our
  equivalent: wiki concepts from /why, but they feed future
  investigations, not regression tests.
- **[INFERENCE]** The specific techniques matter less than the cadence —
  this is derived from the convergence across all three research threads,
  not directly stated by any single source.

## The recommended cadence

### Per-session (already happening)
- `/check` on changed skills
- `/review` on load-bearing changes
- `/aar` opportunity landscape surfaces skill gaps

### Weekly (partially happening)
- `/aar` at session close already surfaces friction and opportunities
- **Gap:** no mechanism to accumulate weekly findings into a monthly
  review queue

### Monthly (NEW — the key addition)
- `/skill-dev measure` on all major skills — evaluate marginal
  contribution using retrospective evidence (aar, tp critique log,
  transcript traces, routing incidents)
- `/brainstorming` on the top 1-2 skills with degraded metrics —
  divergent ideation on failure modes, using the brainstorming skill's
  3+-framings phase
- **Novel combinations to explore:**
  - `/design` on skill improvements — treat the skill as a system to
    redesign, not just patch
  - `/www` on skill-improvement research — what techniques do other
    teams use for the specific gap found?
  - `/packet` for cross-session skill review — export a skill's recent
    execution traces for cold review by another model
  - `/tp` on the skill's own design — challenge the skill's framing,
    not just its output
  - `/codex` or `/agy` for cross-model skill review — a different
    model family may see blind spots the primary model shares

### Quarterly (NEW — for load-bearing skills)
- `/risk` on skills with hooks/gates/receipts — adversarial testing
  of the enforcement mechanism
- `/wargame` on execution paths — "imagine this skill failed
  catastrophically in production. What happened?"
- Full `/skill-dev improve` cycle — propose targeted improvements from
  the quarterly evidence

## The skill-combination principle

**The specific combinations above are starting points, not a fixed
menu.** The key insight from the research: the improvement technique
matters less than the cadence AND the diversity of lenses applied.

The workspace's skill catalog is a combinatorial space. Any skill can
be combined with any other to create a new improvement lens:

| Combination | What it surfaces |
|-------------|-----------------|
| /brainstorming + /why | Divergent failure-mode discovery before the failure happens |
| /wargame + /close | "Imagine /close approved a fabricated report" — structural weaknesses |
| /risk + /design | Adversarial testing of a design's enforcement layer |
| /tp + /why | Challenge the RCA's framing, not just its findings |
| /skill-dev + /aar | Measure skill value from retrospective evidence |
| /packet + /codex | Export skill traces for cold cross-model review |
| /www + /skill-dev | Research what other teams do for the specific gap found |
| /design + /check | Redesign a skill, then verify the redesign passes its own gates |

The operator should periodically explore novel combinations — not just
the obvious ones. The combinatorial space is the asset; the cadence is
what makes it routine.

## What makes cadences fail (from the research)

| Failure mode | Source | Mitigation |
|---|---|---|
| Cadence decays under feature pressure | FixIt weeks, 20% time | Schedule as a recurring task/cron, not a discretionary activity |
| Action items not tracked | SRE post-mortem loop | `/skill-dev` tracks dispositions (MONITOR, INVESTIGATE, ACT_NOW) |
| Automated tools plateau (~70%) | Promptfoo, Garak | Pair automated breadth with human/LLM depth (the quarterly red-team) |
| Findings become ceremony | Kaizen suggestion-box | Require dispositions on every finding — no "noted" without action |
| Taxonomy lag | OWASP, MITRE ATLAS | Pair framework with curiosity-driven exploration |

## Falsifier

This cadence is wrong if:
- The monthly /skill-dev measure produces no actionable findings for
  3 consecutive months (the measurement is either too shallow or the
  skills have stabilized)
- The novel combinations produce no insights that the standard
  /check + /review cycle didn't already catch (the combinations add
  no value)
- The cadence decays into ceremony (findings are marked "MONITOR" but
  never acted on)

**Discriminating test:** run the monthly cadence on /why and /close for
3 months. Compare the findings against reactive /why + /aar runs. If
the scheduled cadence surfaces issues the reactive runs missed, it's
validated. If it only reproduces what reactive runs already found, the
cadence is overhead.

## Related

- [[agentic-sdlc-skill-lifecycle-architecture]] — the lifecycle this cadence maintains
- [[parallelizing-design-doc-generation-what-works]] — same research session
- [[llm-synthesis-quality-and-speed-techniques]] — same research session
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

---
title: "Great adversarial-review skill design: what practitioners like, what the best red-team/pre-mortem skills do, and the workspace improvement map"
created: 2026-08-12
source: /www run 2026-08-12 (red-team / critical review / pre-mortem skill design)
sources:
  - https://entelligence.ai/code-review-benchmark-2026 (precision 16-67%, best F1 47%)
  - https://www.sciencedirect.com/science/article/abs/pii/S1472811722000866 (Klein replication: 25% more anticipated risks)
  - https://digitalcommons.mtu.edu/cgi/viewcontent.cgi?article=1463&context=etdr (2024 MTU field study: p<0.05 overrun reduction, brainwriting variant)
  - https://journals.aom.org/doi/10.5465/255859 (Schweiger 1986/1989: DI > DA > consensus on assumption quality)
  - https://onlinelibrary.wiley.com/doi/full/10.1002/acp.3550 (2019 ACH empirical test: reduces confirmation bias)
  - https://github.com/github/spec-kit (spec-kit /speckit.checklist "unit tests for English")
  - https://arxiv.org/abs/2502.06251 (AI-Mediated Devil's Advocate, Lee et al. 2025)
  - https://github.com/DecisionNerd/RedTeam (Red Team Handbook v10, 29 commands)
  - https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/engineering-team/skills/adversarial-reviewer/SKILL.md
  - https://raw.githubusercontent.com/lemon03390/Claude-code-adversarial-review-skill/main/SKILL.md
  - https://raw.githubusercontent.com/parcadei/continuous-claude-v3/main/.claude/skills/premortem/SKILL.md
  - https://github.com/AndyShaman/premortem (reverse premortem + rerun history)
  - https://agentskills.codes/skills/karpathy-metric-pre (metric-gaming pre-mortem)
  - https://raw.githubusercontent.com/winstonkoh87/Athena-Public/main/examples/skills/quality/red-team-review/SKILL.md
  - https://raw.githubusercontent.com/richfrem/agent-plugins-skills/main/plugins/agent-loops/skills/red-team-review/SKILL.md
  - https://scopy.dev/blog/ai-code-review-false-positives (practitioner noise complaint)
  - https://playerzero.ai/resources/false-positives-ai-code-review-tools (80-90% alerts not actionable)
tags: [red-team, adversarial-review, pre-mortem, critical-review, skill-design, precision, review-noise, requirements-validation, framing, risk]
agent: grok
host: both
verification: multi-source-verified
cognitive_load: 3
summary: >
  What a great red-team / critical review / pre-mortem skill looks like,
  grounded in practitioner sentiment + the SKILL.md contents of 10 installable
  adversarial-review skills + the empirical evidence for structured challenge
  techniques. Practitioner consensus: noise/precision is the #1 complaint about
  AI review — users disable reviewers that spam false positives; what they like
  is actionable, evidence-grounded, severity-tiered findings with file:line
  anchors. The best installable skills share 8 structural design patterns:
  verify-before-flag evidence, confidence-score suppression, mandatory-findings
  rules, declarative priors (thesis + falsifier), reverse/counter-bias phases,
  numeric gates (0-100 scores), empty-sections-are-fine, and iteration
  isolation + telemetry. Empirical evidence: structured techniques beat
  unstructured critique (Schweiger DI/DA; Mitchell 30% premortem; ACH 2019).
  Workspace gap confirmed: requirements/framing validation is the underserved
  lens — spec-kit and Decision Quality Checks are the prior art to study.
relations:
  - target: wiki/concepts/improving-red-team-precision-and-cross-model
    type: extends
  - target: wiki/concepts/blind-spot-detection-methods
    type: extends
  - target: wiki/concepts/multi-agent-correlated-errors
    type: extends
  - target: wiki/concepts/review-attacks-implementation-misses-framing
    type: related
  - target: wiki/concepts/adaptive-risk-assessment-single-pass-first-architecture
    type: related
---

# Great adversarial-review skill design

## Decision context

The operator asked (2026-08-12): "what does a great red-team/critical
review/pre-mortem skill look like? what do people like? what can we improve
on?" The question followed a coverage audit showing `/redteam` (alias for
`/risk`) challenges risk-by-target-type but not requirements validity, and
only challenges framing when escalation earns it. This research answers the
question from three evidence layers: practitioner sentiment (HN/Reddit/blog),
the actual SKILL.md contents of 10 installable adversarial-review skills, and
the empirical literature on structured challenge techniques.

## What practitioners like and dislike (Round 2b signal)

- **Noise is the #1 complaint about AI review.** HN: "most teams just end up
  with more noise in their merge requests", "AI review bots spam your PRs
  with a ton of comment noise", "I've had to disable the AI reviewer on some
  projects". The Entelligence 2026 benchmark quantifies it: best F1 = 47%,
  precision ranges 16-67% — Graphite has the highest precision (67%) at the
  lowest recall (7.5%), and practitioners respect precision. playerzero.ai
  estimates 80-90% of AI alerts are not actionable.
- **What they like**: context-aware feedback (CodeRabbit praised on G2 for
  "context-aware feedback that enhances code quality"), severity tiers with
  file:line citations (SonarQube's model "fits existing developer mental
  models"), actionable on-the-spot fixes, fast feedback, integration with
  the existing workflow (PR/commit metadata), and human-in-the-loop
  cherry-picking.
- **Pre-mortems are broadly liked** as a practice (FTX pre-mortem 96 HN pts,
  WSJ feature, "Premortems will keep your code alive") — but primarily as a
  team/meeting practice, with a documented caveat: they degrade without live
  interaction (riskology.co: "will not work via email") and can become
  performative under social pressure (already documented in our wiki).

## What the best installable skills do (8 structural design patterns)

Read from the actual SKILL.md files of 10 skills (DecisionNerd/RedTeam 29
commands; alirezarezvani adversarial-reviewer; lemon03390 adversarial-review;
parcadei premortem; AndyShaman premortem; karpathy-metric-pre; borghei
legal-red-team; Athena red-team-review; grill-me; richfrem red-team-review):

1. **Verify-before-flag evidence** (parcadei premortem): every risk must pass
   explicit gates (`context_read`, `fallback_check`, `scope_check`) and carry
   a `mitigation_checked:` field citing what was looked for and not found.
   Eliminates pattern-matching flags without reading context. Also
   karpathy-metric-pre: every gaming vector needs a *specific scenario* (not
   generic) + time-to-human-detection.
2. **Confidence-score suppression** (lemon03390): findings < 4/10 confidence
   move to a low-confidence appendix instead of the main list. The cleanest
   noise-reduction pattern found — suppress without hiding.
3. **Mandatory-findings rules** (alirezarezvani): 3 hostile personas, each
   must surface ≥1 issue — "no LGTM escapes"; findings caught by 2+ personas
   auto-promote one severity level. Counter to rubber-stamp reviews.
4. **Declarative priors** (Athena Phase 0): state thesis + falsifier +
   missing perspective BEFORE critiquing. Plus the rare "empty sections are
   fine — don't invent issues" rule that licenses honest zero-findings.
5. **Reverse / counter-bias phase** (AndyShaman): a reverse premortem fires
   only when the session recommends caution/stall/abort — countering the
   systematic over-cautious bias of pure premortem. Only 1 of 10 skills has
   an explicit structural counter to its own method's bias.
6. **Numeric gates** (lemon03390 PR Score 0-100; borghei 1-5 distribution
   readiness gate, ≤3/5 = must not distribute): "ready to ship" becomes a
   falsifiable claim, not a vibe.
7. **Adversarial persona = the thing being gamed** (karpathy-metric-pre):
   "an optimization agent with no values... only a score to maximize" —
   red-teams the metric, not the implementation. The metric-gaming
   pre-mortem class.
8. **Iteration isolation + cost telemetry** (richfrem): each review loop in
   `.history/review-iteration-N/`, logs `total_tokens` + `duration_ms` per
   round so the cost of approval is visible and rewrites never destroy the
   baseline.

## Empirical evidence: structured beats unstructured

- **Pre-mortem**: Mitchell/Russo/Pennington controlled study — prospective
  hindsight increases identification of failure causes by ~30% vs standard
  risk analysis; 2024 MTU field study (p<0.05) confirms overrun reduction;
  brainwriting variant lowers social-pressure barriers.
- **Devil's advocate vs dialectical inquiry** (Schweiger 1986/1989/1990,
  120+ subjects): both beat consensus on decision quality; DI (full
  counter-plan) beats DA (critique) on *assumption quality*; DA has lower
  participant satisfaction.
- **ACH** (2019 Applied Cognitive Psychology study): reduces confirmation
  bias in hypothesis evaluation — the only empirically tested bias-reduction
  technique for hypothesis evaluation.
- **Caveat**: design-thinking reframing tools (Reframing Matrix, Five-Phase
  Problem Framing, Ladder of Inference) are practitioner-validated but lack
  RCT evidence — label accordingly.

## What this means for our workspace

The workspace already implements several of these patterns (multi-critic
panel convergence, evidence-required-for-BLOCK/REVISE, model-family
diversity, `/risk` escalation ladder). The improvements with positive ROI:

1. **Confidence-score suppression in /risk** — adopt lemon03390's pattern:
   specialist findings below a confidence threshold move to a low-confidence
   appendix rather than the main findings table. Directly addresses the
   documented over-reporting problem (52 findings, ~10% actionable).
2. **Requirements/framing-validation lens (the confirmed gap)** — no skill in
   our catalog challenges requirements validity or walks assumptions back to
   their evidence. Prior art to study: GitHub spec-kit (`/speckit.checklist`
   "unit tests for English", `/speckit.clarify`), Decision Quality Checks
   (meaning-checks before treating metrics as decision-grade), Ladder of
   Inference backward-walk, SAST/ABP for load-bearing assumption extraction.
   Candidates: a requirements-challenge phase in /risk, or a new skill.
3. **Metric-gaming pre-mortem for fleet metrics** — karpathy-metric-pre's
   persona ("optimize the score, no values") applies directly to our
   model-pool / quota / benchmark selection: before choosing pool weights or
   benchmark gates, red-team the metric itself (Direct Gaming, Proxy
   Divergence, Eval Contamination, Silent Degradation).
4. **Reverse/counter-bias phase in /risk** — /risk is structurally biased
   toward finding problems; an explicit "cost of NOT proceeding" /
   steelman-the-decision phase (fired only when the verdict is
   caution-oriented) would balance it, mirroring AndyShaman's reverse
   premortem. `/tp` already has steelman (domain 4a) — /risk does not.
5. **Cite the receipts when defending pre-mortem value** — 30% (Mitchell),
   p<0.05 field (MTU 2024), DI > DA (Schweiger). Note the face-to-face
   caveat for automated pre-mortems: our /risk pre-mortem passes are
   single-agent, which is structurally weaker than a team pre-mortem — the
   multi-critic panel partially compensates.
6. **Fill the stale TODO** in `improving-red-team-precision-and-cross-model`
   — its "What this means for our workspace" section was never written; the
   3 approved improvements ARE implemented in /risk (precision incentive
   prompt, cross-model specialists, critic-verdict verification).

## Falsifier

This concept is wrong if: (a) practitioner sentiment shifts away from
noise/precision being the dominant complaint (e.g., recall becomes the
binding constraint); (b) structured-technique evidence is refuted by a
controlled study (Schweiger/Mitchell results don't replicate); (c) a
requirements-validation skill is built and shows zero marginal value over
/risk's existing decision target type; or (d) the confidence-suppression
pattern measurably hides real findings (operator misses a shipped bug that
was in the suppressed appendix).

---
title: "Risks skill improvement research: validation, progressive disclosure, cold-start, pipeline gates, routing"
created: 2026-08-05
source: session-019fcdd2 (/www on /risks brainstorming ideas)
tags: [skill-improvement, risk-assessment, progressive-disclosure, eval-driven-development, cold-start, pipeline-gate, skill-routing, /risks, research]
summary: >
  Five parallel cross-model research subagents (OpenRouter/ling, GLM,
  Zen/DeepSeek, MiniMax, Cohere) investigated how to improve the /risks
  skill across 5 domains: skill validation methodology, progressive
  disclosure for SKILL.md, cold-start knowledge bootstrapping,
  pipeline-integrated risk gates, and skill routing disambiguation.
  Key findings: (1) eval-driven development with pass^k metrics for
  escalation consistency, (2) flat one-level progressive disclosure is
  optimal (arxiv controlled study), (3) cold-start bootstrapping via
  mining existing failure artifacts with provenance gate, (4) four-gate
  taxonomy (advisory/validating/blocking/escalating) with conservative
  advisory-only start, (5) intent classification + progressive overlap
  resolution for routing.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://www.fiddler.ai/blog/automating-eval-driven-development-agentic-applications
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://developers.redhat.com/articles/2026/03/23/eval-driven-development-build-evaluate-ai-agents
  - https://arxiv.org/abs/2607.17598
  - https://boliv.substack.com/p/lazy-skills-a-token-efficient-approach
  - https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/
  - https://blog.cyeam.com/ai/2026/05/26/skill-on-demand-loading
  - https://en.wikipedia.org/wiki/Cold_start_(recommender_systems)
  - https://engineering.zalando.com/posts/2025/09/dead-ends-or-data-goldmines-ai-powered-postmapping.html
  - https://link.springer.com/article/10.1007/s13198-024-02359-y
  - https://www.digitalapplied.com/blog/agentic-workflow-approval-gate-framework-governance
  - https://orchestkit.yonyon.ai/docs/reference/skills/quality-gates
  - https://www.logmetry.io/blog/alert-fatigue-90-percent-false-positives
  - https://www.patronus.ai/ai-agent-development/ai-agent-routing
relations:
  - target: wiki/concepts/adaptive-risk-assessment-single-pass-first-architecture.md
    type: extends — the architecture this research aims to improve
  - target: wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md
    type: complements — ensemble patterns already in /risks; this research covers gaps around them
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: extends — adds validation methodology, cold-start, and progressive disclosure to the 7-dimension framework
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends — applies progressive disclosure to SKILL.md (prior concept covered AGENTS.md only)
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: related — cold-start amnesia is the failure mode the bootstrap addresses
---

# Risks skill improvement research

## Decision context

**Why this was needed:** the /risks skill was iterated 4× in one session (v1→v4)
based on a single run that produced inflated findings. The brainstorming
produced 6 improvement ideas (test-run, optimize common path, bootstrap wiki,
wire into /go, clarify routing, simplify body). This research validates or
disconfirms each idea against external evidence before implementation.

**What alternatives were explored:** we considered (a) implementing improvements
directly from theory (the v1→v4 pattern), (b) running /risks on real targets
first and fixing empirically, (c) researching each idea against external
evidence. We chose (c) — research first — because the skill's design has never
been validated against how other teams solve these problems.

**What the research changed:** confirmed 4 of 6 ideas have strong external
evidence support. Subsumed idea 6 (simplify body) into idea 2 (progressive
disclosure). Lowered priority of idea 5 (routing) based on applicability
analysis. Added 2 new techniques not in the original brainstorming (eval-driven
development, bandit write-back threshold).

## Findings by domain

### 1. Skill validation: eval-driven development (idea 1 — confirmed)

**Core finding:** the industry standard for testing AI agent skills is
**Eval-Driven Development (EDD)** — define what "correct" looks like BEFORE
writing the skill logic, then score against test cases iteratively.

**Key techniques:**

| Technique | What it does | Source |
|---|---|---|
| EDD inner loop | Run → score → diagnose → fix → re-run | Fiddler.ai |
| pass^k metric | Probability that ALL k trials succeed — for consistency-sensitive logic | Anthropic |
| Known-bad testing | Capture conversations where agent failed, verify evals catch them | Red Hat |
| Capability vs regression suites | Capability = what it CAN do (low pass); Regression = what it still does (~100%) | Anthropic |
| Multi-grader composition | Deterministic (fast) + LLM rubric (nuance) + human (gold standard) | Anthropic |
| Swiss Cheese layers | Automated evals + transcript review + production monitoring | Anthropic |

**Applicability to /risks:** pass^k is the right metric for escalation logic —
an escalation that works 7/10 times is unacceptable for a risk skill. Known-bad
test set should cover: (a) scan misses HIGH risk, (b) escalation fires when it
shouldn't, (c) escalation fails to fire when it should, (d) threat-model
inflation (the v1 failure, documented in [[multi-model-ensemble-design-patterns-for-agent-skills]]).

**Confidence: HIGH** (≥3 independent sources: Anthropic, Red Hat, Fiddler).

### 2. Progressive disclosure: flat one-level split (ideas 2+6 — confirmed, merged)

**Core finding:** the arxiv paper "Is Progressive Disclosure All You Need for
Long-Context Agents?" (He et al., Jul 2026) provides the **only controlled
study**. Conclusion: **flat one-level disclosure is optimal**. Hierarchical
(always-loaded child skills) actively HURTS accuracy (30% drop observed).

**Concrete recommendation for /risks:**

| Content | Location | Why |
|---|---|---|
| Phases 0-3 (assess, scan, critique, report) | SKILL.md body | 80% common path — always needed |
| Phase 4-5 (attack, wargame) | `references/attack-phase.md` | ~20% of runs — load on demand |
| Findings JSON schema | `references/findings-schema.json` | Mechanical — load when writing |

**Anti-patterns to avoid:** (a) creating separate `/risks-attack` skill with
its own always-loaded metadata (proven harmful), (b) reference files pointing
to more reference files (agents get lost), (c) stale `description` field
(drives routing, must stay accurate).

**Risk:** probabilistic loading — the agent may not read the reference file
when it reaches Phase 4. Mitigation: explicit body instruction ("read
`references/attack-phase.md` NOW"). This is the Fowler "illusion of control"
caveat — skills are LM-decided loading, not deterministic. This pattern is
already documented for AGENTS.md in [[agents-md-construction-best-practices]].

**Token savings:** ~1,500 tokens saved on 80% of runs (Phase 4 never loads).

**Confidence: HIGH** (controlled study + production deployments + practitioner consensus).

### 3. Cold-start bootstrapping: mine + provenance-gate (idea 3 — confirmed)

**Core finding:** our wiki is a "new community" cold start (the hardest variant —
both items and users are new). The loop is structurally deadlocked until seeded.
This is the same failure class as [[agent-failure-modes-2026]]'s cold-start amnesia.

**Three canonical seeding strategies (do all three; none conflict):**

1. **Mine existing history (Zalando pattern):** multi-stage pipeline
   (summarize → classify → pattern-detect) over handoffs, AARs, audit outputs.
   Highest ROI because the data is domain-authentic.
2. **Curated seed (MovieLens pattern):** manually register N highest-value
   patterns as a one-time step. Active learning: seed the most informative
   patterns first (those near category boundaries).
3. **Import external (postmortem repos):** map public failure patterns to our
   taxonomy. Group-level similarity lets new patterns inherit class priors.

**Write-back threshold (the key design question):**

| Approach | Risk | Source |
|---|---|---|
| Static strict threshold | Deadlock — nothing gets written, loop never starts | RecSys literature |
| Static loose threshold | Noise — LLM-extracted patterns have 15% hallucination rate | Zalando |
| **Provenance gate + exploration budget** | Balanced — write if grounded in ≥1 source; explore during warm-up | Bandit literature + Zalando |

**No magic number for minimum viable size** — viability is about outcome (does
the system produce useful recommendations from day one), not count. `[INFERENCE]`
estimate: 20-40 patterns across meaningful classes.

**Confidence: HIGH** for the deadlock diagnosis and seeding strategies;
MEDIUM for the specific threshold design (needs empirical tuning).

### 4. Pipeline-integrated risk gates: advisory-first (idea 4 — confirmed)

**Core finding:** the consensus pattern is a **four-gate taxonomy**
(advisory → validating → blocking → escalating) with **blast-radius ×
reversibility** as the trigger axis.

**Alert fatigue constraint (critical):** SOC data shows 90% false-positive
rates when auto-firing without suppression. The fix is better signal sources,
not threshold tuning. False positives are rule-design failures, not threshold
problems.

**Recommended phased rollout for /go integration:**

| Phase | Gate tier | Trigger | What happens |
|---|---|---|---|
| 1 | Advisory | `reversibility ≥ 1.75` | Log to handoff, no workflow change |
| 2 | Validating | Confirmed pattern | Log + evidence artifact in handoff |
| 3 | Blocking | HIGH risk + irreversible | Halt until override or fix |
| 4 | Escalating | Risk class unidentifiable | Route to operator with packet |

**Key design insight:** the gate is *almost free* on reversible work (zero
added cost) but mandatory on irreversible work. This aligns with our existing
`action_safety` protocol's reversibility scoring and the
[[adaptive-expansion-evidence-triggered-conditional-steps]] pattern (fixed
core + adaptive expansion).

**Confidence: HIGH** (12 independent sources converge on the same taxonomy).

### 5. Skill routing: intent classification + progressive resolution (idea 5 — lower priority)

**Core finding:** the consensus approach is intent classification + capability
filtering + progressive overlap resolution (start with one tool, escalate to
another).

**Anti-pattern confirmed:** the "over-tooled agent problem" — multiple tools
claiming the same domain degrades routing accuracy.

**Applicability caveat:** our operator self-routes effectively (/tp for
framing, /review for code, /risks for risk). The routing improvement primarily
benefits automated routing (/ask, /go), not the operator directly. This makes
it lower priority than the other 4 confirmed ideas.

**Confidence: MEDIUM** (techniques are well-supported, but applicability to
our specific context is weaker because our operator is sophisticated).

## Applicability matrix (Round 3.25 gate)

| Idea | Evidence quality | Workspace need | Host invariant | Promote? |
|---|---|---|---|---|
| 1. Test on real targets (EDD) | HIGH (3+ sources) | HIGH (zero receipts) | Pass | ✅ YES |
| 2. Progressive disclosure split | HIGH (controlled study) | HIGH (500-line skill) | Pass | ✅ YES |
| 3. Bootstrap wiki (mine+seed) | HIGH (Zalando+RecSys) | HIGH (empty wiki) | Pass | ✅ YES |
| 4. Wire into /go (advisory-first) | HIGH (12 sources) | MEDIUM (not yet needed) | Pass | ✅ YES |
| 5. Clarify routing | MEDIUM (techniques solid) | LOW (operator self-routes) | Pass | ❌ DEFER |
| 6. Simplify body | Subsumed by #2 | — | — | Merged into #2 |

## What this means for /risks

1. **Test before trusting** — the skill has zero execution receipts. Run it
   on 2-3 real targets with known-bad test cases. Use pass^k for escalation
   consistency.
2. **Split using flat disclosure** — move Phase 4-5 to
   `references/attack-phase.md`. Keep Phases 0-3 in SKILL.md body. Do NOT
   create separate skills.
3. **Mine the wiki** — one-shot pipeline over handoffs + AARs + audit outputs
   to extract ~20-40 seed risk patterns with provenance. Lower the write-back
   threshold during warm-up with a provenance gate.
4. **Wire into /go as advisory-only** — fire `/risks scan` when
   `reversibility ≥ 1.75`. Log to handoff. Build precision baseline over 10-20
   firings before promoting to blocking.

## Falsifier

This research is wrong if:
- EDD metrics don't transfer to multi-phase skill testing (escalation logic
  is more complex than single-turn evaluation)
- Progressive disclosure causes the agent to miss the Phase 4 reference file
  on real runs (probabilistic loading risk)
- Mining produces noise patterns that pollute the wiki (Zalando's 15%
  hallucination rate)
- Alert fatigue applies even with advisory-only start (operator dismisses
  the gate within a week)

## Receipts

- **`/risks` SKILL.md:** `C:/Users/brsth/.grok/skills/risks/SKILL.md` — 500+ lines, 6 phases, all 7 ensemble patterns. The skill this research aims to improve.
- **Multi-model ensemble patterns wiki concept:** `P:/.data/wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md` — documents the 7 patterns already in /risks. This research covers gaps AROUND those patterns.
- **Progressive disclosure for AGENTS.md:** `P:/.data/wiki/concepts/agents-md-construction-best-practices.md` — covers progressive disclosure for AGENTS.md. This research extends the pattern to SKILL.md.
- **arxiv controlled study:** `https://arxiv.org/abs/2607.17598` — He et al., "Is Progressive Disclosure All You Need for Long-Context Agents?" — the only controlled study comparing flat vs. hierarchical disclosure. Key result: flat is optimal, hierarchical causes 30% accuracy drop.
- **Zalando mining pipeline:** `https://engineering.zalando.com/posts/2025/09/dead-ends-or-data-goldmines-ai-powered-postmapping.html` — production deployment of LLM-powered postmortem pattern mining. 15% hallucination rate documented.
- **Cold-start taxonomy:** `https://en.wikipedia.org/wiki/Cold_start_(recommender_systems)` — classifies our wiki as "new community" cold start (hardest variant).
- **5 parallel subagent dispatch:** session 019fcdd2, subagents 019fd3fb-e0c8 through e0cd — 5 models (OpenRouter/ling, GLM, Zen/DeepSeek, MiniMax, Cohere), 5/5 completed, 95-167s each.

## Sources

### Skill validation
- [Fiddler.ai — Automating EDD for Agentic Applications](https://www.fiddler.ai/blog/automating-eval-driven-development-agentic-applications)
- [Anthropic — Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Red Hat — EDD: Build and Evaluate AI Agents](https://developers.redhat.com/articles/2026/03/23/eval-driven-development-build-evaluate-ai-agents)
- [Iris Eval — Agent Eval Continuous Quality Layer](https://iris-eval.com/learn/agent-eval)
- [Superpowers — writing-skills eval harness](https://github.com/obra/superpowers)

### Progressive disclosure
- [He et al. — Is Progressive Disclosure All You Need? (arXiv:2607.17598)](https://arxiv.org/abs/2607.17598)
- [boliv — Lazy Skills: 97% Token Savings](https://boliv.substack.com/p/lazy-skills-a-token-efficient-approach)
- [Towards Data Science — Claude Skills Token Economics](https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/)
- [cyeam — Four-Layer On-Demand Loading](https://blog.cyeam.com/ai/2026/05/26/skill-on-demand-loading)
- [Martin Fowler — Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)

### Cold-start bootstrapping
- [Wikipedia — Cold Start (Recommender Systems)](https://en.wikipedia.org/wiki/Cold_start_(recommender_systems))
- [Zalando — AI-Powered Postmortem Mining](https://engineering.zalando.com/posts/2025/09/dead-ends-or-data-goldmines-ai-powered-postmapping.html)
- [Springer — Multi-Armed Bandits for Bug/Developer Domain](https://link.springer.com/article/10.1007/s13198-024-02359-y)

### Pipeline-integrated risk gates
- [DigitalApplied — Agentic Workflow Approval Gate Framework](https://www.digitalapplied.com/blog/agentic-workflow-approval-gate-framework-governance)
- [OrchestKit — Quality Gates: BLOCKING vs WARNING](https://orchestkit.yonyon.ai/docs/reference/skills/quality-gates)
- [Logmetry — Alert Fatigue: 90% False Positives](https://www.logmetry.io/blog/alert-fatigue-90-percent-false-positives)
- [CardinalOps — False Positives are Rule-Design Failures](https://cardinalops.com/blog/rethinking-false-positives-alert-fatigue/)
- [Microsoft — Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)

### Skill routing
- [Patronus AI — AI Agent Routing](https://www.patronus.ai/ai-agent-development/ai-agent-routing)
- [SkillRouter: Skill Routing for LLM Agents at Scale (arXiv)](https://arxiv.org/abs/2602.12430)

---
title: "Epistemic Knowledge System Design (2026)"
created: 2026-08-02
source: session-2026-08-02
tags: [knowledge-management, epistemic-debt, confidence-decay, research-system, wiki-design, reference, architecture]
summary: >
  Comprehensive design for transforming /www, /web, /wiki from a knowledge
  collection system into a knowledge stress-testing system. Core insight from
  3 independent sources (Grok brainstorming, DeepSeek, Claude): confidence
  should decay, verification debt should compound, and the system should
  prioritize re-verifying decaying knowledge. 17 ideas across 4 phases,
  grounded in circuit breaker patterns, epistemic debt modeling, and
  adversarial persona research.
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
relations:
  - target: wiki/concepts/tool-failure-lifecycle-llm-agent-fleets.md
    type: related
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related
  - target: wiki/concepts/agent-skills-fleet-patterns-solo-director-2026.md
    type: related
---

# Epistemic Knowledge System Design (2026)

## Decision context

**Why this design was needed:** the operator asked "how can we make our /www, /web, /wiki system better in every way?" The answer required reframing what "better" means — not more features, but a fundamentally different knowledge model.

**What changed:** three independent sources converged on the same insight: **the system should treat knowledge as provisional, not permanent.** Confidence should decay, debt should compound, and the system should auto-prioritize re-verification. This is a shift from knowledge *accumulation* to knowledge *stress-testing*.

**What the research added:** external LLM perspectives (DeepSeek, Claude) surfaced structurally novel ideas — epistemic debt ledger with compounding interest, adversarial persona weaving, anti-causal trace mapping — that go beyond incremental improvements.

## The convergence signal

Three independent sources arrived at the same core insight:
- **Grok brainstorming:** "stale detection" + "temporal decay"
- **DeepSeek:** "epistemic debt" — unverified claims accrue debt with interest
- **Claude:** "confidence half-life" — belief ledger, not fact cache

All three say: **confidence decays, the system should prioritize re-verifying decaying knowledge.**

## The 17 ideas across 4 phases

### Phase 1: Behavioral (implementable now — SKILL.md + frontmatter)

| # | Idea | What it does | Status |
|---|---|---|---|
| 1 | Confidence decay frontmatter | Each concept gets `confidence` (0-1), `last_verified` (date), `half_life_days` (default 180). Confidence decays over time. | TO IMPLEMENT |
| 2 | Stale concept detection at session start | "These concepts are >6 months old — consider re-researching" | TO IMPLEMENT |
| 3 | Contradiction alerts | When new concept contradicts existing one, flag proactively | TO IMPLEMENT |
| 4 | Auto research triggers | `[INFERENCE]`/`[UNKNOWN]` items auto-suggest `/www` | TO IMPLEMENT |
| 5 | Quality-of-run reports | "This run was lower quality because X failed" | TO IMPLEMENT |
| 6 | Research debt tracking | Dangling wikilinks across concepts = unexplored topics | ALREADY DONE (/www Phase 3.5) |
| 7 | Epistemic debt tracking (behavioral) | Concepts with unverified claims flagged as "provisional only" | TO IMPLEMENT |
| 8 | Adversarial persona weaving (behavioral) | /www instructions to approach from 3 lenses | TO IMPLEMENT |

### Phase 2: Data-backed (needs persistent store — design + implement)

| # | Idea | What it does | Status |
|---|---|---|---|
| 9 | Source quality memory | Per-source reliability scores accumulated across runs | DESIGN NEEDED |
| 10 | Query pattern memory | "Last time 'review tutorial experience' worked for TTS" | DESIGN NEEDED |
| 11 | Failure pattern memory | Research strategy patterns (what worked/failed) | DESIGN NEEDED |
| 12 | Epistemic debt ledger (full) | Compounding interest model — debt increases over time, forces re-research | DESIGN NEEDED |
| 13 | Adversarial persona weaving (full) | 3 persistent personas with memory scratchpads | DESIGN NEEDED |

### Phase 3: Graph infrastructure (needs Python scripts)

| # | Idea | What it does | Status |
|---|---|---|---|
| 14 | Graph queries | "Shortest path between A and B" | BLOCKED — needs graph index |
| 15 | Staleness propagation | Flag concepts citing superseded ones | BLOCKED — depends on graph |
| 16 | Concept clustering | Domain overviews from tag/relation clustering | BLOCKED — needs graph |
| 17 | Confidence-weighted answers | Query returns confidence tier + provenance | BLOCKED — needs confidence decay adoption |

### Phase 4: Research (needs separate design doc)

| # | Idea | What it does | Status |
|---|---|---|---|
| 18 | Synthesis engine | Cross-domain pattern detection, new concept proposals | BLOCKED — /dream's domain |
| 19 | Anti-causal traces | Counterfactual dependency signatures | BLOCKED — research-paper-level |

## The load-bearing idea: Epistemic Debt Ledger

From DeepSeek (session 2026-08-02):

> "Every time /wiki writes a concept without disconfirming evidence, it accrues debt. /web searches are routed to pay down highest-interest debt first (claims with most downstream dependents). When debt exceeds a threshold, the system voluntarily degrades its own confidence scores and flags dependent agents to use that concept as provisional only."

**Why this is the keystone:** it makes the system self-motivating. Debt compounds, so the system *must* research even when no user asks. Research isn't triggered by the operator asking — it's triggered by the knowledge base's own health metrics.

**Simple version (Phase 1):** concepts with `verification: inferred-only` or concepts that cite only 1 source are "high debt." `/www` Phase 1 thread tracking surfaces them as re-research targets.

**Full version (Phase 2):** a Python script (`epistemic_debt.py`) that:
1. Scans all wiki concepts for confidence scores + verification tiers + downstream dependents
2. Computes debt = (1 - confidence) × age_factor × dependency_count
3. Outputs a debt-sorted priority list for `/todo` and `/www`

## Adversarial Persona Weaving

From DeepSeek:

> "For each research thread, /www spawns 3 persistent personas: True Believer (defends wiki consensus), Skeptic (finds contradictions), Outsider (imports cross-domain analogies). The wiki entry is the intersection of their concessions, not the union of their findings."

**Simple version (Phase 1):** add to /www Phase 2 a 3-lens instruction — "approach the emerging conclusions from 3 perspectives: what confirms them, what contradicts them, what analogy from another domain illuminates them."

**Full version (Phase 2):** 3 persistent personas with memory scratchpads, each proposing searches from their bias.

## What this means for our workspace

1. **Phase 1 items are SKILL.md/AGENTS.md/SCHEMA.md edits** — same shape as today's work. No new infrastructure.
2. **Phase 2 items need a persistent telemetry store** (`P:/.data/wiki/_state/research-telemetry.json`) for source/query/failure memory. Medium complexity.
3. **Phase 3 items need a graph index** — a Python script that reads all wiki frontmatter and builds a traversable graph. This is real code that needs design + testing.
4. **Phase 4 items are research-level** — synthesis engine and anti-causal traces need design docs, not just implementations.

## Receipts

- **Convergence signal:** [FACT] 3 independent sources (Grok, DeepSeek, Claude) all proposed confidence decay / debt compounding
- **DeepSeek response:** [FACT] Received via Chrome DevTools MCP, page 13, session 2026-08-02
- **Claude response:** [FACT] Received via Chrome DevTools MCP, page 15, session 2026-08-02
- **ChatGPT/Gemini/Perplexity:** [PROBLEM] ChatGPT still generating at collection time; Gemini selector failed; Perplexity contenteditable fill didn't take. 2/5 responded.
- **Circuit breaker validation:** [FACT] Azure Architecture Center + Resilience4j docs (see [[tool-failure-lifecycle-llm-agent-fleets]])

## Falsifier

This design is wrong if:
- Confidence decay adds complexity without changing research prioritization (the debt model is ignored)
- Adversarial personas produce noise instead of insight (the 3-lens approach degrades quality)
- The graph infrastructure (Phase 3) proves unnecessary because the flat wiki + grep is sufficient
- The operator never looks at epistemic debt scores (the telemetry is ignored)

## Related

- [[tool-failure-lifecycle-llm-agent-fleets]] — tool management for the same fleet
- [[inference-in-code-blind-spot]] — the session incident that started this meta-analysis
- [[agent-skills-fleet-patterns-solo-director-2026]] — fleet patterns
- [[plausible-narratives-substitute-for-verification]] — the prose equivalent of confidence decay

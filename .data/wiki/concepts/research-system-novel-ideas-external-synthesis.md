---
title: "Research System Structurally Novel Ideas (External Research Synthesis)"
created: 2026-08-04
source: "Perplexity KB project (Jul 18, 2026) — 30 academic sources"
tags: [research-system, belief-ledger, research-market, adversarial-replay, knowledge-management, external-research, architecture]
summary: >
  Three structurally novel ideas for improving the /wiki → /web → /www research
  system, sourced from external academic research (arxiv, ACM, OpenReview). Not
  incremental tweaks — they change the system's internal economics, memory model,
  and learning loop. (1) Belief ledger: claims as evolving objects with provenance,
  confidence, and revision history. (2) Research market: budget allocation by
  expected information gain. (3) Adversarial replay harness: past runs as
  counterfactual test assets. Priority order: belief ledger first, adversarial
  replay second, research market third.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - "Perplexity: fleet of AI coding agents with research system (Jul 18, 2026) — https://www.perplexity.ai/search/52ee59fd-5e08-4c25-a637-3ff25a2ffb81"
  - "Graph-based agent memory research — arxiv (extraction, storage, retrieval, evolution lifecycle stages)"
  - "Zep/Graphiti temporally aware memory systems"
  - "DeepResearch Bench (citation accuracy and effective citations as separate dimensions)"
  - "Information-gain work in retrieval and active learning"
  - "Adversarial framing reduces overconfidence (OpenReview)"
relations:
  - target: wiki/concepts/epistemic-knowledge-system-design-2026.md
    type: refines
  - target: wiki/concepts/persistent-kb-architecture-model-sunset-survivability.md
    type: complements
  - target: wiki/concepts/sdlc-command-cognitive-jobs-taxonomy.md
    type: related
---

# Research System Structurally Novel Ideas (External Research Synthesis)

## Decision context

**Why this research was needed:** the operator asked ChatGPT and Perplexity: "What 3 ideas would make this research system genuinely better?" The system already had /wiki (800+ concepts, auto-linking, gap detection), /web (multi-backend search with RRF merge), and /www (wiki→web→wiki orchestrator). The question was not about incremental improvements but structurally novel ideas that change the system's internal economics.

**What the external research added:** three ideas grounded in academic literature that go beyond what the internal brainstorming ([[epistemic-knowledge-system-design-2026]]) produced. Each changes a different axis: memory model, budget allocation, and learning loop.

## Idea 1: Belief ledger

**The concept:** transform /wiki from a polished notebook into a lightweight epistemic database. Each important claim becomes a structured object with provenance, time validity, confidence, supporting evidence, disconfirming evidence, and a revision history — rather than collapsing into one "best current note."

**Claim object schema:**
```
claim: "X is true"
scope: <what domain this applies to>
status: active | superseded | contradicted
confidence: 0.0-1.0
valid_from: <date>
valid_until: <date or null>
supersedes: <previous claim ID or null>
supported_by: [<evidence IDs>]
challenged_by: [<evidence IDs>]
depends_on: [<prerequisite claim IDs>]
```

**Evidence object schema:**
```
source_metadata: <URL, author, date>
extraction_span: <exact quote or paraphrase>
authority_score: 0-10
freshness_score: 0-10
evidence_type: direct | second-hand
```

**Revision rules:** auto-downgrade confidence when evidence ages out, source authority drops, or contradictions accumulate. Query modes: "highest-confidence current belief," "most-contested claim," "beliefs needing revalidation."

**Why this is genuinely better:**
- Reduces silent knowledge drift (especially for fast-changing topics)
- Lets the system answer "what changed, why did we believe it, and what would falsify it now?" instead of only "what do we know?"
- Makes thread tracking more useful — threads become trajectories of belief revision, not just histories of documents

**Relationship to existing work:** [[epistemic-knowledge-system-design-2026]] already proposes confidence decay frontmatter (`confidence`, `last_verified`, `half_life_days`). The belief ledger extends this by making claims first-class objects with contradiction edges and dependency tracking, rather than just frontmatter fields on concept pages. The existing design is Phase 1 (behavioral); the belief ledger would be Phase 2+ (structural). This concept also connects to [[persistent-kb-architecture-model-sunset-survivability]] — the belief ledger lives in Layer 1 (canonical store) as structured frontmatter, not in a derived index.

## Idea 2: Research market

**The concept:** replace the fixed wiki→web→wiki pipeline with a market-based planner where candidate actions compete for budget based on expected information gain. Each research step becomes an investment decision under uncertainty.

**Action types:** expand, verify, disconfirm, refresh, synthesize, stop.

**Utility function per action:**
```
U(a) = α(Δuncertainty) + β(Δcitation_quality) + γ(Δcoverage) − λ(cost) − μ(tool_risk)
```

**How it works:** the orchestrator runs a small auction each cycle; the top action wins budget. Portfolio constraints ensure diversity (e.g., at least one disconfirming action if confidence exceeds a threshold without source diversity). System diagnostics expose: "we did not browse further because expected gain was below threshold."

**Why this is genuinely better:**
- Prevents over-searching obvious areas while under-investigating fragile claims
- Gives a principled stopping rule: stop when no action has enough expected value
- Turns "proactive suggestions after every run" into ranked research opportunities with explicit payoff estimates

**DeepResearch Bench validates the multi-dimensional quality model:** citation accuracy and effective citations are separate dimensions. "More retrieved information" and "better grounded information" are not the same thing.

## Idea 3: Adversarial replay harness

**The concept:** treat every completed /www run as a reusable test asset. Persist the trace, decision points, skipped alternatives, uncertainty estimates, and final claims. Then automatically generate "counterfactual replays":

- What would the system conclude if its top source vanished?
- Would it still make the same claim if evidence arrived in reverse order?
- Would it incorrectly merge two similar entities?
- Would it cite pooled evidence from the wrong source?
- Would confidence remain too high after tool failures?

**Scoring dimensions:**
- **Calibration:** did confidence match actual robustness?
- **Attribution accuracy:** was each claim tied to the correct source, not merely some supporting source?
- **Recovery behavior:** did the system degrade gracefully under tool failures and evidence loss?

**Why this is genuinely better:**
- Converts one-off production experience into a permanent red-team dataset
- Attacks the hardest failure mode in research systems: plausible but misattributed or under-challenged synthesis
- Gives a path to measurable improvement via calibration and provenance, not just anecdotal "seems smarter"

**Perturbation types:** source removal, source swap, stale snapshot, injected contradiction, authority inversion, MCP/tool poisoning simulations.

## Priority order

| Idea | Why first | Main upside | Main risk |
|------|-----------|-------------|-----------|
| **Belief ledger** | Upgrades memory, makes later improvements coherent | Change tracking, contradiction handling, cross-session reasoning | Schema and maintenance complexity |
| **Adversarial replay** | Fastest route to measurable truthfulness gains | Calibration, provenance discipline, robust failure learning | Requires good trace capture and evaluation design |
| **Research market** | Highest upside once the first two exist | Smarter budget allocation, principled stopping | Utility function can be gamed or misweighted early |

## What this means for our workspace

1. **The belief ledger is the natural evolution of the epistemic system design.** Phase 1 (confidence decay) is already implemented. The belief ledger would be Phase 2 — structured claim objects in the canonical store, not just frontmatter fields. The `build_graph.py` planned in Phase 3 of the epistemic system design would read claim objects as nodes.

2. **The research market would change /www from a pipeline to a planner.** Currently /www runs a fixed Phase 1 (wiki query) → Phase 2 (web search) → Phase 3 (wiki write) sequence. The market model would let it choose dynamically: "skip web search because the wiki already covers this with high confidence" or "do a disconfirming search because the current evidence is one-sided."

3. **The adversarial replay harness connects to /harvest and /aar.** Past research runs are already partially captured in the www-ledger. The replay harness would turn those into test assets by adding trace persistence (query plan, retrieved docs, claim deltas, confidence snapshots) and perturbation generators. See [[sdlc-command-cognitive-jobs-taxonomy]] — `/research` reducing uncertainty is the cognitive job that the replay harness would measure.

4. **These three ideas together turn the research system from a capable workflow into a self-improving epistemic system.** The belief ledger provides the memory model, the research market provides the allocation intelligence, and the adversarial replay harness provides the learning loop.

## Falsifier

These ideas are wrong if:
- The belief ledger schema is too complex for agents to maintain consistently (drift makes it unreliable)
- The research market's utility function weights are impossible to tune (every action looks equally valuable or worthless)
- The adversarial replay harness produces only obvious failures that manual review would have caught anyway
- The current pipeline architecture already handles these cases through other mechanisms (proactive suggestions, gap detection, contradiction scanning)

## Sources

- Perplexity: fleet of AI coding agents with research system (Jul 18, 2026) — 30 academic sources
- Graph-based agent memory literature (arxiv) — extraction, storage, retrieval, evolution lifecycle
- Zep/Graphiti — temporally aware memory systems for cross-session synthesis
- DeepResearch Bench — citation accuracy and effective citations as separate quality dimensions
- Information-gain work in retrieval and active learning (ACM)
- Adversarial framing research (OpenReview) — reduces overconfidence, improves calibration

## Receipts

- Existing epistemic system design: `P:/.data/wiki/concepts/epistemic-knowledge-system-design-2026.md` (Phase 1 confidence decay implemented; Phases 2-4 in handoff)
- www-ledger location: `P:/.data/wiki/_state/www-ledger.json` (tracks /www runs — would be the source for adversarial replay traces)
- [INFERENCE] The belief ledger schema would extend the existing SCHEMA.md frontmatter format rather than creating a new storage system
- [INFERENCE] The research market utility function weights (α, β, γ, λ, μ) are not yet tuned and would need empirical calibration

## Auto-related

- [[skill-catalog]]
- [[research-applicability-checking-dont-cite-without-verifying-assumptions]]
- [[research-vs-design-vs-architect-skills-and-www-self-assessment]]
- [[deep-research-systems-and-web-upgrade]]
- [[skill-graph]]


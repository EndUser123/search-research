---
title: "Systematic problem anticipation: decision graphs, FMEA, MCTS, and what skills exist"
created: 2026-07-27
source: session-019fa276 (/www research on outcome-space mapping + existing tools)
tags: [decision-analysis, FMEA, MCTS, LATS, tree-of-thoughts, sensitivity-analysis, pre-mortem, formal-methods, outcome-mapping, skills-survey, decision-graph]
summary: >
  Two-part research: (1) what formal methods exist for mapping all possible
  outcomes and comparing to optimal — from informal (pre-mortem) through
  semi-formal (decision trees, Monte Carlo) to formal (MDP/POMDP, MCTS, model
  checking); and (2) what skills/repos/tools already implement these, across
  our environment, the Claude marketplace, and the internet. Key finding:
  exhaustive outcome enumeration is computationally intractable for real
  decisions; the professional answer is smart sampling (MCTS) + structured
  safeguards (FMEA, pre-mortem, sensitivity analysis). Existing tools: LATS
  (650 citations, ICML 2024) brings MCTS to LLM agents; Tree of Thoughts
  (7900 citations) does deliberate tree search; FMEA skills exist in the
  Claude marketplace; our workspace has the informal layer (pre-mortem,
  steelman) but lacks FMEA, sensitivity analysis, and MCTS.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - "https://arxiv.org/abs/2310.04406" (Zhou et al., LATS, ICML 2024, 650 citations)
  - "https://openreview.net/forum?id=5Xc1ecxO1h" (Yao et al., Tree of Thoughts, NeurIPS 2023, 7900 citations)
  - "https://openreview.net/forum?id=G7sIFXugTX" (Antoniades et al., SWE-Search, 152 citations)
  - "https://github.com/lapisrocks/LanguageAgentTreeSearch" (LATS official repo)
  - "https://github.com/kyegomez/tree-of-thoughts" (ToT plug-and-play implementation)
  - "https://github.com/opendilab/LightZero" (MCTS + deep RL, NeurIPS 2023)
  - "https://mcpmarket.com/tools/skills/fmea-risk-analysis-1" (FMEA Claude Code skill)
  - "https://www.claudedirectory.org/skills/claude-skills-scenario-war-room" (Scenario War Room skill)
  - "https://github.com/tjboudreaux/cc-thinking-skills" (28 mental model frameworks for Claude Code)
  - "https://www.naboo.ai/how-to-build-a-decision-graph/" (Decision Graph for AI agents, Naboo, Jun 2026)
  - "https://github.com/YuchenXia/LLMRiskAnalyzer" (FMEA for LLM systems)
  - "P:/.data/wiki/concepts/blind-spot-detection-methods.md" (pre-mortem + RCF + ACH coverage)
  - "P:/.data/wiki/concepts/cognitive-enforcement-patterns-for-ai-coding-agents.md" (pre-mortem protocol)
relations:
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: extends
  - target: wiki/concepts/cognitive-enforcement-patterns-for-ai-coding-agents.md
    type: extends
  - target: wiki/concepts/mental-models-for-tp-and-brainstorming.md
    type: complements
  - target: wiki/concepts/skill-domain-map.md
    type: related
---

# Systematic problem anticipation: decision graphs, FMEA, MCTS, and what skills exist

## Decision context

**Why this research was needed:** the operator asked whether "mapping every
possible choice or outcome onto a graph and comparing to optimal" is what
the agent does when asked "what are the predictable problems?" The answer
is no — and the operator wanted to know what tools, skills, repos, and
methods exist for this class of question, across our environment and the
broader ecosystem.

## Part 1: Can you map every possible outcome?

### The math says no (for real decisions)

| Decision complexity | Possible outcomes | Exhaustive feasible? |
|---|---|---|
| 10 binary choices | 2^10 = 1,024 | Yes |
| 20 binary choices | 2^20 = ~1 million | Borderline |
| 30 binary choices | 2^30 = ~1 billion | No |
| Real software decision | Continuous + interacting | Definitely not |

The optimality assumption (enumerate outcomes, assign probabilities, define
optimal) breaks on (a) exponential blowup, (b) unknowable probabilities,
and (c) subjective optimality criteria.

### The spectrum: informal → formal

| Tier | Method | What it does | Computational cost |
|---|---|---|---|
| **Informal** | Pre-mortem (Klein 2007) | "It failed. Why?" — narrative backward | Zero (human reasoning) |
| **Informal** | Steelman + falsifier | Name strongest alternative + disconfirmation | Zero |
| **Semi-formal** | FMEA | Systematic failure-mode enumeration per component | Low (structured checklist) |
| **Semi-formal** | Decision tree | Discrete choices + probabilities + outcomes | Moderate (tree size) |
| **Semi-formal** | Monte Carlo simulation | Sample outcomes randomly vs enumerate all | Moderate (N samples) |
| **Semi-formal** | Sensitivity analysis | Vary each assumption, find which matter | Low (parameter sweep) |
| **Semi-formal** | Scenario planning | 3-5 narrative futures, stress-test plan | Low (qualitative) |
| **Formal** | MDP/POMDP | States + actions + transitions + rewards | High (requires model) |
| **Formal** | MCTS | Sample promising tree branches, converge on optimal | High but bounded (anytime) |
| **Formal** | Model checking (SPIN, NuSMV) | Exhaustively verify all reachable states | Very high (state explosion) |
| **Formal** | Formal specification (TLA+, Alloy) | Prove properties hold mathematically | Very high (expert needed) |

### The method closest to "map every outcome": MCTS

Monte Carlo Tree Search (used by AlphaGo) explores the outcome tree by
**sampling** rather than enumerating. It balances exploration (try
unexplored branches) vs exploitation (deepen promising ones) via the UCB
formula. It converges on the optimal path without visiting most of the tree.

**Applied to LLM agents:** LATS (Language Agent Tree Search, ICML 2024,
650 citations) unifies reasoning, acting, and planning by treating each
LLM thought + action as a tree node. The LLM generates candidate actions,
self-evaluates them, and uses MCTS to decide which path to explore. SWE-
Search (152 citations) applies this to software engineering — multiple
agents explore different solution paths and backtrack from dead ends.

## Part 2: What skills, repos, and tools exist?

### Our environment (Grok Build)

| Capability | Skill/Tool | Status |
|---|---|---|
| Pre-mortem | `/risk` (pre-mortem specialist), `/tp` (domain 3a) | ✅ Strong — multiple skills |
| Steelman + falsifier | `/tp`, `/design` (critical friend) | ✅ Strong |
| Disconfirmation | `/www` Round 3 (mandatory) | ✅ Strong |
| Adversarial review | `/risk` (8 specialist lenses) | ✅ Strong |
| Content discipline under uncertainty | `/wargame` | ✅ Present |
| Decision tree (SDLC) | `decision-tree` (cc-skills-architect, in catalog) | ⚠ In catalog, not loaded in Grok Build |
| FMEA | — | ❌ Missing |
| Sensitivity analysis | — | ❌ Missing |
| MCTS / LATS | — | ❌ Missing |
| Monte Carlo simulation | — | ❌ Missing |
| Formal verification (TLA+/Alloy) | — | ❌ Missing |
| Outcome-space visualization | — | ❌ Missing |

### Claude marketplace / community skills

| Skill | What it does | Source |
|---|---|---|
| **FMEA Risk Analysis** | Claude performs structured FMEA with severity × occurrence × detection scoring | [mcpmarket.com](https://mcpmarket.com/tools/skills/fmea-risk-analysis-1) |
| **Scenario War Room** | Cascading risk modeling, what-if analysis, risk scenarios for complex decisions | [claudedirectory.org](https://www.claudedirectory.org/skills/claude-skills-scenario-war-room) |
| **creating-financial-models** | DCF, sensitivity testing, Monte Carlo simulations, scenario planning | [awesomeskill.ai](https://awesomeskill.ai/skill/claude-creating-financial-models) |
| **scenario-planner** | What-if analysis for construction projects (cost/schedule/resource impacts) | [claudeskills.info](https://claudeskills.info/skills/datadrivenconstruction/ddc_skills_for_ai_agents_in_construction/scenario-planner/) |
| **cc-thinking-skills** | 28 mental-model and critical-thinking frameworks for Claude Code | [github.com/tjboudreaux](https://github.com/tjboudreaux/cc-thinking-skills) |
| **decision-tree** | SDLC decision engine for architecture, incidents, refactors, migrations | cc-skills-architect (in our catalog) |

### Internet repos (research-grade)

| Repo | What it does | Citations | Link |
|---|---|---|---|
| **LATS** (Language Agent Tree Search) | MCTS + LLM reasoning/acting/planning; unifies all three in one framework | 650 (ICML 2024) | [github.com/lapisrocks/LanguageAgentTreeSearch](https://github.com/lapisrocks/LanguageAgentTreeSearch) |
| **Tree of Thoughts (ToT)** | Deliberate problem solving via tree search over reasoning paths; self-evaluates branches | 7,900 (NeurIPS 2023) | [github.com/kyegomez/tree-of-thoughts](https://github.com/kyegomez/tree-of-thoughts) |
| **SWE-Search** | MCTS for software engineering tasks; multiple agents explore solution paths | 152 (2025) | [openreview.net/forum?id=G7sIFXugTX](https://openreview.net/forum?id=G7sIFXugTX) |
| **LightZero** | MCTS + deep RL unified toolkit (AlphaZero, MuZero, EfficientZero) | NeurIPS 2023 Spotlight | [github.com/opendilab/LightZero](https://github.com/opendilab/LightZero) |
| **LLMRiskAnalyzer** | FMEA framework specifically for LLM systems | — | [github.com/YuchenXia/LLMRiskAnalyzer](https://github.com/YuchenXia/LLMRiskAnalyzer) |
| **kg-rag-fmea** | Knowledge-graph RAG for FMEA during product ramp-up | — | [github.com/lukasbahr/kg-rag-fmea](https://github.com/lukasbahr/kg-rag-fmea) |
| **awesome-mcts-papers** | Curated list of MCTS papers with implementations | — | [github.com/benedekrozemberczki/awesome-monte-carlo-tree-search-papers](https://github.com/benedekrozemberczki/awesome-monte-carlo-tree-search-papers) |

### Commercial platforms

| Platform | What it does | Link |
|---|---|---|
| **Naboo** (Decision Graph) | Models decisions as first-class nodes (owner, trigger, blockers, evidence); live joins across enterprise systems | [naboo.ai](https://www.naboo.ai/how-to-build-a-decision-graph/) |
| **Dovient** (AI FMEA Generator) | Generates structured FMEA from equipment data and failure history | [dovient.com](https://dovient.com/learning/ai-generated-fmea-explained) |

## What professionals actually do

| Profession | Primary method | Why that method |
|---|---|---|
| Decision analysis consultants (SRI/Stanford) | Influence diagrams + decision trees + Monte Carlo | Auditable, handles uncertainty, proven in high-stakes |
| Scenario planners (Shell, GBN) | 3-5 narrative futures + cross-impact analysis | When future is fundamentally uncertain (not probabilistic) |
| Systems/safety engineers | FMEA, HAZOP, fault tree analysis | Systematic component-level failure enumeration |
| Formal methods engineers (Amazon, Microsoft) | TLA+, Alloy, SPIN model checking | When correctness is critical (distributed protocols) |
| AI planning researchers | MDPs, POMDPs, MCTS | Autonomous planning under uncertainty |
| DevOps/SRE | Game days, chaos engineering, fault injection | Empirical: inject failures, observe response |

## Receipts

- **LATS (650 citations):** verified via [arxiv.org/abs/2310.04406](https://arxiv.org/abs/2310.04406)
  and [ICML 2024 proceedings](https://openreview.net/forum?id=6LNTSrJjBe). Official
  repo: [github.com/lapisrocks/LanguageAgentTreeSearch](https://github.com/lapisrocks/LanguageAgentTreeSearch).
- **ToT (7900 citations):** verified via
  [NeurIPS 2023 proceedings](https://openreview.net/forum?id=5Xc1ecxO1h). Plug-and-play
  implementation: [github.com/kyegomez/tree-of-thoughts](https://github.com/kyegomez/tree-of-thoughts).
- **FMEA Claude skill:** verified at
  [mcpmarket.com/tools/skills/fmea-risk-analysis-1](https://mcpmarket.com/tools/skills/fmea-risk-analysis-1).
- **Scenario War Room:** verified at
  [claudedirectory.org](https://www.claudedirectory.org/skills/claude-skills-scenario-war-room).
- **cc-thinking-skills (28 frameworks):** verified at
  [github.com/tjboudreaux/cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills).
- **Our skill coverage:** verified by scanning all SKILL.md files in
  `.agents/skills/`, `~/.grok/skills/`, and `~/.grok/bundled/skills/` for
  decision-analysis keywords. Only pre-mortem matched (3 skills).

## What this means for our workspace

- **The informal layer is strong** (pre-mortem in `/risk` + `/tp` +
  `/wargame`; disconfirmation in `/www`; steelman in `/tp`). Don't add more
  of the same — the literature says layer different techniques, not stack
  copies.
- **FMEA is the highest-value gap.** It's the structured component-level
  failure enumeration that pre-mortem's narrative frame misses. A Claude
  marketplace skill already exists ([FMEA Risk Analysis](https://mcpmarket.com/tools/skills/fmea-risk-analysis-1));
  evaluate it before building our own.
- **Sensitivity analysis is the second gap.** We have 7 pipeline parameters
  with no measured impact on output. A parameter sweep on the pilot notebook
  would tell us which actually matter.
- **MCTS/LATS is research-grade, not production-ready for our use case.**
  LATS requires a reward function, a world model, and significant compute.
  Our decisions are low-frequency (a few per session) and reversible (git).
  MCTS shines in high-frequency, irreversible decisions (game moves, robot
  control). Defer unless we build an autonomous orchestration layer.
- **The `cc-thinking-skills` repo (28 mental models)** is worth evaluating
  — it may contain frameworks we don't have (second-order thinking,
  inversion, probabilistic thinking) that are more applicable to our
  decision volume than full MCTS.

## Falsifier

- The informal layer (pre-mortem + steelman + disconfirmation) may be
  sufficient for our decision volume and reversibility profile. If blind
  spots don't recur across the next 6 months, FMEA/sensitivity analysis
  are unnecessary overhead. Testable: track unresolved blind spots in AARs.
- LATS/MCTS may be overkill for our use case. Our decisions are
  human-in-the-loop with operator judgment — the agent doesn't need to
  autonomously converge on optimal; it needs to surface the right
  alternatives and let the operator decide. Testable: identify one decision
  where MCTS would have produced a materially different outcome than
  pre-mortem + steelman.
- The Claude marketplace FMEA skill may not fit our workspace's enforcement
  model (we use hooks + validators, not chat-only skills). Evaluate before
  adopting.

## Sources

- [LATS: Language Agent Tree Search](https://arxiv.org/abs/2310.04406) (Zhou et al., ICML 2024, 650 citations) — MCTS + LLM reasoning/acting/planning
- [Tree of Thoughts](https://openreview.net/forum?id=5Xc1ecxO1h) (Yao et al., NeurIPS 2023, 7900 citations) — deliberate tree search over reasoning paths
- [SWE-Search](https://openreview.net/forum?id=G7sIFXugTX) (Antoniades et al., 2025, 152 citations) — MCTS for software engineering
- [LightZero](https://github.com/opendilab/LightZero) (NeurIPS 2023 Spotlight) — MCTS + deep RL toolkit
- [FMEA Risk Analysis skill](https://mcpmarket.com/tools/skills/fmea-risk-analysis-1) — Claude Code skill for structured FMEA
- [Scenario War Room](https://www.claudedirectory.org/skills/claude-skills-scenario-war-room) — cascading risk modeling
- [cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills) — 28 mental model frameworks
- [Naboo Decision Graph](https://www.naboo.ai/how-to-build-a-decision-graph/) (Jun 2026) — decisions as first-class graph nodes
- [LLMRiskAnalyzer](https://github.com/YuchenXia/LLMRiskAnalyzer) — FMEA for LLM systems
- [awesome-mcts-papers](https://github.com/benedekrozemberczki/awesome-monte-carlo-tree-search-papers) — curated MCTS implementations
- `P:/.data/wiki/concepts/blind-spot-detection-methods.md` — pre-mortem + RCF + ACH coverage
- `P:/.data/wiki/concepts/cognitive-enforcement-patterns-for-ai-coding-agents.md` — pre-mortem protocol in AI agents

## Auto-related

- [[blind-spot-detection-methods]] — five techniques for detecting cognitive blind spots (pre-mortem, devil's advocate, RCF, bias awareness, ACH)
- [[cognitive-enforcement-patterns-for-ai-coding-agents]] — pre-mortem as a structural enforcement pattern
- [[mental-models-for-tp-and-brainstorming]] — critical friend, double diamond, pre-mortem as mental models
- [[skill-domain-map]] — which SDLC domains we cover and which are weak
- [[stateful-skills-need-maintenance-surface]] — maintenance as systematic failure detection

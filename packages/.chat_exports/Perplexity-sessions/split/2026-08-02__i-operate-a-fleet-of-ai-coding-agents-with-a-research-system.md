---
title: "I operate a fleet of AI coding agents with a research system of 3 skills:1. /wiki: persistent knowledge base (800+ markd"
date: "2026-08-02"
mode: "COPILOT"
uuid: "6d0d4cba-c7d2-4a2b-b30f-ff123402075d"
entry_count: 1
---

## Human

I operate a fleet of AI coding agents with a research system of 3 skills:1. /wiki: persistent knowledge base (800+ markdown concepts, auto-linking, lint, validation, write-time gap detection)2. /web: multi-backend web search (DDG+MiniMax+Firecrawl+Exa, RRF merge, source scoring, cross-search pattern notes)3. /www: orchestrator chaining wiki→web→wiki (research gaps, disconfirm findings, persist knowledge, post-research suggestions, cross-session thread tracking)Recent improvements: proactive research suggestions after every run, tool-failure lifecycle management, gap-as-signal disconfirmation.Question: What 3 ideas would make this system genuinely better? Define better however you want. Focus on structurally novel ideas, not incremental tweaks.[ref: A3F2B9E1]

## Assistant

Three structurally novel ideas would make your system materially better: add a **belief ledger** that tracks claims as evolving objects rather than static notes, build a **research market** that allocates search/verification budget by expected information gain, and create an **adversarial replay harness** that turns failures and near-misses into standing counterfactual tests. These are not “better prompting” or “better ranking” tweaks; they change the system’s internal economics, memory model, and learning loop.[1][2][3][4][5]

## 1) Belief ledger

Right now your wiki sounds strong at storing concepts, links, and gaps, but the next step is to store **belief states**: each important claim should have provenance, time validity, confidence, supporting evidence, disconfirming evidence, and a revision history rather than collapsing into one “best current note.” Graph-based agent memory research points toward structured memory that separates semantic, temporal, causal, and entity relations, and temporally aware memory systems like Zep/Graphiti show why this matters for cross-session synthesis and change tracking.[2][6][1]

The novel part is to make `/wiki` less like a polished notebook and more like a lightweight epistemic database. A claim node might look like: “X is true,” linked to source observations, contradiction edges, expiry heuristics, and “last challenged” timestamps; then `/www` would not just persist findings, it would perform **belief revision** when new evidence arrives. This directly supports your “gap-as-signal disconfirmation” idea, because unresolved contradiction becomes a first-class object rather than a side effect in prose.[7][8][1]

Why this is genuinely better:
- It reduces silent knowledge drift, especially for fast-changing topics.[2][7]
- It lets the system answer “what changed, why did we believe it, and what would falsify it now?” instead of only “what do we know?”[8][2]
- It makes thread tracking more useful, because threads become trajectories of belief revision, not just histories of documents.[6][1]

Concrete design:
- Claim object: `claim`, `scope`, `status`, `confidence`, `valid_from`, `valid_until`, `supersedes`, `supported_by`, `challenged_by`, `depends_on`.
- Evidence object: source metadata plus extraction span, authority score, freshness score, and whether it is direct or second-hand.
- Revision rules: auto-downgrade confidence when evidence ages out, source authority drops, or contradictions accumulate.
- Query mode: retrieve by “highest-confidence current belief,” “most-contested claim,” or “beliefs needing revalidation.”

FACT: graph-based memory literature explicitly emphasizes extraction, storage, retrieval, and evolution as separate lifecycle stages.[1]
CONSENSUS: temporality and relation structure are important for long-horizon agents.[6][1][2]
SPECULATION, high confidence: this would outperform plain markdown memory for research agents because your bottleneck is likely no longer storage volume, but belief maintenance.

## 2) Research market

Your orchestrator currently chains wiki \(\rightarrow\) web \(\rightarrow\) wiki, which is good procedural structure, but it still sounds like a pipeline. A stronger architecture is a **market-based planner** where candidate actions compete for budget based on expected information gain: search a new source, re-query a weak claim, seek a disconfirming source, inspect a stale wiki node, or stop because marginal value is low. Information-gain work in retrieval and active learning both support the idea that the next action should be chosen by expected uncertainty reduction, not by a fixed sequence.[9][5]

The novel part is not just “score results better,” but to treat every research step as an investment decision under uncertainty. Each candidate action gets a predicted payoff such as: expected reduction in claim entropy, expected citation value, expected contradiction resolution, expected freshness gain, and expected cost in tokens/time/tool risk. Deep-research benchmarks also show that quality is multi-dimensional, especially citation accuracy and effective citations, so the market should optimize for evidence quality, not only answer coverage.[4][10][11]

Why this is genuinely better:
- It prevents over-searching obvious areas while under-investigating fragile claims.[5][4]
- It gives you a principled stopping rule: stop when no action has enough expected value.
- It turns “proactive suggestions after every run” into ranked research opportunities with explicit payoff estimates.

Concrete design:
- Define action types: `expand`, `verify`, `disconfirm`, `refresh`, `synthesize`, `stop`.
- Compute per-action utility:
  \[
  U(a) = \alpha(\Delta \text{uncertainty}) + \beta(\Delta \text{citation quality}) + \gamma(\Delta \text{coverage}) - \lambda(\text{cost}) - \mu(\text{tool risk})
  \]
- Let the orchestrator run a small auction each cycle; the top action wins budget.
- Add portfolio constraints, for example at least one disconfirming action if confidence exceeds a threshold without source diversity.
- Expose system diagnostics: “we did not browse further because expected gain was below threshold.”

This pairs naturally with your existing source scoring and RRF merge. Instead of using those mainly at ranking time, use them in **decision time** to choose the next kind of evidence to acquire.[11][4][5]

FACT: DeepResearch Bench evaluates citation accuracy and effective citations as separate dimensions, which means “more retrieved information” and “better grounded information” are not the same thing.[4][11]
SPECULATION, high confidence: a research market would be one of the highest-leverage changes because your system already has multiple backends, cross-search notes, and gap signals; what it likely lacks is a stronger budget allocator.

## 3) Adversarial replay harness

Your system already does disconfirmation during live runs. The next structural leap is to build a **standing adversarial replay harness** that continuously re-runs past research traces against mutated conditions: missing authoritative sources, injected low-quality corroboration, stale wiki priors, poisoned tool descriptions, contradictory evidence orderings, and tasks reframed as bug-finding rather than verification. Research on agentic uncertainty shows adversarial framing can reduce overconfidence and improve calibration, while provenance-focused work argues that factual support alone is insufficient if attribution is wrong.[3][12]

The novel part is to treat every completed `/www` run as a reusable test asset. Instead of only persisting knowledge, persist the trace, decision points, skipped alternatives, uncertainty estimates, and final claims; then automatically generate “counterfactual replays” such as:
- What would the system conclude if its top source vanished?
- Would it still make the same claim if evidence arrived in reverse order?
- Would it incorrectly merge two similar entities?
- Would it cite pooled evidence from the wrong source?
- Would confidence remain too high after tool failures?

Why this is genuinely better:
- It converts one-off production experience into a permanent red-team dataset.
- It attacks the hardest failure mode in research systems: plausible but misattributed or under-challenged synthesis.[13][12][14]
- It gives you a path to measurable improvement via calibration and provenance, not just anecdotal “seems smarter.”

Concrete design:
- Persist trace artifacts: query plan, retrieved docs, claim graph deltas, confidence snapshots, final report.
- Generate perturbations: source removal, source swap, stale snapshot, injected contradiction, authority inversion, MCP/tool poisoning simulations.
- Score replays on:
  - Calibration: did confidence match actual robustness?[3]
  - Attribution accuracy: was each claim tied to the correct source, not merely some supporting source?[12]
  - Recovery behavior: did the system degrade gracefully under tool failures and evidence loss?
- Feed failures back into `/wiki` as “known reasoning hazards,” not just factual corrections.

This is especially relevant because current deep-research systems are reported to struggle with confidence calibration and source authority discrimination, even when they are otherwise strong at synthesis.  If your system becomes unusually good at knowing when it is brittle, that is a real moat.[14][13]

## Priority order

If I were optimizing for real-world impact rather than novelty alone, I would implement them in this order:

| Idea | Why first | Main upside | Main risk |
|---|---|---|---|
| Belief ledger | It upgrades memory and makes every later improvement more coherent. [1][2] | Better change tracking, contradiction handling, cross-session reasoning. [1][6] | More schema and maintenance complexity. |
| Adversarial replay harness | Fastest route to measurable truthfulness gains. [3][12] | Better calibration, provenance discipline, robust failure learning. [3][13] | Requires good trace capture and evaluation design. |
| Research market | Highest upside once the first two exist. [4][5] | Smarter budget allocation, principled stopping, less wasted search. [4][11] | Utility function can be gamed or misweighted early. |

My strongest recommendation is this: make `/wiki` store **beliefs under revision**, make `/www` allocate effort by **expected information gain**, and make every run become a **future adversarial test**. Together, those three changes turn your stack from a capable research workflow into a self-improving epistemic system.[5][1][3][4]

Would you like me to turn these into a concrete architecture spec with data models, scoring formulas, and agent handoff contracts?

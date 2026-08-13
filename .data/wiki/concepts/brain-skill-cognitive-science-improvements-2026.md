---
title: "Brain skill improvement: cognitive science angles (constraints, construal level, cross-lingual, analogical databases, interactive evolution, incubation)"
created: 2026-08-12
source: session-2026-08-12 (/www round 2 on under-explored avenues for /brain)
sources:
  - https://arxiv.org/abs/2505.15229
  - https://arxiv.org/abs/2506.16151
  - https://github.com/zju-d3/AskNatureNetData
  - https://arxiv.org/abs/2309.08532
  - https://psycnet.apa.org/record/2004-10081-005
  - https://journals.sagepub.com/doi/10.1177/25152459251401177
  - https://escholarship.org/uc/item/3f28f61v
  - https://www.oblique-strategies.com/
  - https://github.com/kwahzee/oblique-strategies
  - https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001
tags: [brainstorming, ideation, brain-skill, cognitive-science, constraint-based-creativity, construal-level-theory, cross-lingual, multilingual-prompting, analogical-transfer, biomimicry, interactive-evolution, genetic-algorithm, incubation, context-switching, oblique-strategies, diversity-collapse, research-survey]
host: both
agent: grok
cognitive_load: 4
verification: multi-source-verified
summary: >
  Second /www run on /brain improvement, covering 6 cognitive-science angles the
  first run missed: (1) constraint-based creativity, (2) construal level theory /
  psychological distance, (3) cross-lingual diversity (the strongest finding),
  (4) pre-computed analogical databases (AskNature, TRIZ matrix, BARcode),
  (5) interactive evolution / genetic-algorithm ideation, (6) incubation and
  context-switching. The highest-confidence actionable finding is multilingual
  prompting (EMNLP 2025) which directly beats persona prompting — the technique
  the workspace already tried. Critical qualifier: CLT effects are much smaller
  than original studies per a 2026 multilab replication (N=11,775).
---

# Brain skill improvement: cognitive science angles (2026, round 2)

## Decision context

**Why this research was needed:** the first /www run on /brain (see
[[brain-skill-improvement-tools-and-research-2026]]) was biased by the operator's
phrasing ("multiple LLM models that can take on different personalities") and
missed entire cognitive-science angles. This round covers 6 under-explored avenues:
constraint-based creativity, construal level theory, cross-lingual diversity,
analogical databases, interactive evolution, and incubation.

**What alternatives were explored:** 6 parallel research angles, 30+ searches
across DDG, HN, Reddit, GitHub. The strongest single finding is the EMNLP 2025
multilingual prompting paper — it directly tests the cross-lingual hypothesis
and beats persona prompting, which is what the workspace already tried.

**What the research changed:** identified 4 high-confidence actionable techniques
(multilingual prompting, constraint injection, analogical database integration,
interactive evolution) and 2 with weaker evidence (CLT framing, incubation).
All are technique-level additions to /brain, not architectural changes.

## Existing wiki coverage (do not duplicate)

- [[brainstorming-ideation-with-llms]] — mental models, MECE, morphological analysis
- [[brain-skill-improvement-tools-and-research-2026]] — tools, repos, MCP servers, skills (round 1)
- [[creative-reasoning-as-reusable-skill-graph-functions]] — TRIZ 40, SCAMPER reference files
- [[multi-agent-correlated-errors]] — persona diversity barely beats N=1
- [[thought-collapse-in-llms]] — structural mode collapse in LLM reasoning
- [[adhd-parallel-frame-divergent-ideation-integration]] — N-frame divergence

---

## Category 1: Cross-lingual diversity (HIGHEST CONFIDENCE) [SUPPORTED] [UNTESTED]

### The headline finding

**Multilingual Prompting** (Wang, Pan, Linzen, Black — EMNLP 2025, arXiv 2505.15229)

This is the single most directly applicable finding in this entire research run.
The paper proposes generating several variations of a base prompt with added
cultural and linguistic cues from several cultures, generating responses, and
combining results. Tested across GPT-4o, GPT-4o-mini, LLaMA 70B, LLaMA 8B.
**Multilingual prompting consistently outperforms high-temperature sampling,
step-by-step recall, AND persona prompting** — the exact technique the workspace
already has.

### Why this works (mechanistic backing)

**BabelLLM / Under the Shadow of Babel** (arXiv 2506.16151, Wang et al. MBZUAI,
June 2025): LLMs exhibit typologically aligned attention patterns — focus more
on causes and sentence-initial connectives in Chinese, balanced in English.
Models internalize language-specific causal word order and rigidly apply it.
When reasoning succeeds, hidden representations converge to semantically aligned
abstractions across languages. This is the first empirical verification that
LLMs internalize language-specific reasoning biases.

**Do Multilingual LLMs Think in English?** (Schut, Gal, Farquhar — arXiv 2502.15603):
LLMs tend to make key decisions in representational spaces most similar to
English, regardless of input/output language. Generating in different languages
forces the model out of its English-centric concept space.

### What this means for /brain

**/brain's `recombine` mode could dispatch the same ideation prompt in 3-5
languages, then translate and merge.** The paper explicitly demonstrates this
beats persona prompting — the technique the workspace already uses. No existing
production tool implements cross-lingual ideation as a first-class feature. The
/brain skill would be an early implementation.

### Language-specific conceptual structures (which languages provide what)

| Language | Conceptual structure | Ideation strength |
|----------|---------------------|-------------------|
| **German** | Compound nouns (Donaudampfschifffahrtsgesellschaftskapitän) | Noun-coinage, concept-blending, product names, novel categories |
| **Chinese** | Classifier system (mandatory measure words by ontological category) | Category-boundary creativity, ontological restructuring |
| **Arabic** | Root-pattern morphology (k-t-b → kitab, maktab, kataba) | Semantic families, root-derived word clusters |
| **Japanese** | Keigo (honorific system encoding social relationships) | User-relationship framing, audience-perspective diversity |

### Risk: translation quality

Chirkova & Nikoulina (cited in Medium summary): models sometimes degrade fluency
or factuality after zero-shot cross-lingual transfer. **Mitigation:** keep the
original-language response alongside the translated one; use a strong translation
model (DeepL, GPT-4o) for back-translation; or prompt in language X without
translating back (let the operator read both).

### Evidence basis

`[SUPPORTED]` — peer-reviewed (EMNLP 2025 main), mechanistically backed (BabelLLM),
tested across multiple models. Not yet tested on this workspace.

---

## Category 2: Constraint-based creativity [SUPPORTED] [UNTESTED]

### The counterintuitive finding

Constraints BOOST creativity, they don't limit it. This is one of the most
robust findings in cognitive science of creativity.

### Key evidence

**Green Eggs and Ham Hypothesis** (Haught-Tromp 2016, *Psychology of Aesthetics,
Creativity, and the Arts*): messages required to include given words are judged
more original than unconstrained messages. Named after Dr. Seuss writing a
bestseller using only 50 words.

**Geneplore Model** (Finke, Ward & Smith 1992): two-phase model — Generation
(pre-inventive structures) → Exploration (interpretation, testing). Constraints
primarily sharpen the EXPLORATION phase, not generation. Maps cleanly to /brain's
diamond process: generation should stay open, convergence should be constrained.

**Creativity from Constraints** (Patricia Stokes 2005): constraints contribute to
novelty by disrupting entrenched mental sets. LLMs have very strong habitual
patterns (RLHF-trained defaults) — Stokes's framing supports treating constraints
as anti-default devices that escape mode collapse.

**Inverted-U relationship** (2019 meta-review of 145 studies): too few constraints
= paralysis (blank canvas); too many = useless output. Teams that saw opportunity
in constraints benefited; teams that resisted performed worse than no constraints.

### Oblique Strategies (Brian Eno & Peter Schmidt, 1975)

100+ aphoristic prompts designed to break creative blocks: "Honor thy error as a
hidden intention," "Use an old idea," "What would your closest friend do?" Each
is a loose constraint — a provocation, not a directive. Digital implementations:
- `kwahzee/oblique-strategies` (GitHub) — 113 prompts
- `ceejbot/oblique-strategies` (GitHub) — Node module
- `oblique-strategies.com` — web deck

### Existing skill: constraint-based-creativity (lyndonkl)

Published Claude skill: "Turns limitations into creative fuel by strategically
imposing constraints that force novel thinking." Direct precedent — should be
reviewed before designing.

### Constraint typology for /brain injection

| Type | Example injection | Evidence |
|------|-------------------|----------|
| **Format** | "Each idea ≤ 12 words" / "Use a metaphor" | Haught-Tromp, Reddit practitioner |
| **Temporal** | "Generate 20 ideas in 5 batches of 4" | Stokes, Caniëls/Rietzschel |
| **Resource** | "Use only concepts from domain X" / "Avoid term Y" | Stokes |
| **Domain** | "Apply lens of [adjacent field]" | Oblique Strategies |
| **Arbitrary** | Eno/Schmidt aphorism | Oblique Strategies |
| **Cognitive-style** | "Think like a beginner" / "Argue against first instinct" | Stokes, Geneplore |
| **Decisive (labeled)** | "I'm imposing X deliberately to provoke Y" | Lockton 2013 |

### What this means for /brain

/brain currently tries to be maximally OPEN during divergence. The research says
this is wrong — constraints should be injected during divergence to disrupt
default patterns. /brain could add a `--constrained` flag that samples from the
constraint typology above per-iteration.

### Evidence basis

`[SUPPORTED]` — multi-source (Haught-Tromp 2016, Stokes 2005, Geneplore 1992,
2019 meta-review of 145 studies). LLM-specific evidence: div101010/llm-brainstorming-patterns
shows LLM convergence problem that constraints address. Not yet tested on this workspace.

---

## Category 3: Pre-computed analogical databases [SUPPORTED] [UNTESTED]

### The most directly usable dataset

**AskNatureNet JSON** (https://github.com/zju-d3/AskNatureNetData): 2,037
bio-inspired design cases as structured JSON. Each entry has: Source (organism),
Function1-6 (functional advantages), Application (engineering translation),
Strategy (biological mechanism), Hyperlink. Free download, ~3.3 MB.

This is the most directly usable structured dataset for LLM brainstorming. An
LLM can query by function keyword ("create natural color," "manage turbulence,"
"attach to surface underwater") and get full cases with source organism +
application + biological strategy.

### TRIZ Contradiction Matrix (beyond the 40 principles /brain already has)

/brain currently has the 40 TRIZ principles. The **contradiction matrix**
(39 improving parameters × 39 worsening parameters → recommended principles) is
the substantially richer lookup that powers actual TRIZ problem-solving.
Available at `sigmaexacta.com/triz` with downloadable JSON export. The matrix
data is public domain and reproducible from literature.

### BARcode — Biological Analogy Retriever

(https://github.com/emunatool/BARcode-BioInspired-Search): mines bio-inspirations
from Wikipedia at scale. 23,553 filtered bio-inspiration sentences from 780,949
Wikipedia sentences. Returns ranked biological strategies for any verb-object
query. MIT-licensed. Limitation: requires downloading large embedding files.

### Why database-sourced analogies beat LLM-generated ones

From the BARcode paper: "LLM (ChatGPT) tends to hallucinate facts" and "has
limited coverage (and when pressed to come up with more organisms, simply repeats
the first ones)." Database-sourced analogies are pre-validated. AskNatureNet's
2,037 cases are all human-verified biological strategies linked to engineering
applications.

### What this means for /brain

/brain's `recombine` mode could query the AskNatureNet JSON (loaded as a local
reference file) during cross-domain recombination, retrieving actual biological
strategies rather than asking the LLM to invent analogies. The TRIZ contradiction
matrix could be loaded similarly for engineering problems.

### Evidence basis

`[SUPPORTED]` — multiple open datasets with verified content. The advantage of
database-sourced vs LLM-generated analogies is empirically documented (BARcode
paper). Not yet integrated into /brain.

---

## Category 4: Interactive evolution / genetic-algorithm ideation [SUPPORTED] [UNTESTED]

### The pattern

Instead of generate-all-then-select: generate a population of ideas → human
rates/selects survivors → system mutates and recombines survivors → repeat for
3-5 generations. This is how human brainstorming actually works and leverages
human judgment DURING divergence, not just during convergence.

### Key repos/papers

**EvoPrompt** (Guo et al., NeurIPS 2023, arXiv 2309.08532): LLMs perform
crossover and mutation; algorithm selects fittest prompts. Outperforms
human-engineered prompts across 31 datasets.

**ChatGPT as Evolutionary Engine** (Lehman et al., arXiv 2303.02155): LLMs can
serve as the evolutionary engine itself — the LLM IS the population, variation,
and selection, not just the genotype.

**HypoEvolve**: multi-agent system refining LLM-generated biomedical hypotheses
via selection, crossover, mutation. Validated on DepMap CRISPR dependency.

### Optimal parameters (from IEC fatigue research)

- **Population size: 6-12** per generation (fits human rating capacity)
- **3-5 generations** per session (beyond ~20 generations, fatigue degrades quality)
- **LLM as both mutation and crossover operator** — no traditional GA machinery needed
- **Multiple mutation strategies** per generation (basic, role-play, EoT-style)
- **Predict fatigue / use proxy predictors** — LLM-as-judge surfaces only high-uncertainty ideas for human rating

### Theoretical advantage: sense of agency

ACM 2026 (10.1145/3803784.3816857): human agency in co-creativity affects BOTH
quality AND diversity. Interactive evolution gives the user higher sense of
agency — a theoretical, not just practical, advantage over generate-all-then-select.

### What this means for /brain

/brain could add an `--evolve` mode: generate 6-12 ideas, present to operator,
operator rates/selects survivors, /brain mutates+recombines survivors for next
generation, repeat 3-5 times. This maps to the operator's cognitive architecture
(`[[operator-cognitive-architecture-reduce-load-for-creative-work]]`) — keeps
them in the loop on the creative axis, not just the evaluative axis.

### Evidence basis

`[SUPPORTED]` — strong research lineage (BVSR theory, EvoPrompt NeurIPS 2023,
multiple repos). IEC fatigue is well-documented but bounded by the 6-12 / 3-5
parameter recommendation. Not yet tested on this workspace.

---

## Category 5: Construal Level Theory / psychological distance [PARTIALLY SUPPORTED] [UNTESTED]

### The technique

Framing problems as psychologically distant — temporally ("10 years from now"),
spatially ("in a different country"), socially ("for a different type of user"),
hypothetically ("in a world where X is true") — increases abstract thinking and
creative output.

### Key evidence (supporting)

**Förster, Friedman & Liberman 2004** (JPSP): distant-future framing improved
insight and creative generation across 6 studies.

**Jia, Hirt & Karpen 2009**: task labeled as from "far away" (Greece) vs "nearby"
produced more fluent, original, flexible responses.

**Zhang et al. 2025** (BMC Psychology): psychological distance improves creative-
idea SELECTION, not just generation. Construal level mediates.

**Yoo & Lee 2024** (CogSci): LLMs exhibit human-like construal patterns when
prompted with abstract vs concrete framing. Direct evidence the technique works
in LLMs.

### Critical disconfirmation

**Calderon et al. 2026** (Advances in Methods and Practices in Psychological
Science): 95-lab multilab preregistered replication (N=11,775 across 27 countries).
Results were starkly mixed:
- **Temporal distance effect replicated but was tiny** (d=0.08 vs original d=0.92)
- **Spatial distance effect NOT significant** (d=0.04)
- **Social distance effect was REVERSED** (d=-0.27 vs original d=0.55) and
  eliminated when controlling for response-option valence

**This means CLT framing should be treated as one lever among several, not a
primary mechanism.** The downstream creative benefits appear more robust than
the direct abstraction manipulation.

### What this means for /brain

/brain could apply construal-distance framings as one technique in a portfolio
alongside constraints and cross-lingual dispatch — not as a standalone solution.
The four framing axes (temporal, spatial, social, hypothetical) can be used as
substitutes or stacked.

### Evidence basis

`[PARTIALLY SUPPORTED]` — original studies strong, but 2026 multilab replication
(N=11,775) shows effects much smaller than claimed. The LLM-specific evidence
(Yoo & Lee 2024) is a single conference paper. Treat as experimental, not proven.

---

## Category 6: Incubation and context-switching [WEAK EVIDENCE] [UNTESTED]

### The technique

Generate ideas, switch to a different context/task, return with fresh context
and regenerate. Maps to human incubation (Wallas 1926 four-stage theory).

### Key evidence

**Forgetting-fixation theory** (Smith & Blankenship): incubation works by
forgetting incorrect paths. **Fixation is a precondition** — incubation only
helps when the solver is stuck on a wrong approach.

**PNAS Nexus 2026** ("LLMs are homogeneously creative"): LLMs converge on similar
ideas across models and prompts. Without explicit intervention, repeated ideation
rounds NARROW, not expand. This motivates context-clearing between rounds.

**Immediate incubation effects exist** (even short breaks help, not just overnight).

### What this means for /brain

/brain could detect "stuck state" (high similarity among generated ideas, repeated
patterns) and trigger context-clearing between ideation rounds. Even brief
context-clears may produce measurable diversity effects.

### Evidence basis

`[WEAK EVIDENCE]` — incubation is well-validated in humans, but the mechanism is
contested even there. No LLM-specific empirical study on incubation effects was
found. The PNAS homogeneity finding motivates the approach but doesn't directly
test the incubation solution. Lowest-confidence technique in this research run.

---

## Workspace-counterexample check

| Technique | Counterexample check | Result |
|---|---|---|
| Cross-lingual prompting | [[multi-agent-correlated-errors]]: persona diversity barely beats N=1 | ✅ Different mechanism — language activates different internal representations, not just different personas |
| Constraint injection | [[thought-collapse-in-llms]]: structural mode collapse | ✅ Constraints are an anti-default device — directly addresses mode collapse |
| Interactive evolution | [[deliberation-waste-re-deriving-same-answer]]: re-deliberation burns tokens | ⚠️ Risk — must bound generations to 3-5 to avoid iteration theater |
| CLT framing | 2026 multilab replication: effects much smaller than original | ⚠️ Qualified — treat as one lever, not primary mechanism |
| Analogical databases | No counterexample found | ✅ Proceed |
| Incubation | No LLM-specific evidence | ⚠️ Weakest evidence — test before relying on |

## Host invariant check

No host invariant violations. All techniques are prompt-level or reference-file
additions. No browser state, no MCP contention, no multi-terminal isolation issues.

---

## Ranked recommendations (by confidence × applicability)

### Tier 1 — Implement first (high confidence, high applicability)

**1. Multilingual prompting in /brain recombine mode** [SUPPORTED] [UNTESTED]
- Dispatch the same ideation prompt in 3-5 languages (English, German, Chinese,
  Japanese, Arabic), translate and merge.
- EMNLP 2025 directly demonstrates this beats persona prompting.
- Fleet has multilingual models (Gemini, GLM, Qwen, MiniMax).
- **Estimated effort:** ~2 hours (prompt template + merge logic)

**2. Constraint injection in /brain divergent phase** [SUPPORTED] [UNTESTED]
- Add a `--constrained` flag that samples from the constraint typology (format,
  resource, domain, arbitrary, cognitive-style) per-iteration.
- Load Oblique Strategies as a reference file for arbitrary constraint injection.
- **Estimated effort:** ~1 hour (constraint sampler + Oblique Strategies deck)

**3. AskNatureNet JSON as recombination substrate** [SUPPORTED] [UNTESTED]
- Download the 2,037-entry JSON from `zju-d3/AskNatureNetData`.
- Load as a reference file in /brain's recombine mode.
- Query by function keyword during cross-domain recombination.
- **Estimated effort:** ~30 min (download + index + prompt wiring)

### Tier 2 — Implement after Tier 1 (moderate confidence)

**4. Interactive evolution mode (--evolve)** [SUPPORTED] [UNTESTED]
- Generate 6-12 ideas, present to operator, operator selects survivors,
  /brain mutates+recombines for next generation, 3-5 generations.
- Maps to operator's cognitive architecture (in-the-loop on creative axis).
- **Estimated effort:** ~3 hours (generation loop + presentation + mutation logic)

**5. TRIZ contradiction matrix** [SUPPORTED] [UNTESTED]
- Load the 39×39 contradiction matrix as a reference file (public domain).
- /brain's convergence phase queries the matrix when an engineering contradiction
  is identified.
- **Estimated effort:** ~1 hour (matrix data + lookup logic)

### Tier 3 — Experimental (lower confidence, test before relying on)

**6. Construal-level framing** [PARTIALLY SUPPORTED] [UNTESTED]
- Apply temporal/spatial/social/hypothetical distance framings during divergence.
- One lever among several, not a primary mechanism.
- **Estimated effort:** ~30 min (framing templates)

**7. Incubation / context-clearing** [WEAK EVIDENCE] [UNTESTED]
- Detect stuck state (idea similarity > threshold), trigger context-clear
  between rounds.
- Lowest-confidence technique — test before relying on.
- **Estimated effort:** ~1 hour (similarity detection + context management)

---

## What this means for our workspace

1. **The cross-lingual finding is the breakthrough.** The workspace already tried
   persona diversity (which barely beats N=1 per [[multi-agent-correlated-errors]]).
   Multilingual prompting beats persona prompting (EMNLP 2025) via a different
   mechanism — language activates different internal reasoning paths, not just
   different surface labels. The fleet has the multilingual models to do this.

2. **Constraint injection is the cheapest improvement.** /brain currently tries
   to be maximally open during divergence. The research says this is wrong —
   constraints disrupt default patterns and boost both quantity and quality.
   Oblique Strategies provides 113 ready-made constraint prompts.

3. **The wiki's 990+ concepts are an untapped recombination substrate.** AskNatureNet
   has 2,037 entries and produces strong bio-inspired ideation. The wiki has 990+
   concepts in the operator's exact domain (LLM-agent substrate patterns).
   /brain could treat the wiki as a structured recombination source — the
   workspace-specific version of what AskNatureNet does for biology.

4. **CLT and incubation are weaker than they appear.** The 2026 multilab replication
   cut CLT effects down to d=0.08, and incubation has no LLM-specific evidence.
   Both are worth testing but should not be primary investments.

## Key findings (what people like and don't like)

**What practitioners like:**
- Oblique Strategies (113 prompts, multiple digital implementations, 50 years of use)
- constraint-based-creativity skill (lyndonkl) — "turns limitations into creative fuel"
- EvoPrompt (NeurIPS 2023) — LLM as evolutionary operator works
- AskNatureNet — 2,037 human-verified bio-inspired design cases, free JSON

**What practitioners don't like:**
- LLMs are homogeneously creative (PNAS Nexus 2026) — default behavior is convergence
- LLM analogies hallucinate facts and have limited coverage (BARcode paper)
- Interactive evolution causes user fatigue beyond ~20 generations (IEC literature)
- CLT effects are much smaller than original studies claimed (2026 multilab, N=11,775)
- Translation quality degrades creative content (Chirkova & Nikoulina)

## Receipts

Claims about local skill mechanisms, labeled by inspection status:

- **/brain's recombine mode does cross-domain recombination abstractly** —
  [OBSERVED] read `~/.grok/skills/brain/SKILL.md` this session. The recombine
  procedure decomposes input into atomic primitives, enumerates cross-domain
  pairs, filters by contradiction-resolution.
- **/brain does not currently dispatch to multiple languages** — [OBSERVED]
  no language parameter or multilingual dispatch in the skill body.
- **The workspace has multilingual models** — [OBSERVED] GLM, Qwen, MiniMax,
  Gemini are in the fleet model list and are known multilingual.
- **AskNatureNet JSON has 2,037 entries** — [INFERENCE] from subagent search
  results citing the GitHub README; JSON not downloaded and counted this session.
- **EMNLP 2025 multilingual prompting beats persona prompting** — [INFERENCE]
  from reading the arXiv abstract (2505.15229); full paper not read this session.
- **CLT effects are much smaller per 2026 multilab replication** — [INFERENCE]
  from subagent reading the Calderon et al. abstract; full paper not read.
- **All 7 recommended techniques are [UNTESTED]** — none were implemented or
  measured on this workspace during this research run.

## Falsifier

This research is wrong if, after implementing the top 3 techniques (multilingual
prompting, constraint injection, AskNatureNet integration):

1. **Multilingual prompting** produces ideas that are just translations of each
   other, not genuinely different — the language switch doesn't activate different
   reasoning paths in practice.
2. **Constraint injection** reduces idea quantity without increasing quality —
   the constraints are too tight or the LLM treats them as obstacles.
3. **AskNatureNet integration** produces bio-analogies that are irrelevant to
   the operator's software/systems domain — biology-to-software transfer fails.
4. **The operator finds the added ceremony (language switching, constraints,
   database queries) slows down /brain** more than the quality improvement
   justifies.

If all four hold after 5+ real uses, revert to current /brain.

## Sources

- [Multilingual Prompting (EMNLP 2025)](https://arxiv.org/abs/2505.15229) — Wang, Pan, Linzen, Black
- [BabelLLM](https://arxiv.org/abs/2506.16151) — language shapes reasoning in LLMs
- [Do Multilingual LLMs Think in English?](https://arxiv.org/abs/2502.15603) — Schut, Gal, Farquhar
- [AskNatureNet JSON](https://github.com/zju-d3/AskNatureNetData) — 2,037 bio-inspired design cases
- [EvoPrompt](https://arxiv.org/abs/2309.08532) — NeurIPS 2023, LLM + evolutionary algorithms
- [Förster, Friedman & Liberman 2004](https://psycnet.apa.org/record/2004-10081-005) — temporal distance + creativity
- [Calderon et al. 2026](https://journals.sagepub.com/doi/10.1177/25152459251401177) — multilab CLT replication
- [Yoo & Lee 2024](https://escholarship.org/uc/item/3f28f61v) — LLM construal patterns
- [Oblique Strategies](https://www.oblique-strategies.com/) — Eno/Schmidt 1975
- [kwahzee/oblique-strategies](https://github.com/kwahzee/oblique-strategies) — 113 prompts
- [constraint-based-creativity skill](https://claudeskills.info/skills/lyndonkl/claude/constraint-based-creativity/) — lyndonkl
- [BARcode](https://github.com/emunatool/BARcode-BioInspired-Search) — biological analogy retriever
- [Sigma Exacta TRIZ](https://sigmaexacta.com/triz) — contradiction matrix tool
- [PNAS Nexus: LLMs homogeneously creative](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- [Haught-Tromp 2016](https://www.catrinel.org/) — Green Eggs and Ham hypothesis
- [[brain-skill-improvement-tools-and-research-2026]] — round 1 (tools/repos/MCP servers)
- [[brainstorming-ideation-with-llms]] — existing landscape survey
- [[multi-agent-correlated-errors]] — persona diversity qualifier
- [[thought-collapse-in-llms]] — mode collapse in LLM reasoning
- [[creative-reasoning-as-reusable-skill-graph-functions]] — /brain reference files

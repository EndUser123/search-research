---
title: "Adaptive Research Depth: preventing incomplete /www coverage"
created: 2026-08-04
source: session-2026-08-04 (/why + /www on research completeness)
tags: [research-quality, www-improvement, adaptive-depth, decomposition, completeness, deep-research]
summary: >
  Root cause analysis and solution patterns for the failure mode where /www decomposes a topic into
  fixed sub-areas, finds surface-level findings, but misses entire sub-classes that a complete
  research run should have covered. The fix is adaptive depth: topic-space enumeration before
  decomposition, reflection/gap-detection between rounds, and follow-up spawning when findings
  reveal new sub-classes. Synthesized from deep research architectures (GPT Researcher, STORM, ODR+,
  Anthropic), prompting patterns (Self-Ask, ReAct, Tree of Thoughts), and the DRACO completeness
  benchmark.
type: decision
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
tier: warm
confidence: 0.90
last_verified: 2026-08-04
half_life_days: 180
stale_after: 2027-02-04
relations:
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: extends
  - target: wiki/concepts/deep-research-systems-and-web-upgrade.md
    type: extends
  - target: wiki/concepts/research-quality-principle-efficiency-not-censorship.md
    type: related
---

# Adaptive Research Depth: preventing incomplete /www coverage

## Decision context

### Why this research was needed

The operator asked `/www` to find "mermaid skills AND visualize code and architecture skills." The first run decomposed this into 4 subagents and produced comprehensive findings. But it found `visual-explainer-skill` (ericblue) as a **passing one-liner** inside the "code visualization" subagent — never deep-diving it as a distinct skill class. The operator had to come back and ask for the follow-up.

The operator's question: *"Why didn't we do the proper searching to be professional and complete? Searching is EASY. What does it take for us to anticipate questions, search for the answers?"*

### What alternatives were explored

- **Blame the model** → insufficient; the model executed the skill faithfully, the skill's decomposition was the gap
- **Add more subagents** → insufficient; the problem isn't subagent count, it's that the decomposition was input-driven (operator's words) rather than domain-driven (topic space)
- **Better prompting** → partially helps (Self-Ask, ReAct patterns) but the deeper fix is architectural

### What the research changed

Confirmed that the fix is **adaptive depth** — three mechanisms drawn from production deep research systems. The `/www` skill needs a topic-space breadth scan before decomposition, a reflection/gap-detection step between rounds, and follow-up spawning when findings reveal new sub-classes.

---

## Root cause chain (5 whys)

1. **Why was the research incomplete?** → The topic decomposition produced 4 angles, but "visual explainer skills" was not one of them. It was found incidentally inside "code visualization skills."

2. **Why wasn't "visual explainer" its own decomposition angle?** → The decomposition was done from the operator's literal words, not from the **topic space**. The operator's phrasing maps to ~6-8 distinct skill classes, but only 4 were created.

3. **Why did the decomposition stop at 4?** → `/www` has **no mechanism for discovering sub-areas the operator didn't name**. No breadth scan step asks "what sub-topics exist in this domain?"

4. **Why is there no breadth scan?** → Round 2 discovery questions are supposed to catch "unknown unknowns" but they're generic ("what else should we know?"), not systematic sub-topic enumeration.

5. **Why didn't the follow-up trigger fire when subagent 3 returned "visual-explainer-skill"?** → **Because there IS no follow-up trigger.** `/www` is a one-pass pipeline (Round 1 → Round 2 → Round 2b → Round 3). Findings from Round 1 can't trigger new Round 1 subagents.

---

## The structural gap

| What `/www` has | What `/www` lacks |
|---|---|
| Fixed 4-round pipeline | **Adaptive sub-topic spawning** — findings that reveal a new sub-class don't trigger a new subagent |
| Discovery questions (Round 2) | **Topic-space enumeration** — a breadth scan that maps the full domain before decomposition |
| Parallel dispatch (≥3 sub-areas) | **Follow-up trigger on interesting findings** — "this result mentions X as a distinct class; deep-dive X" |

---

## Solution patterns from deep research architectures

### 1. Subtopic Decomposition (GPT Researcher) — `[HIGH confidence]`

**How it works:** GPT Researcher's `DetailedReport` class breaks the main query into discrete subtopics, then for each subtopic conducts focused research independently, generates draft section titles, retrieves previously written content to avoid redundancy, and writes a report section.

**Completeness mechanism:** Each subtopic gets independent coverage. The subtopic list is generated from the topic itself, not from the user's phrasing. This is the "topic-space enumeration" step `/www` lacks.

**Source:** [docs.gptr.dev/docs/examples/detailed_report](https://docs.gptr.dev/docs/examples/detailed_report)

**How to adapt for /www:** Before spawning Phase 2 subagents, run a single fast search ("what are ALL the sub-topics/skill classes in <domain>?") to enumerate the topic space. Decompose based on what exists, not just what the operator named. This adds ~10 seconds and prevents entire sub-classes from being missed.

### 2. Reflection & Gap Detection Loop (Reflexion pattern) — `[HIGH confidence]`

**How it works:** After each research iteration, the agent evaluates accumulated findings against the original query to identify coverage gaps — topics mentioned but under-sourced, sub-questions unanswered, or conflicting evidence. It then generates targeted follow-up queries for the gaps and repeats.

**Completeness mechanism:** Forces the agent to ask "what's still missing?" before synthesis. The `/www` Round 3 disconfirmation pass does something similar for *refuting* evidence, but there's no equivalent for *missing* evidence.

**Source:** [deepwiki.com/SalesforceAIResearch/enterprise-deep-research/3.6-reflection-and-gap-detection](https://deepwiki.com/SalesforceAIResearch/enterprise-deep-research/3.6-reflection-and-gap-detection)

**How to adapt for /www:** Add a Round 2.75 step between practitioner signal (Round 2b) and disconfirmation (Round 3): "Reflection pass — for each Phase 1 gap, check whether Round 1+2+2b findings addressed it. For each finding that mentions a sub-class not yet deep-dived, spawn a follow-up subagent."

### 3. Multi-Perspective Question Asking (STORM) — `[HIGH confidence]`

**How it works:** STORM discovers diverse perspectives by surveying related Wikipedia articles, personifies the LLM with distinct perspectives, simulates multi-turn conversations between a "writer" and an "expert" grounded in web sources. The conversation loop generates follow-up questions iteratively — answers provoke new questions.

**Completeness mechanism:** Perspective diversity. By modeling different viewpoints (e.g., "developer" vs. "designer" vs. "stakeholder"), STORM covers facets that a single perspective would miss. The simulated conversation prevents premature termination.

**Source:** [arxiv.org/html/2402.14207v1](https://arxiv.org/html/2402.14207v1)

**How to adapt for /www:** During decomposition, generate perspectives: "how would a <developer/designer/stakeholder/researcher> decompose this topic?" Each perspective produces a different sub-topic list. Union the lists before spawning subagents.

### 4. Self-Ask Prompting (Press et al.) — `[MEDIUM confidence]`

**How it works:** The model is prompted to explicitly generate follow-up sub-questions before answering. A Yes/No gate forces it to decide whether follow-ups are needed, then iterates through Follow-up → Intermediate answer pairs.

**Completeness mechanism:** Makes sub-question generation an explicit step. The agent can't declare "done" until it has answered every sub-question it identified.

**Source:** [learnprompting.org/docs/advanced/few_shot/self_ask](https://learnprompting.org/docs/advanced/few_shot/self_ask)

**How to adapt for /www:** The Self-Ask pattern is the lowest-cost improvement — add a prompt step after Phase 1 (wiki query) that asks the orchestrator: "Before spawning subagents, list every sub-question this topic raises. Did you miss any sub-classes?" This is a prompting pattern, not an architectural change.

### 5. DRACO Completeness Metric — `[MEDIUM confidence]`

**How it works:** The DRACO benchmark (Perplexity AI, Feb 2026) evaluates deep research agents on a "Completeness" axis — measuring whether all sub-topics implied by the query are addressed. Uses ~40 weighted rubric criteria per task.

**Completeness mechanism:** Completeness is evaluated explicitly; without it, agents optimize for the first satisfactory answer.

**Source:** [research.perplexity.ai/articles/evaluating-deep-research-performance-in-the-wild-with-the-draco-benchmark](https://research.perplexity.ai/articles/evaluating-deep-research-performance-in-the-wild-with-the-draco-benchmark)

**How to adapt for /www:** After synthesis, score the concept against a completeness checklist: "Did we cover every sub-class the operator's query implies? Did we check what the community says (Reddit)? Did we enumerate the topic space?"

---

## Prompting patterns that prevent shallow coverage

These are from the prompting-patterns research track:

| Pattern | Mechanism | Token cost | Fit for /www |
|---------|-----------|-----------|--------------|
| **Self-Ask** | Explicit sub-question generation + gate | Low | ✅ Add as Phase 1.5 step |
| **ReAct Loop** | Thought → Action → Observation cycles | Medium | ✅ Already partially present (Round 1 → Round 2 → Round 2b) |
| **Tree of Thoughts (BFS)** | Branching exploration + backtracking | High (10-50x) | ⚠️ Too expensive for routine runs; reserve for depth=deep |
| **Prompt Chaining** | Sequential steps with explicit gap identification | Medium | ✅ Add gap-identification between rounds |
| **Self-Consistency** | Multiple paths → majority vote | High (5-10x) | ⚠️ Too expensive; reserve for verification |

**Best combination for /www:** Self-Ask (sub-question decomposition) + Prompt Chaining (gap identification before synthesis). These are low-cost prompting improvements that directly prevent premature closure.

---

## The search-reason-search loop

The cross-cutting pattern from all production deep research systems (OpenAI, Anthropic, Perplexity, GPT Researcher, ODR+, STORM):

```
Plan → Search → Read → Reflect → Iterate → Synthesize
                   ↑                    |
                   └─── (if gaps) ──────┘
```

**The key insight:** `/www` currently runs Plan → Search → Synthesize (one pass). Production systems run Plan → Search → Reflect → [iterate] → Synthesize (adaptive loop). The reflection step is what catches "we found a new sub-class but didn't deep-dive it."

**ODR+ ablation evidence:** removing sub-question decomposition drops accuracy from 10% to 0% — the decomposition step is the primary completeness mechanism.

**STORM ablation evidence:** removing the perspective mechanism drops heading entity recall from 45.91% to 42.70%; removing conversation iteration drops it to 39.30%.

---

## Concrete improvements for /www

### Improvement 1: Topic-space breadth scan (Phase 1.5 — new)

Before decomposing into subagents, run a single DDG search to enumerate the topic space:

```
python P:/.agents/scripts/ddgs_search.py "all types of <topic> skill classes categories" --max 10
```

Then decompose based on what the search reveals, not just what the operator named. ~10 seconds added, prevents entire sub-classes from being missed.

### Improvement 2: Reflection/gap-detection step (Round 2.75 — new)

Between Round 2b (practitioner signal) and Round 3 (disconfirmation):

```
For each Phase 1 gap: was it addressed by Round 1+2+2b?
For each Round 1 finding that mentions a sub-class not yet deep-dived: spawn a follow-up subagent.
```

This is the "search-reason-search" loop — findings from Round 1 can now trigger new subagents.

### Improvement 3: Self-Ask prompt gate (Phase 1.5 — prompting pattern)

Add to the orchestrator's Phase 1 reasoning:

> "Before spawning subagents, list every sub-question this topic raises. Did you miss any sub-classes? What would a <developer/designer/stakeholder/researcher> ask that you didn't?"

This is the lowest-cost fix — a prompting pattern embedded in the skill's Phase 1 instructions.

### Improvement 4: Completeness checklist (Phase 3 pre-write)

Before declaring the research complete, score against:

- [ ] Did we cover every sub-class the operator's query implies?
- [ ] Did we check what the community says (Reddit, HN, GitHub)?
- [ ] Did we enumerate the topic space (not just the operator's words)?
- [ ] Did any finding mention a sub-class we didn't deep-dive? If yes, did we follow up?

---

## Existing wiki coverage (retirement check)

This concept extends two existing concepts:
- **[[compound-skill-improvement-patterns]]** (2026-07-21) — identified gap analysis and research ledger, but not adaptive depth
- **[[deep-research-systems-and-web-upgrade]]** (2026-07-22) — documented the search-reason-search loop in vendors, but didn't apply it to /www

Neither concept is superseded — this adds the adaptive-depth layer they both lacked.

---

## What this means for our workspace

The `/www` skill has a structural gap: it's a one-pass pipeline, not an adaptive loop. The fix is three concrete improvements (topic-space breadth scan, reflection/gap-detection step, Self-Ask prompt gate) drawn from production deep research architectures. The prompting patterns (Self-Ask, Prompt Chaining) are the lowest-cost fixes — they can be added as SKILL.md instructions without architectural changes. The reflection step requires a new Round 2.75 in the pipeline.

The operator's question — "what does it take for us to anticipate questions, search for the answers?" — has a clear answer: **the skill needs to enumerate the topic space before decomposing, and reflect on whether findings revealed new sub-classes worth following up.** These are solved problems in the deep research literature. The gap is that /www hasn't adopted them yet.

## Falsifier

This analysis is wrong if:
- The visual-explainer omission was a one-off model execution failure (not a structural gap in /www's decomposition) — testable by running /www on a different broad topic and checking whether sub-classes get missed
- Adding the breadth scan + reflection step doesn't actually improve coverage (testable by before/after comparison on the same topic)
- The prompting patterns (Self-Ask) are already implicitly present in /www's Round 2 discovery questions (they're not — Round 2 questions are generic, not systematic sub-topic enumeration)

## Receipts

| Claim | Receipt |
|-------|---------|
| /www decomposed into 4 subagents and found visual-explainer as one-liner | Session transcript — subagent 3 output (this session) |
| GPT Researcher uses subtopic decomposition as primary completeness mechanism | DDG subagent finding, source: `docs.gptr.dev/docs/examples/detailed_report` |
| ODR+ ablation: removing sub-question decomposition drops accuracy 10%→0% | DDG subagent finding, source: `arxiv.org/html/2508.10152v1` |
| STORM ablation: removing perspective drops recall 45.91%→42.70% | DDG subagent finding, source: `arxiv.org/html/2402.14207v1` |
| Reflexion pattern for gap detection | DDG subagent finding, source: `deepwiki.com/SalesforceAIResearch/enterprise-deep-research/3.6` |
| Self-Ask prompting prevents premature closure | DDG subagent finding, source: `learnprompting.org/docs/advanced/few_shot/self_ask` |
| DRACO benchmark evaluates completeness as explicit dimension | DDG subagent finding, source: `research.perplexity.ai/articles/evaluating-deep-research-performance-in-the-wild-with-the-draco-benchmark` |
| /www is a one-pass pipeline, not adaptive loop | `/www` SKILL.md — Phase 2 has Round 1→2→2b→3 with no feedback loop for spawning new Round 1 subagents |
| [[compound-skill-improvement-patterns]] identified gap analysis but not adaptive depth | `read_file` of `P:/.data/wiki/concepts/compound-skill-improvement-patterns.md` |
| [[deep-research-systems-and-web-upgrade]] documented vendor loops but didn't apply to /www | `read_file` of `P:/.data/wiki/concepts/deep-research-systems-and-web-upgrade.md` |

## Cross-references

- [[compound-skill-improvement-patterns]] — the 7-dimension /www improvement framework this extends
- [[deep-research-systems-and-web-upgrade]] — vendor deep research architectures documented here
- [[research-quality-principle-efficiency-not-censorship]] — quality is the constraint, not time
- [[mechanisms-for-thought-partner-behavior]] — anticipation is the hardest component of thought-partner behavior
- [[prompting-patterns-for-ai-agent-control]] — prompting patterns reference for skill authoring

## Auto-related

- [[skill-catalog]]
- [[deep-research-systems-and-web-upgrade]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[web-search-tool-routing]]
- [[research-applicability-checking-dont-cite-without-verifying-assumptions]]


---
title: "Compensating for weaker models: ensemble and multi-pass techniques"
created: 2026-07-21
source: session-2026-07-21 (/www research on model weakness compensation)
sources:
  - https://kinde.com/learn/ai-for-software-engineering/workflows/llm-fan-out-101-self-consistency-consensus-and-voting-patterns/
  - https://www.mdpi.com/2078-2489/16/8/688
  - https://arxiv.org/abs/2309.04269
  - https://arxiv.org/html/2311.08154v3
  - https://openreview.net/forum?id=1PL1NIMMrw
  - https://aclanthology.org/2024.acl-long.78.pdf
  - P:/.data/wiki/concepts/multi-agent-correlated-errors.md
  - P:/.data/wiki/concepts/testing-methodology-both-outcomes-informative.md
  - P:/.data/wiki/concepts/skill-techniques-index.md
tags: [ensemble, self-consistency, multi-pass, weak-model, compensation, fan-out, chain-of-density, prompt-ensemble, llm-as-judge]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "Techniques for compensating for relative weakness in cheaper/smaller LLMs like DiffusionGemma. Three families: fan-out (self-consistency, prompt ensembles, voting), progressive refinement (chain of density, iterative passes), and task decomposition. Each technique documented with how it works, when it helps, cost, and applicability to DiffusionGemma via direct API."
---

# Compensating for weaker models: ensemble and multi-pass techniques

## Context

DiffusionGemma (tested 2026-07-21) is 42x faster and free but produces less detailed summaries than ccr-ornith. The quality gap is real but proportional to the task. This concept documents techniques to close that gap — getting better results from a weaker/cheaper model by making multiple calls and combining them intelligently.

## The three families

| Family | Core idea | Best for |
|---|---|---|
| **Fan-out** | Generate N responses to the same query, aggregate | Reducing errors, increasing confidence |
| **Progressive refinement** | Iteratively improve a single output through multiple passes | Summarization, quality improvement |
| **Task decomposition** | Break complex tasks into simpler subtasks the weak model can handle | Multi-step reasoning, long inputs |

## Family 1: Fan-out (self-consistency, prompt ensembles, voting)

Source: [Kinde LLM Fan-Out 101](https://kinde.com/learn/ai-for-software-engineering/workflows/llm-fan-out-101-self-consistency-consensus-and-voting-patterns/), [Wang et al. Self-Consistency (ICLR 2023, 4930 citations)](https://openreview.net/forum?id=1PL1NIMMrw)

### Technique 1: Self-consistency sampling

**How it works:** Run the same prompt through the same model N times with high temperature (0.7-1.0). Each run produces a different reasoning path. Aggregate by majority vote (for factual answers) or LLM-as-judge (for open-ended answers).

**Why it works:** LLMs are probabilistic. Different temperature samples explore different reasoning paths. If most paths converge on the same answer, confidence is high. If they diverge, the answer is uncertain.

**For DiffusionGemma:**
```python
# Run 3 passes with different temperature
for temp in [0.3, 0.7, 1.0]:
    response = call_diffusiongemma(file_content, temperature=temp)
    responses.append(response)
# Aggregate: for factual claims, majority vote; for summaries, LLM-as-judge
```

**Cost:** 3x API calls. At ~1s per call via DiffusionGemma's direct API, total is ~3s. Still 15x faster than ccr-ornith's single 46s call.

**When it helps:** factual extraction, technique identification, any task where there's a "right answer" that multiple passes should converge on.

**When it doesn't help:** creative tasks, tasks with no single right answer, tasks where the model consistently gets the same thing wrong (self-consistency amplifies shared blind spots).

### Technique 2: Prompt ensembles (multi-perspective)

**How it works:** Instead of varying temperature, vary the prompt. Ask the same question from different angles. If the model produces consistent findings across prompt variations, those findings are robust.

Source: [Huang et al. Multi-Perspective Self-Consistency (ACL 2024, 81 citations)](https://aclanthology.org/2024.acl-long.78.pdf)

**For DiffusionGemma:**
```python
prompts = [
    "What is the purpose of this skill? What unique techniques does it use?",
    "If you were auditing this skill for quality, what would you note as distinctive?",
    "What problem does this skill solve, and what approach does it take?",
    "List the 3 most important features of this skill file.",
]
responses = [call_diffusiongemma(file_content, prompt=p) for p in prompts]
# Merge: union of all unique findings, deduplicated
```

**Cost:** 4x API calls. ~4s total via DiffusionGemma.

**When it helps:** summarization, feature extraction, any task where different phrasings surface different aspects. The multi-perspective approach catches things a single prompt misses.

**When it doesn't help:** simple lookups where the prompt wording doesn't change the answer.

### Technique 3: Majority voting + LLM-as-judge aggregation

**How it works:** After fan-out (techniques 1 or 2), aggregate:
- **For factual answers:** majority vote. If 3 of 5 passes say "X is a technique," it's confirmed.
- **For open-ended answers (summaries):** use a separate LLM call (the "judge") to pick the best response or synthesize a merged version.

Source: [Kinde](https://kinde.com/learn/ai-for-software-engineering/workflows/llm-fan-out-101-self-consistency-consensus-and-voting-patterns/)

**Judge prompt:**
```
You are given 4 summaries of the same skill file, produced from different
perspectives. Synthesize them into a single summary that captures:
- All unique findings mentioned across the summaries
- Findings confirmed by multiple summaries (mark as [HIGH] confidence)
- Findings from only one summary (mark as [MEDIUM] confidence)
- Conflicting findings (mark as [CONFLICT])
```

**Cost:** N fan-out calls + 1 judge call. For DiffusionGemma fan-out + parent-inherited judge: ~4s + ~5s = ~9s. Still 5x faster than ccr-ornith alone.

**When it helps:** when fan-out produces diverse outputs that need synthesis rather than simple voting.

## Family 2: Progressive refinement

### Technique 4: Chain of Density (iterative summarization)

Source: [Adams et al. Chain of Density (EMNLP 2023, 126 citations)](https://arxiv.org/abs/2309.04269)

**How it works:** Generate an initial summary, then iteratively make it denser (more information per token) through N passes. Each pass adds missing entities and tightens prose.

**For DiffusionGemma:**
```python
# Pass 1: initial summary
summary = call_diffusiongemma(file_content, "Summarize this file in 3 sentences.")
# Pass 2: densify
summary = call_diffusiongemma(
    f"Original text: {file_content}\n\nCurrent summary: {summary}\n\n"
    "Add missing important details. Make it denser without adding length.",
    context=summary
)
# Pass 3: final polish
summary = call_diffusiongemma(
    f"Summary: {summary}\n\nFix any errors, add any missing techniques, ensure accuracy.",
)
```

**Cost:** 3x sequential calls. ~3s via DiffusionGemma.

**When it helps:** summarization tasks where the first pass is too sparse. The iterative densification catches details the model missed initially.

**When it doesn't help:** non-summarization tasks; tasks where one pass is sufficient.

### Technique 5: Self-agreement (confidence calibration)

Source: [Lu et al. Self-Agreement (arXiv 2023)](https://arxiv.org/html/2311.08154v3)

**How it works:** Run the model N times on the same task. If all N outputs agree, confidence is high. If they disagree, flag the finding as uncertain. Don't aggregate — just use the agreement pattern as a confidence signal.

**For DiffusionGemma:**
```python
# Run 3 times with default temperature
outputs = [call_diffusiongemma(file_content) for _ in range(3)]
# Check agreement: do all 3 mention the same techniques?
agreed_techniques = intersection(outputs)
uncertain_techniques = symmetric_difference(outputs)
# Mark agreed as [HIGH], uncertain as [UNCERTAIN]
```

**Cost:** 3x calls. ~3s.

**When it helps:** when you need a confidence signal, not just better output. This is the model-verification analog of the testing methodology's "both outcomes" principle.

## Family 3: Task decomposition

### Technique 6: Chunked processing

**How it works:** Instead of feeding the entire file at once, split it into chunks (e.g., per-section), summarize each chunk independently, then merge.

**For DiffusionGemma:**
```python
# Split SKILL.md into sections by header
sections = split_by_header(file_content)
# Summarize each section independently
section_summaries = [call_diffusiongemma(s, "Summarize this section in 2 sentences.") for s in sections]
# Merge into final summary
final = call_diffusiongemma(
    "Merge these section summaries into a coherent skill summary:\n" + "\n".join(section_summaries)
)
```

**Cost:** N+1 calls (N sections + 1 merge). For a typical SKILL.md with 5 sections: ~6s.

**When it helps:** long files where the model's attention degrades (the "lost in the middle" problem). Also helps when different sections need different prompt framing.

### Technique 7: Extract-then-synthesize

**How it works:** First pass extracts structured data (facts, techniques, features). Second pass synthesizes the structured data into prose. Separating extraction from synthesis lets each step focus.

**For DiffusionGemma:**
```python
# Pass 1: extract
facts = call_diffusiongemma(file_content, "Extract all facts, techniques, and features as a JSON list.")
# Pass 2: synthesize
summary = call_diffusiongemma(
    f"Synthesize these extracted facts into a coherent summary:\n{facts}",
    "Write a structured summary using the extracted facts."
)
```

**Cost:** 2x calls. ~2s.

**When it helps:** when the model is better at extraction than at prose synthesis (or vice versa). Separating the tasks lets each pass optimize for its strength.

## Practical recipe for DiffusionGemma

Based on the T4 comparison (DiffusionGemma scored 17/20 vs ccr-ornith's 20/20), the gap was in:
- **Completeness** (missed line citations, incident references) → fix with chunked processing or prompt ensembles
- **Detail** (less verbose) → fix with chain of density

**Recommended compensation recipe for mechanical reads:**

```python
def diffusiongemma_enhanced_read(file_path):
    content = read(file_path)

    # Step 1: multi-perspective extraction (catches more features)
    perspectives = [
        "What is the purpose? What techniques does it use?",
        "What failure modes does it prevent? What is unique?",
        "List the 3 most important features with their section names.",
    ]
    raw_findings = [call_diffusiongemma(content, p) for p in perspectives]

    # Step 2: merge + densify (improves completeness)
    merged = call_diffusiongemma(
        "Merge these findings into a single summary. Add any missing details. Mark "
        "findings confirmed by multiple perspectives as [HIGH] confidence:\n\n"
        + "\n---\n".join(raw_findings)
    )

    return merged
```

**Cost:** 4 calls × ~1s = ~4s. Quality should approach ccr-ornith's 46s output at 10x the speed and zero cost.

**Falsifier:** run the enhanced recipe on the same handoff/SKILL.md file used in T4 and blind-compare against the original DiffusionGemma single-pass output and ccr-ornith's output. If the enhanced recipe doesn't score ≥19/20, the compensation isn't sufficient.

## Do's

1. **Use multi-perspective prompting** — different angles surface different features
2. **Use temperature variation** for self-consistency on factual extraction
3. **Use chain of density** for summarization tasks that need more detail
4. **Use LLM-as-judge** to aggregate fan-out outputs when simple voting doesn't work
5. **Measure the compensation** — run the enhanced recipe blind against the single-pass and the stronger model. If it doesn't close the gap, the compensation isn't working.
6. **Calculate total cost** — N calls at 1s each may still be faster than 1 call at 46s. The speed advantage compounds.

## Don'ts

1. **Don't use fan-out when the model consistently gets the same thing wrong** — self-consistency amplifies shared blind spots. If all 3 passes miss the same technique, voting won't help.
2. **Don't use fan-out for creative tasks** — there's no "right answer" to converge on.
3. **Don't use chain of density beyond 3 passes** — diminishing returns; later passes start hallucinating to fill perceived gaps.
4. **Don't compensate when a stronger model is available and the task is high-stakes** — compensation is for breadth scanning, not for the final synthesis.
5. **Don't assume compensation closes the gap without measuring** — the T4 blind comparison methodology applies here too.

## Relationship to existing concepts

- [[multi-agent-correlated-errors]] — warns that ensemble diversity should target correlated errors, not persona diversity. The multi-perspective technique above targets different extraction angles, not different personas.
- [[testing-methodology-both-outcomes-informative]] — the falsifier for compensation recipes is a blind comparison with both outcomes specified.
- [[skill-techniques-index]] T20 (two-phase analysis) — the compensation recipe fits as the LLM breadth-read tier, between code scan and LLM depth-read.
- [[skill-techniques-index]] T7 (two-lens critique) — self-agreement (technique 5) is structurally similar: multiple passes check each other.

## Open questions

- Does the enhanced recipe (4 calls) actually close the quality gap to ccr-ornith? Needs T4-style blind comparison.
- What's the optimal number of perspectives for multi-perspective prompting? (3? 5? More = more cost, diminishing returns)
- Does DiffusionGemma support temperature parameter via the Nvidia endpoint? (Not tested yet — T2 tested thinking=False, not temperature)
- Can the compensation recipe be automated in `diffusiongemma_read.py`?

## Sources

- [LLM Fan-Out 101: Self-Consistency, Consensus, and Voting Patterns](https://kinde.com/learn/ai-for-software-engineering/workflows/llm-fan-out-101-self-consistency-consensus-and-voting-patterns/) — Kinde. Fan-out pattern overview, three tactics (self-consistency, prompt ensembles, voting), when to avoid.
- [Ensemble Large Language Models: A Survey](https://www.mdpi.com/2078-2489/16/8/688) — Mienye & Swart, Information 2025, 31 citations. Model-level ensembles compensate for individual model weaknesses. Bagging, boosting, stacking, knowledge distillation.
- [From Sparse to Dense: GPT-4 Summarization with Chain of Density Prompting](https://arxiv.org/abs/2309.04269) — Adams et al., EMNLP 2023, 126 citations. Iterative summarization with increasing density.
- [Just Ask One More Time! Self-Agreement Improves LLM Reasoning](https://arxiv.org/html/2311.08154v3) — Lu et al. Self-agreement as confidence calibration.
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://openreview.net/forum?id=1PL1NIMMrw) — Wang et al., ICLR 2023, 4930 citations. Foundational self-consistency paper.
- [Enhancing LLMs in Coding Through Multi-Perspective Self-Consistency](https://aclanthology.org/2024.acl-long.78.pdf) — Huang et al., ACL 2024, 81 citations. Multi-perspective framework for coding tasks.

## Auto-related

- [[multi-agent-correlated-errors]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

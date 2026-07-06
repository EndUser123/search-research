---
name: prompt_refiner
disable-model-invocation: true
description: "DEPRECATED entry — use /improve generate-prompt. Executable prompt specification system: Q1-Q3 triage, complexity/domain/ambiguity/multi-faceted scoring, and 6 cognitive-technique templates (CoT/Socratic/Self-Refine/Chain-of-Verification/Tree-of-Thoughts/QueryFanout)."
version: "2.1.0"
status: "stable"
category: strategy
triggers:
  - /prompt_refiner
aliases:
  - /prompt_refiner
workflow_steps: []
enforcement: advisory
suggest:
  - /improve
  - /nse
  - /design
---

# /prompt_refiner — DEPRECATED entry (engine retained)

`/prompt_refiner` is now `/improve generate-prompt`:

```
/improve generate-prompt <target-or-task>
```

`/improve generate-prompt` reads the artifacts, then emits a tuned prompt for
another LLM or subagent — tagging each instruction's evidence basis and the
falsification condition the reviewer must check.

The `/prompt_refiner` **engine is unchanged** — `/improve generate-prompt` reuses
these techniques directly:

**Q1-Q3 Rapid Triage** (kept by `/improve generate-prompt` as the routing matrix):
- Q1 reversibility (1.0-1.25 MIN-EFFORT/CoT · 1.5-1.75 STANDARD/ToT · 2.0 MAXIMUM-SAFETY/Multi-Agent)
- Q2 dependencies (0-1 CoT · 2-4 ToT+Self-Consistency · 5+ Multi-Agent Debate)
- Q3 evidence (YES Tier 1 · NO Tier 3 · UNCERTAIN Tier 4)

**Scoring heuristics** (0.0-1.0 each): Complexity, Domain Specificity, Ambiguity
(ambiguity_indicators vs specificity_penalty), Multi-Faceted. Diagnostic metrics:
Contradiction Score, Cognitive Load, Persona Drift, Semantic Coverage.

**Cognitive-technique template library** (6 templates, applied by appending to the
generated prompt): Chain-of-Thought · Socratic · Self-Refine · Chain-of-Verification
· Tree-of-Thoughts · QueryFanout. Selection matrix maps (complexity, ambiguity,
multi-faceted, domain) → technique.

`/prompt_refiner` remains the **source of truth** for its triage matrix, scoring
heuristics, and technique templates — `/improve generate-prompt` reads them, does
not vendor. This stub entry will be removed after one release cycle; the technique
library stays as the canonical reference.

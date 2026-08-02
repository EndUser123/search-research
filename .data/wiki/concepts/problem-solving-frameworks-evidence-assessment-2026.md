# Problem-solving frameworks: evidence-based assessment

**Host:** grok
**Created:** 2026-08-02
**Session:** 019fba58

## What

Evidence-based assessment of 10+ problem-solving frameworks from research conducted via 3 parallel subagents (32 search topics). Identifies which frameworks have experimental support, which are craft disciplines, and which are folklore. Maps each to AI agent applicability.

## The universal failure mode: premature convergence

Five of ten frameworks studied share the same hazard: converging to one simple explanation too early. 5-Whys, Occam's Razor, MECE, hypothesis-driven consulting, and single-loop learning all push toward a single root cause. The counterweight in every tradition is the same: **divergent enumeration first, evidence-gated convergence second.**

This matches the workspace pattern documented in `[[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]`.

## Evidence assessment

### Real experimental evidence

| Framework | Evidence | Key finding |
|-----------|----------|-------------|
| **Paul–Elder critical thinking** | Meta-analytic (ERIC 1990, 117 studies) | Explicit CT instruction works. IUI'26 paper: "particularly well-suited for operationalizing in computational systems." 8 elements map to checkable reasoning components. |
| **TRIZ** | Cambridge 2026 RCT: TRIZ + LLM > LLM alone on design | Contradiction matrix is deterministic lookup. "Resolve the contradiction instead of accepting the tradeoff" is a checkable reasoning move. |
| **Double-loop learning** (Argyris) | Conceptually durable, empirically under-operationalized | The distinction between retrying strategy (single-loop) vs questioning assumptions (double-loop) is the exact failure mode this workspace documents repeatedly. |

### Craft disciplines (practitioner-validated, no RCTs)

| Framework | Evidence | Caveat |
|-----------|----------|--------|
| MECE (McKinsey) | Apprenticeship-validated | "MECE theater" — exhaustive-looking trees that overlap or miss branches. The hypothesis-driven structure (not MECE itself) is the valuable part. |
| First principles | Pop-content + philosophical tradition | Defensible core: reductionist decomposition. Failure mode: cost — analogy is cheaper for routine problems. Route by novelty. |
| 5-Whys / Toyota Kata | Case-based, practitioner-reported | "5-Whys Delusion" critique: each "why" has a single answer, but real failures have multiple contributing causes. Kata's Challenge vs Target Condition split is durable. |
| Design thinking | Qualitative (Liedtka HBR 2018, 50 projects) | No RCTs found. Value: forces contact with problem before solution generation. Already encoded in workspace "search before proposing" rule. |

### Mostly folklore

| Framework | Evidence | Assessment |
|-----------|----------|------------|
| OODA loop | None. Boyd never wrote it down. Hankins: "vague enough that defenders and attackers see what they want." | Transferable insight: Orient is the heavy stage. But not uniquely OODA. |
| Occam's Razor | Actively contested. Oreskes (Scientific American): "no good reason to prefer simpler explanation." | Correct use: Occam orders hypotheses to TEST, not conclusions to ACCEPT. Agents misuse as truth test. |

## What was operationalized in session 019fba58

1. Paul–Elder reasoning elements labeled on existing `/tp` protocol.md steps (A-D)
2. Intellectual standards rubric (clarity, accuracy, relevance, depth, fairness) added to `/tp` Step C
3. TRIZ contradiction reframing added as `/tp explore` directive 10
4. De Bono lateral thinking added as `/tp explore` directive 11
5. Paul–Elder "what am I assuming?" check replacing generic "could I be wrong?" in AGENTS.md per-turn protocol

## What was NOT incorporated (and why)

- OODA loop — no evidence, too vague
- Design thinking as a process — already encoded in existing rules
- 5-Whys as single-chain method — convergence failure mode
- MECE as standalone framework — useful as decomposition check, not worth adding as named process

## Sources

- Paul–Elder: criticalthinking.org, ERIC ED328614, IUI'26 "Criticality" paper
- TRIZ: triz40.com, Cambridge 2026 "Evaluating TRIZ with and without LLM support"
- Double-loop: Argyris HBR 1977, PMC8671862
- MECE: McKinsey, mconsultingprep.com, strategyu.co
- Occam: Oreskes Scientific American, nesslabs.com
- 5-Whys: dp.cx "Five Whys and the Myth of the Single Root Cause"
- OODA: Wikipedia (incl. Hankins critique), taskandpurpose.com
- Design thinking: Liedtka HBR 2018, Stanford d.school

## Extends

- [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]
- [[first-principles-thinking]]
- [[blind-spot-detection-methods]]
- [[solution-first-before-root-cause-overengineering-failure]]

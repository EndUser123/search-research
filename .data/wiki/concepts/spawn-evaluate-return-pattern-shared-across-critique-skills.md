---
title: "Spawn-evaluate-return pattern shared across critique skills"
created: 2026-08-05
source: session-019fd276
tags: [skill-design, critique, pattern-similarity, skill-boundary, spawn-evaluate-return]
summary: >
  /tp, /risk, and /review all implement the spawn-evaluate-return pattern
  (spawn agents → evaluate target → return findings + verdict) independently
  with different implementations. They share a pattern, not an implementation.
  Decomposition reveals 3 potentially shared utility functions (context packing,
  finding verification, verdict derivation), but each skill's evaluation logic
  is domain-specific and legitimately different. The pattern similarity is
  intentional diversity, not accidental duplication.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/multi-agent-correlated-errors.md
    type: related
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: related
  - target: wiki/concepts/cross-model-ensemble-design-patterns-for-agent-skills.md
    type: related
---

# Spawn-evaluate-return pattern shared across critique skills

## Decision context

**Why this was investigated:** during a session where `/todo` appeared to be a
superset of `/tp` findings (via transcript scan), the operator asked whether the
two skills should be merged or whether /tp's critique engine should be extracted
into a shared capability on the skill graph. This raised the broader question:
how much implementation do `/tp`, `/risk`, and `/review` actually share?

## The pattern

All three skills implement the same operational flow:

1. **Spawn** — invoke one or more subagents (possibly cross-model) with a target
   and context
2. **Evaluate** — the agent reads the target (code, diff, decision, design) and
   produces structured findings
3. **Return** — the parent synthesizes findings, derives a verdict
   (PROCEED/REVISE/BLOCK), and persists results

This is the "spawn-evaluate-return" pattern. It's the agent-fleet equivalent of
the human practice of "get a second opinion."

## Decomposition: what's genuinely shared vs domain-specific

| Operation | /tp | /risk | /review | Shared? |
|-----------|------|--------|---------|---------|
| Model selection | `pick_model.py` | `pick_model.py` | `pick_model.py` | **Already shared** |
| Spawn | `spawn_subagent` × 1 | `spawn_subagent` × 2-3 | `spawn_subagent` × N | **Platform primitive** |
| Context packing | `tp_dispatch.py` | inline | inline | **Same operation, reimplemented** |
| Evaluation criteria | framing, optimal, falsifiability | risk severity, failure modes | code correctness, security | **Domain-specific — NOT shared** |
| Findings schema | prose + evidence tags | JSON (id, severity, evidence, fix) | JSON (nearly identical to /risk) | **/risk and /review overlap; /tp is different** |
| Findings verification | parent reads file:line | parent reads file:line | parent reads file:line | **Same operation, reimplemented** |
| Verdict derivation | inline (any BLOCK → BLOCK) | inline (same logic) | n/a (findings only) | **Same logic, reimplemented** |
| Persistence | `tp_critique_log.py` (JSONL) | `run_dir/*.json` | `run_dir/FINDINGS.md` | **Different consumers, different formats** |

Three operations are genuinely the same logic reimplemented three times:
1. **Context packing** — ~50 lines each, assemble prompt from target + context
2. **Finding verification** — ~15 lines each, read cited source and confirm
3. **Verdict derivation** — ~10 lines each, severity → verdict mapping

Total duplicated: ~75 lines × 3 = ~225 lines of conceptually identical code.

## Why the implementations diverge (intentional diversity)

The evaluation logic is different because the questions are different:

- **/tp** asks "is this the right approach?" → needs framing analysis,
  counterfactuals, pre-mortem thinking. Output is dialogue-shaped (prose with
  evidence tags) because the consumer is the operator in conversation.
- **/risk** asks "what could go wrong?" → needs risk-category scanning,
  severity × likelihood assessment. Output is structured JSON because the
  consumer is the escalation pipeline (critique → attack → wargame).
- **/review** asks "is this code correct?" → needs file-level analysis,
  lint/type/test integration. Output is `FINDINGS.md` because the consumer is
  the ship pipeline (fix-loop reads it).

Forcing these into a shared evaluation engine would either:
- Flatten the differences (all skills get the same lens — loses /tp's framing
  analysis or /review's file-level precision)
- Parameterize everything (the parameter config becomes as complex as the
  original code — abstraction without simplification)

See [[multi-agent-correlated-errors]]: "the value of parallel agents comes from
cross-family model diversity, not from parallelism itself." The same principle
applies to evaluation diversity — the skills' value comes from their different
lenses, not from sharing one.

This connects to [[blind-spot-detection-methods]]: the reason /tp uses a fresh
subagent is structural independence (Costa & Kallick). Sharing evaluation logic
across skills would re-introduce the shared-blind-spot problem that cross-model
spawning was designed to solve — the shared evaluator would have the same blind
spots in all three skills.

See also [[multi-model-ensemble-design-patterns-for-agent-skills]] for the
parallel: model diversity matters for the spawn step, evaluation diversity
matters for the evaluate step. Both are load-bearing; neither should be
collapsed for the sake of code reuse.

The [[model-pool-selection-policy-speed-quota-diversity]] policy already
externalizes model selection — all three skills call `pick_model.py`. This
proves the pattern works: genuinely shared operations (model selection) are
already extracted and consumed by all three. The operations that aren't shared
(context packing, evaluation criteria) aren't extracted because they diverge.

## What this means for our workspace

**No extraction needed today.** The pattern similarity is an observation for
future maintainers, not a maintenance burden causing real problems. The 225
lines of duplicated utility logic are spread across 3 skills that evolve
independently — coupling them would create coordination overhead exceeding the
duplication cost.

**When to revisit:** if a 4th skill implements spawn-evaluate-return, the
pattern is established enough to justify extracting the 3 shared utilities
(context packing, finding verification, verdict derivation) into a shared
library. At that point the duplication is 4×, not 3×, and the coordination
cost is amortized across more consumers.

**Maintenance rule:** when modifying spawn-evaluate-return logic in any of the
three skills, check whether the change applies to the others. The pattern
similarity means a bug fix in `/tp`'s finding verification likely applies to
`/risk` and `/review` too — but verify, don't assume.

## Falsifier

This "don't extract yet" decision is wrong if:
- The 3 skills' shared operations drift in incompatible ways (one gains a
  feature the others need but can't use because they reimplemented
  independently). Measurement: track whether changes to finding verification
  in one skill are manually propagated to the others.
- A 4th skill implements the pattern and the operator has to explain the shared
  logic from scratch each time (onboarding cost exceeds extraction cost).
- The duplicated context-packing logic causes a real bug in one skill that the
  others already fixed (synchronization failure).

If none of these occur within 3 months, the decision to not extract is
validated. If any occurs, extract the 3 utilities.

## Receipts

- `tp_dispatch.py`: `~/.grok/skills/tp/__lib/tp_dispatch.py` (context packing)
- `/risk` Phase 3: `~/.grok/skills/risk/SKILL.md` lines ~155-200 (inline critique panel)
- `/review` pipeline: `~/.grok/skills/review/SKILL.md` (reviewer + findings format)
- `pick_model.py`: `~/.grok/skills/model-quota/scripts/pick_model.py` (shared model selection)

## Auto-related

- [[model-quota-contention-coordination-fleet-rate-limiting]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[skill-catalog]]
- [[skill-graph]]
- [[prompt-patterns-improvement-ideas-2026]]


---
title: "Creative reasoning as reusable skill-graph functions"
created: 2026-08-06
source: session-20260806
tags: [skill-design, creative-techniques, combinatorial-creativity, TRIZ, ideation, skill-graph, reusable-component]
summary: >
  Creative reasoning techniques (combinatorial ideation, TRIZ contradiction
  resolution, SCAMPER, diamond process, 20 ideation heuristics) extracted
  from /brain's body into reusable reference files loadable by any skill.
  The techniques live at ~/.grok/skills/brain/references/. Skills discover
  them via wiki grounding (this concept matches "decompose", "combine",
  "contradiction", "ideation", "creative"). This enables automatic,
  intelligent invocation — not manual Load instructions.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/brainstorming-ideation-with-llms.md
    type: extends
  - target: wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md
    type: complements
  - target: wiki/concepts/combinatorial-recombination-research-25-ideas-2026.md
    type: extends
---

# Creative reasoning as reusable skill-graph functions

## Decision context

The operator asked: why isn't the rest of /brain a reusable function in the skill graph? The answer: it should be. The creative reasoning patterns inside /brain (diamond process, divergent framing, TRIZ, SCAMPER, combinatorial ideation) are general-purpose techniques that any skill might need. Locking them inside /brain's body means other skills can't access them without the full /brain invocation.

## What was done

Extracted three reference files from /brain:

| File | Contents | When skills load it |
|---|---|---|
| `brain/references/combinatorial-ideation.md` | Decompose → recombine → filter procedure. Formal names (GMA, CCA, TRIZ). Evidence (12.5% hit rate, 9.1% baseline). | When needing systematic idea generation from existing concepts |
| `brain/references/ideation-heuristics.md` | 20 cognitive moves (H1-H20) in 5 categories. Mutation operators for ideas. | When needing to mutate or jump-start idea generation |
| `brain/references/creative-techniques.md` | Diamond process, TRIZ 40 principles (agent-design-specific), SCAMPER, cross-domain analogy | When needing divergent thinking, contradiction resolution, or systematic exploration |

## How automatic invocation works — and the discovery gap

Skills with wiki grounding (like /www, /risk, /why, /design) query the wiki before executing. When this concept matches their domain keywords ("decompose", "combine", "contradiction", "ideation", "creative", "divergent"), they find this concept, which points them to the reference files. The invocation chain:

```
Skill queries wiki for "decompose" or "contradiction" or "combine"
  → finds this concept
  → reads: "Load brain/references/combinatorial-ideation.md"
  → loads the procedure
  → applies it
```

No manual Load instruction needed in each skill's SKILL.md. The wiki IS the routing layer.

**Discovery gap (tested 2026-08-06):** "decompose" appears 88 times across all wiki concepts. "ideation" appears 55 times. The concept is present in search results but not necessarily first. Skills that grep with multi-word patterns ("combinatorial ideation", "TRIZ contradiction", "cross-domain recombination") find it easily (1-5 hits). Skills that grep with single common words ("decompose", "combine") will need to scan through noise.

**Mitigation:** the reference files themselves are in `~/.grok/skills/brain/references/`. Skills that explicitly `Load` the reference path bypass the wiki search entirely. The wiki concept is for **discovery** (when a skill doesn't know it needs creative techniques); the explicit Load path is for **invocation** (when a skill knows it needs them).

Skills with wiki grounding (like /www, /risk, /why, /design) query the wiki before executing. When this concept matches their domain keywords ("decompose", "combine", "contradiction", "ideation", "creative", "divergent"), they find this concept, which points them to the reference files. The invocation chain:

```
Skill queries wiki for "decompose" or "contradiction" or "combine"
  → finds this concept
  → reads: "Load brain/references/combinatorial-ideation.md"
  → loads the procedure
  → applies it
```

No manual Load instruction needed in each skill's SKILL.md. The wiki IS the routing layer.

## What this means for our workspace

1. `/brain recombine <input>` is the explicit invocation mode
2. Other skills get the capability automatically when their wiki grounding matches
3. The techniques are versioned and maintained in one place (the reference files), not duplicated across skills
4. The TRIZ 40 principles are agent-design-specific — each principle has a concrete agent-fleet application example

## Falsifier

If skills with wiki grounding do NOT discover these techniques (because their query keywords don't match "decompose/combine/contradiction"), the automatic invocation doesn't work and we need explicit Load instructions in each skill's body. Test: run /www or /risk on a task where decomposition would help and verify the technique is discovered.

## Receipts

- Combinatorial ideation reference: `~/.grok/skills/brain/references/combinatorial-ideation.md` (written this session)
- Ideation heuristics reference: `~/.grok/skills/brain/references/ideation-heuristics.md` (written this session, adapted from ICLR 2026)
- Creative techniques reference: `~/.grok/skills/brain/references/creative-techniques.md` (written this session)
- /brain SKILL.md: modes table + recombine mode + reference pointers added (verified via read_file)
- Session 2026-08-06: 25 recombinations from ~200 pairs = 12.5% hit rate (above 9.1% literature baseline)

## Related concepts

- [[brainstorming-ideation-with-llms]] — prior wiki concept on divergent ideation with LLMs
- [[adhd-parallel-frame-divergent-ideation-integration]] — parallel-frame decomposition technique
- [[combinatorial-recombination-research-25-ideas-2026]] — the 25-idea research that proved the technique works

## Auto-related

- [[design-graphs-solution-graphs-value-for-ai-agent-fleet]]
- [[context-management-in-claude-code]]
- [[latent-reasoning-in-language-models]]
- [[technique-capture-and-surfacing-system]]
- [[latent-chain-of-thought-reasoning]]


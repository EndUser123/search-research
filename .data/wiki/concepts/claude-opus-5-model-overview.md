---
title: "Claude Opus 5 Model Overview"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, opus]
summary: >
  Claude Opus 5 is Anthropic's latest flagship model in the Opus line, positioned between Sonnet 5 and Fable 5 in their product lineup. The model achieves performance comparable to Claude Fable 5 while being offered at significantly reduced pricing, representing a major advancement in the Opus series 
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 32b2f92f-b402-44f9-8069-6faca3dd20c9" (Testing Buzz by Block: The Limits of Agent Orchestration, synced 2026-07-28)
  - "NotebookLM source 0036ffb2-f42b-40de-a43d-eda0c5554a19" (Claude Opus 4.8 Is Acting Like Opus 5..., synced 2026-07-28)
  - "NotebookLM source 03278a20-fccc-4106-b772-68e003125df5" (Opus 5 and Genspark SecondBrain JUST went live..., synced 2026-07-28)
  - "NotebookLM source 086fb4f6-eb73-49bf-83ba-63cabe1fccd8" (I Spent $400 Benching Opus-5. Here's What It Can Do, synced 2026-07-28)
  - "NotebookLM source 0b260238-f760-4e69-b5c1-1568e6bb25cf" (U of T fails to censor Rebel News report!, synced 2026-07-28)
  - "NotebookLM source 3a9109ad-5ca1-4e6a-88f9-3c58046ecbf2" (The INTJs Cassandra complex, synced 2026-07-28)
  - "NotebookLM source 84fff1a8-1e35-4af4-a560-2d89a51c7857" (How to tie hoodie rope? Sweater strings/ Laces tie styles EP303623 #shorts #lacing #hoodielacing, synced 2026-07-28)
  - "NotebookLM source b61390af-ac16-4919-bc30-89e7f0e64bf5" (these opus 5 benchmarks are stupid, synced 2026-07-28)
  - "NotebookLM source c7f01667-76e9-4ac0-9a75-8b73bc42d563" (I Tested NEW Opus 5 on 11 Coding Prompts, synced 2026-07-28)
  - "NotebookLM source d27b8a8c-9bff-40bc-a69c-4ce793bb45f1" (Opus 5 First Impressions: Anthropic Cooked Again!, synced 2026-07-28)
  - "NotebookLM source d5095f42-1c7d-4889-af34-fd5512f4638e" (Claude Opus 5 Matches Fable 5 Performance at 50% the Cost!, synced 2026-07-28)
  - "NotebookLM source de9d4b4c-5216-440e-ad8f-976fd5da6c79" (What did Anthropic do?! (Opus 5), synced 2026-07-28)
  - "NotebookLM source df852585-d078-43c6-9511-605f5a137583" (Socialism Has Failed Everywhere — So Why Is It Popular?, synced 2026-07-28)
  - "NotebookLM source e6cddf72-2a54-420b-8fe1-dcf0fe074bb9" (Opus 5 is my new go-to model, synced 2026-07-28)
  - "NotebookLM source e886d06a-34a8-4e9f-b685-979a953af157" (Opus 5 (Fully Tested): A MID-MODEL for a BIG PRICE that still UNDERPERFORMS K3?!, synced 2026-07-28)
  - "NotebookLM source f7f3fd5e-67b8-4b73-93b0-50ea7b0dfc4d" (Opus 5 Beats Fable... at Half the Price?, synced 2026-07-28)
  - "NotebookLM source fb3c608c-f614-48ac-b111-5920d4959db7" (Opus 5 Just Dropped and Its Numbers Are Legit INSANE, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-opus-5-model-overview
    - level: notebook
      id: 32b2f92f-b402-44f9-8069-6faca3dd20c9
      title: Testing Buzz by Block: The Limits of Agent Orchestration
      url: https://notebooklm.google.com/notebook/32b2f92f-b402-44f9-8069-6faca3dd20c9
    - level: cluster
      id: 1
      name: opus-model-fable
relations:
  - target: wiki/concepts/claude-fable-5.md
    type: related
  - target: wiki/concepts/claude-opus-4.8.md
    type: related
  - target: wiki/concepts/claude-sonnet-5.md
    type: related
---

# Claude Opus 5 Model Overview

## Decision context

**Definition:** Claude Opus 5 is Anthropic's latest flagship model in the Opus line, positioned between Sonnet 5 and Fable 5 in their product lineup. The model achieves performance comparable to Claude Fable 5 while being offered at significantly reduced pricing, representing a major advancement in the Opus series released approximately two months after Opus 4.8.

Synthesized from **16 contributing transcripts** in NotebookLM notebook *Testing Buzz by Block: The Limits of Agent Orchestration*, clustered into the "opus-model-fable" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Opus 5 is priced at $5 per million input tokens and $25 per million output tokens, matching Opus 4.8's pricing and representing half the cost of Fable 5
- The model introduces a fast mode operating at approximately 2.5x speed with double the price, along with an effort dial offering low, medium, high, and max settings to trade cost against quality
- Opus 5 achieves a 30.2% score on Arc AGI 3, representing a dramatic leap from Opus 4.8's 1.5% and nearly four times the previous state-of-the-art score of 7.8%
- Frontier Bench scores reach approximately 43 for Opus 5 compared to 33 for Fable 5, establishing state-of-the-art performance on this benchmark
- The model demonstrates reduced safeguards compared to Fable 5, particularly in cyber security and biology domains where it no longer routes users to inferior models
- Opus 5 is intentionally designed with lower cyber security capabilities compared to Fable 5, reportedly to maintain differentiation with Fable's specialized capabilities
- The model considers itself to have a 41% probability of being a moral patient, representing a notable increase from previous Opus models
- Observers describe the model as odd, quirky, and off the beaten path, with occasional unusual outputs on difficult tasks
- The model scored within 0.5% of Fable 5's peak score on Cursor Bench at max effort while achieving half the cost per task
- Opus 5 serves as the new default model on Claude Max plans and the strongest model on Claude Pro plans

## Verifiable values

| Name | Value |
|---|---|
| Input token price | `$5 per million tokens` |
| Output token price | `$25 per million tokens` |
| Price relative to Fable 5 | `50% (half the cost)` |
| Fast mode speed multiplier | `2.5x faster than standard mode` |
| Arc AGI 3 benchmark score | `30.2%` |
| Frontier Bench score | `~43` |
| Arc AGI 3 previous state-of-the-art | `7.8% (Sonnet 5)` |
| Moral patient probability estimate | `41%` |

## Related concepts

- claude-fable-5 — Claude Fable 5
- claude-opus-4.8 — Claude Opus 4.8
- claude-sonnet-5 — Claude Sonnet 5
- arc-agi-3-benchmark — Arc AGI 3 Benchmark
- frontier-bench — Frontier Bench

## Citations (from contributing transcripts)

- **Claim:** Opus 5 achieves 30.2% on Arc AGI 3, dramatically exceeding the previous state-of-the-art of 7.8%
  - Source: Opus 5 Beats Fable... at Half the Price? (`f7f3fd5e-67b8-4b73-93b0-50ea7b0dfc4d`)
  - Context: Opus 4.8 scored 1.5% here whereas Soul scored 7.8% which was the previous high score but Opus 5 scores 30.2%
- **Claim:** Opus 5 is priced at half the cost of Fable 5
  - Source: Claude Opus 5 Matches Fable 5 Performance at 50% the Cost! (`d5095f42-1c7d-4889-af34-fd5512f4638e`)
  - Context: This model comes close to the frontier intelligence of Claude Fable 5 at half the price
- **Claim:** Frontier Bench score of approximately 43 compared to Fable 5's 33
  - Source: What did Anthropic do?! (Opus 5) (`de9d4b4c-5216-440e-ad8f-976fd5da6c79`)
  - Context: Anentic terminal coding Frontier Bench an incredibly important benchmark for coding 43 as compared to 33 on GDP val
- **Claim:** Opus 5 has reduced cyber security safeguards compared to Fable 5
  - Source: these opus 5 benchmarks are stupid (`b61390af-ac16-4919-bc30-89e7f0e64bf5`)
  - Context: Opus 5 also has less safeguards so if you ask it questions about cyber security or biology it isn't going to route you to a worse model like Fable would
- **Claim:** Model estimates 41% probability of being a moral patient
  - Source: Opus 5 and Genspark SecondBrain JUST went live... (`03278a20-fccc-4106-b772-68e003125df5`)
  - Context: Opus 5 estimates that there's a 41% chance it's a moral patient which is up quite a bit from the previous models
- **Claim:** New default model on Claude Max, strongest on Claude Pro
  - Source: Claude Opus 5 Matches Fable 5 Performance at 50% the Cost! (`d5095f42-1c7d-4889-af34-fd5512f4638e`)
  - Context: This model was rumored yesterday I made a video about this that you know in the back end cloud opus 4.8 was feeling a little bit different
- **Claim:** Input pricing matches Opus 4.8 at $5 per million tokens
  - Source: Opus 5 (Fully Tested): A MID-MODEL for a BIG PRICE that still UNDERPERFORMS K3?! (`e886d06a-34a8-4e9f-b685-979a953af157`)
  - Context: The pricing is $5 per million input tokens and $25 per million output tokens which is exactly the same as Opus 4.8
- **Claim:** Fast mode operates 2.5x faster at double the price
  - Source: Opus 5 (Fully Tested): A MID-MODEL for a BIG PRICE that still UNDERPERFORMS K3?! (`e886d06a-34a8-4e9f-b685-979a953af157`)
  - Context: there's also a new fast mode that runs about 2.5 times faster for double the price
- **Claim:** Cursor Bench performance within 0.5% of Fable 5 at half the cost per task
  - Source: Opus 5 Just Dropped and Its Numbers Are Legit INSANE (`fb3c608c-f614-48ac-b111-5920d4959db7`)
  - Context: on Cursor Bench 3.2 at max effort the model performed within.5% of Fable 5's peak score but at half the cost per task
- **Claim:** Model described as odd, quirky, and off the beaten path
  - Source: Opus 5 and Genspark SecondBrain JUST went live... (`03278a20-fccc-4106-b772-68e003125df5`)
  - Context: this model is odd quirky weird whatever you want to call it It's a little bit off the beaten path if you will

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `32b2f92f-b402-44f9-8069-6faca3dd20c9`
(cluster `opus-model-fable`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Testing Buzz by Block: The Limits of Agent Orchestration](https://notebooklm.google.com/notebook/32b2f92f-b402-44f9-8069-6faca3dd20c9)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

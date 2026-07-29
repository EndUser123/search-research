---
title: "AI Model Benchmarking Performance"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  AI model benchmarking involves evaluating and ranking AI models on standardized tests and real-world task simulations to determine relative performance, with results often influencing adoption decisions and market positioning among labs.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 23bf4931-d0cb-4550-9d11-f9b38843254a" (WL-Pilot: Claude Skills & Code, synced 2026-07-27)
  - "NotebookLM source 24dd4898-fee6-49f7-b022-ab458d75d764" (Qwen 3.7 Max: The Model Beating Claude Opus (Nobody's Talking About), synced 2026-07-27)
  - "NotebookLM source 3f0ac243-4260-4a16-918b-edd6391bb97c" (GLM 5.2 Works BEST with the RIGHT Harness, synced 2026-07-27)
  - "NotebookLM source 4b868a0a-47eb-4e1a-bd19-345f17940591" (NEW Claude Sonnet 5 is INSANE!, synced 2026-07-27)
  - "NotebookLM source 4c583e9f-4e38-40d3-b2d8-755c18b54707" (Claude Opus 4.8 Is Acting Like Opus 5..., synced 2026-07-27)
  - "NotebookLM source 5bc26b09-abe3-465a-91d9-9301458b1a48" (Mistral Medium 3.5 BEATS Kimi AND Claude? 🤯 Local AI TEST & REVIEW, synced 2026-07-27)
  - "NotebookLM source 7afd63d7-7528-4498-8455-f0a45487c36e" (NEW Claude Sonnet 5 coming?, synced 2026-07-27)
  - "NotebookLM source 7b488c0b-22a7-42e5-984c-172ebcd86215" (Sonnet 5 vs Opus Head-to-Head | The Results Will Surprise You, synced 2026-07-27)
  - "NotebookLM source 8dacd1b7-a0a0-495a-a17b-5c45ebe7d18b" (Plan with Claude Opus, Build with Kimi K2.6? LIVE Mixed-Provider Benchmark, synced 2026-07-27)
  - "NotebookLM source 91d62939-8475-49b4-bc7d-fcaf114ef02f" (Rumor: Claude Opus 5 this Thursday, synced 2026-07-27)
  - "NotebookLM source aa5e2326-70b3-4bc0-bf80-936758e5e524" (I Replaced Claude Opus With GLM 5.2 Inside Claude Code — Here's Where the #1 Open Model Breaks, synced 2026-07-27)
  - "NotebookLM source d43551a0-85ae-4373-b6e7-6aa380745f08" (Claude Opus 4.8 Review: New Demos You Need to See, synced 2026-07-27)
  - "NotebookLM source db059f17-14b2-4e34-946b-815cfe77c450" (Claude Opus 4.8 actually blew my mind..., synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: ai-model-benchmarking-performance
    - level: notebook
      id: 23bf4931-d0cb-4550-9d11-f9b38843254a
      title: WL-Pilot: Claude Skills & Code
      url: https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a
    - level: cluster
      id: 3
      name: claude-opus-model
relations:
  - target: wiki/concepts/claude-opus-4.8.md
    type: related
  - target: wiki/concepts/glm-5.2.md
    type: related
  - target: wiki/concepts/qwen-3.7-max.md
    type: related
---

# AI Model Benchmarking Performance

## Decision context

**Definition:** AI model benchmarking involves evaluating and ranking AI models on standardized tests and real-world task simulations to determine relative performance, with results often influencing adoption decisions and market positioning among labs.

Synthesized from **12 contributing transcripts** in NotebookLM notebook *WL-Pilot: Claude Skills & Code*, clustered into the "claude-opus-model" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Terminal Bench 2.0 simulates a real software engineer working in a sandbox terminal, measuring practical coding capabilities beyond theoretical benchmarks
- Real-world agentic work benchmarks published by Artificial Analysis rank models by ELO score for tasks involving planning, research, and multi-step implementation
- Mixture of Experts (MoE) architecture allows large models like GLM 5.2 (753B parameters) to only activate ~40B parameters at runtime, maintaining speed while scaling parameters
- Agentic coding benchmarks test models on browser use, terminal operations, and autonomous multi-step task completion
- Reasoning effort settings allow users to adjust how much computation a model uses per response, trading speed for quality

## Verifiable values

| Name | Value |
|---|---|
| Qwen 3.7 Max Terminal Bench 2.0 score | `69.7` |
| Deepseek V3 Pro Max Terminal Bench 2.0 score | `67.9` |
| Claude Opus 4.6 Max Terminal Bench 2.0 score | `65.4` |
| Kimi K2.6 Thinking Terminal Bench 2.0 score | `66.7` |
| GLM 5.2 ELO score on Artificial Analysis agentic benchmark | `15009` |
| GLM 5.2 total parameters | `753 billion` |
| GLM 5.2 active parameters (MoE) | `~40 billion` |
| Claude Opus 4.8 price per million tokens | `$5` |
| Claude Sonnet 5 price per million tokens | `$3` |
| Claude Sonnet 5 price per million tokens | `$3` |

## Related concepts

- [[claude-opus-4.8]] — Claude Opus 4.8
- [[glm-5.2]] — GLM 5.2
- [[qwen-3.7-max]] — Qwen 3.7 Max
- [[claude-sonnet-5]] — Claude Sonnet 5
- [[mixture-of-experts-architecture]] — Mixture of Experts Architecture
- [[agentic-ai]] — Agentic AI
- [[terminal-bench-2.0]] — Terminal Bench 2.0

## Citations (from contributing transcripts)

- **Claim:** Qwen 3.7 Max scores 69.7 on Terminal Bench 2.0, beating Opus 4.6 Max at 65.4 and Kimi K2.6 Thinking at 66.7
  - Source: Qwen 3.7 Max: The Model Beating Claude Opus (Nobody's Talking About) (`24dd4898-fee6-49f7-b022-ab458d75d764`)
  - Context: On Terminal Bench 2.0 which is the benchmark that basically simulates a real software engineer working in a sandbox terminal Coin 3.7 Max scores 69.7 beating Deepseek version pro max at 67.9 Opus 4.6 Max at 65.4 and Kimmy K2.6 Thinking at 66.7
- **Claim:** GLM 5.2 ranks third overall on Artificial Analysis real-world agentic work benchmark with ELO score of 15009
  - Source: GLM 5.2 Works BEST with the RIGHT Harness (`3f0ac243-4260-4a16-918b-edd6391bb97c`)
  - Context: GLM 5.2 as of today is ranked third overall its ELO score at X high reasoning efforts at 15009 uh only behind Claude Fable 5 and Opus 4.8
- **Claim:** GLM 5.2 is the leading openweight model ahead of Claude Sonnet 5 and Opus 4.8
  - Source: GLM 5.2 Works BEST with the RIGHT Harness (`3f0ac243-4260-4a16-918b-edd6391bb97c`)
  - Context: GLM 5.2 right now is the leading openweight model
- **Claim:** GLM 5.2 has 753 billion parameters but uses Mixture of Experts to activate only ~40 billion at a time
  - Source: I Replaced Claude Opus With GLM 5.2 Inside Claude Code — Here's Where the #1 Open Model Breaks (`aa5e2326-70b3-4bc0-bf80-936758e5e524`)
  - Context: it is huge 753 billion parameters but it is a mixture of experts design so it only switches on about 40 billion at a time which is what keeps it fast
- **Claim:** Sonnet 5 shows serious improvement over Sonnet 4.6 in agentic coding and computer use benchmarks, numbers close to Opus 4.8
  - Source: Sonnet 5 vs Opus Head-to-Head | The Results Will Surprise You (`7b488c0b-22a7-42e5-984c-172ebcd86215`)
  - Context: Sonnet 5 is built to be the most agentic Sonic model yet these numbers are pretty close to Opus 4.8
- **Claim:** Claude Opus 4.8 costs $5 per million tokens while Sonnet 5 costs $3 per million tokens
  - Source: Sonnet 5 vs Opus Head-to-Head | The Results Will Surprise You (`7b488c0b-22a7-42e5-984c-172ebcd86215`)
  - Context: Claude Fable 5 model is $10 for every million tokens opus 4.8 is $5 for every million tokens and then Sonnet 5 is $3 for every million tokens

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [WL-Pilot: Claude Skills & Code](https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

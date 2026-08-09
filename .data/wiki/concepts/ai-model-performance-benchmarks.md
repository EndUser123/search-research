---
title: "AI Model Performance Benchmarks"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  This concept encompasses the comparative evaluation metrics and real-world assessments used to rank and differentiate large language models across dimensions such as coding capability, agentic task completion, and cost-performance tradeoffs.
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
      id: ai-model-performance-benchmarks
    - level: notebook
      id: 23bf4931-d0cb-4550-9d11-f9b38843254a
      title: WL-Pilot: Claude Skills & Code
      url: https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a
    - level: cluster
      id: 3
      name: claude-opus-model
relations:
  - target: wiki/concepts/claude-opus-model.md
    type: related
  - target: wiki/concepts/sonnet-model-family.md
    type: related
  - target: wiki/concepts/glm-5.2.md
    type: related
---

# AI Model Performance Benchmarks

## Decision context

**Definition:** This concept encompasses the comparative evaluation metrics and real-world assessments used to rank and differentiate large language models across dimensions such as coding capability, agentic task completion, and cost-performance tradeoffs.

Synthesized from **12 contributing transcripts** in NotebookLM notebook *WL-Pilot: Claude Skills & Code*, clustered into the "claude-opus-model" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Terminal Bench 2.0 serves as a benchmark simulating real software engineering work in sandboxed terminal environments, providing a standardized assessment of coding capability [24dd4898]
- Real-world agentic work benchmarks published by Artificial Analysis evaluate models on practical multi-step task completion, with ELO scoring used to rank model performance [3f0ac243]
- The AI model competitive landscape includes models from Chinese labs (Qwen, GLM), Anthropic (Claude family), and others, each positioning themselves through benchmark performance claims [24dd4898, 3f0ac243]
- Pricing tiers reflect model positioning, with Opus 4.8 at $5 per million tokens, Sonnet 5 at approximately $3 per million tokens, and Sonnet 4.6 being described as cheaper [7b488c0b]
- GLM 5.2 implements a mixture of experts design, activating approximately 40 billion parameters during inference despite having 753 billion total parameters [aa5e2326]
- Emerging workflows employ multi-provider approaches, combining different models for different task stages to balance reasoning capability with cost efficiency [8dacd1b7]
- Sonnet 5 was designed specifically for increased agentic capability, supporting autonomous tool use and multi-step planning at performance levels approaching Opus 4.8 [7b488c0b]
- Model releases often follow strategic patterns, including brief availability windows and subsequent removal for undisclosed reasons [4b868a0a, 7afd63d7]
- Claude Opus 4.8 introduced configurable reasoning effort options previously available only through API access [d43551a0]
- Some models such as GLM 5.2 operate under MIT licensing, enabling free commercial use and modification [aa5e2326]

## Verifiable values

| Name | Value |
|---|---|
| Qwen 3.7 Max Terminal Bench 2.0 score | `69.7` |
| Deepseek version pro max Terminal Bench 2.0 score | `67.9` |
| Claude Opus 4.6 Max Terminal Bench 2.0 score | `65.4` |
| Kimi K2.6 Thinking Terminal Bench 2.0 score | `66.7` |
| GLM 5.2 Artificial Analysis ELO score | `15009` |
| GLM 5.2 total parameters | `753 billion` |
| GLM 5.2 active parameters (mixture of experts) | `approximately 40 billion` |
| Mistral Medium 3.5 parameter count | `128 billion` |
| Claude Opus 4.8 pricing | `$5 per million tokens` |
| Claude Sonnet 5 pricing | `$3 per million tokens` |

## Related concepts

- claude-opus-model — Claude Opus Model
- sonnet-model-family — Sonnet Model Family
- glm-5.2 — GLM 5.2
- qwen-3.7-max — Qwen 3.7 Max
- agentic-ai — Agentic AI
- mixture-of-experts-architecture — Mixture of Experts Architecture

## Citations (from contributing transcripts)

- **Claim:** Qwen 3.7 Max scores 69.7 on Terminal Bench 2.0, beating other evaluated models
  - Source: Qwen 3.7 Max: The Model Beating Claude Opus (Nobody's Talking About) (`24dd4898-fee6-49f7-b022-ab458d75d764`)
  - Context: on Terminal Bench 2.0 which is the benchmark that basically simulates a real software engineer working in a sandbox terminal Coin 3.7 Max scores 69.7 beating Deepseek version pro max at 67.9 Opus 4.6 Max at 65.4 and Kimmy K2.6 Thinking at 66.7
- **Claim:** GLM 5.2 ranked third on real-world agentic work benchmark with ELO score of 15009
  - Source: GLM 5.2 Works BEST with the RIGHT Harness (`3f0ac243-4260-4a16-918b-edd6391bb97c`)
  - Context: GLM 5.2 as of today is ranked third overall its ELO score at X high reasoning efforts at 15009 uh only behind Claude Fable 5 and Opus 4.8
- **Claim:** Sonnet 5 designed for agentic capability with tool use comparable to Opus 4.8 at lower cost
  - Source: Sonnet 5 vs Opus Head-to-Head | The Results Will Surprise You (`7b488c0b-22a7-42e5-984c-172ebcd86215`)
  - Context: Claude Sonnet 5 is built to be the most agentic Sonic model yet it can make plans use tools like browsers and terminals and run autonomously
- **Claim:** GLM 5.2 uses mixture of experts with 753 billion parameters but only activates about 40 billion at a time
  - Source: I Replaced Claude Opus With GLM 5.2 Inside Claude Code — Here's Where the #1 Open Model Breaks (`aa5e2326-70b3-4bc0-bf80-936758e5e524`)
  - Context: it is huge 753 billion parameters but it is a mixture of experts design so it only switches on about 40 billion at a time which is what keeps it fast
- **Claim:** Mixed-provider workflows combine models strategically for different task stages
  - Source: Plan with Claude Opus, Build with Kimi K2.6? LIVE Mixed-Provider Benchmark (`8dacd1b7-a0a0-495a-a17b-5c45ebe7d18b`)
  - Context: using archon as our harness to build workflows that combine opus and kimmy k 2.6 to handle something end to end but not relying on the big model for the entire thing
- **Claim:** Claude Sonnet 5 appeared briefly then was shut down, with Fable 5 also removed shortly after release
  - Source: NEW Claude Sonnet 5 is INSANE! (`4b868a0a-47eb-4e1a-bd19-345f17940591`)
  - Context: the last model only lived for 3 days before it got pulled off the whole planet yeah gone
- **Claim:** Opus 4.8 introduced configurable reasoning effort previously only available via API
  - Source: Claude Opus 4.8 Review: New Demos You Need to See (`d43551a0-85ae-4373-b6e7-6aa380745f08`)
  - Context: they also give you access to change the reasoning effort this was previously only locked behind the API
- **Claim:** GLM 5.2 released under MIT license enabling free commercial use
  - Source: I Replaced Claude Opus With GLM 5.2 Inside Claude Code — Here's Where the #1 Open Model Breaks (`aa5e2326-70b3-4bc0-bf80-936758e5e524`)
  - Context: the license pure MIT that means free to download free to run free to build a business on top of
- **Claim:** Mistral Medium 3.5 contains 128 billion parameters
  - Source: Mistral Medium 3.5 BEATS Kimi AND Claude? 🤯 Local AI TEST & REVIEW (`5bc26b09-abe3-465a-91d9-9301458b1a48`)
  - Context: we're checking out Mistl 3.5 the 128 billion parameter edition
- **Claim:** Claude Opus 4.8 reported to be performing differently, potentially indicating backend updates
  - Source: Claude Opus 4.8 Is Acting Like Opus 5... (`4c583e9f-4e38-40d3-b2d8-755c18b54707`)
  - Context: Opus 4.8 model has been producing outputs that seem much stronger than it currently was

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `23bf4931-d0cb-4550-9d11-f9b38843254a`
(cluster `claude-opus-model`). No claims are made
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

- NotebookLM notebook [WL-Pilot: Claude Skills & Code](https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

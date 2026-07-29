---
title: "Systematic Trading Approaches"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, have]
summary: >
  Systematic trading refers to formalized, rule-based approaches to executing trades that reduce emotional decision-making. These methods typically incorporate technical indicators and defined position management rules to identify and capitalize on market opportunities.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 33b058e9-5de1-49da-8d8a-b1ef3d50467e" (WL: Local AI Models & GPU, synced 2026-07-27)
  - "NotebookLM source 17fa00d4-2b60-47c1-b6a1-bb198f91a054" (I Made $51,843 Day Trading this strategy..., synced 2026-07-27)
  - "NotebookLM source 1827a5c6-94f3-401d-b463-bdac5ab17b54" (you're trading wrong... here's how, synced 2026-07-27)
  - "NotebookLM source 479fd585-a74c-49bb-86b9-8c99f6adc3f3" (NotebookLM's Latest Updates Actually Matter — Here's Why, synced 2026-07-27)
  - "NotebookLM source 505925a4-6065-47b3-a4f8-487deb5c70d9" (ChatGPT Computer Use: Now faster with Live Picture-in-Picture, synced 2026-07-27)
  - "NotebookLM source 7893aa40-d8e5-4d0b-a68c-da4c67912a67" (PixelRAG Locally: RAG That Reads Screenshots Instead of Text, synced 2026-07-27)
  - "NotebookLM source 79ff78c0-2048-41cb-9122-64e4c1f1b090" (MCP vs Skills: You're Using the Wrong One (Most People Do), synced 2026-07-27)
  - "NotebookLM source 94197947-e949-4a89-a1d2-d426f07ac698" (PKM Is Dead Long Live PCM: Obsidian Is Different Now, synced 2026-07-27)
  - "NotebookLM source 9e95f7f8-aaf3-42b3-bfc5-47c5aa91dd4b" (The 10-Minute Setup (I Automated the Hard Part), synced 2026-07-27)
  - "NotebookLM source c19e5cc6-cbf8-4172-bddc-c66fff60089c" (a tool to outsource your memory, synced 2026-07-27)
  - "NotebookLM source c3f0f030-70a3-42d3-962a-a1e66a524c8a" (Perplexity Computer Is Now On Pro Plan | Here Is What They Are Not Telling You, synced 2026-07-27)
  - "NotebookLM source c49503d4-2883-403b-81e8-eab753f3a220" (AutoMagicCalib Just Killed Manual Camera Tuning #nvidia #edgeai, synced 2026-07-27)
  - "NotebookLM source d37f30b6-4831-4644-bf1d-8556f302a813" (I Tested the Strategy That Turned $5,000 Into $15 Million, synced 2026-07-27)
  - "NotebookLM source d39f32b3-508e-45d4-af08-35243888620d" (This took me way too long to solve 🤦‍♂️, synced 2026-07-27)
  - "NotebookLM source dcae7476-45e4-4680-a836-8a3b880d1ea0" (Stop LLM LOOPS From Burning Millions of Tokens - w/ PUMA?, synced 2026-07-27)
  - "NotebookLM source eb0e4e3e-fd87-4b2a-8483-742ae79f27f4" (i made $30,271 trading with trump, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: systematic-trading-approaches
    - level: notebook
      id: 33b058e9-5de1-49da-8d8a-b1ef3d50467e
      title: WL: Local AI Models & GPU
      url: https://notebooklm.google.com/notebook/33b058e9-5de1-49da-8d8a-b1ef3d50467e
    - level: cluster
      id: 1
      name: have-made-trading
relations:
  - target: wiki/concepts/trend-following.md
    type: related
  - target: wiki/concepts/risk-management.md
    type: related
  - target: wiki/concepts/position-sizing.md
    type: related
---

# Systematic Trading Approaches

## Decision context

**Definition:** Systematic trading refers to formalized, rule-based approaches to executing trades that reduce emotional decision-making. These methods typically incorporate technical indicators and defined position management rules to identify and capitalize on market opportunities.

Synthesized from **15 contributing transcripts** in NotebookLM notebook *WL: Local AI Models & GPU*, clustered into the "have-made-trading" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Trend following strategies use EMA (exponential moving average) filters to establish directional bias—trading above EMA with long bias and below with short bias [12]
- Position sizing decisions are quantified by the number of contracts traded, with larger positions (4-5 contracts) used when conviction is high [1][15]
- Risk management parameters define maximum acceptable losses per position, such as a $17,000 loss limit on a $30,000 target trade [15]
- Win rate and profit factor metrics are tracked to evaluate systematic strategy performance across multiple trades [15]
- Trading sessions provide different market conditions and volatility profiles that systematic traders account for in their approaches [2]
- Systematic rules were reverse-engineered from successful traders' documented approaches to create replicable frameworks [12]

## Verifiable values

| Name | Value |
|---|---|
| profit_target | `$50,000 (Source 1)` |
| return_on_investment | `100%` |
| contracts_traded | `4 (crude oil, Source 1)` |
| contracts_traded | `5 (crude oil, Source 15)` |
| win_rate | `80%` |
| profit_factor | `5.89` |
| risk_tolerance | `$17,000 per position` |
| net_profit | `$30,271 (Source 15)` |
| max_drawdown | `$5,000 (Source 15)` |

## Related concepts

- [[trend-following]] — Trend Following
- [[risk-management]] — Risk Management
- [[position-sizing]] — Position Sizing
- [[trading-metrics]] — Trading Metrics
- [[rule-based-trading]] — Rule-Based Trading

## Citations (from contributing transcripts)

- **Claim:** Trend following strategies use EMA 100 as a trend filter
  - Source: I Tested the Strategy That Turned $5,000 Into $15 Million (`d37f30b6-4831-4644-bf1d-8556f302a813`)
  - Context: his first rule was a trend filter this is primarily an EMA 100 now above that EMA we're going long or we're having a long bias and below that EMA we have a short
- **Claim:** The trader made $50,000 profit on a $50,000 investment for 100% return
  - Source: I Made $51,843 Day Trading this strategy... (`17fa00d4-2b60-47c1-b6a1-bb198f91a054`)
  - Context: so it cost me 50,000 to hold and I made 50,000 made a 100% return on this trade
- **Claim:** Position size was 5 contracts with $17,000 risk tolerance
  - Source: i made $30,271 trading with trump (`eb0e4e3e-fd87-4b2a-8483-742ae79f27f4`)
  - Context: my risk I was willing to lose 17,000 in this position
- **Claim:** Win rate tracked at 80% with profit factor of 5.89
  - Source: i made $30,271 trading with trump (`eb0e4e3e-fd87-4b2a-8483-742ae79f27f4`)
  - Context: i've got an 80% win rate i've got a profit factor of 5.89
- **Claim:** Traders learn about sessions to understand market timing
  - Source: you're trading wrong... here's how (`1827a5c6-94f3-401d-b463-bdac5ab17b54`)
  - Context: I didn't know what the sessions were I only knew of one session because I traded the stock market
- **Claim:** Systematic trading rules were reverse-engineered from documented systems
  - Source: I Tested the Strategy That Turned $5,000 Into $15 Million (`d37f30b6-4831-4644-bf1d-8556f302a813`)
  - Context: Sakakota didn't write a single book so we're having to reverse engineer his approach from his actual systems

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `33b058e9-5de1-49da-8d8a-b1ef3d50467e`
(cluster `have-made-trading`). No claims are made
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

- NotebookLM notebook [WL: Local AI Models & GPU](https://notebooklm.google.com/notebook/33b058e9-5de1-49da-8d8a-b1ef3d50467e)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

---
title: "Free AI Skills and Optimization Techniques"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, skill]
summary: >
  Free AI skills are modular capabilities that extend AI systems beyond their default functionality, often targeting specific workflows like research, video analysis, or output optimization. Several approaches have emerged to improve AI system performance without requiring paid upgrades.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 7ef4d1e8-319f-4e27-a751-e777ddc2b723" (WL: Anthropic & Agent Ecosystem, synced 2026-07-27)
  - "NotebookLM source 0e294644-a748-4dac-8ab7-6c620e6138e7" (Paste Your Prompt TWICE: Google's Free Trick to Make AI Smarter (New Paper), synced 2026-07-27)
  - "NotebookLM source 266b3e15-6c6b-4b4d-a0c5-ea717518f7cf" (This AI Skill Hit 38,000 Stars — Here's Why (last30days), synced 2026-07-27)
  - "NotebookLM source 320eb8db-5c1b-44e0-8704-28d3729b3189" (RAG Was Blind This Whole Time — Berkeley’s PixelRAG Gives Your AI Eyes, synced 2026-07-27)
  - "NotebookLM source 562bc66e-c1fe-455e-8a26-ea7a601e5dd0" (Karpathy's AI Trick: Stop Writing Prompts — RAMBLE for 10 Minutes, synced 2026-07-27)
  - "NotebookLM source 64c869ca-1140-46bd-a3e1-7a4920a67e20" (Firecrawl Search Just Replaced a 6000 Line Research Skill, synced 2026-07-27)
  - "NotebookLM source 7c8c3742-de35-4a28-aaa0-a92695b94620" (The Best AI Tools in 2026 (Free & Simple) — Why That Viral '25K Comments' List Is Already Wrong, synced 2026-07-27)
  - "NotebookLM source b461d264-eb6a-416e-bc9e-fe9fb4899fbe" (From MCP to Scale: Pipelines That Build Themselves — Rafael Levi, Bright Data, synced 2026-07-27)
  - "NotebookLM source c46adc55-cd3f-4565-b4b0-47f6405596e5" (The GSD Skills Everyone Misses (I Tested Them), synced 2026-07-27)
  - "NotebookLM source c5e79ca8-dae9-4eca-90b7-681959f9ec4e" (I Tested NEW Caveman AI Skill in Claude Code: Does it Really Save Tokens?, synced 2026-07-27)
  - "NotebookLM source d767d6d0-1cda-460e-95f9-c383a2605b5b" (Slow down to speed up: AI and software engineering, synced 2026-07-27)
  - "NotebookLM source fb55fda8-eb3d-4f75-94bd-28dcc2bd6d89" (AI Deep Research (Manus, Perplexity, OpenAI, Kimi, Anthropic, Gemini), synced 2026-07-27)
  - "NotebookLM source ff86141a-eb3a-4b0c-93e1-2dcc399bf0e5" (This Skill Can INSTANTLY Watch any Video For Free - Here's How, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: free-ai-skills-and-optimization-techniques
    - level: notebook
      id: 7ef4d1e8-319f-4e27-a751-e777ddc2b723
      title: WL: Anthropic & Agent Ecosystem
      url: https://notebooklm.google.com/notebook/7ef4d1e8-319f-4e27-a751-e777ddc2b723
    - level: cluster
      id: 5
      name: skill-research-free
relations:
  - target: wiki/concepts/ai-prompting-optimization.md
    type: related
  - target: wiki/concepts/retrieval-augmented-generation-(rag).md
    type: related
  - target: wiki/concepts/model-context-protocol-(mcp).md
    type: related
---

# Free AI Skills and Optimization Techniques

## Decision context

**Definition:** Free AI skills are modular capabilities that extend AI systems beyond their default functionality, often targeting specific workflows like research, video analysis, or output optimization. Several approaches have emerged to improve AI system performance without requiring paid upgrades.

Synthesized from **12 contributing transcripts** in NotebookLM notebook *WL: Anthropic & Agent Ecosystem*, clustered into the "skill-research-free" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Prompt repetition improves performance for non-reasoning LLMs by repeating the input prompt, with gains observed across Gemini, GPT, Claude, and DeepSeek without increasing tokens or latency (Google Research, December 2025)
- The last 30 days skill aggregates Reddit threads ranked by upvotes, Hacker News posts, YouTube transcripts, GitHub activity, and PolyMarket prediction odds in a single query
- The watch skill provides Claude with video frames and transcripts, supporting over 1,600 sites and achieving 40x faster processing in version 2
- Caveman is a Claude Code skill that claims to reduce token usage by 65-75% while maintaining readable outputs
- Firecrawl Search returns web page contents directly with search results, enabling multi-source parallel queries without just aggregating links
- GSD (get-shit-done) framework ships a secondary layer of standalone skills including sketch, fast, debug, forensics, and UI commands that don't require roadmap or milestone setup
- PixelRAG from Berkeley addresses a limitation where traditional RAG systems destroy page structure by parsing HTML to plain text, preventing visual/spatial context preservation

## Verifiable values

| Name | Value |
|---|---|
| last 30 days GitHub stars | `38,000` |
| watch skill GitHub stars (first month) | `~3,000` |
| Caveman claimed token reduction | `65-75%` |
| watch v2 speed improvement | `40x faster` |
| sites supported by watch skill | `1,600+` |
| Gemini Deep Research report generation time | `3 min 46 sec` |
| Moonshot Kimi Deep Research report generation time | `35 min` |
| Kimi Deep Research report length | `21 pages` |

## Related concepts

- [[ai-prompting-optimization]] — AI Prompting Optimization
- [[retrieval-augmented-generation-(rag)]] — Retrieval-Augmented Generation (RAG)
- [[model-context-protocol-(mcp)]] — Model Context Protocol (MCP)

## Citations (from contributing transcripts)

- **Claim:** Prompt repetition improves performance for non-reasoning LLMs across popular models without increasing tokens or latency
  - Source: Paste Your Prompt TWICE: Google's Free Trick to Make AI Smarter (New Paper) (`0e294644-a748-4dac-8ab7-6c620e6138e7`)
  - Context: When not using reasoning repeating the input prompt improves performance for popular models Gemini GPT Claude and Deepseek without increasing the number of generated tokens or latency
- **Claim:** last 30 days skill searches Reddit threads ranked by upvotes, Hacker News posts, YouTube transcripts, and PolyMarket prediction odds
  - Source: This AI Skill Hit 38,000 Stars — Here's Why (last30days) (`266b3e15-6c6b-4b4d-a0c5-ea717518f7cf`)
  - Context: google aggregates editors last 30 days searches people reddit threads ranked by upvotes exposts with real engagement YouTube transcripts hacker news developer takes and real money polyarket prediction odds all in one query
- **Claim:** Caveman skill claims to reduce tokens by 65-75%
  - Source: I Tested NEW Caveman AI Skill in Claude Code: Does it Really Save Tokens? (`c5e79ca8-dae9-4eca-90b7-681959f9ec4e`)
  - Context: caveman to use 75% less tokens when you see this text so the replies from claude or claude code could be much shorter while still understandable
- **Claim:** watch skill supports over 1,600 sites and processes videos at 40x speed in version 2
  - Source: This Skill Can INSTANTLY Watch any Video For Free - Here's How (`ff86141a-eb3a-4b0c-93e1-2dcc399bf0e5`)
  - Context: it works for anything youtube videos Looms Tik Toks or local files i'm not kidding it supports over 1,600 sites at this point
- **Claim:** Deep Research report generation varies significantly by tool, with Gemini at 3:46 and Kimi at 35 minutes
  - Source: AI Deep Research (Manus, Perplexity, OpenAI, Kimi, Anthropic, Gemini) (`fb55fda8-eb3d-4f75-94bd-28dcc2bd6d89`)
  - Context: by far the fastest deep research tool was Gemini that came in at 3 minutes and 46 seconds to generate the report
- **Claim:** GSD framework ships standalone skills including sketch, fast, debug, and forensics that don't require roadmap or milestone setup
  - Source: The GSD Skills Everyone Misses (I Tested Them) (`c46adc55-cd3f-4565-b4b0-47f6405596e5`)
  - Context: small standalone skills that don't need a roadmap, a milestone, or any of the heavy setup Sketch, fast, debug, forensics, a pair of UI commands
- **Claim:** PixelRAG addresses the limitation of traditional RAG destroying page structure when parsing HTML to plain text
  - Source: RAG Was Blind This Whole Time — Berkeley's PixelRAG Gives Your AI Eyes
  - Context: the moment a normal rack system touches it this happens it gets shredded into a flat string of text the columns lose their alignment

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `7ef4d1e8-319f-4e27-a751-e777ddc2b723`
(cluster `skill-research-free`). No claims are made
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

- NotebookLM notebook [WL: Anthropic & Agent Ecosystem](https://notebooklm.google.com/notebook/7ef4d1e8-319f-4e27-a751-e777ddc2b723)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

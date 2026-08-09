---
title: "Open Knowledge Format (OKF)"
created: 2026-07-30
source: nlm-sync-2026-07-30
tags: [nlm-synced, reference, google]
summary: >
  The Open Knowledge Format (OKF) is an open specification published by Google Cloud that defines a standardized folder structure of markdown files with YAML front matter, designed to provide AI agents with organized internal business knowledge in place of fragmented, unstructured document retrieval a
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c" (Perplexity: perplexity-videos-tab, synced 2026-07-30)
  - "NotebookLM source 1eb93972-f714-4168-882f-25a405ba5a36" (Google Just Made Vector Databases Optional — And It’s Just a Folder (OKF), synced 2026-07-30)
  - "NotebookLM source 29732b49-db37-47bc-800f-732dba684db8" (Google's Open Knowledge Format: Just Markdown for AI Agents, synced 2026-07-30)
  - "NotebookLM source 3714b5e0-6fd6-434b-94ad-5cf838b1abe3" (Google Just Invented a Universal Language for AI Knowledge, synced 2026-07-30)
  - "NotebookLM source 532a2a48-f14e-4d3c-9bb8-bfdb38d9956b" (Google OKF + RAG: The Ultimate AI Agent Architecture, synced 2026-07-30)
  - "NotebookLM source 686ce484-32d5-4bca-a88e-d182ead9ba1a" (Open Knowledge Format Explained - Google's Secret Tool OKF for Smarter AI Agents, synced 2026-07-30)
  - "NotebookLM source 69fdad31-b76c-4d69-8de9-8af56efd4f6d" (Open Knowledge Format: How AI Will Read Your Business Now, synced 2026-07-30)
  - "NotebookLM source 75498905-023c-4ebe-8fab-986ef8a2f2b7" (Google Just Turned AI Memory Into a Folder — Open Knowledge Format Explained, synced 2026-07-30)
  - "NotebookLM source 821290d6-2e3f-486f-ac30-a5d272bfbb3c" (The Ultimate Knowledge Base: Bring YouTube Into Your AI Second Brain, synced 2026-07-30)
  - "NotebookLM source 85671601-ea3b-47ca-adc0-dfe240984eb6" (Google Open Knowledge Format (OKF) Explained: Is This the New Standard for AI Agent Context?, synced 2026-07-30)
  - "NotebookLM source a5a1aabb-2755-45f9-b39b-b19f83c4c756" (Google OKF vs RAG Confusion, Finally Cleared Up, synced 2026-07-30)
  - "NotebookLM source e467effa-165f-4209-ab7b-0936ecc08847" (Google's OKF: Why a Folder Beats the Vector Database, synced 2026-07-30)
  - "NotebookLM source e9d0e4a2-1e19-43df-a316-5c395ac40df8" (Google's OKF: The Simple Folder Replacing Vector Databases, synced 2026-07-30)
  - "NotebookLM source efffc65d-22d2-4b79-a55f-bfc4beef6b4d" (Introducing the Open Knowledge Format, synced 2026-07-30)
provenance:
  chain:
    - level: concept
      id: open-knowledge-format-okf
    - level: notebook
      id: ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c
      title: Perplexity: perplexity-videos-tab
      url: https://notebooklm.google.com/notebook/ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c
    - level: cluster
      id: 1
      name: google-knowledge-format
relations:
  - target: wiki/concepts/retrieval-augmented-generation-(rag).md
    type: related
  - target: wiki/concepts/vector-databases.md
    type: related
  - target: wiki/concepts/mcp-(model-context-protocol).md
    type: related
---

# Open Knowledge Format (OKF)

## Decision context

**Definition:** The Open Knowledge Format (OKF) is an open specification published by Google Cloud that defines a standardized folder structure of markdown files with YAML front matter, designed to provide AI agents with organized internal business knowledge in place of fragmented, unstructured document retrieval approaches.

Synthesized from **13 contributing transcripts** in NotebookLM notebook *Perplexity: perplexity-videos-tab*, clustered into the "google-knowledge-format" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- OKF uses plain markdown files with YAML front matter metadata, making knowledge readable in any text editor and renderable on GitHub [2]
- The format ships as a simple folder structure that can be distributed as a tarball, hosted in any git repository, or mounted on any file system [2]
- Google Cloud's data cloud team authored the specification, with tech leads Sam McViti and Amir Hormati credited in the announcement [2]
- The specification launched as version 0.1 in June 2026 as an open standard, with Google explicitly inviting other vendors and the community to adopt and extend it [2]
- Unlike retrieval-based approaches that shred documents into fragments and discard structural relationships, OKF preserves curated knowledge in its original context [4][7]
- The format defines three guiding principles: just markdown, just files, and just YAML front matter [2]
- OKF enables precise, auditable answers with direct source links, as demonstrated when a refund window query returned exactly '14 days with a link straight to the source policy' [4]
- The approach addresses the problem of scattered organizational knowledge that exists across database schemas, metrics definitions, runbooks, code comments, and internal wikis [11][13]
- OKF complements rather than replaces retrieval-based approaches; it functions as a format while retrieval systems function as a process [10]
- The format follows the same standardization pattern as MCP (agent-to-tool standard) and A2A (agent-to-agent standard), establishing an agent-to-knowledge-base standard [8]

## Verifiable values

| Name | Value |
|---|---|
| Specification version | `0.1` |
| Release month/year | `June 2026` |
| Authoring team | `Google Cloud data cloud team` |
| Supported metadata format | `YAML front matter` |
| Knowledge representation format | `Markdown` |

## Related concepts

- [[retrieval-augmented-generation-(rag)]] — Retrieval Augmented Generation (RAG)
- vector-databases — Vector Databases
- [[mcp-(model-context-protocol)]] — MCP (Model Context Protocol)
- [[a2a-(agent-to-agent-protocol)]] — A2A (Agent-to-Agent Protocol)
- llm-wiki — LLM Wiki

## Citations (from contributing transcripts)

- **Claim:** OKF uses plain markdown files with YAML front matter as its core structure
  - Source: Google's Open Knowledge Format: Just Markdown for AI Agents (`29732b49-db37-47bc-800f-732dba684db8`)
  - Context: Google describes it in three words just markdown just files just YAML front matter
- **Claim:** The specification was authored by Google Cloud's data cloud team
  - Source: Google's Open Knowledge Format: Just Markdown for AI Agents (`29732b49-db37-47bc-800f-732dba684db8`)
  - Context: OKF comes from the data cloud team written up by tech leads Sam McViti and Amir Hormati
- **Claim:** OKF launched as an open specification inviting community adoption
  - Source: Google's Open Knowledge Format: Just Markdown for AI Agents (`29732b49-db37-47bc-800f-732dba684db8`)
  - Context: The framing is deliberately humble This is an open specification not a product Google is explicitly inviting other vendors and the community to adopt it extend it
- **Claim:** The refund window example demonstrates OKF's precision over retrieval-based approaches
  - Source: Google OKF + RAG: The Ultimate AI Agent Architecture (`532a2a48-f14e-4d3c-9bb8-bfdb38d9956b`)
  - Context: Ask it the same question and it answers exactly 14 days with a link straight to the source policy
- **Claim:** RAG shreds documents into fragments while OKF preserves structured context
  - Source: Google OKF + RAG: The Ultimate AI Agent Architecture (`532a2a48-f14e-4d3c-9bb8-bfdb38d9956b`)
  - Context: It shredded your clean structured policy into fragments grabbed the three that look similar and threw away the order that made them mean anything
- **Claim:** RAG is a process while OKF is a format, making them complementary rather than competing approaches
  - Source: Google OKF vs RAG Confusion, Finally Cleared Up (`a5a1aabb-2755-45f9-b39b-b19f83c4c756`)
  - Context: Rag is a process OKF is a format Comparing them is a category error
- **Claim:** OKF establishes an agent-to-knowledge-base standard alongside MCP and A2A
  - Source: The Ultimate Knowledge Base: Bring YouTube Into Your AI Second Brain (`821290d6-2e3f-486f-ac30-a5d272bfbb3c`)
  - Context: just like MCP created the agent to tool standard and A2A created the agent to agent standard okf is creating the agent to knowledgebased standard
- **Claim:** Version 0.1 was released in June 2026
  - Source: Open Knowledge Format: How AI Will Read Your Business Now (`69fdad31-b76c-4d69-8de9-8af56efd4f6d`)
  - Context: It is not a ranking factor It's not a product to buy It is a very simple and free way to organize knowledge so AI can read that information Again with a lot of the other things

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c`
(cluster `google-knowledge-format`). No claims are made
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

- NotebookLM notebook [Perplexity: perplexity-videos-tab](https://notebooklm.google.com/notebook/ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

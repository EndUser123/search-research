---
title: "Vector Search vs Plain Text Search"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, vector]
summary: >
  Recent research and industry implementations have challenged the assumption that vector databases are necessary for AI knowledge retrieval, with multiple studies and practical deployments demonstrating that traditional text search approaches can match or exceed vector search performance for many age
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8b807d28-b283-4de3-a369-4ff5e065ac92" (WL: Claude Code Repos & Tools, synced 2026-07-27)
  - "NotebookLM source 4df24149-8372-4bee-bc58-adfc7a3c58e5" (Maybe It’s Time to Leave Windows, synced 2026-07-27)
  - "NotebookLM source 58c88362-f5e0-4e3c-86d1-4716fde32a64" (Grep vs vector search. #ai #tech #techtech, synced 2026-07-27)
  - "NotebookLM source 5b63a5f2-46f7-40bd-ad51-0f8faa2950c9" (PocketBase + HTMX: A Whole Production App Built in One File, synced 2026-07-27)
  - "NotebookLM source 5e499223-6f5f-47e7-8634-bba8d9d3396a" (Google OKF + Claude : Why We Stopped Using RAG, synced 2026-07-27)
  - "NotebookLM source 64ea62d7-db16-455c-a3e6-c885b6547b0c" (Claude Code Just Gave My Obsidian OS a HUGE Glow Up, synced 2026-07-27)
  - "NotebookLM source 7cbcb6f8-a170-4ce5-be92-9004895b94ec" (OKF kills vector databases but creates 3 new ones #Google #shorts, synced 2026-07-27)
  - "NotebookLM source b916647b-323b-4567-a664-b98946e35ca6" (🚀 OKF vs Vector Databases: Is AI Knowledge Management Entering a New Era?, synced 2026-07-27)
  - "NotebookLM source c2d110ef-8287-405c-8a72-9752b3a7340c" (Dolt: This Makes SQL Feel Like Git, synced 2026-07-27)
  - "NotebookLM source c67c64b5-c582-4b22-b4cd-af8698f83455" (Google's NEW AutoSync Just DESTROYED Notion (Free & Auto-Updates), synced 2026-07-27)
  - "NotebookLM source daab95e2-87e2-4895-b9af-02cbd7cfc12e" (Blume turns a folder of Markdown or MDX into a polished documentation site, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: vector-search-vs-plain-text-search
    - level: notebook
      id: 8b807d28-b283-4de3-a369-4ff5e065ac92
      title: WL: Claude Code Repos & Tools
      url: https://notebooklm.google.com/notebook/8b807d28-b283-4de3-a369-4ff5e065ac92
    - level: cluster
      id: 2
      name: vector-google-every
relations:
  - target: wiki/concepts/open-knowledge-format.md
    type: related
  - target: wiki/concepts/rag-alternative-approaches.md
    type: related
  - target: wiki/concepts/agent-memory-management.md
    type: related
---

# Vector Search vs Plain Text Search

## Decision context

**Definition:** Recent research and industry implementations have challenged the assumption that vector databases are necessary for AI knowledge retrieval, with multiple studies and practical deployments demonstrating that traditional text search approaches can match or exceed vector search performance for many agent memory tasks.

Synthesized from **10 contributing transcripts** in NotebookLM notebook *WL: Claude Code Repos & Tools*, clustered into the "vector-google-every" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- A PwC study comparing Grep and vector search across five AI models and four different agents found that Grep outperformed vector search on all tested models including GPT and Gemini for question-answering tasks over conversation history
- Claude Code initially implemented a local vector database but removed it after discovering that plain text search across real files outperformed the vector-based approach
- The Open Knowledge Format (OKF) specification formalizes a folder-based approach where knowledge is stored as plain markdown files in git, with the file path serving as the identifier and a required type declaration in each file
- OKF processes knowledge upfront at index time rather than performing vector computation at each query, reducing computational overhead compared to traditional vector database approaches
- Plain text file approaches offer benefits including diff capability, reviewability, offline operation, and no requirement for external servers or API keys
- Known limitations of the plain text approach include the absence of automatic freshness mechanisms in the OKF specification, potential for messy markdown generation by models, and inconsistent type field usage across implementations

## Verifiable values

| Name | Value |
|---|---|
| PWC study question count | `2016 questions through months of conversation history` |
| AI models tested | `five different models` |
| Agents tested | `four different agents` |

## Related concepts

- [[open-knowledge-format]] — Open Knowledge Format
- [[rag-alternative-approaches]] — RAG Alternative Approaches
- [[agent-memory-management]] — Agent Memory Management

## Citations (from contributing transcripts)

- **Claim:** Grep won in every single model when compared to vector search in the PwC study
  - Source: Grep vs vector search. #ai #tech #techtech (`58c88362-f5e0-4e3c-86d1-4716fde32a64`)
  - Context: they had Gre and Vector Search go through all those questions and compare the answers and surprisingly Grep won in every single model claw GPT Gemini it didn't really matter as much
- **Claim:** Claude Code tried a local vector database and then removed it because plain search beat it
  - Source: Google OKF + Claude : Why We Stopped Using RAG (`5e499223-6f5f-47e7-8634-bba8d9d3396a`)
  - Context: claude Code tried exactly this a local vector database baked right in and then ripped it out plain old search GP across real files beat it no embeddings no index just the agent reading what is actually there
- **Claim:** Google formalized the folder-based approach as the Open Knowledge Format standard in June
  - Source: OKF kills vector databases but creates 3 new ones #Google #shorts (`7cbcb6f8-a170-4ce5-be92-9004895b94ec`)
  - Context: this June Google made that folder an official standard the open knowledge format the spec is almost comically small a bundle is a folder every file is one concept
- **Claim:** OKF stores knowledge as plain markdown in git with type declarations
  - Source: OKF kills vector databases but creates 3 new ones #Google #shorts (`7cbcb6f8-a170-4ce5-be92-9004895b94ec`)
  - Context: every file declares what type of thing it is plain markdown underneath it lives in git right next to your code and the model writes it for you
- **Claim:** Plain text approaches eliminate server and API key requirements
  - Source: OKF kills vector databases but creates 3 new ones #Google #shorts (`7cbcb6f8-a170-4ce5-be92-9004895b94ec`)
  - Context: why beat an expensive database rack does its thinking at every single question the wiki does it once up front and it is only text you can diff it review it run it offline no server no API key

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8b807d28-b283-4de3-a369-4ff5e065ac92`
(cluster `vector-google-every`). No claims are made
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

- NotebookLM notebook [WL: Claude Code Repos & Tools](https://notebooklm.google.com/notebook/8b807d28-b283-4de3-a369-4ff5e065ac92)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

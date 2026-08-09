---
title: "Karpathy's LLM Wiki Method"
created: 2026-07-30
source: nlm-sync-2026-07-30
tags: [nlm-synced, reference, knowledge]
summary: >
  An AI-maintained personal knowledge base approach where a large language model wiki accumulates and persists information over time, eliminating the need to reprocess documents from scratch with each query. The system stores compiled knowledge in local files, allowing complex questions to be answered
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c" (Perplexity: perplexity-videos-tab, synced 2026-07-30)
  - "NotebookLM source 3bdb3942-d002-4cb9-883f-346d5cef9878" (Build An AI Second Brain Knowledge Base (Step-By-Step), synced 2026-07-30)
  - "NotebookLM source 5f3e9708-ca83-42c5-be30-0f2e82c461dd" (How to Build a Personal LLM Knowledge Base (Karpathy’s Method), synced 2026-07-30)
  - "NotebookLM source 7d7d0c83-bc14-4f96-82f6-df27def9112b" (Build A Claude Knowledge Base That Self-Improves!, synced 2026-07-30)
  - "NotebookLM source 86540a98-8ec9-4f28-b215-f83fd1bdc0a0" (Karpathy's LLM Wiki - Full Beginner Setup Guide, synced 2026-07-30)
provenance:
  chain:
    - level: concept
      id: karpathys-llm-wiki-method
    - level: notebook
      id: ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c
      title: Perplexity: perplexity-videos-tab
      url: https://notebooklm.google.com/notebook/ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c
    - level: cluster
      id: 2
      name: knowledge-base-karpathy
relations:
  - target: wiki/concepts/ai-second-brain.md
    type: related
  - target: wiki/concepts/personal-knowledge-management.md
    type: related
  - target: wiki/concepts/llm-powered-documentation.md
    type: related
---

# Karpathy's LLM Wiki Method

## Decision context

**Definition:** An AI-maintained personal knowledge base approach where a large language model wiki accumulates and persists information over time, eliminating the need to reprocess documents from scratch with each query. The system stores compiled knowledge in local files, allowing complex questions to be answered against an ever-growing repository without repeated document processing.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *Perplexity: perplexity-videos-tab*, clustered into the "knowledge-base-karpathy" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The method addresses a core inefficiency in standard AI document interaction: most systems process uploaded documents fresh for each query, saving nothing between sessions, so every question starts from zero
- Three-phase workflow guides the process: Collect (gathering source material), Compile (organizing into the wiki), and Query (asking questions against the compiled knowledge)
- Implementation relies on local computer files with an LLM, avoiding dedicated vector databases or specialized note-taking software
- The approach requires minimal technical setup—essentially only the ability to create a folder on a local computer
- The system is designed to self-improve over time as more information is added and connections are made between entries
- Unlike simple document storage systems where information goes unexamined, the wiki structure actively surfaces relevant connections when querying
- Source material includes diverse formats such as YouTube transcripts, articles, tweets, podcasts, and blog posts
- The compiled wiki serves as a persistent memory layer that the AI can reference across multiple conversations and over extended time periods

## Verifiable values

| Name | Value |
|---|---|
| Social reach | `14 million views in 72 hours (Karpathy's original Tweet)` |
| Community interest | `105,000 bookmarks of the knowledge base guide` |
| Setup time | `approximately 45 minutes` |
| Required tools | `Obsidian, Claude, and local computer files` |

## Related concepts

- ai-second-brain — AI Second Brain
- personal-knowledge-management — Personal Knowledge Management
- llm-powered-documentation — LLM-powered Documentation
- obsidian-as-a-knowledge-graph — Obsidian as a Knowledge Graph
- claude-for-personal-productivity — Claude for Personal Productivity

## Citations (from contributing transcripts)

- **Claim:** Andrej Karpathy, one of the early members of OpenAI, coined the term 'vibe coding' and posted a Tweet describing this approach that received 14 million views in 72 hours
  - Source: How to Build a Personal LLM Knowledge Base (Karpathy's Method)
  - Context: who is one of the early members of OpenAI and literally coined the term vibe coding posted a Tweet that got 14 million views in 72 hours
- **Claim:** The LLM Wiki approach uses three phases: Collect, Compile, and Query
  - Source: How to Build a Personal LLM Knowledge Base (Karpathy's Method)
  - Context: There's three phases Collect compile and query
- **Claim:** The system is built using Obsidian, Claude, and local computer files
  - Source: How to Build a Personal LLM Knowledge Base (Karpathy's Method)
  - Context: Built using Obsidian Claude and your local computer files
- **Claim:** Standard AI document interaction processes everything from scratch each time, with nothing saved between queries
  - Source: Karpathy's LLM Wiki - Full Beginner Setup Guide (`86540a98-8ec9-4f28-b215-f83fd1bdc0a0`)
  - Context: Ask a similar question tomorrow and the AI does all of that work again from scratch Nothing was saved Nothing was built up Every single question starts from zero
- **Claim:** The approach is accessible to non-technical users who can create folders on their computer
  - Source: Karpathy's LLM Wiki - Full Beginner Setup Guide (`86540a98-8ec9-4f28-b215-f83fd1bdc0a0`)
  - Context: You don't need to be technical If you can create a folder on your computer you can do this
- **Claim:** Karpathy's guide was bookmarked by 105,000 people and the setup takes approximately 45 minutes
  - Source: Build A Claude Knowledge Base That Self-Improves! (`7d7d0c83-bc14-4f96-82f6-df27def9112b`)
  - Context: 105000 people bookmarked it and probably almost none of them have built one and that's the problem this is genuinely the most useful AI setup I've seen in months and implemented in Claude and it takes probably 45 minutes to build
- **Claim:** The system requires no vector databases or coding knowledge to implement
  - Source: Build A Claude Knowledge Base That Self-Improves! (`7d7d0c83-bc14-4f96-82f6-df27def9112b`)
  - Context: No Obsidian no vector databases no code just a brilliant self-improving knowledge base
- **Claim:** The knowledge base follows a five-step framework for building and maintaining the system
  - Source: Build A Claude Knowledge Base That Self-Improves! (`7d7d0c83-bc14-4f96-82f6-df27def9112b`)
  - Context: The five-step framework is this you set it up you dump y
- **Claim:** Most second brain systems fail because stored information goes unexamined without active review
  - Source: Build An AI Second Brain Knowledge Base (Step-By-Step) (`3bdb3942-d002-4cb9-883f-346d5cef9878`)
  - Context: Problem is that's kind of where the information just goes to die Unless you're like actively going back through and reviewing the notes all the time

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `ca3b8f0e-ec39-4867-b6f1-acc9b7c9326c`
(cluster `knowledge-base-karpathy`). No claims are made
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

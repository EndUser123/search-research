---
title: "LLM Wiki Knowledge Pattern"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, github]
summary: >
  A design for building personal knowledge bases where an LLM incrementally builds and maintains a structured, interlinked collection of markdown files rather than just retrieving data chunks.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 55c988d8-818d-4ed9-b08b-12d6c697ff5f" (Claude Code and QMD: Persistent Knowledge Architecture, synced 2026-07-28)
  - "LLM Wiki - GitHub Gist" (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f, transcript synced 2026-07-28)
  - "NotebookLM source 471bb7a5-71d0-4f74-b1f0-08b6fcceee39" (The Karpathy Architecture: Engineering Autonomous Knowledge Compilation and Self-Evolving Cognitive Systems, synced 2026-07-28)
  - "NotebookLM source 6d649c8e-b473-4dd7-a1fa-36bef824f537" (The Engineering Architecture of Persistent LLM Knowledge Systems: Implementing the Karpathy Wiki Pattern with Claude Code on Windows 11, synced 2026-07-28)
  - "llm-wiki - GitHub Gist" (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6084207, transcript synced 2026-07-28)
  - "The knowledge compiler. Raw sources in, interlinked wiki out. Inspired by Karpathy's LLM Wiki pattern. - GitHub" (https://github.com/atomicmemory/llm-wiki-compiler, transcript synced 2026-07-28)
  - "NotebookLM source b93aef47-0e2c-4b71-9ac5-1fc0f7eb8171" (karpathy-llm-wiki.md, synced 2026-07-28)
  - "Ss1024sS/LLM-wiki: based on karpathy https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f · GitHub - GitHub" (https://github.com/Ss1024sS/LLM-wiki, transcript synced 2026-07-28)
  - "The 'llm-wiki' GitHub Gist, shared by Andrej Karpathy,... - daily.dev" (https://app.daily.dev/posts/the-llm-wiki-github-gist-shared-by-andrej-karpathy-outlines-a-pattern-for-building-personal-know-dx4n0eg9d, transcript synced 2026-07-28)
  - "LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons ..." (https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: llm-wiki-knowledge-pattern
    - level: notebook
      id: 55c988d8-818d-4ed9-b08b-12d6c697ff5f
      title: Claude Code and QMD: Persistent Knowledge Architecture
      url: https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f
    - level: cluster
      id: 1
      name: github-https-wiki
    - level: source_url
      url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
      title: LLM Wiki - GitHub Gist
    - level: source_url
      url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6084207
      title: llm-wiki - GitHub Gist
    - level: source_url
      url: https://github.com/atomicmemory/llm-wiki-compiler
      title: The knowledge compiler. Raw sources in, interlinked wiki out. Inspired by Karpathy's LLM Wiki pattern. - GitHub
    - level: source_url
      url: https://github.com/Ss1024sS/LLM-wiki
      title: Ss1024sS/LLM-wiki: based on karpathy https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f · GitHub - GitHub
    - level: source_url
      url: https://app.daily.dev/posts/the-llm-wiki-github-gist-shared-by-andrej-karpathy-outlines-a-pattern-for-building-personal-know-dx4n0eg9d
      title: The 'llm-wiki' GitHub Gist, shared by Andrej Karpathy,... - daily.dev
    - level: source_url
      url: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
      title: LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons ...
relations:
  - target: wiki/concepts/retrieval-augmented-generation-(rag).md
    type: related
  - target: wiki/concepts/knowledge-compilation.md
    type: related
  - target: wiki/concepts/obsidian.md
    type: related
---

# LLM Wiki Knowledge Pattern

## Decision context

**Definition:** A design for building personal knowledge bases where an LLM incrementally builds and maintains a structured, interlinked collection of markdown files rather than just retrieving data chunks.

Synthesized from **9 contributing transcripts** in NotebookLM notebook *Claude Code and QMD: Persistent Knowledge Architecture*, clustered into the "github-https-wiki" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The LLM acts as a disciplined librarian and programmer of its own memory using agentic CLI interfaces.
- The system establishes a persistent environment of markdown files that sits between the user and raw sources.
- When a new source is added, the LLM synthesizes it into the wiki instead of simply indexing it.
- The approach shifts from stateless Retrieval-Augmented Generation (RAG) to autonomous Knowledge Compilation.

## Verifiable values

| Name | Value |
|---|---|
| environment format | `markdown files` |

## Related concepts

- [[retrieval-augmented-generation-(rag)]] — Retrieval-Augmented Generation (RAG)
- [[knowledge-compilation]] — Knowledge Compilation
- [[obsidian]] — Obsidian

## Citations (from contributing transcripts)

- **Claim:** The pattern represents a shift from RAG to autonomous knowledge compilation.
  - Source: The Karpathy Architecture: Engineering Autonomous Knowledge Compilation and Self-Evolving Cognitive Systems (`471bb7a5-71d0-4f74-b1f0-08b6fcceee39`)
  - Context: This paradigm move from Retrieval-Augmented Generation (RAG) toward autonomous 'Knowledge Compilation' addresses the primary bottleneck
- **Claim:** The LLM builds a persistent wiki of interlinked markdown files.
  - Source: karpathy-llm-wiki.md (`b93aef47-0e2c-4b71-9ac5-1fc0f7eb8171`)
  - Context: Instead of just retrieving from raw documents at query time, the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files
- **Claim:** Standard RAG suffers from stateless amnesia and rediscovering context every time.
  - Source: The Engineering Architecture of Persistent LLM Knowledge Systems: Implementing the Karpathy Wiki Pattern with Claude Code on Windows 11 (`6d649c8e-b473-4dd7-a1fa-36bef824f537`)
  - Context: standard RAG implementations often suffer from a 'stateless' amnesia, re-discovering context from raw documents at every query without any persistent accumulation of synthesized understanding

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `55c988d8-818d-4ed9-b08b-12d6c697ff5f`
(cluster `github-https-wiki`). No claims are made
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

- NotebookLM notebook [Claude Code and QMD: Persistent Knowledge Architecture](https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

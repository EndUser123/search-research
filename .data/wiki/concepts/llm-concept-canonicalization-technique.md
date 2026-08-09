---
title: "LLM-Based Concept Canonicalization for Knowledge Bases"
created: 2026-08-01
source: session-20260801
tags: [technique, knowledge-management, wiki-maintenance, canonicalization]
summary: >
  When building a knowledge base from diverse sources (videos, transcripts, docs),
  the same underlying concept appears under different surface labels. LLM-based
  canonicalization uses semantic reasoning — not keyword matching — to identify
  that "PIV loop" = "plan implement validate workflow" = "plan build verify" and
  collapse them into a single canonical concept file. Combined with an
  "appears more than once" threshold for concept inclusion, this prevents both
  fragmentation (same idea split across N files) and bloat (single-mention
  concepts cluttering the namespace).
agent: grok
host: grok
cognitive_load: 2
verification: single-source-verified
sources:
  - https://www.youtube.com/watch?v=8JWhwhxWtJw (Cole Medin, 2026-07-30)
relations:
  - target: wiki/concepts/llm-wiki-knowledge-pattern.md
    type: extends
  - target: wiki/concepts/open-knowledge-format-okf.md
    type: complements
  - target: wiki/concepts/skill-usability-audit-cold-read-critique.md
    type: related
---

# LLM-Based Concept Canonicalization for Knowledge Bases

## Decision context

**The problem:** When ingesting knowledge from many heterogeneous sources — especially video transcripts where speakers use informal, varying language — the same underlying concept gets referenced under different surface names across different sources. A naive keyword-indexed knowledge base fragments this into separate pages, making the knowledge base harder to navigate and query. The canonicalization step asks: which surface variants refer to the same underlying concept, and which concepts deserve their own dedicated file?

This technique was described by Cole Medin (2026) as the "hardest part" of building an OKF knowledge base from 200 YouTube videos. The key insight is that keyword matching is insufficient — the LLM must *reason* about semantic equivalence between surface variants. This extends the [[llm-wiki-knowledge-pattern]] by naming the step that most implementations leave implicit, and complements [[open-knowledge-format-okf]] by describing the editorial process that produces clean concept files from messy raw sources.

## Technique

### The canonicalization pipeline

1. **Extract all raw sources** into a common format (e.g., timestamped markdown transcripts)
2. **Bird's-eye pass:** review all sources at once to identify recurring entities and concepts
3. **Fuzzy variant matching:** for each candidate concept, use LLM reasoning to identify all surface variants across sources (e.g., "PIV loop" / "plan implement validate workflow" / "PIV workflow" / "plan build verify" → all resolve to the canonical "PIV loop" concept)
4. **Threshold filter:** a concept or entity must appear in **more than one source** to deserve a dedicated file. Single-mention items are excluded to prevent namespace bloat and scaling problems.
5. **Aggregate:** merge all variant references into a single canonical concept/entity file with source citations and timestamps

### Entity vs Concept distinction

- **Entities** = named tools, products, frameworks (e.g., AG-UI, Bolt.new, BMAD Method)
- **Concepts** = ideas, workflows, patterns (e.g., abstraction distraction, PIV loop)

Both follow the same canonicalization rules but serve different navigation purposes. Entities help users find "what tools does this channel/source set cover?" while concepts help users find "what ideas are discussed?"

### Why keyword matching fails

The critical constraint: concept name variants are not lexically similar. "PIV loop" and "plan build verify" share no common keywords. A keyword-based deduplication system cannot detect that these refer to the same workflow. Only LLM-level semantic reasoning can bridge the gap between surface label and underlying concept identity.

## What this means for our workspace

Our wiki at `P:/.data/wiki/concepts/` has grown to hundreds of concept pages. We already implicitly practice canonicalization when `/wiki` or `/skill-prune` merges or deduplicates concepts, but we lack an explicit, named technique for the LLM fuzzy-matching step. The [[knowledge-capture-cant-afford-to-lose]] principle applies here: losing a concept variant mapping is as costly as losing any other knowledge.

**Potential applications:**
- `/skill-prune` could adopt the "appears more than once" threshold to identify single-source stub concepts for archival
- `/wiki` could benefit from a canonicalization pass that identifies concept pages with semantically equivalent content but different slugs
- The entity/concept distinction maps to our existing implicit separation of "tool reference" pages vs "pattern/technique" pages

**What we already do well:** Our `wikilink` cross-referencing system handles the knowledge graph construction automatically — once canonical concepts exist, the links build themselves. This mirrors the [[skill-usability-audit-cold-read-critique]] insight that structural mechanisms beat behavioral reminders. The gap is in the upstream canonicalization step.

## Falsifier

If keyword-based or embedding-based matching proves as effective as LLM reasoning for identifying concept variants (e.g., if sentence-transformer cosine similarity reliably groups "PIV loop" with "plan build verify"), then the LLM-reasoning requirement is unnecessary overhead and this technique should be simplified. Test: run both approaches on a corpus of 50+ concept variants and compare cluster purity.

## Sources

- [The Ultimate Knowledge Base: Bring YouTube Into Your AI Second Brain](https://www.youtube.com/watch?v=8JWhwhxWtJw) (Cole Medin, 2026-07-30) — described canonicalization as the hardest step; the PIV loop variant-matching example; the "more than once" threshold rule; entity vs concept distinction
- Transcript saved at `P:/.data/wiki/sources/transcripts/8JWhwhxWtJw-cole-medin-okf-youtube-kb.md`

## Auto-related

- [[skill-catalog]]
- [[wiki-improvement-opportunities-practitioner-evidence]]
- [[open-knowledge-format-okf]]
- [[karpathy-style-knowledge-base-workflow]]
- [[llm-wiki-knowledge-pattern]]


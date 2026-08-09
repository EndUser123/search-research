---
title: "Persistent KB Architecture for Model-Sunset Survivability"
created: 2026-08-04
source: "Perplexity Deep Research (Jul 7, 2026) + ChatGPT consultations"
tags: [knowledge-management, architecture-decision, model-deprecation, survivability, rag, embeddings, canonical-store, disposable-index]
summary: >
  Design principle for knowledge base systems that survive model deprecation:
  separate the canonical content store (durable, model-independent) from derived
  indexes (disposable, model-dependent). The canonical store must be readable
  without the model. Every derived store must be disposable. If deleting the
  vector DB would destroy knowledge, the vector DB has been misclassified as a
  source of truth rather than a rebuildable cache. Four-layer architecture:
  canonical content → derived indexes → retrieval abstraction → generation/routing.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "Perplexity Deep Research: Architecting Persistent Knowledge Bases (Jul 7, 2026) — https://www.perplexity.ai/computer/tasks/44313349-2549-4dee-a403-837c1d1f7620"
  - "OpenAI model deprecation policy — https://platform.openai.com/docs/deprecations"
  - "Anthropic model deprecation — https://docs.anthropic.com/en/api/deprecations"
  - "Google Gemini shutdown behavior — https://ai.google.dev/gemini-api/docs/deprecate-models"
  - "Microsoft Azure OpenAI retirement (410 Gone) — https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/model-retirements"
  - "RAG paper (Lewis et al., 2020) — parametric vs non-parametric memory split"
relations:
  - target: wiki/concepts/epistemic-knowledge-system-design-2026.md
    type: complements
  - target: wiki/concepts/design-graphs-solution-graphs-value-for-ai-agent-fleet.md
    type: related
  - target: wiki/concepts/codebase-knowledge-graph-mapping.md
    type: related
---

# Persistent KB Architecture for Model-Sunset Survivability

## Decision context

**Why this design was needed:** the operator consulted ChatGPT and Perplexity about architecting a knowledge base on the wiki infrastructure. The core question: how do you build a KB that doesn't break when a model provider deprecates or retires a model you depend on? Vendors are explicit that shutdown means inaccessible — OpenAI deprecated models are unavailable after their shutdown date, Anthropic retired models fail, Google shut-down endpoints are "completely turned off," Microsoft retired Azure OpenAI deployments return 410 Gone.

**The problem:** embeddings are the biggest trap. Vector coordinates are not portable across embedding spaces. Moving from text-embedding-ada-002 to text-embedding-3-large requires generating new embeddings from scratch. If your KB's knowledge lives in a vector DB, and the embedding model is deprecated, your KB is effectively destroyed.

## The four-layer separation

```
┌─────────────────────────────────────────┐
│  Layer 4: Generation / Routing          │
│  (swappable model, adapter pattern)     │
├─────────────────────────────────────────┤
│  Layer 3: Retrieval Abstraction         │
│  (model-agnostic interface, consensus)  │
├─────────────────────────────────────────┤
│  Layer 2: Derived Indexes               │
│  (DISPOSABLE: vector DB, embeddings,    │
│   graph index, FTS — all rebuildable)   │
├─────────────────────────────────────────┤
│  Layer 1: Canonical Content Store       │
│  (DURABLE: corpus, provenance, schemas, │
│   skills, prompts, evals — survives      │
│   any model deprecation)                │
└─────────────────────────────────────────┘
```

**Layer 1 — Canonical Content Store (DURABLE):** markdown corpus, provenance metadata, frontmatter schemas, skill definitions, prompt templates, eval suites. This is what our wiki vault (`P:/.data/wiki/concepts/`) already is. It must be readable without any model — plain text, human-parseable. This aligns with [[design-graphs-solution-graphs-value-for-ai-agent-fleet]] — the wiki vault's `relations:` frontmatter and `wikilinks` are already a lightweight graph structure at the canonical layer.

**Layer 2 — Derived Indexes (DISPOSABLE):** vector embeddings, graph adjacency lists, FTS5 indexes, QMD indexes. All of these can be rebuilt from Layer 1. Our `build_skill_graph.py`, `qmd` index, and FTS5 search are all derived indexes. See [[codebase-knowledge-graph-mapping]] for how codebase KG tools like Graphify fit at this layer — they produce derived structural indexes, not canonical content.

**Layer 3 — Retrieval Abstraction:** model-agnostic query interface. Our `grep` + `read_file` + `wiki_health_check.py` are the current retrieval layer. A future semantic search would sit here.

**Layer 4 — Generation/Routing:** the LLM itself (Grok, ChatGPT, Gemini, etc.). Swappable. The adapter pattern (`/agy`, `/codex`, `/mmx`, `/model-web`) already implements this.

## The central rule

**The canonical store must be readable without the model, and every derived store must be disposable.** If deleting the vector DB would destroy knowledge, the vector DB has been misclassified as a source of truth rather than a rebuildable cache.

This mirrors RAG's original split between parametric model memory (the LLM's weights — ephemeral, non-portable) and external non-parametric index (documents — durable, portable). Our wiki vault is the non-parametric index. The LLM is the parametric memory. Derived indexes (embeddings, graphs) are caches that speed retrieval but must not become the source of truth.

## Embedding portability — the biggest trap

Vector coordinates are not portable across embedding spaces. Azure explicitly states moving from `text-embedding-ada-002` to `text-embedding-3-large` requires generating new embeddings. The durable fix: maintain a canonical chunk table with stable chunk IDs derived from document structure (not token counts), so re-embedding is a fast side-by-side operation from the canonical source, not a lossy migration.

## The single best survivability hedge

A golden eval suite that travels with the KB. It turns "does this still work?" into a reproducible measurement. Tools: Promptfoo, Inspect, Braintrust, Ragas, DeepEval cover provider-agnostic and RAG-specific metrics.

## What this means for our workspace

Our wiki vault (`P:/.data/wiki/concepts/`) is already a proper Layer 1 canonical store — plain markdown, frontmatter schemas, human-readable. This is the right architecture. The key implications:

1. **Never let a derived index become load-bearing.** QMD, FTS5, `build_skill_graph.py` output — all rebuildable. If any of them disappeared tomorrow, the wiki content would survive. This is already true; the architecture is sound.

2. **If we add semantic/vector search,** the embedding store must be treated as Layer 2 (disposable). The canonical text stays in markdown. Re-embedding is always possible from the canonical source.

3. **The epistemic system design** ([[epistemic-knowledge-system-design-2026]]) adds confidence decay and verification debt to Layer 1 — making the canonical store self-describing about its own reliability. This is the right direction: enrich the canonical layer, don't create a parallel derived layer for metadata.

4. **For the 12GB VRAM setup:** BGE/E5/Nomic local embeddings + sqlite-vec or LanceDB for local vectors + LM Studio/Ollama for Q4 7B-8B generation. LM Studio exposes OpenAI-compatible local REST endpoints, making the adapter pattern practical for local failover.

## Steelman (rejected alternative)

**Single-layer with API fallback:** keep everything in one store (markdown + embeddings together) and just swap the API endpoint when a model is deprecated. This is simpler and works if the new API is backward-compatible. **Why rejected:** API breakage is not just model deprecation — it includes rate cliffs, region blocks, preview cliffs (models pulled mid-beta), and fine-tune loss. A single-layer system has no recovery path when the embedding model changes and the stored vectors are invalid. The four-layer separation costs more upfront but makes recovery deterministic rather than ad-hoc.

## Falsifier

This architecture is wrong if:
- The canonical store is so large that rebuilding derived indexes takes longer than acceptable (hours/days), making the "disposable" label impractical
- The useful retrieval quality gap between derived indexes and raw grep is so small that the derived layer adds no value
- Model providers converge on a standard embedding space, making portability concerns moot
- The eval suite never catches a real regression (false confidence)

## Sources

- Perplexity Deep Research: Architecting Persistent Knowledge Bases (Jul 7, 2026)
- OpenAI model deprecation policy (vendor lifecycle docs)
- Anthropic model deprecation (requests to retired models fail)
- Google Gemini shutdown behavior ("completely turned off")
- Microsoft Azure OpenAI retirement (410 Gone)
- RAG paper (Lewis et al., 2020) — parametric vs non-parametric memory split

## Receipts

- Workspace canonical store: `P:/.data/wiki/concepts/` (810+ markdown files with frontmatter schemas, human-readable)
- Derived graph index: `P:/.data/wiki/scripts/build_skill_graph.py` (reads frontmatter + wikilinks → generates `skill-graph.md`)
- SCHEMA.md four-layer alignment: `P:/.data/wiki/SCHEMA.md` defines the canonical content format (frontmatter, wikilinks, log protocol)
- [INFERENCE] The wiki vault currently has no vector/embedding layer — all retrieval is grep + FTS5 + QMD. If semantic search is added, it would be Layer 2 (disposable).

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[claude-code-project-memory]]
- [[mermaid-and-code-visualization-skills-landscape]]
- [[design-docs-reaped-from-temp-pattern]]


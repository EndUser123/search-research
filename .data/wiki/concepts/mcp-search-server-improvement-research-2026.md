---
title: "MCP search server improvement research: hybrid search, composition, usage-driving"
created: 2026-08-07
source: session-019fd8dc
tags: [mcp, search, hybrid-search, reranking, embeddings, caching, composition, usage-driving, rag, knowledge-base, research]
summary: >
  Research on improving the search_wiki and search_web MCP servers across three
  axes: search intelligence (full-body indexing, hybrid BM25+embeddings, cross-encoder
  reranking), composition (unified server with search_all, wiki-first escalation), and
  usage-driving (tool descriptions, result formatting). The lyonzin/knowledge-rag repo
  (v4.8.0, 557 tests) is the reference implementation — it validates every proposed
  approach and provides concrete patterns. Key new ideas discovered: hybrid_alpha
  parameter, MMR diversification, min_score filtering, snippet_mode, lazy embeddings,
  LightRAG graph+vector hybrid, evaluate_retrieval metrics, SPLADE sparse embeddings.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/wiki-search-mcp-server-pull-based-knowledge-retrieval.md
    type: extends
  - target: wiki/concepts/optimal-multi-backend-search-strategy.md
    type: related
  - target: wiki/concepts/mcp-server-sharing-multi-terminal.md
    type: related
  - target: wiki/concepts/qmd-semantic-search-requires-llm-backend.md
    type: related
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
---

# MCP search server improvement research

## Decision context

**The problem:** the two MCP search servers built in session 019fd8dc are
functionally thin. search_wiki indexes only frontmatter (~10% of content),
search_web does no caching or re-ranking, the two don't compose, and nothing
drives the model to use them at the right time. The /brain session proposed
Approach 1 (unified intelligence server) and the operator asked for /www
validation before committing to a design.

**What this research changed:** validated every axis of Approach 1 against
external implementations. Discovered 10 new ideas not in the original
brainstorming. Identified the key architectural decision: port patterns from
lyonzin/knowledge-rag vs adopt it directly vs leverage our existing
search-research package.

## The reference implementation: lyonzin/knowledge-rag

**Repo:** https://github.com/lyonzin/knowledge-rag
**Version:** v4.8.0 (2026-08-06), 202 commits, 557 tests
**Maturity:** PyPI + NPM + Docker, Glama listed, 7-pillar quality gate

This is the most directly relevant open-source MCP search server. It implements
almost exactly what Approach 1 proposed, with production-tested patterns:

### Architecture

```
User Query → Synonym Expansion → Keyword Router
                                          ↓
                              ┌──────────┴──────────┐
                              ↓                     ↓
                     Semantic Search           BM25 Keyword
                     (ChromaDB vectors)      (inverted index)
                              └──────────┬──────────┘
                                         ↓
                              Reciprocal Rank Fusion
                              (hybrid_alpha weighted)
                                         ↓
                              Cross-Encoder Reranker
                              (ms-marco-MiniLM-L-6-v2)
                                         ↓
                              MMR Diversification
                                         ↓
                              min_score Filter
                                         ↓
                              snippet_mode Truncation
                                         ↓
                                    Results
```

### Key patterns validated

1. **Hybrid search with RRF** — BM25 inverted index + ChromaDB semantic vectors,
   fused via RRF with a tunable `hybrid_alpha` parameter (0.0 = pure BM25, 1.0 =
   pure semantic, 0.3 default keyword-heavy).

2. **Cross-encoder re-ranking** — Xenova/ms-marco-MiniLM-L-6-v2 via ONNX.
   Lazy-loaded on first query (~2-3s one-time delay). Falls back to RRF order
   if model unavailable.

3. **Section-aware markdown chunking** — `.md` files split at `##` and `###`
   header boundaries. Sections larger than chunk_size are sub-chunked with
   overlap. Directly applicable to our wiki concepts (frontmatter + structured
   sections).

4. **FastEmbed ONNX embeddings** — BAAI/bge-small-en-v1.5 (384D, ~33MB). Runs
   locally, no API keys, no cloud. Lazy-loaded on first query since v3.8.0.

5. **Query cache** — LRU with 5-min TTL. Simpler than semantic caching,
   sufficient for most cases.

6. **SSE/streamable-http transport** — one server process serves all clients
   with shared embedding model, shared ChromaDB, shared cache. Exactly the
   pattern our wiki recommends for multi-terminal setups.

7. **Incremental indexing** — mtime/size change detection. Only re-indexes
   modified files. Background reindex with progress polling.

8. **Zero-vector corruption guard (v3.8.1 hotfix)** — FastEmbed can silently
   return zero vectors if ONNX model fails to load. The fix is loud-fail
   (raise EmbeddingModelLoadError), not silent-degrade. This is the same
   failure class as our QMD bug where embeddings were computed but never used.

9. **snippet_mode** — truncates content to ~500 chars at natural break points,
   reducing token consumption ~72%. Adds content_length field; use get_document
   for full content.

10. **min_score filtering** — discard results below 0.0-1.0 threshold. Use
    0.2-0.4 to cut noise. Response includes filtered_by_score count.

11. **MMR diversification** — Maximal Marginal Relevance reduces redundant
    results. Important for knowledge bases with overlapping concepts.

12. **evaluate_retrieval tool** — built-in MRR@5 and Recall@5 metrics for
    tuning hybrid_alpha, testing query expansion, validating after reindexing.

## New ideas discovered (not in original brainstorming)

| Idea | Source | Applicability |
|------|--------|---------------|
| `hybrid_alpha` parameter | lyonzin/knowledge-rag | HIGH — lets caller tune keyword vs semantic per query |
| MMR diversification | lyonzin/knowledge-rag | HIGH — our 990-concept wiki has overlapping concepts |
| `min_score` threshold filtering | lyonzin/knowledge-rag | HIGH — current search_wiki returns all matches |
| `snippet_mode` truncation | lyonzin/knowledge-rag | MEDIUM — reduces token consumption ~72% |
| Zero-vector corruption guard | lyonzin v3.8.1 hotfix | HIGH — same failure class as our QMD bug |
| Lazy-loaded embeddings | lyonzin v3.8.0 | HIGH — stdio multi-process idle cost |
| LightRAG graph+vector hybrid | olafgeibig/knowledge-mcp | MEDIUM — could leverage [[wikilink]] network |
| `evaluate_retrieval` metrics | lyonzin/knowledge-rag | HIGH — measure whether changes improve quality |
| SPLADE sparse embeddings | r/MachineLearning consensus | LOW — emerging technique, may be premature |
| Symmetric query expansion groups | lyonzin/knowledge-rag | MEDIUM — better than our camelCase normalization |

## Workspace inventory: what we already have

**Critical finding:** our search-research package already implements most of
the intelligence features. The question is wiring, not building.

| Feature | In search-research? | In our MCP servers? |
|---------|---------------------|---------------------|
| RRF | ✅ `processors/ensemble.py` + `hybrid_ensemble.py` | ✅ search_web (Brave+Exa+DDG) |
| FTS5+embeddings hybrid | ✅ `core/chs/search.py` (adaptive/rrf/weighted/combsum) | ❌ search_wiki (FTS5 only) |
| Cross-encoder reranking | ✅ `processors/reranking.py` | ❌ |
| Caching | ✅ `core/cache.py` (LRU+TTL) | ❌ |
| Query expansion + synonyms | ✅ `core/query/expander.py`, `synonyms.py` | ❌ (camelCase norm only) |
| Intent classification | ✅ `core/intent_classifier.py` | ❌ |
| Diversity (MMR) | ✅ `core/diversity.py` | ❌ |
| HyDE | ✅ `core/hyde.py` + variants | ❌ |

## Popular repos for ideas

| Repo | Signal | Key pattern |
|------|--------|-------------|
| lyonzin/knowledge-rag | 202 commits, 557 tests, v4.8.0 | Reference implementation: hybrid BM25+semantic+reranking, 13 MCP tools, SSE transport |
| olafgeibig/knowledge-mcp | Glama listed, HN mentioned | LightRAG graph+vector hybrid, domain-specific KBs |
| Airweave (BunsDev) | 176pts HN | Federated search across apps/databases/docs behind one interface |
| Memoriki | 5pts HN | LLM Wiki + Memory Palace for persistent personal KB |
| Morphik | 7pts HN | Open-source MCP for technical document search |
| knowledge-graph-rag-mcp (PyPI) | PyPI listed | Watches knowledge repo, extracts entities, EmbeddingGemma, graph+vector retrieval |

## Usage-driving research

**AWS blog on MCP tool design (Jul 2026)** identifies common MCP tool design
mistakes and context engineering fixes. Key patterns:
- Tool descriptions should describe relationships between tools, not just
  what each tool does ("use this BEFORE search_web for workspace knowledge")
- Result formatting affects trust and reuse — consistent format, relevance
  scores, and source paths build the model's confidence in the tool

**ToolExpNet (ACL 2025)** shows that learning relationships between tools
improves multi-tool selection. Tool descriptions that explicitly state
ordering ("call A before B") outperform independent descriptions.

**Evolution of Tool Use survey (arXiv:2603.22862):** multi-tool orchestration
is the frontier. The model's tool selection improves when tools have clear,
distinct purposes and explicit composition hints.

## Sources

- https://github.com/lyonzin/knowledge-rag — reference implementation (v4.8.0, accessed 2026-08-07)
- https://github.com/olafgeibig/knowledge-mcp — LightRAG graph+vector hybrid
- https://github.com/BunsDev/airweave-agents — federated search (176pts HN)
- https://aws.amazon.com/blogs/machine-learning/mcp-tool-design-practical-approaches-and-tradeoffs/ — MCP tool design (Jul 2026)
- https://aclanthology.org/2025.findings-acl.811/ — ToolExpNet (ACL 2025)
- https://arxiv.org/abs/2603.22862 — Evolution of Tool Use survey
- https://www.pinecone.io/learn/chunking-strategies/ — chunking strategies
- https://vucense.com/dev-corner/embedding-models-2026/ — local embedding model benchmarks
- https://d-central.tech/local-embedding-models/ — 20 open-source embedding models
- https://pypi.org/project/knowledge-graph-rag-mcp/ — graph+vector MCP server
- P:/packages/.claude-marketplace/plugins/search-research/ — our existing search package

## Falsifier

This research is wrong if: (1) lyonzin/knowledge-rag doesn't work on our
Windows + Python 3.14 + Grok Build setup, (2) the search-research package's
CHS module can't be wired into our MCP servers without major refactoring,
or (3) the hybrid_alpha tuning doesn't materially improve retrieval quality
over our current frontmatter-only FTS5 (testable via evaluate_retrieval).

## What this means for our workspace

The design should:
1. Port lyonzin/knowledge-rag's patterns (hybrid_alpha, MMR, min_score,
   snippet_mode, zero-vector guard, lazy embeddings) into our lightweight
   MCP servers rather than adopting ChromaDB (heavier than our SQLite FTS5).
2. Investigate whether the search-research package's existing modules
   (reranking, cache, query expansion) can be imported directly.
3. Phase the work: Phase 1 (full-body FTS5 + caching + usage-driving), Phase 2
   (embeddings + reranking), Phase 3 (composition + SSE transport).
4. Add an evaluate_retrieval tool from the start so we can measure improvement.

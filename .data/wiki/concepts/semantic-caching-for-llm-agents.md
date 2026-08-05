---
title: "Semantic caching for LLM agents: skip the call, not just the tokens"
created: 2026-08-05
source: session-2026-08-05 (/www research on self-improving agent patterns we don't have)
sources:
  - external: https://github.com/zilliztech/GPTCache (GPTCache, Zilliz, MIT license)
  - external: https://arxiv.org/abs/2411.05276 (GPT Semantic Cache paper, 68.8% API call reduction)
  - external: https://redis.io/docs/latest/develop/use-cases/semantic-cache/ (Redis semantic cache)
  - external: https://www.percona.com/blog/semantic-caching-for-llm-apps-reduce-costs-by-40-80-and-speed-up-by-250x/ (Percona benchmark, 40-80% cost reduction, 250x speedup)
  - external: https://www.theagentecosystem.com/blog/llm-semantic-cache (Agent Ecosystem guide)
  - external: https://ssimplifi.com/blog/cache-invalidation-strategies-for-llm-apis (cache invalidation strategies)
  - external: https://n8nlab.io/blog/ai-agent-development-caching (multi-tier caching, L1-L5)
  - external: https://docs.nvidia.com/nemo/curator/curate-text/process-data/deduplication/semdedup (NVIDIA SemDeDup)
tags: [semantic-caching, llm-cache, embedding-cache, response-cache, cost-optimization, latency-optimization, gptcache, cache-invalidation, multi-tier-cache, semantic-dedup]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Semantic caching stores LLM query-response pairs keyed by embedding
  similarity, returning cached responses for semantically similar queries at
  zero model cost and near-zero latency. Measured impact: 40-80% API cost
  reduction, 250x latency improvement on cache hits. Distinct from prompt
  caching (which discounts a repeated prefix but still runs the model) —
  semantic caching can skip the model call entirely. They compose: run both.
  The workspace has TTL and SQLite caching but zero semantic/embedding-based
  caching. The recommended starting point: GPTCache with local all-MiniLM-L6-v2
  embeddings + SQLite/FAISS backend, threshold 0.95, no external infrastructure.
  Critical risk: false positives from low thresholds serve wrong answers; stale
  responses from missing invalidation serve outdated facts.
relations:
  - target: wiki/concepts/token-optimization-patterns-for-agent-fleets.md
    type: complement
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
  - target: wiki/concepts/nlm-to-wiki-optimization-opportunities.md
    type: related
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: related
---

# Semantic caching for LLM agents: skip the call, not just the tokens

## Decision context

**Why this research was needed:** the operator identified semantic caching as a pattern the workspace doesn't have. The workspace re-derives answers to similar questions across sessions, with no LLM response cache. The existing caches (TTL in email-skill, SQLite for NLM transcripts) are exact-match only — they miss paraphrased queries entirely.

**Core distinction:**
- **Prompt caching** (provider-native): discounts a repeated input prefix (system prompt, tool schemas). The model still runs. Saves tokens, not calls.
- **Semantic caching** (application-level): compares query embeddings; if similarity clears a threshold, returns the stored response. The model is never called. Saves entire calls.

They compose: semantic cache first (skip the call), prompt cache second (discount the prefix on calls that do reach the model).

## Key Findings

### How it works (5-step loop)

1. Embed the incoming query
2. Search the vector store of past query-response pairs
3. Compare top match against similarity threshold
4. If hit: return stored response (zero model cost, ~25ms latency)
5. If miss: call the model, store new pair, return

### Measured impact

| Metric | Without cache | With semantic cache | Source |
|--------|-------------|-------------------|--------|
| API cost (10K queries/day, Claude Sonnet) | $1,230/mo | $492/mo (60% hit rate) | Percona |
| Latency per call | 5-7 seconds | ~25ms on hit | Percona, Gravitee |
| API call reduction | 0% | 61.6-68.8% | GPT Semantic Cache paper |
| Speedup on hit | 1x | 250x | Gravitee |

### Threshold tuning (the main dial)

| Cosine threshold | Hit rate | False positive rate | Use case |
|-----------------|----------|---------------------|----------|
| 0.99 | 1-3% | <0.1% | Safety-critical (nearly exact match only) |
| 0.97 | 5-10% | ~0.5% | High-precision |
| 0.95 | 15-25% | 1-3% | **Recommended starting point** |
| 0.93 | 25-40% | 3-7% | Aggressive (tolerate some wrong answers) |
| 0.90 | 35-55% | 7-15% | High-volume, low-stakes |

**There is no universal number.** The threshold must be tuned against real traffic with a labeled set of query pairs.

### Multi-tier caching architecture (L1-L5)

| Layer | What it caches | Workspace equivalent |
|-------|---------------|---------------------|
| L1: Provider prompt cache | Repeated input prefix (KV cache) | Implicit (provider handles) |
| L2: Exact-match response | SHA-256 hash of prompt + params | TTL cache in email-skill |
| L3: Semantic response | Embedding-based similarity | **Missing** |
| L4: Tool result cache | Tool outputs (grep results, file reads) | **Missing** |
| L5: Plan/structure cache | Compiled execution templates | **Missing** (see [[token-optimization-patterns-for-agent-fleets]] LOOP pattern) |

### When NOT to use semantic caching

- **Personalized responses** — answers that depend on the specific user, account, or session state
- **Time-sensitive facts** — answers that change over time (prices, status, availability)
- **Creative outputs** — responses that should be unique each time
- **Low-volume workloads** — if queries rarely repeat, the embedding overhead exceeds the savings

### Failure modes

| Failure | Cause | Mitigation |
|---------|-------|-----------|
| **False positive** (wrong cached answer served) | Threshold too low | Start at 0.95; sample 1-5% of hits for grading; raise if FP > 2% |
| **Stale response** | Facts changed but cache didn't invalidate | TTL per workload class (1h dynamic, 24h stable); prompt-version keying |
| **No hits** | Threshold too high | Lower gradually; measure real hit rate |
| **Storage growth** | Unbounded accumulation | LRU eviction; max_entries limit |

## Honest trade-offs

**Like:** semantic caching is the single highest-ROI optimization for workloads with repeated queries; it eliminates entire model calls (not just tokens); implementation is straightforward with GPTCache; local embeddings are free and fast.

**Dislike:** the threshold is a knife-edge — too low serves wrong answers confidently, too high gives almost no benefit; cache invalidation is an unsolved problem in general (every cache strategy eventually goes stale); for a single-user CLI workspace with highly contextual queries, the hit rate may be too low to justify the overhead.

## Falsifier

This concept is wrong if, within 3 months of implementation:
- Semantic hit rate is below 5% (the embedding overhead exceeds savings)
- False positive rate exceeds 5% despite threshold tuning (the approach is fundamentally mismatched to the query distribution)
- A provider ships native semantic caching at the API level, making application-level caching obsolete

## What this means for our workspace

**Current state:** zero semantic caching. TTL caching exists in specific scripts but is exact-match only. The workspace re-derives answers to semantically similar questions across sessions.

**Recommended approach (if the operator chooses to pursue this):**

1. **Start with GPTCache + SQLite/FAISS + all-MiniLM-L6-v2** — no external infrastructure, Python-native, MIT license. The workspace already uses SQLite (NLM transcripts) and Python extensively.

2. **Apply to high-repeat, low-personalization workloads first:**
   - Wiki queries (same concepts asked in different words)
   - Library documentation lookups (same library, different phrasing)
   - Code pattern questions (same pattern, different context)
   - Tool/CLI usage (same tool, different flags)

3. **Do NOT apply to:** session-specific debugging, code review of specific diffs, operator-specific preferences, time-sensitive quota/status checks.

4. **Threshold: start at 0.95.** Monitor hit rate and FP rate. Lower to 0.93 only if FP rate stays below 2%.

5. **TTL: 1 hour for general queries, 24 hours for stable reference content.** Add prompt-version keying so AGENTS.md changes auto-invalidate.

**Integration point:** the semantic cache would sit between the agent's reasoning layer and the model API. For subagent dispatches, the parent could check the cache before spawning a subagent for a query that has a high-probability cached answer.

**Caveat for this workspace:** the workspace's queries are highly contextual (specific files, specific sessions, specific errors). The hit rate may be lower than the 60% reported for support/FAQ workloads. The operator should measure actual query repetition before committing to implementation. Run a 1-week log of all LLM queries, cluster by semantic similarity, and count how many collapse into shared intents.

## Related

- [[token-optimization-patterns-for-agent-fleets]]@complement — semantic caching as one layer of the token optimization stack
- [[context-firewall-architecture]]@related — subagent context isolation as a caching boundary
- [[nlm-to-wiki-optimization-opportunities]]@related — existing caching patterns (embedding cache concept already proposed)
- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@related — broader self-improvement landscape

## Sources

**Tools:**
- GPTCache (Zilliz, MIT) — https://github.com/zilliztech/GPTCache
- Redis Semantic Cache — https://redis.io/docs/latest/develop/use-cases/semantic-cache/
- mcp-compressor (Atlassian) — https://github.com/atlassian-labs/mcp-compressor

**Papers:**
- GPT Semantic Cache (arXiv 2411.05276) — https://arxiv.org/abs/2411.05276
- Semantic Caching for Low-Cost LLM Serving (Microsoft, INFOCOM 2025) — https://www.microsoft.com/en-us/research/wp-content/uploads/2026/02/infocom25_semanticCaching.pdf
- Hierarchical Caching for Agentic Workflows (MDPI) — https://www.mdpi.com/2504-4990/8/2/30

**Guides:**
- Percona: 40-80% cost reduction, 250x speedup — https://www.percona.com/blog/semantic-caching-for-llm-apps-reduce-costs-by-40-80-and-speed-up-by-250x/
- The Agent Ecosystem: Semantic Cache — https://www.theagentecosystem.com/blog/llm-semantic-cache
- Cache Invalidation Strategies — https://ssimplifi.com/blog/cache-invalidation-strategies-for-llm-apis
- Multi-Tier Caching for AI Agents — https://n8nlab.io/blog/ai-agent-development-caching
- Threshold Tuning (Portkey) — https://portkey.ai/blog/semantic-caching-thresholds
- KV-Cache Aware Prompt Engineering — https://ankitbko.github.io/blog/2025/08/prompt-engineering-kv-cache/

**Semantic deduplication:**
- NVIDIA NeMo Curator SemDeDup — https://docs.nvidia.com/nemo/curator/curate-text/process-data/deduplication/semdedup

**Cost benchmarks:**
- Percona benchmark (10K queries/day, Claude Sonnet): https://www.percona.com/blog/semantic-caching-for-llm-apps-reduce-costs-by-40-80-and-speed-up-by-250x/
- Gravitee benchmark (250x speedup): https://www.gravitee.io/blog/semantic-caching-for-llms-how-to-reduce-ai-costs-and-latency-at-the-gateway
- GPT Semantic Cache paper (68.8% API call reduction): https://arxiv.org/abs/2411.05276

**Threshold tuning:**
- Portkey threshold guide: https://portkey.ai/blog/semantic-caching-thresholds

**Research method:** /www pipeline, parallel or-ling-3-flash-free subagent + parent DDG/firecrawl practitioner signal, 20+ sourced findings synthesized.

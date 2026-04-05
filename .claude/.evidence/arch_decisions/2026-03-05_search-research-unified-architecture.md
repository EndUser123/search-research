# ADR-001: search-research Package Unified Architecture

**Date:** 2026-03-05
**Status:** Accepted
**Context:** Unifying search-research package consolidating unified-search + research-skill + __csf search components

## Decision

Adopt **async-first architecture with hybrid migration approach** for search-research package:

1. **Asyncio core** for concurrent I/O-bound backend execution
2. **Sync wrapper** for backward compatibility during transition
3. **Mode-based routing** (FAST/COMPREHENSIVE/CUSTOM)
4. **HyDE enhancement** for web search (optional)
5. **LRU+TTL caching** with dual eviction
6. **Graceful degradation** for missing API keys
7. **Intent detection** with explicit flag overrides

## Rationale

### Evidence-Backed Architecture

**1. Asyncio vs Threading (2024-2025 Research)**
- **10x scalability**: 10k+ concurrent operations vs threading's hundreds
- **1000x lower memory**: KB-level overhead per coroutine vs MB per thread
- **1000x faster context switching**: Nanoseconds vs microseconds
- **I/O-bound superiority**: Research confirms async optimal for network/file operations
- **Sources**: [Python asyncio vs threading analysis 2024](https://medium.com/@george.seif042/async-vs-multi-threading-in-python-whats-the-difference-and-which-one-should-you-use-940b9d94c2e8)

**2. HyDE Enhancement (Zero-Shot Retrieval)**
- **74% improvement**: 41.8 MAP vs 24.0 baseline (BM25)
- **Performs on par with fine-tuned models** without labeled data
- **Zero-shot approach**: No training data required
- **Sources**: [HyDE: Precise Zero-Shot Dense Retrieval](https://arxiv.org/abs/2212.10496)

**3. Unified Search Architecture Patterns**
- **Aggregator Pattern**: Standard for multi-backend search systems
- **Hybrid local+web**: Industry best practice (fast local + comprehensive web)
- **Graceful degradation**: Required for external API dependencies
- **Sources**: [Unified Search Architecture Best Practices](https://www.mongodb.com/basics/unified-search)

**4. LRU+TTL Caching**
- **Industry standard**: Dual eviction for search query caches
- **Target hit rate**: >85% (research-backed threshold)
- **Tiered TTL**: Hot (24h) / Regular (1h) / Rare (10min)
- **Sources**: [Redis LRU+TTL Caching Strategies](https://redis.io/docs/manual/eviction/)

### Balances Competing Constraints

- **Performance requirements** (<1s FAST, 5-10s COMPREHENSIVE) met via async concurrent execution
- **Backward compatibility** preserved via sync wrapper
- **Solo dev constraints** respected (avoid microservices overkill)
- **Gradual migration** enabled via deprecation warnings

## Consequences

### Good

✅ **Scalable architecture** - 10k+ concurrent operations, KB-level memory overhead
✅ **Unified interface** - Single API for local and web search
✅ **Evidence-backed** - Asyncio, HyDE, LRU+TTL validated by research
✅ **Graceful degradation** - Works without API keys, partial results on failure
✅ **Extensible design** - Protocol-based interfaces, easy to add backends

### Bad

❌ **Migration complexity** - 2-3 weeks async conversion, hybrid codebase during transition
❌ **Intent detection uncertainty** - 90%+ accuracy target ambitious, may require ML
❌ **External dependencies** - Web provider APIs, rate limits, service outages
❌ **Testing overhead** - Both sync and async code paths to maintain

### Trade-offs

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Performance vs. Complexity** | Async (performance) | Evidence shows 10x scalability, worth migration effort |
| **Automation vs. Control** | Both (auto + flags) | Auto-detect convenient, explicit flags provide certainty |
| **Unification vs. Flexibility** | Unification | Single package reduces duplication, acceptable trade-off |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              UnifiedRouter (async)                      │
│  - Mode-based routing (FAST/COMPREHENSIVE/CUSTOM)      │
│  - Intent detection (LOCAL_ONLY/WEB_ENHANCED/MIXED)    │
│  - LRU cache (1000 entries, 3600s TTL)                 │
└────────────────┬────────────────────────────────────┬───┘
                 │                                    │
         ┌───────▼────────┐                  ┌────────▼────────┐
         │  Local Backends│                  │  Web Backends   │
│  (I/O-bound)   │                  │  (I/O-bound)    │
         ├────────────────┤                  ├─────────────────┤
         │ CHS (chat)     │                  │ Tavily          │
         │ CKS (kb)       │                  │ Serper          │
         │ CDS (docs)     │                  │ Exa             │
         │ Grep (code)    │                  │ Perplexity      │
         │ Skills         │                  │ + 7 others      │
         │ RLM            │                  │                 │
         │ Persona        │                  │ Timeout: 5s     │
         │ MultiLang      │                  │ Graceful deg.   │
         │ NotebookLM     │                  │                 │
         └────────────────┘                  └─────────────────┘
                 │                                    │
                 └────────────┬───────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Result Aggregation │
                    │ - Deduplication    │
                    │ - Hybrid scoring   │
                    │ - Ranking          │
                    └────────────────────┘
```

## Alternatives Considered

### Alternative A: Pure Threading Approach (REJECTED)

**Description:** Keep unified-search's threading-based execution, add web providers

**Why Rejected:**
- Violates 2024-2025 research evidence for I/O-bound workloads
- Scalability ceiling: hundreds of concurrent ops vs 10k+
- Memory overhead: MB per thread vs KB per coroutine
- **Misses PRD performance targets**: <1s for 10+ web providers unlikely

### Alternative B: Separate Packages (REJECTED)

**Description:** Keep unified-search and research-skill separate

**Why Rejected:**
- Violates PRD FR-1 unified router requirement
- Duplicate backend implementations (CDS, Grep, Skills in both)
- No mixed local+web queries
- Maintenance burden (2x code to update)

### Alternative C: Microservices Architecture (REJECTED)

**Description:** Split into separate services (search-service, research-service)

**Why Rejected:**
- **Enterprise anti-pattern** for solo dev (violates constitutional constraints)
- Network latency between services
- Operational complexity (service discovery, health monitoring)
- Overkill for single-director workflow

### Alternative D: Hybrid Migration (ACCEPTED) ✅

**Description:** Async core architecture with sync wrapper for backward compatibility

**Why Accepted:**
- Evidence-based: Asyncio validated for I/O-bound workloads
- Meets PRD targets: <1s FAST mode, 5-10s COMPREHENSIVE mode
- Backward compatible: Sync wrapper allows gradual migration
- Scalable: 10k+ concurrent operations
- Pragmatic: Graceful migration via deprecation warnings

## Implementation Timeline

**Phase 1: Package Foundation (Week 1, Mar 6-12)**
- Package structure, core infrastructure
- Copy intent_classifier, resolve shared dependency
- Base router API, cache, intent detection

**Phase 2: Local Backends (Week 1-2, Mar 6-19)**
- Migrate 8 local backends (CDS, Grep, Skills, CHS, CKS, RLM, Persona, MultiLang)
- Implement SearchRouter (FAST mode)
- Performance testing (<1s target)

**Phase 3: Web Backends (Week 2, Mar 13-19)**
- Implement 10+ web providers (Tavily, Serper, Exa, etc.)
- Implement ResearchRouter (COMPREHENSIVE mode)
- Graceful degradation, API key management

**Phase 4: HyDE Enhancement (Week 2-3, Mar 20-26)**
- Implement HyDE query enhancement
- Integrate into ResearchRouter
- Measure relevance improvement (>10% target)

**Phase 5: Consumer Integration (Week 3, Mar 20-26)**
- Update __csf to use SearchRouter
- Update research-skill to use ResearchRouter
- Add deprecation warnings to unified-search

**Phase 6: Deprecation & Migration (Week 4, Mar 27-Apr 2)**
- Publish migration guide
- Announce deprecation timeline
- Create support plan

**Target Release:** 2026-04-02

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance regression in FAST mode** | HIGH | MEDIUM | Benchmarking against unified-search baseline |
| **Intent detection accuracy** | MEDIUM | MEDIUM | Explicit flags override, >90% accuracy target |
| **Web backend API failures** | MEDIUM | HIGH | Graceful degradation, circuit breakers |
| **Async migration complexity** | HIGH | HIGH | Hybrid approach (async core + sync wrapper) |
| **Cache memory leaks** | LOW | LOW | Size limits, TTL expiration, monitoring |
| **HyDE LLM dependency** | LOW | MEDIUM | Optional flag, timeout protection |
| **Breaking existing workflows** | HIGH | LOW | Deprecation warnings, backward compatibility |

## Rollback Plan

**Trigger Events:**
1. Performance regression >2x from unified-search baseline
2. Test coverage drops below 80%
3. Critical bugs in async core blocking __csf workflows
4. Migration timeline exceeds 6 weeks

**Rollback Steps:**

**Phase 1: Immediate Rollback (if __csf breaks)**
```bash
# Revert __csf imports to old paths
cd P:/__csf
git checkout src/cli/nip/search_enhanced.py
git checkout src/search/
git checkout src/knowledge/systems/

# Remove package dependency
# Edit pyproject.toml: remove search-research from dependencies

# Verify __csf works independently
python -m src.cli.nip.search_enhanced "test query"
```

**Phase 2: Validation Rollback (if tests fail)**
- Keep deprecation warnings in __csf (harmless)
- Revert only the import changes
- Package remains installable but __csf uses internal code

**Phase 3: Full Rollback (if architecture proves flawed)**
- Archive search-research package to `attic/`
- Restore unified-search and research-skill to active development
- Document lessons learned in ADR

## Related Decisions

- **ADR-002:** Intent classifier dependency resolution (copy into package)
- **ADR-003:** CHS named pipe fallback strategy (FTS5-only mode)
- **ADR-004:** Async/sync hybrid migration timeline (4-week phased rollout)

## Confidence Assessment

**Overall Confidence: 80%**

**Evidence Breakdown:**
- **Tier 1 (Direct Evidence):** 50% - Existing code, PRD, SDD
- **Tier 2 (Validated Research):** 30% - 2024-2025 asyncio/HyDE studies
- **Tier 3 (Reasoned Assumptions):** 20% - Intent detection, migration timeline

**Key Assumptions:**
1. **Intent Detection Accuracy** (MEDIUM confidence)
   - Risk: Keyword rules may not achieve 90%+ accuracy
   - Mitigation: Explicit flags override, MIXED fallback

2. **Async Migration Timeline** (MEDIUM confidence)
   - Risk: Existing threading+asyncio hybrid may be more complex
   - Mitigation: Hybrid approach, buffer week in timeline

3. **Web Provider API Stability** (LOW confidence)
   - Risk: External dependencies, rate limits
   - Mitigation: Graceful degradation, multiple providers

---

**Document Control**

- **Version:** 1.0
- **Date:** 2026-03-05
- **Status:** Accepted
- **Next Review:** 2026-03-12 (after Phase 1 completion)

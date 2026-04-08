# unified-search Deprecation Announcement

**Date:** 2026-03-06
**End of Life:** 2026-09-01 (Q3 2026)

## Summary

The `search.unified_router` module in `__csf` is deprecated and will be removed on **2026-09-01**. Users should migrate to the new `search-research` package.

## What's Changing

- **Deprecated:** `EnhancedUnifiedSearchRouter` from `search.unified_router`
- **Replacement:** `SearchRouter` and `ResearchRouter` from `search-research` package
- **End of Life:** 2026-09-01 (Q3 2026)

## Why This Change?

The new `search-research` package provides:

1. **Better Performance**: Concurrent backend execution using `asyncio.gather()` and `ThreadPoolExecutor`
2. **Simpler API**: No manual backend initialization needed
3. **More Backends**: 11 web providers (Tavily, Serper, Exa, Perplexity, Brave, Bing, Google, DuckDuckGo, Kagi, You, Mojeek)
4. **HyDE Enhancement**: Zero-shot dense retrieval using Claude Code (orchestrator) - no external API calls from Python
5. **Graceful Degradation**: Missing API keys don't crash searches
6. **Better Testing**: 90%+ test coverage, comprehensive integration tests

## Migration Timeline

### Phase 1: Deprecation (2026-03-06 to 2026-04-01)
- ✅ Deprecation warnings added to `unified-search`
- ✅ Migration guide published (MIGRATION.md)
- ✅ New package available (`search-research`)
- Users see warnings when importing deprecated code

### Phase 2: Migration Period (2026-04-01 to 2026-06-01)
- Users migrate to `search-research`
- Bug fixes for migration issues
- Documentation improvements
- Support for both old and new packages

### Phase 3: Hard Deprecation (2026-06-01 to 2026-09-01)
- Warning messages become more prominent
- New features only added to `search-research`
- Critical bug fixes only for `unified-search`
- Strong recommendation to migrate

### Phase 4: End of Life (2026-09-01)
- `unified-search` removed from __csf
- No further updates or support
- All users must use `search-research`

## How to Migrate

### Quick Start

```bash
# Install the new package
pip install search-research[all]
```

### Code Changes

**Before (deprecated):**
```python
from search.unified_router import EnhancedUnifiedSearchRouter

router = EnhancedUnifiedSearchRouter(
    chs_backend=chs_backend,
    cks_backend=cks_backend,
    enable_cache=True,
)
results = router.search("query", limit=10)
```

**After (new):**
```python
from search_research import SearchRouter

router = SearchRouter(
    cache_ttl=3600,
    enable_cache=True,
)
results = router.search("query", limit=10)
```

### CLI Changes

**Before (deprecated):**
```bash
python -m __csf.src.cli.nip.search_enhanced "query"
```

**After (new):**
```bash
# Fast local search
python -m __csf.src.cli.nip.search "query"

# Comprehensive web research
python -m __csf.src.cli.nip.research "query"
```

For detailed migration instructions, see [MIGRATION.md](MIGRATION.md).

## Support During Migration

### Getting Help

- **Migration Issues:** Check [MIGRATION.md](MIGRATION.md) for common issues
- **Bug Reports:** File issues on GitHub with "migration:" label
- **Questions:** Contact maintainers or check documentation

### Rollback Plan

If you encounter issues during migration:

1. **Immediate Rollback:**
   ```bash
   # Uninstall new package
   pip uninstall search-research

   # Old code continues to work with warnings
   ```

2. **Report Issue:**
   - Document the issue (error messages, behavior differences)
   - File bug report with "migration:" label
   - Include code examples showing the problem

3. **Continue Using Old System:**
   - Old system remains functional until EOL (2026-09-01)
   - You'll see deprecation warnings but code works
   - Migrate at your own pace before EOL

## Breaking Changes

### API Changes

| Old API | New API | Notes |
|---------|---------|-------|
| `EnhancedUnifiedSearchRouter` | `SearchRouter` / `ResearchRouter` | Split into two routers |
| Manual backend initialization | Automatic backend discovery | Simpler API |
| `use_cache` parameter | `enable_cache` in constructor | Config change |
| `time_params` argument | Removed | Use backend-specific time filters |
| Result dicts | `SearchResult` objects | Richer result objects |

### Behavioral Changes

- **Concurrent Execution**: New router runs backends in parallel (faster but different timing)
- **Backend Names**: Use lowercase (`cds`, `grep`) instead of uppercase (`CDS`, `GREP`)
- **Error Handling**: Failed backends log warnings instead of raising exceptions
- **Result Format**: `SearchResult` objects instead of dicts (but compatible via `.to_dict()`)

## Feature Parity

### Features Available in Both

- ✅ 8 local backends (CDS, Grep, Skills, CHS, CKS, KG, RLM, Persona)
- ✅ Query caching with LRU + TTL
- ✅ Backend health tracking
- ✅ Result deduplication
- ✅ Configurable backend filtering

### New Features in search-research

- ✅ 11 web providers (Tavily, Serper, Exa, Perplexity, Brave, Bing, Google, DuckDuckGo, Kagi, You, Mojeek)
- ✅ HyDE query enhancement (zero-shot dense retrieval)
- ✅ Concurrent async execution (5-10x faster for web search)
- ✅ Graceful degradation for missing API keys
- ✅ Better test coverage (90%+)
- ✅ Comprehensive documentation

### Features Removed from search-research

- ❌ Faceted filtering (not commonly used)
- ❌ Stage-aware search (complexity vs benefit)
- ❌ Reranking (can be added later if needed)

## Questions & Answers

### Q: Do I have to migrate immediately?
**A:** No. The old system works until 2026-09-01. You'll see deprecation warnings but functionality is unchanged.

### Q: Will the old system stop working?
**A:** Not until 2026-09-01 (EOL). Until then, it works as-is with warnings.

### Q: Is the new system stable?
**A:** Yes. It has 90%+ test coverage and comprehensive integration tests.

### Q: What if I find a bug during migration?
**A:** File an issue with "migration:" label. We'll fix it promptly.

### Q: Can I use both systems during migration?
**A:** Yes. They're independent packages. You can gradually migrate code.

### Q: What happens to my existing data?
**A:** Nothing. Both systems use the same backend databases (CHS, CKS). No data migration needed.

## Next Steps

1. **Read** [MIGRATION.md](MIGRATION.md) for detailed instructions
2. **Install** `search-research` package: `pip install search-research[all]`
3. **Update** your code following the migration guide
4. **Test** thoroughly in your environment
5. **Report** any issues you encounter

## Timeline Summary

| Date | Milestone |
|------|-----------|
| 2026-03-06 | Deprecation announcement |
| 2026-04-01 | Migration period begins |
| 2026-06-01 | Hard deprecation begins |
| 2026-09-01 | End of life - unified-search removed |

**Questions?** See [MIGRATION.md](MIGRATION.md) or file an issue on GitHub.

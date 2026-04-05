# Search-Research Migration Status

**Date**: 2026-03-17
**Status**: Phase 1 Complete - Critical files migrated

## Summary

The migration from `P:/__csf/src/search/` to `P:/packages/search-research/` is complete for critical files. The deadline has been moved from Q3 2026 to **NOW (March 2026)**.

## Completed Migrations

### 1. Core Test Files (CRITICAL)
- ✅ `P:/__csf/src/tests/test_search_stream.py` - Migrated to AsyncSearchRouter
- ✅ `P:/__csf/src/tests/test_unified_router.py` - Updated API calls
- ✅ `P:/__csf/src/tests/test_intent_based_search.py` - Updated API calls

### 2. CLI Files (CRITICAL)
- ✅ `P:/__csf/src/cli/nip/search_enhanced.py` - Updated to use AsyncSearchRouter

### 3. Documentation
- ✅ `P:/__csf/src/search/CLAUDE.md` - Updated deprecation notice to "NOW"
- ✅ `P:/__csf/src/knowledge/search/CLAUDE.md` - Added migration notice

### 4. Package
- ✅ `search-research` package installed system-wide via `pip install -e .`

## API Migration Summary

| Old API | New API |
|---------|---------|
| `EnhancedUnifiedSearchRouter(enable_daemon=False)` | `AsyncSearchRouter(mode="fast")` |
| `router.search_stream(query)` | `router.search(query)` (sync) |
| `router.search_async(query)` (if existed) | `await router.search_async(query)` |
| Results as `dict` | `SearchResult` objects with `.to_dict()` method |

## Files Still Using Legacy Imports

### Lower Priority (non-critical paths)
These files can be updated incrementally or removed:

- `P:/__csf/src/cli/nip/search.py` - Large file with extensive legacy imports (fallback code exists)
- `P:/__csf/src/knowledge/search/router.py` - Legacy router (deprecated)
- `P:/__csf/src/search/` - Legacy directory (deprecated)

### Test Files (non-blocking)
- `P:/__csf/src/search/test_search_metrics.py`
- `P:/__csf/src/search/test_baseline_measurement.py`
- `P:/__csf/src/search/backends/tests/test_chs_incremental_enhanced.py`
- `P:/__csf/src/tests/test_filter_debug.py`
- `P:/__csf/src/tests/test_debug_kg.py`
- `P:/__csf/src/modules/chat_search/memory_efficient_rag.py`
- `P:/__csf/src/commands/search/task_cli.py`
- `P:/__csf/src/commands/search/status.py`
- `P:/__csf/src/commands/llm_models.py`

### Knowledge System Files
- `P:/__csf/src/knowledge/search/backends/tests/` (various)
- `P:/__csf/src/knowledge/search/tests/` (various)
- `P:/__csf/src/knowledge/systems/cks/reranking.py`

## Next Steps

1. **Remove legacy code**: After verification, remove `P:/__csf/src/search/` and `P:/__csf/src/knowledge/search/`
2. **Update remaining files**: Incrementally migrate lower-priority files
3. **Update documentation**: Ensure all references point to new package

## Verification

To verify the migration works:

```bash
# Test the new package
python -c "from search_research import AsyncSearchRouter; router = AsyncSearchRouter(mode='fast'); print(router.search('test'))"

# Run the updated CLI
python P:/__csf/src/cli/nip/search_enhanced.py "async patterns" --limit 5
```

## Rollback Plan

If issues are found:
1. Restore legacy imports from git history
2. Revert CLAUDE.md deprecation notices
3. File bugs for specific API incompatibilities

---

*Generated: 2026-03-17*
*Migration: TASK-026 (unified_router imports)*

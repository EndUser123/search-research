# Specification: FAISS Incremental Update Performance Optimization

## Project Context
**TSK ID**: TSK-251230-NSE
**Project**: faiss-optimization
**Date**: 2024-12-31

## Problem Statement

The CHS (Chat History Search) FAISS incremental update is taking **2-3+ hours** to scan the 424,688-line `history.jsonl` file on every run. This makes automatic incremental updates before CHS searches unusable.

### Root Cause Analysis

1. **Full file scan**: Script scans all 424k lines even when only ~100 new messages exist
2. **O(n) duplicate checking**: `msg_id in indexed_ids` checked for every message (42M operations)
3. **Model reloading**: `EmbeddingManager()` reloads 420MB model on every run

### Current Performance

| Metric | Current | Target |
|--------|---------|--------|
| Time to scan | 2-3 hours | <60 seconds |
| Lines processed | 424,688 | ~100 new only |
| Duplicate checks | ~42 million | ~100 |
| Model reloads | Every run | Cached (singleton) |

## Solution Overview

Implement file position tracking to resume from last byte position, eliminate redundant duplicate checking, and use singleton pattern for EmbeddingManager.

## Success Criteria

1. ✅ Design artifacts created (arch.md, plan.md, tasks.json)
2. ⏳ Incremental update completes in <60 seconds for ~100 new messages
3. ⏳ File position tracking works correctly
4. ⏳ No duplicate messages in final FAISS index
5. ⏳ Auto-update before CHS search is fast enough to be usable
6. ⏳ Documentation complete

## Constraints

- Must not break existing FAISS index (97,830 vectors)
- Must maintain backward compatibility with state file format
- Must handle edge cases: file rotation, corruption recovery
- Must work with existing CWO12 workflow integration

## Non-Goals

- Changing FAISS index structure (IndexFlatIP)
- Rebuilding the entire index
- Changing the embedding model (all-mpnet-base-v2)
- Modifying the FAISSVectorStore API

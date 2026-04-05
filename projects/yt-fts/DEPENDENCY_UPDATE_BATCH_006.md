# Dependency Update - Batch 006

**Date**: 2026-03-07
**Status**: ✅ Complete (with rollbacks)

---

## Packages Updated (2 packages)

### Successfully Updated
- **huggingface-hub**: 0.36.0 → 0.36.2 ✅
- **pandas**: 2.3.3 → 3.0.1 ✅ (major version bump)

### Rolled Back (blocking conflicts)
- **transformers**: 4.57.3 → 4.57.6 ✅ (minor update only)
- **protobuf**: 5.29.6 → 5.29.6 ✅ (no change)

---

## Dependency Conflicts

### Blocking Conflicts (Resolved by Rollback)

**transformers 5.x conflict:**
- `sentence-transformers 5.1.2` requires `transformers<5.0.0,>=4.41.0`
- yt-fts uses sentence-transformers for local embeddings
- **Decision**: Rolled back to transformers 4.57.6

**protobuf 7.x conflict:**
- `google-auth` libraries require `protobuf<6.0.0,>=3.19.5`
- yt-fts uses google.auth for YouTube OAuth
- **Decision**: Kept protobuf at 5.29.6

### Non-blocking Conflicts
- semgrep conflicts (same as Batch 4 - not in project requirements)

---

## Rationale

Updated pandas 3.0 (major version with breaking changes) and huggingface-hub. Rolled back transformers and protobuf due to blocking conflicts with yt-fts dependencies (sentence-transformers and google.auth).

---

## Test Results

✅ All packages import successfully:
- huggingface_hub ✅
- transformers ✅
- pandas ✅
- google.protobuf ✅

---

**Progress**: 17/35 high-severity packages updated (49% complete)
**Remaining**: 18 packages
**Time tracking**: 1.0 hours total

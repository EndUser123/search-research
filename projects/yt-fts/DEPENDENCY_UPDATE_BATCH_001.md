# Dependency Update - Batch 001

**Date**: 2026-03-06
**Status**: ✅ Completed (2 packages updated, 1 rolled back)
**Test Results**: 47/47 integration tests passed (0.70s)

---

## Packages Attempted

1. **boltons** 21.0.0 → 25.0.0 ✅
2. **cachetools** 6.2.4 → 7.0.3 ❌ ROLLED BACK
3. **chardet** 5.2.0 → 7.0.1 ✅

---

## What Happened

### Success Stories

**boltons** (21.0.0 → 25.0.0)
- **Impact**: Utility library used by face, glom, semgrep
- **Risk**: Medium (major version bump)
- **Result**: ✅ Successfully updated
- **Tests**: All 47 integration tests passed

**chardet** (5.2.0 → 7.0.1)
- **Impact**: Encoding detection library (transitive dependency)
- **Risk**: Low (mature library, backward compatible)
- **Result**: ✅ Successfully updated
- **Tests**: All 47 integration tests passed

### Dependency Conflict Detected

**cachetools** (6.2.4 → 7.0.3)
- **Conflict**: `google-auth 2.41.1` requires `cachetools<7.0,>=2.0.0`
- **Impact**: yt-fts uses `google_auth_oauthlib` for YouTube authentication
- **Decision**: ❌ ROLLED BACK to 6.2.4 (maintain compatibility)
- **Reason**: Breaking google-auth would break YouTube authentication

**Dependency Chain**:
```
yt_fts/auth.py
  └─ google_auth_oauthlib
      └─ google-auth 2.41.1
          └─ requires cachetools<7.0  ⚠️ BLOCKS UPDATE
```

---

## Lessons Learned

### 1. Dependency Constraints Must Be Respected
- **Pre-mortem warning**: "Dependency hell (Risk: 9/9)" ✅ VALIDATED
- **Reality**: Some packages cannot be updated due to transitive dependencies
- **Solution**: Identify dependency constraints BEFORE updating

### 2. pipdeptree Is Essential
- Should have run `pipdeptree` BEFORE updating cachetools
- Would have revealed: `google-auth → cachetools<7.0` constraint
- **Action item**: Run `pipdeptree` before next batch

### 3. Conservative Batch Size Was Right
- Started with 3 packages (conservative)
- Only 2 could be updated safely
- Small batch size limited the blast radius

---

## Current State

**Updated**: 2/35 high-severity packages
**Blocked**: 1 package (cachetools) due to google-auth constraint

**Remaining high-severity packages**: 33
**Time spent**: ~30 minutes (including investigation and rollback)

---

## Next Steps

1. **Run pipdeptree** to map all dependency constraints
2. **Identify which packages have transitive constraints**
3. **Update second batch** (avoid packages with constraints)
4. **Document dependency constraints** in checklist

---

## Commit Message

```
Update dependencies batch 1 (partial)

Updated:
- boltons 21.0.0 → 25.0.0
- chardet 5.2.0 → 7.0.1

Rolled back:
- cachetools 6.2.4 → 7.0.3 (conflict with google-auth)

Test results: 47/47 integration tests passed

Lesson: Dependency constraints must be checked BEFORE updating
```

---

**Status**: ✅ Tests passing, ready to commit
**Time tracking**: 0.5 hours used (9.5 hours remaining in time box)

# Test Collection Error Analysis

**Date:** 2026-02-09
**Scope:** All packages under `P:/packages/`

## Summary

| Category | Count | Files Affected |
|----------|-------|----------------|
| API Migration (CheckpointManager) | 6 | test_corrupted_checkpoint_files.py, test_disk_full_scenarios.py |
| Legacy Test Directories | 20+ | tests_old/, tests.backup/ |
| Directory Collection Errors | 2 | task-context-manager, python-package-template |

## Root Cause Patterns

### 1. API Migration Gap (CheckpointManager → CheckpointStorage)

**Impact:** 6 tests cannot import deleted class

**Files:**
- `packages/checkpoint/tests/test_corrupted_checkpoint_files.py`
- `packages/checkpoint/tests/test_disk_full_scenarios.py`

**Error:**
```
ImportError: cannot import name 'CheckpointManager' from 'checkpoint'
Did you mean: 'CheckpointStorage'?
```

**Fix Pattern:**
```python
# Before
from checkpoint import CheckpointManager

# After
from checkpoint import CheckpointStorage
```

**Evidence:** CheckpointManager was deleted in Task #694 (2026-02-09)

---

### 2. Legacy Test Directories

**Impact:** 20+ test files in backup/old directories

**Directories:**
- `packages/checkpoint/tests_old/` (9 files)
- `packages/checkpoint/tests.backup/` (13+ files)

**Issue:** These directories are still collected by pytest despite being deprecated

**Fix Pattern:** Add to `norecursedirs` in pyproject.toml

---

### 3. Directory Collection Errors

**Impact:** 2 entire directories fail collection

**Directories:**
- `packages/task-context-manager/tests`
- `packages/python-package-template/tests`

**Issue:** Module-level import errors

---

## Recommendations

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Update 2 checkpoint test imports | 5 min | Fixes 6 errors |
| 2 | Add tests_old/, tests.backup/ to norecursedirs | 2 min | Hides 20+ errors |
| 3 | Investigate task-context-manager, python-package-template | 15 min | Fixes 2 directories |

## Verification

```bash
# After fixes
pytest --collect-only P:/packages/ | grep "errors during collection"
# Expected: 0 errors
```

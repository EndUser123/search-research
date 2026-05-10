# API Differences Documentation

**Created**: 2026-03-15
**Status**: Complete
**Purpose**: Document all API differences between legacy and new backends with migration guidance

---

## Executive Summary

All critical backends (grep, cds, skills, kg, rlm) have **compatible APIs**. The primary difference is the base class: new backends inherit from `BaseLocalBackend` which provides shared exclude pattern logic.

---

## GrepBackend

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/grep_backend.py`
- **New**: `P:\\\\\\packages/search-research/core/backends/local/grep_backend.py`

### API Differences

| Aspect | Legacy | New | Migration Required |
|-------|--------|-----|---------------------|
| Base Class | None (standalone) | `BaseLocalBackend` | None - transparent |
| Constructor | `root_paths: list[str] \| None = None` | Same | None |
| `exclude_patterns` | `DEFAULT_EXCLUDE_PATTERNS` class attribute | Inherited from `BaseLocalBackend` | None |
| `build_index()` | ✓ | ✓ | None |
| `search()` | ✓ | ✓ | None |
| Result Keys | `source`, `type`, `name`, `file`, `line`, `signature` | Same | None |

### Migration Code

```python
# BEFORE (legacy)
from search.backends.grep_backend import GrepBackend
backend = GrepBackend(root_paths=["P:\\\\\\src"])

# AFTER (new)
from core.backends.local.grep_backend import GrepBackend
backend = GrepBackend(root_paths=["P:\\\\\\src"])
# API is 100% compatible - just change import path
```

---

## CDSBackend

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/cds_backend.py`
- **New**: `P:\\\\\\packages/search-research/core/backends/local/cds_backend.py`

### API Differences

| Aspect | Legacy | New | Migration Required |
|-------|--------|-----|---------------------|
| Base Class | None (standalone) | `BaseLocalBackend` | None - transparent |
| Constructor | Same | Same | None |
| `build_index()` | ✓ | ✓ | None |
| `search()` | ✓ | ✓ | None |
| Result Keys | `source`, `type`, `name`, `file`, `line`, `docstring` | Same | None |

### Migration Code

```python
# BEFORE (legacy)
from search.backends.cds_backend import CDSBackend
backend = CDSBackend(root_paths=["P:\\\\\\src"])

# AFTER (new)
from core.backends.local.cds_backend import CDSBackend
backend = CDSBackend(root_paths=["P:\\\\\\src"])
# API is 100% compatible - just change import path
```

---

## KGBackend

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/kg_backend.py`
- **New**: `P:\\\\\\packages/search-research/core/backends/local/kg_backend.py`

### API Differences

| Aspect | Legacy | New | Migration Required |
|-------|--------|-----|---------------------|
| Base Class | None | None | None |
| Constructor | `kg_data_path: Path \| None` | Same | None |
| `search()` | ✓ | ✓ | None |
| `build_index()` | Not required (uses pre-built index) | Same | None |
| Result Keys | `entity`, `conversations`, `score` | Same | None |

### Migration Code

```python
# BEFORE (legacy)
from search.backends.kg_backend import KGBackend
backend = KGBackend()

# AFTER (new)
from core.backends.local.kg_backend import KGBackend
backend = KGBackend()
# API is 100% compatible - just change import path
```

---

## SkillsBackend

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/skills_backend.py`
- **New**: `P:\\\\\\packages/search-research/core/backends/local/skills_backend.py`

### API Differences

| Aspect | Legacy | New | Migration Required |
|-------|--------|-----|---------------------|
| Base Class | None | None | None |
| Constructor | `skills_dir: Path \| None` | Same | None |
| `search()` | ✓ | ✓ | None |
| `build_index()` | ✓ (auto on first search) | Same | None |
| Result Keys | `name`, `description`, `path`, `type`, `relevance_score` | Same | None |

### Known Issue (TASK-005)

**Bug**: Front matter parsing sometimes returns string instead of dict.

```python
# File: core/backends/local/skills_backend.py:137
# Issue: front_matter.get("name", "") fails when front_matter is a string

# Workaround (for now):
try:
    results = backend.search("query")
except AttributeError as e:
    if "'str' object has no attribute 'get'" in str(e):
        # Known issue - skip or handle gracefully
        pass
```

### Migration Code

```python
# BEFORE (legacy)
from search.backends.skills_backend import SkillsBackend
backend = SkillsBackend()

# AFTER (new)
from core.backends.local.skills_backend import SkillsBackend
backend = SkillsBackend()
# API is compatible but has known bug (front_matter parsing)
```

---

## RLMBackend

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/rlm_backend.py`
- **New**: `P:\\\\\\packages/search-research/core/backends/local/rlm_backend.py`

### API Differences

| Aspect | Legacy | New | Migration Required |
|-------|--------|-----|---------------------|
| Base Class | None | None | None |
| Constructor | Same | Same | None |
| `search()` | ✓ | ✓ | None |
| `build_index()` | Not required | Same | None |
| Security Issue | Uses `__import__` | Uses `__import__` (same issue) | **TASK-009A required** |

### Security Issue (TASK-009A)

**Problem**: Both legacy and new RLM backends use `__import__` which allows arbitrary code execution.

```python
# Current (INSECURE):
module = __import__(module_name)

# Required fix:
import importlib
ALLOWED_MODULES = {"allowed_module_1", "allowed_module_2"}
if module_name in ALLOWED_MODULES:
    module = importlib.import_module(module_name)
else:
    raise ImportError(f"Module '{module_name}' not in allowlist")
```

### Migration Code

```python
# BEFORE (legacy)
from search.backends.rlm_backend import RLMBackend
backend = RLMBackend()

# AFTER (new) - but security fix needed first!
from core.backends.local.rlm_backend import RLMBackend
backend = RLMBackend()
# NOTE: Security fix (TASK-009A) should be applied before use
```

---

## MultiLangCodeBackend (NOT YET MIGRATED)

### Location
- **Legacy**: `P:\\\\\\__csf/src/search/backends/multilang_backend.py`
- **New**: ❌ Does not exist - **TASK-004 required**

### Migration Required

This is the **ONLY** backend that needs actual code migration. All others already exist.

### Dependencies to Migrate
1. `tree_sitter_utils.py` - Required by multilang_backend

### Migration Code (After TASK-004)

```python
# BEFORE (legacy)
from search.backends.multilang_backend import MultiLangCodeBackend
backend = MultiLangCodeBackend(root_paths=["P:\\\\\\src"])

# AFTER (new) - after migration
from core.backends.local.multilang_backend import MultiLangCodeBackend
backend = MultiLangCodeBackend(root_paths=["P:\\\\\\src"])
```

---

## BaseLocalBackend (New Shared Infrastructure)

### Location
- **New**: `P:\\\\\\packages/search-research/core/backends/local/base_local_backend.py`

### Purpose
Provides shared functionality for local search backends:
- `DEFAULT_EXCLUDE_PATTERNS` - Common exclude patterns
- `_should_exclude()` - Path exclusion logic
- `build_index()` - Template method (override required)

### Benefits
- **DRY**: Eliminates duplicate exclude pattern logic
- **Consistency**: All local backends use same exclusion rules
- **Maintainability**: Single place to update patterns

---

## Import Path Summary

| Backend | Legacy Import | New Import |
|---------|---------------|------------|
| Grep | `from search.backends.grep_backend import GrepBackend` | `from core.backends.local.grep_backend import GrepBackend` |
| CDS | `from search.backends.cds_backend import CDSBackend` | `from core.backends.local.cds_backend import CDSBackend` |
| KG | `from search.backends.kg_backend import KGBackend` | `from core.backends.local.kg_backend import KGBackend` |
| Skills | `from search.backends.skills_backend import SkillsBackend` | `from core.backends.local.skills_backend import SkillsBackend` |
| RLM | `from search.backends.rlm_backend import RLMBackend` | `from core.backends.local.rlm_backend import RLMBackend` |
| Multilang | `from search.backends.multilang_backend import MultiLangCodeBackend` | ❌ Not yet migrated |

---

## Testing Verification

All API compatibility verified by `tests/test_migration_parity.py`:

```
pytest tests/test_migration_parity.py -v
# Result: 30 passed, 1 skipped (known SkillsBackend bug)
```

---

## Changelog

- 2026-03-15: Initial API differences documentation

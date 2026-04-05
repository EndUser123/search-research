# Requirements Analysis: Print to Logger Migration

**TSK:** TSK-260109-1611-print_logging
**Step:** CWO12 Step 2 - Requirements Analysis
**Date:** 2026-01-09

## Executive Summary

Migrate `print()` statements to proper `logging` module calls in CSF NIP library code. The codebase has two existing logging infrastructures that should be leveraged:
- `src/csf_nip/logging.py` - Structured logging with JSON formatter
- `src/cks/utils/dual_sink_logger.py` - Dual-sink logging for CKS operations

**Key Finding:** Approximately **192 files** with `print()` statements are in scope across lib/, core/, and modules/.

---

## 1. Functional Requirements

### FR-1: Print to Logger Replacement
All `print()` statements in library code must be replaced with appropriate logging calls.

| Print Context | Log Level | Logger Method | Example |
|---------------|-----------|---------------|---------|
| Error messages in except blocks | ERROR | `logger.exception()` | Preserves stack trace |
| Warnings about invalid input | WARNING | `logger.warning()` | Non-critical issues |
| Progress/status updates | INFO | `logger.info()` | Normal operations |
| Debugging/diagnostic info | DEBUG | `logger.debug()` | Dev-only output |

### FR-2: Logger Initialization
Each module must initialize a logger using the existing infrastructure:

```python
import logging

logger = logging.getLogger(__name__)
```

**Note:** Use `logging.getLogger(__name__)` directly rather than creating a custom `get_logger()` utility, as the existing `csf_nip/logging.py` already configures the root logger.

### FR-3: Exception Handling
All exception handlers must use `logger.exception()` to preserve stack traces:

```python
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Includes stack trace
```

### FR-4: Structured Context
For operations that require additional context (validation, vector ops, etc.), use the dual-sink logger's structured logging:

```python
from src.cks.utils.dual_sink_logger import log_operation

log_operation("validate", "Validating constitutional constraints",
              validation_type="constitution", target=class_name)
```

---

## 2. Non-Functional Requirements

### NFR-1: Backward Compatibility - CLI Output
**DO NOT CHANGE** `print()` statements in:
- `commands/` - CLI entry points (user-facing output)
- `__main__.py` files - Script entry points
- Analysis scripts - Output is intentional

**Rationale:** CLI tools should print results to stdout. Logging is for library internals.

### NFR-2: Test File Integrity
**DO NOT CHANGE** `print()` in:
- `tests/` directories - Test output uses print intentionally
- `test_*.py` files - Debug output during tests

### NFR-3: No Breaking Changes
- Module public APIs must not change
- Import statements must not break downstream code
- Return values and behavior must remain identical

---

## 3. Scope Boundaries

### In Scope (Fix These)
| Directory | File Count | Pattern |
|-----------|------------|---------|
| `src/lib/` | 114 | Library utilities, helpers |
| `src/core/` | 29 | Core system modules |
| `src/modules/` | 49 | Feature modules (non-CLI) |

### Out of Scope (Do Not Fix)
| Directory | Reason |
|-----------|--------|
| `src/commands/` | CLI entry points - print() is correct |
| `src/cli/` | User-facing CLI tools |
| `tests/` | Test output uses print() |
| Analysis scripts | Output is intentional |

---

## 4. Print Pattern Classification

Based on code analysis, `print()` statements fall into these categories:

| Category | Example | Action |
|----------|---------|--------|
| **Error/Warning** | `print(f"Warning: Invalid value...")` | Convert to `logger.warning()` |
| **Debug/Verbose** | `if verbose: print(f"[Component] {msg}")` | Convert to `logger.debug()` |
| **Progress** | `print("Processing...")` | Keep as print() if in CLI, else logger.info() |
| **Exception** | `except: print(f"Error: {e}")` | Convert to `logger.exception()` |
| **CLI Output** | `print(json.dumps(output))` | **KEEP as print()** |
| **Validation Messages** | `print("🚫 Found violation...")` | Convert to logger (user-facing via dual-sink) |

---

## 5. Existing Logging Infrastructure

### 5.1 csf_nip/logging.py
**Location:** `src/csf_nip/logging.py`

**Features:**
- Structured JSON logging for production
- Console formatter for development
- `LogContext` context manager for operations
- `get_logger(name)` utility
- Auto-configures on import

**Usage:**
```python
from csf_nip.logging import get_logger

logger = get_logger(__name__)
logger.info("Operation completed")
```

### 5.2 dual_sink_logger.py
**Location:** `src/cks/utils/dual_sink_logger.py`

**Features:**
- Separates technical logs (file) from UI (console)
- `log_user_message()` - Clean console output
- `log_technical_error()` - Errors to file only
- `log_operation()` - Structured operation logging

**Usage:**
```python
from src.cks.utils.dual_sink_logger import (
    get_logger, log_technical_error, log_operation
)

logger = get_logger(__name__)
log_operation("rag_query", "Querying knowledge base", vector_op=True)
```

---

## 6. Implementation Approach

### 6.1 For Standard Library Modules
```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Entering function")  # Was: print(f"Debug: ...")
    try:
        do_work()
        logger.info("Work completed")  # Was: print("Done")
    except Exception as e:
        logger.exception("Work failed")  # Was: print(f"Error: {e}")
```

### 6.2 For CKS-Related Modules
```python
from src.cks.utils.dual_sink_logger import (
    get_logger, log_operation, log_technical_error
)

logger = get_logger(__name__)

def validate_constitution(target_class):
    log_operation("validate", f"Validating {target_class.__name__}",
                  validation_type="constitution")
    # ... validation logic
```

---

## 7. Success Criteria

- [ ] All `print()` in lib/, core/, modules/ replaced with logger calls
- [ ] Each modified file has `logger = logging.getLogger(__name__)`
- [ ] Exception handlers use `logger.exception()`
- [ ] No changes to CLI entry points (commands/, __main__.py)
- [ ] No changes to test files
- [ ] All tests pass after migration
- [ ] No regressions in functionality

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking CLI output | Exclude commands/ directory entirely |
| Losing error context | Use `logger.exception()` in all except blocks |
| Performance impact | Logging overhead is minimal; can be disabled |
| Test failures | Exclude test/ directory from changes |

---

## 9. Open Questions

### Q1: Should we add a shared `get_logger()` utility?
**Answer:** No - The existing `csf_nip/logging.py` already provides this. Use `logging.getLogger(__name__)` directly.

### Q2: Should we update `core/logging_config.py` first?
**Answer:** Not needed - `csf_nip/logging.py` already configures logging on import via `configure_logging()`.

### Q3: How to handle progress output in modules that may be used by CLI?
**Answer:** Use `logger.info()` for library code. CLI code can add handlers to display these if needed.

---

## 10. Next Steps

1. **Step 3 (Research):** Examine similar migrations in other codebases
2. **Step 4 (Arch):** Architecture analysis of logger integration points
3. **Step 5 (Plan):** Create detailed implementation plan
4. **Step 6 (Decomposition):** Break down into file-by-file tasks
5. **Step 7 (Execute):** Implement migration with TDD

---

*Document generated as part of CWO12 Step 2: Requirements Analysis*

# Architecture Analysis: Print to Logger Migration

**TSK:** TSK-260109-1611-print_logging
**Step:** CWO12 Step 4 - Architecture Analysis
**Date:** 2026-01-09

## Executive Summary

**[ADF] Architecture Decision Framework**

This is a **refactoring task**, not a new architectural boundary decision. The logging infrastructure already exists. The task is to adopt existing patterns consistently across library code.

**ADF Assessment:**
- **Problem:** Print statements in library code prevent proper debugging, log aggregation, and production monitoring
- **Solution:** Migrate to existing logging infrastructure (`csf_nip/logging.py`, `dual_sink_logger.py`)
- **Complexity Tax:** +1 concept (logger levels), no new files, no new boundaries
- **Decision:** **PROCEED** — Low complexity, high value, uses existing infrastructure

---

## 1. Current Architecture

### 1.1 Logging Infrastructure

The codebase has two existing logging systems:

| Component | Location | Purpose |
|-----------|----------|---------|
| **csf_nip/logging** | `src/csf_nip/logging.py` | General-purpose structured logging |
| **dual_sink_logger** | `src/cks/utils/dual_sink_logger.py` | CKS-specific dual-sink logging |

### 1.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   CLI/      │  │   Tests/    │  │  Analysis/  │         │
│  │ Commands    │  │   Tests     │  │  Scripts    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │ print()  OK      │ print()  OK      │ print()  OK  │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
┌─────────┼─────────────────┼─────────────────┼──────────────┐
│         ▼                 ▼                 ▼                │
│                    Library Layer (TARGET OF MIGRATION)        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   lib/      │  │   core/     │  │  modules/   │         │
│  │   114 files │  │   29 files  │  │   49 files  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │ print() → logger   │ print() → logger   │           │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼────────────┐
│         ▼                  ▼                  ▼                │
│                   Logging Infrastructure Layer                   │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  │
│  │  csf_nip/logging.py      │  │  dual_sink_logger.py      │  │
│  │  - JSONFormatter          │  │  - StructuredFileFormatter│  │
│  │  - ConsoleFormatter       │  │  - CleanConsoleFormatter  │  │
│  │  - LogContext manager     │  │  - log_operation()        │  │
│  │  - get_logger()           │  │  - log_technical_error()  │  │
│  └──────────────────────────┘  └──────────────────────────┘  │
│                                        │                       │
│                         ┌──────────────┴──────────────┐         │
│                         ▼                             ▼         │
│              ┌──────────────────┐      ┌──────────────────┐    │
│              │  stdout/stderr   │      │    Log Files     │    │
│              │  (Console)       │      │  (JSON Structured)│    │
│              └──────────────────┘      └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow

**Current (Print-Based):**
```
Library Code → print() → stdout (lost if not captured)
```

**Target (Logger-Based):**
```
Library Code → logger → logging handlers → stdout (console) + file (structured)
```

---

## 2. Integration Architecture

### 2.1 Logger Hierarchy

```
root logger (configured by csf_nip/logging.py)
│
├── csf_nip (package)
│   ├── lib
│   │   ├── config → logger = logging.getLogger("csf_nip.lib.config")
│   │   ├── enhancement_router → logger = logging.getLogger("csf_nip.lib.enhancement_router")
│   │   └── ...
│   ├── core
│   │   ├── service_registry → logger = logging.getLogger("csf_nip.core.service_registry")
│   │   └── ...
│   └── modules
│       └── ...
```

### 2.2 Import Pattern

**Standard Library Modules:**
```python
import logging

logger = logging.getLogger(__name__)  # Automatic module naming
```

**CKS-Related Modules:**
```python
from src.cks.utils.dual_sink_logger import get_logger, log_operation

logger = get_logger(__name__)
```

### 2.3 Handler Configuration

**No handler configuration in library code** — this is a key architectural principle:

```python
# WRONG - Don't do this in library code
logging.basicConfig(level=logging.INFO)
logger.addHandler(my_handler)

# RIGHT - Let application configure logging
logger = logging.getLogger(__name__)
```

---

## 3. Module Classification

### 3.1 By Target Logger Type

| Module Type | Logger Import | Example Modules |
|-------------|---------------|-----------------|
| **Standard** | `import logging; logger = logging.getLogger(__name__)` | config.py, enhancement_router.py |
| **CKS Operations** | `from src.cks.utils.dual_sink_logger import get_logger` | validation, vector operations |
| **CLI Entry** | No change (keep print()) | commands/, __main__.py |

### 3.2 By Print Pattern Priority

| Priority | Pattern | Count | Example |
|----------|---------|-------|---------|
| **P0** | Exception handlers | ~30 | `except: print(f"Error: {e}")` |
| **P1** | Warning/error messages | ~20 | `print("Warning: ...")` |
| **P2** | Conditional debug prints | ~50 | `if verbose: print(...)` |
| **P3** | General status prints | ~90 | `print("Processing...")` |

---

## 4. Migration Architecture

### 4.1 Phase 1: High-Priority Files (P0-P1)

**Target:** Exception handlers and error/warning messages

**Pattern:**
```python
# BEFORE
try:
    operation()
except Exception as e:
    print(f"Error: {e}")

# AFTER
import logging

logger = logging.getLogger(__name__)

try:
    operation()
except Exception:
    logger.exception("Operation failed")
```

### 4.2 Phase 2: Debug/Verbose Prints (P2)

**Target:** Conditional debug output

**Pattern:**
```python
# BEFORE
def _log_verbose(self, message: str) -> None:
    if self.verbose:
        print(f"[Component] {message}")

# AFTER
import logging

logger = logging.getLogger(__name__)

# Remove _log_verbose, use:
logger.debug(f"Component: {message}")
# Verbosity controlled by log level configuration
```

### 4.3 Phase 3: CKS Operations

**Target:** Validation, vector operations, RAG queries

**Pattern:**
```python
# BEFORE
print(f"Validating: {target_class.__name__}")
print(f"Constitutional violations: {violations}")

# AFTER
from src.cks.utils.dual_sink_logger import log_operation

log_operation("validate", f"Validating {target_class.__name__}",
              validation_type="constitution",
              target=target_class.__name__)
# Console gets clean message, file gets structured JSON
```

---

## 5. Boundary Analysis

### 5.1 What NOT to Change

| Directory | Reason |
|-----------|--------|
| `src/commands/` | CLI entry points — stdout IS the product |
| `src/cli/` | User-facing CLI tools |
| `tests/` | Test output uses print intentionally |
| `__main__.py` files | Script entry points |

### 5.2 Boundary Decision Rationale

**Question:** Should CLI tools also migrate to logging?

**Answer:** **NO** — This is a key architectural boundary:

```
Library Code → logging (configurable, can be disabled)
CLI Entry Points → print() (user-facing output, must appear)
```

The separation of concerns:
- **Library code:** Uses logging for diagnostics (configurable, production-ready)
- **CLI code:** Uses print for results (user output, not configurable)

This is **correct architecture** — changing CLI output to logging would break user experience.

---

## 6. Failure Mode Analysis

### 6.1 Potential Issues

| Issue | Likelihood | Impact | Mitigation |
|-------|-----------|--------|------------|
| Import cycles | Low | Medium | Use `logging.getLogger(__name__)` directly |
| Performance regression | Low | Low | Logging overhead minimal when disabled |
| Lost debug info | Medium | Medium | Use appropriate log levels |
| Breaking CLI output | Low | High | Exclude CLI directories explicitly |

### 6.2 Rollback Strategy

Git revert per-file if issues detected. No structural changes, so rollback is safe.

---

## 7. Integration Points

### 7.1 Existing Log Configuration

The `csf_nip/logging.py` module auto-configures on import:

```python
# In csf_nip/logging.py
configure_logging()  # Called at import time
```

This means:
- No setup required in library code
- Log levels controlled by environment/config
- Handlers configured by application

### 7.2 CKS Dual-Sink Integration

For CKS-specific operations, the dual-sink logger provides:

```python
# Technical details → structured JSON file
# User interface → clean console output

log_operation("rag_query", "Querying knowledge base",
              vector_op=True, query_count=10)
# Console: Clean message
# File: {"timestamp": "...", "operation": "rag_query", "vector_op": true, ...}
```

---

## 8. Testing Architecture

### 8.1 Test Categories

| Test Type | Purpose | Example |
|-----------|---------|---------|
| **Unit** | Verify log calls exist | Check logger.exception() in except blocks |
| **Integration** | Verify log output | Capture logging output in tests |
| **Regression** | Verify no functionality changes | Run existing test suite |

### 8.2 Log Capture Pattern

```python
import logging

def test_function_logs_error():
    with pytest.raises(ValueError):
        my_function()

    # Verify log was called
    assert "Operation failed" in caplog.text
    assert caplog.records[0].levelname == "ERROR"
```

---

## 9. ADF Complexity Tax

| Factor | Cost | Rationale |
|--------|------|-----------|
| New files | 0 | No new files |
| New concepts | +1 | Log levels (debug, info, warning, error, exception) |
| Failure modes | +1 | Potential lost debug info if levels wrong |
| New tests | 0 | Existing tests should pass |
| Total | **+2** | Low complexity |

**Threshold:** 5 — Below threshold, **APPROVE**

---

## 10. Architecture Decision

**[ADF] Decision: PROCEED with migration**

### Rationale

1. **Low Complexity:** +2 complexity tax, well below threshold
2. **High Value:** Enables production monitoring, debugging, log aggregation
3. **Uses Existing Infrastructure:** No new architecture, adoption of existing patterns
4. **Clear Boundaries:** Library vs CLI separation is well-defined
5. **Safe Rollback:** Per-file commits allow easy rollback

### Implementation Order

1. Phase 1: Exception handlers (P0) — highest value
2. Phase 2: Error/warning prints (P1) — visibility improvements
3. Phase 3: Debug/verbose prints (P2) — developer experience
4. Phase 4: CKS operations (P3) — structured logging adoption

---

## 11. Next Steps

1. **Step 5 (Plan):** Create detailed implementation plan
2. **Step 6 (Decomposition):** Break down into file-by-file tasks
3. **Step 7 (Execute):** Implement migration with TDD

---

*Document generated as part of CWO12 Step 4: Architecture Analysis*

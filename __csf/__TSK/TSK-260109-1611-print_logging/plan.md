# Implementation Plan: Print to Logger Migration

**TSK:** TSK-260109-1611-print_logging
**Step:** CWO12 Step 5 - Implementation Planning
**Date:** 2026-01-09
**Estimated Effort:** 8-12 hours across 192 files

---

## Overview

Migrate `print()` statements to proper `logging` module calls in CSF NIP library code. This is a refactoring task that adopts existing logging infrastructure patterns consistently across the codebase.

**Key Principles:**
- Use existing `csf_nip/logging.py` infrastructure
- No new architecture — adoption of established patterns
- Clear boundary: Library code uses logging, CLI keeps print()
- Incremental migration with per-file commits

---

## Phase 1: High-Priority Migration (Exception Handlers)

**Target:** ~30 files with exception handlers using `print()`

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

**Files (examples from analysis):**
1. `src/lib/config.py:220` — Invalid env var warnings
2. `src/core/service_registry.py:221` — Constitutional violations
3. Files in `src/lib/llm_providers/` — Provider errors

**Implementation:**
1. Add `import logging` at top of file
2. Add `logger = logging.getLogger(__name__)` after imports
3. Replace exception print statements with `logger.exception()`
4. Test: Run existing tests to verify no regressions

**Acceptance Criteria:**
- All exception handlers use `logger.exception()`
- Stack traces preserved in log output
- No changes to exception handling logic

---

## Phase 2: Warning and Error Messages

**Target:** ~20 files with warning/error `print()` statements

**Pattern:**
```python
# BEFORE
print(f"Warning: {feature} is deprecated")
print(f"⚠️ Constitutional violations in {class_name}")

# AFTER
logger.warning("%s is deprecated", feature)
logger.warning("Constitutional violations in %s", class_name)
```

**Key Files:**
1. `src/core/service_registry.py` — Constitutional validation messages
2. `src/core/rollback_system.py` — Rollback warnings
3. `src/lib/analysis/intel.py` — Analysis warnings

**Implementation:**
1. Use appropriate log level (`logger.warning()` for warnings)
2. Use lazy formatting (`%s` not f-strings) for performance
3. Preserve message content exactly

**Acceptance Criteria:**
- All warnings use `logger.warning()`
- All errors use `logger.error()`
- Message content preserved

---

## Phase 3: Debug and Verbose Output

**Target:** ~50 files with conditional debug prints

**Pattern:**
```python
# BEFORE
class Component:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def _log(self, message):
        if self.verbose:
            print(f"[Component] {message}")

# AFTER
import logging

logger = logging.getLogger(__name__)

class Component:
    def __init__(self, verbose=False):
        # Verbose now controlled by log level
        if verbose:
            logging.getLogger(__name__).setLevel(logging.DEBUG)

    # Remove _log method, use:
    logger.debug("Component: %s", message)
```

**Key Files:**
1. `src/lib/enhancement_router.py:188-190` — Verbose logging
2. `src/lib/claude_commands/` — Various debug outputs
3. `src/modules/` — Module-specific debug prints

**Implementation:**
1. Remove `verbose` parameters where possible (use log level instead)
2. Replace conditional prints with `logger.debug()`
3. Document that verbosity is now controlled via logging config

**Acceptance Criteria:**
- Conditional debug prints replaced with `logger.debug()`
- Verbosity controlled by log level configuration
- No functionality loss

---

## Phase 4: CKS-Specific Operations

**Target:** CKS validation, vector operations, RAG queries

**Pattern:**
```python
# BEFORE
print(f"Validating: {target_class.__name__}")
print(f"Vector operation: {op_name}")

# AFTER
from src.cks.utils.dual_sink_logger import log_operation

log_operation("validate", f"Validating {target_class.__name__}",
              validation_type="constitution",
              target=target_class.__name__)
```

**Key Files:**
1. `src/core/service_registry.py` — Constitutional validation
2. `src/cks/` — CKS operations
3. Files using constitutional validation patterns

**Implementation:**
1. Import from `dual_sink_logger` for CKS operations
2. Use `log_operation()` for structured logging
3. Console gets clean messages, file gets structured JSON

**Acceptance Criteria:**
- CKS operations use `dual_sink_logger`
- Structured JSON in log files
- Clean console output

---

## Phase 5: General Status Messages

**Target:** ~90 remaining files with general status prints

**Pattern:**
```python
# BEFORE
print("Service Registry Initialized")
print("   Feature 1: Enabled")
print("   Feature 2: Enabled")

# AFTER
logger.info("Service Registry initialized")
logger.debug("Feature 1: enabled")
logger.debug("Feature 2: enabled")
```

**Implementation:**
1. Status messages → `logger.info()`
2. Detail messages → `logger.debug()`
3. Use structured logging where valuable

**Acceptance Criteria:**
- Status messages use appropriate log levels
- Important info visible at INFO level
- Details available at DEBUG level

---

## File-by-File Execution Order

### Priority 0 (Exception Handlers) — Do First
1. `src/lib/config.py`
2. `src/core/service_registry.py`
3. `src/lib/llm_providers/unified_manager.py`
4. `src/lib/llm_providers/provider_registry.py`

### Priority 1 (Warnings/Errors)
1. `src/core/rollback_system.py`
2. `src/lib/analysis/intel.py`
3. `src/lib/constraint_checking.py`

### Priority 2 (Debug/Verbose)
1. `src/lib/enhancement_router.py`
2. `src/lib/claude_commands/research_router.py`
3. `src/modules/chat_search/chat_search.py`

### Priority 3 (General Status)
1. Remaining files in `src/lib/`
2. Remaining files in `src/core/`
3. Remaining files in `src/modules/`

---

## Testing Strategy

### Unit Testing
- Verify log calls exist in modified code
- Check appropriate log levels used
- Validate exception handlers use `logger.exception()`

### Integration Testing
- Run existing test suite — no regressions
- Verify log output captured in tests where needed
- Check logging configuration controls output

### Regression Testing
- All existing tests pass
- No functionality changes
- Log output appears as expected

---

## Quality Gates

### Before Committing Each File
- [ ] `import logging` added
- [ ] `logger = logging.getLogger(__name__)` added
- [ ] All print() replaced with appropriate logger calls
- [ ] Exception handlers use `logger.exception()`
- [ ] File syntax valid (`ruff check --fix`)
- [ ] Existing tests pass

### Final Validation
- [ ] All in-scope files migrated
- [ ] CLI files unchanged (commands/, __main__.py)
- [ ] Test files unchanged
- [ ] Full test suite passes
- [ ] Log output verifiable

---

## Rollback Strategy

- Per-file commits enable safe rollback
- Git revert individual files if issues detected
- No structural changes → rollback is safe

---

## Success Criteria

1. All `print()` in library code replaced with logger calls
2. Each module has `logger = logging.getLogger(__name__)`
3. Exception handlers use `logger.exception()`
4. No changes to CLI entry points
5. No changes to test files
6. All existing tests pass
7. Log output is configurable via log levels

---

## Open Questions

**Q1:** Should we remove `verbose` parameters from classes?
**A1:** Yes — log level configuration replaces verbose flags. This is cleaner and more standard.

**Q2:** What about user-facing progress output in modules?
**A2:** If a module is used by CLI and needs progress output, keep print() for that specific output or use `logger.info()` and let CLI add a handler.

**Q3:** Should we add type hints for logger?
**A3:** Optional — can add `logger: logging.Logger` if desired, but not required.

---

## Next Steps

1. **Step 6 (Task Decomposition):** Create tasks.json with file-by-file breakdown
2. **Step 7 (Execution):** Implement migration with testing

---

*Document generated as part of CWO12 Step 5: Implementation Planning*

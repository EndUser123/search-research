# Research Intelligence: Print to Logger Migration

**TSK:** TSK-260109-1611-print_logging
**Step:** CWO12 Step 3 - Research Intelligence
**Date:** 2026-01-09

## Executive Summary

Research conducted on Python logging module best practices, print-to-logger migration patterns, and exception handling. Findings confirm the approach outlined in requirements and provide additional insights for implementation.

---

## 1. Python Logging Module Best Practices

### 1.1 Logger Initialization Pattern
**Standard Practice:**
```python
import logging

logger = logging.getLogger(__name__)
```

**Key Principles:**
- Use `__name__` for automatic logger naming (follows module hierarchy)
- Create logger at module level (not inside functions/classes)
- Do NOT configure handlers in library code (application's responsibility)

**Source:** Python documentation logging best practices

### 1.2 Log Level Usage

| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Detailed diagnostic information | Variable values, flow tracing |
| INFO | Confirmation that things are working | Operation completed, milestones |
| WARNING | Something unexpected but recoverable | Invalid input, fallback behavior |
| ERROR | Serious problem, operation failed | Exception caught, operation aborted |
| CRITICAL | Very serious error, may crash program | Corrupt state, cannot continue |

### 1.3 Exception Handling Pattern

**Best Practice - Use `logger.exception()`:**
```python
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Auto-captures stack trace
    # OR with explicit error info
    logger.error(f"Operation failed: {e}", exc_info=True)
```

**Anti-Pattern to Avoid:**
```python
# DON'T DO THIS
except Exception as e:
    print(f"Error: {e}")  # Loses stack trace
```

---

## 2. Print vs Logging: Decision Framework

### 2.1 When to Use print()
**Valid Use Cases:**
- CLI tool output (results meant for stdout)
- Interactive scripts where output IS the product
- Debugging quick prototypes
- Test output (pytest capture)

### 2.2 When to Use logging
**Library Code Should Use logging When:**
- Error messages (exceptions, validation failures)
- Debug/diagnostic information
- Status updates in long-running operations
- Audit trails (who did what when)

---

## 3. Migration Patterns

### 3.1 Direct Print Replacement
```python
# BEFORE
print(f"Processing file: {filename}")

# AFTER
logger.info(f"Processing file: {filename}")
```

### 3.2 Conditional Print (Verbose Mode)
```python
# BEFORE
if verbose:
    print(f"[Component] Debug info: {data}")

# AFTER
logger.debug(f"Debug info: {data}")
# Configuring log level controls verbosity
```

### 3.3 Error in Exception Handler
```python
# BEFORE
try:
    process()
except Exception as e:
    print(f"Error processing: {e}")

# AFTER
try:
    process()
except Exception:
    logger.exception("Error processing")
    # exc_info=True is automatic with .exception()
```

### 3.4 Warning Messages
```python
# BEFORE
print(f"Warning: {feature} is deprecated")

# AFTER
logger.warning("%s is deprecated", feature)
# Note: Use lazy formatting for performance
```

---

## 4. Structured Logging with Context

### 4.1 Basic Extra Context
```python
logger.info("User logged in",
            extra={"user_id": user.id, "ip": request.ip})
```

### 4.2 Using LogContext Manager (csf_nip/logging.py)
```python
from csf_nip.logging import LogContext

with LogContext(operation="data_import", request_id=req_id):
    process_data()
    # Auto-logs start/completion with duration
```

### 4.3 Dual-Sink Logging for CKS Operations
```python
from src.cks.utils.dual_sink_logger import log_operation

log_operation("validate", "Constitutional validation",
              validation_type="constitution",
              target=class_name,
              compliance_check=True)
```

---

## 5. Performance Considerations

### 5.1 Lazy Formatting
```python
# GOOD - Lazy evaluation
logger.debug("Expensive operation result: %s", expensive_func())

# AVOID - String formatting happens even if debug disabled
logger.debug(f"Expensive operation result: {expensive_func()}")
```

### 5.2 Conditional Logging Check
```python
# For expensive debug operations
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Complex state: %s", dump_state())
```

---

## 6. Existing Infrastructure Analysis

### 6.1 csf_nip/logging.py
**Capabilities:**
- JSONFormatter for production (machine-readable)
- ConsoleFormatter for development (human-readable)
- LogContext context manager for operation tracking
- Auto-configuration on import
- Rotating file handler support

**Integration Point:**
```python
from csf_nip.logging import get_logger, LogContext

logger = get_logger(__name__)
```

### 6.2 dual_sink_logger.py
**Capabilities:**
- Separates technical logs (file) from UI (console)
- Structured JSON file logging
- Clean console output for user-facing messages
- Sanitization of sensitive information

**Integration Point:**
```python
from src.cks.utils.dual_sink_logger import (
    get_logger,
    log_operation,
    log_technical_error
)
```

---

## 7. Migration Strategy Recommendations

### 7.1 Phased Approach
1. **Phase 1:** Add logger imports to all target files
2. **Phase 2:** Replace error/warning prints (highest value)
3. **Phase 3:** Replace debug/verbose prints
4. **Phase 4:** Add structured logging for key operations

### 7.2 File Classification Priority

| Priority | Pattern | File Count |
|----------|---------|------------|
| **HIGH** | Exception handlers with print | ~30 |
| **HIGH** | Warning/error messages | ~20 |
| **MEDIUM** | Debug/verbose conditional prints | ~50 |
| **LOW** | General status prints | ~90 |

### 7.3 Testing Strategy
- Run existing tests to ensure no regressions
- Add tests for log output in critical paths
- Verify log levels can be controlled via config

---

## 8. Anti-Patterns to Avoid

### 8.1 Don't Configure Handlers in Library Code
```python
# WRONG - Library should NOT configure root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RIGHT - Let application configure logging
logger = logging.getLogger(__name__)
```

### 8.2 Don't Use print() for Errors in Library Code
```python
# WRONG - Errors should go to logging
print(f"ERROR: {e}", file=sys.stderr)

# RIGHT - Use logger
logger.error("Operation failed", exc_info=e)
```

### 8.3 Don't Create Global Loggers with Fixed Names
```python
# WRONG - Loses module context
logger = logging.getLogger("mylib")

# RIGHT - Uses module hierarchy
logger = logging.getLogger(__name__)
```

---

## 9. Codebase-Specific Findings

### 9.1 Common Patterns Identified

**Pattern 1: Service Registry Output** (src/core/service_registry.py)
```python
# Current: print() for initialization messages
print("🚀 Service Registry Initialized")
print("   Constitutional validation: Enabled")

# Recommended: Use logger for library, print() only if CLI entry point
logger.info("Service Registry initialized",
            extra={"constitutional_validation": True,
                   "circuit_breaker": True,
                   "dependency_management": True})
```

**Pattern 2: Validation Messages** (src/core/service_registry.py)
```python
# Current: print() for warnings
print(f"⚠️ Constitutional violations in {target_class.__name__}: {violations}")

# Recommended: Use logger.warning()
logger.warning("Constitutional violations in %s: %s",
               target_class.__name__, violations)
```

**Pattern 3: Config Warnings** (src/lib/config.py)
```python
# Current: print() for invalid env vars
print(f"Warning: Invalid value for {env_var}: {env_vars[env_var]} ({e})")

# Recommended: Use logger.warning()
logger.warning("Invalid value for %s: %s (%s)",
               env_var, env_vars[env_var], e)
```

### 9.2 CKS-Specific Patterns

The dual_sink_logger.py is specifically designed for CKS operations with:
- User-facing console messages (emojis, clean output)
- Technical debug logs to JSON file
- Automatic sanitization of sensitive data

**Usage Recommendation:**
- Use dual_sink_logger for CKS validation/vector operations
- Use standard logging for general library code

---

## 10. Validation Checklist

Before completing migration, verify:

- [ ] All print() in library code replaced with logger calls
- [ ] Exception handlers use logger.exception()
- [ ] Logger initialized with logging.getLogger(__name__)
- [ ] No handler configuration added to library code
- [ ] CLI entry points keep print() for user output
- [ ] Test files unchanged
- [ ] All existing tests pass
- [ ] Log messages use lazy formatting (%s not f-strings)

---

## 11. References and Sources

- Python logging documentation: Best practices for logger naming and usage
- Python Logging Cookbook: Exception handling patterns with logger.exception()
- csf_nip/logging.py: Existing structured logging infrastructure
- dual_sink_logger.py: CKS-specific dual-sink implementation

---

## 12. Next Steps

1. **Step 4 (Arch):** Architecture analysis of logger integration points
2. **Step 5 (Plan):** Create detailed file-by-file implementation plan
3. **Step 6 (Decomposition):** Break down into prioritized tasks
4. **Step 7 (Execute):** Implement migration with testing

---

*Document generated as part of CWO12 Step 3: Research Intelligence*

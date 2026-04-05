# Specification: Print to Logger Migration

**TSK:** TSK-260109-1611-print_logging
**Created:** 2026-01-09
**Status:** Draft

## Overview

Replace `print()` statements with proper `logging` module calls in CSF NIP library files. This improves debuggability, provides log levels, and enables centralized log configuration.

**Scope:** Library modules only (`lib/`, `core/`, `modules/`) — NOT CLI scripts or analysis tools.

## Requirements

### Functional Requirements
- **FR-1**: Replace `print()` in library code with `logging` calls
- **FR-2**: Use appropriate log levels (debug, info, warning, error, critical)
- **FR-3**: Preserve error information (use `logger.exception()` in except blocks)
- **FR-4**: Add logger initialization (`get_logger(__name__)`) to each module

### Non-Functional Requirements
- **NFR-1**: Maintain backward compatibility for CLI output (keep print() there)
- **NFR-2**: No changes to test files (test output uses print intentionally)
- **NFR-3**: No changes to documentation examples (docstrings)

## User Stories

### US-1: Library Error Logging
**As a** developer debugging library code
**I want** error messages logged with stack traces
**So that** I can diagnose issues in production

**Acceptance Criteria:**
- [ ] All exception handlers use `logger.exception()` instead of `print()`
- [ ] Error messages include context (what operation failed)

### US-2: Debug Output Control
**As a** developer
**I want** to control debug output via log levels
**So that** I can enable/disable verbose logging without code changes

**Acceptance Criteria:**
- [ ] Debug messages use `logger.debug()`
- [ ] Info messages use `logger.info()`
- [ ] Can be controlled via logging config

## Scope

### In Scope
- `lib/` — Library modules (shared utility code)
- `core/` — Core system modules (logging, config, etc.)
- `modules/` — Feature modules (excluding CLI wrappers)

### Out of Scope
- `commands/` — CLI entry points (print() is correct for user output)
- `analysis/` — Analysis scripts (output is intentional)
- `tests/` — Test files (assert output uses print)
- `__main__.py` — Entry points (error output should stay print)

## Success Criteria

- All `print()` calls in library files replaced with `logger`
- Each module has `logger = logging.getLogger(__name__)`
- No regressions in existing functionality

## Technical Approach

### Logger Pattern
```python
import logging

logger = logging.getLogger(__name__)

# Replace print with appropriate level:
logger.debug("Variable value: %s", var)
logger.info("Operation completed")
logger.warning("Unexpected input")
logger.error("Operation failed")
logger.exception("Exception occurred")  # In except blocks
```

### What NOT to Change
```python
# CLI output - keep as print()
def main():
    print("Results:", results)
    print(f"Processed {count} files")

# Test output - keep as print()
def test_something():
    print("Test output:", result)
```

## Implementation Plan

1. **Analyze**: Identify all `print()` in scope (`lib/`, `core/`, `modules/`)
2. **Categorize**: Classify as error, debug, info, or warning
3. **Replace**: Convert to `logger` calls with appropriate levels
4. **Test**: Verify no functionality regressions
5. **Validate**: Run quality gates

## Files to Fix

Initial scan shows ~50-100 files with `print()` in scope.

## Open Questions

- Should we add a shared `get_logger()` utility with standard formatting?
- Should `core/logging_config.py` be updated first to set up log handlers?

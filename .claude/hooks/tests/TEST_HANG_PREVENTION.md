# Problem Statement: Test Hangs from Subprocess Calls Without Timeouts

## Problem

Tests in `P:/.claude/hooks/tests/` hang indefinitely when `subprocess.run()` calls are made without a `timeout` parameter. If the subprocess blocks (e.g., due to SQLite lock contention, FileLock blocking, or infinite loop), the pytest test also hangs forever.

### Root Causes

1. **Missing timeout on subprocess.run()** — `test_stop_negative_existence_guard.py` called `subprocess.run()` without `timeout=` at lines 92-97, causing indefinite hangs when the guard script blocked.

2. **No pytest-wide timeout** — `pytest.ini` lacked a `timeout` setting, so even pytest itself had no safeguard.

3. **Fixtures without try/finally** — Autouse fixtures (`clean_test_state`, `isolate_notifications`) had yield but no guaranteed cleanup. If a test hangs during execution, the yield never executes, leaving state polluted for subsequent tests.

### Evidence

| File | Issue |
|------|-------|
| `tests/test_stop_negative_existence_guard.py:97` | `subprocess.run()` without `timeout=` |
| `tests/conftest.py:70-106` | `clean_test_state` fixture — yield without try/finally |
| `tests/conftest.py:23-49` | `isolate_notifications` fixture — yield without try/finally |
| `pytest.ini` | No `timeout` setting |

### Impact

- Tests hang indefinitely on Windows (where `portalocker` FileLock can block)
- Cross-test pollution when fixtures don't clean up after hangs
- No way to run the test suite reliably in CI/CD

---

## Proposed Solution

### 1. Test Standards Document

Create `tests/README.md` documenting required patterns for all test files:

```
## Required Patterns

### Subprocess calls
All `subprocess.run()` calls MUST include a `timeout=` parameter.
```python
# CORRECT
subprocess.run([...], timeout=15)

# WRONG — causes indefinite hang
subprocess.run([...])
```

### Autouse fixtures
All `@fixture(autouse=True)` fixtures MUST use try/finally for guaranteed cleanup.
```python
# CORRECT
@pytest.fixture(autouse=True)
def my_fixture():
    setup()
    try:
        yield
    finally:
        cleanup()  # Runs even if test hangs

# WRONG — no cleanup on hang
@pytest.fixture(autouse=True)
def my_fixture():
    setup()
    yield
    cleanup()  # Never runs if test hangs
```
```

### 2. Ruff Linter Rule

Add `ruff` configuration to `pyproject.toml` or `pytest.ini` to detect `subprocess.run()` without `timeout=`:

```python
[tool.ruff.lint]
select = ["S"]  # Security-related rules
[tool.ruff.lint.ruleS]  # subprocess without timeout
```

Alternatively, a custom rule:
```python
# Disallow subprocess.run without timeout in test files
import ast

class SubprocessTimeoutChecker:
    def visit_Call(self, node):
        if node.func.attr == "run" and node.func.value.id == "subprocess":
            # Check if timeout keyword argument exists
            has_timeout = any(k.arg == "timeout" for k in node.keywords)
            if not has_timeout:
                # Check if in test file
                if "test" in self.filepath:
                    self.error(node, "subprocess.run() without timeout in test file")
```

## Verification

Run the test suite and confirm:
1. All tests complete without hanging
2. `ruff` passes on test files
3. A test that hangs is killed after 30 seconds (pytest timeout)

## Files to Create

| File | Purpose |
|------|---------|
| `tests/README.md` | Test standards documentation |
| `pyproject.toml` or `ruff.toml` | Linter configuration for subprocess timeout rule |

## Files Modified (Historical Fixes)

| File | Change |
|------|--------|
| `tests/test_stop_negative_existence_guard.py` | Added `timeout=15` to subprocess.run calls |
| `tests/conftest.py` | Added try/finally to autouse fixtures |
| `pytest.ini` | Added `timeout = 30` |

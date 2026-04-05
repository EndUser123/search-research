# Ralph TDD Pattern Library

Patterns learned from real-world testing scenarios. Use these when writing tests.

## Pattern: Write Tests for Refactored Modules

### Mock Strategy for Non-Existent Modules

When testing code that imports modules that don't exist yet (lazy imports):

```python
import sys
from types import ModuleType
import pytest

@pytest.fixture(autouse=True)
def setup_missing_modules():
    """Create mock modules for non-existent dependencies."""
    # Create mock module
    mock_ui = ModuleType("yt_fts.core.ui")
    mock_ui.is_textual_compatible = MagicMock(return_value=(True, "0.50.0"))
    
    # Inject into sys.modules
    sys.modules["yt_fts.core.ui"] = mock_ui
    sys.modules["yt_fts.core.ui.dashboard"] = mock_ui
    
    yield
    
    # Cleanup
    for mod in ["yt_fts.core.ui", "yt_fts.core.ui.dashboard"]:
        sys.modules.pop(mod, None)
```

### Patch Location Rule (CRITICAL)

**Patch where modules are IMPORTED, not where they are DEFINED.**

When code has:
```python
# src/yt_fts/core/batch_execution.py
from ..download.quota_strategy import create_quota_strategy
```

The test must patch:
```python
# tests/test_batch_execution.py
@patch("yt_fts.download.quota_strategy.create_quota_strategy")  # ✅ CORRECT
def test_something(self, mock_create_quota):
    pass

# NOT:
@patch("yt_fts.core.batch_execution.create_quota_strategy")  # ❌ WRONG
def test_something(self, mock_create_quota):
    pass
```

**How to find the correct patch path:**
1. Read the source file
2. Find the import statement
3. Use the import path as the patch target

### @contextmanager Requirement

When testing a `@contextmanager` function, the function **must** have a `yield` statement:

```python
from contextlib import contextmanager

@contextmanager
def graceful_interrupt_handler(downloader, fail_fast: bool = False):
    signal.signal(signal.SIGINT, signal_handler)
    try:
        downloader.download_all()
        yield  # CRITICAL: This MUST be present
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        raise
    finally:
        signal.signal(signal.SIGINT, original_handler)
```

Missing the `yield` causes: `TypeError: 'NoneType' object is not an iterator`

### Test Execution Pattern

Always run the full test suite to verify:

```bash
pytest tests/ -v --tb=short
```

Common issues:
- **Module doesn't exist**: Use sys.modules injection
- **Wrong patch path**: Check imports in source file
- **AttributeError**: Patch at import location, not definition

### Common Patterns

| Scenario | Pattern |
|----------|---------|
| Non-existent module | `sys.modules` injection in fixture |
| Mocking imported function | Patch at import location |
| Testing context manager | Ensure `yield` statement exists |
| Lazy imports | Patch before importing test module |
| Multiple test files | Use `autouse=True` fixture in conftest.py |

## Per-Iteration File Tracking

When running TDD iterations, track only files changed in the current iteration:

The state file tracks:
```yaml
iteration_started_at: "2025-01-05T12:00:00Z"
```

Use this timestamp to run tests only on files modified since then:

```bash
# Get files changed this iteration
git diff --name-only --since="$(grep iteration_started_at .data/ralph-loop.local.md | cut -d'"' -f2)"

# Run tests only for changed files
pytest $(git diff --name-only --since="..." | grep test_.*\.py)
```

This provides faster feedback during iterations.

## Coverage Threshold Enforcement

Always require a minimum coverage threshold:

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Default: 80% coverage required. Adjust with `--coverage-threshold` flag.

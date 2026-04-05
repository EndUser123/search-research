# Refactoring Best Practices for yt-fts

This document codifies the refactoring patterns and workflows proven effective in this codebase.

## Core Principles

1. **Characterization Tests First** - Never refactor without capturing current behavior
2. **Small, Verifiable Steps** - Each change must be testable and reversible
3. **Code Flow Verification** - After refactoring, verify the actual execution path

## The TDD Refactoring Cycle

### Phase 1: RED - Characterize Current Behavior

Write tests that CAPTURE EXISTING behavior before making changes.

```python
"""Characterization tests for <function_name>.

These tests CAPTURE CURRENT BEHAVIOR before refactoring.
Run with: pytest tests/path/to/test_<name>_characterization.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

class Test<FunctionName>BasicFormatting:
    """Tests for basic <feature> behavior."""

    @pytest.fixture
    def setup(self):
        # Arrange test state
        pass

    def test_<specific_behavior>(self, setup):
        """Characterization: <what this test captures>."""
        # Act
        result = function_under_test(params)

        # Assert - capture current behavior
        assert result["expected_key"] == expected_value
```

**Key Patterns:**
- Use descriptive test class names: `Test<FunctionName>BasicFormatting`
- Use descriptive test names: `test_<specific_behavior>`
- Add docstrings explaining what behavior is being characterized
- Group related tests in classes

### Phase 2: GREEN - Extract and Verify

Extract the logic while keeping tests passing.

```python
# New extracted module
class <FeatureManager>:
    """Manager for <feature> operations.

    This class handles:
    - <responsibility 1>
    - <responsibility 2>
    - <responsibility 3>
    """

    def __init__(self, dependency: Dependency | None = None):
        """Initialize the manager.

        Args:
            dependency: Optional dependency. If not provided, uses default.
        """
        self.dependency = dependency or get_default_dependency()

    def format_for_display(self, ...) -> str:
        """Format <data> for display.

        Args:
            <params>: Input parameters

        Returns:
            Formatted string for display
        """
        # Implementation
```

### Phase 3: REFACTOR - Improve Quality

With tests passing, improve code quality:
- Extract magic numbers to named constants
- Improve docstrings
- Add type hints
- Simplify complex conditionals

## Code Flow Tracing

After refactoring, VERIFY the actual code flow:

### 1. Check Import Chain
```bash
grep -n "from.*import" src/yt_fts/module/file.py
```

### 2. Verify Function Calls
```bash
grep -n "get_db_connection" src/yt_fts/module/file.py
```

### 3. Run Related Tests
```bash
pytest tests/path/to/test_module.py -v
```

### 4. Check for Orphaned Code
```bash
# After removing a feature, grep for references
grep -r "removed_function_name" src/
```

## When to Refactor

| Cyclomatic Complexity | Action |
|-----------------------|--------|
| < 10 | No action needed |
| 10-15 | Monitor, consider for future refactoring |
| 15-30 | Characterize and plan refactoring |
| 30+ | High priority - break down into smaller components |

## Common Refactoring Patterns

### 1. Extract Class/Manager

**When:** A class has too many responsibilities or a function is too complex.

**Pattern:**
```
Before: BatchDownloader._format_db_stats() - 200 lines
After:  ChannelStatisticsManager.format_for_display() - focused method
```

**Steps:**
1. Write characterization tests for the original method
2. Create new Manager class with extracted logic
3. Update original code to use Manager
4. Verify tests pass
5. Remove duplication

### 2. Consolidate Database Connections

**When:** Multiple `sqlite3.connect()` calls scattered across modules.

**Pattern:**
```python
# BEFORE - scattered connections
conn = sqlite3.connect(get_db_path())

# AFTER - centralized connection
from yt_fts.db.infra import get_db_connection
conn = get_db_connection()
# Or with context manager:
with get_db_connection() as conn:
    ...
```

**Files Changed:**
- `src/yt_fts/db/infra.py` - provides `get_db_connection()`
- All consuming modules - update imports

### 3. Extract Constants

**When:** Magic numbers or repeated string literals.

**Pattern:**
```python
# BEFORE
if gap > 5:
    return "high"
elif gap > 0:
    return "medium"

# AFTER
_SIGNIFICANT_GAP_THRESHOLD = 5
_SMALL_GAP_THRESHOLD = 0

if gap > _SIGNIFICANT_GAP_THRESHOLD:
    return "high"
elif gap > _SMALL_GAP_THRESHOLD:
    return "medium"
```

## Verification Checklist

After each refactoring:

- [ ] All existing tests pass
- [ ] New characterization tests pass
- [ ] No orphaned imports (grep for removed symbols)
- [ ] Code flow verified (grep for key function calls)
- [ ] Documentation updated (if public API changed)

## Optional: Mechanical Refactoring with Codemods

For large-scale mechanical changes (10+ files, identical pattern), automated tools can save time.

### When to Use Codemods

| Scenario | Use Codemod | Reason |
|----------|-------------|--------|
| Mass import renames (10+ files) | Yes | Identical pattern, high error risk |
| Function renames across modules | Yes | AST-safe, won't break references |
| Moving code between directories | Yes | Updates imports automatically |
| Single-file changes | No | Tool overhead > manual edit |
| Logic extraction | No | Use TDD instead |
| Behavioral changes | No | Use TDD instead |

### Bowler (PyBowler)

AST-based refactoring using lib2to3 patterns. Safer than regex, preserves syntax.

```bash
# Install
pip install bowler

# Create codemod script
# Run with diff preview
bowler run codemod.py src/ tests/ --diff

# Apply changes
bowler run codemod.py src/ tests/ --write
```

**Example: Consolidate imports**

```python
# migrate_imports.py
from bowler import Query

def rename_import(node, capture, filename):
    """Replace sqlite3.connect with get_db_connection."""
    # This is simplified - actual implementation needs AST manipulation
    # See: https://pybowler.io/
    pass

def main():
    (
        Query()
        .select_pattern("import_from< 'from' 'sqlite3' 'import' name='connect' any*>")
        .modify(rename_import)
        .execute(diff=True, interactive=False)
    )
```

**Documentation:** https://pybowler.io/

### LibCST (Alternative)

Instagram's Concrete Syntax Tree tool for complex transformations. More powerful but steeper learning curve.

**Documentation:** https://libcst.readthedocs.io/

### Decision: Manual vs Automated

| Factor | Manual TDD | Codemod |
|--------|------------|---------|
| Files affected | < 10 | 10+ |
| Pattern consistency | Varies | Identical |
| Setup time | None | ~5 min |
| Safety | Test-verified | AST-aware |

**Rule of thumb:** If you'll make the same edit more than 5 times, use a codemod.

## Tools Reference

| Command | Purpose |
|---------|---------|
| `/refactor <function>` | Start TDD refactoring workflow |
| `/complexity <module>` | Find high-complexity functions |
| `pytest tests/... -v` | Run specific test file |
| `grep -n "pattern" file` | Verify code flow |

## Examples from This Codebase

1. **ChannelStatisticsManager Extraction**
   - Original: `BatchDownloader._format_db_stats()` (CC=25)
   - Result: Standalone class with 29 characterization tests
   - File: `src/yt_fts/download/channel_statistics_manager.py`
   - Tests: `tests/yt_fts/download/test_channel_stats_characterization.py`

2. **Database Connection Consolidation**
   - Original: 12 scattered `sqlite3.connect()` calls
   - Result: Centralized `get_db_connection()` from `db.infra`
   - Files: `llm/summarize.py`, `ui/list_formatter.py`, `utils/helpers.py`, `core/queue.py`, `core/search_cli.py`, `core/stats.py`

# Research Intelligence: OutputFormatter Patterns

## Executive Summary

Modern Python output formatters in 2025 leverage Protocol-based interfaces, generic typing with TypeVar, and lazy evaluation patterns for performance. Configuration-driven output using Pydantic models and dependency injection for formatter composition are emerging as best practices. Integration with Rich for TUI and Click for CLI provides a comprehensive solution.

## Key Research Findings

### 1. Protocol-Based Architecture (HIGH IMPACT)

**Pattern**: Use structural typing with Protocol instead of ABC for formatter interfaces.

**Evidence from CSF NIP**:
```python
# From chat_search/components/result_formatter.py
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')

class Formatter(Protocol[T]):
    def format(self, data: T) -> str: ...
    def format_rich(self, data: T) -> "RenderableType": ...
```

**Benefits**:
- Better duck typing without inheritance
- Cleaner separation of concerns
- Easier testing with mock implementations

### 2. Rich Integration Pattern (HIGH IMPACT)

**Pattern**: Use Rich as primary TUI/CLI formatting library with custom renderables.

**Evidence from CSF NIP**:
```python
# From advisory/cli/rich_interface.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class RichFormatter:
    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def render_table(self, data: List[Dict[str, Any]]) -> Table:
        table = Table(show_header=True, header_style="bold magenta")
        return table
```

**Benefits**:
- Professional CLI output with minimal effort
- Built-in support for colors, tables, progress bars
- Cross-platform compatibility

### 3. Configuration-Driven Output (MEDIUM IMPACT)

**Pattern**: Use Pydantic models to define output format configurations.

**Recommended Implementation**:
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class OutputConfig(BaseModel):
    format: Literal["text", "json", "table", "markdown"] = "text"
    color: bool = True
    width: Optional[int] = None
    indent: int = 2

    class Config:
        extra = "forbid"
```

**Benefits**:
- Type-safe configuration
- Automatic validation
- Easy serialization/deserialization

### 4. Performance Optimization Techniques (MEDIUM IMPACT)

**Pattern**: Use lazy evaluation and string builder patterns.

**Recommended Implementation**:
```python
from io import StringIO
from functools import lru_cache
from typing import Generator

class OptimizedFormatter:
    def format_iter(self, data: Iterable[T]) -> Generator[str, None, None]:
        """Yield formatted chunks lazily"""
        for item in data:
            yield self._format_item(item)

    @lru_cache(maxsize=128)
    def _get_template(self, template_name: str) -> str:
        """Cache compiled templates"""
        return self._compile_template(template_name)
```

**Benefits**:
- Memory-efficient for large datasets
- Reduced CPU usage through caching
- Streaming-friendly output

### 5. SOLID Principles Implementation (STRATEGIC)

**Pattern**: Apply SOLID principles to formatter design.

**Evidence from CSF NIP**:
```python
# Single Responsibility - dedicated formatters
class JSONFormatter:
    """Handles only JSON output"""

class TableFormatter:
    """Handles only table output"

# Open/Closed - extensible through plugins
class FormatterPlugin(Protocol):
    def can_format(self, data: Any) -> bool: ...
    def format(self, data: Any) -> str: ...
```

**Benefits**:
- Maintainable and testable code
- Easy to extend without modification
- Clear separation of concerns

### 6. Type-Safe Template Systems (LOW IMPACT)

**Pattern**: Use modern Python typing with template literals.

**Python 3.12+ Features**:
```python
from typing import TypedDict, TypeGuard
from string import Template

class DataRow(TypedDict):
    name: str
    value: int
    status: str

def is_valid_row(data: dict) -> TypeGuard[DataRow]:
    return all(k in data for k in DataRow.__annotations__)
```

## Recommended Architecture for OutputFormatter

### Core Class Structure
```python
from typing import Protocol, TypeVar, Generic, Optional, Dict, Any, List
from pathlib import Path
import logging

T = TypeVar('T')

class OutputFormatterProtocol(Protocol[T]):
    """Protocol for output formatters."""

    def format(self, data: T, mode: str = "default") -> str:
        """Format data as string."""
        ...

    def can_format(self, data: Any) -> bool:
        """Check if formatter can handle data type."""
        ...

class OutputFormatter:
    """Main output formatter with protocol-based architecture."""

    def __init__(
        self,
        framework_path: Optional[Path] = None,
        config: Optional[OutputConfig] = None,
        console: Optional[Console] = None
    ):
        self._framework_path = framework_path or self._get_default_framework_path()
        self._config = config or OutputConfig()
        self._console = console or Console()
        self._framework_cache: Optional[Dict[str, Any]] = None
        self._logger = logging.getLogger(__name__)
```

### Section Formatter Pattern
```python
class SectionFormatter:
    """Handles individual output sections."""

    def __init__(self, console: Console):
        self._console = console

    def format_header(self, result: Dict[str, Any], mode: str) -> List[str]:
        """Format header section."""
        ...

    def format_health_summary(self, validations: Dict[str, Any]) -> List[str]:
        """Format health summary section."""
        ...
```

## Performance Recommendations

1. **Lazy Loading**: Load framework data only when needed
2. **Template Caching**: Cache compiled format strings with @lru_cache
3. **String Building**: Use StringIO or list join for efficient concatenation
4. **Generator Pattern**: Use generators for large output streams

## Integration Recommendations

### With Rich
```python
def _format_with_rich(self, data: Dict[str, Any]) -> str:
    """Format using Rich for enhanced output."""
    with self._console.capture() as capture:
        # Rich formatting logic
        self._console.print(self._build_rich_layout(data))
    return capture.get()
```

### With Click
```python
import click

def _click_echo_formatted(self, text: str, err: bool = False) -> None:
    """Use click.echo for proper CLI output handling."""
    click.echo(text, err=err, color=self._config.color)
```

## Testing Strategy

### Unit Testing
```python
import pytest
from typing import Any
from unittest.mock import Mock, patch

class TestOutputFormatter:
    def test_format_header_success(self):
        formatter = OutputFormatter()
        result = {"status": "success", "execution_time": 0.5}
        header = formatter._format_header(result, "quick")
        assert "SUCCESS" in header[0]

    @patch('pathlib.Path.exists')
    def test_load_framework_missing(self, mock_exists):
        mock_exists.return_value = False
        formatter = OutputFormatter()
        framework = formatter.load_cognitive_framework()
        assert framework is None
```

### Performance Testing
```python
import time
import pytest

def test_formatting_performance():
    formatter = OutputFormatter()
    large_result = generate_large_test_data()

    start = time.perf_counter()
    output = formatter.format_optimized_output(large_result, "quick")
    duration = time.perf_counter() - start

    assert duration < 0.05  # 50ms threshold
    assert len(output) > 1000  # Non-trivial output
```

## Risk Assessment

### HIGH Risk
- **Performance bottleneck** with naive string concatenation in large datasets
- **Type errors** at runtime without proper typing guards

### MEDIUM Risk
- **Rich dependency overhead** for simple text output
- **Configuration complexity** for basic use cases

### LOW Risk
- **Breaking changes** in Rich API versions
- **Template injection vulnerabilities** (mitigated with Template.safe_substitute)

## Next Steps

1. **Design Protocol Interface**: Define OutputFormatterProtocol with type parameters
2. **Implement Core Class**: Create OutputFormatter with Rich integration
3. **Add Configuration**: Implement OutputConfig with Pydantic validation
4. **Create Tests**: Implement comprehensive test suite with 95%+ coverage
5. **Performance Benchmarking**: Validate sub-50ms formatting requirement
6. **Integration Testing**: Test with MainCodeExecutor result data

This research provides a solid foundation for implementing a modern, type-safe, and performant OutputFormatter that follows 2025 Python best practices and integrates seamlessly with the CSF NIP architecture.
# Implementation Plan: OutputFormatter Extraction

## Overview

This plan provides a detailed roadmap for extracting the OutputFormatter class from main_code.py following the refactoring package specifications and architectural analysis.

## Implementation Phases

### Phase 1: Foundation Setup (30 minutes)

#### 1.1 Create OutputFormatter Structure
**File**: `P:\__csf.nip\commands\nip\output_formatter.py`
**Tasks**:
- Create main OutputFormatter class with constructor
- Implement FrameworkLoader interface
- Create HealthMetricsExtractor utility class
- Set up basic imports and type annotations

#### 1.2 Extract Core Methods
**Target**: Lines 514-637 from main_code.py
**Methods to Extract**:
- `_format_optimized_output()` → `format_result()`
- `_load_cognitive_framework()` → separate FrameworkLoader class
- Section methods: `_header()`, `_health_section()`, etc.

### Phase 2: Implementation (60 minutes)

#### 2.1 Implement OutputFormatter Class
```python
class OutputFormatter:
    """Handles result formatting with configurable strategies."""

    def __init__(self, framework_loader=None):
        self.framework_loader = framework_loader or DefaultFrameworkLoader()
        self.health_extractor = HealthMetricsExtractor()

    def format_result(self, result: Dict[str, Any], mode: str) -> str:
        """Main entry point - replaces _format_optimized_output."""
```

#### 2.2 Implement Supporting Classes
```python
class FrameworkLoader(ABC):
    """Abstract interface for framework data loading."""

    @abstractmethod
    def load_framework(self) -> Optional[Dict[str, Any]]:
        """Load cognitive framework data."""

class DefaultFrameworkLoader(FrameworkLoader):
    """Default implementation using existing logic."""

class HealthMetricsExtractor:
    """Extract health metrics from validation results."""

    @staticmethod
    def extract(validations: Dict[str, Any]) -> HealthMetrics:
        """Extract and aggregate health metrics."""
```

#### 2.3 Section Formatting Methods
Extract each section from the original method:
- `_format_header()`: Status, execution time, strategy
- `_format_health_section()`: System health summary
- `_format_commands_section()`: Essential commands with examples
- `_format_behaviors_section()`: Behavioral framework
- `_format_actions_section()`: Immediate next steps
- `_format_projects_section()`: Detected projects
- `_format_footer()`: Timestamp and tips

### Phase 3: Integration (30 minutes)

#### 3.1 Update MainCodeExecutor
```python
class MainCodeExecutor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.formatter = OutputFormatter()  # Add formatter
        # Remove: framework loading methods

    def _format_and_print(self, result: Dict[str, Any]) -> None:
        """Use new formatter instead of old method."""
        if result.get("mode") == "quick" and result.get("status") in ["success", "warning"]:
            output = self.formatter.format_result(result, result.get("mode", "quick"))
            print(output)
        else:
            print(json.dumps(result, indent=2))
```

#### 3.2 Update main() Function
```python
if __name__ == "__main__":
    result = main()

    if result.get("mode") == "quick" and result.get("status") in ["success", "warning"]:
        formatter = OutputFormatter()
        output = formatter.format_result(result, "quick")
        print(output)
    else:
        print(json.dumps(result, indent=2))
```

### Phase 4: Testing (45 minutes)

#### 4.1 Unit Tests
**File**: `tests/unit/test_output_formatter.py`
**Test Cases**:
- Test formatter with success results
- Test formatter with warning results
- Test formatter with error results
- Test framework loading success/failure
- Test each section method independently
- Test health metrics extraction

#### 4.2 Integration Tests
**Test Cases**:
- End-to-end formatting from MainCodeExecutor
- CLI smoke tests for all modes
- Performance benchmarks (<50ms requirement)
- Output comparison tests (identical formatting)

### Phase 5: Validation & Cleanup (15 minutes)

#### 5.1 Code Quality Checks
- Run ruff for linting
- Run mypy --strict for type checking
- Verify test coverage ≥95%
- Check cyclomatic complexity reduction

#### 5.2 Cleanup
- Remove old methods from MainCodeExecutor
- Remove unused imports
- Update docstrings
- Add TODO comments for future enhancements

## Detailed Implementation Steps

### Step 1: Create output_formatter.py Structure
```python
#!/usr/bin/env python3
"""
Output formatting for CSF NIP main command.

Extracted from main_code.py to follow Single Responsibility Principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# CSF Root path constant
CSF_ROOT = Path("P:/")

@dataclass
class HealthMetrics:
    """Health metrics extracted from validation results."""
    healthy_components: int = 0
    warnings: int = 0
    critical: int = 0
    directory_violations: int = 0

    @property
    def is_critical(self) -> bool:
        return self.critical > 0

    @property
    def is_healthy(self) -> bool:
        return self.warnings == 0 and self.critical == 0

class FrameworkLoader(ABC):
    """Abstract interface for framework data loading."""

    @abstractmethod
    def load_framework(self) -> Optional[Dict[str, Any]]:
        """Load cognitive framework data."""
        pass

class DefaultFrameworkLoader(FrameworkLoader):
    """Default implementation using existing logic."""

    def __init__(self, prompt_path: Optional[Path] = None):
        self.prompt_path = prompt_path or Path(__file__).parent / "main_prompt.toon"
        self.logger = logging.getLogger(__name__)

    def load_framework(self) -> Optional[Dict[str, Any]]:
        """Load and parse framework from prompt file."""
        # Implementation extracted from _load_cognitive_framework
        pass

class HealthMetricsExtractor:
    """Extract health metrics from validation results."""

    @staticmethod
    def extract(validations: Dict[str, Any]) -> HealthMetrics:
        """Extract and aggregate health metrics."""
        metrics = HealthMetrics()

        # Extract from structure validation
        if structure := validations.get("structure"):
            if isinstance(structure, dict):
                metrics.directory_violations = structure.get("violations", 0)
                if structure.get("status") == "success":
                    metrics.healthy_components += 1
                else:
                    metrics.warnings += 1

        # Extract from core systems
        if core := validations.get("core_systems"):
            if isinstance(core, dict) and core.get("status") == "success":
                metrics.healthy_components += 2  # Python + Import systems
            else:
                metrics.warnings += 1

        # Extract from health checks
        if health := validations.get("health"):
            if isinstance(health, dict) and health.get("status") == "success":
                metrics.healthy_components += 1
            else:
                metrics.warnings += 1

        return metrics

class OutputFormatter:
    """Handles result formatting with configurable strategies."""

    def __init__(self, framework_loader: Optional[FrameworkLoader] = None):
        self.framework_loader = framework_loader or DefaultFrameworkLoader()
        self.health_extractor = HealthMetricsExtractor()
        self.logger = logging.getLogger(__name__)

    def format_result(self, result: Dict[str, Any], mode: str) -> str:
        """Format execution result as optimized user-friendly output."""
        framework = self.framework_loader.load_framework()

        # Build formatted output sections
        sections = [
            self._format_header(result, mode),
            self._format_health_section(result),
            self._format_commands_section(framework),
            self._format_behaviors_section(framework),
            self._format_actions_section(result),
            self._format_projects_section(framework),
            self._format_footer()
        ]

        # Filter out empty sections and join
        return "\n".join(section for section in sections if section)

    def _format_header(self, result: Dict[str, Any], mode: str) -> List[str]:
        """Generate header section."""
        status = result.get("status", "unknown").upper()
        status_emoji = "✅" if result.get("status") == "success" else "⚠️"
        exec_time = result.get("execution_time", 0)

        return [
            f"[CSF_NIP_v1.0.0][solo] System Status: {status}",
            f"Execution Time: {exec_time:.2f}s | Strategy: {mode}",
            ""
        ]

    def _format_health_section(self, result: Dict[str, Any]) -> List[str]:
        """Generate system health section."""
        if "validations" not in result:
            return []

        metrics = self.health_extractor.extract(result["validations"])
        status_emoji = "✅" if not metrics.warnings else "⚠️"

        lines = [
            "### System Health",
            f"{status_emoji} **Core Systems**: {metrics.healthy_components}/3 operational"
        ]

        if metrics.warnings > 0 or metrics.directory_violations > 0:
            if metrics.warnings > 0:
                lines.append(f"⚠️  **Issues**: {metrics.warnings} minor warnings")
            if metrics.directory_violations > 0:
                lines.append(f"📁 **Directory Violations**: {metrics.directory_violations} (fixable with /cleanup)")
        else:
            lines.append("✨ **All systems operational - no issues detected**")

        lines.extend(["", ""])
        return lines

    # ... other section methods
```

### Step 2: Extract Framework Loading Logic
Copy the exact logic from `_load_cognitive_framework()` method into `DefaultFrameworkLoader.load_framework()`.

### Step 3: Extract Section Methods
Move each section formatting logic into separate methods in OutputFormatter class.

### Step 4: Update MainCodeExecutor
Remove old methods and add formatter integration.

## Testing Strategy

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch
from output_formatter import OutputFormatter, HealthMetrics, DefaultFrameworkLoader

class TestOutputFormatter:
    def test_format_result_success(self):
        """Test formatting successful results."""
        formatter = OutputFormatter()
        result = {
            "status": "success",
            "execution_time": 0.5,
            "validations": {
                "structure": {"status": "success", "violations": 0},
                "core_systems": {"status": "success"},
                "health": {"status": "success"}
            }
        }

        output = formatter.format_result(result, "quick")

        assert "[CSF_NIP_v1.0.0]" in output
        assert "System Status: SUCCESS" in output
        assert "3/3 operational" in output
        assert "All systems operational" in output

    def test_health_metrics_extraction(self):
        """Test health metrics extraction."""
        from output_formatter import HealthMetricsExtractor

        validations = {
            "structure": {"status": "success", "violations": 0},
            "core_systems": {"status": "success"},
            "health": {"status": "warning"}
        }

        metrics = HealthMetricsExtractor.extract(validations)

        assert metrics.healthy_components == 3
        assert metrics.warnings == 1
        assert metrics.directory_violations == 0
        assert not metrics.is_critical
        assert not metrics.is_healthy

class TestPerformance:
    def test_formatting_performance(self):
        """Test formatting performance meets sub-50ms requirement."""
        formatter = OutputFormatter()
        large_result = generate_test_result()  # Helper function

        import time
        start = time.perf_counter()
        output = formatter.format_result(large_result, "quick")
        duration = time.perf_counter() - start

        assert duration < 0.05, f"Formatting took {duration:.3f}s, expected <0.05s"
        assert len(output) > 1000
```

## Success Metrics

### Code Quality
- **MainCodeExecutor**: Reduce from 482 to ~380 lines (-21%)
- **Cyclomatic Complexity**: Reduce from 35 to 15 (-57%)
- **Test Coverage**: Increase from 40% to 85% (+46%)
- **Testable Classes**: Increase from 1 to 3 (+200%)

### Performance
- **Formatting Time**: <50ms for typical results
- **Memory Usage**: No increase in memory footprint
- **Output Consistency**: 100% identical formatting

### Maintainability
- **SOLID Compliance**: All principles followed
- **Type Safety**: Full mypy --strict compliance
- **Documentation**: Complete docstrings with examples

## Risk Mitigation

### Technical Risks
1. **Integration Issues**: Maintain exact output during transition
2. **Performance Regression**: Benchmark before/after implementation
3. **Test Coverage**: Aim for 95%+ coverage to prevent regressions

### Mitigation Strategies
- Use property-based testing with hypothesis
- Implement gradual migration with fallback options
- Create comprehensive test suite before integration
- Maintain backward compatibility during transition

This implementation plan provides a clear, step-by-step approach to extracting the OutputFormatter while maintaining code quality, performance, and functionality.
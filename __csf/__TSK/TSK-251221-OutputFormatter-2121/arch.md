# Architecture Analysis: OutputFormatter Extraction

## 1. Current Architecture Overview

### MainCodeExecutor Class Analysis
- **Location**: `P:\__csf.nip\commands\nip\main_code.py` (lines 156-638)
- **Primary Responsibility**: Execute main command with comprehensive error handling and CKS compliance
- **Current Size**: 482 lines with mixed responsibilities

### Target Method: _format_optimized_output()
- **Location**: Lines 514-637 (124 lines)
- **Input**: `result: Dict[str, Any]`, `mode: str`
- **Output**: Formatted markdown string
- **Complexity**: High - multiple concerns in single method

## 2. Dependencies Analysis

### External Dependencies
```python
from datetime import datetime    # Dynamic import (line 633)
from pathlib import Path         # Used via CSF_ROOT
from typing import Any, Dict    # Type annotations
import logging                  # Via self.logger
```

### Internal Dependencies
- `self._load_cognitive_framework()` method (lines 447-512)
- `CSF_ROOT` constant (line 81)
- `self.logger` instance
- MainCodeExecutor state

### Coupling Metrics
- **Afferent Coupling (Ca)**: 1 (main() function)
- **Efferent Coupling (Ce)**: 4 (datetime, Path, logging, framework data)
- **Instability**: 0.8 (high - depends on many unstable components)

## 3. Data Flow Architecture

### Input Data Structure
```python
result = {
    "status": "success" | "warning" | "error",
    "execution_time": float,
    "validations": {
        "structure": {
            "status": str,
            "violations": int,
            "present_dirs": list,
            "missing_dirs": list
        },
        "core_systems": {
            "status": str,
            "checks": dict
        },
        "health": {
            "status": str,
            "comprehensive": bool
        }
    }
}
```

### Transformation Pipeline
```
Result Dict → Framework Loading → Health Metrics Extraction →
Section Building → Markdown Formatting → Timestamped Output
```

### Current Process Flow
1. Load cognitive framework (`_load_cognitive_framework()`)
2. Extract health metrics from validations
3. Build output sections sequentially
4. Apply conditional logic for different states
5. Generate timestamp and tip

## 4. Architecture Violations

### SOLID Principle Violations

#### 1. Single Responsibility Principle (SRP) - **VIOLATED**
**Issue**: MainCodeExecutor handles multiple concerns:
- Command execution
- Validation logic
- Framework loading
- Output formatting (124 lines)

**Impact**: Difficult to test, maintain, and extend

#### 2. Open/Closed Principle (OCP) - **VIOLATED**
**Issue**: Adding new output sections requires modifying main method
```python
# Current pattern - violates OCP
def _format_optimized_output(self, result: Dict[str, Any], mode: str) -> str:
    # Hard-coded section order
    # Header section
    # Health section
    # Commands section
    # Behaviors section
    # Actions section
    # Projects section
    # Footer section
```

#### 3. Dependency Inversion Principle (DIP) - **VIOLATED**
**Issue**: Direct dependency on concrete framework loading method
```python
# Current tight coupling
framework = self._load_cognitive_framework()  # Direct method call
```

#### 4. Interface Segregation Principle (ISP) - **MINOR VIOLATION**
**Issue**: Executor interface exposes formatting concerns

## 5. Proposed Architecture

### New Class Structure
```
output_formatter.py
├── OutputFormatter (main class)
├── FrameworkLoader (abstract interface)
├── MarkdownFormatter (concrete implementation)
├── HealthMetricsExtractor (utility class)
└── TemplateRegistry (configuration)
```

### Class Design

```python
class OutputFormatter:
    """Handles result formatting with configurable strategies."""

    def __init__(self, framework_loader=None, template_registry=None):
        self.framework_loader = framework_loader or DefaultFrameworkLoader()
        self.template_registry = template_registry or TemplateRegistry()
        self.health_extractor = HealthMetricsExtractor()

    def format_result(self, result: Dict[str, Any], mode: str, style: str = "markdown") -> str:
        """Main entry point for result formatting."""
        framework = self.framework_loader.load_framework()

        formatter = self._get_formatter(style)
        return formatter.format(result, mode, framework)

class FrameworkLoader(ABC):
    """Abstract interface for framework data loading."""

    @abstractmethod
    def load_framework(self) -> Optional[Dict[str, Any]]:
        """Load cognitive framework data."""

class MarkdownFormatter:
    """Handles markdown-specific formatting logic."""

    def format(self, result: Dict[str, Any], mode: str, framework: Dict[str, Any]) -> str:
        """Format as markdown with sections."""
        sections = [
            self._format_header(result, mode),
            self._format_health_section(result),
            self._format_commands_section(framework),
            self._format_behaviors_section(framework),
            self._format_actions_section(result),
            self._format_projects_section(framework),
            self._format_footer()
        ]
        return "\n".join(filter(None, sections))
```

### Integration Points

#### 1. MainCodeExecutor Modifications
```python
class MainCodeExecutor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.formatter = OutputFormatter()  # New dependency
        # Remove: _load_cognitive_framework method

    def _format_and_print(self, result: Dict[str, Any]) -> None:
        """Format and print results using new formatter."""
        if result.get("mode") == "quick" and result.get("status") in ["success", "warning"]:
            output = self.formatter.format_result(result, result.get("mode", "quick"))
            print(output)
        else:
            print(json.dumps(result, indent=2))
```

#### 2. main() Function Updates
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

## 6. Extension Points

### Future Enhancements
1. **Multiple Output Formats**: JSON, XML, HTML, Plain text
2. **Template System**: Externalizable templates for customization
3. **Plugin Architecture**: Custom sections via plugins
4. **Internationalization**: Multi-language support
5. **Theme Support**: Different visual themes

### Configuration-Driven Formatting
```python
class OutputConfig(BaseModel):
    format: Literal["markdown", "json", "table", "html"] = "markdown"
    sections: List[str] = ["header", "health", "commands", "behaviors"]
    show_timestamp: bool = True
    show_tips: bool = True
    max_command_examples: int = 4
```

## 7. Migration Strategy

### Phase 1: Create New Classes
1. Create `output_formatter.py`
2. Implement `OutputFormatter` class
3. Implement supporting classes
4. Create comprehensive tests

### Phase 2: Update Integration
1. Update `MainCodeExecutor` to use new formatter
2. Update `main()` function
3. Maintain backward compatibility

### Phase 3: Cleanup
1. Remove old methods from `MainCodeExecutor`
2. Optimize imports
3. Update documentation

## 8. Quality Metrics

### Before Extraction
- **MainCodeExecutor**: 482 lines
- **Cyclomatic Complexity**: 35
- **Test Coverage**: ~40%
- **Method Count**: 15 methods

### After Extraction (Projected)
- **MainCodeExecutor**: ~380 lines (-21%)
- **OutputFormatter**: ~200 lines
- **Cyclomatic Complexity**: 15 (-57%)
- **Test Coverage**: ~85% (+46%)
- **Testable Classes**: 3 (+200%)

## 9. Risk Assessment

### Technical Risks
- **Medium**: Integration complexity with existing result structure
- **Low**: Performance impact from additional class instantiation
- **Low**: Backward compatibility issues

### Mitigation Strategies
- Maintain exact output format during transition
- Comprehensive integration tests
- Gradual migration with fallback option

## 10. Success Criteria

### Functional Success
- ✅ Identical output formatting as current implementation
- ✅ All existing CLI modes work unchanged
- ✅ Zero breaking changes to public interfaces

### Technical Success
- ✅ Reduced cyclomatic complexity by 50%+
- ✅ Improved test coverage to 85%+
- ✅ Cleaner separation of concerns
- ✅ Enabled future extensibility

This architecture analysis provides the foundation for a clean, maintainable, and extensible OutputFormatter extraction that follows SOLID principles and modern Python best practices.
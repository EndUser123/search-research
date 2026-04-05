# BugJail - Automated Bug Detection System

Phase 2 Implementation for CSF NIP Security Framework

## Overview

BugJail is a comprehensive automated bug detection and vulnerability scanning system that integrates with the CSF NIP exploration workflow. It provides static analysis capabilities with constitutional compliance validation and actionable fix recommendations.

## Features

### Core Capabilities

- **Pattern-Based Bug Detection**: Detects common bug patterns across multiple programming languages
- **OWASP Top 10 Vulnerability Scanning**: Comprehensive security vulnerability detection
- **Constitutional Compliance Validation**: Ensures CSF NIP constitutional requirements are met
- **Actionable Fix Recommendations**: Provides specific code fixes and best practice guidance
- **Exploration Workflow Integration**: Seamlessly integrates with CWO12 and RCA workflows

### Supported Languages

- Python
- JavaScript / TypeScript
- Java
- C/C++
- C#
- Go
- Rust

### Bug Categories

- Null Pointer Dereference
- Race Conditions
- Logic Errors
- Resource Leaks
- Memory Leaks
- API Misuse
- Division by Zero
- Array Bounds Issues
- Type Errors
- Infinite Loops
- Dead Code

### Vulnerability Types (OWASP Top 10)

- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Identification/Authentication Failures
- A08: Software/Data Integrity Failures
- A09: Logging/Monitoring Failures
- A10: Server-Side Request Forgery

## Quick Start

### Basic Usage

```python
from bugjail import BugJailDetector, BugJailConfig

# Create detector with default configuration
detector = BugJailDetector()

# Analyze a file
report = detector.analyze_path("/path/to/your/code.py")

# View results
print(f"Found {report.total_issues} issues")
print(f"Bugs: {len(report.bugs)}")
print(f"Vulnerabilities: {len(report.vulnerabilities)}")

# View recommendations
for rec in report.recommendations:
    print(f"- {rec.title}: {rec.description}")
```

### Custom Configuration

```python
from bugjail import BugJailDetector, BugJailConfig, BugSeverity

# Create custom configuration
config = BugJailConfig(
    min_severity_level=BugSeverity.HIGH,
    enable_vulnerability_scanning=True,
    enable_constitutional_compliance=True,
    include_patterns=["**/*.py", "**/*.js"],
    exclude_patterns=["**/test/**", "**/node_modules/**"],
    parallel_analysis=True,
    max_workers=4
)

# Create detector with custom config
detector = BugJailDetector(config)
```

### Integration with CWO12 Workflow

```python
from bugjail import BugJailAnalyzer
import asyncio

# Create analyzer
analyzer = BugJailAnalyzer()

# CWO12 Step 5 - Architecture Analysis
async def step5_analysis():
    result = await analyzer.trigger_cwo12_step5_enhancement("/path/to/project")
    print(f"Found {result['architecture_analysis']['total_issues']} issues")
    return result

# Run analysis
result = asyncio.run(step5_analysis())
```

## Architecture

### Core Components

1. **Detector** (`core/detector.py`): Main detection engine
2. **Analyzer** (`core/analyzer.py`): Orchestrates analysis and workflow integration
3. **Pattern Library** (`patterns/library.py`): Manages detection patterns
4. **Vulnerability Scanner** (`vulnerability/scanner.py`): OWASP vulnerability detection
5. **Compliance Validator** (`compliance/validator.py`): Constitutional compliance checking
6. **Recommendation Engine** (`recommendations/engine.py`): Fix recommendation generation

### Data Flow

```
Source Code → Pattern Matching → AST Analysis → Vulnerability Scanning
    ↓
Constitutional Compliance Validation → Recommendation Generation
    ↓
Analysis Report → Integration Callbacks → Workflow Enhancement
```

## API Reference

### REST API

BugJail provides a REST API for integration with external systems.

#### Scan a Path

```python
from bugjail.api import BugJailAPI

api = BugJailAPI()

# Scan a directory
request = {
    "path": "/path/to/scan",
    "options": {
        "min_severity": "medium",
        "enable_vulnerabilities": True,
        "parallel": True
    }
}

response = api.scan_path(request)
report = response["data"]
```

#### CWO12 Integration

```python
# CWO12 Step 5
request = {
    "project_path": "/path/to/project",
    "step": "step5"
}
response = api.trigger_cwo12_analysis(request)

# CWO12 Step 7
request = {
    "project_path": "/path/to/project",
    "step": "step7",
    "step7_tasks": ["Refactor auth module", "Add input validation"]
}
response = api.trigger_cwo12_analysis(request)
```

## Configuration Options

### BugJailConfig

- `enable_bug_detection`: Enable bug pattern detection (default: True)
- `enable_vulnerability_scanning`: Enable OWASP vulnerability scanning (default: True)
- `enable_constitutional_compliance`: Enable constitutional validation (default: True)
- `min_severity_level`: Minimum severity level to report (default: LOW)
- `include_patterns`: File patterns to include (default: Python, JS, TS)
- `exclude_patterns`: File patterns to exclude (default: node_modules, __pycache__)
- `parallel_analysis`: Enable parallel file analysis (default: True)
- `max_workers`: Maximum worker threads (default: 4)
- `generate_recommendations`: Generate fix recommendations (default: True)

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest bugjail/tests/

# Run specific test module
python -m pytest bugjail/tests/test_patterns.py

# Run with coverage
python -m pytest --cov=bugjail bugjail/tests/
```

### Test Coverage

The test suite covers:
- Bug detection patterns
- Vulnerability scanning
- Constitutional compliance validation
- Exploration workflow integration
- API endpoints
- Error handling

## Constitutional Compliance

BugJail enforces CSF NIP constitutional requirements:

### Anti-Sycophancy
- Ensures security issues are marked with appropriate severity
- Prevents agreement with incorrect code patterns
- Validates confidence scores reflect actual certainty

### Data Safety
- Prevents operations that could cause data loss
- Flags potentially destructive operations
- Requires explicit user confirmation for risky operations

### Truthfulness
- Ensures honest confidence scoring
- Marks uncertain findings appropriately
- Avoids unsubstantiated claims

### Solo Developer Context
- Avoids enterprise over-engineering patterns
- Keeps complexity manageable for solo development
- Follows 75-85% reliability target

## Integration Points

### CWO12 Workflow

- **Step 5**: Enhanced architecture analysis with bug detection
- **Step 7**: Pre-implementation risk assessment and issue identification

### RCA Enhancement

- Bug localization based on error information
- Related issue identification
- Suggested root causes and recommendations

### Pre-commit Hooks

- Automatic scan before commits
- Block commits with critical vulnerabilities
- Provide immediate feedback

## Performance

### Benchmarks

- **Small projects** (< 100 files): < 5 seconds
- **Medium projects** (100-1000 files): < 30 seconds
- **Large projects** (> 1000 files): < 2 minutes

### Optimization Features

- Parallel file processing
- Result caching
- Incremental analysis
- Configurable analysis depth

## Contributing

### Adding New Patterns

1. Create pattern in appropriate language file
2. Add test cases in `tests/test_patterns.py`
3. Update documentation

```python
from bugjail.patterns.library import DetectionPattern, BugCategory, BugSeverity

pattern = DetectionPattern(
    id="custom_001",
    name="Custom Pattern",
    category=BugCategory.LOGIC_ERROR,
    severity=BugSeverity.MEDIUM,
    pattern=r"custom_regex_pattern",
    language="python",
    description="Custom pattern description"
)
```

### Adding New Vulnerability Types

1. Update `vulnerability/scanner.py`
2. Add OWASP category mapping
3. Create test cases

### Adding Constitutional Rules

1. Create rule in `compliance/validator.py`
2. Define violation conditions
3. Add compliance tests

## License

BugJail is part of the CSF NIP Security Framework.

## Support

For issues and questions:
- Check the test suite for usage examples
- Review the API reference documentation
- Consult the constitutional compliance guidelines
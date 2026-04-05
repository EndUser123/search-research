# Critic System Documentation

## Overview

The Critic System is a comprehensive code and architecture evaluation framework for the Persistent Learning Agent Ecosystem. It provides actionable feedback, quality scoring, and architectural analysis to improve code quality and maintainability.

## Components

### 1. CodeCritic (`critic.py`)

The `CodeCritic` class analyzes Python code for quality issues including:

- **Complexity Analysis**: Cyclomatic complexity, cognitive complexity, parameter count
- **Security Issues**: Hardcoded passwords, dangerous eval usage, shell injection risks
- **Performance Issues**: Inefficient patterns, string concatenation problems
- **Maintainability**: Empty functions/classes, TODO/FIXME comments
- **Style Issues**: Code style violations, long lines

#### Key Features:
- AST-based structural analysis
- Pattern-based issue detection
- Configurable complexity thresholds
- Quality score calculation (0-100 scale)
- Actionable recommendations

#### Usage:
```python
from critic import create_critic

critic = create_critic()
result = critic.evaluate_code(code_string, file_path="example.py")

print(f"Quality Score: {result.quality_score.overall}/100")
print(f"Issues Found: {len(result.issues)}")
for issue in result.issues:
    print(f"- [{issue.severity.value.upper()}] {issue.title}")
```

### 2. ArchitectureCritic (`critic.py`)

The `ArchitectureCritic` class evaluates software architecture and design patterns:

- **Project Structure**: Essential directories, configuration files
- **Dependencies**: Circular imports, dependency management
- **Design Patterns**: Singleton, Factory, Observer pattern usage
- **SOLID Principles**: Adherence to Single Responsibility, Open/Closed, etc.
- **Quality Gates**: Configurable quality thresholds

#### Key Features:
- Comprehensive project analysis
- SOLID principles validation
- Design pattern detection
- Architecture quality scoring
- Refactoring recommendations

#### Usage:
```python
from critic import create_critic

critic = create_critic()
result = critic.evaluate_architecture(project_path)

print(f"Architecture Score: {result.quality_score.overall}/100")
for recommendation in result.recommendations:
    print(f"- {recommendation}")
```

### 3. EvaluationPipeline (`evaluation.py`)

The `EvaluationPipeline` orchestrates evaluation tasks with advanced features:

- **Async Processing**: Concurrent evaluation with configurable workers
- **Priority Queue**: Task prioritization and dependency management
- **Caching**: Result caching to avoid redundant evaluations
- **Quality Gates**: Automated quality threshold checking
- **Continuous Evaluation**: Periodic re-evaluation of targets
- **Batch Processing**: Evaluate multiple files/projects together

#### Configuration Options:
```python
from evaluation import EvaluationConfig, Priority, EvaluationType

config = EvaluationConfig(
    max_concurrent_evaluations=5,
    cache_enabled=True,
    cache_ttl=3600.0,  # 1 hour
    quality_gates={
        'critical_threshold': 60.0,
        'warning_threshold': 80.0,
        'max_critical_issues': 5,
        'max_total_issues': 50
    }
)
```

#### Usage:
```python
from evaluation import create_evaluation_pipeline, Priority

pipeline = create_evaluation_pipeline(config)
pipeline.start()

# Submit evaluation task
task_id = pipeline.evaluate_code(code, priority=Priority.HIGH)

# Wait for completion
result = pipeline.wait_for_completion(task_id, timeout=30.0)

# Generate report
report = pipeline.generate_report("evaluation_report.json")
```

## Quality Scoring System

### Score Calculation (0-100 Scale)

- **Base Score**: 100 points
- **Deductions**:
  - Critical Issues: -25 points each
  - High Issues: -15 points each
  - Medium Issues: -8 points each
  - Low Issues: -3 points each
  - Info Issues: -1 point each

### Category Scores

- **Security**: Vulnerability and security practice assessment
- **Performance**: Performance optimization opportunities
- **Maintainability**: Code structure and documentation
- **Style**: Coding style and formatting compliance
- **Complexity**: Cyclomatic and cognitive complexity
- **Architecture**: Design pattern and SOLID principles

### Quality Interpretation

- **90-100**: Excellent quality, production-ready
- **80-89**: Good quality, minor improvements needed
- **70-79**: Acceptable quality, moderate improvements needed
- **60-69**: Below standard, significant improvements needed
- **0-59**: Poor quality, major refactoring required

## Issue Types and Severity

### Severity Levels

1. **Critical**: Blocks execution (syntax errors, runtime errors)
2. **High**: Major quality issues (security vulnerabilities, performance problems)
3. **Medium**: Moderate issues (complexity, design violations)
4. **Low**: Minor issues (style, documentation)
5. **Info**: Informational (suggestions, best practices)

### Common Issue Categories

#### Security Issues
- Hardcoded passwords/API keys
- Dangerous eval() or exec() usage
- Shell injection vulnerabilities
- Insecure default configurations

#### Performance Issues
- Inefficient loops and iterations
- Memory leaks
- Poor database queries
- Inefficient string operations

#### Maintainability Issues
- High cyclomatic complexity
- Too many parameters
- Large classes/functions
- Duplicate code
- Missing documentation

#### Style Issues
- Code formatting violations
- Naming convention violations
- Inconsistent style
- Long lines

## Integration with Agent Factory

The Critic System is integrated with the Agent Factory module:

```python
from agent_factory import (
    create_critic,
    create_evaluation_pipeline,
    quick_evaluate_code,
    quick_evaluate_file,
    quick_evaluate_project
)

# Quick evaluations
result = quick_evaluate_code("def test(): pass")
result = quick_evaluate_file("example.py")
results = quick_evaluate_project("path/to/project")
```

## Example Usage Patterns

### 1. Continuous Integration

```python
# In CI/CD pipeline
from evaluation import create_evaluation_pipeline

pipeline = create_evaluation_pipeline()
pipeline.start()

# Evaluate all changed files
for file in changed_files:
    task_id = pipeline.evaluate_file(file, priority=Priority.HIGH)

# Wait for all evaluations
for task_id in task_ids:
    result = pipeline.wait_for_completion(task_id)
    if result.quality_score.overall < 80:
        raise Exception(f"Quality gate failed: {result.quality_score.overall}")
```

### 2. Development Feedback

```python
# IDE integration or pre-commit hook
from critic import evaluate_file

import sys
file_path = sys.argv[1]
result = evaluate_file(file_path)

if result.quality_score.overall < 85:
    print(f"⚠️  Quality score: {result.quality_score.overall}/100")
    print("Top issues:")
    for issue in result.issues[:5]:
        print(f"- {issue.title}")
        print(f"  {issue.suggestion}")
```

### 3. Architecture Review

```python
# Project health check
from critic import create_critic

critic = create_critic()
result = critic.evaluate_architecture("project_path")

print(f"Architecture Health: {result.quality_score.overall}/100")
if result.quality_score.overall < 70:
    print("🚨 Architecture needs attention!")
    for rec in result.recommendations:
        print(f"- {rec}")
```

## Configuration and Customization

### Customizing Thresholds

```python
from critic import CodeCritic

critic = CodeCritic()
critic.complexity_thresholds = {
    'cyclomatic_complexity': 15,  # Default: 10
    'cognitive_complexity': 20,   # Default: 15
    'max_lines_per_function': 75, # Default: 50
    'max_parameters': 7,          # Default: 5
    'max_nesting_depth': 5        # Default: 4
}
```

### Custom Quality Patterns

```python
critic.quality_patterns['custom'] = [
    re.compile(r'FIXME'),  # Custom pattern detection
    re.compile(r'HACK'),   # Another custom pattern
]
```

### Quality Gates Configuration

```python
from evaluation import EvaluationConfig

config = EvaluationConfig(
    quality_gates={
        'critical_threshold': 70.0,  # Stricter threshold
        'warning_threshold': 85.0,   # Warning level
        'max_critical_issues': 2,    # Allow fewer critical issues
        'max_total_issues': 30       # Lower total issue limit
    }
)
```

## Performance Considerations

### Caching
- Enable result caching for repeated evaluations
- Configure TTL based on change frequency
- Cache size management for large projects

### Concurrency
- Adjust worker count based on system resources
- Use appropriate timeouts for large files
- Monitor memory usage for batch evaluations

### Optimization Tips
- Use file filters to exclude non-relevant files
- Batch evaluate similar files together
- Configure appropriate complexity thresholds

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Memory Issues**: Reduce concurrent evaluations or enable caching
3. **Timeout Errors**: Increase timeout for large files/projects
4. **False Positives**: Adjust thresholds or custom patterns

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for critic system
logger = logging.getLogger('critic')
logger.setLevel(logging.DEBUG)
```

## API Reference

### Core Classes

- `CriticSystem`: Main orchestrator for code and architecture evaluation
- `CodeCritic`: Specialized code quality analysis
- `ArchitectureCritic`: Architecture and design pattern evaluation
- `EvaluationPipeline`: Task-based evaluation orchestration

### Data Classes

- `CriticResult`: Complete evaluation result with scores and issues
- `CriticIssue`: Individual issue with metadata and suggestions
- `QualityScore`: Quality assessment with category breakdown
- `EvaluationTask`: Task definition for pipeline processing

### Enums

- `Severity`: Issue severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `CriticType`: Type of critic (CODE, ARCHITECTURE, SECURITY, etc.)
- `EvaluationType`: Evaluation type (CODE, ARCHITECTURE, PROJECT, BATCH)
- `Priority`: Task priority (LOW, MEDIUM, HIGH, CRITICAL, URGENT)

### Factory Functions

- `create_critic()`: Create configured critic system
- `create_evaluation_pipeline()`: Create configured evaluation pipeline
- `quick_evaluate_*()`: Simple evaluation functions

## Contributing

When extending the Critic System:

1. **New Issue Types**: Add new issue categories and severity levels
2. **Custom Patterns**: Extend pattern detection for domain-specific issues
3. **Quality Metrics**: Add new quality metrics and scoring algorithms
4. **Integration Points**: Add new evaluation pipeline integrations

## License

This Critic System is part of the CSF NIP Persistent Learning Agent Ecosystem.
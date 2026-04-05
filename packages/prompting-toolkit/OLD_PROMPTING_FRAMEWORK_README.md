# prompting-framework

> Advanced prompt optimization framework with GA/DE algorithms and multi-strategy optimization

[![PyPI Version](https://img.shields.io/pypi/v/prompting-framework)](https://pypi.org/project/prompting-framework/)
[![Python Version](https://img.shields.io/pypi/pyversions/prompting-framework)](https://pypi.org/project/prompting-framework/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/csf-framework/prompting-framework/actions)
[![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen.svg)](https://github.com/csf-framework/prompting-framework/actions)

## Features

- **Meta-Prompt Optimization**: Genetic Algorithm (GA) and Differential Evolution (DE) for prompt optimization
- **Multi-Strategy Support**: Chain-of-Verification, Socratic, Self-Refine, and more
- **Context-Aware Selection**: Automatic technique selection based on query characteristics
- **Performance Monitoring**: Built-in performance tracking and optimization
- **Constitutional Compliance**: Safety constraints built into the framework
- **Plugin Architecture**: Extensible technique system

## Quick Start

### Installation

```bash
pip install prompting-framework
```

### Basic Usage

```python
from prompting_framework import PromptingOrchestrator, PromptingContext

orchestrator = PromptingOrchestrator()
context = PromptingContext(
    query="How should I implement this feature?",
    domain="software",
    complexity="medium",
    user_intent="get_advice"
)

techniques = await orchestrator.select_applicable_techniques(context)
print(f"Applicable techniques: {[t.name for t in techniques]}")
```

### Prompt Optimization

```python
from prompting_framework import MetaPromptOptimizer, OptimizationConfig

config = OptimizationConfig(
    strategy=OptimizationStrategy.GENETIC_ALGORITHM,
    generations=10,
    population_size=20
)

optimizer = MetaPromptOptimizer(config)
result = optimizer.optimize(
    initial_prompt="You are a helpful assistant.",
    evaluator=lambda prompt: evaluate_quality(prompt)  # Your evaluation function
)

print(f"Best prompt: {result.best_prompt}")
print(f"Score: {result.best_score}")
```

## Architecture

```
prompting-framework/
├── src/prompting_framework/
│   ├── base_prompting_technique.py    # Abstract base for all techniques
│   ├── meta_prompt_optimizer.py        # GA/DE optimization engine
│   ├── prompting_orchestrator.py      # Main orchestration logic
│   ├── context_models.py               # Data models for context
│   ├── techniques/                    # Concrete technique implementations
│   │   ├── chain_of_verification.py
│   │   ├── socratic_prompting.py
│   │   ├── self_refine.py
│   │   └── ...
│   └── config/                       # Configuration files
└── tests/                           # Test suite
```

## Techniques

| Technique | Description | Use Case |
|-----------|-------------|-----------|
| Chain-of-Verification | Multi-step verification | Critical reasoning tasks |
| Socratic Prompting | Question-based guidance | Learning and exploration |
| Self-Refine | Iterative self-improvement | Writing and analysis |
| Query Fanout | Parallel query execution | Complex multi-faceted queries |
| Verbalized Sampling | Explicit reasoning | Math and logic problems |

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/csf-framework/prompting-framework.git
cd prompting-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=prompting_framework --cov-report=html

# Run specific test file
pytest tests/unit/test_optimizer.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Configuration

Configuration can be provided through:

1. **Environment variables**: Prefix with `PROMPTING_FRAMEWORK_`
2. **Config files**: JSON format in standard locations
3. **Programmatic**: Python API for runtime configuration

```python
from prompting_framework import MetaPromptOptimizer, OptimizationConfig

config = OptimizationConfig(
    generations=20,
    population_size=50,
    mutation_rate=0.1,
    crossover_rate=0.8
)

optimizer = MetaPromptOptimizer(config)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 1.0.0 (2025-02-13)

- Initial release as standalone package
- 23 technique modules migrated from CSF framework
- GA/DE optimization algorithms
- Comprehensive test suite
- Full type hints support

## Acknowledgments

- Built with [Python](https://www.python.org/)
- Optimization algorithms inspired by [DEAP](https://github.com/DEAP/deap)
- Testing: [pytest](https://pytest.org/)

## Support

- GitHub Issues: [https://github.com/csf-framework/prompting-framework/issues](https://github.com/csf-framework/prompting-framework/issues)
- Documentation: [https://prompting-framework.readthedocs.io](https://prompting-framework.readthedocs.io)

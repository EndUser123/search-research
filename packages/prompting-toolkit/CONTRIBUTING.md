# Contributing to Prompting Toolkit

Thank you for your interest in contributing! This document provides guidelines for contributing to the Prompting Toolkit monorepo.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Requests](#pull-requests)
- [Package-Specific Guidelines](#package-specific-guidelines)

---

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build better prompting tools together.

---

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Familiarity with prompt engineering concepts

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/csf-dev/prompting-toolkit.git
cd prompting-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e packages/hook
pip install -e packages/framework[dev,test]

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Verify Installation

```bash
# Run tests
pytest packages/hook/tests/
pytest packages/framework/tests/

# Run linting
ruff check packages/
black --check packages/
```

---

## Development Workflow

### 1. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/csf-dev/prompting-toolkit.git
cd prompting-toolkit

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation as needed
- Run tests locally before committing

### 3. Commit Changes

```bash
git add .
git commit -m "feat: add new technique for XYZ"
```

**Commit message format:**
```
<type>: <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

---

## Testing

### Hook Package Tests

```bash
cd packages/hook
pytest
pytest --cov=hook --cov-report=html
```

### Framework Package Tests

```bash
cd packages/framework
pytest
pytest --cov=prompting_framework --cov-report=html
```

### All Tests (From Root)

```bash
pytest packages/hook/tests packages/framework/tests
```

### Writing Tests

- Unit tests for individual functions
- Integration tests for complex workflows
- Async tests for async functions (use `pytest-asyncio`)
- Mock external dependencies (use `pytest-mock`)

**Example:**

```python
import pytest
from prompting_framework import PromptingOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_selects_techniques():
    orchestrator = PromptingOrchestrator()
    context = PromptingContext(
        query="test query",
        domain="general",
        complexity="low"
    )
    techniques = await orchestrator.select_applicable_techniques(context)
    assert len(techniques) > 0
```

---

## Documentation

### Code Documentation

- Use docstrings for all public functions/classes
- Follow Google docstring style
- Include type hints

```python
def enhance_prompt(prompt: str, context: dict) -> str:
    """Enhance a prompt with domain-specific guidance.

    Args:
        prompt: The original user prompt
        context: Domain and complexity information

    Returns:
        Enhanced prompt with additional guidance

    Raises:
        ValueError: If prompt is empty
    """
    ...
```

### README Updates

- Update relevant README for package-level changes
- Add examples for new features
- Update installation instructions if needed

### Example Updates

- Add new examples to `examples/`
- Update `examples/README.md` with new examples
- Ensure examples are runnable and well-documented

---

## Pull Requests

### PR Title Format

Use the same format as commit messages:

```
feat: add new prompting technique
fix: resolve race condition in state management
docs: update migration guide
```

### PR Description

Include:

- **What:** Summary of changes
- **Why:** Motivation for the change
- **How:** Implementation approach
- **Testing:** How you tested the changes
- **Screenshots:** If applicable (UI changes)

### Review Checklist

Before submitting, ensure:

- [ ] Tests pass locally
- [ ] Code follows style guidelines (black, ruff)
- [ ] Documentation updated
- [ ] Examples added/updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Commits follow commit message format

---

## Package-Specific Guidelines

### Hook Package (`packages/hook/`)

**Scope:** Claude Code integration, automatic prompt enhancement

**Guidelines:**
- Minimal dependencies (prefer zero external deps)
- Multi-terminal safe (isolated state)
- Fast execution (hooks block Claude Code)
- Clear user feedback (choice UI)

**Example Contributions:**
- New domain detection patterns
- Improved complexity analysis
- Better state management
- Enhanced choice UI

### Framework Package (`packages/framework/`)

**Scope:** Python library, prompting strategies, optimization algorithms

**Guidelines:**
- Full type hints required
- Comprehensive tests (70%+ coverage)
- Performance conscious (optimization algorithms)
- Well-documented techniques

**Example Contributions:**
- New prompting techniques
- Additional optimization strategies
- Performance improvements
- Better context models

---

## Code Style

### Formatting

We use **Black** for code formatting:

```bash
black packages/ --line-length 100
```

### Linting

We use **Ruff** for linting:

```bash
ruff check packages/ --fix
```

### Type Checking

We use **mypy** for type checking (framework package):

```bash
mypy packages/framework/src/
```

---

## Questions or Issues?

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas
- **Pull Requests:** Contributions

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

Thank you for contributing! 🚀

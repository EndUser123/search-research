# Contributing to rca

Thank you for your interest in contributing to rca! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/EndUser123/rca.git
cd rca
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Install in editable mode:
```bash
pip install -e ".[dev,test]"
```

## Running Tests

### Run All Tests

```bash
pytest tests/ skill/tests/ -v
```

### Run with Coverage

```bash
pytest --cov=rca --cov-report=html tests/ skill/tests/
```

### Run Specific Test

```bash
pytest tests/test_session.py -v
pytest skill/tests/test_evidence_saturation.py -v
```

## Code Style

This project uses:
- **ruff** for linting and formatting
- **mypy** for type checking

### Linting

```bash
ruff check src/
```

### Auto-fix Lint Issues

```bash
ruff check --fix src/
```

### Type Checking

```bash
mypy src/rca/
```

## Project Structure

```
rca/
├── src/rca/         # Python package source
│   ├── cli.py             # CLI entry point
│   ├── session.py         # Session management
│   ├── error_signature.py # Error analysis
│   └── ...
├── skill/                 # Claude Code skill
│   ├── SKILL.md           # Skill definition
│   ├── hooks/             # Hook implementations
│   ├── templates/         # Report templates
│   └── tests/             # Skill tests
├── tests/                 # Package tests
├── README.md
├── LICENSE
├── pyproject.toml
└── CHANGELOG.md
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes and commit:
```bash
git add .
git commit -m "feat: add your feature description"
```

4. Run tests and linting:
```bash
pytest tests/ skill/tests/ -v
ruff check src/
```

5. Push to your fork:
```bash
git push origin feature/your-feature-name
```

6. Create a pull request on GitHub

## Commit Message Convention

We follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Example:
```bash
git commit -m "feat: add evidence saturation algorithm"
git commit -m "fix: resolve session state persistence issue"
```

## Development Guidelines

### Code Quality

- Write descriptive docstrings for functions and classes
- Use type hints for function signatures
- Keep functions focused and modular
- Add tests for new functionality

### Testing

- Write tests for new features
- Maintain test coverage above 80%
- Use pytest fixtures for common test setup
- Mock external dependencies

### Documentation

- Update README.md for user-facing changes
- Update SKILL.md for skill behavior changes
- Add docstrings to new modules and functions
- Update CHANGELOG.md for version changes

## Questions or Issues?

- Open an issue on GitHub for bugs or feature requests
- Check existing issues before creating new ones
- Use discussions for questions and general topics

## License

By contributing to rca, you agree that your contributions will be licensed under the MIT License.

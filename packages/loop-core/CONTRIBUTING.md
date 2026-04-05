# Contributing to loop-core

Thank you for your interest in contributing to loop-core!

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/python-kyt/loop-code.git
   cd loop-core
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e .
   pip install pytest pytest-cov ruff mypy
   ```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=loop_core --cov-report=term-missing

# Run specific test file
pytest tests/test_state_manager.py -v
```

## Code Style

This project uses:
- **Ruff** for linting and formatting
- **Mypy** for type checking
- **pytest** for testing

Run checks before submitting:
```bash
ruff check .
ruff format --check .
mypy loop_core/
pytest tests/ -v
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Test Coverage

We aim for 80%+ test coverage. New features should include:
- Unit tests for core functionality
- Integration tests for component interaction
- Regression tests to prevent breaking changes

## Documentation

Update documentation for:
- New features or functions (docstrings)
- Changed behavior (README.md)
- Breaking changes (CHANGELOG.md)

Thank you for contributing! 🎉

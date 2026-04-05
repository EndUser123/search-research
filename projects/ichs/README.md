# iCHS - Intelligent Code Health System

iCHS is an AI-powered code quality analysis and improvement system that provides comprehensive insights into your codebase health, identifies patterns, and suggests improvements.

## Features

- **AI-Powered Analysis**: Leverages OpenAI and Anthropic APIs for intelligent code analysis
- **Multi-Tool Integration**: Works with Ruff, mypy, and other popular Python tools
- **Historical Tracking**: Maintains a database of analysis results for trend analysis
- **Issue Correlation**: Identifies related issues and calculates risk scores
- **Trend Analysis**: Visualizes code quality trends over time
- **Autofix Capabilities**: Safe, Git-integrated autofix suggestions
- **Comprehensive Reporting**: Generates detailed markdown reports
- **Async CLI**: Fast, non-blocking command-line interface

## Installation

```bash
pip install -e .
```

For development dependencies:

```bash
pip install -e .[dev]
```

## Quick Start

```bash
# Analyze the current directory
ichs analyze

# Analyze a specific directory
ichs analyze /path/to/your/project

# Generate a report
ichs report

# Run with specific tools
ichs analyze --tools ruff,mypy
```

## Configuration

Create an `ichs.toml` configuration file in your project root:

```toml
[database]
path = "./ichs.db"

[analysis]
tools = ["ruff", "mypy"]
max_file_size = "10MB"
exclude_patterns = ["*/tests/*", "*/venv/*"]

[ai]
openai_api_key = "your-openai-key"
anthropic_api_key = "your-anthropic-key"
model = "gpt-4"

[reporting]
output_dir = "./reports"
include_charts = true
```

## Project Structure

```
ichs/
├── __init__.py           # Package initialization
├── config.py            # Configuration management
├── runner.py            # Command execution engine
├── database.py          # Database operations
├── synthesis.py         # Issue correlation and risk scoring
├── trends.py            # Trend analysis and visualization
├── diagnostics.py       # AI-powered diagnostics
├── autofix.py           # Safe autofix capabilities
├── reporting.py         # Report generation
├── cli.py               # Command-line interface
├── parsers/             # Output parsers
│   ├── __init__.py
│   └── ruff.py          # Ruff output parser
└── setup.py             # Package setup
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy ichs/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

# AI Coding Agent Instructions for _Projects Workspace

## Project Overview
This is a complex Python workspace containing multiple AI/ML projects, testing frameworks, and development tools. The workspace follows a modular architecture with extensive AI integration and Test-Driven Development (TDD) methodology. The Cognitive Steering Framework (CSF) provides tools and workflows for developing other projects in the workspace.

## Core Architecture

### Multi-Project Structure
- **Main Workspace**: `c:\_Python\_Projects\` - Root workspace with shared configuration
- **CSF NIP Framework**: `__csf.nip/` - Cognitive Steering Framework tools and workflows for developing other projects
- **Scripts Directory**: `scripts/` - Shared utilities and automation tools

### Key Components
- **LiteLLM Configuration**: `config.yaml` - Complex model routing with fallbacks (OpenRouter, Chutes AI, Gemini, Groq)
- **AI Tool Integration**: AI-powered tool recommenders and intelligent development assistants
- **Database Services**: SQLite-based services with transaction management and dependency injection

## Development Workflow

### Testing Strategy
- **TDD Methodology**: Red-Green-Refactor cycle extensively used
- **Test Configuration**: `pytest.ini` restricts testing to `__csf.nip/tests/` to avoid conflicts
- **Test Categories**: Unit, integration, validation-gate tests
- **Coverage**: Extensive test coverage with specialized markers

### Build & Dependencies
- **Package Management**: `pyproject.toml` with dev, ml, and core dependencies
- **Python Version**: Requires Python 3.11+ (`python_version = "3.11"`)
- **Virtual Environment**: Use `uv` for dependency management and virtual environments

### Code Quality
- **Linting**: Ruff for fast Python linting (`ruff check --fix`)
- **Formatting**: Black with 88-character line length
- **Type Checking**: MyPy with strict settings
- **Import Sorting**: Ruff handles import organization

## Critical Patterns & Conventions

### AI Integration Patterns
- **Context Injection**: Comprehensive context provided to AI agents for implementation
- **Validation Loops**: Executable tests/lints run during development cycles
- **Tool Recommendations**: AI-powered tool suggestions based on development context

### Database Patterns
- **DatabaseService**: Centralized database abstraction replacing direct sqlite3 calls
- **Dependency Injection**: Factory functions register database services in DI containers
- **Transaction Safety**: Context managers for database operations
- **Migration Strategy**: TDD-driven migrations from direct sqlite3 to DatabaseService

### File Organization
- **Markdown Documentation**: Extensive use of `.md` files for specifications and handovers
- **Backup Files**: `.backup` extensions preserve original implementations during migrations
- **Test Structure**: `tests/` directories with comprehensive test suites
- **Configuration**: YAML/JSON configs with environment variable substitution

## Integration Points

### External Dependencies
- **AI Providers**: OpenRouter, Chutes AI, Gemini, Groq with complex fallback routing
- **Database**: SQLite with custom DatabaseService abstraction
- **Development Tools**: Git hooks, pre-commit, automated testing pipelines

### Cross-Component Communication
- **Event System**: Bidirectional sync and event handling across components
- **Configuration Sharing**: Centralized config with environment-specific overrides
- **Tool Registry**: Shared tool definitions across AI recommendation systems
- **Health Monitoring**: Comprehensive health checks and compliance validation

## Developer Workflows

### Common Commands
```bash
# Testing (restricted to CSF NIP framework)
uv run pytest __csf.nip/tests/ -v

# Code Quality
ruff check --fix && mypy .

# AI Tool Recommendations
python scripts/ai_tool_recommender.py --context "current development situation"
```

### Environment Setup
- **Virtual Environment**: `uv venv` and `uv pip install -e .`
- **Environment Variables**: Extensive use of `.env` files with API keys
- **Configuration**: `config.yaml` for LiteLLM routing, `ichs.toml` for health monitoring

### Debugging Patterns
- **Health Checks**: Automated compliance and health validation
- **Evidence Collection**: Comprehensive logging and evidence gathering
- **Error Analysis**: Detailed error reporting with context and recommendations
- **Performance Monitoring**: CPU/memory monitoring with configurable thresholds

## Key Files & Directories

### Essential Reference Files
- `pyproject.toml` - Package configuration and dependencies
- `pytest.ini` - Test configuration and discovery patterns
- `config.yaml` - LiteLLM model routing configuration
- `ichs.toml` - Health monitoring and security configuration

### Framework Components
- `__csf.nip/src/` - Core framework implementation
- `__csf.nip/tests/` - Framework test suites
- `scripts/ai_tool_recommender.py` - AI-powered development assistance

### Documentation
- `*.md` files throughout workspace provide comprehensive implementation details
- `CLAUDE.md` files contain AI agent instructions for specific components
- Migration summaries document architectural changes and rationale

## Quality Assurance

### Validation Gates
- **Syntax & Style**: `ruff check --fix && mypy .`
- **Unit Tests**: `uv run pytest tests/ -v`
- **Integration Tests**: Full system integration validation
- **Security Scans**: Automated security and compliance checks

### Performance Standards
- **Caching**: TTL-based caching (24h default) for performance optimization

## Migration & Evolution Patterns

### Architectural Changes
- **AI Integration**: Progressive enhancement with AI tool integration
- **Testing Evolution**: From basic unit tests to comprehensive test coverage
- **Configuration Management**: Centralized config

### Backward Compatibility
- **Factory Functions**: Preserve interfaces during architectural migrations
- **Import Paths**: Maintain compatibility during refactoring
- **Configuration**: Support legacy configs alongside new structures
- **API Contracts**: Versioned APIs with deprecation notices

This workspace represents a sophisticated AI-first development environment with extensive tooling, comprehensive testing, and advanced architectural patterns. The Cognitive Steering Framework provides essential tools and workflows for developing other projects. Focus on understanding the TDD methodology and AI integration patterns when making changes.</content>
<parameter name="filePath">c:\_Python\_Projects\.github\copilot-instructions.md

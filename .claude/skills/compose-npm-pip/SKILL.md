---
name: compose-npm-pip
description: Generate production-ready, tested, validated code from natural language prompts.
version: 1.0.0
status: stable
category: development

# Complete Code Generation

## Purpose

Generate complete, production-ready code with comprehensive tests from natural language prompts. NOT a scaffold - a complete solution you can use immediately.

## Project Context

### Constitution/Constraints
- **Best Long-Term Solution First** - Generate working code, not templates
- **Evidence-First** - Validate generated code through execution
- **Complete Solutions** - No TODOs, no scaffolds

### Technical Context
- **Package Discovery**: Searches npm/PyPI for best packages
- **Code Generation**: Complete implementation with comprehensive tests
- **Execution Validation**: Runs npm install/pip install + compilation + tests automatically
- **Smart Retry**: Falls back to ranked package alternatives
- **Coverage**: Validates minimum 80% test pass rate

### Architecture Alignment
- Supports both npm and pip ecosystems
- Works with `//p-2025`, `/code-typescript-2025`

## Your Workflow

1. Parse natural language prompt for requirements
2. Identify appropriate ecosystem (npm or pip)
3. Discover and rank packages for the task
4. Generate complete implementation code
5. Generate comprehensive test suite
6. Create package.json/requirements.txt with exact versions
7. Create build configuration (tsconfig.json/pyproject.toml)
8. Execute installation and build
9. Run tests to validate
10. Report results with pass rate

## Validation Rules

### Output Artifacts

| Artifact | Description |
|----------|-------------|
| `main_code` | Complete, working implementation |
| `test_code` | Comprehensive test suite |
| `package.json` / `requirements.txt` | Exact dependency versions |
| `tsconfig.json` / `pyproject.toml` | Build configuration |
| `install_command` | Ready-to-run installation |

### Prohibited Actions

- Do NOT generate scaffolds or TODOs
- Do NOT skip test generation
- Do NOT skip execution validation
- Do NOT use packages without verification

NOT a scaffold - a complete solution you can use immediately.

## Quick Start

```bash
/compose-npm-pip Create a web scraper
/compose-npm-pip Build an Express API server
/compose-npm-pip Make a data pipeline with pandas
```

## What It Does

- **Automatic package discovery & selection** - Searches npm/PyPI for best packages
- **Full code generation** - Complete implementation with comprehensive tests
- **Execution validation** - Runs npm install + tsc + jest automatically
- **Smart retry strategy** - Falls back to ranked package alternatives
- **Test pass rate measurement** - Validates minimum 80% test coverage

## Example Usage

```
You:  /compose-npm-pip Create a web scraper

System: [Discovers packages] → [Generates code] → 
        [Runs npm install] → [Compiles TypeScript] → 
        [Runs 12 tests] → [All pass] → ✅ Done in 26s

Result: Copy-paste ready code, not scaffolds or TODOs
```

## Output

| Artifact | Description |
|----------|-------------|
| `main_code` | Complete, working implementation |
| `test_code` | Comprehensive test suite |
| `package.json` / `requirements.txt` | Exact dependency versions |
| `tsconfig.json` / `pyproject.toml` | Build configuration |
| `install_command` | Ready-to-run installation |

## Options

### Override Ecosystem

```bash
/compose-npm-pip Create an API --ecosystem npm
/compose-npm-pip Create an API --ecosystem pip
```

## Examples

| Prompt | Ecosystem | Packages Generated |
|--------|-----------|-------------------|
| "Create a FastAPI web scraper" | pip | fastapi, beautifulsoup4, httpx |
| "Build an Express API server" | npm | express, @types/express, typescript |
| "Make a data pipeline" | pip | pandas, numpy, pydantic |

## Memory Aid

When you can't remember the exact name, think "npm or pip" → `/compose-npm-pip`

---

ARGUMENTS: <user prompt> [--ecosystem npm|pip]

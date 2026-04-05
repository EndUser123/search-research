---
name: diffbro
description: AI-powered code review using diffbro (semantic diff analysis)
version: "1.0.0"
status: "stable"
category: quality
triggers:
  - /diffbro
aliases:
  - /diffbro

suggest:
  - /analyze
  - /comply
  - /llm-api
---

## Code Editing Patterns

For Python code editing patterns and anti-patterns:
- **Authority**: /p Neural Cache
- **Example**: `/search "ThreadPoolExecutor KeyboardInterrupt immediate cleanup"`
- **Example**: `/search "string manipulation AST LibCST code editing"`

Reflect automatically propagates code editing learnings to /p. Query CKS for patterns.


# Diffbro - AI Code Review

AI-powered code review using diffbro for semantic diff analysis and contextual code understanding.

## Purpose

AI-powered code review using diffbro for semantic diff analysis and contextual code understanding.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first analysis (reads actual code changes)
- Requires external tools (diffbro CLI, OpenAI API key)

### Technical Context
- Semantic diff understanding (not just syntax)
- Multiple intensity levels (chill, mid, chad)
- File filtering capabilities
- Commit message generation from diffs

### Architecture Alignment
- Integrates with /analyze and /comply workflows
- Supports CWO quality validation
- Complementary to /llm-api

## Your Workflow

1. Select intensity level based on change significance
2. Run diffbro on changed files
3. Review semantic analysis results
4. Use --summarize for commit message generation
5. Apply filters (--only, --ignore) for targeted review

## Validation Rules

- OpenAI API key must be set (OPENAI_API_KEY)
- diffbro CLI must be installed
- Use --chad mode for production code
- Use --chill mode for iterative development

## Quick Start

```bash
/diffbro              # Quick review (chill mode)
/diffbro --mid       # Balanced review (default)
/diffbro --chad      # Thorough staff-engineer review
/diffbro --summarize # Generate commit message from diff
```

## Features

- **Semantic Diff Understanding**: AI analysis of what changed and why
- **Contextual Code Review**: Understands code, not just syntax
- **Multiple Intensity Levels**: chill, mid, chad
- **File Filtering**: Include/exclude specific files
- **Commit Summary**: Generate commit messages

## Usage Examples

### Basic Code Review
```bash
/diffbro              # Quick review
/diffbro --chad       # Thorough review for production
```

### File Filtering
```bash
/diffbro --only .py   # Review only Python files
/diffbro --ignore .md # Skip documentation
```

### Custom Prompts
```bash
/diffbro --prompt "Focus on security issues only"
```

## Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `--chill` | Quick, casual review | Local development, iterative changes |
| `--mid` | Balanced review (default) | Most development work |
| `--chad` | Thorough review | Production code, critical changes |

## Requirements

### External Dependencies

- **diffbro CLI**: `pip install diffbro`
- **OpenAI API Key**: Set `OPENAI_API_KEY` environment variable

### Installation

```bash
pip install diffbro
export OPENAI_API_KEY=sk-...
```

## Configuration

```bash
export OPENAI_API_KEY=sk-...          # Required
export DIFFBRO_MODEL=gpt-4             # Optional: Model selection
export DIFFBRO_DEFAULT_MODE=mid         # Optional: Default mode
```

## Integration with CWO

Enable during CWO workflow:
```bash
/cwo --with-diffbro    # Adds diffbro to quality validation
```

## Complementary Tools

- `/comply` - Static analysis and standards validation
- `/analyze` - Unified analysis engine
- `/cwo` - Full workflow orchestration

## See Also

- [diffbro GitHub](https://github.com/disler/diffbro) - Upstream documentation

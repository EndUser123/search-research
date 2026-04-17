# CLI Usage Patterns

## Overview

The search-research migration split the monolithic `research_skill/cli.py` (5,957 lines) into two focused CLIs:

- **`search-research`** - Core search CLI (reusable across projects)
- **`research`** - Skill orchestration CLI (Claude Code-specific features)

---

## Core Search CLI (`search-research`)

**Purpose**: Multi-source search with 11+ providers, HyDE enhancement, and result synthesis.

**Installation**:
```bash
pip install -e P:/packages/search-research
```

### Basic Usage

```bash
# Simple search (auto mode)
search-research "python async/await"

# Specific provider
search-research "web scraping" --mode tavily

# JSON output
search-research "machine learning" --output json

# Save results
search-research "data science" --save results.json
search-research "AI trends" --save report.md

# Limit results
search-research "climate change" --max-cap 10
```

### Available Modes

**Multi-provider modes**:
- `auto` - Automatic provider selection
- `web` - Multi-provider web search (tavily + serper)
- `quick` - Fast single-provider search

**Direct provider modes**:
- `tavily` - Tavily API
- `serper` - Google-powered search
- `exa` - Exa AI search
- `perplexity` - Perplexity AI search
- `glm` - GLM/Zhipu AI search
- `zai` - ZAI web search
- `webreader` / `fetch` - Direct URL fetching
- `webreader_mcp` - Enhanced WebReader with MCP
- `github` - GitHub repository search
- `notebooklm` - NotebookLM MCP
- `claude` - Claude Code built-in web search

### HyDE Enhancement

```bash
# Enable HyDE (Hypothetical Document Embeddings)
search-research "quantum computing" --hyde

# HyDE retrieval mode
search-research "blockchain technology" --hyde-retrieval

# Multi-HyDE with perspectives
search-research "AI ethics" --multi-hyde --hyde-perspectives technical,ethical,societal
```

### Advanced Options

```bash
# Saturation detection
search-research "deep learning" --saturation-threshold 0.1 --min-results 10

# Timeout
search-research "complex query" --timeout 300

# Vision analysis
search-research "computer vision" --vision

# Depth modes
search-research "topic" --depth quick      # Fast
search-research "topic" --depth detailed    # Medium
search-research "topic" --depth comprehensive  # Thorough
```

### Output Formats

```bash
# Text (default)
search-research "query" --output text

# JSON
search-research "query" --output json

# Markdown
search-research "query" --output markdown

# JSON shorthand
search-research "query" --json
```

---

## Research Skill CLI (`research`)

**Purpose**: Extends core search with Claude Code-specific features (knowledge graphs, ML enhancement, persona memory).

**Installation**:
```bash
pip install -e P:/packages/research
```

### Core Search Modes

The `research` CLI inherits all core search modes from `search-research`:

```bash
# All core modes work
research "python async/await" --mode auto
research "web scraping" --mode tavily
research "machine learning" --output json
```

### Skill-Specific Modes

**Knowledge graph systems**:
```bash
# CKS (Constitutional Knowledge System)
research "software architecture" --mode cks

# CHS (Chat History System)
research "previous discussion" --mode chs

# Knowledge mode
research "research findings" --mode knowledge
```

**Persona Memory**:
```bash
research "my project requirements" --mode persona
```

**ML-Enhanced modes**:
```bash
# Hybrid Detection
research "complex topic" --mode ml_hybrid_detection

# GPU Accelerated
research "large dataset" --mode gpu_accelerated_research

# Intelligent Caching
research "frequently asked" --mode cached_intelligent_research

# Semantic Synthesis
research "interdisciplinary topic" --mode semantic_research_synthesis
```

### Query Expansion

```bash
# Enable query expansion (default)
research "distributed systems" --expand-queries

# Maximum query variants
research "microservices" --max-variants 10

# Entity-specific expansion
research "kubernetes" --entity devops
```

### Advanced Features

```bash
# Two-phase research with novelty saturation
research "emerging technology" --two-phase --budget 5.0 --max-iterations 10

# MMR (Maximal Marginal Relevance) reranking
research "topic" --enable-mmr --mmr-lambda 0.5

# Temporal boosting for recent sources
research "latest news" --temporal-boost --temporal-half-life 90
```

### Entity-Specific Research

```bash
# TaskMaster entity
research "workflow" --entity taskmaster

# Custom entity
research "documentation" --entity my-project
```

---

## Comparison Table

| Feature | `search-research` | `research` |
|---------|------------------|------------|
| Core search providers | ✅ 11 providers | ✅ 11 providers (inherited) |
| Knowledge graph modes | ❌ | ✅ cks, chs, knowledge |
| Persona memory | ❌ | ✅ persona |
| ML-enhanced modes | ❌ | ✅ 4 ML modes |
| Two-phase research | ❌ | ✅ |
| Query expansion | ❌ | ✅ (with CKS QueryExpander) |
| MMR reranking | ❌ | ✅ |
| Temporal boosting | ❌ | ✅ |
| Lines of code | 1,359 | 1,039 |
| Reusability | High (standalone) | Medium (extends core) |
| Dependencies | Minimal | Requires CKS/CHS ecosystem |

---

## Common Patterns

### Pattern 1: Quick Web Search

**Use**: `search-research` with auto mode

```bash
search-research "python async await tutorial"
```

### Pattern 2: Comprehensive Research

**Use**: `research` with two-phase mode

```bash
research "emerging AI technology 2026" --two-phase --budget 10.0 --max-iterations 5
```

### Pattern 3: GitHub Repository Search

**Use**: `search-research` with github mode

```bash
search-research "machine learning framework" --mode github --max-cap 20
```

### Pattern 4: Knowledge Graph Query

**Use**: `research` with CKS mode

```bash
research "previous architecture decisions" --mode cks
```

### Pattern 5: Direct URL Processing

**Use**: `search-research` with webreader mode

```bash
search-research "https://example.com/article" --mode webreader --vision
```

---

## Entry Points

After installation, both CLIs are available as commands:

```bash
# Core search CLI
search-research "query" [options]

# Research skill CLI
research "query" [options]
```

**Programmatic usage**:

```python
from search_research.cli import _main_sync
import sys

sys.argv = ['search-research', 'query', '--mode', 'auto']
_main_sync()
```

```python
from research_skill.cli import _main_sync
import sys

sys.argv = ['research', 'query', '--mode', 'cks']
_main_sync()
```

---

## Migration Notes

**Before**: Single monolithic CLI (`research_skill/cli.py` - 5,957 lines)

**After**: Split CLIs
- Core search (1,359 lines) - **82.6% reduction**
- Skill CLI (1,039 lines)
- Shared utilities (95 lines)

**Benefits**:
- ✅ Cleaner separation of concerns
- ✅ Core search is reusable across projects
- ✅ Easier to maintain and extend
- ✅ No circular dependencies
- ✅ All functionality preserved

**Compatibility**:
- All original CLI arguments preserved
- Backward compatible with existing scripts
- Both CLIs can coexist in same environment

# Chat History Search (CHS) - Complete Documentation

**Version**: 1.0
**Category**: Analysis (ANL)
**Module**: `src/modules/analysis/chat_search/`
**Command**: `chs`

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Command Reference](#command-reference)
5. [Usage Examples](#usage-examples)
6. [Integration Guide](#integration-guide)
7. [API Reference](#api-reference)
8. [Development Guide](#development-guide)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

## Overview

### What is CHS?

Chat History Search (CHS) is an advanced cross-session chat intelligence system that provides semantic search, pattern analysis, and trend discovery across your entire chat history. Built following CSF NIP principles, CHS transforms your chat conversations into a searchable, analyzable knowledge base.

### Key Features

- 🔍 **Semantic Search**: TF-IDF based relevance scoring with intelligent ranking
- 📅 **Time-based Filtering**: Search specific time periods with granular control
- 🎯 **Context-aware Results**: Understand project vs general chat contexts
- 📊 **Pattern Analysis**: Identify recurring themes and conversation patterns
- 🏆 **Smart Ranking**: Results ranked by relevance, recency, or frequency
- 🔗 **CSF Integration**: Seamless integration with TaskMaster, ValidationGate, and AXIOM
- 💾 **Efficient Indexing**: Fast inverted index for millisecond searches
- 📈 **Trend Analysis**: Track conversation themes over time

### Use Cases

- **Research**: Find previous solutions and discussions
- **Project Tracking**: Monitor progress and decision history
- **Knowledge Discovery**: Identify recurring patterns and insights
- **Problem Solving**: Find similar issues and their resolutions
- **Workflow Analysis**: Understand communication patterns and inefficiencies

---

## Architecture

### System Components

```
CHS Architecture
├── Chat History Parser      → Parses JSONL chat history
├── Index Builder           → Creates TF-IDF vocabulary and inverted index
├── Search Engine           → Semantic search with relevance scoring
├── Pattern Analyzer        → Identifies conversation patterns
├── Trend Analyzer          → Tracks changes over time
├── Integration Layer       → CSF component integration
└── CLI Interface           → Command-line interface
```

### Data Flow

```
Chat History (JSONL) → Parser → Index Builder → Search Engine → Results
                                    ↓
                              Pattern Analyzer → Insights
                                    ↓
                              CSF Integration → TaskMaster/AXIOM
```

### Storage Structure

```
.taskmaster/chat_search_index/
├── chat_index.json        → Main inverted index
├── vocabulary.json        → TF-IDF vocabulary data
├── metadata.json          → Index metadata and statistics
└── cache/                 → Search result caches
```

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- CSF NIP framework
- Access to Claude chat history file (`~/.claude/history.jsonl`)

### Quick Setup

1. **Verify Installation**:
   ```bash
   cd "C:/_Python/_Projects/__csf.nip"
   python -m src.modules.analysis.chat_search.src.chs status
   ```

2. **Index Chat History**:
   ```bash
   python -m src.modules.analysis.chat_search.src.chs index --rebuild
   ```

3. **Test Search**:
   ```bash
   python -m src.modules.analysis.chat_search.src.chs search "test query"
   ```

### Configuration

CHS automatically configures itself, but you can customize:

- **Index Location**: Controlled via `ChatHistorySearcher(index_dir=path)`
- **Chat History Path**: Controlled via `ChatHistorySearcher(chat_history_path=path)`
- **Logging**: Configure via standard Python logging

---

## Command Reference

### Main Commands

#### `chs search` - Search Chat History

Search your chat history with intelligent filtering and ranking.

```bash
chs search "QUERY" [OPTIONS]
```

**Arguments**:
- `query`: Search query (natural language)

**Options**:
- `--session-filter`: Filter by time period (`today`, `yesterday`, `week`, `month`, `all`)
- `--context-filter`: Filter by context (`project`, `general`, `technical`, `all`)
- `--rank-by`: Ranking method (`relevance`, `recency`, `frequency`)
- `--limit, -l`: Maximum number of results (default: 20)
- `--format, -f`: Output format (`text`, `json`, `markdown`)
- `--output, -o`: Output file (optional)

**Examples**:
```bash
# Basic search
chs search "archon search engines"

# Advanced filtering
chs search "docker errors" --session-filter week --context-filter technical

# Export results
chs search "authentication issues" --format markdown --output auth_research.md
```

#### `chs analyze` - Analyze Chat Patterns

Perform comprehensive analysis of chat patterns and trends.

```bash
chs analyze [OPTIONS]
```

**Options**:
- `--pattern-analysis`: Include pattern analysis
- `--trend-analysis`: Include trend analysis
- `--topic-modeling`: Include topic modeling
- `--output, -o`: Output file for analysis results

**Examples**:
```bash
# Full analysis
chs analyze --pattern-analysis --trend-analysis --topic-modeling

# Pattern analysis only
chs analyze --pattern-analysis

# Save analysis
chs analyze --output chat_analysis.json
```

#### `chs index` - Index Chat History

Build or rebuild the chat search index.

```bash
chs index [OPTIONS]
```

**Options**:
- `--rebuild`: Rebuild entire index from scratch

**Examples**:
```bash
# Initial index build
chs index

# Rebuild index
chs index --rebuild
```

#### `chs status` - Show System Status

Display comprehensive system status and health information.

```bash
chs status
```

**Output Includes**:
- Chat history availability and size
- Index status and statistics
- Vocabulary size and coverage
- System health checks
- Integration status

#### `chs export` - Export Data

Export search results or indexed data in various formats.

```bash
chs export [OPTIONS]
```

**Options**:
- `--format, -f`: Export format (`json`, `csv`, `markdown`)
- `--output, -o`: Output filename
- `--search-query`: Export specific search results

**Examples**:
```bash
# Export all data
chs export --format json --output full_export.json

# Export search results
chs export --search-query "python errors" --format markdown --output python_errors.md
```

---

## Usage Examples

### Research Scenarios

#### Finding Previous Solutions

```bash
# Search for previous Docker solutions
chs search "docker permission denied" --session-filter month --rank-by relevance

# Export findings for documentation
chs search "api authentication errors" --format markdown --output api_auth_solutions.md
```

#### Project Progress Tracking

```bash
# Analyze project-related discussions
chs search "project milestone" --context-filter project --session-filter week

# Track decision patterns
chs analyze --pattern-analysis --topic-modeling --output project_decisions.json
```

#### Technical Investigation

```bash
# Find error patterns
chs search "python traceback" --context-filter technical --rank-by frequency

# Analyze technical discussions
chs search "performance optimization" --session-filter month --format json --output perf_analysis.json
```

### Workflow Integration

#### Daily Standup Preparation

```bash
# Yesterday's technical discussions
chs search "bug fix" --session-filter yesterday --context-filter technical --limit 10

# Recent project decisions
chs search "decision" --session-filter week --context-filter project
```

#### Knowledge Base Creation

```bash
# Export all technical solutions
chs export --format json --output technical_knowledge.json

# Create topic-specific exports
chs search "database connection" --format markdown --output db_solutions.md
```

---

## Integration Guide

### TaskMaster Integration

CHS automatically integrates with TaskMaster to:

1. **Create Tasks from Findings**: Actionable items from search results
2. **Store Insights**: Pattern analysis results as task knowledge
3. **Workflow Enhancement**: Context-aware task recommendations

```python
# Example integration code
from src.modules.analysis.chat_search.src.chs import ChatHistoryCommand

chs = ChatHistoryCommand()
results = chs.searcher.search("urgent issues")

# TaskMaster integration happens automatically
# Creates tasks for actionable findings
```

### ValidationGate Integration

CHS uses ValidationGate for:

1. **Search Result Validation**: Quality checks on search results
2. **Index Health Monitoring**: Continuous index validation
3. **System Health Checks**: Overall system status validation

### AXIOM Integration

CHS integrates with AXIOM knowledge system to:

1. **Store Important Findings**: Key insights in knowledge base
2. **Learn from Patterns**: Pattern recognition improvements
3. **Build Conversational Memory**: Long-term context retention

### Custom Integration

```python
from src.modules.analysis.chat_search.src.chat_history_search import ChatHistorySearcher

# Initialize with custom paths
searcher = ChatHistorySearcher(
    chat_history_path=Path("custom/history.jsonl"),
    index_dir=Path("custom/index")
)

# Use in your applications
results = searcher.search("custom query", limit=50)
```

---

## API Reference

### Core Classes

#### `ChatHistorySearcher`

Main search engine class.

```python
class ChatHistorySearcher:
    def __init__(self, chat_history_path=None, index_dir=None)

    def search(self, query, session_filter="all", context_filter="all",
               rank_by="relevance", limit=20) -> List[Dict]

    def analyze_patterns(self, pattern_analysis=True, trend_analysis=True,
                        topic_modeling=True) -> Dict[str, Any]

    def index_chat_history(self, rebuild=False) -> bool

    def get_status(self) -> Dict[str, Any]

    def export_results(self, search_query=None, format="json",
                      output_file=None) -> bool
```

#### `ChatHistoryCommand`

CLI command interface.

```python
class ChatHistoryCommand:
    def handle_search(self, args) -> int
    def handle_analyze(self, args) -> int
    def handle_index(self, args) -> int
    def handle_status(self, args) -> int
    def handle_export(self, args) -> int
```

### Data Structures

#### Search Result

```python
{
    "id": "unique_entry_id",
    "display": "chat_message_content",
    "timestamp": 1234567890000,
    "project": "project_name_or_empty",
    "relevance_score": 21.08,
    "matched_tokens": ["matched", "keywords"]
}
```

#### Analysis Result

```python
{
    "timestamp": "2025-10-01T21:23:13.425191",
    "pattern_analysis": {
        "total_tokens": 15420,
        "unique_tokens": 1648,
        "top_keywords": [("python", 156), ("error", 89)]
    },
    "trend_analysis": {
        "daily_activity": {"2025-10-01": 45, "2025-09-30": 32},
        "most_active_day": ["2025-10-01", 45]
    },
    "topic_modeling": {
        "python": [("code", 23), ("script", 19)],
        "docker": [("container", 15), ("image", 12)]
    }
}
```

---

## Development Guide

### Project Structure

```
src/modules/analysis/chat_search/
├── chs_inst.md                    # Instruction file for Claude
├── src/
│   ├── chat_history_search.py    # Core search engine
│   └── chs.py                    # CLI command interface
├── docs/
│   └── CHS_DOCUMENTATION.md      # This documentation
├── tests/                        # Test suite (to be created)
└── README.md                     # Module overview
```

### Adding New Features

1. **Core Functionality**: Modify `ChatHistorySearcher`
2. **CLI Commands**: Update `chs.py` parser and handlers
3. **Documentation**: Update this file and instruction files
4. **Tests**: Create comprehensive test coverage

### Testing

```bash
# Run basic functionality test
python -m src.modules.analysis.chat_search.src.chs status

# Test search functionality
python -m src.modules.analysis.chat_search.src.chs search "test"

# Test analysis functionality
python -m src.modules.analysis.chat_search.src.chs analyze --pattern-analysis
```

### Code Standards

- Follow CSF NIP coding standards
- Use type hints consistently
- Include comprehensive docstrings
- Handle errors gracefully
- Log important operations

---

## Troubleshooting

### Common Issues

#### Index Not Found

**Problem**: `Index status: not_built`

**Solution**:
```bash
chs index --rebuild
```

#### No Search Results

**Problem**: Search returns 0 results

**Solutions**:
1. Check query spelling
2. Try broader terms
3. Remove filters: `--session-filter all --context-filter all`
4. Rebuild index: `chs index --rebuild`

#### Performance Issues

**Problem**: Slow search performance

**Solutions**:
1. Check index size with `chs status`
2. Rebuild index: `chs index --rebuild`
3. Use limits: `--limit 10`

#### Integration Errors

**Problem**: TaskMaster/ValidationGate integration fails

**Solutions**:
1. Check CSF NIP installation
2. Verify module imports
3. Check system status: `chs status`

### Debug Mode

Enable verbose logging:
```bash
chs --verbose search "query"
```

### Log Files

Check logs in:
- Console output (for immediate debugging)
- CSF NIP logging system
- Python logging output

---

## Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** feature branch
3. **Implement** changes with tests
4. **Update** documentation
5. **Test** thoroughly
6. **Submit** pull request

### Code Review Requirements

- **90%+ test coverage** required
- **Documentation updates** mandatory
- **Integration tests** for new features
- **Performance impact** assessment

### Submitting Issues

Include:
- **Environment**: OS, Python version, CSF NIP version
- **Reproduction steps**: Clear, reproducible example
- **Expected vs actual**: What should happen vs what does
- **Logs**: Any error messages or debug output

---

## Related Documentation

- [CSF NIP README](../../../README.md) - Project overview
- [Commands System Guide](../../commands/README.md) - Command architecture
- [Integration Guide](../../../docs/INTEGRATION_GUIDE.md) - CSF integration patterns
- [Testing Standards](../../../docs/TESTING_STANDARDS.md) - Testing requirements
- [Chat Analyzer (CAI)](../chat_analyzer/) - Related analysis module

---

**License**: CSF NIP License
**Maintainers**: CSF NIP Development Team
**Last Updated**: 2025-10-01

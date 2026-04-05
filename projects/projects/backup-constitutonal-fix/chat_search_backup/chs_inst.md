---
name: "Chat History Search Instructions"
category: "Analysis"
purpose: "Advanced cross-session chat history search with intelligent filtering and ranking"
entry_point: "primary"
triggers: ['chat search', 'search history', 'chs', 'find in chat', 'chat memory', 'search sessions']
integrates_with: ["/tsk", "/validate", "/health"]
---

# CHS - Chat History Search Instructions

## Command Pattern
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search [COMMAND] [OPTIONS]
```

## Quick Start

**System Status:**
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search status
```

**Basic Search:**
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "your query"
```

**RAG-Enhanced Search (NEW):**
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "python error handling" --enable-rag --search-mode rag
```

**Advanced Search:**
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker permission denied" --session-filter week --context-filter technical --search-mode hybrid
```

## Essential Commands

### Search Chat History
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "QUERY" [OPTIONS]
```
**Key Options:**
- `--session-filter FILTER` - Filter by timeframe (today, yesterday, week, month, all)
- `--context-filter FILTER` - Filter by context (project, general, technical)
- `--rank-by METHOD` - Ranking method (relevance, recency, frequency)
- `--limit N` - Maximum results (default: 20)
- `--format FORMAT` - Output format (text, json, markdown)
- `--search-mode MODE` - Search mode: traditional, rag, hybrid (NEW)
- `--enable-rag` - Enable RAG functionality (NEW)
- `--use-rag` - Alias for --enable-rag (NEW)

**Smart Indexing Options (NEW):**
- `--refresh` - Force refresh index before searching (immediate update)
- `--auto-refresh` - Auto-refresh if index is older than threshold
- `--threshold THRESHOLD` - Time threshold for auto-refresh (default: 1h)

**Time Threshold Formats:**
- `1h` - 1 hour
- `30m` - 30 minutes
- `2d` - 2 days
- `1w` - 1 week

### Analyze Chat Patterns
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze [OPTIONS]
```
**Analysis Types**: `--pattern-analysis`, `--trend-analysis`, `--topic-modeling`, `--output FILE`

### Index Management
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search index [OPTIONS]
```
**Operations**: `--rebuild` (2-5 min), `--optimize` (1-2 min), `--incremental` (10-30 sec, default), `--force-rag-index` (force RAG reindexing, NEW)

### RAG-Specific Operations
```bash
# Enable RAG indexing (first-time setup)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search index --enable-rag

# Force RAG reindexing (after major changes)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search index --force-rag-index
```

### Export Results
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export [OPTIONS]
```
**Export Options**: `--search-query QUERY`, `--format FORMAT` (json, csv, markdown, html), `--output FILE`, `--all`

### Session Duration Monitoring (NEW)
```bash
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.session_duration_monitor [COMMAND]
```
**Commands**: `status` (current metrics), `impact` (productivity analysis), `recommendations` (optimization suggestions)

## Integrations & Use Cases

**Core Integrations**: TaskMaster (task knowledge), Validation System (standards research), Health Monitoring (performance patterns)

**Common Examples**:
```bash
# Traditional Search (Find Previous Solutions)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker permission denied" --session-filter week

# RAG-Enhanced Search (Semantic Understanding)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "python error handling" --enable-rag --search-mode rag

# Hybrid Search (Best of Both Worlds)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "machine learning optimization" --search-mode hybrid --rank-by relevance

# Project Progress Analysis
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --trend-analysis --session-filter month

# Research & Export with RAG
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "authentication patterns" --enable-rag --rank-by relevance --limit 15
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "best practices" --format markdown --output practices.md --enable-rag

# Smart Indexing Examples (NEW)
# Force refresh before search
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker issues" --refresh

# Auto-refresh if index is older than 2 hours
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "api errors" --auto-refresh --threshold 2h

# Auto-refresh with custom threshold (30 minutes)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "recent work" --auto-refresh --threshold 30m

# Session Duration Monitoring (NEW)
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.session_duration_monitor status
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.session_duration_monitor impact
cd "P:/__csf.nip" && python -m src.modules.analysis.chat_search.src.session_duration_monitor recommendations
```

## Resources

**Command Help**: `chs_help.md` (detailed options & troubleshooting)
**Use Cases**: `chs_use_cases.md` (when to use & workflow integration)
**Examples**: `chs_examples.md` (comprehensive examples & scripts)

**Quick Reference**: Use `--help` flag for command-line help

# claude-history

Fast keyword search for Claude Code chat history using SQLite FTS5.

## Overview

`claude-history` is a Rust-based command-line tool for searching Claude Code conversation history. It provides:

- **Fast keyword search** over ~2.7GB of chat history using SQLite FTS5
- **JSONL streaming mode** for recent messages not yet indexed
- **MCP server mode** for tool integration
- **Multi-terminal safety** with WAL mode for concurrent reads

## Domain Split

| System         | Domain          | Technology      | Purpose                              |
|----------------|-----------------|-----------------|--------------------------------------|
| **claude-history** | Chat history    | Rust + SQLite FTS5 | Search archived conversations        |
| **semantic_daemon** | CKS knowledge   | Python + FAISS  | Search memories/patterns/lessons     |

## Installation

```bash
cd P:/packages/claude-history
cargo build --release
```

This creates `target/release/claude-history.exe`.

## Usage

### CLI Commands

#### Search chat history

```bash
# Search recent messages (JSONL streaming)
claude-history search "async patterns" --source jsonl --limit 10

# Search indexed database (SQLite FTS5)
claude-history search "async patterns" --source db --limit 10

# Filter by project
claude-history search "hooks" --project "P:/packages/search-research" --limit 5

# JSON output
claude-history search "test" --format json
```

#### List recent sessions

```bash
claude-history list --limit 20
claude-history list --project "P:/" --sort recent
```

#### Get session details

```bash
claude-history get 00e77db9-182c-462c-85d7-aeb2f16e161d
claude-history get 00e77db9-182c-462c-85d7-aeb2f16e161d --format json
```

#### Statistics

```bash
claude-history stats
```

Output:
```
Claude History Statistics:

Total Sessions: 5814
Total Messages: 9056
Indexed Messages: 0
Projects: C:/Users/brsth/.claude, P:/, ...

Data Sources:
  JSONL: C:/Users/brsth/.claude/history.jsonl
  Database: P:/__csf/data/chat_history.db
```

### MCP Server Mode

Start the MCP server for tool integration:

```bash
claude-history --mcp-server
```

The server exposes the following tools:

- `search_sessions`: Search chat history
- `get_session`: Get full session details
- `list_projects`: List all projects
- `stats`: Get database statistics

## Architecture

### Data Sources

1. **JSONL file** (`C:/Users/brsth/.claude/history.jsonl`):
   - Primary data source
   - Streaming read, no full load
   - ~2.7GB, ~9k messages

2. **SQLite database** (`P:/__csf/data/chat_history.db`):
   - FTS5 full-text index
   - Fast BM25 ranking
   - WAL mode for concurrent reads

### Entry Types

The JSONL file contains various entry types:

- `assistant`: Assistant messages
- `user`: User messages
- `system`: System messages
- `summary`: Session summaries
- `custom-title`: Custom session titles
- `file-history-snapshot`: File backup snapshots
- `queue-operation`: Queue operations

## Integration with search-research

The Python backend wrapper is at:
`P:/packages/search-research/core/backends/local/claude_history_backend.py`

This backend invokes the CLI directly:

```python
result = subprocess.run(
    ["claude-history", "search", query, "--source", "jsonl", "--format", "json"],
    capture_output=True
)
return json.loads(result.stdout)
```

### Usage in /search and /all skills

The claude-history backend is automatically integrated with the search-research package:

- **Backend name**: `claude-history` (appears as `CLAUDE-HISTORY` in results)
- **Score**: 0.9 (competitive with CKS for chat history queries)
- **Data source**: JSONL streaming mode (default) for fast access to recent messages
- **Result format**: Standardized with `title`, `content`, `score`, and `metadata` fields

Example query patterns that trigger chat history search:
- "what did we discuss about X"
- "you mentioned something about Y"
- "our conversation about Z"

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and bug fixes.

## Development

### Build

```bash
cargo build --release
```

### Test

```bash
cargo test
```

### Run

```bash
./target/release/claude-history.exe search "test" --limit 5
```

## License

MIT

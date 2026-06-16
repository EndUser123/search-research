# MCP Server - Search Research

## Overview

MCP (Model Context Protocol) server for unified search across local codebase and web sources.

**Tools Available:**
- `unified_search` - Intelligent local + web search with quality-based routing
- `local_search` - Fast local-only search (<1s)
- `web_search` - Web-only search (5-10s)

## Installation

### 1. Install Dependencies

```bash
cd P://packages/.claude-marketplace/plugins/search-research
uv pip install mcp fastmcp pydantic
```

### 2. Register MCP Server

Add to `C:\Users\brsth\.claude.json` (for Claude Code CLI):

```json
{
  "mcpServers": {
    "search-research": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "P://packages/.claude-marketplace/plugins/search-research",
        "run",
        "python",
        "-m",
        "search_research.mcp_server"
      ],
      "env": {}
    }
  }
}
```

**Note**: For Claude Desktop GUI, use `%APPDATA%\Claude\claude_desktop_config.json` instead.

### 3. Restart Claude Code

Restart Claude Code for the server to be loaded.

## Usage

Once registered, Claude Code can automatically use these tools:

```
User: "Find where the FooBar class is used"
Claude: [automatically uses mcp__search_research__local_search]

User: "What are the best practices for FastAPI async?"
Claude: [automatically uses mcp__search_research__unified_search]

User: "Current documentation for Pydantic v2"
Claude: [automatically uses mcp__search_research__web_search]
```

## Tool Details

### unified_search

**Best for**: General research when you want comprehensive results

**Modes**:
- `auto` (default) - Quality checks determine if web search needed
- `local-only` - Fast local search, no web APIs
- `web-fallback` - Check quality, use web if needed
- `unified` - Always search both, merge with RRF

**Example Results**:
```markdown
## Search Results: "FastAPI async patterns"

**Mode**: auto | **Duration**: 2.34s | **Results**: 15

### 1. FastAPI Async Patterns
**Source**: LOCAL | **Score**: 0.95
**Preview**: Demonstrates async/await patterns with dependencies...
```

### local_search

**Best for**: Quick codebase searches, finding implementations

**Speed**: <1 second

**Sources**:
- Code files (Grep-based)
- Chat history (CKS)
- Documentation
- Skills and hooks

### web_search

**Best for**: Current documentation, best practices, external research

**Speed**: 5-10 seconds

**Providers**: Tavily, Serper, Exa, and more

## Development

### Testing the Server

```bash
# Run server directly
cd P://packages/.claude-marketplace/plugins/search-research
uv run python -m search_research.mcp_server

# Test with MCP inspector
npx @modelcontextprotocol/inspector uv run python -m search_research.mcp_server
```

### Adding New Tools

1. Define tool function in `mcp_server.py`
2. Use `@mcp.tool()` decorator with description
3. Return formatted markdown results

Example:
```python
@mcp.tool(description="Search GitHub repositories")
async def github_search(query: str) -> str:
    # Implementation
    return formatted_results
```

## Architecture

```
search-research MCP Server
    ├── mcp_server.py          # Main server with FastMCP
    ├── src/search_research/
    │   └── core/unified_router.py  # Async search router
    └── tests/
        └── test_mcp_server.py     # Server tests
```

**Key Components**:
- `FastMCP` - MCP server framework
- `UnifiedAsyncRouter` - Search orchestration
- Quality-based routing - Progressive enhancement

## Troubleshooting

### Server Not Starting

**Check**: Dependencies installed
```bash
uv pip install mcp fastmcp pydantic
```

**Check**: Python path in MCP config
```bash
# Test command works
uv --directory P://packages/.claude-marketplace/plugins/search-research run python -m search_research.mcp_server
```

### Tools Not Available

**Check**: Claude Desktop config location
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Check**: Server running
```bash
# Look for errors in Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%\Claude\logs\
```

### Search Returns No Results

**Check**: Local backends configured
- Grep available
- CKS database exists
- Skills directory accessible

**Check**: API keys for web search
```bash
# Check .env files
cat P://.env
cat P://__csf/.env
```

## Performance

| Operation | Speed | Use Case |
|-----------|-------|----------|
| `local_search` | <1s | Quick lookups |
| `unified_search` (auto) | 1-10s | Adaptive |
| `unified_search` (local-only) | <1s | Fast local |
| `unified_search` (unified) | 5-11s | Comprehensive |
| `web_search` | 5-10s | External research |

## Related Documentation

- `README.md` - Package overview
- `CLAUDE.md` - Development guide
- `/all` skill - User-facing unified search

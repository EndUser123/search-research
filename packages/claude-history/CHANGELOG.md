# Changelog

All notable changes to the claude-history Rust package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-03-19

### Added
- **FTS5 snippet extraction**: Search results now include 30-character context snippets with `<b>` tags highlighting matched terms
- **Public API**: `parse_timestamp()` is now public for external testing
- **MCP resources/list handler**: Added `resources/list` endpoint returning chat sessions and statistics resources
- **Test suite**: 4 new tests covering FTS5 snippets, BM25 ranking, timestamp parsing, and WAL mode
- **Module exports**: `src/lib.rs` for testing and external integration

### Changed
- **Signal handling**: MCP server now handles SIGINT/SIGTERM for graceful shutdown on Unix systems
- **Error handling**: Fixed double unwrap in ToolResult processing to prevent panics

### Dependencies
- Added `tempfile = "3.14"` as dev-dependency for WAL mode testing

## [1.0.1] - 2026-03-19

### Fixed
- **Character boundary panic in snippet generation** - Fixed Rust panic when byte index 200 fell in the middle of a multi-byte UTF-8 character (e.g., box-drawing characters like `─`). Changed from byte slicing to character-based slicing using `.chars().take(200).collect::<String>()`.
  - Location: `src/ingest.rs:308`
  - Impact: Search with `--limit > 10` now works correctly for all content types
  - Issue: `subprocess.CalledProcessError: Command returned non-zero exit status 101` with panic message "byte index 200 is not a char boundary"

### Added
- Integration with search-research package for `/search` and `/all` skills
- Python backend wrapper: `P:/packages/search-research/core/backends/local/claude_history_backend.py`
- Automatic backend registration in AsyncSearchRouter

## [1.0.0] - 2026-03-18

### Added
- Initial release of claude-history Rust package
- Fast keyword search over Claude Code chat history using SQLite FTS5
- JSONL streaming mode for recent messages
- MCP server mode for tool integration
- Multi-terminal safety with WAL mode
- CLI commands: `search`, `list`, `get`, `stats`

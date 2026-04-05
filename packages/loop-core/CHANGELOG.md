# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-14

### Changed
- **BREAKING**: Converted from Python library to Claude Code plugin
- Package structure: `loop_core/` → `core/`
- Import path: `from loop_core import ...` → `from core import ...`
- Removed `pyproject.toml` (plugins don't use pip packaging)
- Added `.claude-plugin/plugin.json` for plugin metadata
- Updated all documentation to reflect plugin deployment model

### Migration Notes
- Update imports: `from loop_core import X` → `from core import X`
- No pip install required - plugins are auto-discovered by Claude Code
- Backup of original structure available in `.backup/`

## [0.1.0] - 2026-03-14

### Added
- TerminalStateManager class for terminal-local state management
- Plan parser for extracting tasks from markdown files
- Terminal detection with 5-priority fallback system
- Atomic write operations (temp file + rename pattern)
- PID-based lock management with stale lock cleanup
- Multi-terminal isolation support
- Comprehensive test suite (45 tests, 79% coverage)
- Documentation (README, ARCHITECTURE, USAGE_EXAMPLES)
- Demo script for quick start

### Features
- **Multi-terminal safe**: Each terminal gets its own state directory
- **Crash-safe state**: Atomic writes prevent corrupted state
- **Automatic lock cleanup**: Stale PIDs detected and cleaned up
- **Zero configuration**: Auto-detects terminal ID
- **File-based persistence**: No database or Git dependency
- **Plan parsing**: Extract tasks from markdown with metadata

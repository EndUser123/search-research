# Changelog

All notable changes to the ai-chutes skill will be documented in this file.

## [1.1.0] - 2026-03-18

### Added
- **CLI list command** - Dynamic model discovery with 24-hour caching
  - Models fetched from Chutes `/models` endpoint via OpenAI SDK
  - Local cache at `~/.claude/cache/ai-chutes/models.json`
  - Categorized display (Large Context, Code Generation, Reasoning, Other)
  - `--refresh` flag to force cache update
  - `--verbose` flag for detailed model information
  - Cache status indicator showing age and freshness

### Changed
- Updated CLI help text with list command examples

### Fixed
- Added pragma comment to resolve detect-secrets hook false positive

## [1.0.0] - Initial Release

### Added
- Health check CLI with API key validation and connectivity testing
- Optional inference sanity check
- Quota checking via Chutes API
- Python and TypeScript SDK examples for litellm and OpenAI SDK
- Model selection strategies and fallback patterns

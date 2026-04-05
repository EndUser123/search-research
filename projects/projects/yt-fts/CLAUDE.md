# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/code) when working with this repository.

## Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | User guide, installation, features |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flows, decisions |
| [PRD.md](PRD.md) | Product requirements, roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [P:/.claude/skills/tdd/SKILL.md](P:/.claude/skills/tdd/SKILL.md) | TDD workflow |

## Scoping Rules (Critical)

**Session Context is Terminal Context:**
- This terminal's conversation history = the work context for this session
- "Review recent work" = what was discussed/changed IN THIS TERMINAL, not git history
- Do NOT conflate with other projects (CSF NIP, ralph-wiggum, etc.) even if they share a parent directory
- If scope is ambiguous, ASK: "Do you mean git commits, this session's changes, or something else?"

**Project Boundary:**
- IN scope: `projects/yt-fts/` files, commits, issues
- OUT of scope: `__csf.nip/`, `ralph-wiggum-python/`, `.claude/` (those are separate projects)
- When user says "yt-fts", they mean THIS project only

**Before Expanding Scope:**
1. Confirm the user wants broader scope
2. Explain why you're expanding (e.g., "Found related file in __csf.nip, include it?")
3. Get explicit approval

## Key Architecture Points for Claude

- **3-tier download**: RSS → yt-api → yt-dlp (quota optimization)
- **Dual-sink logging**: JSON file logs + clean console output
- **Database**: SQLite with FTS5, schema in ARCHITECTURE.md
- **Continue-on-error**: Batch processing doesn't stop on single failures

## When Making Changes

1. **Read ARCHITECTURE.md first** - understand the data flow
2. **Check PRD.md** - is there a requirement for this?
3. **Use TDD** - Write tests BEFORE changing code
   - For NEW features: Write test for desired behavior, then implement
   - For REFACTORING: Write test capturing current behavior, then restructure
4. **Update CHANGELOG.md** - document the change
5. **Run tests**: `pytest`

### Critical: TDD is Mandatory

Before changing any code (new or existing):
1. **WRITE TESTS FIRST** - Define expected behavior
2. Change code (implement or refactor)
3. **VERIFY** - Run tests to ensure they pass

**See:** `P:/.claude/skills/tdd/SKILL.md` for the complete TDD workflow.

## File Locations

- CLI: `src/yt_fts/core/cli.py`
- Downloads: `src/yt_fts/download/`
- Database: `src/yt_fts/core/database.py`
- Search: `src/yt_fts/core/search.py`
- Tests: `tests/`
- Logs: `logs/` (dev) or `~/.config/yt-fts/logs/` (prod)

# CWO12: Jules Pattern Integration Specification

## Overview

This specification documents the integration of three high-priority patterns from the Jules yt-fts codebase into the existing yt-fts project.

**Status**: Step 1 - Input Validation & Quality via /specify
**Version**: 1.0.0
**Date**: 2026-01-03

**Target Project**: `P:/projects/yt-fts/src/yt_fts`
**Source Reference**: `C:/Users/brsth/Downloads/jules_session_17326749298833802222/projects/yt-fts/src/yt_fts`

---

## Pattern 1: Enhanced Diagnostic Framework

### Source Analysis

**Source File**: `diagnostics/checker.py`

The Jules version provides a clean diagnostic framework with:
- Enum-based status levels (PASS, WARN, FAIL, INFO)
- Structured `DiagnosticResult` dataclass
- Auto-fix capabilities via optional callable
- Icon-based display formatting

### Current State Assessment

The target project at `P:/projects/yt-fts/src/yt_fts/diagnostics/` already has:
- A `DiagnosticChecker` base class with similar functionality
- Multiple checker implementations (DatabaseChecker, NetworkChecker, CookieChecker, YtdlpChecker)
- CLI integration via `diagnostics/cli.py`
- Status enum and DiagnosticResult dataclass

**Key Finding**: The core framework is already implemented and matches the Jules pattern.

### Requirements

#### 1.1 Enhance Auto-Fix Capabilities

**Current Gap**: The `try_fix()` method exists but has a bare except that silently fails.

**Requirements**:
- Implement proper error logging in `try_fix()` method
- Add a return type indicating which fixes were attempted and their results
- Implement at least one concrete auto-fix example

**Acceptance Criteria**:
- [ ] `try_fix()` returns a dict mapping result IDs to fix outcomes
- [ ] Failed fix attempts are logged (not silently ignored)
- [ ] At least one checker implements a working `auto_fix` callable

#### 1.2 Add Diagnostic History Tracking

**Requirements**:
- Track diagnostic results over time
- Enable trend analysis (e.g., database growth, latency changes)

**Acceptance Criteria**:
- [ ] Results can be serialized to JSON
- [ ] Optional diagnostic history file support
- [ ] `--history` flag in CLI to show past results

### Integration Approach

**File**: `P:/projects/yt-fts/src/yt_fts/diagnostics/checker.py`

**Changes**:
1. Enhance `try_fix()` to return structured results
2. Add serialization methods to `DiagnosticResult`
3. Add import/export for diagnostic history

**Minimal changes required** - the pattern is already present.

---

## Pattern 2: Transcription Engine Abstraction

### Source Analysis

**Source Files**:
- `common/transcribe.py` - Abstract base class
- `common/schema.py` - Data models (Video, Transcript, TranscriptChunk)

The Jules version provides:
- `TranscriptionEngine` ABC with `transcribe()` method
- Clean separation of concerns for different transcription backends
- Structured data models for transcripts
- Support for multiple sources (official, generated_whisper, generated_visual)

### Current State Assessment

**Finding**: NO transcription engine abstraction exists in the target project.

**Current State**:
- Subtitles are downloaded via yt-dlp (official YouTube captions only)
- No support for Whisper/local transcription
- Transcripts are stored directly in FTS5 format, not as structured objects

### Requirements

#### 2.1 Create Transcription Engine Interface

**File**: `P:/projects/yt-fts/src/yt_fts/transcribe/__init__.py` (NEW)

**Requirements**:
- Abstract `TranscriptionEngine` base class
- `LocalWhisperEngine` implementation using faster-whisper
- `OfficialCaptionEngine` wrapper for existing yt-dlp functionality

**Acceptance Criteria**:
- [ ] `TranscriptionEngine` ABC defined with `transcribe()` method
- [ ] Type hints using `Transcript`, `TranscriptChunk` from schema
- [ ] Language detection support parameter
- [ ] Translation support parameter (translate to English)

#### 2.2 Create Transcript Data Models

**File**: `P:/projects/yt-fts/src/yt_fts/transcribe/schema.py` (NEW)

**Requirements**:
- Dataclass for `Video` metadata
- Dataclass for `TranscriptChunk` (text, start_time, duration)
- Dataclass for `Transcript` (video_id, language, chunks, source_type)

**Acceptance Criteria**:
- [ ] All dataclasses use pydantic or dataclasses with proper type hints
- [ ] `source_type` enum: "official", "generated_whisper", "generated_visual"
- [ ] Serialization to/from dict support

#### 2.3 LocalWhisperEngine Implementation

**File**: `P:/projects/yt-fts/src/yt_fts/transcribe/whisper_engine.py` (NEW)

**Requirements**:
- Use `faster-whisper` for efficient transcription
- Support model size selection (tiny, base, small, medium, large)
- Handle audio file preparation (using yt-dlp download)
- Return structured `Transcript` objects

**Acceptance Criteria**:
- [ ] Transcribes audio files to `Transcript` objects
- [ ] Configurable model size via environment variable or parameter
- [ ] Progress reporting during transcription
- [ ] Handles language auto-detection
- [ ] Converts word-level timestamps to chunk-based format

#### 2.4 Database Schema Updates

**File**: `P:/projects/yt-fts/src/yt_fts/core/database.py` (MODIFY)

**Requirements**:
- Add `source_type` column to Subtitles table
- Add migration for existing data (default to "official")

**Acceptance Criteria**:
- [ ] Migration function adds `source_type` column
- [ ] Existing rows default to "official"
- [ ] Index on `(video_id, source_type)` for efficient queries

#### 2.5 CLI Integration

**File**: `P:/projects/yt-fts/src/yt_fts/core/cli.py` (MODIFY)

**Requirements**:
- New command: `yt-fts transcribe <video_url>`
- Options for model selection, language, translation
- Progress bar using Rich

**Acceptance Criteria**:
- [ ] Downloads audio if not present
- [ ] Runs transcription with selected engine
- [ ] Stores results in database with correct source_type
- [ ] Shows progress and statistics

### Dependencies

Add to `pyproject.toml` dependencies (optional dependency group):

```toml
[project.optional-dependencies]
transcribe = [
    "faster-whisper>=1.0.0",
    "torch>=2.0.0",
]
```

### Integration Approach

1. Create new `transcribe/` package
2. Define base abstractions and models
3. Implement Whisper engine
4. Add database migration
5. Wire up CLI command
6. Add tests for transcription pipeline

---

## Pattern 3: Schema Migration Pattern

### Source Analysis

**Source File**: `migrations/v2_schema.py`

The Jules version provides:
- Clean, single-purpose migration functions
- `sqlite-utils` for safe schema changes
- Idempotent operations (try/except for existing columns)
- Clear print statements for migration progress

### Current State Assessment

The target project has a **more comprehensive** migration system at:
- `P:/projects/yt-fts/src/yt_fts/utils/migrations.py`
- `P:/projects/yt-fts/src/yt_fts/core/database.py` (contains `run_migrations()`)

**Current Features** (SUPERIOR to Jules):
- Multiple named migrations (multi_language, api_total_tracking)
- Migration status checking via `check_migration_status()`
- Automatic migration application via `ensure_migrations()`
- Idempotent operations with proper error handling

### Requirements

#### 3.1 Standardize Migration Pattern

**Current state already matches requirements.**

The existing pattern follows best practices:
- Each migration is a named function
- Uses sqlite-utils `add_column()` with defaults
- Idempotent via try/except for duplicate columns
- Status checking before running migrations
- Clear console output with checkmarks

**Acceptance Criteria**: Already met.

#### 3.2 Document Migration Guidelines

**File**: `P:/projects/yt-fts/docs/migrations.md` (NEW)

**Requirements**:
- Document the migration pattern used in this project
- Provide template for new migrations
- List all applied migrations with version numbers

**Acceptance Criteria**:
- [ ] Migration template documented
- [ ] All existing migrations catalogued with dates
- [ ] Instructions for adding new migrations

#### 3.3 Add Migration Version Tracking

**Requirements**:
- Track which migrations have been applied in the database
- Add a `_migrations` table to store applied migration names and timestamps

**Acceptance Criteria**:
- [ ] `_migrations` table created on first run
- [ ] Each migration records its name and timestamp
- [ ] `ensure_migrations()` checks this table before running

### Integration Approach

**Minimal changes required** - the pattern is already implemented and is more comprehensive than the Jules version.

Add only:
1. Migration documentation
2. Optional: Version tracking table for better state management

---

## Python 2025 Standards Compliance

All new code MUST follow Python 2025 standards:

### Type Hints
- All functions MUST have complete type hints
- Use `X | None` instead of `Optional[X]`
- Use `list[X]` instead of `List[X]`
- Strict mode compatibility

### Code Style
- Ruff for linting and formatting
- Classes must not exceed 300 lines
- Functions must not exceed 50 lines
- No bare `except` clauses

### Dependencies
- Use `uv` for packaging (for new dependencies)
- Prefer type-safe libraries (pydantic for data models)

---

## Testing Strategy

### Unit Tests Required

| Pattern | Test Coverage Target | Key Test Cases |
|---------|---------------------|----------------|
| Diagnostics | 90%+ | Status enum, auto-fix, serialization |
| Transcription | 85%+ | Engine interface, Whisper mock, CLI |
| Migrations | 95%+ | Idempotency, rollback, status checks |

### Integration Tests Required

- Full transcription pipeline (download -> transcribe -> store)
- Migration from fresh database
- Auto-fix execution and verification

---

## Risk Assessment

| Pattern | Risk Level | Mitigation |
|---------|------------|------------|
| Diagnostics | Low | Minimal changes, enhance existing |
| Transcription | Medium | New dependency (faster-whisper), optional feature |
| Migrations | Very Low | Already implemented, documentation only |

---

## File Location Summary

### New Files to Create

```
P:/projects/yt-fts/src/yt_fts/transcribe/
├── __init__.py           # Package exports
├── base.py               # TranscriptionEngine ABC
├── schema.py             # Transcript data models
├── whisper_engine.py     # LocalWhisperEngine implementation
└── official_engine.py    # OfficialCaptionEngine wrapper

P:/projects/yt-fts/docs/
└── migrations.md         # Migration documentation
```

### Files to Modify

```
P:/projects/yt-fts/src/yt_fts/diagnostics/checker.py    # Enhance auto-fix
P:/projects/yt-fts/src/yt_fts/diagnostics/__init__.py   # Add exports
P:/projects/yt-fts/src/yt_fts/core/database.py          # Add source_type column
P:/projects/yt-fts/src/yt_fts/core/cli.py              # Add transcribe command
P:/projects/yt-fts/pyproject.toml                      # Add optional dependencies
```

---

## Implementation Priority

1. **Phase 1** - Transcription Engine Abstraction (High Value, New Feature)
   - Create base abstractions
   - Implement Whisper engine
   - Database schema update
   - CLI integration

2. **Phase 2** - Migration Documentation (Low Effort, High Value)
   - Document existing migration pattern
   - Add version tracking

3. **Phase 3** - Enhanced Diagnostics (Low Priority, Nice-to-Have)
   - Improve auto-fix capabilities
   - Add history tracking

---

## Acceptance Checklist

### Overall
- [ ] No breaking changes to existing functionality
- [ ] All new code has type hints
- [ ] All new code is tested (80%+ coverage)
- [ ] Documentation updated
- [ ] Changelog entry added

### Pattern 1 - Diagnostics
- [ ] `try_fix()` returns structured results
- [ ] At least one working auto-fix implemented
- [ ] Diagnostic history export/import working

### Pattern 2 - Transcription
- [ ] `TranscriptionEngine` ABC implemented
- [ ] `LocalWhisperEngine` transcribes audio
- [ ] Database migration for `source_type` applied
- [ ] CLI command `yt-fts transcribe` working
- [ ] Tests cover main use cases

### Pattern 3 - Migrations
- [ ] Migration documentation created
- [ ] Version tracking table implemented
- [ ] All existing migrations catalogued

---

## References

- Source: `C:/Users/brsth/Downloads/jules_session_17326749298833802222/projects/yt-fts/src/yt_fts`
- Target: `P:/projects/yt-fts/src/yt_fts`
- Python 2025 Standards: See code-python-2025 skill

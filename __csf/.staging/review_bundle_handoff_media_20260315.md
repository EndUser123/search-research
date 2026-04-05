# Handoff Package - Media Generation Review Bundle

**Generated**: 2026-03-15
**Scope**: P:/packages/handoff
**Purpose**: Architectural context for NotebookLM media generation

---

## 1. PROJECT CONTEXT

### Domain & Purpose
**handoff** is a Claude Code plugin that provides compact/resume continuity for sessions. It captures terminal state before transcript compaction and restores it on session start, preserving work context across compactions and multi-terminal workflows.

**Current Version**: v0.3.1 (March 15, 2026)
**Test Status**: 103/103 tests passing ✅

### Scale Metrics
- **Lines of Code**: ~3,500 Python LOC
- **Major Subsystems**: 7 (Capture, Restore, State Management, Transcript Parsing, Validation, Utilities, Tests)
- **Deployment Scope**: Claude Code plugin (hooks-based)
- **Change Frequency**: Active development (recent v0.3.0 migration from core/ to scripts/)

### Environment
- **Platform**: Windows, macOS, Linux (multi-platform)
- **Primary Language**: Python 3.9+
- **Framework**: Claude Code hooks (PreCompact, SessionStart)
- **Storage**: JSON files with SHA256 checksum validation
- **External Services**: None (local state management only)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                      HANDOFF SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ PreCompact Hook  │         │ SessionStart Hook │             │
│  │  (Capture)       │         │   (Restore)       │             │
│  └────────┬─────────┘         └────────┬─────────┘             │
│           │                            │                         │
│           ▼                            ▼                         │
│  ┌──────────────────────────────────────────────┐              │
│  │         V2 Handoff Envelope                  │              │
│  │  ┌─────────────────────────────────────┐    │              │
│  │  │ • resume_snapshot                    │    │              │
│  │  │   - current_task, progress, blockers │    │              │
│  │  │   - active_files, pending_ops        │    │              │
│  │  │ • decision_register                  │    │              │
│  │  │   - constraints, decisions, anti-goals│    │              │
│  │  │ • evidence_index (reference-only)    │    │              │
│  │  │   - files, transcripts, tests, logs  │    │              │
│  │  │ • checksum (SHA256)                   │    │              │
│  │  └─────────────────────────────────────┘    │              │
│  └──────────────────┬───────────────────────────┘              │
│                     │                                           │
│                     ▼                                           │
│  ┌────────────────────────────────────────────┐                │
│  │  Per-Terminal State Storage               │                │
│  │  ~/.claude/state/handoff/{terminal}_*.json │                │
│  └────────────────────────────────────────────┘                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Subsystem Components

**1. Capture System (PreCompact_handoff_capture.py)**
- **Entry Point**: PreCompact hook triggered before transcript compaction
- **Purpose**: Extract context from transcript and build V2 envelope
- **Key Functions**:
  - `main()` - Hook entry point
  - `detect_session_type()` - Categorize session (debug, feature, refactor, etc.)
  - `detect_planning_session()` - Identify planning blockers
  - `_build_evidence_index()` - Compile supporting evidence
  - `_build_decisions()` - Extract decision register
  - `_estimate_progress()` - Calculate task progress

**2. Restore System (SessionStart_handoff_restore.py)**
- **Entry Point**: SessionStart hook triggered after session start
- **Purpose**: Restore context from handoff file with validation
- **Key Functions**:
  - `main()` - Hook entry point
  - `_normalize_session_start_source()` - Detect session type
  - `_reject_if_possible()` - Validate and reject invalid/stale snapshots
  - Restore policy enforcement (terminal ID, status, freshness window)

**3. State Management (handoff_files.py, handoff_store.py)**
- **Purpose**: File I/O and state lifecycle management
- **Functions**: Save, load, update status, checksum validation
- **Storage**: Per-terminal JSON files with status tracking

**4. Transcript Parsing (transcript.py)**
- **Purpose**: Extract structured information from Claude transcripts
- **Key Functions**:
  - `extract_last_substantive_user_message()` - Find user's last real task
  - `extract_pending_operations()` - Detect pending work from tool_use events
  - `extract_session_start_transcript()` - Get session start context
  - Session boundary detection (session_chain_id changes)
  - Topic shift detection (semantic similarity 30% threshold)

**5. Validation (handoff_v2.py, hook_input_validation.py)**
- **Purpose**: Ensure data integrity and schema compliance
- **Components**: SHA256 checksums, schema validation, freshness checks

**6. Utilities**
- **project_root.py**: Detect project root directory
- **terminal_detection.py**: Derive terminal ID from environment
- **task_identity_manager.py**: Multi-terminal isolation
- **capture_cache.py**: Capture result caching

**7. Tests (tests/)**
- **Coverage**: 103 tests covering all features
- **Test Files**: 16 test files + fixtures
- **Status**: All passing after v0.3.1 import fixes

---

## 3. EXECUTION AND DATA FLOW

### Capture Flow (PreCompact)
```
Transcript compaction triggered
    ↓
PreCompact hook invoked
    ↓
Parse transcript for:
  • Last substantive user message (canonical goal)
  • Pending operations (tool_use events)
  • Active files
  • Decisions and constraints
  • Session metadata (type, invoked command)
    ↓
Build V2 envelope:
  • resume_snapshot (task, progress, blockers, files, ops)
  • decision_register (constraints, decisions, anti-goals)
  • evidence_index (files, transcripts, tests, logs)
  • checksum (SHA256)
    ↓
Write to per-terminal state file
    ↓
Mark status: pending
```

### Restore Flow (SessionStart)
```
New session starts
    ↓
SessionStart hook invoked
    ↓
Check for pending snapshot:
  • Same terminal ID?
  • Status == pending?
  • Within freshness window (20 min)?
    ↓
If valid:
  • Inject restore message into transcript
  • Mark status: consumed
    ↓
If invalid/stale:
  • Inject rejection hint
  • Mark status: rejected_stale / rejected_invalid
```

### State Management
- **Storage**: Per-terminal JSON files
- **Isolation**: Each terminal has independent state
- **Consistency**: SHA256 checksums validate integrity
- **Freshness**: 20-minute window for automatic restoration

### Error Handling
- **Policy**: Fail-closed (reject invalid snapshots)
- **Validation**: Checksum verification, schema validation, freshness checks
- **Fallback**: Inject restoration hint with error details

---

## 4. COMPONENT INVENTORY

### Core Library Modules (`scripts/hooks/__lib/`)

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| `handoff_v2.py` | V2 envelope schema and data structures | `build_envelope()`, `build_resume_snapshot()`, `make_decision_id()`, `make_evidence_id()` |
| `handoff_files.py` | File I/O and state management | `save_handoff()`, `load_handoff()`, `update_handoff_status()` |
| `transcript.py` | Transcript parsing and extraction | `extract_last_substantive_user_message()`, `extract_pending_operations()` |
| `hook_input_validation.py` | Input validation and sanitization | `validate_transcript_path()`, `validate_project_root()` |
| `project_root.py` | Project root detection | `detect_project_root()`, `HANDOFF_PROJECT_ROOT` override |
| `terminal_detection.py` | Terminal ID derivation | `get_terminal_id()`, `detect_terminal_id()` |
| `task_identity_manager.py` | Multi-terminal isolation | `get_task_identity()`, `normalize_task_id()` |
| `capture_cache.py` | Capture result caching | `cache_capture_result()`, `get_cached_capture()` |

### Hook Entry Points
- `PreCompact_handoff_capture.py` - State capture before compaction
- `SessionStart_handoff_restore.py` - State restoration after session start

### Configuration Files
- `.claude-plugin/plugin.json` - Plugin metadata
- `hooks/hooks.json` - Hook registration
- `README.md` - Package documentation
- `CHANGELOG.md` - Version history
- `AGENTS.md` - AI-maintainable documentation

### Test Suite (`tests/`)
- `test_canonical_goal_extraction.py` - Goal extraction (7 tests)
- `test_pending_operations_extraction.py` - Pending ops detection (17 tests)
- `test_handoff_integration.py` - End-to-end integration
- `test_deterministic_checksums.py` - Checksum validation
- `test_terminal_isolation.py` - Multi-terminal behavior
- `test_context_gathering_boundaries.py` - Session boundary detection
- Plus 10 more test files covering all features

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Multi-terminal isolation**: Each terminal has independent handoff state
2. **Stateless design**: No shared state between terminals
3. **V2-only design**: No backward compatibility reads (clean break from V1)
4. **Research-backed**: V2 envelope based on handoff research findings

### Technology Constraints
- **No external dependencies**: Pure Python with standard library
- **File-based storage**: JSON files for state persistence
- **SHA256 validation**: Checksums for data integrity
- **Platform-agnostic**: Works on Windows, macOS, Linux

### Performance SLAs
- **Capture latency**: < 1 second for PreCompact hook
- **Restore latency**: < 1 second for SessionStart hook
- **Test performance**: 103 tests in ~4 seconds

### Things That Must NOT Change
- ✅ V2 envelope schema (resume_snapshot, decision_register, evidence_index, checksum)
- ✅ Per-terminal isolation model
- ✅ SHA256 checksum validation
- ✅ Session boundary detection using session_chain_id
- ✅ Topic shift detection with 30% threshold
- ✅ Freshness window (20 minutes default)
- ✅ Multi-terminal state isolation

---

## 6. KNOWN ISSUES

### Resolved Issues (v0.3.1)
- ✅ **Test import paths**: Fixed 16 test files with broken imports after core/ → scripts/ migration
- ✅ **Symlink paths**: Updated README.md to use correct `scripts/hooks/` paths
- ✅ **Documentation inconsistency**: Updated all docs to reflect current structure

### Current Limitations
- ⚠️ **No V1 backward compatibility**: V2-only design (intentional)
- ⚠️ **Freshness window hardcoded**: 20-minute default (configurable via env var)
- ⚠️ **Manual symlink setup**: Development requires manual symlink creation

---

## 7. INTEGRATION POINTS

### Hook Registration
- **PreCompact**: Registered in `hooks/hooks.json` with matcher pattern
- **SessionStart**: Registered in `hooks/hooks.json` with matcher pattern
- **Invocation**: Claude Code hooks system auto-discovers and executes

### Data Exchange
- **Input**: Transcript path, project root (from hook environment)
- **Output**: Handoff JSON file written to state directory
- **Side Effects**: Injects restoration message into transcript

### Extension Points
- **Custom capture modules**: Add new capture phases (e.g., git_state, test_state)
- **Custom validation**: Extend checksum validation
- **Custom restoration**: Modify restoration message format

---

## 8. MEDIA GENERATION CONTEXT

### Key Features for Asset Generation

**1. V2 Handoff Envelope**
- Resume snapshot with task progress, blockers, active files
- Decision register with constraints and decisions
- Evidence index with reference-only supporting context
- SHA256 checksum validation

**2. Transcript Extraction**
- Canonical goal extraction (last substantive user message)
- Pending operations detection (tool_use events)
- Session boundary detection (session_chain_id changes)
- Topic shift detection (30% semantic similarity threshold)

**3. Multi-Terminal Isolation**
- Per-terminal state directories
- Independent handoff state per terminal
- Terminal ID derivation from environment

**4. Restore Policy**
- Automatic restore for fresh snapshots (same terminal, pending status, < 20 min)
- Reject stale snapshots (outside freshness window)
- Reject invalid snapshots (checksum failures, schema violations)

**5. Testing & Quality**
- 103 tests covering all features
- All tests passing after v0.3.1 fixes
- Comprehensive test coverage for extraction, validation, and isolation

### Visual Assets Needed
1. **Banner**: GitHub social preview (1200×630)
2. **Architecture diagram**: System overview with V2 envelope structure
3. **Explainer video**: Technical walkthrough of capture/restore workflow
4. **Slide deck**: Feature presentation with use cases

### Target Audience
- Developers evaluating handoff for their workflows
- Claude Code users interested in session continuity
- Contributors understanding the architecture

### Tone & Style
- Technical, calm, direct, low-hype
- Focus on architecture, workflow, and outputs
- Concrete nouns and file paths over abstract claims
- Avoid marketing language and dramatic storytelling
- Length target: 60-120 seconds for video

---

## 9. APPENDIX: RECENT CHANGES

### v0.3.1 (2026-03-15)
- Fixed 16 test files with broken imports after core/ → scripts/ migration
- Updated README.md Quick Start section with correct symlink paths
- All 103 tests now passing
- Documentation fully updated and consistent

### v0.3.0 (2026-03-14)
- Migrated from `core/` to `scripts/` for plugin standards compliance
- Updated hook configuration to reference new paths
- Removed obsolete `skill/` directory

### Migration Impact
- Import path changes: `from core.hooks.__lib` → `from __lib` with sys.path setup
- Symlink path changes: `core/hooks/` → `scripts/hooks/`
- All documentation updated to reflect new structure
- Rollback available via git commit backup (e161e635b4)

---

**Status**: ✅ Package is GitHub-ready with accurate documentation, working tests, and correct import structure.

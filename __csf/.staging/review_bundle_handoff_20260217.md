# Review Bundle: handoff Package

**Generated**: 2026-02-17
**Scope**: P:/packages/handoff/
**File Count**: ~70 files
**Execution Mode**: 4-agent parallel analysis

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Package**: `handoff`
- **Version**: 0.2.0
- **Repository**: https://github.com/EndUser123/handoff (private)
- **File Count**: ~70 files (Python modules, tests, documentation)
- **Execution Mode**: 4-agents (comprehensive parallel analysis)

### Domain & Purpose
The **handoff** package provides automatic session state capture and restoration for Claude Code. When transcripts are compacted (to manage token limits), handoff preserves the complete conversation context: user requests, visual evidence, incomplete operations, and session decisions. This ensures AI assistants can resume work seamlessly without losing critical context.

### Scale Metrics
- **LOC**: ~7,087 lines (33 files in initial commit)
- **Major Subsystems**: 6 (core models, checkpoint chains, transcript parsing, storage protocol, hooks integration, CLI wrapper)
- **Deployment Scope**: Standalone Python package with zero external dependencies
- **Change Frequency**: Active development (v0.2.0 as of 2026-02-17)

### Your Environment
- **OS**: Windows 11 Pro
- **Primary Languages**: Python 3.9+ (standard library only)
- **Package Managers**: `uv` (development), `pip` (installation)
- **Build Tools**: `pyproject.toml` (no build system required)
- **Databases/External Services**: None (local filesystem storage only)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Hooks                        │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ PreCompact Hook  │         │ SessionStart Hook│         │
│  │  (Capture State) │         │  (Restore State) │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
└───────────┼───────────────────────────┼─────────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Handoff Core Layer                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │              TranscriptParser                       │     │
│  │  • Extract user messages (untruncated)             │     │
│  │  • Extract modifications, blockers, decisions       │     │
│  │  • Extract visual context (screenshots)            │     │
│  │  • Extract pending operations (incomplete work)    │     │
│  └──────────────────┬─────────────────────────────────┘     │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────┐     │
│  │              HandoffStore                          │     │
│  │  • Build handoff data from extracted context       │     │
│  │  • Add checkpoint chain links (parent/child)       │     │
│  │  • Calculate quality scores                        │     │
│  │  • Enrich with bridge tokens                       │     │
│  └──────────────────┬─────────────────────────────────┘     │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────┐     │
│  │         HandoffStorage Protocol                    │     │
│  │  • save_handoff() - Atomic write with validation    │     │
│  │  • load_handoff() - Restore from task metadata     │     │
│  │  • list_handoffs() - Query available checkpoints   │     │
│  │  • delete_handoff() - Cleanup old checkpoints      │     │
│  └──────────────────┬─────────────────────────────────┘     │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Task Tracker Metadata                       │
│  File: {terminal_id}_tasks.json                              │
│  {                                                           │
│    "active_session": {                                       │
│      "checkpoint_id": "abc-123",                             │
│      "metadata": { "handoff": {...} }                       │
│    },                                                        │
│    "continue_session": { ... }                               │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Subsystem Details

#### **Core Models** (`src/handoff/models.py`)
- **Files**: `models.py`, `checkpoint_ops.py`
- **Entry Points**: `HandoffCheckpoint`, `PendingOperation`
- **Dependencies**: None (pure Python dataclasses)
- **Critical Invariants**:
  - `original_user_request` is NEVER truncated (authentic user intent)
  - `checksum` is SHA256 of sorted JSON (data integrity)
  - `checkpoint_id`, `parent_checkpoint_id`, `chain_id` enable traversal
  - `pending_operations` tracks incomplete work (edit, test, read, command, skill)

#### **Checkpoint Chains** (`src/handoff/checkpoint_chain.py`)
- **Files**: `checkpoint_chain.py`
- **Entry Points**: `CheckpointChain`, `HandoffCheckpointRef`
- **Dependencies**: `models.py`, `protocol.py`
- **Critical Invariants**:
  - Parent-child relationships form traversable chains
  - Chains grouped by `chain_id` (UUID v4)
  - `_cache` prevents reloading chains
  - Checkpoints sorted by `created_at` for traversal

#### **Transcript Parsing** (`src/handoff/hooks/__lib/transcript.py`)
- **Files**: `transcript.py`
- **Entry Points**: `TranscriptParser`, `TranscriptLines`
- **Dependencies**: None (reads Claude Code transcript JSON)
- **Critical Invariants**:
  - `TranscriptLines` uses O(1) memory (lazy loading, no full file load)
  - MAX_FILE_SIZE=10MB, MAX_ENTRIES=50K (quality control)
  - `extract_last_user_message()` returns FULL message (no truncation)
  - `extract_visual_context()` preserves screenshots/image analysis

#### **Storage Protocol** (`src/handoff/protocol.py`)
- **Files**: `protocol.py`, `config.py`
- **Entry Points**: `HandoffStorage` (Protocol), configuration constants
- **Dependencies**: None (type hints only)
- **Critical Invariants**:
  - Protocol interface enables multiple storage backends
  - HANDOFF_DIR = `.claude/handoffs/` (configurable via env var)
  - CLEANUP_DAYS=90, MAX_VERSIONS=20 (retention policies)

#### **Hooks Integration** (`src/handoff/hooks/`)
- **Files**: `handoff_store.py`, `handover.py`, `task_identity_manager.py`, `bridge_tokens.py`
- **Entry Points**: `HandoffStore`, `HandoverBuilder`, `TaskIdentityManager`
- **Dependencies**: Internal modules + `transcript.py`
- **Critical Invariants**:
  - Atomic writes with Windows file locking retry
  - Terminal isolation (per-terminal task files prevent cross-contamination)
  - Bridge tokens format: `BRIDGE_YYYYMMDD-HHMMSS_TOPIC`
  - 6-source resilience chain for task identity recovery

#### **CLI Wrapper** (`skill/lib/hod.py`)
- **Files**: `hod.py`
- **Entry Points**: `/hod` skill command
- **Dependencies**: HandoffStore, TaskIdentityManager, BridgeTokens
- **Purpose**: Manual handoff generation (rarely used - hooks handle automatically)

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### **Capture Flow (PreCompact Hook)**
```
1. PreCompact_hook triggered
   ↓
2. TaskIdentityManager.get_current_task()
   • Try 6 sources: ad-hoc command → env var → session file →
     compact metadata → git worktree → user prompt
   ↓
3. TranscriptParser.extract_*()
   • Extract blocker, modifications, decisions, patterns
   • Extract visual context, pending operations
   • Extract FULL last user message (untruncated)
   ↓
4. HandoffStore.build_handoff_data()
   • Generate checkpoint_id (UUID v4)
   • Link to parent_checkpoint_id (from previous checkpoint)
   • Reuse chain_id (session identifier)
   • Calculate quality score (optional)
   • Enrich with bridge tokens (optional)
   ↓
5. validate_handoff_size() (QUAL-009)
   • Enforce 500KB limit
   • Truncate: active_files (100), next_steps (10K chars),
     handover (10 each), recent_tools (30), modifications (50)
   ↓
6. compute_metadata_checksum()
   • SHA256 of sorted JSON (deterministic)
   ↓
7. HandoffStore.create_continue_session_task()
   • Create "active_session" task (for SessionStart detection)
   • Create "continue_session" task (user-visible)
   • Atomic write with Windows file locking retry
   ↓
8. Task tracker saves to {terminal_id}_tasks.json
```

#### **Restore Flow (SessionStart Hook)**
```
1. SessionStart_hook triggered
   ↓
2. TaskIdentityManager.get_current_task()
   • Check session file for active task
   ↓
3. HandoffStorage.load_handoff(task_name, terminal_id, strict=False)
   • Read task metadata
   • Extract handoff data
   ↓
4. Validate checksum
   • Compare SHA256
   • If mismatch: log warning, continue (best-effort)
   ↓
5. CheckpointChain.get_latest(chain_id)
   • Load most recent checkpoint in chain
   ↓
6. Restore session context
   • Display original_user_request (untruncated)
   • Display blocker, progress, next_steps
   • Display visual context (screenshots)
   • Display pending_operations (incomplete work)
   ↓
7. Seek transcript to transcript_offset
   • Resume from exact character position
```

### Mandatory Ordering Constraints
1. **Capture must complete before compaction** - PreCompact hook runs before transcript truncation
2. **Restore must complete before AI response** - SessionStart hook runs before user prompt processing
3. **Parent checkpoint must exist before child** - `parent_checkpoint_id` references previous checkpoint
4. **Checksum must be computed after data assembly** - SHA256 calculated on final handoff data
5. **Task identity must be recovered before load** - SessionStart hook restores task name first

### State Management
- **State Stores**: Task tracker metadata files (`{terminal_id}_tasks.json`)
- **Ownership**: HandoffStore owns write operations; SessionStart hook owns read operations
- **Consistency Model**: Eventual consistency (atomic writes with retry on Windows file locking)
- **Isolation Boundaries**: Per-terminal task files (double underscore separator in task IDs)

### Error Handling
- **Fail-Open Policy**: If handoff load fails, log warning and continue (don't block session start)
- **Checksum Mismatch**: Log warning, don't raise exception (best-effort restoration)
- **File I/O Errors**: Returns None or empty collections (graceful degradation)
- **Validation Errors**: Raises ValueError for missing required fields (strict validation on save)
- **Retry Logic**: Atomic write with exponential backoff (5ms → 10ms → 20ms → 40ms, max 5 retries)

---

## 4. COMPONENT INVENTORY

### Core Logic

#### **TranscriptParser** (`src/handoff/hooks/__lib/transcript.py`)
- **Path**: `hooks/__lib/transcript.py`
- **Key Functions**:
  - `extract_current_blocker()` - Get last user message as blocker (may truncate)
  - `extract_last_user_message()` - Get FULL, untruncated user message
  - `extract_modifications(limit=50)` - Get Edit tool operations (FIFO)
  - `extract_session_decisions()` - Extract decisions from conversation
  - `extract_session_patterns()` - Extract discovered patterns
  - `extract_visual_context()` - Extract screenshots/image analysis
  - `extract_pending_operations()` - Extract incomplete operations
- **Responsibilities**: Parse Claude Code transcript JSON to extract session context
- **Inputs**: Transcript file path (JSONL format)
- **Outputs**: Dictionary with extracted session data
- **Known Limitations**:
  - MAX_FILE_SIZE=10MB (larger files rejected)
  - MAX_ENTRIES=50K (larger transcripts rejected)
  - Requires user message to be in `message.content` field

#### **HandoffStore** (`src/handoff/hooks/__lib/handoff_store.py`)
- **Path**: `hooks/__lib/handoff_store.py`
- **Key Methods**:
  - `build_handoff_data(...)` - Assemble complete handoff from extracted data
  - `create_continue_session_task(...)` - Create task with handoff in metadata
- **Responsibilities**: Build handoff data and create continue_session tasks
- **Inputs**: Extracted session data (blocker, modifications, decisions, etc.)
- **Outputs**: HandoffCheckpoint dataclass
- **Known Limitations**:
  - MAX_HANDOFF_SIZE_BYTES=500KB (larger handoffs truncated)
  - Requires task identity to be known (uses TaskIdentityManager)

#### **CheckpointChain** (`src/handoff/checkpoint_chain.py`)
- **Path**: `checkpoint_chain.py`
- **Key Methods**:
  - `get_chain(chain_id)` - Get all checkpoints in chain (oldest→newest)
  - `get_latest(chain_id)` - Get newest checkpoint
  - `get_previous(checkpoint_id)` - Get previous checkpoint
  - `get_next(checkpoint_id)` - Get next checkpoint
- **Responsibilities**: Traverse chains of related handoff checkpoints
- **Inputs**: chain_id or checkpoint_id
- **Outputs**: List of HandoffCheckpointRef or single HandoffCheckpointRef
- **Known Limitations**:
  - Requires checkpoints to have checkpoint_chain fields
  - Cached chains may become stale if new checkpoints added

### Utilities/Helpers

#### **TaskIdentityManager** (`src/handoff/hooks/__lib/task_identity_manager.py`)
- **Path**: `hooks/__lib/task_identity_manager.py`
- **Key Methods**:
  - `get_current_task()` - Get task using 6-source resilience chain
  - `set_current_task(task_name)` - Set task and persist to session file
  - `record_active_command(command, phase, metadata)` - Track ad-hoc commands
- **Responsibilities**: Manage task identity across compaction events
- **Inputs**: None (reads from multiple sources)
- **Outputs**: Task name string or None
- **Known Limitations**:
  - 6-source chain may fail if all sources unavailable
  - Session files may become stale (cleanup required)

#### **BridgeTokens** (`src/handoff/hooks/__lib/bridge_tokens.py`)
- **Path**: `hooks/__lib/bridge_tokens.py`
- **Key Functions**:
  - `generate_bridge_token(topic, timestamp)` - Generate cross-session continuity token
  - `extract_bridge_tokens(handoff_data)` - Extract all tokens from handoff decisions
- **Responsibilities**: Generate and validate bridge tokens for decision tracking
- **Inputs**: Topic string and timestamp
- **Outputs**: Bridge token string (format: `BRIDGE_YYYYMMDD-HHMMSS_TOPIC`)
- **Known Limitations**:
  - Tokens limited to 20 chars (topic truncated)
  - No built-in expiration (manual cleanup required)

#### **HandoverBuilder** (`src/handoff/hooks/__lib/handover.py`)
- **Path**: `hooks/__lib/handover.py`
- **Key Methods**:
  - `build(task_name)` - Generate handover dict from session and CKS context
- **Responsibilities**: Generate handover data from session context
- **Inputs**: Task name string
- **Outputs**: Dictionary with decisions, patterns, controversial decisions, objectives
- **Known Limitations**:
  - Requires `.claude/objectives.txt` file for session objectives
  - Pattern detection relies on keyword heuristics

### Configuration

#### **Config** (`src/handoff/config.py`)
- **Path**: `config.py`
- **Key Constants**:
  - `PROJECT_ROOT` - Project root directory (default: `P:/`)
  - `HANDOFF_DIR` - Handoff storage directory (`.claude/handoffs/`)
  - `TRASH_DIR` - Trash directory for deleted handoffs
  - `CLEANUP_DAYS` - Days before auto-cleanup (default: 90)
  - `MAX_VERSIONS` - Max versions to retain (default: 20)
- **Responsibilities**: Centralize paths, retention policies, and defaults
- **Inputs**: Environment variables
- **Outputs**: Path objects and constants
- **Known Limitations**:
  - No runtime configuration reload (requires restart)
  - Hardcoded defaults (no config file support)

#### **Protocol** (`src/handoff/protocol.py`)
- **Path**: `protocol.py`
- **Key Classes**:
  - `HandoffStorage` - Protocol interface for type-safe storage operations
- **Responsibilities**: Define storage contract for multiple backend implementations
- **Inputs**: None (type hints only)
- **Outputs**: Protocol interface
- **Known Limitations**:
  - No built-in implementations (must implement manually)
  - Protocol only checked at runtime (not static type checked)

### Infrastructure

#### **Models** (`src/handoff/models.py`)
- **Path**: `models.py`
- **Key Classes**:
  - `HandoffCheckpoint` - Complete handoff checkpoint with chain links
  - `PendingOperation` - Tracks incomplete operations for fault tolerance
- **Responsibilities**: Provide typed dataclass models for handoff data validation
- **Inputs**: Dictionary data (for deserialization)
- **Outputs**: Typed dataclass instances
- **Known Limitations**:
  - No Pydantic validation (manual validation in from_dict)
  - No JSON schema generation

#### **Migrate** (`src/handoff/migrate.py`)
- **Path**: `migrate.py`
- **Key Functions**:
  - `compute_metadata_checksum(handoff_data)` - Compute SHA256 checksum
  - `load_handoff_json(json_path)` - Load and validate legacy JSON files
  - `handoff_to_task(handoff_data, terminal_id)` - Convert legacy to task metadata
  - `validate_handoff_size(handoff_data)` - Enforce 500KB limit
- **Responsibilities**: Migrate legacy JSON files to task metadata format
- **Inputs**: Legacy handoff JSON file path
- **Outputs**: Task metadata dictionary
- **Known Limitations**:
  - Migration is one-way (no rollback)
  - Requires manual invocation (not automatic)

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Zero External Dependencies** - Pure Python standard library only (no pip install required for runtime)
2. **Hook-Only Architecture** - All capture and restoration happens automatically via Claude Code hooks
3. **Full User Message Preservation** - `original_user_request` is NEVER truncated (authentic source of user intent)
4. **Terminal Isolation** - Each terminal gets its own task file (prevents cross-terminal handoff contamination)
5. **Data Integrity** - SHA256 checksums on all handoff data (validates corruption)
6. **Fault Tolerance** - `pending_operations` tracks incomplete work (enables recovery after compaction)

### Technology Constraints
1. **Python 3.9+** - Minimum Python version (uses `from __future__ import annotations`)
2. **Standard Library Only** - No external dependencies for runtime (dev dependencies optional)
3. **Filesystem Storage** - Local filesystem only (no S3, no database)
4. **JSON Format** - All data stored as JSON (no binary formats, no msgpack)
5. **Windows File Locking** - Atomic writes with retry logic for Windows file locking

### Performance SLAs
1. **Capture Time** - <5 seconds for PreCompact hook (prevent compaction delays)
2. **Restore Time** - <2 seconds for SessionStart hook (prevent session start delays)
3. **File Size** - 500KB max per handoff (enforced by validate_handoff_size)
4. **Memory Usage** - O(1) for transcript parsing (TranscriptLines lazy loading)

### Things That Must NOT Change
1. **`original_user_request` Truncation** - NEVER truncate this field (authentic user intent)
2. **Checksum Algorithm** - SHA256 with sorted JSON (deterministic, verifiable)
3. **Checkpoint Chain Fields** - `checkpoint_id`, `parent_checkpoint_id`, `chain_id` required for traversal
4. **Terminal Isolation** - Per-terminal task files (never share across terminals)
5. **Hook-Based Architecture** - No CLI commands for core functionality (hooks handle everything)
6. **Atomic Writes** - Temp file + rename pattern (no partial writes)
7. **Backward Compatibility** - Migration from old format must work (migrate.py)

---

## 6. KNOWN ISSUES

### Issue #1: Duplicate PendingOperation Model
- **Scenario**: `PendingOperation` defined in both `models.py` and `checkpoint_ops.py`
- **Expected vs Actual**: Should have single source of truth, but duplicated across two files
- **Impact**: Maintenance burden (changes must be made in two places)
- **Current Workaround**: Use `models.py` version (primary), ignore `checkpoint_ops.py`
- **Fix**: Remove `checkpoint_ops.py`, consolidate to `models.py`

### Issue #2: Low Test Coverage (29.5%)
- **Scenario**: Badge shows red coverage badge (<50% threshold)
- **Expected vs Actual**: Should have >80% coverage for production-quality package
- **Impact**: Reduced confidence in code correctness, potential undetected bugs
- **Current Workaround**: Manual testing during development
- **Fix**: Add tests for uncovered paths:
  - `handoff_store.py` (core logic)
  - `task_identity_manager.py` (6-source chain)
  - `bridge_tokens.py` (token generation/validation)
  - `handover.py` (handover building)

### Issue #3: No Runtime Configuration Reload
- **Scenario**: Config constants loaded at import time, not reloaded on change
- **Expected vs Actual**: Should reload config when .env changes, but requires restart
- **Impact**: Cannot change retention policies without restarting Python process
- **Current Workaround**: Restart Claude Code session
- **Fix**: Implement config watcher with file system observer

### Issue #4: Stale Session Files
- **Scenario**: Session files may become orphaned if terminal closed unexpectedly
- **Expected vs Actual**: Should auto-cleanup stale files, but requires manual cleanup call
- **Impact**: Disk space usage, potential task identity confusion
- **Current Workaround**: Call `cleanup_stale_terminal_files()` periodically
- **Fix**: Auto-cleanup on SessionStart hook (check file age before using)

### Issue #5: Checksum Mismatch Silently Ignored
- **Scenario**: If handoff data corrupted, checksum mismatch logs warning but continues
- **Expected vs Actual**: Should fail fast on corruption, but best-effort restoration may be confusing
- **Impact**: May restore corrupted handoff data without user awareness
- **Current Workaround**: Check logs for checksum warnings
- **Fix**: Add user-visible alert on checksum mismatch (require user confirmation)

---

## 7. INTEGRATION POINTS

### Hook Integration Points
- **PreCompact Hook** - `P:/.claude/hooks/pre_compact_hook.py`
  - **Invocation Model**: Automatic before transcript compaction
  - **Data Exchange Contract**: Expects `TRANSCRIPT_PATH` env var, writes handoff to task metadata
  - **Output Expectations**: Creates `active_session` and `continue_session` tasks

- **SessionStart Hook** - `P:/.claude/hooks/session_start_hook.py`
  - **Invocation Model**: Automatic on session resume
  - **Data Exchange Contract**: Reads handoff from task metadata, displays to user
  - **Output Expectations**: Restores session context (blocker, progress, next_steps)

### Task Tracker Integration
- **Location**: `.claude/taskmaster/tasks/{terminal_id}_tasks.json`
- **Data Format**: JSON with top-level task objects, handoff in `metadata.handoff` field
- **Write Pattern**: Atomic write with temp file + rename
- **Read Pattern**: Load full JSON, extract task by name, access metadata.handoff

### CLI Skill Integration
- **Skill Path**: `P:/.claude/skills/handoff/` (symlink to `packages/handoff/skill`)
- **Invocation**: User types `/hod` to manually generate handoff
- **Data Exchange**: Reads current task, extracts transcript, creates handoff
- **Output**: Displays handoff summary with quality score

### Migration Integration
- **Script**: `packages/handoff/scripts/rename_from_checkpoint.py`
- **Invocation**: Manual one-time migration from old "checkpoint" terminology
- **Data Exchange**: Reads old JSON files, writes new task metadata format
- **Output**: Migrated handoffs with checkpoint chain fields

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Example Handoff Data Structure
```json
{
  "checkpoint_id": "abc-123-def-456",
  "parent_checkpoint_id": "previous-checkpoint-id",
  "chain_id": "session-uuid-v4",
  "created_at": "2026-02-17T14:30:00Z",
  "task_name": "implement-feature-x",
  "task_type": "feature-dev",
  "progress_percent": 45,
  "blocker": {
    "description": "Need to clarify requirements with product owner",
    "severity": "high",
    "source": "user"
  },
  "next_steps": [
    "1. Schedule meeting with product owner",
    "2. Update requirements document",
    "3. Implement core logic"
  ],
  "git_branch": "feature/implementation",
  "active_files": [
    "src/handoff/models.py",
    "src/handoff/checkpoint_chain.py"
  ],
  "recent_tools": [
    {"tool": "Edit", "target": "models.py", "timestamp": "..."},
    {"tool": "Read", "target": "checkpoint_chain.py", "timestamp": "..."}
  ],
  "modifications": [
    {
      "file": "src/handoff/models.py",
      "line": 42,
      "before": "old code",
      "after": "new code",
      "reason": "Add checksum field"
    }
  ],
  "handover": {
    "decisions": [
      "Use SHA256 for checksums (deterministic, verifiable)",
      "Store handoffs in task metadata (eliminate dual storage)"
    ],
    "patterns_learned": [
      "PreCompact hook must complete before compaction starts",
      "SessionStart hook must restore context before AI response"
    ],
    "controversial_decisions": [],
    "session_objectives": ["Implement handoff for session continuity"]
  },
  "visual_context": [
    {
      "description": "Screenshot of error message",
      "type": "screenshot",
      "tool": "analyze_image",
      "user_response": "Yes, that's the error I'm seeing"
    }
  ],
  "original_user_request": "Implement handoff package for session continuity across compaction events. Preserve full user intent, visual context, and incomplete operations.",
  "first_user_request": "Create handoff system",
  "pending_operations": [
    {
      "type": "edit",
      "target": "src/handoff/checkpoint_chain.py",
      "state": "in_progress",
      "details": {"change": "Add chain traversal methods"},
      "started_at": "2026-02-17T14:25:00Z"
    }
  ],
  "checksum": "sha256:a1b2c3d4e5f6...",
  "transcript_offset": 1234567,
  "transcript_entry_count": 234
}
```

### Example Quality Score Calculation
```python
# From calculate_quality_score() in handoff_store.py

def calculate_quality_score(handoff_data):
    # 30% Completion (resolved issues vs modifications)
    completion_score = min(1.0, resolved_issues / total_modifications) * 0.3

    # 25% Outcomes (blocker presence = incomplete)
    outcome_score = 0.0 if handoff_data.get("blocker") else 1.0 * 0.25

    # 20% Decisions (number captured, max 10)
    decision_score = min(len(decisions) / 10, 1.0) * 0.2

    # 15% Issues (blocker indicates incomplete)
    issue_score = 0.0 if handoff_data.get("blocker") else 1.0 * 0.15

    # 10% Knowledge (patterns learned, max 5)
    knowledge_score = min(len(patterns) / 5, 1.0) * 0.1

    return completion_score + outcome_score + decision_score + issue_score + knowledge_score

# Example: Good session
# completion_score = 0.24 (8/10 resolved)
# outcome_score = 0.25 (no blocker)
# decision_score = 0.16 (8 decisions)
# issue_score = 0.15 (no blocker)
# knowledge_score = 0.08 (4 patterns)
# total = 0.88 (88% quality)
```

### Example Bridge Token Generation
```python
# From generate_bridge_token() in bridge_tokens.py

from datetime import datetime

topic = "Authentication"
timestamp = datetime(2026, 2, 17, 14, 30, 0)

# Format: BRIDGE_YYYYMMDD-HHMMSS_TOPIC_KEYWORD
time_part = timestamp.strftime("%Y%m%d-%H%M%S")  # "20260217-143000"
topic_clean = topic.upper()[:20].replace(" ", "_")  # "AUTHENTICATION"

bridge_token = f"BRIDGE_{time_part}_{topic_clean}"
# Result: "BRIDGE_20260217-143000_AUTHENTICATION"
```

### Example Checksum Validation Failure
```log
WARNING: Checksum mismatch for handoff checkpoint abc-123
Expected: sha256:a1b2c3d4e5f6...
Actual:   sha256:x9y8z7w6v5u4...
Handoff data may be corrupted. Using best-effort restoration.
Task: implement-feature-x
Terminal: terminal_1
```

---

## END OF REVIEW BUNDLE

This review bundle provides comprehensive context for the handoff package, including architecture, components, design decisions, known issues, and integration points. Use this document to understand the system before making changes or for LLM question-answering about the handoff package.

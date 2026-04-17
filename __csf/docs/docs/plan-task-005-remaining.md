# TASK-005: Per-Terminal State Directories - Remaining Implementation

**Created**: 2026-03-14
**Phase**: Phase 1-3 Completion
**Estimated Time**: 2-4 hours

## Overview

Complete the migration of remaining hooks to use the new terminal-scoped state directory structure established in TASK-005 foundation. This includes updating intent_extractor.py and session_data_retention.py to use state_paths.py utilities, creating a migration script for legacy state files, and implementing comprehensive testing.

## Architecture

**Module Structure**:
```
P:/.claude/hooks/
├── __lib/
│   ├── state_paths.py          # Foundation utilities (✅ complete)
│   └── hook_base.py             # Centralized get_terminal_id() (✅ complete)
├── UserPromptSubmit_modules/
│   ├── skill_enforcer.py       # ✅ Migrated (commit db569bb89d)
│   └── intent_extractor.py     # ⏳ To migrate
├── session_data_retention.py    # ⏳ To migrate
└── scripts/
    └── migrate_state_files.py    # ⏳ To create
```

**New State Directory Structure**:
```
.claude/state/
├── terminals/              # Terminal-scoped (persists across sessions)
│   ├── {terminal_id}/
│   │   ├── pending_command_intent.json
│   │   ├── intent_state.json
│   │   └── [terminal-scoped state files]
├── sessions/                # Session-scoped (unique per session)
│   ├── {session_id}/
│   │   └── [session-scoped state files]
└── shared/                   # Global state (all terminals/sessions)
    └── [shared state files]
```

## Data Flow

### Hook State File Usage Flow

```
Hook Execution
    ↓
Get Terminal ID (get_terminal_id from hook_base.py)
    ↓
Determine State Scope:
  - Terminal-scoped: persists across sessions in same terminal
  - Session-scoped: unique per CC session
  - Shared: global across all terminals/sessions
    ↓
Get State Path (state_paths.py utilities)
  - get_terminal_state_path(terminal_id, filename)
  - get_session_state_path(session_id, filename)
  - get_shared_state_path(filename)
    ↓
Read/Write State File
```

### Migration Flow

```
Legacy State Files (.claude/state/*.json)
    ↓
Migration Script Scans & Classifies
    ↓
Determines New Location:
  - Terminal-scoped: terminals/{terminal_id}/{filename}
  - Session-scoped: sessions/{session_id}/{filename}
  - Shared: shared/{filename}
    ↓
Copies to New Location (migrate_legacy_state_file)
    ↓
Verifies Migration Success
    ↓
Cleanup Legacy Files (cleanup_legacy_state_file)
```

## Error Handling

**Migration Errors**:
- **File copy failure**: Log error, skip file, continue with next file
- **Permission denied**: Log warning, skip file, continue
- **Disk full**: HALT migration, report error to user
- **Corrupted state file**: Log warning, skip file, continue

**Runtime Errors**:
- **Missing terminal_id**: Graceful degradation to global state
- **Invalid session_id**: Use fallback "unknown" session ID
- **State file write failure**: Retry with exponential backoff (3 attempts max)
- **Directory creation failure**: Fallback to temp directory (TEMP environment variable)

## Test Strategy

### Unit Tests (Phase 5: TDD)

1. **intent_extractor.py migration tests**:
   - Test intent state file uses session-scoped path
   - Test legacy file cleanup on read
   - Test backward compatibility during transition

2. **session_data_retention.py migration tests**:
   - Test cleanup operations use new state paths
   - Test legacy file detection and cleanup
   - Test terminal-scoped and session-scoped separation

3. **Migration script tests**:
   - Test legacy file detection (finds all patterns)
   - Test classification logic (terminal/session/shared)
   - Test migration success (file copied correctly)
   - Test cleanup safety (original file preserved if copy fails)

### Integration Tests (Phase 6: TEST)

1. **Single terminal operations**:
   - Create terminal state files
   - Verify hooks read/write correctly
   - Verify cleanup works

2. **Multiple concurrent terminals**:
   - Simulate 3 terminals operating simultaneously
   - Verify no cross-terminal contamination
   - Verify each terminal has isolated state

3. **Session isolation**:
   - Create session-scoped state files
   - Verify session isolation works
   - Verify cleanup respects session boundaries

4. **Migration rollback safety**:
   - Test migration with simulated errors
   - Verify original files preserved on failure
   - Test rollback and re-migration

## Standards Compliance

**Python Standards** (`//p`):
- Use type hints for all function signatures
- Follow PEP 8 formatting (ruff linting)
- Use pathlib.Path for all file operations (no os.path)
- Add docstrings to all public functions
- Use f-strings for string formatting
- Apply ruff auto-fix for linting issues

**Testing Standards**:
- pytest for test framework
- Coverage threshold: 80%+ for new code
- Mock external dependencies (file system, environment)
- Fixture-based test setup/teardown
- Descriptive test names (test_<function>_<scenario>)

**Error Handling Standards**:
- Never fail silently - log all errors
- Use specific exception types (OSError, PermissionError, etc.)
- Graceful degradation when terminal_id unavailable
- Retry with exponential backoff for transient failures

## Ramifications

**Impact on Existing Code**:
- **Breaking changes**: None during transition period (dual-path compatibility)
- **Performance**: Minimal impact (Path operations are fast, <10ms per directory creation)
- **Memory**: Negligible increase (Path objects, no large data structures)
- **Disk space**: Moderate increase (new directory structure, but cleanup removes old files)

**Migration Considerations**:
- **Transition period**: Dual-path support (old + new paths) during migration
- **Backward compatibility**: Legacy files cleaned up gradually, not forced
- **Rollback plan**: If migration fails, old code still works with legacy paths
- **Data loss risk**: LOW - migration copies files first, deletes only after success verification

**Multi-Terminal Implications**:
- **True isolation**: Each terminal has its own state subdirectory
- **No collisions**: Multiple terminals can operate simultaneously safely
- **Cleanup safety**: Each terminal's cleanup doesn't affect others
- **Scalability**: Supports unlimited concurrent terminals

## Pre-Mortem Analysis

**Failure Mode 1: Data Corruption During Migration**
- **Root Cause**: Concurrent write operations during file copy
- **Prevention**: Migration script is read-only for source files, copies before cleanup
- **Test**: Migration test with concurrent hook operations running

**Failure Mode 2: Terminal ID Collision**
- **Root Cause**: Two terminals generate same terminal_id
- **Prevention**: Centralized get_terminal_id() with 5-priority detection, caching
- **Test**: Concurrent terminal test with 3+ terminals

**Failure Mode 3: Legacy Files Not Cleaned Up**
- **Root Cause**: Cleanup logic only runs during write operations, not on startup
- **Prevention**: Migration script proactively cleans up legacy files
- **Test**: Verify legacy file count decreases after migration

**Failure Mode 4: Session State Leaks**
- **Root Cause**: Session-scoped state files not cleaned up after session end
- **Prevention**: SessionEnd hooks already cleanup session data; extend for new paths
- **Test**: Session isolation test verifies cleanup after session end

**Observability Planning**:
- **Metrics**: Number of terminal subdirectories, disk usage trends
- **Logs**: Migration script logs all operations with success/failure
- **Alerts**: No automated alerts planned (manual verification sufficient)
- **Diagnosis**: Check .claude/state/terminals/ directory count and size

## Execution Plan

### Task 1: Update intent_extractor.py (30 min)
1. Import state_paths utilities (get_session_state_path)
2. Replace INTENT_STATE_FILE with session-scoped path
3. Update file read/write operations
4. Add legacy file cleanup on read
5. Test with single terminal

### Task 2: Update session_data_retention.py (45 min)
1. Import state_paths utilities
2. Update STATE_DIR references to use new structure
3. Update cleanup logic for terminal-scoped and session-scoped paths
4. Test cleanup operations
5. Verify legacy file cleanup works

### Task 3: Create migration script (45 min)
1. Create `.claude/hooks/scripts/migrate_state_files.py`
2. Implement legacy file scanning (glob patterns for old filenames)
3. Implement classification logic (terminal/session/shared)
4. Implement migration with verification
5. Implement cleanup with safety checks
6. Add command-line interface (dry-run mode, verbose mode)

### Task 4: Integration testing (60 min)
1. Single terminal test (basic operations)
2. Multiple concurrent terminals test (3 terminals)
3. Session isolation test (session boundaries)
4. Migration rollback safety test (error handling)
5. Backward compatibility test (dual-path support)

### Task 5: Documentation updates (15 min)
1. Update task-005-foundation-summary.md
2. Update multi-terminal-architecture.md
3. Add migration script documentation
4. Update task status to complete

## Success Criteria

- [ ] intent_extractor.py uses session-scoped state paths
- [ ] session_data_retention.py uses terminal/session-scoped state paths
- [ ] Migration script created and tested
- [ ] All tests pass (unit + integration)
- [ ] Documentation updated
- [ ] Git commit with all changes
- [ ] TASK-005 marked complete

## Risk Assessment

**Medium Risk** - Changes touch core hook state management
- **Mitigation**: Dual-path compatibility during transition period
- **Rollback**: Old code paths still work if migration fails
- **Testing**: Comprehensive integration tests before commit

**Estimated Completion Time**: 2-4 hours

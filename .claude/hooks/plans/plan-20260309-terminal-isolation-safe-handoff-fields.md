# Implementation Plan: Terminal-Isolation-Safe Handoff Fields

## 1. Problem Statement

**Current Situation:**
The handoff system successfully captures and restores session state across compaction events, but it lacks terminal-isolation-safe project-level context that would be valuable for session continuation. Currently, handoff data focuses on session-specific information (task, files, next steps) but doesn't capture:

1. **Project state**: Git branch, uncommitted changes, dependency versions
2. **Test outcomes**: Test results, coverage percentages
3. **Architectural decisions**: Project-level constraints and assumptions
4. **User-intent data**: Pending questions, clarification needs

**Why This Matters:**
When a session is restored, the AI agent lacks awareness of:
- Whether there are uncommitted changes that might affect implementation
- If dependencies have conflicts or version issues
- What test coverage looks like (are we breaking tests?)
- Architectural constraints already established
- Questions the user wanted to answer

**Terminal Isolation Constraint:**
Critical requirement: Any new fields MUST be terminal-isolation-safe. This means:
- Data must be project-level, not terminal-specific
- No terminal-attached state (e.g., running processes, open files)
- No cross-terminal contamination risk
- Must be safe to restore in ANY terminal working on the same project

## 2. Context Analysis

### Current Handoff Architecture

**Storage Location:**
```
.claude/state/handoff/{terminal_id}_handoff.json
```

**Data Structure (`handoff_internal`):**
```python
{
    "session_info": {
        "session_id": str,
        "terminal_id": str,
        "captured_at": ISO timestamp,
        "session_type": str,  # debug, feature, refactor, etc.
        "emoji": str
    },
    "task": {
        "name": str,
        "user_message": str,
        "canonical_goal": str,
        "progress_pct": int,
        "blocker": dict | None
    },
    "context": {
        "active_files": list[str],
        "primary_files_with_roles": list[dict],
        "pending_operations": list[dict],
        "visual_context": list[dict],
        "skill_invocations": list[dict]
    },
    "continuation": {
        "next_steps": list[dict],
        "decisions": list[dict],
        "do_not_revisit": list[dict]
    },
    "transcript_path": str
}
```

### Terminal Isolation History

**Previous Behavior (REMOVED):**
- Cross-terminal fallback was implemented to restore from the most recent handoff across all terminals
- This caused context confusion when multiple terminals worked on different tasks
- **Removed in SessionStart line 399**: "Cross-terminal fallback has been removed to prevent context confusion"

**Current Behavior:**
- Each terminal has its own handoff file
- SessionStart ONLY loads handoff from matching `terminal_id`
- If no handoff found for that terminal, starts fresh session
- Terminal ID validation prevents path traversal and security issues (handoff_files.py:94-106)

### Cross-Terminal Fallback History

**Evidence from code:**
```python
# SessionStart line 398-400
# If no handoff found for this terminal, start fresh (no cross-terminal fallback)
# Cross-terminal fallback has been removed to prevent context confusion
if not handoff_data:
    logger.info(f"No handoff found for terminal '{terminal_id}' - starting fresh session")
```

**Why it was removed:**
- Concurrent sessions in different terminals would contaminate each other's context
- Terminal A working on feature X would get Terminal B's handoff for debugging Y
- Causes agent confusion and incorrect task restoration

## 3. Existing Implementation Discovery

### Key Files Analyzed

**1. HandoffFileStorage** (`P:/packages/handoff/src/handoff/hooks/__lib/handoff_files.py`)
- Lines 94-106: Terminal ID validation (path traversal, null bytes, absolute paths)
- Lines 108-162: `save_handoff()` - atomic write with file locking
- Lines 164-213: `load_handoff()` - loads with terminal_id mismatch detection
- Lines 189-196: **Terminal ID match verification** - rejects handoff if terminal_id doesn't match

**2. PreCompact Handoff Capture** (`P:/packages/handoff/src/handoff/hooks/PreCompact_handoff_capture.py`)
- Lines 911-939: `handoff_internal` structure definition
- Lines 941-969: `validate_handoff_internal()` - critical vs advisory validation
- Lines 1031-1042: File-based storage using `HandoffFileStorage`

**3. SessionStart Handoff Restore** (`P:/packages/handoff/src/handoff/hooks/SessionStart_handoff_restore.py`)
- Lines 42-266: `build_quick_reference()` - quality-aware restoration message
- Lines 284-346: `find_most_recent_handoff()` - **NO LONGER USED** (cross-terminal fallback removed)
- Lines 398-405: Fresh session start (no cross-terminal fallback)
- Lines 521-526: Planning session blocker detection

**4. HandoffStore** (`P:/packages/handoff/src/handoff/hooks/__lib/handoff_store.py`)
- Lines 787-863: `build_handoff_data()` - assembles complete handoff structure
- Lines 865-979: `create_continue_session_task()` - task tracker integration

### Current Validation Patterns

**Terminal ID Validation** (handoff_files.py:94-106):
```python
def _validate_terminal_id(self, terminal_id: str) -> None:
    if not terminal_id or not terminal_id.strip():
        raise ValueError("terminal_id cannot be empty or whitespace-only")
    if '\x00' in terminal_id:
        raise ValueError(f"terminal_id cannot contain null bytes")
    if '..' in terminal_id or terminal_id.startswith('./'):
        raise ValueError(f"terminal_id cannot contain path traversal sequences")
    if terminal_id.startswith('/') or terminal_id.startswith('\\'):
        raise ValueError(f"terminal_id cannot be an absolute path")
```

**Checksum Validation** (handoff_store.py:695-748):
- SHA256 checksum computed from `handoff_internal` only
- Ensures data integrity across serialization
- Platform-independent (sorted keys, stable JSON encoding)

## 4. Test Discovery

### Existing Test Infrastructure

**Integration Tests:**
- `tests/test_handoff_integration.py` - Full compaction/restoration cycle with real data
- `tests/test_integration_e2e.py` - End-to-end operational verification
- `tests/test_backward_compatibility.py` - Legacy format handling

**Unit Tests:**
- `tests/test_deterministic_checksums.py` - Checksum computation
- `tests/test_canonical_goal_extraction.py` - Goal normalization
- `tests/test_restoration_message.py` - QUICK REFERENCE formatting

**Verification Scripts:**
- `tests/run_operational_verification.py` - Production-style testing
- `verify_phase1.py` - Phase 1 implementation verification

### Terminal Isolation Testing

**Current Coverage:**
- ✅ Terminal ID validation (null bytes, path traversal, absolute paths)
- ✅ Terminal ID mismatch rejection in `load_handoff()`
- ✅ Per-terminal handoff file isolation
- ❌ **MISSING**: Cross-terminal contamination prevention test
- ❌ **MISSING**: Assertion that restored terminal_id matches session terminal_id

**Test Gap Analysis:**
No test currently verifies that SessionStart rejects handoff data with mismatched terminal_id. This is a critical safety check that should be added.

## 5. Proposed Solution

### Architecture Decision: Expand `handoff_internal` Structure

**Approach:**
Add new optional sections to `handoff_internal` for terminal-isolation-safe project-level context. These fields are:

1. **Optional** (missing = not captured, not an error)
2. **Terminal-agnostic** (safe to restore in any terminal)
3. **Project-level** (describe the project, not the terminal session)
4. **Filtered** (exclude terminal-specific artifacts)

### Schema Changes

**New Fields in `handoff_internal`:**

```python
handoff_internal = {
    # ... existing sections ...

    # NEW: Project state (terminal-isolation-safe)
    "project_state": {
        "git": {
            "branch": str,  # Current branch name
            "has_uncommitted_changes": bool,
            "modified_files": list[str],  # Paths to modified files
            "last_commit": {
                "hash": str,
                "message": str,
                "author": str,
                "timestamp": str
            }
        },
        "dependencies": {
            "package_manager": str,  # "npm", "pip", "poetry", etc.
            "installed_packages": list[dict],  # [{"name": "pkg", "version": "1.0.0"}]
            "conflicts": list[str],  # Known dependency conflicts
            "outdated": list[str]  # Outdated package names
        },
        "tests": {
            "last_run": ISO timestamp | None,
            "pass_count": int,
            "fail_count": int,
            "coverage_percentage": float | None,
            "test_file_paths": list[str]  # Locations of test files
        }
    },

    # NEW: Architectural context (terminal-isolation-safe)
    "architecture": {
        "assumptions": list[str],  # Project-level assumptions (e.g., "PostgreSQL is required")
        "constraints": list[str],  # Technical constraints (e.g., "Must support Python 3.9+")
        "decisions": list[dict],  # Settled architectural decisions
        "pending_questions": list[str]  # Questions user wants answered
    },

    # NEW: Recent errors (FILTERED - project-level only)
    "recent_errors": [
        {
            "error": str,
            "file": str | None,  # Project file where error occurred
            "solution": str | None,
            "timestamp": ISO timestamp
        }
    ]
}
```

### Field Safety Analysis

**SAFE Fields (terminal-isolation-safe):**
- Git state: Project repository state, same across terminals
- Dependencies: Project dependencies, same across terminals
- Test results: Project test outcomes, same across terminals
- Assumptions/constraints: Project architecture, same across terminals
- Project-level errors: Import errors, runtime errors in project code

**UNSAFE Fields (terminal-specific - DO NOT CAPTURE):**
- Running processes (terminal-attached)
- Open file descriptors (terminal-attached)
- Shell environment variables (may be terminal-specific)
- Temporary files (terminal-specific)
- Tool operation state (Edit validation failures, etc.)

### Filtering Rules for `recent_errors`

**INCLUDE (project-level errors):**
- Import errors: `ImportError: No module named 'foo'`
- Runtime errors: `AttributeError: 'Bar' object has no attribute 'baz'`
- Test failures: `AssertionError: Expected 200, got 500`
- Type errors: `TypeError: unsupported operand type(s)`

**EXCLUDE (terminal-specific errors):**
- Edit operation failures: `Edit operation failed: file changed`
- File read errors: `File not found: /tmp/terminal-specific`
- Hook errors: `PreCompact hook failed`
- Tool timeout: `Command timed out after 30s`

**Filtering Implementation:**
```python
def is_project_level_error(error_message: str) -> bool:
    """Check if error is project-level (safe) or terminal-specific (unsafe)."""
    unsafe_patterns = [
        r"Edit operation failed",
        r"hook failed",
        r"Command timed out",
        r"File not found: /tmp/",
        r"terminal",
        r"tty",
    ]

    return not any(re.search(pattern, error_message, re.I) for pattern in unsafe_patterns)
```

## 6. Implementation Plan

### PHASE 1: Safe Fields (Implement Now)

**Task 1.1: Add Git State Capture**
- File: `src/handoff/hooks/__lib/git_state.py` (NEW)
- Functions:
  ```python
  def capture_git_state(project_root: Path) -> dict | None:
      """Capture git repository state (branch, uncommitted changes, last commit).

      Returns:
          dict with keys: branch, has_uncommitted_changes, modified_files, last_commit
          Returns None if not a git repo or on error.

      Raises:
          subprocess.TimeoutExpired: If git command exceeds 2s timeout
      """

  def _get_git_branch(project_root: Path) -> str | None:
      """Get current branch name using 'git rev-parse --abbrev-ref HEAD'."""

  def _get_uncommitted_changes(project_root: Path) -> list[str]:
      """Get list of modified files using 'git status --porcelain'."""

  def _get_last_commit(project_root: Path) -> dict | None:
      """Get last commit info using 'git log -1 --format=%H|%s|%an|%ct'."""
  ```
- Path validation: Validate `project_root` is within allowed paths before subprocess calls
- Error handling: Return None if not a git repo, log warnings, handle subprocess.TimeoutExpired
- Integration: Call from PreCompact after handoff_internal validation (parallel with other captures)

**Task 1.2: Add Dependency State Capture**
- File: `src/handoff/hooks/__lib/dependency_state.py` (NEW)
- Functions:
  - `capture_dependency_state(project_root: Path) -> dict | None`
  - `_detect_package_manager() -> str | None` (npm, pip, poetry, cargo)
  - `_get_installed_packages() -> list[dict]`
  - `_check_conflicts() -> list[str]`
- Error handling: Return None if no package manager detected
- Integration: Call from PreCompact after git_state capture

**Task 1.3: Add Test Results Capture**
- File: `src/handoff/hooks/__lib/test_state.py` (NEW)
- Functions:
  - `capture_test_state(project_root: Path) -> dict | None`
  - `_find_test_files() -> list[str]`
  - `_parse_test_results() -> dict | None` (pytest, jest, cargo test)
  - `_get_coverage() -> float | None`
- Error handling: Return None if no tests found or results unavailable
- Integration: Call from PreCompact after dependency_state capture

**Task 1.4: Add Assumptions/Constraints Capture**
- File: `src/handoff/hooks/__lib/architecture_capture.py` (NEW)
- Functions:
  - `capture_architectural_context(project_root: Path) -> dict | None`
  - `_scan_architecture_docs() -> list[dict]` (ADR files, ARCHITECTURE.md)
  - `_extract_assumptions() -> list[str]`
  - `_extract_constraints() -> list[str]`
- Sources: `docs/adr/`, `ARCHITECTURE.md`, `docs/constraints.md`
- Error handling: Return empty dict if no docs found
- Integration: Call from PreCompact after test_state capture

**Task 1.5: Add Pending Questions Capture**
- File: `src/handoff/hooks/__lib/user_intent.py` (NEW)
- Functions:
  ```python
  def capture_pending_questions(transcript: str) -> list[str]:
      """Extract pending user questions from transcript.

      Returns:
          List of question strings found in transcript.
          Returns empty list if no questions found.
      """

  def _extract_questions_from_transcript(transcript: str) -> list[str]:
      """Pattern matching for questions: Look for "?", "clarify", "confirm", "verify"."""
  ```
- Error handling: Return empty list if no questions found
- Integration: Call from PreCompact using transcript parameter

**Task 1.5.1: Add Capture Caching** (NEW)
- File: `src/handoff/hooks/__lib/capture_cache.py` (NEW)
- Purpose: Cache capture results with 5-minute TTL to avoid redundant subprocess calls
- Functions:
  ```python
  class CaptureCache:
      """Cache capture results with 5-minute TTL to reduce subprocess overhead.

      Cache key: f"{capture_type}:{project_root}:{path_hash}"
      TTL: 300 seconds (5 minutes)
      """

      def get(self, key: str) -> dict | None:
          """Get cached result if available and not expired."""

      def set(self, key: str, value: dict) -> None:
          """Cache capture result with current timestamp."""

      def clear(self) -> None:
          """Clear all cached entries (useful for testing)."""
  ```
- Integration: Wrap capture calls in CaptureCache in PreCompact
- Error handling: Cache failures don't block capture (fallback to direct call)

**Task 1.6: Update handoff_internal Structure**
- File: `src/handoff/hooks/PreCompact_handoff_capture.py`
- Lines: After line 939 (before validation)
- Changes:
  ```python
  handoff_internal = {
      # ... existing sections ...

      # NEW: Terminal-isolation-safe project state
      "project_state": {
          "git": capture_git_state(project_root),
          "dependencies": capture_dependency_state(project_root),
          "tests": capture_test_state(project_root)
      },
      "architecture": capture_architectural_context(project_root),
      "pending_questions": capture_pending_questions(transcript)
  }
  ```

**Task 1.7: Update Restoration Message**
- File: `src/handoff/hooks/SessionStart_handoff_restore.py`
- Function: `build_quick_reference()`
- Add sections after line 158 (after Current Focus):
  ```python
  # Project State
  lines.append("Project State")
  project_state = handoff_internal.get("project_state", {})
  if project_state.get("git", {}).get("branch"):
      lines.append(f"- Git branch: {project_state['git']['branch']}")
  if project_state.get("git", {}).get("has_uncommitted_changes"):
      lines.append(f"- ⚠️ Uncommitted changes: {len(project_state['git']['modified_files'])} files")
  # ... etc
  ```

**Task 1.8: Implement Parallel Capture Execution** (NEW)
- File: `src/handoff/hooks/__lib/parallel_capture.py` (NEW)
- Purpose: Execute capture modules in parallel to reduce PreCompact overhead
- Functions:
  ```python
  import asyncio
  from concurrent.futures import ThreadPoolExecutor, as_completed

  def capture_all_parallel(project_root: Path, transcript: str) -> dict:
      """Execute all capture modules in parallel (git, deps, test, architecture).

      Uses ThreadPoolExecutor to run subprocess-based captures concurrently.
      Reduces PreCompact overhead from sequential (2s + 2s + 2s = 6s) to parallel (~2s max).

      Returns:
          dict with keys: git_state, dependency_state, test_state, architectural_context
      Each value is the result from respective capture function (can be None).
      """
  ```
- Thread pool: Use 4 threads (one per capture module)
- Timeout: 2s per capture (matches risk mitigation requirement)
- Integration: Replace sequential capture calls in PreCompact with `capture_all_parallel()`
- Error handling: Individual capture failures don't block other captures (graceful degradation per module)

### PHASE 2: Conditional Field (Add with Filtering)

**Task 2.1: Add Recent Errors Capture**
- File: `src/handoff/hooks/__lib/error_capture.py` (NEW)
- Functions:
  - `capture_recent_errors(transcript: str, project_root: Path) -> list[dict]`
  - `_extract_errors_from_transcript() -> list[dict]`
  - `is_project_level_error(error_msg: str) -> bool` (FILTERING FUNCTION)
- Filtering: Use `is_project_level_error()` to exclude terminal-specific errors
- Limit: Keep last 5 project-level errors
- Error handling: Return empty list if no errors found
- Integration: Call from PreCompact after pending_questions capture

**Task 2.2: Add Error Filtering Tests**
- File: `tests/test_error_filtering.py` (NEW)
- Test cases:
  - `test_include_import_error()` → Should include
  - `test_exclude_edit_operation_failed()` → Should exclude
  - `test_exclude_hook_failed()` → Should exclude
  - `test_include_runtime_error()` → Should include
  - `test_exclude_timeout_error()` → Should exclude

**Task 2.3: Update handoff_internal with Errors**
- File: `src/handoff/hooks/PreCompact_handoff_capture.py`
- Add to handoff_internal:
  ```python
  "recent_errors": capture_recent_errors(transcript, project_root)
  ```

**Task 2.4: Update Restoration Message with Errors**
- File: `src/handoff/hooks/SessionStart_handoff_restore.py`
- Add section before "Strict Instructions":
  ```python
  lines.append("Recent Errors")
  recent_errors = handoff_internal.get("recent_errors", [])
  if recent_errors:
      for err in recent_errors[:3]:
          lines.append(f"- {err['error'][:80]}")
  else:
      lines.append("- No recent project-level errors")
  ```

### PHASE 3: Verification (Safety Check)

**Task 3.1: Add Terminal ID Assertion**
- File: `src/handoff/hooks/SessionStart_handoff_restore.py`
- Location: After line 394 (after `handoff_data = file_storage.load_handoff()`)
- Code:
  ```python
  # CRITICAL: Verify terminal_id match to prevent cross-terminal contamination
  handoff_internal = handoff_data.get("handoff_internal", {})
  saved_terminal_id = handoff_internal.get("session_info", {}).get("terminal_id")

  if saved_terminal_id and saved_terminal_id != terminal_id:
      logger.error(
          f"[SessionStart] TERMINAL ID MISMATCH: "
          f"expected={terminal_id}, got={saved_terminal_id}. "
          f"Rejecting handoff to prevent cross-terminal contamination."
      )
      output = {
          "decision": "allow",
          "reason": "Terminal ID mismatch - starting fresh to prevent context contamination"
      }
      print(json.dumps(output, indent=2))
      sys.exit(0)

  logger.info(f"[SessionStart] Terminal ID verified: {terminal_id}")
  ```

**Task 3.2: Add Terminal Isolation Tests**
- File: `tests/test_terminal_isolation.py` (NEW)
- Test cases:
  ```python
  def test_terminal_id_mismatch_rejection():
      """Verify that SessionStart rejects handoff with mismatched terminal_id."""
      # Create handoff for terminal_A
      # Try to restore in terminal_B
      # Assert that handoff is rejected
      # Assert that fresh session starts

  def test_no_cross_terminal_contamination():
      """Verify that terminals don't share handoff data."""
      # Create handoff for terminal_A
      # Create handoff for terminal_B
      # Assert that each terminal loads its own handoff
      # Assert that terminal_A doesn't see terminal_B's data

  def test_git_worktree_isolation():
      """Verify that git worktrees are handled correctly."""
      # Create git worktree
      # Create handoff in worktree
      # Assert that handoff loads correctly
      # Assert that git state captures worktree-specific branch

  def test_monorepo_multiple_package_files():
      """Verify that monorepos with multiple package.json/pyproject.toml files are handled."""
      # Create monorepo with packages/app1/pyproject.toml
      # Create monorepo with packages/app2/pyproject.toml
      # Assert that dependency_state detects both packages
      # Assert that capture doesn't fail with multiple files

  def test_project_without_tests():
      """Verify graceful degradation when project has no test framework."""
      # Create project without tests directory
      # Run test_state capture
      # Assert that capture returns None (graceful degradation)
      # Assert that handoff still succeeds without test data

  def test_submodule_handling():
      """Verify that git submodules are handled gracefully."""
      # Create repo with git submodule
      # Run git_state capture
      # Assert that capture returns None or handles submodule (log warning)
      # Assert that handoff doesn't fail
  ```

### Implementation Build Sequence

**Order of Operations:**

1. **Foundation First** (Tasks 1.1-1.5, 1.5.1, 1.8)
   - Create all capture modules with proper error handling
   - Each module returns None on failure (graceful degradation)
   - Write unit tests for each capture module
   - Implement caching layer (5-minute TTL)
   - Implement parallel capture execution (reduce overhead from 6s → 2s)

2. **Integration Second** (Tasks 1.6-1.7)
   - Update PreCompact to call capture modules (use parallel execution)
   - Update SessionStart to display new fields
   - Test full compaction/restoration cycle

3. **Filtering Third** (Tasks 2.1-2.4)
   - Implement error filtering with test coverage
   - Add recent_errors to handoff_internal
   - Update restoration message

4. **Verification Last** (Tasks 3.1-3.3)
   - Add terminal_id assertion in SessionStart
   - Write isolation tests
   - Verify no regressions

## 7. Risks, Success Criteria, Dependencies

### Risks and Mitigations

**Risk 1: Performance Degradation**
- **Risk**: Capturing git/deps/test state on every compaction could slow down hooks
- **Mitigation**:
  - Cache results with 5-minute TTL
  - Use subprocess with timeout (2s max per capture)
  - Make all captures async/non-blocking
  - Add telemetry to monitor capture duration

**Risk 2: Cross-Terminal Contamination**
- **Risk**: New fields might accidentally include terminal-specific data
- **Mitigation**:
  - Add `is_terminal_isolation_safe()` review function
  - Code review checklist for all new fields
  - Automated tests for cross-terminal contamination
  - Terminal ID assertion in SessionStart (Task 3.1)

**Risk 3: Handoff Size Bloat**
- **Risk**: New fields could exceed 500KB limit (QUAL-009)
- **Mitigation**:
  - Limit test results to last 5 test files
  - Limit dependencies to top 20 packages
  - Limit errors to last 5 entries
  - Truncate long strings with markers

**Risk 4: False Positive Errors**
- **Risk**: Error filtering might include terminal-specific errors
- **Mitigation**:
  - Conservative filtering (exclude uncertain cases)
  - Whitelist approach for project-level errors
  - Test coverage for common error patterns
  - Manual review of filtered errors in logs

**Risk 5: Git/Dependency Detection Failures**
- **Risk**: Capture modules might fail in edge cases (submodules, monorepos)
- **Mitigation**:
  - Return None on failure (graceful degradation)
  - Log warnings for detection failures
  - Don't block handoff on capture failures
  - Add fallback for common edge cases

### Success Criteria

**Functional Requirements:**
- ✅ All 5 safe fields capture successfully in 95%+ of projects
- ✅ Restoration message displays new fields without breaking existing format
- ✅ Terminal ID assertion prevents cross-terminal contamination
- ✅ Error filtering excludes 100% of terminal-specific errors
- ✅ Handoff size stays under 500KB limit (QUAL-009)

**Non-Functional Requirements:**
- ✅ PreCompact execution time increases by < 2 seconds
- ✅ SessionStart execution time increases by < 1 second
- ✅ Test coverage remains ≥ 95%
- ✅ No regressions in existing handoff functionality

**Quality Metrics:**
- ✅ All new modules have unit tests with ≥ 90% coverage
- ✅ Integration tests pass for all 3 phases
- ✅ Manual testing with 3+ diverse projects (Python, JS, Rust)
- ✅ Code review approved for terminal isolation safety

### Dependencies

**Required Components:**
1. **Git CLI** - Must be installed and accessible in PATH
2. **Package manager CLIs** - npm, pip, poetry, or cargo (auto-detected)
3. **Test frameworks** - pytest, jest, or cargo test (auto-detected)

**External Libraries:**
- **No new dependencies** - Use subprocess for CLI commands
- **Optional**: `gitpython` if available (faster git parsing)
- **Optional**: `toml` for pyproject.toml parsing

**Code Dependencies:**
- `handoff.hooks.__lib.handoff_files.py` - File storage
- `handoff.hooks.__lib.project_root.py` - Project root detection
- `handoff.hooks.__lib.transcript.py` - Transcript parsing

**Integration Points:**
- **PreCompact hook** - Calls capture modules after handoff_internal validation
- **SessionStart hook** - Displays new fields in restoration message
- **HandoffFileStorage** - Saves enlarged handoff_internal structure
- **Validation system** - Optional fields don't trigger validation errors

### Rollback Strategy

**If Phase 1 Fails:**
1. Remove new capture modules from `src/handoff/hooks/__lib/`
2. Revert PreCompact changes (remove capture calls)
3. Revert SessionStart changes (remove new sections)
4. Delete unit tests for new modules
5. Keep existing handoff functionality intact

**If Phase 2 Fails:**
1. Remove `error_capture.py` module
2. Remove `recent_errors` from handoff_internal
3. Remove error section from restoration message
4. Keep Phase 1 fields (safe, isolated)

**If Phase 3 Fails:**
1. Remove terminal_id assertion (log warning instead)
2. Keep Phase 1 and Phase 2 fields
3. Document terminal_id mismatch as known limitation

**Rollback Testing:**
- Verify that handoffs without new fields still restore correctly
- Verify that old handoffs are backward compatible
- Verify that missing optional fields don't break validation

### Measurable Success Criteria

**Quantitative Metrics:**
1. **Capture Success Rate**: ≥ 95% of projects capture at least 3/5 safe fields
2. **Performance Overhead**: < 2s added to PreCompact, < 1s to SessionStart
3. **Test Coverage**: ≥ 95% for new code (matches existing coverage)
4. **Handoff Size**: < 400KB average (under 500KB limit)
5. **Terminal Isolation**: 0 cross-terminal contamination events in testing

**Qualitative Metrics:**
1. **User Feedback**: Restoration message is more helpful with project context
2. **Code Review**: Approved for terminal isolation safety
3. **Manual Testing**: Successful in 3+ diverse project types
4. **Documentation**: Complete implementation guide and examples

**Definition of Done:**
- ✅ All 3 phases implemented and tested
- ✅ Integration tests pass with real compaction data
- ✅ Terminal isolation verified with cross-terminal tests
- ✅ Performance impact measured and acceptable
- ✅ Documentation updated with new fields
- ✅ Rollback plan tested and validated
- ✅ Code review approved

---

## Appendix: File Creation Checklist

### New Files to Create

**Phase 1:**
- `src/handoff/hooks/__lib/git_state.py` (120 lines)
- `src/handoff/hooks/__lib/dependency_state.py` (150 lines)
- `src/handoff/hooks/__lib/test_state.py` (140 lines)
- `src/handoff/hooks/__lib/architecture_capture.py` (100 lines)
- `src/handoff/hooks/__lib/user_intent.py` (80 lines)
- `src/handoff/hooks/__lib/capture_cache.py` (70 lines) - NEW
- `src/handoff/hooks/__lib/parallel_capture.py` (80 lines) - NEW
- `tests/test_git_state.py` (80 lines)
- `tests/test_dependency_state.py` (90 lines)
- `tests/test_test_state.py` (85 lines)
- `tests/test_architecture_capture.py` (70 lines)
- `tests/test_user_intent.py` (60 lines)

**Phase 2:**
- `src/handoff/hooks/__lib/error_capture.py` (110 lines)
- `tests/test_error_filtering.py` (95 lines)

**Phase 3:**
- `tests/test_terminal_isolation.py` (180 lines) - Updated with 5 edge case tests

**Total: 15 new files, ~1,650 lines of code** (updated from 13 files, 1,400 lines)

### Files to Modify

**Phase 1:**
- `src/handoff/hooks/PreCompact_handoff_capture.py` (+30 lines)
- `src/handoff/hooks/SessionStart_handoff_restore.py` (+50 lines)

**Phase 2:**
- `src/handoff/hooks/PreCompact_handoff_capture.py` (+15 lines)
- `src/handoff/hooks/SessionStart_handoff_restore.py` (+20 lines)

**Phase 3:**
- `src/handoff/hooks/SessionStart_handoff_restore.py` (+25 lines)

**Total: 3 modified files, +140 lines**

### Documentation Updates

- `ARCHITECTURE.md` - Add new fields to data model section
- `docs/api_reference.md` - Document new capture functions
- `HANDOFF_STRUCTURE.md` - Update handoff_internal schema
- `CHANGELOG.md` - Add v0.3.0 entry with new features

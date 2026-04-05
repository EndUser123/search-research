# Phase 1 Critique: GTO v3.1 Skill

## Brief Intent Summary

GTO v3.1 implements a self-verifying completion enforcement system for gap/analysis tasks. It adds binary assertions (A1-A5) that check for artifact existence, health scores, viability status, git validity, and state accessibility. A Stop hook blocks session exit until all assertions pass, ensuring users cannot claim "done" without verifiable artifacts. A PostToolUseFailure hook classifies and logs failures for recovery context. The system uses terminal-isolated state directories to prevent concurrent access issues.

## Logical Gaps & Inconsistencies

1. **Assertion A3 "Implicit Pass" Contradiction**: A3 checks for "PASS" status or absence of "FAIL" in viability files. If no viability file exists, it returns True with "implicit pass" message. This contradicts the strict verification intent — a missing viability artifact should FAIL, not pass. The comment at line 104 says "implicit pass" but this is a loophole.

2. **Hook Registration Mismatch**: SKILL.md registers `gto_failure_capture.py` as PostToolUseFailure hook for "Bash" tool matcher (line 14), but the hook code (line 128) checks if "gto" is in command lowercase. This creates a narrow detection window — only Bash commands containing "gto" trigger classification. Non-Bash failures or typos slip through.

3. **Environment Variable Dependency Chain**: `gto_verify.sh` defaults TERMINAL_ID to "default" (line 11) if unset, but the assertions script requires it as required argument (line 143). If TERMINAL_ID is genuinely missing, the hook passes a default value that creates a fake state directory (`.evidence/gto-state-default/`) that doesn't correspond to any actual terminal, bypassing isolation.

4. **Health Score Extraction Fragility**: A2 (line 72-78) looks for lines containing "%" AND ("score" OR "health" in lowercase). This requires exact keyword co-occurrence. If the health artifact says "Health: 85%" (missing "score") or "Percentage: 75%" (missing "health"), the assertion fails despite valid data.

5. **Artifact Time Window Arbitrariness**: A1 uses a 1-hour window (line 60: `timedelta(hours=1)`) to check for "recent" artifacts. This threshold is arbitrary with no justification — why 1 hour and not 30 minutes or 4 hours? A legitimate GTO run that takes 90 minutes would fail A1 despite producing correct artifacts.

## Hidden Assumptions & Fragile Dependencies

6. **Assumes Unix-style Path Handling**: `gto_verify.sh` uses hardcoded paths (`.claude/skills/gto/evals/gto-assertions.py`) without quoting. On Windows with spaces in paths, or if the skill is moved to a non-standard location, this breaks. The script also lacks error handling for missing Python executable.

7. **Assumes Bash Availability**: The Stop hook is a shell script (`.sh`), which assumes bash is available and executable. On Windows terminals using PowerShell or CMD, this hook will fail silently or not run at all, creating a verification bypass.

8. **Assumes State Directory Structure**: Assertions check `.evidence/gto-state-{terminal_id}/` (line 149) but never verify this structure matches what `state_manager.py` actually creates. If `StateManager` changes its path scheme, assertions break without detection.

9. **Assumes JSON Parseable Hook Input**: `gto_failure_capture.py` (line 121) does `json.load(sys.stdin)` without error handling. If Claude Code passes malformed JSON or the hook is invoked outside expected context, the entire hook crashes and logs nothing.

10. **Assumes File System Atomicity**: The atomic write pattern in `state_manager.py` (lines 302-315) assumes `os.replace()` is atomic. This is true on POSIX but not guaranteed on all filesystems (e.g., network drives, some Windows configurations). The code treats cross-platform atomicity as universal truth.

## Missing Obvious Actions / Best Practices

11. **No Integration Tests**: The implementation has unit tests (`tests/test_lib.py`, `tests/test_orchestrator.py`) but no integration tests that verify the complete hook → assertions → block flow. A test should simulate a GTO run, check assertions fail, then pass after artifacts created.

12. **No Cleanup of Failure Pattern Logs**: `gto_failure_capture.py` creates files in `.claude/failure-patterns/` (line 94-98) but never implements cleanup or rotation. Long-running sessions accumulate thousands of stale failure logs with no size limit or expiration.

13. **No Verification of Hook Registration**: The YAML frontmatter declares hooks but there's no automated verification that these hooks are actually registered and firing. A skill could claim to have verification hooks that don't actually run.

14. **No Graceful Degradation Documentation**: If the Stop hook fails (Python not found, script errors), the session exits without verification. There's no documented fallback procedure or warning message to users about this bypass scenario.

15. **No Assertion State Caching**: Each run of `gto-assertions.py` re-scans all files and re-parses all content. For large projects with many artifacts, this is wasteful. No incremental state or caching exists.

## Risks and Edge Cases

16. **Terminal ID Collision on Restart**: The terminal ID fallback (line 125 in `state_manager.py`) uses `{hostname}-{pid}`. If a terminal restarts and reuses the same PID (likely on Windows), it inherits the previous terminal's state, creating cross-session contamination.

17. **Stop Hook Bypass via Force Exit**: If the user force-closes the terminal or Claude Code crashes, the Stop hook never runs. Users can bypass verification by killing the process, making the enforcement incomplete.

18. **Concurrent GTO Runs in Same Terminal**: If a user somehow triggers two GTO analyses in the same terminal simultaneously (e.g., background process), both write to the same state directory. The atomic write prevents file corruption but doesn't prevent assertion race conditions — one run's artifacts could satisfy another run's verification.

19. **Git Submodule Detection**: A4 checks for `.git/HEAD` (line 118) but doesn't distinguish between main repos and submodules. Running GTO on a submodule directory passes A4 but may fail subsequent checks that assume full repo context.

20. **Symlink Attacks**: The state manager resolves `project_root` with `.resolve()` (line 94) but doesn't validate the result stays within expected bounds. A symlink to `/etc/passwd` or sensitive directories could cause state files to be written outside the project.

## Concrete Recommendations

**Priority 1 (Fix Verification Loopholes):**
- Change A3 to FAIL if no viability file exists (remove "implicit pass")
- Add explicit check for viability artifact existence before content check
- Validate assertion time window against actual GTO runtime, not arbitrary 1-hour

**Priority 2 (Fix Hook Robustness):**
- Add try/except around `json.load(sys.stdin)` in failure capture hook
- Quote all paths in `gto_verify.sh` and add Python existence check
- Add PowerShell fallback script for Windows terminals

**Priority 3 (Add Missing Validation):**
- Create integration test: run GTO → verify assertions block → create artifacts → verify assertions pass
- Add hook registration verification script that checks actual hook files
- Implement failure pattern log rotation (keep last 100, delete older)

**Priority 4 (Fix Assumptions):**
- Document non-POSIX filesystem limitations for atomic writes
- Add terminal ID collision detection (check if state file predates process start)
- Add bounds checking for symlinked project_root paths

**Priority 5 (Improve Maintainability):**
- Externalize magic numbers (1-hour window, 500-char truncation) to config
- Add assertion result caching for repeated runs
- Create "bypass detected" warning when hook doesn't fire

## Open Questions / Unknowns

1. **Hook Execution Order**: When Stop hook blocks (exit 2), do PostToolUseFailure hooks still run? The failure capture hook might never fire if Stop hook terminates first.

2. **Terminal ID Source**: Where does `$TERMINAL_ID` or `$CLAUDE_TERMINAL_ID` come from? Is this set by Claude Code or user-provided? If it's missing, the default "default" value breaks isolation.

3. **Assertion Runtime**: What's the expected runtime of `gto-assertions.py` on large projects? If it takes >5 seconds, users might kill it before seeing results.

4. **Cross-Platform Hook Support**: Does Claude Code execute `.sh` hooks on Windows? If yes, via WSL or Git Bash? If no, the Stop hook never runs on Windows.

5. **State Directory Cleanup**: Who cleans up old terminal state directories (`.evidence/gto-state-*`)? The implementation creates them indefinitely with no expiration or GC mechanism.

6. **(Speculative) Hook Invocation Context**: Does Claude pass full command output or just exit codes to PostToolUseFailure hooks? The failure capture assumes `error` field contains stderr, but this isn't documented.

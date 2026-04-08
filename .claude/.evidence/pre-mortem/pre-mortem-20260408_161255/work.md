Test Hang Prevention Implementation - Phase 1, 2, 3 Complete

Components:
1. PreToolUse_pytest_timeout_guard.py - Blocks pytest without --timeout flag
   - Enforces --timeout flag on pytest commands
   - Exit code 2 when blocking
   - Bypass: --allow-no-timeout

2. PreToolUse_git_commit_test_gate.py - Blocks git commit if tests fail
   - Checks for changed test files before commit
   - Runs pytest on changed files
   - Exit code 2 when blocking
   - Bypass: --allow-failing-tests

3. Tests:
   - tests/test_pretooluse_pytest_timeout_guard.py (14 tests)
   - tests/test_pretooluse_git_commit_test_gate.py (11 tests)
   - All 25 tests passing

4. Registration:
   - Both hooks registered in PreToolUse.py Bash TOOL_HOOKS
   - Env vars configured in settings.json (block mode by default)

Key fixes during implementation:
- Runtime env var evaluation (not module load time)
- Exit code propagation for blocking
- Test file detection specificity (avoid matching pytest as test file)
- Exemption check order (exemptions before git command check)

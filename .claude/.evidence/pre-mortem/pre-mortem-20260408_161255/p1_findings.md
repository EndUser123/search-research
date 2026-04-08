# Phase 1: Triage + Specialist Findings

## Triage Classification
**hook** — PreToolUse hook scripts for test hang prevention (pytest timeout guard and git commit test gate)

## Dispatched Specialists
- **adversarial-security**: Command injection, path validation, subprocess handling, DoS vulnerabilities
- **adversarial-compliance**: Hook registration, exit code protocol, env var handling
- **adversarial-io-validation**: Subprocess calls, git operations, I/O safety
- **adversarial-logic**: Conditional logic, exemption patterns, edge cases

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities (command injection, path traversal, DoS)

**Key findings:**
- [HIGH] Command injection via subprocess without input sanitization (PreToolUse_git_commit_test_gate.py:76-128)
- [HIGH] Path traversal vulnerability in test file detection (PreToolUse_git_commit_test_gate.py:95-100)
- [MEDIUM] Regex injection via unvalidated command input (PreToolUse_pytest_timeout_guard.py:62-67)
- [MEDIUM] Missing timeout exception handling creates DoS vulnerability (PreToolUse_git_commit_test_gate.py:137-138)
- [MEDIUM] TOCTOU vulnerability between file list retrieval and test execution (PreToolUse_git_commit_test_gate.py:199-203)
- [LOW] Information disclosure through error messages (PreToolUse_git_commit_test_gate.py:136)

### adversarial-compliance
**Domain:** Hook system compliance (registration, exit codes, env vars)

**Key findings:**
No significant issues found in [domain]. Implementation follows hook system specifications for registration, exit codes, and environment variable handling. All 25 tests passing with proper documentation.

### adversarial-io-validation
**Domain:** I/O safety (subprocess calls, git operations, timeouts)

**Key findings:**
- [HIGH] Subprocess pytest call has timeout=60 but no check=True validation (PreToolUse_git_commit_test_gate.py:123-128)
- [MEDIUM] No git repository validation before git commands (PreToolUse_git_commit_test_gate.py:76-83)
- [MEDIUM] Test failure detection uses truncation that could hide messages (PreToolUse_git_commit_test_gate.py:134)
- [MEDIUM] Hook entry point uses sys.stdin.read() without timeout (PreToolUse_pytest_timeout_guard.py:149-156)
- [LOW] Subprocess timeout lacks explicit TimeoutExpired handling (PreToolUse_git_commit_test_gate.py:76-82)
- [LOW] Timeout flag detection edge case (PreToolUse_pytest_timeout_guard.py:78-80)
- [LOW] Test subprocess call doesn't verify hook file exists (test_pretooluse_git_commit_test_gate.py:145-152)

### adversarial-logic
**Domain:** Conditional logic, exemption patterns, edge cases

**Key findings:**
- [MEDIUM] Duplicated test file filtering logic with different implementations (PreToolUse_git_commit_test_gate.py:95-107)
- [LOW] Overly complex string manipulation for test_ prefix detection (PreToolUse_git_commit_test_gate.py:98-99)
- [LOW] Short flag '-t' detection only checks first two positional arguments (PreToolUse_pytest_timeout_guard.py:80)

## Consolidated Findings

### Critical Security Issues
1.1. [HIGH] (source: adversarial-security) Command injection via subprocess without input sanitization — File paths from git diff are passed directly to subprocess.run() without sanitization. Git allows filenames with shell metacharacters and path traversal sequences. (PreToolUse_git_commit_test_gate.py:76-128)

1.2. [HIGH] (source: adversarial-security) Path traversal vulnerability in test file detection — Test file detection uses simple string matching '/tests/' in path without normalization, allowing bypass with path traversal like '....//' or mixed separators. (PreToolUse_git_commit_test_gate.py:95-100)

### Logical Gaps & Inconsistencies
2.1. [MEDIUM] (source: adversarial-logic) Duplicated test file filtering logic — Lines 95-100 and 102-107 filter the same changed_files list with different logic. If developer modifies one filter but not the other, behavior becomes inconsistent. (PreToolUse_git_commit_test_gate.py:95-107)

2.2. [MEDIUM] (source: adversarial-io-validation) Test failure detection truncation — stderr[-500:] could hide 'no tests collected' message if it appears earlier in stderr, causing false positive test failure. (PreToolUse_git_commit_test_gate.py:134)

2.3. [LOW] (source: adversarial-logic) Overly complex string manipulation — Line 98 uses obscure bool-to-int conversion for string concatenation. (PreToolUse_git_commit_test_gate.py:98-99)

### Hidden Assumptions & Fragile Dependencies
3.1. [MEDIUM] (source: adversarial-security) TOCTOU vulnerability — Race condition between getting changed test files and running tests. Attacker could substitute malicious files after validation but before execution. (PreToolUse_git_commit_test_gate.py:199-203)

3.2. [MEDIUM] (source: adversarial-io-validation) No git repo validation — Hook assumes git is available and cwd is in a repo. Fail-open behavior allows commits when git subprocess fails silently. (PreToolUse_git_commit_test_gate.py:76-83)

3.3. [LOW] (source: adversarial-io-validation) Short flag detection limitation — '-t' flag only checked at positions 1-2, could miss flags at position 3+. (PreToolUse_pytest_timeout_guard.py:80)

### Missing Obvious Actions / Best Practices
4.1. [HIGH] (source: adversarial-security) Missing timeout exception handling — subprocess.run() timeout doesn't kill child process group, leaving zombie processes that could be exploited for DoS. (PreToolUse_git_commit_test_gate.py:137-138)

4.2. [MEDIUM] (source: adversarial-io-validation) stdin read without timeout — sys.stdin.read() in hook entry point could block indefinitely if pipe is closed, creating session hang. (PreToolUse_pytest_timeout_guard.py:149-156)

4.3. [MEDIUM] (source: adversarial-security) Regex injection risk — re.search() on unvalidated user command could allow ReDoS or bypass via crafted regex characters. (PreToolUse_pytest_timeout_guard.py:62-67)

4.4. [MEDIUM] (source: adversarial-io-validation) No pytest binary validation — subprocess.run(['python', '-m', 'pytest']) relies on returncode but doesn't validate pytest exists. (PreToolUse_git_commit_test_gate.py:123-128)

4.5. [LOW] (source: adversarial-security) Information disclosure — Full stderr output in error messages exposes internal paths and system details. (PreToolUse_git_commit_test_gate.py:136)

### Risks and Edge Cases
5.1. [HIGH] (source: adversarial-security) Command injection exploit path — Malicious file names committed to repo could inject arbitrary commands via subprocess.run() with unsanitized paths.

5.2. [HIGH] (source: adversarial-security) Path traversal exploit path — Attacker could use '../' sequences to escape intended directory scope and test/execute files outside repo.

5.3. [MEDIUM] (source: adversarial-io-validation) Session hang via stdin — sys.stdin.read() without timeout blocks forever if pipe closed, defeating the entire test hang prevention purpose.

5.4. [MEDIUM] (source: adversarial-security) DoS via zombie processes — Repeatedly triggering test gate timeout could accumulate zombie pytest processes, exhausting system resources.

5.5. [LOW] (source: adversarial-io-validation) Network filesystem timeout — git diff timeout of 10s may be insufficient on slow filesystems, causing hook crash with unhandled TimeoutExpired.

### Concrete Recommendations
6.1. [HIGH] Sanitize file paths before subprocess — Implement _sanitize_filename() that rejects path traversal (..), shell metacharacters, newlines, null bytes. Use allowlist for safe characters only.

6.2. [HIGH] Use pathlib.Path for robust path handling — Normalize all paths before validation. Resolve parent directory references and validate final path is within expected bounds.

6.3. [HIGH] Kill child process groups on timeout — Use creationflags=CREATE_NEW_PROCESS_GROUP (Windows) or start_new_session=True (Unix). In TimeoutExpired handler, kill entire process group.

6.4. [MEDIUM] Consolidate duplicated test file filtering — Define test file patterns once and apply in single filter pass. Return filtered result directly.

6.5. [MEDIUM] Validate file hashes at execution time — Calculate SHA256 hash of files at check time, verify at execution time to prevent TOCTOU. Alternative: use git blob IDs.

6.6. [MEDIUM] Add git repository validation — Check if Path('.git').exists() before running git diff subprocess to validate repo assumption explicitly.

6.7. [MEDIUM] Check 'no tests collected' before truncation — Check full stderr for 'no tests collected' message before applying [-500:] truncation.

6.8. [MEDIUM] Add framework-level stdin timeout — Hook framework should provide timeout guarantees for sys.stdin.read(). All hooks currently vulnerable to stdin hangs.

6.9. [LOW] Simplify test_ prefix detection — Replace obscure bool-to-int concatenation with os.path.basename(f).startswith('test_').

6.10. [LOW] Document '-t' flag limitation — Either check all arguments for '-t' or document that positions 1-2 check is intentional for common usage.

6.11. [LOW] Sanitize error messages — Create _sanitize_error_output() to redact sensitive paths and environment details from user-facing messages.

### Open Questions / Unknowns
7.1. [LOW] (source: adversarial-io-validation) Framework-level stdin timeout — Does Claude Code hook runner provide timeout guarantees for stdin reads? If not, all hooks using sys.stdin.read() are vulnerable.

7.2. [LOW] (source: adversarial-io-validation) Network filesystem support — Should git_diff_timeout be configurable via environment variable for slow/network filesystems?

7.3. [LOW] (source: adversarial-io-validation) Pytest availability logging — Should 'pytest not available' fail-open be logged to diagnostics for observability?

7.4. [LOW] (source: adversarial-logic) Additional test file patterns — Are there other test patterns (Test*.py, *Test*.py) that should be included in test file detection?

7.5. [LOW] (source: adversarial-logic) Duplicated filtering intent — Is duplicated test file filtering in git_commit_test_gate.py intentional (defense in depth) or an oversight?

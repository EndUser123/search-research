## Triage Classification
hook + code — On-error stale bytecode cleanup retry logic in hook_importer.py (lines 160-245)

## Dispatched Specialists
- adversarial-logic: Exception variable shadowing in retry path, exception handling correctness
- adversarial-io-validation: Path validation, TOCTOU in _clear_hook_bytecode, file operations
- adversarial-testing: Test coverage gaps, missing scenarios for retry logic
- adversarial-quality: Tech debt, maintainability, error messages

## Specialist Findings Summary

### adversarial-logic
**Domain:** Exception handling and control flow
**Key findings:**
- [HIGH] (LOGIC-001) Exception variable shadowing: inner `except Exception` at line 233 rebinds `e` from outer scope. The `_log_anomaly` at line 238 logs the retry error, not the original ImportError that triggered bytecode cleanup.
- [MEDIUM] (LOGIC-002) Bare except at line 233 swallows retry exception. Final `raise ImportError` at line 245 raises the retry exception (via shadowed `e`), not the original ImportError.

### adversarial-io-validation
**Domain:** Path validation and file operations
**Key findings:**
- [LOW] (IO-001) TOCTOU in _clear_hook_bytecode: exists() check at line 167 followed by iteration. If __pycache__ deleted between check and loop, FileNotFoundError could be raised.
- [LOW] (IO-002) Retry path doesn't re-validate hook_path existence before second spec_from_file_location call.

### adversarial-testing
**Domain:** Test coverage
**Key findings:**
- [HIGH] (TEST-001) test_retry_on_import_error_after_bytecode_cleanup doesn't actually test retry — only verifies cleanup NOT called on success, never triggers retry path
- [HIGH] (TEST-002) Missing test for double-failure (both initial and retry fail) — no verification that failed module is NOT cached
- [MEDIUM] (TEST-003) test_load_hook_catches_syntax_error_and_retries has ambiguous pass/fail
- [MEDIUM] (TEST-004) Missing test for OSError during unlink in _clear_hook_bytecode
- [MEDIUM] (TEST-005) test_isinstance_check_prevents_retry_for_oserror only tests Python builtin, not hook code path
- [MEDIUM] (TEST-006) Missing test for ImportError on retry attempt itself
- [LOW] (TEST-007) No negative cache test after failed load
- [LOW] (TEST-008) No concurrent threading test for _cache race conditions

### adversarial-quality
**Domain:** Code quality and maintainability
**Key findings:**
- No major issues — code is clean and well-structured
- Consider adding docstring noting retry behavior for future maintainers

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (adversarial-logic) — Exception variable shadowing: `e` rebind in inner except at line 233 causes _log_anomaly to log wrong error (retry error instead of original) (hook_importer.py:233)
1.2. [MEDIUM] (adversarial-logic) — Bare except swallows retry exception; final raise propagates wrong error to caller (hook_importer.py:233,245)

### Hidden Assumptions & Fragile Dependencies
2.1. [LOW] (adversarial-io-validation) — TOCTOU race in _clear_hook_bytecode: exists() check before iteration could race with directory deletion (hook_importer.py:167-171)
2.2. [LOW] (adversarial-io-validation) — Retry assumes hook_path still valid without re-checking existence (hook_importer.py:219-220)
2.3. [LOW] (adversarial-testing) — No thread safety on _cache or sys.modules writes; concurrent load could corrupt state (hook_importer.py:188)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (adversarial-testing) — test_retry_on_import_error_after_bytecode_cleanup doesn't exercise the retry path it claims to test (test_hook_bytecode_cleanup.py:100)
3.2. [HIGH] (adversarial-testing) — No test verifying failed load doesn't populate _cache (test_hook_bytecode_cleanup.py)

### Risks and Edge Cases
4.1. [MEDIUM] (adversarial-logic) — If retry fails with different error type than initial, root cause is masked in logs and propagated error
4.2. [LOW] (adversarial-io-validation) — If __pycache__ deleted concurrently during _clear_hook_bytecode, cleanup could raise FileNotFoundError (caught by outer except, prevents retry)

### Concrete Recommendations
5.1. [HIGH] Capture original exception: Store `original_error = e` after line 209, use `original_error` in _log_anomaly at line 238 (hook_importer.py:209,238)
5.2. [HIGH] Add test: verify module NOT in _cache after failed double-attempt load (test_hook_bytecode_cleanup.py)
5.3. [HIGH] Fix test_retry_on_import_error_after_bytecode_cleanup to actually trigger retry path (test_hook_bytecode_cleanup.py:100)
5.4. [MEDIUM] Restructure retry exception handling: use named exception variable `retry_error` at line 233, chain exceptions properly (hook_importer.py:233,245)
5.5. [MEDIUM] Add test: OSError during unlink doesn't prevent retry (test_hook_bytecode_cleanup.py)
5.6. [MEDIUM] Add test: concurrent load_hook from multiple threads doesn't corrupt _cache (test_hook_bytecode_cleanup.py)

### Open Questions / Unknowns
6.1. [LOW] (adversarial-io-validation) — Is multi-process concurrent access to same hooks directory a real scenario? (source: adversarial-io-validation)
6.2. [LOW] (adversarial-quality) — Should _clear_hook_bytecode log when it cleans files? Currently silent success. (source: adversarial-quality)

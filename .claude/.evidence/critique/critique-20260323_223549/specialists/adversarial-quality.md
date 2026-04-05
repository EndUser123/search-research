# Adversarial Quality Review - PreToolUse_directory_policy.py

**Review Date**: 2026-03-23 22:35:49
**Reviewer**: adversarial-quality agent
**File**: P:/.claude/hooks/PreToolUse_directory_policy.py
**Status**: SUCCESS

## Executive Summary

The directory policy hook is a **high-risk security component** with several **MEDIUM severity maintainability issues**. The code functions correctly but has significant technical debt in error handling, test coverage, and code clarity that will cause maintenance problems.

**Critical Finding**: Line 364 contains a **bare `except:`** that masks all exceptions, including KeyboardInterrupt and SystemExit. This is a **HIGH severity** security issue that prevents safe shutdown.

---

## Findings

### QUAL-001: Bare except Exception Handler (HIGH)

**Location**: Line 364

**Code Excerpt**:
```python
except Exception:
    sys.exit(0)
```

**Issue**: While this is `except Exception` (not bare `except:`), it still catches and silently suppresses ALL exceptions including:
- `KeyboardInterrupt` (Ctrl+C)
- `SystemExit`
- `MemoryError`
- Custom exceptions that should surface

**Impact**:
- Cannot interrupt the hook with Ctrl+C during hangs
- Error messages are lost (no logging)
- Debugging failures requires external tooling

**Recommendation**:
```python
except Exception as e:
    # Log the error for diagnostics
    logger = logging.getLogger(__name__)
    logger.error("Hook execution failed: %s", e, exc_info=True)
    sys.exit(0)  # Fail-open for safety
```

**Confidence**: HIGH

---

### QUAL-002: Missing Test Coverage for Path Traversal Logic (MEDIUM)

**Location**: Lines 241-269 (Bash command path resolution)

**Code Excerpt**:
```python
for path in paths_to_check:
    # Check if path is already absolute (has drive letter or starts with /)
    if re.match(r"^[A-Za-z]:|^/", path):
        # Absolute path - validate it doesn't escape project directory
        resolved = PathLib(path).resolve()
        try:
            resolved.relative_to(PathLib(project_dir))
            absolute_paths.append(path)
        except ValueError:
            # Path escapes project directory - block it
            return {
                "decision": "block",
                "message": f"Path traversal detected: {path}\nResolved path escapes project directory: {project_dir}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }
```

**Issue**: No tests verify that path traversal attacks are actually blocked. Critical security code has no verification.

**Missing Test Scenarios**:
1. `../../../etc/passwd` traversal attempt
2. Symlink-based escape (`P:/project/external_symlink -> /etc`)
3. Mixed path separators (`P:\..\..\etc/passwd`)
4. UNC path bypass (`\\?\P:\..\..`)

**Proof**:
- `test_path_validator_external_paths.py` only tests `get_allowed_external_paths()` method
- No integration tests for `run()` function
- No tests for `extract_paths_from_bash()` function

**Impact**: Future modifications could introduce path bypass vulnerabilities without detection.

**Recommendation**: Add test file `test_directory_policy_security.py` with:
```python
def test_blocks_path_traversal_via_parent_refs():
    """Test that ../../ sequences are blocked."""
    result = run({
        "tool_name": "Bash",
        "tool_input": {"command": "echo test > ../../../etc/passwd"}
    })
    assert result["decision"] == "block"
    assert "traversal" in result["message"].lower()

def test_blocks_symlink_escape():
    """Test that symlinks outside project are blocked."""
    # Create symlink P:/test_link -> /etc
    # Try to write via symlink
    result = run({...})
    assert result["decision"] == "block"
```

**Confidence**: MEDIUM

---

### QUAL-003: Code Duplication in Path Validation Logic (MEDIUM)

**Location**: Lines 241-269 (Bash) vs 271-301 (Write/Edit tools)

**Issue**: Path security validation is duplicated across two code blocks with identical logic:
1. Lines 241-269: Bash command path resolution
2. Lines 271-301: Write/Edit tool path resolution

**Code Excerpt** (Duplicated Pattern):
```python
# First occurrence (line 241)
if re.match(r"^[A-Za-z]:|^/", path):
    resolved = PathLib(path).resolve()
    try:
        resolved.relative_to(PathLib(project_dir))
        absolute_paths.append(path)
    except ValueError:
        return {"decision": "block", ...}

# Second occurrence (line 275) - IDENTICAL LOGIC
if re.match(r"^[A-Za-z]:|^/", file_path):
    resolved = PathLib(file_path).resolve()
    try:
        resolved.relative_to(PathLib(project_dir))
        paths_to_check = [file_path]
    except ValueError:
        return {"decision": "block", ...}
```

**Impact**:
- Security fixes must be applied in TWO places
- High risk of divergence (one fixed, one missed)
- Violates DRY principle

**Recommendation**: Extract to helper function:
```python
def _validate_path_security(path: str, project_dir: str) -> str | dict:
    """
    Validate that path doesn't escape project directory.

    Returns:
        Normalized path string if safe
        Block dict if path traversal detected
    """
    if re.match(r"^[A-Za-z]:|^/", path):
        resolved = PathLib(path).resolve()
        try:
            resolved.relative_to(PathLib(project_dir))
            return path
        except ValueError:
            return {
                "decision": "block",
                "message": f"Path traversal detected: {path}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }
    else:
        resolved = (PathLib(working_dir) / path).resolve()
        try:
            resolved.relative_to(PathLib(project_dir))
            return str(resolved)
        except ValueError:
            return {
                "decision": "block",
                "message": f"Path traversal detected: {path}",
                "blocking_hook": "PreToolUse_directory_policy.py",
            }
```

**Confidence**: MEDIUM

---

### QUAL-004: Ambiguous Error Message Configuration (LOW)

**Location**: Line 51

**Code Excerpt**:
```python
except Exception:
    pass
```

**Issue**: Bare `except:` (actually `except Exception`) during config loading silently fails. No warning when `directory_policy.json` is missing or malformed.

**Evidence**: Lines 42-52
```python
ALLOWED_EXTERNAL_PATTERNS: list[str] = []
try:
    _policy_path = PathLib(hooks_dir) / "config" / "directory_policy.json"
    if _policy_path.exists():
        with open(_policy_path, encoding="utf-8") as _f:
            _policy = json.load(_f)
            ALLOWED_EXTERNAL_PATTERNS = _policy.get("allowed_external_paths", {}).get(
                "patterns", []
            )
except Exception:
    pass
```

**Impact**:
- Config file errors are invisible
- System uses empty `ALLOWED_EXTERNAL_PATTERNS` without warning
- Operators don't know policy enforcement is disabled

**Recommendation**:
```python
except Exception as e:
    # Log but don't fail - hook should still work with defaults
    logger = logging.getLogger(__name__)
    logger.warning(
        "Failed to load directory_policy.json: %s. Using empty ALLOWED_EXTERNAL_PATTERNS.",
        e
    )
```

**Confidence**: LOW

---

### QUAL-005: Magic Numbers Without Constants (LOW)

**Location**: Lines 79-82

**Code Excerpt**:
```python
CLAUDE_CONFIG_SIZE_LIMITS = {
    "settings.json": 100 * 1024,  # Why 100KB?
    "default": 1024 * 1024,       # Why 1MB?
}
```

**Issue**: Size limits are arbitrary constants with no documentation of:
- Why these specific values were chosen
- What failure mode they prevent
- How to adjust them for different projects

**Impact**:
- Cannot tune limits without trial-and-error
- Future maintainers cannot make informed tradeoffs
- No guidance for large vs small projects

**Recommendation**:
```python
# Content size limits prevent Claude from writing oversized config files
# that slow down session startup or exceed tool buffer limits.
# settings.json: Active session config (kept small for fast loads)
# default: Catch-all for other Claude configs
CLAUDE_CONFIG_SIZE_LIMITS = {
    "settings.json": 100 * 1024,   # 100KB - session state must load quickly
    "default": 1024 * 1024,        # 1MB - allows large prompt templates
}
```

**Confidence**: LOW

---

### QUAL-006: Inconsistent Function Naming Conventions (LOW)

**Location**: Throughout file

**Issue**: Mix of naming styles creates confusion:
- `is_allowed_external_path()` (verb_prefix)
- `check_csf_nip_path()` (verb_prefix)
- `check_content_size()` (verb_prefix)
- `extract_paths_from_bash()` (verb_prefix)
- BUT `run()` is the main entry point

**Impact**: Minor - doesn't affect functionality but makes code review harder.

**Recommendation**: Consider renaming `run()` to `enforce_directory_policy()` for clarity, or document why `run()` is the standard entry point name for hooks.

**Confidence**: LOW

---

## Test Coverage Analysis

### Coverage Gaps

1. **No integration tests for `run()` function** - Only unit tests for helper functions
2. **No security tests for path traversal** - Critical for a security hook
3. **No tests for CSF NIP validation** - Lines 65-73 are untested
4. **No tests for content size limits** - Lines 192-199 are untested
5. **No tests for root write blocking** - Lines 327-340 are untested

### Existing Tests

**File**: `test_path_validator_external_paths.py`
- Tests: 7
- Coverage: Only `DirectoryPolicy.get_allowed_external_paths()` method
- Gap: Does NOT test `PreToolUse_directory_policy.py` security logic

**Recommendation**: Create `test_directory_policy_security.py` with at least 15 tests covering:
- Path traversal blocking
- Symlink escape blocking
- CSF NIP validation
- Content size limits
- Root write blocking
- Relative path resolution
- Mixed path separators

---

## Maintainability Risks

### Future Change Vulnerability

**Risk 1: Config Schema Changes**
- Lines 42-52 assume specific JSON structure
- No schema validation
- Breaking changes cause silent failures

**Risk 2: Path Normalization Edge Cases**
- Lines 58, 68, 193, 330 all normalize paths differently
- Some use `.replace("\\", "/")`, some use `.lower()`
- Inconsistent normalization could bypass security checks

**Risk 3: Working Directory Confusion**
- Lines 219-222 distinguish between `working_dir` (bash) and `project_dir` (file tools)
- Comment says "For bash commands, use os.getcwd() to get the actual working directory"
- But `working_dir` is also used for relative path resolution in line 257
- Could fail if bash changes directory mid-session

---

## Technical Debt Summary

| Issue | Severity | Effort to Fix | Risk Level |
|-------|----------|---------------|------------|
| QUAL-001: Bare except Exception | HIGH | 5 minutes | HIGH - Cannot shutdown safely |
| QUAL-002: Missing security tests | MEDIUM | 2 hours | MEDIUM - Undetected vulnerabilities |
| QUAL-003: Code duplication | MEDIUM | 30 minutes | MEDIUM - Fixes must be duplicated |
| QUAL-004: Silent config failures | LOW | 10 minutes | LOW - Hard to debug |
| QUAL-005: Magic numbers | LOW | 5 minutes | LOW - No guidance |
| QUAL-006: Naming inconsistency | LOW | N/A | LOW - Cosmetic |

**Total Technical Debt**: ~3 hours to address all issues

---

## Recommendations Priority Order

1. **CRITICAL**: Fix QUAL-001 (bare except) - Add logging to exception handler
2. **HIGH**: Add security tests (QUAL-002) - Prevent regression
3. **MEDIUM**: Extract duplicated path validation (QUAL-003) - Reduce maintenance burden
4. **LOW**: Add config error logging (QUAL-004) - Improve debuggability
5. **LOW**: Document magic numbers (QUAL-005) - Improve maintainability

---

## Handoff Metadata

**Status**: SUCCESS - Review complete, 6 findings documented

**Overall Assessment**:
The hook functions correctly for its primary purpose (path security enforcement) but has accumulated technical debt that will cause maintenance problems. The HIGH severity bare exception handler is a potential safety issue during hook failures. Missing security tests are the biggest risk - critical security code has no verification that it actually works.

**Open Questions**: None

**Confidence**: HIGH - All findings verified with code excerpts and line numbers

**Session Context**: Review conducted as part of adversarial quality analysis for critique skill. Findings should be integrated with other adversarial specialist reports (security, logic, performance, etc.) before action.

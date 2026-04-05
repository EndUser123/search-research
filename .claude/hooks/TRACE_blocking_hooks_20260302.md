# TRACE Report: Critical Blocking Hooks

**Date**: 2026-03-02
**Scope**: PreToolUse blocking hooks (universal + tool-specific)
**Hooks traced**: 5 critical hooks
**Confidence**: Tier 1 (code inspection)

---

## Executive Summary

**FINDINGS:**
- **Logic Errors Found**: 3
- **Race Conditions Found**: 1
- **Case Sensitivity Issues**: 1
- **P2 Quality Issues**: 2

**CRITICAL ISSUES:**
1. ⚠️ **P0** - `path_validator.py` line 269: Case-sensitive path comparison on Windows
2. ⚠️ **P1** - `risk_tier_gate.py` lines 171-178: Race condition in cache deduplication
3. ⚠️ **P2** - `recursive_failure_detector.py` lines 152-154: Incomplete test exemption logic

---

## Hook #1: PreToolUse_path_validator.py

### Scenario Analysis

#### Happy Path: Safe file operation allowed
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Write tool with `file_path="P:/src/main.py"` | `tool_name="Write"`, `is_safe=True` | Allow | ✓ Valid path |
| 2 | Check consent via `check_claude_edit_consent()` | `has_consent=False` | Continue | No consent found |
| 3 | Return `None` (allow) | Result=None | ✅ ALLOW | Pass-through |

#### Error Path: Sensitive file blocked
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Write tool with `file_path="P:/.claude/hooks/CLAUDE.md"` | `is_safe=False`, `violation="CLAUDE_SENSITIVE_EDIT"` | Check consent | ⚠️ Sensitive |
| 2 | Check consent via `check_claude_edit_consent()` | `has_consent=False`, `canonical_path="P:/.claude/hooks/CLAUDE.md"` | Block | No consent |
| 3 | Return block decision | `decision="block"` | ❌ BLOCK | Correct |

#### Edge Case: Windows case sensitivity mismatch
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Write with `file_path="P:/.CLAUDE/..."` | `canonical_path="P:/.claude/..."` | Format hint | ❌ **BUG** |
| 2 | Line 269: `relative_hint = canonical_path.removeprefix("p:/.claude/")` | `canonical_path="P:/.claude/..."` | No removal! | 🔴 **FAIL** |
| 3 | Output: `"approve edit P:/.claude/hooks/CLAUDE.md"` | Case mismatch! | User sees wrong path | ❌ **CONFUSION** |

**❌ LOGIC ERROR #1: Case-sensitive removeprefix on Windows**

**Location:** `PreToolUse_path_validator.py` line 269

**Problem:**
```python
relative_hint = canonical_path.removeprefix("p:/.claude/")
```

Windows paths are case-insensitive. If `canonical_path` is `P:/.claude/...` (uppercase P), the `removeprefix("p:/.claude/")` won't remove anything because `removeprefix()` is case-sensitive.

**Impact:**
- User sees confusing approval message: "approve edit P:/.claude/hooks/CLAUDE.md"
- The hint should be relative: "approve edit hooks/CLAUDE.md"
- But with uppercase P, it shows full path instead

**Fix:**
```python
# Case-insensitive prefix removal on Windows
relative_hint = re.sub(r'^[pP]:/\.claude/', '', canonical_path)
```

---

## Hook #2: recursive_failure_detector.py

### Scenario Analysis

#### Happy Path: First attempt allowed
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Load failures | `failures=[]` | Continue | No prior failures |
| 2 | Compute command hash | `cmd_hash="abc123"` | Check count | ✓ Normalized |
| 3 | Count similar failures | `failure_count=0` | Allow | Below threshold |
| 4 | Return `{"allow": True}` | Result=allow | ✅ ALLOW | Pass-through |

#### Error Path: Catch-22 detected
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Load failures | `failures=[<2+ failures>]` | Check count | ⚠️ Pattern found |
| 2 | Count similar failures | `failure_count=2` | Check threshold | At limit |
| 3 | Generate prescriptive directive | `directive="Stop..."` | Block with guidance | ✓ Helpful |
| 4 | Return `{"block": True, "message": "..."}` | Result=block | ❌ BLOCK | Correct |

#### Edge Case: Test file exemption incomplete
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive MultiEdit with test files | `tool_name="MultiEdit"`, `file_path="__csf/src/cks/tests/test_storage.py"` | Check exemption | 🔴 **BUG** |
| 2 | Line 152: Check `if tool in ("Write", "Edit")` | `tool_name="MultiEdit"` | NOT in tuple | ❌ **FAIL** |
| 3 | Test files NOT exempted for MultiEdit | `is_test_file_operation=True` but check fails | ❌ **WRONG** | MultiEdit writes test files! |

**❌ LOGIC ERROR #2: Incomplete test exemption**

**Location:** `recursive_failure_detector.py` lines 152-154

**Problem:**
```python
# TEST FILE EXEMPTION: Allow test file operations without Catch-22 checking
if tool in ("Write", "Edit") and file_path:
    if is_test_file_operation(file_path):
        return {"allow": True}
```

This only exempts Write and Edit tools. But `MultiEdit` can also write to test files! And other tools like `NotebookEdit` are missing too.

**Impact:**
- Test file operations in MultiEdit subject to Catch-22 detection when they shouldn't be
- False blocking of legitimate test development

**Fix:**
```python
# Expand exemption to all mutation tools
_MUTATION_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
if tool in _MUTATION_TOOLS and file_path:
    if is_test_file_operation(file_path):
        return {"allow": True}
```

---

## Hook #3: PreToolUse_authorization_gate.py

### Scenario Analysis

#### Happy Path: Explicit authorization detected
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Bash with destructive command | `command="rm -rf node_modules"` | Check authorization | ⚠️ Destructive |
| 2 | Extract actual command | `actual_command="rm -rf node_modules"` | Check patterns | ✓ Extracted |
| 3 | Match destructive pattern | `pattern="rm\s+-rf?"` | Check user intent | ✓ Destructive |
| 4 | Get last user message | `last_msg="go ahead and delete it"` | Check patterns | ✓ Explicit |
| 5 | `has_explicit_authorization()` returns True | Allow | ✅ ALLOW | Correct |

#### Error Path: Confirmatory language blocked
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Bash with destructive command | `command="rm -rf node_modules"` | Check authorization | ⚠️ Destructive |
| 2 | Match destructive pattern | `pattern="rm\s+-rf?"` | Check user intent | ✓ Destructive |
| 3 | Get last user message | `last_msg="that's correct"` | Check patterns | Confirmatory |
| 4 | `is_confirmatory_only()` returns True | Block | ❌ BLOCK | Correct |

#### Edge Case: Python -c with subprocess
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Bash: `python -c "import subprocess; subprocess.run(['rm', '-rf', 'x'])"` | Extract Python code | ✓ Matched |
| 2 | Extract Python code: `"import subprocess; subprocess.run(['rm', '-rf', 'x'])"` | Check for subprocess | ⚠️ Has subprocess |
| 3 | `_contains_subprocess_call()` returns True | Return original command | ✓ Correct | Treated as shell command |

**✅ NO LOGIC ERRORS FOUND**

This hook correctly handles:
- Python -c wrappers (extracts code content)
- Subprocess detection (treats as shell command)
- Chained commands (checks each part)
- Shell comment removal (ignores commented text)

---

## Hook #4: PreToolUse_risk_tier_gate.py

### Scenario Analysis

#### Happy Path: Advisory shown once
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Bash: `git status` | `command="git status"` | Classify | ✓ ADVISORY |
| 2 | Check `data["shown_advisories"]` | `shown=set()` | Not shown yet | ✓ First time |
| 3 | Add to shown set | `shown.add(message)` | Return advisory | ✅ ADVISORY |
| 4 | Next call: `git status` | `message in shown` | Suppress | ✓ Deduped |

#### Error Path: Confirm tier blocks
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | Receive Bash: `git reset --hard HEAD` | `command="git reset --hard HEAD"` | Classify | ⚠️ CONFIRM |
| 2 | Get last user message | `last_msg="explain this command"` | No auth pattern | ❌ BLOCK |
| 3 | Return block decision | `decision="block"` | ✅ BLOCK | Correct |

#### Edge Case: Cache deduplication race condition
| Step | Operation | State/Variables | Decision | Notes |
|------|-----------|-----------------|----------|-------|
| 1 | First call: `git status` from terminal_A | `terminal_id="A"` | Cache miss | ✅ Show advisory |
| 2 | Set cache: `data["tier_checked_A_<session>"] = "ADVISORY"` | Cache written | ✅ Stored |
| 3 | Second call: `git status` from terminal_B | `terminal_id="B"` | Cache miss | 🔴 **RACE** |
| 4 | Cache key differs! | `tier_checked_B_<session>" != "tier_checked_A_<session>" | ✅ Show again | ⚠️ **DUPLICATE** |

**⚠️ RACE CONDITION #3: Cache deduplication fails across terminals**

**Location:** `PreToolUse_risk_tier_gate.py` lines 171-178

**Problem:**
```python
checked_key = f"tier_checked_{terminal_id}_{session_id}"
```

The cache key includes `terminal_id`, which means:
- Same command from different terminals → Different cache keys
- Advisory shown multiple times when user runs command from terminal A, then terminal B

**Impact:**
- Annoying duplicate advisories for multi-terminal workflows
- Doesn't break functionality, but reduces UX quality

**Severity:** P2 (minor UX issue)

**Fix Options:**
1. **Option A:** Remove `terminal_id` from cache key (session-based deduplication)
2. **Option B:** Make deduplication opt-in for multi-terminal users
3. **Option C:** Accept current behavior (advisories are idempotent anyway)

**Recommended:** Option A - Change cache key to session-only:
```python
checked_key = f"tier_checked_{session_id}"  # Terminal-agnostic
```

---

## Hook #5: PreToolUse_destructive_git_guard.py

### Status: ✅ FIXED

**Previous Issue:** Exited with code 1 but no stderr output → "No stderr output" error

**Fix Applied:** Now prints JSON to stdout and exits with code 2 (proper PreToolUse blocking protocol)

**Verification:**
```bash
# Test destructive command
echo '{"command":"git reset --hard HEAD"}' | python .claude/hooks/PreToolUse_destructive_git_guard.py
# Output: {"continue": false, "reason": "..."}
# Exit code: 2
```

---

## Summary of Issues

| # | Hook | Issue | Severity | Location | Fix Status |
|---|------|-------|----------|----------|------------|
| 1 | path_validator.py | Case-sensitive removeprefix on Windows | P0 | Line 269 | ⏳ PENDING |
| 2 | recursive_failure_detector.py | Incomplete test exemption for MultiEdit | P1 | Lines 152-154 | ⏳ PENDING |
| 3 | risk_tier_gate.py | Cache deduplication race condition | P2 | Lines 171-178 | ⏳ PENDING |
| 4 | destructive_git_guard.py | "No stderr output" error | P1 | Line 168 | ✅ FIXED |

---

## Recommendations

### Priority 1: Fix path_validator case sensitivity
```python
# Line 269: Change from:
relative_hint = canonical_path.removeprefix("p:/.claude/")

# To:
relative_hint = re.sub(r'^[pP]:/\.claude/', '', canonical_path)
```

### Priority 2: Fix test exemption logic
```python
# Lines 152-154: Change from:
if tool in ("Write", "Edit") and file_path:

# To:
_MUTATION_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
if tool in _MUTATION_TOOLS and file_path:
```

### Priority 3: Fix cache deduplication (optional)
```python
# Line 171: Change from:
checked_key = f"tier_checked_{terminal_id}_{session_id}"

# To:
checked_key = f"tier_checked_{session_id}"
```

---

## TRACE Results

**Overall Status:** ⚠️ 3 logic errors found (1 P0, 1 P1, 1 P2)

**Quality Assessment:**
- ✅ Resource management: No leaks found
- ✅ Exception handling: Proper fallbacks
- ⚠️ Logic correctness: 3 errors found
- ✅ Race conditions: 1 minor issue (P2)
- ⚠️ Windows compatibility: Case sensitivity issue (P0)

**Recommendation:** Fix P0 and P1 issues before next deployment. P2 can be deferred.

---

## Evidence

| Finding | Evidence Type | Confidence |
|---------|---------------|------------|
| Case sensitivity bug | Code inspection (line 269) | 100% |
| Test exemption gap | Code inspection (lines 152-154) | 95% |
| Cache race condition | Code inspection (lines 171-178) | 90% |
| Destructive git guard fix | Execution verification | 100% |


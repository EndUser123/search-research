# Dependency Verification Gate Fix - 2026-03-09

## Problem

The dependency verification gate was failing to track verified packages correctly due to shell metacharacter contamination in package names extracted from commands.

### Symptoms

1. **Verification state mismatch**: After running `cargo search serde"`, the verification state stored `serde\"` instead of `serde`
2. **Install commands incorrectly blocked**: Running `cargo add serde` after verification would still be blocked because the state lookup failed
3. **False positive blocks**: Users would verify packages, then try to install them, and get blocked anyway

### Root Cause

When commands pass through the hook system, they may contain shell-escaped characters (quotes, backticks, backslashes) that are captured by the regex extraction patterns.

The `\S+` pattern in `VERIFICATION_EXTRACTION_PATTERNS` and install patterns captured these shell metacharacters as part of the package name:

```python
# Before fix - captured shell metacharacters
VERIFICATION_EXTRACTION_PATTERNS = {
    "cargo": re.compile(r"\bcargo\s+search\s+(\S+)", re.IGNORECASE)
}

# Command: cargo search serde"
# Extracted: serde"  ❌ Wrong - includes trailing quote
```

This caused:
- Verification state to store `serde"` instead of `serde`
- Install command to check for `serde` but state contains `serde\"`
- Mismatch → install blocked even though user verified

## Solution

Added `clean_package_name()` function that strips shell metacharacters from extracted package names:

```python
def clean_package_name(package: str) -> str:
    """Clean extracted package name by removing shell metacharacters.

    Args:
        package: Raw package name from command string

    Returns:
        Cleaned package name without quotes or shell metacharacters
    """
    # Remove trailing quotes, backslashes, and shell metacharacters
    package = package.rstrip('"\'`\\')
    # Remove leading quotes if present
    package = package.lstrip('"\'`')
    return package
```

Applied to:
1. Verification command extraction (when marking packages as verified)
2. Install command detection (when checking if packages are verified)

## Changes

**File**: `PreToolUse_dependency_verification_gate.py`

1. Added `clean_package_name()` function (line ~107)
2. Updated verification command extraction to use cleaner (line ~431)
3. Updated `check_npm_install()` to use cleaner (line ~322)
4. Updated `check_pip_install()` to use cleaner (line ~343)
5. Updated `check_cargo_add()` to use cleaner (line ~363)

## Verification

### Test Results

```bash
$ python -m pytest tests/test_dependency_verification_gate.py -v
============================= 25 passed in 0.32s ==============================
```

All existing tests pass without modification.

### Manual Testing

```bash
# Step 1: Verification command
$ echo '{"tool_name": "Bash", "tool_input": {"command": "cargo search serde"}}' | \
  python PreToolUse_dependency_verification_gate.py
Exit code: 0  ✅ Allowed

# Step 2: Check state
$ cat state/dependency_verification_*.json
{"verified_packages": {"serde": 1773074100.123}}

# Step 3: Install command
$ echo '{"tool_name": "Bash", "tool_input": {"command": "cargo add serde"}}' | \
  python PreToolUse_dependency_verification_gate.py
Exit code: 0  ✅ Allowed (package verified)
```

## Impact

**Before**: Verification → Install ❌ BLOCKED (state mismatch)
**After**: Verification → Install ✅ ALLOWED (state correct)

## Related Issues

- Fixes false positive blocks after verification commands
- Resolves user frustration with dependency verification workflow
- Enables autonomous recovery workflow to function correctly

## References

- Original issue: User reported halt symptoms after running verification commands
- State file evidence: `state/dependency_verification_env_cb945d4a-6c4c-4407-976a-86715f66bc6e.json` showed corrupted package names like `\"` and `'`
- Test file: `tests/test_dependency_verification_gate.py` (25 tests, all passing)

## Implementation Date

2026-03-09

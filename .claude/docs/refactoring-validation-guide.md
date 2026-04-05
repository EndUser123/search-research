# Refactoring Validation Process

**Purpose**: Prevent syntax errors from propagating through development phases by enforcing immediate validation after batch refactoring operations.

**Problem Solved**: Batch refactoring scripts can introduce syntax errors that persist through entire development phases if not caught immediately. The session ID consolidation introduced 8 syntax errors that were not discovered until the user specifically asked about errors.

**Solution**: Three-layer validation system that catches errors immediately after batch operations.

---

## Three-Layer Validation System

### Layer 1: Script-Level Validation (REQUIRED)

**Location**: Built into every batch refactoring script via `refactor_validation.py`

**What it does**:
- Runs `py_compile` on all modified files
- Exits with error code 1 if syntax errors found
- Optionally runs pytest tests after syntax validation

**Usage**:
```python
from refactor_validation import validate_and_exit

# At the end of your batch script:
validate_and_exit(
    modified_files=["file1.py", "file2.py"],
    test_paths=["tests/"],  # Optional: run pytest
    exit_on_error=True,     # Exit with error 1 if validation fails
)
```

**Output example** (validation failed):
```
============================================================
REFACTORING VALIDATION GATE
============================================================

[1/2] Validating Python syntax...
❌ SYNTAX VALIDATION FAILED

Errors found:
  P:/.claude/hooks/Stop_router.py:
    Syntax error at line 294: invalid syntax

❌ VALIDATION FAILED - Fix syntax errors before proceeding
```

**Output example** (validation passed):
```
============================================================
REFACTORING VALIDATION GATE
============================================================

[1/2] Validating Python syntax...
✅ All 9 files have valid syntax

[2/2] Running test suite...
✅ All tests passed

============================================================
✅ ALL VALIDATIONS PASSED
============================================================
```

---

### Layer 2: Pre-Commit Hook (REQUIRED)

**Location**: `P:/.claude/hooks/pre-commit-syntax-check`

**What it does**:
- Runs `py_compile` on all staged `.py` files before allowing commit
- Blocks commit if any syntax errors found
- Runs automatically on every `git commit`

**Installation**:
```bash
# Install pre-commit hook
ln -s P:/.claude/hooks/pre-commit-syntax-check .git/hooks/pre-commit

# Or manually add to .git/hooks/pre-commit:
# #!/bin/sh
# python P:/.claude/hooks/pre-commit-syntax-check
```

**Output example** (syntax error found):
```
🔍 Validating syntax for 3 staged Python files...

❌ Syntax validation failed - commit blocked

The following files have syntax errors:

P:/.claude/hooks/Stop_router.py:
    Syntax error at line 294: invalid syntax

Fix the syntax errors before committing.
To skip this check (not recommended), use: git commit --no-verify
```

**Bypass**: `git commit --no-verify` (not recommended)

---

### Layer 3: Manual Validation (OPTIONAL)

**Location**: `P:/.claude/hooks/refactor_validation.py` (CLI mode)

**What it does**:
- On-demand syntax validation for any files
- Useful for manual checks before commits
- Can be integrated into CI/CD pipelines

**Usage**:
```bash
# Validate specific files
python P:/.claude/hooks/refactor_validation.py file1.py file2.py

# Validate files and run tests
python P:/.claude/hooks/refactor_validation.py file1.py file2.py --test-paths tests/

# Non-exit mode (for CI/CD)
python P:/.claude/hooks/refactor_validation.py file1.py --no-exit
```

---

## Batch Refactoring Template

**Location**: `P:/.claude/consolidation_template.py`

**Usage**:
1. Copy template to your new refactoring script
2. Replace TODO sections with your refactoring logic
3. Run the script - validation happens automatically

**Example**:
```python
#!/usr/bin/env python3
"""Consolidate session ID resolution across hooks."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "hooks"))
from refactor_validation import validate_and_exit


def main():
    # Define target files
    TARGET_FILES = [
        Path("P:/.claude/hooks/Stop_router.py"),
        Path("P:/.claude/hooks/SessionEnd_cleanup.py"),
        # ... more files
    ]

    # Define replacements
    REPLACEMENTS = [
        (r"def _resolve_session_id\(.*?\):", "def _resolve_session_id(data: dict) -> str:", "Consolidate session ID resolution"),
        # ... more patterns
    ]

    modified_files = []

    # Apply changes
    for file_path in TARGET_FILES:
        content = file_path.read_text(encoding="utf-8")
        for pattern, replacement, description in REPLACEMENTS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                modified_files.append(file_path)
                break

    # CRITICAL: Validate immediately after changes
    validate_and_exit(
        modified_files=modified_files,
        test_paths=None,  # No tests for this refactoring
        exit_on_error=True,
    )

    print("✅ Refactoring complete and validated!")


if __name__ == "__main__":
    main()
```

---

## Process Workflow

### Before This Improvement

```
1. Run batch refactoring script
2. Script completes (no runtime errors)
3. Move to next phase (JSON consolidation)
4. Syntax errors persist through next phase
5. User asks about errors
6. Discover 8 syntax errors
7. Fix errors manually
```

**Problem**: Steps 3-5 should not happen. Errors should be caught at step 2.

### After This Improvement

```
1. Run batch refactoring script
2. Script validates syntax immediately
3a. If errors found: Script exits with error 1, fix errors, re-run
3b. If no errors: Proceed to next phase
4. Pre-commit hook validates again before commit
5. Only clean code reaches git history
```

**Solution**: Errors caught immediately at step 2, before propagating.

---

## Error Prevention Patterns

### Pattern 1: Always Use Validation Gate

**WRONG**:
```python
# Make changes
for file_path in files:
    content = file_path.read_text()
    new_content = re.sub(pattern, replacement, content)
    file_path.write_text(new_content)

print("Done!")  # ❌ No validation
```

**CORRECT**:
```python
from refactor_validation import validate_and_exit

# Make changes
modified_files = []
for file_path in files:
    content = file_path.read_text()
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        file_path.write_text(new_content)
        modified_files.append(file_path)

# ✅ Validate immediately
validate_and_exit(modified_files, exit_on_error=True)
```

### Pattern 2: Regex Replacement Safety

**WRONG** (creates the `0return` bug):
```python
# Risky: Can create invalid syntax
content = re.sub(r"def (\w+)\(.*?\):", r"def \1(data):\n    0return", content)
```

**CORRECT** (validate immediately after):
```python
content = re.sub(r"def (\w+)\(.*?\):", r"def \1(data):\n    return", content)
file_path.write_text(content)
modified_files.append(file_path)

# Validate immediately to catch syntax errors
validate_and_exit(modified_files, exit_on_error=True)
```

### Pattern 3: Import Statement Safety

**WRONG** (creates import concatenation bugs):
```python
# Risky: Can create "import...import re"
content = re.sub(
    r"from shared_utils import (.+)",
    r"from shared_utils import \1\nimport re",
    content
)
```

**CORRECT** (use multiline pattern):
```python
# Safer: Preserves import structure
content = re.sub(
    r"from shared_utils import (.+)",
    r"from shared_utils import \1\n\nimport re",
    content
)

# And validate immediately
validate_and_exit(modified_files, exit_on_error=True)
```

---

## Root Cause Analysis

### What Went Wrong

**Original batch script** (`consolidate_session_id.py`):
```python
# Applied regex replacements
for file_path in TARGET_FILES:
    content = file_path.read_text()
    content = re.sub(pattern, replacement, content)
    file_path.write_text(content)

# ❌ NO VALIDATION STEP
print("Session ID consolidation complete!")
```

**What happened**:
1. Script ran without errors (no runtime exceptions)
2. Moved to next phase (JSON consolidation)
3. 8 syntax errors persisted through JSON phase
4. User asked about errors
5. Discovered errors with `python -m py_compile`

**Why validation didn't happen**:
- Script author (me) forgot to add validation step
- No pre-commit hook was installed
- No automated gate prevented progression to next phase

### Process Gaps

1. **No script-level validation**: Batch script didn't validate syntax
2. **No pre-commit hook**: No gate before committing changes
3. **No phase gate validation**: No validation between phases
4. **No TDD compliance**: `/refactor` skill specifies validation gates, but I didn't follow them

---

## Lessons Learned

### Lesson 1: Regex is Risky

**Regex replacements can create invalid syntax**:
- Indentation bugs (`0return` instead of `return`)
- Import concatenation (`import...import re`)
- Insertion location errors

**Mitigation**: Always validate syntax immediately after regex replacements.

### Lesson 2: Trust No Script Output

**Script completion ≠ Code validity**:
- A script can "complete successfully" while producing invalid code
- Python only checks syntax when importing/compiling
- No runtime errors ≠ no syntax errors

**Mitigation**: Use `py_compile` to validate syntax, not script exit codes.

### Lesson 3: Follow TDD Workflow

**The `/refactor` skill specifies validation gates**:
```python
# From /refactor documentation:
def red_phase(finding: dict) -> str:
    """RED: Write characterization test, verify it FAILS."""
    artifact = collect_test_evidence(f"pytest {test_file} -v")
    if not verify_tdd_red(artifact).is_verified:
        raise RuntimeError(f"TDD RED violated")
```

**I didn't follow this**: I ran batch scripts without collecting evidence or validating.

**Mitigation**: Always follow the documented workflow, even for "simple" batch operations.

---

## Quick Reference

### Validation Commands

```bash
# Validate specific files
python -m py_compile file1.py file2.py

# Validate all Python files in directory
python -m py_compile P:/.claude/hooks/*.py

# Run validation script
python P:/.claude/hooks/refactor_validation.py file1.py file2.py

# Run validation with tests
python P:/.claude/hooks/refactor_validation.py file1.py file2.py --test-paths tests/
```

### Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `SyntaxError: invalid syntax` | Code has syntax error | Run `py_compile` to find exact line |
| `IndentationError` | Indentation bug | Check for `0return` patterns |
| `ImportError` | Import concatenation | Check for `import...import` patterns |

### Bypass Flags

| Situation | Bypass Command |
|-----------|----------------|
| Skip pre-commit hook | `git commit --no-verify` |
| Disable validation gate | Set `exit_on_error=False` (not recommended) |

---

## Implementation Date

**Date**: 2026-03-14

**Components**:
1. `P:/.claude/hooks/refactor_validation.py` - Validation utilities
2. `P:/.claude/hooks/pre-commit-syntax-check` - Pre-commit hook
3. `P:/.claude/consolidation_template.py` - Batch script template
4. `P:/.claude/docs/refactoring-validation-guide.md` - This document

**Status**: ✅ Implemented and active

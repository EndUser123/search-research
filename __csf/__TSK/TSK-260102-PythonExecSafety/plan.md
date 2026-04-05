# Implementation Plan: PreToolUse Python Execution Safety Hook

**Date:** 2026-01-02
**Status:** Ready for Implementation

## Overview

Create `PreToolUse_python_exec.py` hook to automatically convert unsafe `python -c` commands to safe temp file execution.

## Implementation Phases

### Phase 1: Core Hook Implementation (High Priority)

**Tasks:**
1. Create `P:/.claude/hooks/PreToolUse_python_exec.py`
2. Implement detection logic (`should_intercept()`)
3. Implement code extraction (`extract_python_code()`)
4. Implement temp file generation (`get_temp_file_path()`)
5. Implement updatedInput response (`build_updated_input()`)
6. Add error handling and fallback

**Files to Create:**
- `P:/.claude/hooks/PreToolUse_python_exec.py`

**Acceptance Criteria:**
- Hook runs before Bash tool
- Detects `python -c` patterns
- Returns valid JSON response
- Gracefully handles errors

### Phase 2: Testing (High Priority)

**Tasks:**
1. Create test directory structure
2. Write unit tests for each function
3. Write integration tests for full flow
4. Test with various command patterns
5. Test edge cases

**Files to Create:**
- `P:/__csf.nip/.speckit/memory/TSK-260102-PythonExecSafety/tests/test_hook.py`
- `P:/__csf.nip/.speckit/memory/TSK-260102-PythonExecSafety/tests/test_patterns.py`

**Test Cases:**
```python
# Simple commands (should NOT intercept)
"python --version"
"python -m pytest"
"python script.py"

# Complex commands (SHOULD intercept)
'python -c "from pathlib import Path; print(Path(\\"P:/test\\"))"'
'python -c "import json; data = {\\"key\\": \\"value\\"}; print(data)"'
'python -c "for i in range(10): print(i)"'
```

**Acceptance Criteria:**
- All unit tests pass
- Integration tests show hook correctly modifies commands
- Temp files created in correct location
- Modified commands execute successfully

### Phase 3: Documentation (Medium Priority)

**Tasks:**
1. Update CLAUDE.md PART N with Background Task Safety section
2. Create troubleshooting guide
3. Add usage examples

**Files to Modify:**
- `P:/.claude/CLAUDE.md` (PART N)

**Files to Create:**
- `P:/__csf.nip/.speckit/memory/TSK-260102-PythonExecSafety/doc.md`

**Acceptance Criteria:**
- CLAUDE.md updated with working patterns
- Troubleshooting guide covers common issues

### Phase 4: Verification (Medium Priority)

**Tasks:**
1. Test hook in real session
2. Verify exit code 137 issues are resolved
3. Monitor for any regressions
4. Update documentation based on findings

**Acceptance Criteria:**
- Real background tasks succeed
- No exit code 137 failures
- No performance degradation

## Detailed Implementation: PreToolUse_python_exec.py

```python
#!/usr/bin/env python3
"""
PreToolUse Hook: Python Execution Safety

Automatically converts unsafe python -c commands to safe temp file execution.

Problem:
    Complex python -c commands fail with exit code 137 (SIGKILL) on Windows/Git Bash
    due to MINGW64 translation layer mangling quotes, backslashes, and paths.

Solution:
    Intercept python -c commands, extract code, write to temp file, and execute
    the temp file instead. This avoids shell escaping entirely.
"""

import os
import re
import json
import hashlib
import shlex
import sys
from pathlib import Path

# Configuration
TEMP_DIR = Path("P:/__csf.nip/temp")
COMPLEXITY_THRESHOLD = 100  # characters

def should_intercept(tool_input: dict) -> bool:
    """Check if command should be converted to temp file.

    Returns True if:
    - Command is python -c
    - AND command exceeds complexity threshold OR contains complexity markers
    """
    command = tool_input.get("command", "")

    # Must be python -c or python3 -c
    if not re.match(r'^\s*python(?:3)?\s+-c\s+', command):
        return False

    # Check complexity indicators
    complexity_markers = [
        len(command) > COMPLEXITY_THRESHOLD,      # Long command
        '\\' in command,                           # Backslashes
        command.count('"') > 2,                    # Multiple double quotes
        command.count("'") > 2,                    # Multiple single quotes
        'Path(' in command,                        # Windows paths
        'P:/' in command,                          # Windows paths
        'import' in command and 'from' in command, # Multiple imports
        '\n' in command,                           # Multi-line
    ]

    return any(complexity_markers)


def extract_python_code(command: str) -> str | None:
    """Extract Python code from python -c argument.

    Handles:
    - python -c "CODE"
    - python -c 'CODE'
    - Complex quoted strings
    """
    # Try regex first for simple cases
    match = re.match(r'^\s*python(?:3)?\s+-c\s+(["\'])(.+?)\1\s*$', command, re.DOTALL)
    if match:
        return match.group(2)

    # Try shlex for complex cases
    try:
        parts = shlex.split(command)
        if len(parts) >= 3 and parts[1] == '-c':
            # Rejoin remaining parts as code
            return ' '.join(parts[2:])
    except ValueError:
        # shlex failed, try manual extraction
        # Find position after -c
        idx = command.find('-c')
        if idx != -1:
            after_c = command[idx + 2:].strip()
            # Remove leading quote if present
            if after_c and after_c[0] in '"\'':
                # Find matching end quote (handle escaped quotes)
                quote = after_c[0]
                code = []
                i = 1
                while i < len(after_c):
                    if after_c[i] == '\\' and i + 1 < len(after_c):
                        # Escaped character
                        code.append(after_c[i+1])
                        i += 2
                    elif after_c[i] == quote:
                        # End quote
                        break
                    else:
                        code.append(after_c[i])
                        i += 1
                return ''.join(code)

    return None


def get_temp_file_path(code: str) -> Path:
    """Generate deterministic temp file path from code hash.

    Same code = same file path = reuse temp file
    """
    # Hash the code for consistent naming
    code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]

    # Ensure temp directory exists
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    return TEMP_DIR / f"exec_{code_hash}.py"


def write_temp_file(file_path: Path, code: str) -> None:
    """Write Python code to temp file with header."""

    header = f'''# Auto-generated by PreToolUse_python_exec hook
# Created: {hashlib.sha256(code.encode()).hexdigest()[:16]}
# Original: python -c command
# DO NOT EDIT - This file may be reused

'''

    file_path.write_text(header + code, encoding='utf-8')


def build_updated_input(file_path: Path, original_input: dict) -> dict:
    """Build updatedInput JSON for PreToolUse response."""

    # Use forward slashes and quotes for safety
    new_command = f'python "{file_path.as_posix()}"'

    return {
        "decision": "approve",
        "updatedInput": {
            "command": new_command
        }
    }


def main():
    """Main hook entry point."""

    # Read tool input from environment variable
    tool_input_json = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        tool_input = json.loads(tool_input_json)
        command = tool_input.get("command", "")

        # Check if we should intercept this command
        if not should_intercept(tool_input):
            print(json.dumps({"decision": "approve"}))
            return

        # Extract the Python code from -c argument
        code = extract_python_code(command)
        if not code:
            # Couldn't extract code, let it proceed
            print(json.dumps({"decision": "approve"}))
            return

        # Generate temp file path
        temp_file = get_temp_file_path(code)

        # Write temp file only if it doesn't exist (reuse existing)
        if not temp_file.exists():
            write_temp_file(temp_file, code)

        # Return updated input with safe command
        result = build_updated_input(temp_file, tool_input)
        print(json.dumps(result))

    except json.JSONDecodeError:
        # Invalid JSON, let it proceed
        print(json.dumps({"decision": "approve"}))
    except Exception as e:
        # Any other error, log and let proceed
        # In production, might want to log this somewhere
        print(json.dumps({"decision": "approve"}), file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
```

## Test Cases

```python
# test_hook.py

import pytest
import json
from pathlib import Path
from PreToolUse_python_exec import (
    should_intercept,
    extract_python_code,
    get_temp_file_path,
    build_updated_input,
)

class TestShouldIntercept:
    """Test command detection logic."""

    def test_simple_python_command(self):
        """Simple python commands should NOT be intercepted."""
        tool_input = {"command": "python --version"}
        assert not should_intercept(tool_input)

    def test_python_module(self):
        """python -m should NOT be intercepted."""
        tool_input = {"command": "python -m pytest tests/"}
        assert not should_intercept(tool_input)

    def test_python_script(self):
        """python script.py should NOT be intercepted."""
        tool_input = {"command": "python myscript.py"}
        assert not should_intercept(tool_input)

    def test_complex_python_c(self):
        """Complex python -c SHOULD be intercepted."""
        tool_input = {
            "command": 'python -c "from pathlib import Path; print(\\"P:/test\\")"'
        }
        assert should_intercept(tool_input)

    def test_long_python_c(self):
        """Long python -c SHOULD be intercepted."""
        code = "x" * 150
        tool_input = {"command": f'python -c "{code}"'}
        assert should_intercept(tool_input)

    def test_backslashes_in_command(self):
        """Commands with backslashes SHOULD be intercepted."""
        tool_input = {
            "command": r'python -c "import os; os.makedirs(\\"test\\")"'
        }
        assert should_intercept(tool_input)


class TestExtractCode:
    """Test code extraction logic."""

    def test_simple_double_quotes(self):
        """Extract code from double-quoted command."""
        command = 'python -c "print(42)"'
        assert extract_python_code(command) == "print(42)"

    def test_simple_single_quotes(self):
        """Extract code from single-quoted command."""
        command = "python -c 'print(42)'"
        assert extract_python_code(command) == "print(42)"

    def test_nested_quotes(self):
        """Extract code with nested quotes."""
        command = r'python -c "print(\"hello\")"'
        assert extract_python_code(command) == 'print("hello")'

    def test_windows_path(self):
        """Extract code with Windows paths."""
        command = r'python -c "from pathlib import Path; p = Path(\"P:/test\")"'
        result = extract_python_code(command)
        assert 'Path(' in result
        assert 'P:/test' in result


class TestTempFilePath:
    """Test temp file path generation."""

    def test_deterministic(self):
        """Same code should generate same path."""
        code = "print(42)"
        path1 = get_temp_file_path(code)
        path2 = get_temp_file_path(code)
        assert path1 == path2

    def test_different_codes_different_paths(self):
        """Different codes should generate different paths."""
        path1 = get_temp_file_path("print(1)")
        path2 = get_temp_file_path("print(2)")
        assert path1 != path2


class TestBuildUpdatedInput:
    """Test updatedInput generation."""

    def test_json_response(self):
        """Should return valid JSON with decision and updatedInput."""
        temp_file = Path("P:/__csf.nip/temp/exec_abc123.py")
        original = {"command": "python -c \"print(1)\""}

        result = build_updated_input(temp_file, original)

        assert result["decision"] == "approve"
        assert "updatedInput" in result
        assert "command" in result["updatedInput"]
        assert "exec_abc123.py" in result["updatedInput"]["command"]
```

## Installation Steps

1. **Create hook file:**
   ```bash
   # Copy implementation to:
   P:/.claude/hooks/PreToolUse_python_exec.py
   ```

2. **Make executable:**
   ```bash
   chmod +x P:/.claude/hooks/PreToolUse_python_exec.py
   ```

3. **Verify installation:**
   ```bash
   # Test hook returns valid JSON
   CLAUDE_TOOL_INPUT='{"command":"python -c "print(1)"}' \
     python P:/.claude/hooks/PreToolUse_python_exec.py
   ```

4. **Test in session:**
   ```bash
   # Start new Claude Code session
   # Trigger a python -c command
   # Check if temp file was created
   ls P:/__csf.nip/temp/exec_*.py
   ```

## Success Criteria

- [ ] Hook file created at `P:/.claude/hooks/PreToolUse_python_exec.py`
- [ ] Hook returns valid JSON for all inputs
- [ ] Simple python commands pass through unchanged
- [ ] Complex python -c commands are converted to temp files
- [ ] Temp files are created in `P:/__csf.nip/temp/`
- [ ] Modified commands execute successfully
- [ ] No exit code 137 failures in testing
- [ ] CLAUDE.md updated with Background Task Safety section
- [ ] Documentation complete

## Rollback Plan

If hook causes issues:
1. Delete or rename hook file:
   ```bash
   mv P:/.claude/hooks/PreToolUse_python_exec.py \
      P:/.claude/hooks/PreToolUse_python_exec.py.disabled
   ```
2. Clear temp files:
   ```bash
   rm P:/__csf.nip/temp/exec_*.py
   ```
3. Report issue for investigation

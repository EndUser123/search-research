# Documentation: PreToolUse Python Execution Safety Hook

**Date:** 2026-01-02
**Version:** 1.0.0

## Overview

The PreToolUse Python Execution Safety hook automatically converts unsafe `python -c` commands to safe temp file execution, preventing exit code 137 (SIGKILL) failures on Windows/Git Bash environments.

## Problem Solved

**Symptom:**
```
Background task failed with exit code 137
```

**Root Cause:**
Complex `python -c` commands pass through Git Bash's MINGW64 translation layer, which mangles:
- Backslashes
- Nested quotes
- Windows paths (`P:\`)

**Solution:**
Automatically convert to temp file execution, bypassing shell escaping entirely.

## How It Works

```
BEFORE (Unsafe):
python -c "from pathlib import Path; print('complex')"

AFTER (Safe):
python "P:/__csf.nip/temp/exec_abc123.py"
```

The hook:
1. Detects `python -c` commands
2. Extracts Python code
3. Writes to temp file (if not exists)
4. Returns modified command to Bash tool

## Installation

The hook should be installed at:
```
P:/.claude/hooks/PreToolUse_python_exec.py
```

## Usage

**Automatic - No action required.**

The hook intercepts commands automatically. Just use Claude Code normally.

**Commands that ARE converted:**
```bash
# Long commands
python -c "very long code here..."

# Commands with backslashes
python -c "import json; data = '{\"key\": \"value\"}'"

# Commands with Windows paths
python -c "from pathlib import Path; p = Path('P:/test')"

# Commands with nested quotes
python -c "print(\"hello 'world'\")"
```

**Commands that are NOT converted:**
```bash
# Simple commands
python --version
python script.py
python -m pytest
```

## Temp Files

Temp files are created at:
```
P:/__csf.nip/temp/exec_<hash>.py
```

**Properties:**
- Deterministic naming (same code = same file)
- Reused for identical commands
- Already in .gitignore
- No cleanup needed

## Troubleshooting

### Hook not firing?

**Check hook exists:**
```bash
ls -la P:/.claude/hooks/PreToolUse_python_exec.py
```

**Check hook is executable:**
```bash
chmod +x P:/.claude/hooks/PreToolUse_python_exec.py
```

**Test hook manually:**
```bash
CLAUDE_TOOL_INPUT='{"command":"python -c \"print(1)\""}' \
  python P:/.claude/hooks/PreToolUse_python_exec.py
```

Expected output:
```json
{"decision": "approve", "updatedInput": {"command": "python \"P:/__csf.nip/temp/exec_...py\""}}
```

### Still getting exit code 137?

**Verify temp file was created:**
```bash
ls -la P:/__csf.nip/temp/exec_*.py
```

**Check temp file content:**
```bash
cat P:/__csf.nip/temp/exec_*.py
```

**Verify modified command in hook output:**
The hook should return `"updatedInput"` with the temp file path.

### Hook causes issues?

**Disable temporarily:**
```bash
mv P:/.claude/hooks/PreToolUse_python_exec.py \
   P:/.claude/hooks/PreToolUse_python_exec.py.disabled
```

**Report issue with:**
- Original command
- Hook output (set DEBUG=1)
- Error message

## Development

### Running Tests

```bash
# Unit tests
cd P:/__csf.nip/.speckit/memory/TSK-260102-PythonExecSafety
pytest tests/test_hook.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Adding Test Cases

Edit `tests/test_patterns.py`:
```python
def test_new_pattern(self):
    """Description of what you're testing."""
    tool_input = {"command": "your command here"}
    result = should_intercept(tool_input)
    assert result == expected
```

## Related Files

| File | Purpose |
|------|---------|
| `P:/.claude/hooks/PreToolUse_python_exec.py` | Main hook |
| `P:/__csf.nip/scripts/exec_python.py` | Helper script (manual use) |
| `P:/.claude/CLAUDE.md` PART N | Background Task Safety documentation |
| `P:/__csf.nip/.speckit/memory/TSK-260102-PythonExecSafety/` | This project |

## References

- **Research:** See `research.md` for source citations
- **Architecture:** See `arch.md` for design details
- **Implementation:** See `plan.md` for code and tests

## License

Part of CSF NIP constitution compliance.

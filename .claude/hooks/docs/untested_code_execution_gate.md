# Untested Code Execution Gate

## Purpose

Prevents execution of untested, inline-generated code that bypasses evidence tier requirements and TDD workflow.

## Problem Addressed

**Root Cause from Git Skill Failure:**
LLM compressed working Python heredoc into untested `python -c "..."` one-liner, causing syntax error that would have been caught by testing.

**Constitutional Violations:**
- Evidence Tier: Tier 3 confidence (code inspection) used for Tier 1 action (execution)
- Truth Constitution: No verification attempts before execution
- Investigation Gate: Modified working code without testing

## Hook Behavior

### Blocks
- `python -c "..."` with >50 chars of complex code
- `python << EOF` heredocs with loops, imports, comprehensions
- Any inline code execution with untested modifications

### Allows
- `pytest` execution (TDD workflow)
- `python script.py` (file execution)
- Simple inline code (<50 chars, no complexity)
- Execution in exempt directories (scripts/, prototypes/, examples/)
- All non-Python bash commands

## Integration

**Works WITH TDD:**
- pytest always allowed (required for TDD cycle)
- File-based code requires pytest validation
- Enforces test-first workflow

**Prevents:**
- "Optimize working code without testing" errors
- Syntax errors from untested compression/modification
- Confidence > evidence tier violations

## Configuration

```bash
# Enable (default)
CSF_UNTESTED_CODE_GATE=1

# Disable
CSF_UNTESTED_CODE_GATE=0

# Debug
CSF_HOOK_DEBUG=1
```

## Complexity Indicators

Code is considered "complex" if it contains:
- Lambda functions
- Walrus operators (`:=`)
- For loops or list/dict comprehensions
- Import statements
- Dictionary methods (`.items()`, `.keys()`, `.values()`)
- Function or class definitions

## Examples

**BLOCKED:**
```bash
# Complex one-liner without tests
python -c "data = [(x,y) for x in range(10) for y in range(10)]; print(data)"

# Heredoc with imports and loops
python << 'EOF'
import json
result = [k for k, v in data.items() if v > 1]
print(json.dumps(result))
EOF
```

**ALLOWED:**
```bash
# pytest execution (TDD)
pytest tests/test_foo.py -v

# File execution
python script.py --arg value

# Simple inline
python -c "print('hello')"

# Exempt directory
cd scripts/ && python -c "import sys; print(sys.version)"
```

## Test Coverage

Full test suite in `tests/test_untested_code_execution.py`:
- 8/8 tests passing
- Covers blocking, allowing, exemptions, TDD integration

## Files

- Hook: `PreToolUse_untested_code_execution.py`
- Router integration: `PreToolUse_bash_router.py` (v1.2)
- Tests: `tests/test_untested_code_execution.py`
- Documentation: This file

## Version

1.0.0 (2026-01-23)

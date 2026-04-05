# Error Detection Reference

Detailed error patterns and detection guidance for `/gto` skill.

---

## Python Error Patterns

### ImportError
```
ImportError: No module named 'package_name'
```
**Severity**: Critical
**Impact**: Blocks code execution
**Common causes**: Missing dependencies, virtual environment issues

### NameError
```
NameError: name 'variable_name' is not defined
```
**Severity**: High
**Impact**: Runtime failure
**Common causes**: Undefined variables, scope issues

### TypeError
```
TypeError: unsupported operand type(s) for +: 'type' and 'type'
```
**Severity**: High
**Impact**: Runtime failure
**Common causes**: Type mismatches, incorrect operations

### AttributeError
```
AttributeError: 'object' has no attribute 'attribute'
```
**Severity**: High
**Impact**: Runtime failure
**Common causes**: Wrong object type, missing attributes

### SyntaxWarning
```
SyntaxWarning: "invalid escape sequence"
```
**Severity**: Low
**Impact**: Code quality issue
**Common causes**: Raw strings with backslashes

---

## Hook Failure Patterns

### Import Failures
```
IMPORT_FAIL: ... (TypeError: ...)
IMPORT_FAIL: ... (NameError: ...)
```
**Severity**: Critical
**Impact**: Hook fails to load, breaking system functionality
**Detection**: Check SessionStart/SessionEnd hook diagnostics

### Hook Errors
```
Hook error: [python ...]: ...
```
**Severity**: Critical
**Impact**: Hook execution failure
**Detection**: Look for "Hook error" in conversation

---

## Test Failure Patterns

### Test Failures
```
FAILED
ERROR
test_... FAILED
AssertionError
```
**Severity**: High
**Impact**: Broken test suite
**Detection**: Look for test output with FAIL/ERROR keywords

### Assertion Errors
```
AssertionError: Expected X but got Y
```
**Severity**: High
**Impact**: Test logic failure
**Detection**: Check test output for assertion messages

---

## Exit Code Patterns

### Exit Codes
```
Exit code 1
Exit code 2
Process failed with exit code
```
**Severity**: Varies by code
**Impact**: Command execution failure
**Detection**: Scan for "Exit code" or "Process failed" messages

---

## Tool Error Patterns

### Tool Errors
```
tool_use_error
cancelled by user
Command failed
```
**Severity**: Medium
**Impact**: Tool execution failure
**Detection**: Look for error messages in tool invocations

---

## Severity Classification Guide

**Critical** (must fix now):
- Broken hooks blocking system
- Security vulnerabilities
- Data loss risks
- Import errors

**High** (should fix soon):
- User-facing bugs
- Incomplete features in use
- Repeated user corrections
- Test failures

**Medium** (should fix eventually):
- Warnings that don't break functionality
- Dropped topics (non-critical)
- Context switches
- Ambiguous requirements

**Low** (nice to have):
- Style improvements
- Minor conversation flow issues
- Cosmetic problems

---

## How to Extract Errors

1. **Scan last 10-20 turns** of conversation for error patterns
2. **Extract error blocks** with line numbers/messages
3. **Categorize by type** (import error, runtime error, syntax warning, hook failure, test failure)
4. **Match to files** when possible (error messages often include file:line)
5. **Determine severity** using the classification guide above

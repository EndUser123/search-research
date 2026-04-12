# Stop_negative_existence_guard.py — Pattern Extension

## What Changed

Added 3 new regex alternatives to `NEGATIVE_EXISTENCE_PATTERNS` in `P:\.claude\hooks\Stop_negative_existence_guard.py` (lines 79-81):

```python
r"|\bno\s+subprocess\b"
r"|\bthere's\s+no\s+(?:subprocess|thread|process|agent)\b"
r"|\b(?:there's\s+no|has\s+no)\s+\w+\s+(?:method|function|class|module)\b",
```

## Why

A plan-review agent made a false claim "There's no subprocess" when `subprocess.Popen` exists at `gto_orchestrator.py:574`. The guard needed to catch "no subprocess" and similar negative existence claims about runtime constructs.

## Tests Added

11 new test cases in `P:\.claude\hooks\tests\test_stop_negative_existence_guard.py`:
- `test_no_subprocess_blocked` — "There's no subprocess" without verification
- `test_no_subprocess_with_verification_allowed` — same with Read tool
- `test_theres_no_thread_blocked` — "there's no thread"
- `test_theres_no_process_blocked` — "there's no process"
- `test_theres_no_agent_blocked` — "there's no agent"
- `test_theres_no_method_blocked` — "The API has no validate method"
- `test_theres_no_function_blocked` — "There's no helper function"
- `test_theres_no_class_blocked` — "There's no User class"
- `test_theres_no_module_blocked` — "There's no auth module"
- `test_theres_no_method_with_grep_exempted` — exempt after Grep
- `test_theres_no_subprocess_case_insensitive` — uppercase block

All 42 tests pass (19.09s).

## Code Context

Full `NEGATIVE_EXISTENCE_PATTERNS` block (lines 71-83):
```python
NEGATIVE_EXISTENCE_PATTERNS = re.compile(
    r"\bdoesn't\s+exist\b"
    r"|\bdoes\s+not\s+exist\b"
    r"|\bno\s+such\b"
    r"|\bwasn't\s+created\b"
    r"|\bnot\s+documented\b"
    r"|\bno\s+documentation\b"
    r"|\bno\s+\w+\s+file\b"   # "no config file", "no setup file", etc.
    r"|\bno\s+subprocess\b"
    r"|\bthere's\s+no\s+(?:subprocess|thread|process|agent)\b"
    r"|\b(?:there's\s+no|has\s+no)\s+\w+\s+(?:method|function|class|module)\b",
    re.IGNORECASE,
)
```

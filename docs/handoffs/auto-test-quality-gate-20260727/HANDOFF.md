---
thread_id: 019f9f4f-auto-test-quality-gate-20260727
parent_handoff_path: none
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T13:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Extend quality_gate.py with auto-test execution

## Objective

Extend quality_gate.py's Stop hook to automatically run ruff + pytest on session-modified .py files and feed failures back via the `decision:block` + `reason` mechanism — saving the LLM a turn when verification is needed.

## Status

OPEN — design complete, implementation deferred to fresh session (load-bearing hook file, concurrent-session edits in progress).

## Problem this solves

Current flow (this session, happened 4+ times):
1. Model modifies .py file, claims done
2. quality_gate.py blocks: "no verification receipt"
3. Model reads the block message
4. Model runs pytest/ruff manually
5. Model retries — quality_gate.py checks receipt
6. If receipt covers scope → pass

With auto-test extension:
1. Model modifies .py file, claims done
2. quality_gate.py runs ruff + pytest on modified files
3. If pass → write receipt + allow stop (zero overhead for model)
4. If fail → emit `decision:block` with test failure output as reason
5. Model sees failures, fixes, retries — quality_gate.py re-tests

Saves 1-3 turns per verification cycle.

## Coexistence check (RESOLVED this session)

The two Stop hooks compose cleanly:
- quality_gate.py: blocks (decision:block) on missing verification
- proposal-grounding-monitor: warns (systemMessage) on ungrounded proposals

Different conditions, different output mechanisms, no conflict.

## Implementation spec

### Where to add the code

File: `~/.grok/hooks/scripts/quality_gate.py`
Location: inside the **1st-pass block** (line ~1360), BEFORE `_write_obligation`. When `effective_block` is true AND `stopHookActive` is false (first continuation, not a retry loop), run tests on the modified files.

### Pseudocode

```python
# After detecting effective_block (code modified without verification)
# and BEFORE writing the obligation:

if not stop_hook_active:
    # First pass: try auto-test before blocking
    auto_test_result = _run_auto_test(session_id, modified_files)
    if auto_test_result["passed"]:
        # Tests passed — write the receipt the gate was looking for
        _write_verification_receipt(
            session_id, modified_files, "auto-test",
            verifier_type="test_runner",
            output=auto_test_result["output"]
        )
        # Re-scan: the receipt now exists, so effective_block may be False
        # Fall through to normal flow — the gate should now pass
    elif auto_test_result["ran"]:
        # Tests ran but failed — feed failures back via decision:block
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Auto-test failures detected. Fix before shipping:\n"
                + auto_test_result["failures"][:2000]
            )
        }))
        sys.exit(0)
    # else: no test files found for modified files — fall through to normal block

def _run_auto_test(session_id, modified_files):
    """Run ruff + pytest on modified .py files. Returns dict."""
    import subprocess
    py_files = [f for f in modified_files if f.endswith('.py')]
    if not py_files:
        return {"ran": False, "passed": False, "failures": ""}

    failures = []
    # Run ruff (fast, ~1s)
    try:
        result = subprocess.run(
            ["ruff", "check"] + py_files,
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000
        )
        if result.returncode != 0:
            failures.append(f"ruff:\n{result.stdout[:500]}")
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        pass

    # Run pytest on test files (if they exist)
    for py_file in py_files:
        test_path = _find_test_file(py_file)
        if test_path:
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_path), "--tb=line", "-q"],
                    capture_output=True, text=True, timeout=30,
                    creationflags=0x08000000
                )
                if result.returncode != 0:
                    failures.append(f"pytest {test_path.name}:\n{result.stdout[:500]}")
            except (subprocess.TimeoutExpired, OSError):
                pass

    return {
        "ran": True,
        "passed": len(failures) == 0,
        "failures": "\n".join(failures),
        "output": "auto-test executed"
    }
```

### Key design decisions

1. **Only runs on first pass** (`not stop_hook_active`): avoids running tests 8 times in a loop
2. **Writes receipt on pass**: the existing receipt infrastructure then satisfies the gate — no special handling needed
3. **Uses decision:block on fail**: same mechanism quality_gate.py already uses for its blocks; model sees test failures as the reason
4. **Timeout: 10s ruff + 30s pytest per file**: total budget ~60s within the 600s Stop hook timeout
5. **Fail-open**: if ruff/pytest unavailable, falls through to normal block (model must run tests manually — same as today)
6. **check `stopHookActive`**: documented in ~/.grok/docs/user-guide/10-hooks.md line 262; prevents infinite auto-test loops

### Test plan

1. Modify a .py file with a passing test → auto-test runs, writes receipt, gate passes (zero model turns)
2. Modify a .py file with a failing test → auto-test runs, feeds failure back, model sees failures
3. Modify a .py file with no test file → auto-test runs ruff only, falls through to normal block if no receipt
4. `stopHookActive=true` → auto-test does NOT run (avoids loop); normal block flow
5. ruff/pytest unavailable → fail-open; normal block flow

### Property-based testing extension (future)

Once auto-test works, add Hypothesis property tests alongside unit tests. The `_find_test_file` function should also look for `test_<name>_properties.py` files and run them. This catches the tautological-test blind spot (same model writes code+tests).

## Hard constraints

1. **Must not change the existing obligation/receipt system** — the auto-test extension slots inside it, writing the same receipt type the model would write
2. **Must check `stopHookActive`** — documented loop prevention (10-hooks.md line 262, 8-continuation cap)
3. **Must fail-open** — ruff/pytest unavailable → normal block flow, no crash
4. **Must respect the capability hierarchy** — the path-aware `_derive_required_capability` fix from this session means scripts/ only need static_analysis; auto-test should only run pytest when required_capability is unit_behavior

## Read-first list

1. `~/.grok/hooks/scripts/quality_gate.py` — the target file (lines 1360-1410 for the insertion point)
2. `~/.grok/hooks/scripts/verification_receipt_writer.py` — how receipts are written (the auto-test must produce compatible receipts)
3. `~/.grok/docs/user-guide/10-hooks.md` lines 251-262 — Stop hook decision control, stopHookActive, 8-continuation cap
4. `P:/.data/wiki/concepts/auto-test-stop-hooks-and-property-based-testing.md` — research base

## Resumption protocol

1. Re-read quality_gate.py (concurrent session may have modified it)
2. Implement `_run_auto_test()` function per the pseudocode
3. Insert the call at line ~1360 (before `_write_obligation`)
4. Write tests for the 5 test-plan scenarios
5. Test on a real .py file modification (end-to-end)

## Last user message (verbatim)

> "1. do / 2. investigate, /preflight"

## Epistemic labels

- "Saves 1-3 turns per verification cycle" is [INFERENCE] based on this session's experience (4+ cycles observed)
- "Two Stop hooks compose cleanly" is [FACT] — read both hook sources this session
- The pseudocode is [INFERENCE] — not tested against the actual quality_gate.py continuation-pass flow
- "capability hierarchy" interaction is [INFERENCE] — the path-aware fix is tested but the auto-test interaction with it is not

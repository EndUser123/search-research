# Phase 1 Findings — Pre-Mortem of TaskUpdate Auto-Correct Fix

## Triage Classification

**hook** — A PreToolUse hook (`PreToolUse_task_self_doc_gate.py`) with a parameter auto-correct bug and updated tests.

## Dispatched Specialists

- **adversarial-logic**: Analyzed the `_auto_correct_params` transformation logic for TaskUpdate
- **adversarial-compliance**: Reviewed test contradictions and collision handling policy
- **adversarial-testing**: Verified test coverage of the auto-correct fix
- **adversarial-io-validation**: Checked file I/O, path validation, and external service dependencies

## Specialist Findings Summary

### adversarial-logic

**Domain:** Pure logic correctness of the auto-correct transformation

**Key findings:**

- [MEDIUM] `PreToolUse_task_self_doc_gate.py:178-181` — Non-completed TaskUpdate early-returns after auto-correct but without validation. If auto-correct produced an incorrect transformation, it would go undetected for `status != 'completed'` cases. This is a design trade-off rather than a pure logic error.
- No pure logic errors in the auto-correct transformation itself

### adversarial-compliance

**Domain:** Test contradictions and schema/contract compliance

**Key findings:**

- [HIGH] `test_pretooluse_task_self_doc_gate.py:570-580` — Collision test `test_taskupdate_both_taskid_and_task_id` has misleading docstring. Docstring says "should use task_id, remove taskId" but test asserts `result is None` (allow without modification). The collision case silently drops `taskId` without any warning or explicit resolution.
- [MEDIUM] `PreToolUse_task_self_doc_gate.py:134-136` — When both `taskId` and `task_id` are present, the condition `if task_id in tool_input and taskId not in tool_input` evaluates to False and _auto_correct_params returns None. No collision resolution occurs — the gate silently ignores the collision.

### adversarial-testing

**Domain:** Test coverage and gap analysis

**Key findings:**

- No significant issues found in test coverage for this specific bug scenario. The 39 tests all pass and correctly verify the auto-correct direction (`task_id` → `taskId`).

### adversarial-io-validation

**Domain:** File I/O, path validation, external calls

**Key findings:**

- No file I/O operations in the auto-correct path — pure in-memory dict transformation
- No external service dependencies, path validation gaps, or TOCTOU vulnerabilities
- JSON parsing in `main()` is properly guarded with try/except for malformed input

## Consolidated Findings

### 1. Logical Gaps & Inconsistencies

1.1. [MEDIUM] (source: adversarial-logic) — Non-completion TaskUpdate bypasses validation after auto-correct. At `PreToolUse_task_self_doc_gate.py:178-181`, when `status != 'completed'`, the gate returns `modify` after auto-correct without calling `_validate_self_doc`. A buggy auto-correct on a non-completion update would silently pass. File:line: `PreToolUse_task_self_doc_gate.py:178-181`

1.2. [MEDIUM] (source: adversarial-compliance) — Silent collision handling. When both `taskId` and `task_id` are present, the condition `if task_id in tool_input and taskId not in tool_input` evaluates False, and `_auto_correct_params` returns None. The gate neither resolves the collision nor warns about it. File:line: `PreToolUse_task_self_doc_gate.py:134-136`

### 2. Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-compliance) — The collision test `test_taskupdate_both_taskid_and_task_id` encodes ambiguous intent. The test docstring says "should use task_id, remove taskId" but the assertion expects `None` (allow without modification). This suggests the collision policy is underspecified — it's unclear whether silently passing with both params present is intentional or accidental. File:line: `test_pretooluse_task_self_doc_gate.py:570-580`

2.2. [LOW] (source: adversarial-logic) — The non-completion early-return assumes that non-completion TaskUpdate calls don't need parameter validation. This is a workflow assumption — in practice, even `in_progress` updates should probably use `taskId` correctly.

### 3. Missing Obvious Actions / Best Practices

3.1. [MEDIUM] (source: adversarial-compliance) — The collision case (both `taskId` and `task_id` present) should be made explicit. Either add a validation that blocks when both are present (force the user to resolve), or document that the current behavior is "keep `task_id`, silently drop `taskId`".

3.2. [LOW] (source: adversarial-logic) — Consider adding a validation checkpoint for non-completion TaskUpdate even after auto-correct, to catch any future auto-correct bugs early.

### 4. Risks and Edge Cases

4.1. [LOW] — If a future change adds more auto-correct parameters to TaskUpdate, the collision case will silently pass with unpredictable results.

4.2. [LOW] — The collision scenario (both params present) could indicate a user confusion state — they may not realize they're passing the wrong parameter name.

### 5. Concrete Recommendations

5.1. [MEDIUM] (source: adversarial-compliance) — Add explicit collision handling in `_auto_correct_params`: when both `taskId` and `task_id` are present, either (a) block with an explicit error, or (b) log a warning and keep `taskId` (the correct param). Current behavior is silent drop of `taskId`.

5.2. [LOW] (source: adversarial-logic) — Consider calling `_validate_self_doc` for non-completion TaskUpdate after auto-correct, or add a comment explicitly documenting why this is safe to skip.

### 6. Open Questions / Unknowns

6.1. [LOW] (source: adversarial-compliance) — What is the intended behavior when a user passes both `taskId` and `task_id`? Is this a user error that should be blocked, or a scenario the gate should handle gracefully?

6.2. [LOW] (source: adversarial-logic) — Are there other callers of `_auto_correct_params` besides the `run()` function that could be affected by changes to its behavior?

# Fix Verification Protocol

Shared protocol for verifying that code fixes are applied, tested, and edge cases are covered.

Used by: `/gto`, `/tdd`, `/code`, `/refactor`

## When to Run

After any skill makes code changes that fix bugs, address gaps, or modify behavior.

## Steps

### 1. Collect Fix List

Sources (in priority order):
- GTO artifact (`.evidence/gto-artifact-*.json`) if available
- Session task list completed items
- User-specified fix list
- Git diff of changed files in current session

### 2. Per-Fix Verification

For each fix:
1. **Read** the changed file — confirm the code change is actually present
2. **Reproduce** the original trigger — does the condition that caused the issue still exist?
3. **Run tests** — if tests exist for the changed code, run them. If not, note the gap.
4. **Status**: PASS (fix present + trigger resolved + tests pass), PARTIAL (fix present but gaps), FAIL (fix missing or tests fail)

### 3. Edge Case Analysis

Dispatch `adversarial-failure-modes` agent on the changed files:

```
Agent(subagent_type="adversarial-failure-modes", prompt="Analyze the following changed files for failure mode risks: {files}. Focus on: boundary conditions, error handling gaps, state transitions, race conditions, and input validation. Report HIGH confidence findings only.")
```

### 4. Report

Output per-fix status:

```
FIX VERIFICATION REPORT
━━━━━━━━━━━━━━━━━━━━━━
[FIX-001] BUG-001: adjacent_file_scanner docstring detection
  Status: PASS
  Evidence: while loop now handles shebang+encoding prefix skips (line 275-293)
  Tests: 9 edge cases passed

[FIX-002] BUG-002: docs_presence_checker Path vs str comparison
  Status: PARTIAL
  Evidence: str() cast added (line 98)
  Gap: No test file for this fix

EDGE CASES
━━━━━━━━━━
[HIGH] {file}:{line} — {description}
[LOW]  {file}:{line} — {description}

SUMMARY: 2/2 fixes verified, 1 gap remaining, 1 edge case flagged
```

## Integration Points

| Skill | Phase | Trigger |
|-------|-------|---------|
| `/gto` | After Completeness Check | When previous GTO artifact exists with fixes |
| `/tdd` | VERIFY phase (after GREEN) | Standard TDD cycle |
| `/code` | After AUDIT phase | Code changes made |
| `/refactor` | After REGRESSION step | Refactoring complete |

## Agent Types

- `adversarial-failure-modes`: Domain-aware failure mode discovery (primary for edge cases)
- `adversarial-logic`: Pure logic errors (off-by-one, inverted conditionals)
- `adversarial-state-machine`: State transition bugs (if changes involve state)
- `adversarial-io-validation`: I/O assumption bugs (if changes involve file/external calls)

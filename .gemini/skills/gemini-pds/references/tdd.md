# Test-Driven Development & Implementation (TDD)

All code changes must follow the RED -> GREEN -> REFACTOR cycle with mandatory verification evidence.

## 1. RED (Failing Test)
- Create a test that reproduces the bug or covers the new requirement.
- **Evidence:** Run the test and confirm it FAILS. Quote the failure.

## 2. GREEN (Minimal Fix)
- Write the minimal code necessary to make the test pass.
- **Evidence:** Run the test and confirm it PASSES. Quote the success.

## 3. REFACTOR (Cleanup)
- Improve the code structure while keeping tests green.
- **Evidence:** Run tests again after refactoring.

## 4. READ-AFTER-EDIT
- **Principle:** After any `write_file` or `replace`, you MUST perform a `read_file` in the same turn.
- Do not claim "the edit was successful" until you have verified the file content visually.

## 5. HIERARCHICAL VERIFICATION (The Pyramid)
Proving "it works" requires evidence at three distinct levels:

### Tier 1: Unit (Internal Logic)
- **Goal:** Exercise every branch and edge case in the new/modified functions.
- **Requirement:** Direct coverage of new code. Use `pytest --cov`.

### Tier 2: Integration (Module Contracts)
- **Goal:** Verify that the interaction between the new code and its neighbors is correct.
- **Requirement:** Test the module's public API/Interface without mocks where possible.

### Tier 3: System & Regression (The "Claude /test" Tier)
- **Goal:** Ensure the full system lifecycle (CLI, Hooks, Daemons) respects the change.
- **Requirement:** Run the established system test suite (e.g., subprocess tests, E2E scripts).
- **Regression:** You MUST run existing tests related to the modified area, not just your new tests.

## 6. READ-AFTER-EDIT
- **Principle:** After any `write_file` or `replace`, you MUST perform a `read_file` in the same turn.
- Do not claim "the edit was successful" until you have verified the file content visually.

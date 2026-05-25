---
description: "Test-driven pattern development, test locations, anti-mock stance, coverage"
alwaysApply: false
---

# Testing

## Test-Driven Pattern Development

1. Write a failing test that captures the desired behavior
2. Run the test — confirm it fails for the right reason
3. Write the minimal implementation to make it pass
4. Run the test — confirm it passes
5. Refactor if needed, keeping tests green

## Test File Location

- Hook tests: `P:/.claude/hooks/tests/`
- Plugin tests: `<plugin>/tests/`
- Test naming: `test_<module_name>.py`

## Anti-Mock Stance

Test hook behavior against real dispatch, not mocked inputs.
Mocks hide integration failures. If a hook reads a file, create a real temp file.
If a hook calls a function, call the real function with real arguments.

Exceptions: external APIs, expensive operations, non-deterministic behavior.

## Coverage

- Target: >80% coverage for new modules
- Use `pytest --cov` to measure
- Focus on behavior coverage, not line coverage

## Contract-Preserving Implementation

When refactoring, tests define the contract:
1. Run existing tests before refactoring — all must pass
2. Refactor the implementation
3. Run the same tests — they must still pass
4. If a test breaks, the refactoring violated the contract — fix the refactoring, not the test

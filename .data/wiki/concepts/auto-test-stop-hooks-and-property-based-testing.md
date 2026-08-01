---
title: "Auto-test Stop hooks and property-based testing for AI-generated code"
created: 2026-07-27
source: session-2026-07-27 (/www research on auto-test hooks + mutation/property testing)
sources:
  - external: https://code.claude.com/docs/en/hooks-guide
  - external: https://agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
  - external: https://mutmut.readthedocs.io/
  - external: https://cosmic-ray.readthedocs.io/en/latest/concepts.html
  - external: https://www.anthropic.com/research/property-based-testing
  - external: https://arxiv.org/html/2506.18315v1
  - internal: ~/.grok/docs/user-guide/10-hooks.md § "Stop Decision Control"
tags: [auto-test, stop-hook, property-based-testing, mutation-testing, quality-gate, self-correction, hook-feedback, hypothesis, additionalContext]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Auto-test-in-Stop-hook saves LLM turns by running tests mechanically and
  feeding failures via additionalContext JSON (not exit-2-stderr). The hook
  runs pytest/ruff on modified files, emits structured feedback, the agent
  continues same-turn — eliminating the block→read-stderr→run-test→receipt
  cycle. Property-based testing (Hypothesis) catches 81% of AI-code bugs vs
  69% for unit tests alone — the key failure mode is tautological tests
  (same model generates code+tests, inheriting blind spots). Mutation
  testing (mutmut/cosmic-ray) is too slow for 60s hook timeout; use in
  CI/nightly instead. Recommendation: extend quality_gate.py to run tests
  itself + emit additionalContext + check stopHookActive; add Hypothesis
  property tests alongside unit tests.
relations:
  - target: wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md
    type: extends
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: related
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: related
---

# Auto-test Stop hooks and property-based testing for AI-generated code

## Decision context

**Why this research was needed:** critic_stop.py was built to auto-run tests in a Stop hook and deleted as "redundant." The operator corrected: the goal was to save LLM turns by making test execution mechanical (hook runs tests) rather than conversational (model runs tests, gets receipt, retries). Three questions: (1) is auto-test-in-hook a good idea? (2) could it work inside quality_gate.py? (3) what tests are better than unit tests for AI code?

## Key Findings

### Auto-test in Stop hooks saves turns — confirmed

The Agentic-Patterns "Stop Hook Auto-Continue" pattern runs tests inside the hook and feeds failures back as `additionalContext`. The agent continues in the same turn with the test output — no separate "run tests" turn needed. On this workspace, that would eliminate the cycle that consumed multiple turns this session: quality_gate.py blocks → model reads stderr → model runs pytest → model gets receipt → model retries. With auto-test, quality_gate.py runs pytest → feeds failures via additionalContext → model sees failures and revises in the same turn.

### quality_gate.py is the right place (not a separate hook)

The existing quality_gate.py Stop hook already fires on every code-modifying turn. Extending it to run tests (not just check receipts) is additive — no new hook registration needed. The hook would:
1. Detect modified .py files (already done via mutation receipts)
2. Run ruff + pytest on those files
3. If failures: emit `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "<failure output>"}}`
4. Check `stopHookActive` to avoid running tests 8 times in a loop (the documented 8-continuation cap)

### Property-based testing (Hypothesis) is better than unit tests for AI code

LLM-generated code has a specific failure mode: **tautological tests**. The same model that writes the code writes the tests, so the tests inherit the model's blind spots. Unit tests test what the model thought to test; property-based tests generate thousands of inputs from invariant definitions, catching edge cases the model didn't consider.

Research data (arxiv 2506.18315, 2025): hybrid PBT + unit tests detect ~81% of bugs vs ~69% for either alone. Anthropic's agentic PBT (2026) autonomously discovers properties and writes Hypothesis tests that found real bugs in NumPy/Pandas.

### Mutation testing is too slow for hooks

mutmut default timeout: `(baseline + 1s) × 15`. Cosmic-ray supports `timeout = 60` but treats timeouts as killed mutants. Full mutation runs take minutes-hours. Tools recommend CI/nightly, not pre-commit or Stop hooks. Use mutation testing in a scheduled `/check --deep` or CI pipeline, not in quality_gate.py.

## Recommendation

### Extend quality_gate.py with auto-test (Mechanism C: additionalContext)

```python
# Pseudocode for the extension:
if stop_hook_active:
    exit(0)  # already continuing from a previous block; don't re-test

modified_py_files = get_session_modified_py_files()
if not modified_py_files:
    exit(0)  # no code changed; nothing to test

failures = []
for f in modified_py_files:
    ruff_result = run_ruff(f)
    if ruff_result.failed:
        failures.append(ruff_result.output)

    test_file = find_test_file(f)
    if test_file.exists():
        pytest_result = run_pytest(test_file)
        if pytest_result.failed:
            failures.append(pytest_result.output)

if failures:
    feedback = "\n".join(failures)[:2000]  # truncate for context budget
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": f"Auto-test failures:\n{feedback}"
        }
    }))
    # Do NOT exit(2) — the JSON stdout keeps the agent working via Mechanism C
else:
    exit(0)  # all tests passed; allow stop
```

### Add Hypothesis property tests alongside unit tests

For new AI-generated code, add `@given` decorators with invariant definitions:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    result = my_sort(lst)
    assert len(result) == len(lst)
```

This catches edge cases (empty lists, duplicates, negative numbers, large inputs) that hand-written unit tests miss.

### Use mutation testing in CI, not hooks

Schedule mutmut or cosmic-ray as a nightly `/check --deep` task. Too slow for 60s hook timeout.

## Honest trade-offs

**Like:** auto-test saves turns; additionalContext is cleaner UX than exit-2-stderr; PBT catches tautological-test blind spots.

**Dislike:** auto-test adds 5-30s to every Stop hook (ruff + pytest on modified files); risk of testing the wrong files if mutation receipts are incomplete; PBT tests are harder to write than unit tests (require invariant definitions).

## Falsifier

This concept is wrong if:
- Auto-test in the hook is slower than the model running tests itself (the hook's subprocess spawn overhead exceeds the conversational overhead)
- PBT doesn't catch more bugs than unit tests on our specific codebase (our code may not have the edge-case failure mode the research targets)
- The 8-continuation cap is too low for complex test failures (agent needs >8 iterations to fix)

## Receipts

- **"additionalContext JSON mechanism documented":** receipt — `~/.grok/docs/user-guide/10-hooks.md` lines 251-262, read this session.
- **"PBT catches 81% vs 69%":** [INFERENCE] from subagent summary of arxiv 2506.18315 — the paper was cited but not directly read.
- **"mutmut default timeout formula":** [INFERENCE] from subagent summary of mutmut docs — not directly read.
- **"Anthropic agentic PBT found bugs in NumPy/Pandas":** [INFERENCE] from subagent summary of anthropic.com/research — not directly read.
- **"quality_gate.py already fires on every code-modifying turn":** receipt — `~/.grok/hooks/quality-gate.json` lines 69-79, read this session.

## Related

- [[grok-build-stop-hook-patterns-and-feedback-mechanism]]@extends — the three feedback mechanisms (A/B/C) documented here
- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@related — CRITIC hook and Self-Correct Loop techniques
- [[hook-evidence-collection-cost-vs-timeout-tradeoff]]@related — same hook infrastructure, different concern

## Sources

- Claude Code hooks guide — https://code.claude.com/docs/en/hooks-guide
- Agentic-Patterns auto-continue — https://agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
- mutmut docs — https://mutmut.readthedocs.io/
- Cosmic Ray docs — https://cosmic-ray.readthedocs.io/en/latest/concepts.html
- Anthropic property-based testing — https://www.anthropic.com/research/property-based-testing
- PBT + unit test comparison — https://arxiv.org/html/2506.18315v1
- Grok Build hooks docs — `~/.grok/docs/user-guide/10-hooks.md`
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

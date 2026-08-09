---
title: "Good tests vs coverage tests: the distinction that catches regressions"
created: 2026-08-09
source: session-2026-08-09 (operator pushback on Phase 2 feature tests)
tags: [testing, test-quality, mutation-testing, coverage, regression, behavioral-test, durable-knowledge]
summary: >
  A coverage test exercises a code path and passes; a good test would FAIL if
  the behavior broke. The distinction: good tests assert on meaningful state
  changes or real outputs, not just return codes behind mocks. The mutation
  test is the canonical discriminator: if you delete the implementation, does
  the test still pass? If yes, it's a coverage test. This concept defines the
  distinction, gives a mechanical checklist, and connects to mutation testing
  as the verification layer.
agent: grok
host: both
cognitive_load: 3
verification: observed
type: concept
confidence: 0.90
last_verified: 2026-08-09
half_life_days: 730
relations:
  - target: wiki/concepts/auto-test-stop-hooks-and-property-based-testing.md
    type: extends — that concept covers WHEN to run mutation testing; this covers WHAT makes a test good
  - target: wiki/concepts/writing-discipline-not-enforced.md
    type: related — "write tests" is advisory; this defines what "good tests" means
---

# Good tests vs coverage tests: the distinction that catches regressions

## Decision context

During session 2026-08-09, the operator reviewed Phase 2 feature tests for ship-py and asked: "are these good tests and not just coverage tests?" The honest answer was mixed — some tests (version-bump) were good (real file I/O, specific inputs/outputs, edge cases); others (design_check, babysit) were thin coverage tests (mock everything, check return codes). The operator then asked: "do we have a durable way that is reusable to know when we have good tests?" The answer was no — no wiki concept defined the distinction. This concept fills that gap.

## The distinction

| Property | Good test (behavioral) | Coverage test (thin) |
|---|---|---|
| **Mocks** | Mocks only external boundaries (filesystem via tmp_path, network via fake responses). Real logic runs. | Mocks everything including the function under test. Checks return codes only. |
| **Delete test** | If you delete the implementation, the test FAILS. | If you delete the implementation, the test still PASSES (it mocks the behavior). |
| **Assertions** | Asserts on meaningful state changes, real outputs, file contents, specific values. | Asserts `return_code == 0` or `result is True`. |
| **Edge cases** | Tests boundary conditions (empty input, malformed data, off-by-one, concurrent state). | Tests the happy path only. |
| **Data** | Uses real data structures, real files (tmp_path), real database state. | Uses MagicMock for all inputs and outputs. |

## The mutation test (canonical discriminator)

**The single most reliable test:** delete (or break) the implementation the test is supposed to verify. Does the test fail?

- **Test FAILS → good test.** The test actually depends on the implementation's behavior.
- **Test PASSES → coverage test.** The test exercises a code path but doesn't verify outcomes. It's decorative.

This is a manual mutation test. Automated mutation testing (mutmut, cosmic-ray) does this systematically — it mutates the source code and checks whether tests catch the mutation. But the manual version is free and takes 30 seconds.

## Worked examples from this workspace

### Good test (from ship-py publish version-bump)
```python
def test_bumps_skill_md_version(self, tmp_path):
    skill_md = tmp_path / "my-skill" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text("---\nversion: 1.0.0\n---\n", encoding="utf-8")
    results = _bump_skill_versions([str(skill_md)], "patch")
    assert results[0]["new_version"] == "1.0.1"
    assert "version: 1.0.1" in skill_md.read_text()  # reads the ACTUAL file
```
**Why good:** Uses tmp_path (real file I/O). Asserts on the actual file content after the bump. If `_bump_version` returned wrong values, or if the file wasn't written, this fails.

### Coverage test (from ship-py design_check)
```python
def test_blocks_on_contradicted_claims(self):
    with patch("phases.design_check.load_state", return_value=state), \
         patch("phases.design_check.save_state"):
        result = cmd_record_design_check(args)
    assert result == 2
```
**Why thin:** Mocks load_state and save_state. Checks only the return code. If the CONTRADICTED detection logic was deleted (always returned 0), this test would fail — but only because of the return code, not because it tested whether the right claims were detected. The test doesn't verify the actual claim-matching behavior.

## What this means for our workspace

1. **Prefer real I/O over mocks.** Use `tmp_path` for filesystem, real Pydantic models for data, real function calls for logic. Mock only at genuine boundaries (network, subprocess, git).
2. **The monkeypatch lesson (xfail fix, this session).** The `test_flags_already_shipped` xfail was caused by mocking the wrong module binding (`phases._shared._git` instead of `phases.detect._git`). The test was "passing" for 2 weeks because nobody ran the mutation test. When the xfail was removed, the test failed immediately. This is the coverage-test failure mode in action: the test existed but didn't verify anything.
3. **Mutation testing as periodic validation.** Run `mutmut run` or manual delete-the-implementation checks periodically. If a mutant survives, the corresponding test is a coverage test.

## Falsifier

This distinction is wrong if:
- Mock-based tests that check return codes actually catch real regressions in practice (they sometimes do, when the return code encodes meaningful state)
- The cost of writing behavioral tests (real I/O, edge cases) exceeds the value (caught regressions) for simple utility functions

## Worked examples from this workspace

### Good test (from ship-py publish version-bump)

Receipt: `~/.grok/skills/ship-py/tests/test_phase2_features.py::TestBumpSkillVersions::test_bumps_skill_md_version`

### Coverage test (from ship-py design_check)

Receipt: `~/.grok/skills/ship-py/tests/test_phase2_features.py::TestDesignCheckRecord::test_blocks_on_contradicted_claims`

### The xfail incident

Receipt: `~/.grok/skills/ship-py/tests/test_ship_orchestrator.py::TestAlreadyShippedDetection` — the test was xfailed for 2+ weeks because the mock patched `phases._shared._git` instead of `phases.detect._git` (commit a25132f fixed it). The test existed but didn't verify anything — the canonical coverage-test failure mode.

## What this means for our workspace

When writing tests, ask: "if I deleted the function under test, would this test fail?" If not, it's a coverage test — improve it or mark it as characterization-only. See [[mechanical-enforcement-over-behavioral-reminder]] for why structural checks (like mutation testing) beat advisory rules (like "write good tests").

## Falsifier

This distinction is wrong if:
- Mock-based tests that check return codes actually catch real regressions in practice (they sometimes do, when the return code encodes meaningful state)
- The cost of writing behavioral tests (real I/O, edge cases) exceeds the value (caught regressions) for simple utility functions

## Receipts

- **xfail incident:** `~/.grok/skills/ship-py/tests/test_ship_orchestrator.py:467-525` — `TestAlreadyShippedDetection`. Fixed commit `a25132f`. Root cause: monkeypatch on wrong module binding.
- **Good test example:** `test_phase2_features.py:147-157` — `test_bumps_skill_md_version` uses real `tmp_path` file I/O and asserts on file content.
- **Coverage test example:** `test_phase2_features.py:54-70` — `test_blocks_on_contradicted_claims` mocks load_state/save_state and checks only return code.

## Auto-related

- [[auto-test-stop-hooks-and-property-based-testing]]
- [[sdlc-proactive-prevention-techniques-2026]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[ai-automated-test-generation-patterns]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]


---
title: "Test selection for session verification: full suite, not testmon"
created: 2026-07-30
source: session-019fa94d (/www research on test selection best practices)
sources:
  - https://github.com/tarpas/pytest-testmon
  - https://martinfowler.com/articles/remove-test-attrition.html
  - https://harness.io/blog/test-impact-analysis
tags: [testing, test-selection, pytest, testmon, full-suite, verification, check]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 1
summary: >
  For session verification (/check), run the full package test suite, not
  test-selected tests. The industry consensus (Harness, Martin Fowler, Meta)
  is: full suite is the default for correctness; test selection (TIA, testmon)
  is a CI cost optimization, not a correctness improvement. Our suites are
  small (<15s) so there's no performance reason to select.
relations:
  - target: wiki/concepts/sdlc-proactive-prevention-techniques-2026.md
    type: related
  - target: wiki/concepts/test-coverage-gap-detection-structural-fix.md
    type: complements
---

# Test selection for session verification: full suite, not testmon

## Decision context

The question: when `/check` verifies session work, should it run only
tests for changed files, tests selected by testmon, or the full package
suite? The issue is that changed-file-only tests miss integration breaks
where a change in one file breaks an importer in another.

## What the research found

| Approach | What runs | Speed | Catches integration bugs? | Consensus |
|----------|-----------|-------|--------------------------|-----------|
| Changed file tests only | `pytest tests/test_foo.py` | Fast | ❌ | Local dev norm |
| Full suite | `pytest <package>/` | Slower | ✅ | **Correctness default** |
| Testmon | Coverage-selected | Fast | ⚠️ (misses static file deps) | CI optimization |

**Key findings:**
1. **Full suite is the industry default for correctness** — teams run
   everything, parallelized, capped at <10 min. Selective CI is a cost
   optimization, not a quality boundary.
2. **Testmon has known gaps** — doesn't track static files, external
   services, or environment changes. A test that passes testmon's filter
   but depends on a config file change would be skipped.
3. **Local-dev vs CI split** — affected tests locally for fast feedback,
   full suite as authoritative gate. `/check` is the authoritative gate.

## Decision: full package suite for /check

For our use case (small suites, <15s total), there's no performance
reason to select. Running the full package suite:

1. Catches integration breaks (changed file breaks importer)
2. Catches test ordering issues
3. Doesn't require coverage infrastructure (testmon needs `.testmondata`)
4. Is the simplest possible approach (no configuration, no edge cases)

## What this means for /check

The verifier protocol Step 6 now instructs:
```
pytest <package_root>/ --cov-branch --cov-report=xml:coverage.xml
```

This produces `coverage.xml` which the diff-cover layer uses for
new-line coverage gating. Branch coverage (`--cov-branch`) catches
untested `except` blocks — the exact pattern where AI-agent bugs hide.

## When testmon would be the right choice

- Large monorepos where full suite takes >5 minutes
- CI pipelines where cost-per-minute matters
- Test suites with heavy I/O or integration tests that can't be parallelized

None of these apply to our fleet. Our largest suite (/check itself) is
222 tests in 6 seconds.

## Falsifier

This decision is wrong if:
- Our suites grow to >30 seconds and running full suite on every /check
  becomes annoying. At that point, testmon or pytest-testmon-for-changes
  would be worth the complexity.
- We add integration tests that require external services (databases,
  APIs) that make the full suite non-hermetic. At that point, we'd need
  to separate unit from integration tests.

## Sources

- [pytest-testmon](https://github.com/tarpas/pytest-testmon) — coverage-based local selection
- [Martin Fowler: Remove Test Attrition](https://martinfowler.com/articles/remove-test-attrition.html) — TIA context
- [Harness: Test Impact Analysis](https://harness.io/blog/test-impact-analysis) — TIA at scale

## Related

- [[sdlc-proactive-prevention-techniques-2026]] — the 9-layer pipeline
- [[test-coverage-gap-detection-structural-fix]] — complementary test quality fix

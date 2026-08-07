---
title: Check-after-ship-py sequence — catches non-determinism that single-pass verify misses
created: 2026-08-07
session: 019fcdd2-e190-7323-9b77-57a1c73dada5
verified: OBSERVED
host: grok
---

# Check-after-ship-py — two-skill verification sequence

## The pattern

Running `/check` after `/ship-py` catches non-reproducible claims that `/ship-py`'s verify phase cannot detect. The sequence is:

1. `/ship-py` — build, review, fix, verify (single-pass), ship
2. `/check` — independent verifier re-runs tests and checks claims against reality

## Why it works

`/ship-py`'s verify phase runs each test **once**. If the test passes at that moment, the ship proceeds. But tests that depend on mutable state (live transcripts, shared files, time-sensitive data) can produce different results when re-run later in the same session.

`/check` spawns an **independent verifier** (a subagent with no stake in the original work) that re-runs the tests from scratch. This catches:
- Tests that passed at build time but drift as session state changes
- Claims ("4/4 passed") that don't reproduce under independent verification
- Non-hermetic test designs (external-state dependencies)

## Evidence

- **Session 019fcdd2 (2026-08-07):** `/ship-py` verified the claim-judge hook with 4/4 e2e test passing. One hour later, `/check`'s verifier re-ran the same test 3 times — all 3/4. The "Discussion" case had drifted to a false positive because the test reads the live transcript tail, which grew during the intervening hour.
- `/ship-py`'s verify phase could not have caught this because the drift hadn't happened yet at verify time.

## When to use

- After any `/ship-py` run where the tests touch **external state** (transcripts, live files, shared directories, time-dependent data)
- When the test suite includes **non-hermetic** tests (tests without deterministic fixtures)
- For hooks/scripts that read session data — the session grows between build and check

## When NOT needed

- Tests with fully deterministic fixtures (no external state)
- Pure unit tests (no I/O)
- Trivial changes (typo fixes, config bumps)

## Related

- [[ungrounded-state-prediction-claims-detection-architecture]] — the hook where this pattern was discovered
- [[premature-closure-narrative-sufficiency-external-approaches]] — the broader "claim without receipt" pattern

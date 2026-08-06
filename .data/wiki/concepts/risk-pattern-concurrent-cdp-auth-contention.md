---
title: "Risk pattern: concurrent CDP auth contention"
created: 2026-08-06
source: session-20260728
tags: [risk-pattern, concurrency, browser-state, multi-terminal, auth]
summary: >
  Tools that read shared live browser state (Chrome cookie DB, CDP sessions)
  contend for the same DB lock. A state refresh in one terminal silently
  invalidates other terminals' sessions. The fix is per-profile isolated
  files instead of live browser reads.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: extends
---

# Risk pattern: concurrent CDP auth contention

## Pattern

When multiple terminals concurrently access shared live browser state (Chrome's cookie database, active CDP sessions, browser profiles), they contend for the same DB lock. A state refresh in one terminal silently invalidates all other terminals' sessions, producing 0-page failures across all notebooks or sync operations.

## Evidence

- **Session 2026-07-28:** two concurrent sync drivers both called `nlm login`, silently invalidating each other's CDP sessions → 0-page failures across all notebooks.
- **Session 2026-07-28:** `yt-dlp --cookies-from-browser chrome` recommended by `/www` research without considering multi-terminal contention.
- **Fix:** per-profile isolated cookie files (`export_yt_cookies.py --all`), one driver type per queue.

## What this means for our workspace

1. In multi-terminal workflows, never use flags that read live browser state (`--cookies-from-browser`, concurrent `nlm login` from multiple drivers).
2. Export needed state to per-profile isolated files and read from file instead.
3. This applies to any tool that touches Chrome's cookie DB, not just yt-dlp and nlm.

## Falsifier

If concurrent `--cookies-from-browser` calls from multiple terminals never produce session invalidation (e.g., Chrome's locking is sufficient for the workload), the pattern is overcautious. If the contention only manifests above N>2 concurrent terminals, the threshold should be documented.

## Related concepts

- [[multi-terminal-isolation-stale-data-immunity]] — the design checklist for session-scoped evidence
- [[concurrent-cdp-auth-contention]] — the original incident documentation
- [[invariants-beat-environment-comfort]] — multi-terminal isolation is a workspace invariant

## Receipts

- Session 2026-07-28: 0-page failures across all notebooks from concurrent `nlm login`
- Wiki concept: `concurrent-cdp-auth-contention.md`
- AGENTS.md § "Multi-terminal isolation (live browser state hazards)"

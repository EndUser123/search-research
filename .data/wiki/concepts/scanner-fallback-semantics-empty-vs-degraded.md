---
title: "Scanner fallback semantics: empty-vs-degraded distinction for session isolation"
concept_type: "architecture-decision"
created: 2026-08-06
source: session-019fcd47
agent: grok
host: grok
tags: [multi-agent, concurrency, session-isolation, scanners, stale-data, todo-skill]
summary: >
  When a session-scoped scanner resolves a session ID but finds no artifacts
  for it, the correct behavior is to return EMPTY (correctly scoped — nothing
  to find), not to fall back to scanning ALL sessions' artifacts (degraded
  mode). These are different conditions with different correct responses.
  Confusing them causes cross-session evidence contamination: the scanner
  reports other sessions' work as if it belonged to the current session.
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: refines
---

# Scanner fallback semantics: empty-vs-degraded

## Decision context

**The problem:** during session 019fcd47, the `/todo` scanner was showing
"WARNING: scanning ALL artifacts (multi-terminal isolation disabled)" even
though the session ID was correctly resolved. Investigation revealed the
root cause: `_session_artifacts_dir()` returned `None` in two different
situations, and the callers treated both the same way:

1. **Session ID unavailable** (env var not set, no summary.json) → `None` →
   fall back to scanning all artifacts (degraded mode — correct, we can't scope)

2. **Session ID available, no artifacts directory exists yet** → `None` →
   fall back to scanning all artifacts (WRONG — this is correctly scoped, the
   session simply has no artifacts to find)

Case 2 is the bug. The session IS correctly identified. The scanner IS
correctly scoped. There just aren't any artifacts yet. The correct response
is to return an empty list, not to expand the search to every session's
artifacts on the host.

## The fix

The distinction must be explicit in the scanner's return contract:

```
_session_artifacts_dir() returns:
  - Path  → session-scoped directory exists, search within it
  - None  → session ID unavailable, CANNOT scope → caller enters degraded mode
  - EMPTY → session ID available but no directory → caller returns empty list
```

In practice, this means `_session_artifacts_dir()` must distinguish "can't
scope" from "scoped but empty." The simplest implementation: return a
sentinel or use a two-value return (can_scope: bool, path: Path|None).

```python
# WRONG (the bug):
if artifacts_dir is None:
    # Falls through to scan_all — contaminates with other sessions' data
    items = scan_all_artifacts()

# CORRECT (the fix):
session_id = _resolve_session_id()
if session_id is None:
    items = scan_all_artifacts()  # degraded mode — can't scope
else:
    artifacts_dir = _session_artifacts_dir(session_id)
    if artifacts_dir is None or not artifacts_dir.exists():
        items = []  # correctly scoped — session has no artifacts
    else:
        items = scan_dir(artifacts_dir)  # correctly scoped — search within
```

## Why this matters

Cross-session evidence contamination has real consequences:

- `/todo` shows items from other sessions as if they're this session's work
- `/close` attributes other sessions' uncommitted files to the wrong session
- `/check` reports failures from other sessions as this session's failures
- Review triage reports other sessions' open findings as this session's debt

Each instance creates false-positive work items that waste operator attention
and erode trust in the scanner output. The operator's correction during this
session: "We are supposed to be multi-terminal isolated and immune to stale
data."

This refines [[multi-terminal-isolation-stale-data-immunity]] which covers
session-scoped state directories but does not address the fallback semantics
when a scoped directory doesn't exist. It also relates to
[[scanner-regex-scope-discipline]] — both are scanner correctness patterns
where the scanner's search scope is broader than intended.

## What this means for our workspace

Every scanner in `scan_functions.py` that calls `_session_artifacts_dir()`
must distinguish "can't scope" (degraded) from "scoped but empty" (return
empty list). The fix was applied to:

- `scan_review_findings()` — review FINDINGS.md
- `scan_check_failures()` — check-state files
- `scan_epistemic_debt()` — epistemic debt items (via different path but same pattern)

Any future scanner that uses session-scoped artifact directories must follow
the same pattern: check session ID availability first, then check directory
existence, and only enter degraded mode when the session ID itself is missing.

## Falsifier

A scanner that correctly distinguishes empty from degraded will NEVER produce
"WARNING: multi-terminal isolation disabled" when the session ID is available
in `summary.json` or the `GROK_SESSION_ID` environment variable. If the
warning appears despite a valid session ID, the fallback semantics are still
wrong. See [[scanner-regex-scope-discipline]] for the companion failure mode
(regex scope too broad) and [[multi-terminal-isolation-stale-data-immunity]]
for the parent isolation requirement.

## Receipts

- `~/.grok/skills/todo/__lib/scan_functions.py` — `_session_artifacts_dir()` function, `scan_review_findings()`, `scan_check_failures()`. Fixed in commit `e32feae` (session 019fcd47).
- `P:/.data/wiki/concepts/multi-terminal-isolation-stale-data-immunity.md` — parent concept covering session-scoped state directories. This concept refines it with the empty-vs-degraded distinction.

## Auto-related

- [[close-scanner-unavailable-fallback-session-observations-handoff]]
- [[mechanical-as-input-not-mechanical-as-frame]]
- [[close-scanner-verification-gap-stale-read]]
- [[code-orchestrates-model-judges-skill-scale]]
- [[scanner-to-handoff-gap-discovered-work-not-persisted]]


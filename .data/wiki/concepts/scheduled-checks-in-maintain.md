---
title: "Scheduled checks in /maintain: pull-based upstream monitoring"
slug: scheduled-checks-in-maintain
date: 2026-08-01
tags: [maintain, scheduled-checks, upstream-tracking, pull-based, design-decision, host-invariants]
host: grok
---

# Scheduled checks in /maintain

## Summary

Upstream dependencies (PRs we're waiting on, package versions, wiki concept
freshness) need periodic checking. Instead of push-based scheduled tasks (which
create visual notifications the operator finds annoying and auto-expire after 7
days), we use a **pull-based** approach: `/maintain` reads a registry of
scheduled checks, runs those not yet checked today, and surfaces results inline.

## Decision context

### The problem

Chrome DevTools MCP PR #991 (multi-session support) would upgrade `/model-web`
from sequential to parallel ensemble dispatch. We needed a way to check
periodically whether it merged. The initial solution was `scheduler_create`
(every 3 days) — but the operator found the recurring notification visually
annoying and the 7-day auto-expiry meant the check would die silently.

### What the research changed

The operator proposed the correct architecture: check during `/maintain` runs,
not via scheduled tasks. This is **pull-based** monitoring — the operator pulls
results when they're ready to act, rather than receiving push notifications at
arbitrary times. The scheduled task was cancelled and replaced with this design.

## Architecture

```
P:/.data/scheduled-checks.json    ← registry (state + config)
P:/.agents/scripts/scheduled_checks.py  ← runner (reads registry, runs checks, updates state)
/maintain Step 2h                 ← integration point (calls the runner)
```

### Registry format

```json
[
  {
    "id": "unique-slug",
    "description": "Human-readable description",
    "check_type": "github_issue",
    "check_args": {"repo": "owner/repo", "issue": 123, "look_for": "closed"},
    "action_on_found": "What to do when the check resolves",
    "frequency": "daily",
    "last_checked": null,
    "status": "pending",
    "created": "2026-08-01"
  }
]
```

### Check types

| Type | What it checks | How |
|---|---|---|
| `github_issue` | Is an issue/PR closed or merged? | `gh issue view N --repo owner/repo --json state` |
| _(future: `command_exit_code`)_ | Does a command succeed? | Run command, check exit code |
| _(future: `file_age`)_ | Is a file stale? | Check mtime against threshold |
| _(future: `wiki_concept_age`)_ | Is a wiki concept outdated? | Check git log date |

Adding a new check type = add a handler function to `scheduled_checks.py` and
reference it in `CHECK_HANDLERS`. No registry format change needed.

### State machine

```
pending → (checked, not resolved) → pending (last_checked updated)
pending → (checked, resolved)     → resolved
resolved items remain in registry for audit (don't delete)
```

### Frequency control

`last_checked` tracks the date of the last check. `is_due()` returns true only
when `last_checked != today` and `status == pending`. This means:
- Running `/maintain` twice in one day: second run skips already-checked items
- Running `/maintain` after a week away: all pending items check on first run
- No accumulated notifications during absence — just one inline report

## Why pull beats push for this use case

| Dimension | Scheduled task (push) | /maintain check (pull) |
|---|---|---|
| Visual noise | Creates notifications at arbitrary times | Zero — results are inline in `/maintain` output |
| Auto-expiry | Dies after 7 days | Persists until resolved |
| Operator control | Fires without operator action | Fires only when operator runs `/maintain` |
| Batching | One notification per item | All checks in one report |
| Context | Notification arrives without context | Results appear alongside other maintenance findings |
| Recovery | Expired task is silent failure | Stale `last_checked` date is visible in `--list` |

Scheduled tasks are still correct for **urgent** monitoring (CI failures, quota
exhaustion, active incidents). Scheduled checks in `/maintain` are correct for
**non-urgent** monitoring (upstream PRs, version tracking, freshness audits).

## Current registered checks

| ID | What | Status |
|---|---|---|
| `mcp-multi-session-pr-991` | Chrome DevTools MCP multi-session support (issue #926) | pending |

## Adding a new check

1. Add an entry to `P:/.data/scheduled-checks.json`
2. If using a new check_type, add a handler to `scheduled_checks.py`
3. The next `/maintain` run picks it up automatically

No code changes needed for `github_issue` type — just add the registry entry.

## Cross-references

- [[multi-llm-aggregator-landscape]] — why we're tracking PR #991
- [[tool-fallbacks]] — tool failure patterns (related maintenance surface)
- [[agent-consolidation-in-parallel-workflows]] — parallel dispatch constraints

## Falsifier

This design is wrong if:
- `/maintain` is rarely run, so checks never fire (mitigated: `/maintain` is the
  primary maintenance entry point and runs at least monthly)
- The registry grows stale with resolved items never cleaned (mitigated: resolved
  items stay for audit but don't re-check)
- A check type needs real-time data that `/maintain` cadence can't provide
  (then it belongs in a scheduled task or hook, not here)

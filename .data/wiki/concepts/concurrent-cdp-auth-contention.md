---
title: Concurrent CDP Auth Contention
slug: concurrent-cdp-auth-contention
created: 2026-07-28
category: failure-pattern
tags: [auth, concurrency, notebooklm, cdp, multi-agent, silent-failure]
sources:
  - "yt-is benchmark: 3+3 workers hit 4,123 VPH; 4+4 regressed to 1,150 VPH"
  - "Session 019fa276 (2026-07-28): queue workers produced 0 pages for all notebooks when old bulk_sync.py was still running"
host: both
---

# Concurrent CDP Auth Contention

## The pattern

When two or more processes both call `nlm login --profile <name>` to
re-authenticate against NotebookLM, they **invalidate each other's CDP
(Chrome DevTools Protocol) session**. The second login succeeds for its
caller but silently breaks the first caller's session. The first caller's
subsequent API calls return empty results (0 sources, 0 transcripts) with
**no error** — the API accepts the stale cookie and returns nothing.

## Symptoms

- Queue workers report 0 pages for **every** notebook (not just some)
- Citation coverage drops to 0% despite sources existing in NotebookLM
- No error in logs — the failure is silent
- `list_sources()` returns an empty list
- Transcript export produces 0 files (file-exists skip doesn't apply — nothing was exported)

## Root cause

`nlm login --profile codex` opens a CDP connection to Chrome, navigates to
the Google OAuth flow, and harvests the session cookie. The cookie is stored
per-profile. A second login from a different process **overwrites** the
stored cookie, invalidating the first process's in-memory session. The
NotebookLM API then accepts the old cookie (HTTP 200) but returns empty
results because the session is no longer valid server-side.

This is **not** a race condition in the file system — it's a server-side
session invalidation. Each new login creates a new server session, and the
old one is revoked.

## Detection

The signature is: multiple sync drivers running concurrently + 0-page
results across all notebooks. Check for competing processes:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'queue_sync|bulk_sync|sync\.py|export_transcripts' }
```

If more than one driver-type is running (e.g., `bulk_sync.py` AND
`queue_sync.py`), that's the cause.

## Fix

1. **Kill all competing sync drivers.** Only one driver type should be
   running at a time. The queue worker (`queue_sync.py`) is the approved
   parallel driver — it manages its own worker count and doesn't compete
   with itself (workers share the same auth profile but don't re-login
   unless auth is expired, and the queue file serializes claims).

2. **Re-auth once:** `nlm login --profile a.hominidae`

3. **Retry failed items:** `python queue_sync.py --retry-failed`

## Related failure: stale Chrome port-map PID

A **distinct but related** failure: when an `nlm login` is interrupted or
times out, the Chrome process it launched may die but its PID remains
registered in `~/.notebooklm-mcp-cli/chrome-port-map.json`. The next login
attempt sees port 9222 as "occupied" and either:

- launches Chrome without CDP (detection never fires → "waiting for sign-in"
  hangs forever), or
- fails with "Chrome is already running, so the sign-in browser couldn't
  start with remote debugging."

**Detection:** `nlm login` hangs at "Waiting for sign-in in browser window"
or fails with the "Chrome is already running" error.

**Fix:**
```powershell
# 1. Kill stray Chrome CDP processes
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -match 'remote-debugging-port=9222' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# 2. Clear the port map
python -c "import json; from pathlib import Path; p = Path.home() / '.notebooklm-mcp-cli' / 'chrome-port-map.json'; p.write_text(json.dumps({})); print('cleared')"

# 3. Retry login
nlm login --profile <name>
```

This is not the same as auth contention — only one driver is running. The
stale PID is a cleanup problem, not a concurrency problem. But the symptom
(silent login failure) looks identical, so both root causes are documented
here.

## Prevention

| Rule | Why |
|------|-----|
| Never run `sync.py --all` alongside queue workers | Both call `nlm login` on auth expiry → mutual invalidation |
| Never run two different bulk drivers concurrently | Same root cause |
| The queue worker is the sole approved parallel driver | It handles worker count internally; workers don't compete for auth |
| If you need to test a single notebook, stop the queue workers first | A manual `sync.py --notebook <id>` will call `nlm login` if auth expired, invalidating the workers' sessions |

## Why queue workers don't contend with each other

Queue workers share the same auth session. When `ensure_auth()` runs in a
worker, it checks if auth is valid first (`nlm notebook list --quiet`). If
it returns rc=0, no re-login happens. Only one worker will hit the rc!=0
path and call `nlm login`; the others see the refreshed session. The risk
is only when a **different driver** (not a queue worker) also calls
`nlm login`.

## Cross-cutting applicability

This pattern applies to any system where:
- Auth uses a stored session cookie (not per-request tokens)
- Multiple processes share the same profile/credential
- Re-authentication revokes the previous session server-side
- The API fails silently (returns empty, not an error) on invalid sessions

The detection signature (0 results + no error + concurrent processes) is
the same regardless of the specific API.

## Reference incidents

- **2026-07-28 (session 019fa276):** queue workers produced 0 pages for
  all notebooks. Root cause: old `bulk_sync.py` process was still running
  from an earlier serial run. Both called `nlm login`, invalidating each
  other. Fix: killed `bulk_sync.py`, re-authed, workers produced pages
  normally. Dry-run on notebook 917784eb confirmed the fix (272 transcripts
  → 5 clusters → 5 pages).
- **2026-07-28 (session 019fa276, same day):** stale port-map PID blocked
  free-profile logins. Three consecutive `nlm login` attempts for
  `troup.hominidae` and `brsthomson` all hung at "Waiting for sign-in" or
  failed with "Chrome is already running." Fix: killed stray Chrome on port
  9222, cleared `chrome-port-map.json`, retried — both profiles authenticated
  instantly via silent CDP. Also upgraded nlm from 0.9.0 → 0.9.4 (handles
  `notebook.google.com` URL rebrand).

## Related

- [[notebooklm-cli-operational-gotchas]] — Gotcha 1 (auth recovery recipe)
- [[nlm-to-wiki-optimization-opportunities]] — 3-worker ceiling
- [[shared-directory-contamination-pattern]] — another silent-failure pattern in this pipeline
- [[queue-of-work-pattern-for-nlm-to-wiki]] — the approved parallel driver
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

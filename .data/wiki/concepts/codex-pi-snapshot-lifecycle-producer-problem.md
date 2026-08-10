---
title: codex-pi snapshot lifecycle producer problem
created: 2026-08-10
verified: 2026-08-10
tags: [codex-pi, delegation, workspace-hygiene, tmp-bloat, structural-fix]
host: both
---

# codex-pi snapshot lifecycle producer problem

## Problem

Every `codex-pi` contract-hardening delegation run creates a full workspace
snapshot in `P:\tmp\codex-pi-contract-hardening-{date}-{N}\` containing
~18,000 files (11,911 `.md` + 4,701 `.py` + a 1.18GB `artifacts/` blob).

Two consecutive runs produce ~36,000 files consuming ~2.28GB — nearly all
of the remaining `P:\tmp` space. `/maintain` cleans these up after 3 days,
but the producer should not be creating them in the first place.

## Root cause

The delegation code copies the entire workspace (including prior `.artifacts/`)
into a snapshot directory. This is wrong for two reasons:

1. **A delegation snapshot should not recursively ingest prior execution
   artifacts** — the 1.18GB `artifacts/` blob is especially strong evidence
   that the snapshot boundary is incorrect.

2. **Full workspace copies are unnecessary in a Git workspace** — a temporary
   git worktree at the current base + overlay of only dirty/untracked files
   is sufficient and orders of magnitude smaller.

## Recommended lifecycle

```
delegation starts
    ↓
create run-scoped disposable workspace (worktree + overlay, NOT full copy)
    ↓
execute
    ↓
SUCCESS → delete immediately
FAILURE → retain manifest + useful evidence for bounded TTL (24-72h)
    ↓
automatic expiry
```

## Exclusions for any snapshot

If full snapshots are temporarily necessary, these directories must be
excluded from the copy:
- `.artifacts` (prior execution evidence — the 1.18GB blob)
- `__pycache__`, `.venv`, `node_modules` (cache bloat)
- Prior delegation snapshots (recursive accumulation)

## Namespace

Snapshots should live under a clearly owned run namespace:
```
P:\tmp\codex-pi\<run_id>\
```
with a manifest containing `created_at`, `owner`, `status`, `retain_until`.

## Status

**Identified and documented. Not yet fixed.** The codex-pi/external-delegation
skill producer code needs to be updated to use worktree+overlay instead of
full copy, with `try/finally` self-cleanup and bounded failed-run retention.

## Falsifier

This concept is wrong if the delegation runs genuinely require full workspace
copies (e.g., untracked file dependencies that can't be overlaid). If so,
the fix narrows to: exclude `.artifacts/` and caches from the copy, add
try/finally cleanup, and set a 24h TTL.

---
current_session_id: 019fb3a8-42b6-7e81-91c9-1fad5f4130e6
parent_handoff_path: none
status: open
---

# HANDOFF: close_runner.py "scanner unavailable" regression

Session: 019fb3a8-42b6-7e81-91c9-1fad5f4130e6
Date: 2026-07-31
Status: open — blocks /close

## Problem

`close_runner.py` returns "scanner unavailable" and terminal state "blocked" even when `close_accounting.py` runs fine and shows gates resolving. This blocks `/close` from completing.

## Evidence

- `close_accounting.py --format summary` shows gates: retrospective=pre_satisfied, wiki=pre_satisfied, etc.
- `close_runner.py --session <id> --variant standard` returns generic "scanner unavailable" with no gate assessment
- The runner's error handling masks the actual accounting output

## What to investigate

1. Check if `close_runner.py` was modified by a concurrent session (the skill graph shows close changes were made by other sessions during this session)
2. Run `close_runner.py` with verbose/debug output to see where it fails between calling close_accounting and rendering
3. Check if the runner's subprocess invocation of close_accounting is failing silently (timeout, encoding, import error)

## Priority

HIGH — this blocks every session from closing cleanly. Every session that runs `/close` hits this bug.

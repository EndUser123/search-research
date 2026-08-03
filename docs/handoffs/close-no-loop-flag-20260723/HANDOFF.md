---
thread_id: close-no-loop-flag-20260723
parent_handoff_path: none
current_session_id: 019f7cc5-0767-76a2-a461-c2562bf1e91b
current_terminal_id: console
produced_at: 2026-07-23T15:30:00Z
status: CLOSED
handoff_type: investigation
accurate_as_of_head: 35f2185
---

## Objective

Add `--no-loop` flag support to `close_accounting.py` argparse and main() logic. The SKILL.md documents `--no-loop` as a valid variant (`/close --no-loop`), but the scanner doesn't accept it — it errors with "unrecognized arguments: --no-loop".

## Background

The `/close` SKILL.md variant routing table lists:

```
| `/close --no-loop` | `--variant standard` | All 13 gates, resolve each once, no re-scan |
```

But `close_accounting.py` argparse only accepts `--session`, `--since`, `--variant`, `--format`. Running `--no-loop` produces:

```
close_accounting.py: error: unrecognized arguments: --no-loop
```

This was discovered during the 2026-07-23 `/close` invocation.

## Goal

1. Add `--no-loop` flag to argparse
2. When `--no-loop` is set, `main()` resolves gates once without re-scanning (skip the loop in Step 3 of the SKILL)
3. The flag sets a `no_loop = True` variable that short-circuits the re-scan logic
4. Default behavior (without flag) is unchanged

## Evidence

- SKILL.md variant routing table documents the flag
- argparse error when used: `close_accounting.py: error: unrecognized arguments: --no-loop`
- File: `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
- Argparse block at line ~1365

## Scope

- `close_accounting.py`: add `--no-loop` to argparse, add no-loop logic to main()
- SKILL.md: already documents it — no change needed
- Tests: add 1 test that `--no-loop` is accepted and doesn't re-scan

## Status

OPEN — not started. Minor bug (SKILL.md promises a feature the code doesn't deliver).

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** all other work streams

## Acceptance criteria

1. `python close_accounting.py --session <id> --no-loop` runs without error
2. When `--no-loop` is set, the scanner resolves gates once and does not re-scan
3. Default behavior (without flag) is unchanged
4. 77 existing tests pass

## Next steps

1. Add `parser.add_argument("--no-loop", action="store_true")` to argparse
2. In main(), pass `no_loop` to the loop logic (or short-circuit before re-scan)
3. Run tests
4. Add test for the flag

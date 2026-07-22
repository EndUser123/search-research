---
thread_id: hook-diagnostics-fix-20260721
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T21:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: a58d372
source_transcript: C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl
---

# Hook diagnostics and fix — exit code 1 on all global SessionStart hooks

## Objective

Diagnose and fix the exit code 1 reported by all three global SessionStart hooks on new session start. The hooks fire correctly and write data — the exit 1 is a reporting/contract issue.

## Status

OPEN — diagnostic instrumentation deployed, waiting for new-session data.

## Background

All three global hooks report exit code 1 when Grok Build fires them:
```
X global/SessionStart:session_start[0].hooks[0] (1242ms)  exit code 1
X global/active-surface: session_start[0].hooks[0] (441ms) exit code 1
X global/active-surface: session_start[1].hooks[0] (415ms) exit code 1
```

But the hooks work correctly: they exit 0 manually, write to exec logs and status files, and produce correct output.

## What we know

- `[FACT]` All three hooks exit 0 when run manually (verified multiple times)
- `[FACT]` Exec logs confirm hooks fire and write data on real SessionStart events
- `[FACT]` 1242ms timing under Grok is much higher than <50ms measured manually — unexplained
- `[INFERENCE]` Most likely cause: stderr output treated as failure signal (precedent: claude-mem #1181). Confidence: MEDIUM.

## Diagnostic instrumentation deployed

Commit `5145e2c` added diagnostic logging to `qmd_patches_session_start.py`. It writes to `~/.grok/qmd-patches.diagnostic.log`:
- Python executable, version, cwd, argv
- Grok/Claude env vars
- stdio state (isatty, stdin data)
- Elapsed time, result

## Next steps (priority-ordered)

1. **Start a new session**
2. **Read `~/.grok/qmd-patches.diagnostic.log`** — compare invocation environment vs manual run
3. **Based on diagnostic:**
   - If stderr IS the cause: remove `print(..., file=sys.stderr)` from PASS path in all three hooks (`qmd_patches_session_start.py`, `active_surface_snapshot.py`, `drift_surface_session_start.py`). Keep stderr for FAIL/SKIP only.
   - If not: investigate what the diagnostic reveals
4. **Verify with another new session** — confirm exit 0

## Also resolves

- Thread 5 Nit 2 (silent-on-PASS) — the stderr fix makes PASS silent by default
- Thread 5 Nit 1 (exec-log rotation) — can be addressed at the same time

## Key files

- `~/.grok/hooks/scripts/qmd_patches_session_start.py` (hook + diagnostics)
- `~/.grok/hooks/SessionStart.json` (registration)
- `~/.grok/hooks/active-surface.json` (has two entries — second is `drift_surface_session_start.py`)
- `~/.grok/qmd-patches.diagnostic.log` (diagnostic output)
- `~/.grok/qmd-patches.exec.log` (execution history)
- Wiki concept: `P:/.data/wiki/concepts/grok-build-hook-exit-code-1-stderr-as-failure-signal.md`

## Dependencies

- **Requires:** new session (SessionStart event must fire to produce diagnostic data)
- **Blocks:** nothing directly (other groups are independent)
- **Non-blocking to:** Groups B and C

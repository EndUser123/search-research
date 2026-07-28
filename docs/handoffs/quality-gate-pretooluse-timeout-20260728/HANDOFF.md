---
thread_id: quality-gate-pretooluse-timeout-20260728
parent_handoff_path: none
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
produced_at: 2026-07-28T04:15:00Z
status: ready-to-implement
handoff_type: implementation
---

# Fix: quality-gate PreToolUse hook timeout (10s → 30s)

## Objective

Increase the PreToolUse hook timeout in `~/.grok/hooks/quality-gate.json`
from 10s to 30s. The 10s ceiling causes chronic timeouts when the workspace
dirty-tree is large (currently 200+ files from the nlm-to-wiki bulk run).

## Problem

The `quality-gate:pre_tool_use[0].hooks[0]` hook times out at 10,479ms
(ceiling: 10,000ms). This is the third observed instance of the pattern
documented in `P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md`.

**Impact:** the hook fails open (exit 0), silently dropping the verification
receipt for that tool call. The verification-receipts system loses coverage
with no visible signal. Not blocking, but a silent coverage loss that
accumulates across the session.

**Root cause:** the hook's evidence-collection cost scales with workspace
dirty-tree size. `git diff --name-only HEAD` + per-file git subprocess
calls (blob-OID computation) on Windows cost 200-800ms per file. With
200+ modified files, the total exceeds 10s.

## What was supposed to happen

The prior RCA (2026-07-26, `hook-evidence-collection-cost-vs-timeout-tradeoff.md`)
identified three fix tracks:
- Track A (implemented): `/why` Step 0.5 keyword table
- Track B (not implemented): cache dirty-file set
- Track C (not implemented): increase timeout ceiling

Track C was supposed to be applied. It wasn't.

## Fix

### Step 1: Increase timeout

File: `~/.grok/hooks/quality-gate.json`

Change all `"timeout": 10` entries under `pre_tool_use` to `"timeout": 30`.

Current:
```json
"timeout": 10   // appears 2x in pre_tool_use
```

Target:
```json
"timeout": 30
```

Do NOT change the `post_tool_use` timeouts (those are fine at 10s — they
run after the tool completes, not blocking the user).

### Step 2: Verify

After the change, run a tool call (e.g., `read_file` on a tracked file)
and check the hook timing output. The pre_tool_use hooks should complete
within 30s instead of timing out at 10s.

### Step 3: Consider caching (Track B, optional)

The real fix is caching the dirty-file set across hook invocations within
the same session. The hook currently re-runs `git diff --name-only HEAD`
on every tool call. A session-scoped cache would eliminate the repeated
cost. This is a larger change (~50 lines in the hook script) and can be
deferred — the timeout increase is the immediate unblock.

## Acceptance criteria

- [ ] `quality-gate.json` pre_tool_use timeouts changed from 10 to 30
- [ ] No timeout errors on subsequent tool calls
- [ ] PostToolUse timeouts unchanged (remain at 5-10s)
- [ ] Verify by running a tool call and checking hook timing

## Context for the next session

- The wiki concept `hook-evidence-collection-cost-vs-timeout-tradeoff.md`
  has the full RCA and all three fix tracks documented
- The timeout value lives in `~/.grok/hooks/quality-gate.json`
- This is a config change, not a code change — low risk, high impact
- The bulk nlm-to-wiki run produces a large dirty tree (200+ transcript +
  concept files), which is why the timeout fires more frequently now

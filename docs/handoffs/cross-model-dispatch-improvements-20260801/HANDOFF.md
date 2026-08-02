---
thread_id: cross-model-dispatch-improvements-20260801
parent_handoff_path: none
current_session_id: 019fbf02-d3dd-7f72-9ad2-4538790c0a82
created: 2026-08-01
status: open
assigned_to: <unclaimed>
---

# Cross-Model Dispatch Improvements: pre-verify CLI availability + behavioral timeout/path patterns

## Objective

Three efficiency improvements for cross-model dispatch and general command execution:

### Issue 1: Pre-verify cross-model CLI availability before dispatch

`/tp` and `/aar` dispatch to agy/codex/mmx for cross-model audits. In session
019fbf02, agy was dispatched twice (25s + 4.6s) before fail-open. A 2-second
`agy --version` check would have revealed the permissions gap before wasting 30s.

**Fix:** Add a pre-flight verification step in `/tp` Step 2a and `/aar`
cross-model-audit that runs `--version` on each CLI before dispatching the
actual prompt. If the CLI is unavailable or misconfigured, skip it immediately
with disclosure.

### Issue 2: Proactive timeout setting on scanner/analyzer commands

`close_accounting.py` auto-backgrounded twice (>120s default timeout). The
AGENTS.md already says "set timeout: 180000 on scanner/analyzer commands" but
the rule isn't followed consistently.

**Fix:** Add a pre-tool-call checklist for commands that involve git operations
or multi-repo scanning — always set `timeout: 180000` explicitly.

### Issue 3: Direct config path targeting vs recursive search

The agy config search via `Get-ChildItem -Recurse` took 409s traversing
session/history stores. The canonical path (`~/.gemini/settings.json`) was
documented in the wiki.

**Fix:** Add a "known config locations" reference to AGENTS.md or a wiki concept
that maps tool → config path, so agents target known paths directly.

## Status

OPEN — not started.

## Acceptance criteria

- [ ] /tp Step 2a pre-verifies CLI availability before dispatch
- [ ] /aar cross-model-audit pre-verifies CLI availability before dispatch
- [ ] AGENTS.md or wiki has a "known config locations" reference

## Evidence

- Session 019fbf02: agy dispatched 2× (25.43s + 4.60s) before fail-open
- Session 019fbf02: close_accounting.py auto-backgrounded (>120s timeout)
- Session 019fbf02: agy config recursive search took 409s

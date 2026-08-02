---
thread_id: close-infra-fixes-20260801
parent_handoff_path: none
current_session_id: 019fbf02-d3dd-7f72-9ad2-4538790c0a82
created: 2026-08-01
status: open
assigned_to: <unclaimed>
---

# Close Infrastructure Fixes: close_runner.py WinError 123 + close-check --full composition

## Objective

Two close-pipeline infrastructure issues surfaced in session 019fbf02:

### Issue 1: close_runner.py WinError 123 (JSON-as-path bug)

`close_runner.py:1004` receives the full JSON literal as the `session_dir`
argument instead of parsing it. When PowerShell interpolates a JSON variable
into the command line, the braces end up in the filesystem path, causing
`OSError: [WinError 123] The filename, directory name, or volume label syntax
is incorrect`.

**Root cause:** No session_id input validation in close_runner.py + PowerShell
argument quoting in the SKILL.md caller.

**Fix needed:**
1. Add input validation in `close_runner.py` — detect JSON-like input and
   extract `session_id` from it, or reject with a clear error message
2. Fix the SKILL.md caller to pass the session ID string, not the JSON object

**File:** `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py:1004`
**Tests:** `C:/Users/brsth/.grok/skills/close/tests/`

### Issue 2: /close-check --full composition orchestrator

The operator ran /recap-grok → /todo → /tp do? → /wiki → /handoff → /close-check
→ /tp do manually (7 skills in sequence). A `/close-check --full` mode that
orchestrates the pre-close chain (recap + todo + tp session + wiki + handoff)
in one invocation would eliminate 5 manual skill invocations.

**Design considerations:**
- The close-check workflow already runs remediation + finalization phases
- The pre-close skills (recap, todo, tp) are inline (no subagent spawn)
- The operator may want to review each skill's output before proceeding
- Solution: a `--full` flag that runs each skill sequentially, presenting output
  between each, with the operator able to skip or modify

**Effort:** L

## Status

OPEN — not started.

## Acceptance criteria

- [ ] close_runner.py validates session_id input and handles JSON gracefully
- [ ] /close no longer crashes with WinError 123
- [ ] `/close-check --full` orchestrates the pre-close skill chain

## Evidence

- close-check workflow report: `scratch/pre-close-report.md` finding "[fail] close-gates: [SESSION] close_runner.py crash"
- Trace report in close-check output identified `close_runner.py:1004` as the location

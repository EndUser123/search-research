# Stream 1: Red-team reliability handoff

| Field | Value |
|---|---|
| **Stream** | Red-team workflow reliability code fixes |
| **Priority** | HIGHEST — prevents silent failure mode observed this session |
| **Status** | Not started; all design done, code unwritten |
| **Effort** | ~45 min |
| **Delegation** | One subagent (`capability_mode: execute`); `/agy` reviews after |

## Goal

Make `/red-team` catch silent-no-write failures at dispatch time instead of after the critic runs. Three code changes to the red-team plugin source.

## Background (from session 2026-07-19)

During a `/red-team` self-review run, the `red-team-failure-modes` specialist reported success (exit 0, file path in response) but never invoked the write tool. The orchestrator had no post-dispatch verification; the missing file was only caught by manual `Get-ChildItem`. Incident logged as `inc-48fd0ac31fb7`.

Full investigation: `P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md` (sections 1.1, 2.1, 2.2, 2.5).

## Deliverables (3 code changes)

### 1. Post-dispatch Test-Path verification (~30 lines)

**File:** `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` (or wherever the orchestrator's dispatch loop instructions live — check both the command file and any `__lib/` dispatch code).

**Change:** After each specialist returns its claimed file path, before invoking the next specialist or the critic:

```powershell
$claimed = $specialistResponse.Path  # extract from response text
if (-not (Test-Path $claimed)) {
    # Retry once with stronger instruction
    $retryResult = # re-dispatch with "You MUST invoke the write tool before responding. Verify with Test-Path."
    if (-not (Test-Path $claimed)) {
        # Log incident + mark DEFERRED in _run.json + proceed with coverage gap
        & python "<plugin_root>/__lib/incidents.py" add --category specialist-miss ...
    }
}
```

### 2. Agent prompt verification step (~5 lines per specialist, 8 files)

**Files:** Each specialist agent prompt at `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-{planner,claim-refuter,gate-reviewer,workflow-reviewer,logic,state,failure-modes,plugin,testing,critic}.md`.

**Change:** Append to each specialist's output rule:

> Your response must contain ONLY the file path, **and the file MUST exist on disk before responding**. If your `write` tool call failed, do NOT report the path; report `WRITE_FAILED: <reason>` instead.

### 3. Failure-modes retry policy (~15 lines)

**File:** Same dispatch loop as #1.

**Change:** When `Test-Path` returns false after first dispatch, retry once with explicit instruction: *"You previously failed to write the file. You MUST invoke the write tool before responding. Confirm with Test-Path after writing."* If retry also fails, mark DEFERRED + log incident + proceed.

## Dependencies

- None. All changes are to red-team plugin source, independent of other streams.

## Verification criteria

1. After changes, run a test `/red-team` dispatch. The `Test-Path` gate should fire on every specialist.
2. Deliberately dispatch a specialist that doesn't write (simulate the failure). The gate should catch it, retry, and if retry fails, log incident + mark DEFERRED.
3. Plugin cache rebuilt (`plugin-audit-and-fix.py --bump red-team`).

## External review

After implementation, dispatch `/agy` with: "Review these changes to the red-team orchestrator dispatch loop. Does the Test-Path gate actually catch the silent-no-write failure mode? Any bypass path where a specialist could report success without the gate firing?"

## Source references

- `P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md` — full investigation + 5 priorities
- `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/_run.json` — the run where the failure occurred
- `P:/.claude/state/red-team/incidents.jsonl` — incident `inc-48fd0ac31fb7`
- `P:/.data/wiki/concepts/subagent-silent-no-write-failure.md` — wiki page documenting the failure mode

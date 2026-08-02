---
thread_id: hook-verify-after-commit-enforcement-20260802
parent_handoff_path: P:/docs/handoffs/session-019fa276-shipped-work-20260729/HANDOFF.md
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
current_terminal_id: grok-build-terminal
produced_at: 2026-08-02T19:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: 467c275
---

# Hook-based verify-after-commit enforcement

## Objective

Build a PostToolUse hook that fires when a git commit touches a handoff file, automatically running `/handoff verify <path>` (or equivalent checks) instead of relying on the behavioral prose rule in the /handoff SKILL.md.

## Problem

The `/handoff` skill v0.1.2 added a verify-after-commit rule: "After ANY commit that touches work described in an existing handoff from this session, run `/handoff verify <path>` before doing anything else."

This is a behavioral prose rule — it depends on the agent remembering to invoke it under session pressure. The trace agent's Finding 3 (2026-08-02) noted: "behavioral rules don't fire under pressure — `/trace` was skipped this session despite a critical SKILL.md change." The same failure mode applies here: the verify-after-commit rule was added to the SKILL.md but has no mechanical enforcement.

## Proposed approach

### Option A: PostToolUse hook on `run_terminal_command`

Match git commit commands in PostToolUse. If the commit message or staged files include handoff paths (matching `docs/handoffs/*/HANDOFF.md`), emit a warning obligation or auto-run verify.

**Complexity:** Medium. The hook needs to parse git commit arguments to identify staged files, then check if any match the handoff pattern. This is fragile — git commit commands come in many shapes (`-m`, `-F`, `--amend`, implicit staging).

### Option B: Post-commit git hook (`.git/hooks/post-commit`)

A git post-commit hook that checks if the commit touched any handoff file. If yes, it emits a message to stderr: "⚠️ Handoff file modified — run `/handoff verify <path>` to check for stale claims."

**Complexity:** Low. Git already knows which files were committed. The hook is ~20 lines. It doesn't block — it's advisory. But it runs outside the Grok Build hook system, so it won't create a harvest obligation or quality gate receipt.

### Option C: PostToolUse hook with file-watching

Register a PostToolUse hook on `search_replace|write` that checks if the modified file is a handoff under `docs/handoffs/`. If yes, set a flag. Then a separate PostToolUse on `run_terminal_command` matching `git commit` checks the flag and emits the warning.

**Complexity:** High. Requires state passing between two hooks.

## Acceptance criteria

1. When a git commit touches `docs/handoffs/*/HANDOFF.md`, the operator/agent is notified that the handoff may need verification
2. The notification fires mechanically (hook or git hook), not via behavioral prose
3. The notification includes the handoff path and a one-line reason ("handoff claims may be stale after this commit")
4. The mechanism does NOT block the commit — it's advisory, not gating
5. A test exists that verifies the hook fires when a handoff file is committed

## Dependencies

- **Requires:** Nothing — this is self-contained
- **Blocks:** Eliminates the "behavioral rule doesn't fire" failure mode for the verify-after-commit pattern
- **Non-blocking to:** All other work

## Read-first list

1. `~/.grok/skills/handoff/SKILL.md` — the verify-after-commit rule (§ "Mid-session checkpoint pattern")
2. `~/.grok/hooks/quality-gate.json` — hook registration format
3. `~/.grok/hooks/PostToolUse_auto_verify.py` — existing PostToolUse hook pattern to follow
4. `P:/.data/wiki/concepts/handoff-mid-session-checkpoint-pattern.md` — the durable finding

## Falsifier

This approach is wrong if the hook produces too many false positives (fires on commits that don't actually touch handoff content, like `.gitignore` updates in the handoff directory) or if the advisory nature causes agents to dismiss it as noise.

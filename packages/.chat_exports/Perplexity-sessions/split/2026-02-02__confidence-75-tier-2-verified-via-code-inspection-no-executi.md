---
title: "'Confidence: 75% (Tier 2 - verified via code inspection, no execution data)
'GAP 7: TDD State TTL Mismatch
Evidence:
Pre"
date: "2026-02-02"
mode: "COPILOT"
uuid: "532a6bc8-8ef5-4816-83b4-e608a9fab384"
entry_count: 1
---

## Human

"Confidence: 75% (Tier 2 - verified via code inspection, no execution data)
"GAP 7: TDD State TTL Mismatch
Evidence:
PreToolUse_tdd_blocker.py:34: TDD_STATE_TTL_SECONDS = 2 * 3600 (2 hours)
PreToolUse_investigation_gate.py:91: age > 7200 (2 hours)
These match, which is good. But:
stop_success_validator.py:374: MAX_AGE_HOURS = 2
All aligned. ✅ No gap here."
Is this the best solution?
Analyzing TTL alignment across hooks.
TTL Alignment Analysis
Question: Is 2-hour TTL the optimal value?
Current State
HookTTLPurpose
TDD Blocker
2h
Session continuity for continue command
Investigation Gate
2h
Expire stale investigation state
Stop Validator
2h
Reject stale state files
Assessment
The 2-hour value is arbitrary. It "works" but wasn't derived from evidence.
Problems with 2h:
Too long for rapid iteration - If user does 10 quick tasks in 30 minutes, state from task 1 persists for task 10
Too short for complex refactors - Multi-hour refactoring sessions lose state mid-work
No correlation to actual session - TTL doesn't know when user started/stopped working
Better Approaches
Option A: Session-Based (Not Time-Based) [R:2]
# Use actual session marker instead of TTL
SESSION_MARKER = Path(".claude/sessions/.session_start")
if SESSION_MARKER.exists():
    session_start = datetime.fromisoformat(SESSION_MARKER.read_text())
    # Only accept state created AFTER session start

Pro: State automatically scoped to actual work session.
Con: Requires session tracking infrastructure (which you partially have).
Option B: Task-Based TTL [R:1]
# Short TTL for within-task continuity, not cross-task
TTL_MINUTES = 15  # Expire after 15 minutes of inactivity

Pro: Prevents cross-task state bleeding.
Con: May expire during normal pause (lunch, meeting).
Option C: Explicit State Reset on Task Completion [R:1]
# Clear state at Stop hook success (already partially implemented)
# But also clear on new UserPromptSubmit that doesn't match prior task

Pro: State lifetime tied to task, not arbitrary time.
Con: Requires task boundary detection.
Recommendation
Short-term: Keep 2h but add session marker correlation (Option A + current TTL as fallback).
Evidence needed: Log actual session durations to determine empirical TTL. Current 2h is guess.
Reversibility: [R:1] for TTL value changes, [R:2] for session-based approach.
Verdict: Aligned TTLs are better than misaligned, but 2h isn't necessarily optimal. The real fix is session-scoped state, not time-based expiry.
our solution needs to be multi-terminal friendly. Session ID changes after a compact event.
Acknowledged. That constraint changes the analysis significantly.
TTL Analysis with Multi-Terminal + Compaction Constraints
Constraint Summary
ConstraintImpact on State Management
Multi-terminal
State must be terminal-scoped (already using _{terminal_id}.json)
Session ID changes on compaction
Session-based state becomes unreliable across compaction boundary
Compaction = memory loss
Pre-compaction state is orphaned if keyed to session ID
Problem with Session-Based Approach
Session ID correlation (Option A from previous analysis) breaks on compaction:
Session ABC: state created → compaction → Session XYZ: state orphaned

The new session doesn't know about state from the old session ID.
Why TTL is Actually Appropriate Here
Given compaction semantics, time-based TTL is the correct approach because:
Terminal ID persists across compaction - verification_state_{terminal_id}.json survives
Session ID does not persist - Can't use it as state key
TTL approximates "work session" - 2h is rough proxy for "still working on same task"
Refinement: TTL + Terminal + Timestamp Validation
Current implementation already does this correctly:
# From verification_tracker.py
state["session_start"] = datetime.now(UTC).isoformat()
state["modification_timestamps"][normalized] = datetime.now(UTC).isoformat()

# From stop_success_validator.py:373-387
age_hours = (datetime.now(UTC) - session_start).total_seconds() / 3600
if age_hours > max_age:
    clear_verification_state()
    return {}

This pattern is correct for the constraints.
Remaining Question: Is 2h Optimal?
Factors:
DurationProCon
30 min
Tight task scoping
Expires during normal pauses
1 hour
Reasonable work unit
May lose state during lunch
2 hours
Current default, survives breaks
Cross-task bleeding possible
4 hours
Survives long meetings
Definitely cross-task bleeding
Recommendation: 2h is reasonable. The real protection is terminal scoping + timestamp filtering, not TTL alone.
Verification: Current Implementation is Sound
# Terminal scoping: ✅
state_file = STATE_DIR / f"verification_state_{terminal_id}.json"

# Timestamp filtering: ✅  
for file_path, ts_str in state["modification_timestamps"].items():
    file_ts = datetime.fromisoformat(ts_str)
    if file_ts >= session_start:
        modified_files.append(file_path)

# TTL expiry: ✅
if age_hours > max_age:
    clear_verification_state()

Verdict: Current design is correct for multi-terminal + compaction constraints. TTL of 2h is acceptable. No gap here - this was a false positive in my initial analysis.
Summary: The 2h TTL combined with terminal scoping and modification timestamps is appropriate for the constraints. Session-based state would actually be worse due to compaction breaking session continuity.
"

Do people have better ways to do this?

## Assistant

Your current 2-hour TTL approach with terminal scoping and timestamp filtering is solid and aligns well with Claude Code's constraints like session compaction and multi-terminal use. Community practices in AI coding agents and Claude Code hooks emphasize similar time-based expiry combined with file-based persistence for reliability across disruptions.

## Common Practices
Developers handling state in terminal-based AI agents like Claude Code often use TTLs as a proxy for session activity, especially since session IDs change on compaction. Terminal-specific files (e.g., `verification_state_{terminal_id}.json`) prevent cross-terminal bleed, matching your design.[1][2]
- Shared YAML/JSON state files with locking for multi-agent coordination, polled periodically rather than real-time sync.[1]
- PreCompact and SessionStart hooks to snapshot state before compaction loses context, re-injecting it post-compaction.[3][4]
- Durable execution tools like Temporal.io for agent workflows, persisting state externally with configurable timeouts (e.g., extend TTL via timers). This survives restarts but adds infra overhead unsuitable for local hooks.[5][6]

## Alternatives to Fixed TTL
Pure time-based TTL risks issues during pauses or cross-task bleed, but alternatives adapt better under compaction:

| Approach | Pros | Cons | Fit for Multi-Terminal/Compaction |
|----------|------|------|-----------------------------------|
| Inactivity-Based (e.g., 15-30 min no file mods) | Tight to actual work; no cross-task persistence | Needs last_activity timestamp per state entry; expires on lunch breaks | High: Terminal-scoped inactivity check survives compaction [7] |
| Explicit Reset Hooks | Clear on Stop/PostToolUse success or new task detect (prompt analysis) | Requires task boundary logic in hooks | Medium: Use Stop hooks with `decision: "block"` if state invalid [3] |
| Versioned State + Git | State as commit-linked blobs; validate via git log | Heavier for transient TDD state | Low: Overkill for hook-scoped verification [4] |

Inactivity-based refines your setup: Update `modification_timestamps` on every relevant event, expire if `(now - last_mod) > TTL`. This is reversible and empirical—log durations to tune (e.g., via PostToolUse hook appending to a CSV).

## Recommendation
Stick with 2h TTL as baseline but layer inactivity check: In validators, filter timestamps where `file_ts > max(last_session_start, now - 1h_inactive)`. Leverage PreCompact/SessionStart hooks for state backup/restore. This stays lightweight, multi-terminal safe, and handles compaction without external deps.[3]

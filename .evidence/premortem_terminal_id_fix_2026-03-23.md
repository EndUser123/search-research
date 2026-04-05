# Pre-Mortem: Terminal ID Normalization Fix (ADR-20260323)

**Analysis Target**: ADR-20260323 fix to _read_slash_command_intent_state() in StopHook_skill_execution_gate.py
**Date**: 2026-03-23

## Step 1: Failure Scenario
Its 6 months later and the fix FAILED. SLASH COMMAND IGNORED still occurs after compaction.

## Step 2: Brainstorm Causes (10+)
1. CAUSE-001: Write/read normalization mismatch (addressed)
2. CAUSE-002: Compaction destroys state entirely
3. CAUSE-003: State file TTL expires before read
4. CAUSE-004: Compaction changes terminal ID format
5. CAUSE-005: hook_base vs skill_guard library divergence
6. CAUSE-006: Race condition between write/read
7. CAUSE-007: Terminal ID cache invalidation
8. CAUSE-008: PreToolUse deletes state before Stop reads
9. CAUSE-009: Concurrent terminals with same handle
10. CAUSE-010: GetConsoleWindow returns different handle after compaction

## Step 4: Risk Ratings
- CAUSE-001: L=2 x I=3 = 6 (ADDRESSED)
- CAUSE-002: L=2 x I=3 = 6
- CAUSE-008: L=2 x I=3 = 6

## Step 5: Prevent Top 3
1. CAUSE-001: Fallback path check (FIX APPLIED)
2. CAUSE-002: SessionStart re-establishes terminal state
3. CAUSE-008: TTL-based state expiration

## Fix Location
P:/.claude/hooks/StopHook_skill_execution_gate.py:512-538

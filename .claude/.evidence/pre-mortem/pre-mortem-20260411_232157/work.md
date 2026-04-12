handoff skill invocation goal drift fix

## What was fixed
After session compaction, the LLM adopted a Skill invocation's arguments as the canonical session goal, causing it to act on stale args (e.g., running `/pre-mortem` on hook optimizations) instead of resuming the actual user-level task.

## Three-layer fix applied

### 1. META_PATTERNS update (transcript.py)
Added slash-command skip pattern to filter Skill invocations from goal extraction:
- File: packages/handoff/scripts/hooks/__lib/transcript.py
- Pattern: `^/[a-z][a-z0-9_-]*(?:\s+|--?\s)` matches slash-commands with args/flags
- Bare slash-commands like `/plan` are NOT matched (legitimate user intent)

### 2. Defensive fallback (PreCompact_handoff_capture.py)
Added fallback in goal extraction to skip captured Skill args and use preceding message:
- File: packages/handoff/scripts/hooks/PreCompact_handoff_capture.py
- If goal matches Skill invocation pattern, extracts preceding user message instead

### 3. Restore message warning (handoff_v2.py)
Updated build_restore_message_compact() to warn when a Skill was interrupted:
- File: packages/handoff/scripts/hooks/__lib/handoff_v2.py
- If pending_operations contains skill:type with state=in_progress, continuation_rule warns
- Message: "A Skill was in-progress when the session compacted..."

## Tests
- New file: packages/handoff/tests/test_skill_invocation_goal_drift.py
- 9 tests covering slash-command skip behavior and restore message warnings
- All 9 pass

## Files modified
- packages/handoff/scripts/hooks/__lib/transcript.py
- packages/handoff/scripts/hooks/PreCompact_handoff_capture.py
- packages/handoff/scripts/hooks/__lib/handoff_v2.py
- packages/handoff/tests/test_skill_invocation_goal_drift.py (new)

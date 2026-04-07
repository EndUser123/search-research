Exit-Code Feedback Loop Hardening
===
Files:
- P:/.claude/hooks/__lib/write_tool_error_signal.py (NEW) — shared tool error signal writer
- P:/.claude/hooks/PostToolUse.py — refactored to use shared writer
- P:/.claude/hooks/PostToolUse_router.py — refactored to delegate to shared writer  
- P:/.claude/hooks/UserPromptSubmit_modules/failure_context_injector.py — updated TTL check for dual timestamps

Purpose: Fix dual-writer conflict (PostToolUse_router.py and PostToolUse.py both writing last_tool_error.json),
add PostToolUseFailure wiring, dual timestamps, line-based truncation, expire-on-write, session_id/terminal_id.

Key changes:
1. write_tool_error_signal.py: unified single-writer with dual timestamps (wall+monotonic), line-based truncation (40 stderr/20 stdout), expire-on-write, exit_code detection for error flagging
2. PostToolUse_router.py: _write_error_signal now delegates to shared writer (no longer writes directly)
3. PostToolUse.py: inline signal writing replaced with write_tool_error_signal() call
4. failure_context_injector.py: TTL check now supports both old timestamp and new wall_written_at fields
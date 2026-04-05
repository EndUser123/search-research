#!/usr/bin/env python3
"""
Test CC Diagnostic Logging
==========================

Quick verification that the diagnostic system works.
"""

import sys
from pathlib import Path

# Add hooks directory
HOOKS_DIR = Path("P:/.claude/hooks")
sys.path.insert(0, str(HOOKS_DIR))

from cc_diagnostic_logger import (
    DB_PATH,
    DIAGNOSTICS_ENABLED,
    LOG_DIR,
    get_recent_logs,
    get_session_summary,
    log_assumption,
    log_context,
    log_hook_invocation,
    log_tool_call,
)

print(f"Diagnostics enabled: {DIAGNOSTICS_ENABLED}")
print(f"Log directory: {LOG_DIR}")
print(f"Database: {DB_PATH}")
print()

# Test 1: Log a context event
print("Test 1: Logging context event...")
log_context(
    prompt="Test prompt: check database path",
    claude_md_present=True,
    injected_content=["goal_anchor_injection", "test_injection"],
    conversation_length=5,
    metadata={"test": True}
)
print("  ✓ Context logged")

# Test 2: Log a hook invocation
print("Test 2: Logging hook invocation...")
log_hook_invocation(
    hook_name="test_hook",
    event_type="UserPromptSubmit",
    action="inject",
    injection_content="CONTEXT: Solo developer workflow.",
    reason="goal anchoring",
    duration_ms=15.5
)
print("  ✓ Hook invocation logged")

# Test 3: Log a tool call
print("Test 3: Logging tool call...")
log_tool_call(
    tool_name="Bash",
    tool_input={"command": "python -c 'print(1)'"},
    tool_output="1\n",
    success=True,
    duration_ms=250.3
)
print("  ✓ Tool call logged")

# Test 4: Log a tool call with error
print("Test 4: Logging tool call with error...")
log_tool_call(
    tool_name="Bash",
    tool_input={"command": "python bad_file.py"},
    tool_output="FileNotFoundError: bad_file.py",
    success=False,
    error_type="FileNotFoundError",
    error_message="bad_file.py not found",
    duration_ms=50.1
)
print("  ✓ Tool error logged")

# Test 5: Log an assumption
print("Test 5: Logging assumption...")
log_assumption(
    assumption_type="path_assumption",
    assumption="C:\\Users\\brsth\\.config\\yt-fts",
    source="tool_input",
    verified=False
)
print("  ✓ Assumption logged")

# Test 6: Get recent logs
print("\nTest 6: Reading recent tool logs...")
recent = get_recent_logs("tools", n=5)
print(f"  Found {len(recent)} recent tool entries")
for entry in recent[-2:]:
    print(f"    - {entry.get('tool_name')}: success={entry.get('success')}")

# Test 7: Get session summary
print("\nTest 7: Session summary...")
summary = get_session_summary()
print(f"  Session: {summary['session_id']}")
print(f"  Context events: {summary['context_events']}")
print(f"  Hook invocations: {summary['hook_invocations']}")
print(f"  Tool calls: {summary['tool_calls']}")
print(f"  Assumptions: {summary['assumptions_detected']}")
print(f"  Errors: {summary['errors']}")

# Test 8: Verify database exists
print("\nTest 8: Database file verification...")
db_exists = DB_PATH.exists()
db_size = DB_PATH.stat().st_size if db_exists else 0
status = "✓" if db_exists and db_size > 0 else "✗"
print(f"  {status} Database: {db_size:,} bytes")

print("\n" + "="*50)
print("All tests completed!")
print("="*50)

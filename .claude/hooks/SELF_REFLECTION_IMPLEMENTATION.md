# Self-Reflection Implementation Summary

## Overview

Hybrid self-reflection system with **zero persistence**, using all tool use history.

## Components

### 1. System Prompt (CLAUDE.md)
- **Location**: `P:\CLAUDE.md` under "Core Principles"
- **Content**: 5-step self-reflection protocol for high-risk actions

### 2. PostToolUse Hook (v3.1)
- **File**: `P:/.claude/hooks/posttooluse_self_reflection_reminder.py`
- **Trigger**: After tool execution
- **Function**: Non-blocking advisory for risky operations
- **State**: Zero persistence - uses tool_use_history from input

## Key Features

### Zero Persistence
✅ No state files
✅ No SessionStart hook needed
✅ No stale data possible
✅ Uses tool_use_history already in hook input

### Multi-Terminal Friendly
✅ Each terminal has its own tool_use_history
✅ No cross-terminal contamination
✅ No terminal ID detection needed

### No TTL
✅ No time-based cleanup
✅ No background processes
✅ Simple and predictable

### Session-Wide Detection
✅ Counts ALL Write/Edit operations in session
✅ Doesn't reset when you do other work (Read, Grep, etc.)
✅ Accurate reflection of actual work done

## How It Works

The hook uses `tool_use_history` from the hook input:

```python
input_data = json.load(sys.stdin)
tool_use_history = input_data.get("tool_use_history", [])

# Count ALL Write/Edit operations in session
seen_files = set()
for entry in tool_use_history:  # Not [:20] - ALL history
    if entry.get("tool_name") in ("Write", "Edit"):
        file_path = entry.get("tool_input", {}).get("file_path")
        if file_path:
            seen_files.add(file_path)

return len(seen_files)
```

## Triggers

### Multi-File Detection
- Threshold: greater than 3 files in session
- Example: Writing to 4 different files triggers reminder
- Unique files only (writing to same file twice counts as 1)
- Session-wide: Doesn't reset when you do Read/Grep operations

### Risky Patterns
- git push --force / git push -f
- rm -rf / rm -r
- drop table / delete from
- deploy / publish / release
- Direct database writes

## Comparison to Vibe-Check MCP

| Aspect | Vibe-Check MCP | This Implementation |
|--------|---------------|---------------------|
| API calls | Separate API to Gemini/OpenAI | Zero extra calls |
| Cost | Per-query fees | $0 |
| Latency | +1-3 seconds | ~5ms (local) |
| Privacy | Sends code externally | Local only |
| Persistence | Session state | Zero persistence |
| Multi-terminal | Unknown | Naturally isolated |
| Stale data | TTL-based | Impossible (no state) |
| Reliability | Depends on external service | Works offline |
| Session scope | TTL cleanup | Session-wide (all history) |

## Why Count All History (Not Sliding Window)

### Sliding Window (v3.0 - flawed)
```python
recent = tool_use_history[:20]  # Last 20 operations
```
Problem: Write 4 files, then do 20 reads, reminder disappears

### All History (v3.1 - current)
```python
all_history = tool_use_history  # ALL operations
```
Benefits:
- Accurate session-wide count
- Doesn't reset when you do other work
- Simple - just count what happened
- Reminders are non-blocking anyway (just a nudge)

Trade-off:
- In very long sessions (8+ hours), may remind about work from hours ago
- But: That's actually a good reminder to take a break or summarize what you've done
- Reminders are gentle, not blocking

## Version History

- v3.1 (2026-02-26): Count all history (not just sliding window)
- v3.0 (2026-02-26): Zero persistence, sliding window (had flaw)
- v2.0 (2026-02-26): Multi-terminal isolation, state files, SessionStart hook
- v1.0 (2026-02-26): Initial implementation (single shared state file)

Status: Production-ready, zero persistence, simplest possible implementation

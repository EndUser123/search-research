## Work Under Review: Stop Hook Efficiency Improvements

### Fix 1 (REJECTED by user): Short-circuit Phase 1 on tool use
Proposed: If _distinguish_valid_explanation() returns True (Read/Bash used this turn), skip Phase 1 entirely.
Rejected because: tool use alone doesn't validate claim content — a turn could Read(file_A) and claim things about file_B.

### Fix 2 (IMPLEMENTED): Add SELF_VERIFIED patterns to engine.py
File: P:/.claude/hooks/verification/engine.py lines 159-160
Added two patterns to _SELF_VERIFICATION_PATTERNS:
  - `\bcode\s+at\s+`?[\w./\\-]+\.\w+:\d+` (IGNORECASE)  # "Code at file.py:51" or "Code at `file.py:51-53`"
  - `` `[\w./\\-]+\.\w+:\d+[-–]?\d*`\s+shows?\b `` (IGNORECASE)  # "`file.py:51-53` shows"

Rationale: Responses citing file:line evidence (e.g. "Code at StopHook.py:51-53 shows:") were being blocked because
the existing SELF_VERIFIED pattern required the word "read" to precede the file reference. These patterns enable
the inline citation format commonly used in standard verification responses.

Test results: 6/6 test cases passed — 3 that should be SELF_VERIFIED now match, 3 that should remain SILENT
still return False (no false positives on bare filename mentions or timing claims without citations).

### Fix 3 (PROPOSED, not yet implemented): Fix double-event loading bug
File: P:/.claude/hooks/StopHook_unverified_stance.py lines 858-869

Current buggy code:
```python
if isinstance(tool_events, list) and tool_events:
    loaded_events = tool_events         # branch A: use turn events directly
else:
    loaded_events = load_tool_events_for_context(...)  # branch B: load session events

# Second check — DUPLICATES events when branch A was taken
if isinstance(tool_events, list) and tool_events:
    loaded_events.extend(tool_events)   # BUG: loaded_events IS tool_events here, extends itself
```

Proposed fix:
```python
if isinstance(tool_events, list) and tool_events:
    loaded_events = load_tool_events_for_context(...) or []
    loaded_events.extend(tool_events)   # merge session events + turn events
else:
    loaded_events = load_tool_events_for_context(...) or []
```

### Fix 4 (OBSERVED, no fix proposed): PostToolUse Glob/Grep hook false positives
Observation: PostToolUse advisory "Tool returned no results. Your search assumption may be wrong."
fired after every Glob and Grep call in this session even when results WERE returned.
No fix proposed — needs separate investigation.

### Context
- Purpose: Reduce stop hook verification loops without losing content-level validation
- These hooks protect against: ungrounded confident claims, anti-sycophancy, fabrication
- UNVERIFIED_STANCE_MODE defaults to "warn" (advisory), not "block"
- The verification engine _should_block_claim() passes SELF_VERIFIED, SUPPORTED, REFUTED — only blocks SILENT+confident
- The double-event bug affects build_verdicts() accuracy — duplicate events could cause false SUPPORTED verdicts
  or degrade matching by amplifying irrelevant events

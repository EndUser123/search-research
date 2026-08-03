---
thread_id: close-single-pass-scanner-20260723
parent_handoff_path: none
current_session_id: 019f7cc5-0767-76a2-a461-c2562bf1e91b
current_terminal_id: console
produced_at: 2026-07-23T15:30:00Z
status: CLOSED
handoff_type: investigation
accurate_as_of_head: 35f2185
---

## Objective

Extract a shared `_iter_chat_events(session_id)` generator from `_scan_implicit_verification` and `_extract_session_write_paths` in `close_accounting.py` so both consume a single pass over `chat_history.jsonl` instead of opening and iterating the file independently.

## Background

These two functions each open and iterate `chat_history.jsonl` independently — two full passes for every `/close` run. The /tp critique (glm-5-2, 2026-07-23) identified this as deferred work: low I/O ROI at current session sizes (<50MB), but the maintainability win (one parser, not two) is real if a third consumer of chat data appears.

**Why deferred:** `/close` runs once per session. The absolute cost of two passes is milliseconds. The extraction was deferred because the ROI is maintainability, not performance — and the Evidence dataclass pipeline refactor (which WAS done this session) was higher priority.

## Goal

1. Extract `_iter_chat_events(session_id)` generator that yields parsed JSON events from `chat_history.jsonl`
2. Both `_scan_implicit_verification` and `_extract_session_write_paths` consume the generator
3. Both functions keep their existing return types and behavior
4. 77 existing tests pass unchanged
5. Add a test for the generator itself (yields parsed events, handles malformed JSON, handles missing file)

## Evidence

- File: `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
- `_scan_implicit_verification` at line ~291 (opens chat_history.jsonl, iterates line by line)
- `_extract_session_write_paths` at line ~397 (opens same file, iterates independently)
- Both use identical JSON parsing + line iteration logic
- 77 tests in `tests/` — behavior-preserving refactor safety net
- /tp critique verdict: "Defer — but reframe: low I/O ROI + cohesion. Note `_iter_chat_events()` generator as eventual shape."

## Scope

- `close_accounting.py`: extract generator, update both consumers
- `tests/`: add 2-3 tests for the generator
- No behavior change to existing functions

## Status

OPEN — not started. Deferred from 2026-07-23 session. Do when adding a third consumer of chat data, or when touching either function for another reason.

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** all other work streams

## Acceptance criteria

1. `_iter_chat_events(session_id)` exists and yields `(line_no, event_dict)` tuples
2. Both consumers use it instead of opening the file directly
3. 77 existing tests pass
4. New generator tests cover: missing file, malformed JSON line, normal iteration
5. No duplicate file-open logic remains in either consumer

## Next steps

1. Read both functions to identify shared parsing logic
2. Extract `_iter_chat_events` generator
3. Update `_scan_implicit_verification` to consume it
4. Update `_extract_session_write_paths` to consume it
5. Run tests
6. Add generator tests
7. Run tests again

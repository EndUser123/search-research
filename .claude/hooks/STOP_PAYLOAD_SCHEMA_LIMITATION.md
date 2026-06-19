# Stop Payload Schema Missing `tool_events` Field

**Status**: CRITICAL BLIND SPOT — Confirmed 2026-06-18

## Problem

The Stop hook payload schema provides `transcript_path`, `session_id`, and `terminal_id` but **does NOT provide `tool_events`**. Gates that read `data.get("tool_events", [])` receive an empty array in real Stop payloads, creating a shared root cause affecting multiple quality gates.

## Affected Gates

### 1. Intent-Artifact Alignment Gate (`Stop.py:444-446`)
- **File**: `intent_artifact_alignment.py`
- **Dependency**: Requires `tool_events` for `extract_modified_paths()`, `extract_executed_commands()`, `extract_invoked_skills()`
- **Impact**: If `tool_events` is empty, ALL prompt targets appear "missed" → false positives
- **Evidence**: Gate calls `check_alignment(prompt, tool_events, response)` where `tool_events = []`

### 2. Overconfidence Detector (`Stop.py:1161-1162`)
- **File**: `overconfidence_detector.py` (in `cc-aca-epistemic` plugin)
- **Dependency**: Requires `tool_events` for `_has_comparison_evidence()` validation of structural assessment claims
- **Impact**: If `tool_events` is empty, structural assessment patterns ALWAYS flag → false positives
- **Evidence**: Gate calls `detect_all_overconfidence(response, tool_events=tool_events)` where `tool_events = []`

## Root Cause

### Stop Payload Schema
```python
{
    "user_prompt": "...",
    "response": "...",
    "transcript_path": "/path/to/transcript.jsonl",
    "session_id": "...",
    "terminal_id": "...",
    # ❌ "tool_events": [...]  ← MISSING
}
```

### Evidence Loading Gap
Evidence exists in `transcript_path` (JSONL transcript), but gates read from `tool_events` field which is empty. No translation layer exists to populate `tool_events` from the transcript.

### Verification
```python
# In Stop.py, gates do this:
tool_events = data.get("tool_events", [])  # Always [] in real payloads

# But evidence actually lives here:
transcript_path = data.get("transcript_path")
# Gates should read transcript.jsonl and extract tool events
```

## Fix Requirements

### Option A: Load from transcript_path (RECOMMENDED)
Each gate should load `transcript.jsonl` and extract tool events:

```python
transcript_path = data.get("transcript_path")
if transcript_path:
    tool_events = load_tool_events_from_transcript(transcript_path)
else:
    tool_events = []
```

**Pros**:
- Uses existing transcript infrastructure
- No payload schema change required
- Minimal coordination with Claude Code core

**Cons**:
- Repeated file I/O for each gate (mitigate with cache)

### Option B: Add tool_events to Stop payload
File enhancement request to Claude Code core:

```python
{
    "tool_events": [...],  # ← ADD THIS
    "transcript_path": "...",
    # ... other fields
}
```

**Pros**:
- Efficient (no repeated file I/O)
- Clean separation of concerns

**Cons**:
- Requires core changes
- Longer implementation timeline
- May affect other components

## Shared Function Needed

```python
# P:/.claude/hooks/__lib/tool_events_loader.py
def load_tool_events_from_transcript(transcript_path: str) -> list[dict]:
    """Load tool events from transcript.jsonl."""
    events = []
    with open(transcript_path, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("role") == "assistant" and "tool_calls" in entry:
                for tool_call in entry["tool_calls"]:
                    events.append({
                        "name": tool_call.get("name", ""),
                        "input": tool_call.get("input", {}),
                        "output": tool_call.get("output", ""),
                        "status": tool_call.get("status", ""),
                    })
    return events
```

## Verification Steps

After fix:
1. Run `pytest tests/test_intent_artifact_alignment.py` with real transcript
2. Run `pytest tests/test_overconfidence_detector.py` with real transcript
3. Confirm no false positives for valid tool usage
4. Confirm true positives still fire (misalignment without evidence)

## Related Memory

- `hook_system.md` — hook registration, dispatch, diagnostics
- `intent_artifact_alignment.py` — gate implementation
- `overconfidence_detector.py` — detector implementation
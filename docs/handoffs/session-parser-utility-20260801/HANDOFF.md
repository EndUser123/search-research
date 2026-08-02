---
thread_id: session-parser-utility-20260801
parent_handoff_path: none
current_session_id: 019fbf02-d3dd-7f72-9ad2-4538790c0a82
created: 2026-08-01
status: open
assigned_to: <unclaimed>
---

# Session Transcript Parser Utility: lightweight tool-call extractor from updates.jsonl

## Objective

Create a lightweight Python utility at `P:/.agents/scripts/parse_session.py`
that extracts structured tool call data from Grok Build session transcripts.

## Problem

Session 019fbf02 had 10 Python errors (8 Tracebacks + 2 SyntaxErrors) trying
to extract tool call data from `chat_history.jsonl`. The data isn't there —
it lives in `updates.jsonl` under `params.update.sessionUpdate` with type
`tool_call`. See wiki concept
[[grok-build-session-transcript-tool-call-data-in-updates-jsonl]].

Every session that needs to answer "what did this session do?" (recap, todo,
AAR, close-check) re-derives this parsing logic from scratch.

## Solution

A utility script that:
1. Takes a session ID as input
2. Reads `updates.jsonl` from `~/.grok/sessions/<encoded-cwd>/<session-id>/`
3. Extracts all `tool_call` entries with: tool name, arguments, file paths, commands
4. Returns structured output (JSON or formatted table)
5. Optionally: filter by tool name, group by file, count by type

## Design

```python
# P:/.agents/scripts/parse_session.py
# Usage: python parse_session.py <session-id> [--tool <name>] [--json] [--summary]
# Returns: structured tool call data from updates.jsonl
```

**NOT the AAR preprocessor** — the preprocessor is heavyweight (full evidence
packet with detectors, signals, reconciliation). This is a lightweight
extractor for "what tools were called, what files were touched, what commands
were run." Different use case, different output.

## Status

OPEN — not started.

## Acceptance criteria

- [ ] `python parse_session.py <session-id>` returns tool call summary
- [ ] `--json` flag returns structured JSON
- [ ] `--tool <name>` filters by tool name
- [ ] `--summary` returns counts by tool type + files written + commands run
- [ ] Handles missing/empty sessions gracefully

## Evidence

- Session 019fbf02: 10 Python errors from hand-rolled parsing
- Wiki concept: `grok-build-session-transcript-tool-call-data-in-updates-jsonl.md`

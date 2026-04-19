---
type: entity
title: "Session ID Discovery via Transcript"
created: 2026-04-18
source: ~/Downloads/from claude code_ __❯ what is this session id___●.md
hash: 3dfd4aa3d20c0168ad40a3a7c6ae6f6d2ba49d980ec12ad44d12a656e328d78b
tags:
  - session
  - transcript
  - jsonl
  - discovery
summary: "How to extract session IDs from Claude Code transcript JSONL files using Python — pattern matching on permission-mode entries."
---

# Session ID Discovery

## Method

Read the transcript JSONL file and extract `session_id` fields from `permission-mode` entries:

```python
import json

with open("transcript.jsonl") as f:
    for line in f:
        entry = json.loads(line)
        if entry.get("type") == "permission-mode":
            session_id = entry.get("session_id")
            print(f"session_id: {session_id}")
```

## Sources Examined

Multiple session transcripts with entries like:
```
{"type":"permission-mode","session_id":"ef8aba04-e540-4d45-b46a-cdef60644749"}
{"type":"permission-mode","session_id":"57914d7b-4ecd-4f68-9094-2cd8301fb7d7"}
```

## Use Cases

- Cross-session debugging
- Handoff verification
- Transcript correlation

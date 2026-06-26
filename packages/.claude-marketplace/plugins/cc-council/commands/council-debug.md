---
name: council-debug
description: Council state diagnostics and health check
version: 1.0.0
---

# /council-debug - State Diagnostics

Check council system health and state database status.

## Usage

```
/council-debug
```

## Behavior

- Checks ai-api provider health
- Lists available models from configured SDK providers
- Shows session count by state
- Identifies stale sessions
- Reports database status

## Output

Diagnostic report with:
- Provider health status
- Available models
- Session counts by state
- Stale session IDs (if any)
- Database path and size
---
name: catch-22-detection
description: Detect and respond to Catch-22 situations where fixing X requires tools that depend on X.
version: "1.0.0"
status: stable
category: troubleshooting
triggers:
  - 'hook blocked'
  - 'file has been modified'
  - 'permission denied'
  - 'cannot proceed'
  - 'recursive failure'
aliases:
  - '/catch-22'
suggest:
  - /debug
---

## Purpose

A Catch-22 occurs when fixing system X requires tools that depend on system X functioning correctly.

## Detection Triggers

- Same tool fails 2+ times with similar error pattern
- Attempting to repair hooks using commands that trigger those hooks
- Error message references the system being modified
- Each "fix attempt" produces the same or similar failure

## Required Response When Detected

```
⚠️ CATCH-22 DETECTED

Loop: [describe the recursive dependency]
Example: "Trying to fix hook X, but every file write triggers hook X"

Blocked by: [specific obstacle]
Example: "Hook rejects writes to .claude/hooks/ but I need to write there to fix it"

Attempts made: [list what was tried]

Options for user:
1. Disable hooks via `/hooks off` → I repair → `/hooks on`
2. User performs manual repair:
   - File: [exact path]
   - Change: [exact modification needed]
3. Abandon this approach, try: [alternative strategy]

I cannot proceed without external intervention.
```

## Prohibited Behaviors

- Attempting increasingly creative workarounds (each adds noise, wastes tokens)
- Assuming the next variation will work when 2+ have failed
- Blaming environment/timing without evidence of external change

## Exit Condition

User provides one of the three options above, OR provides new information that breaks the loop.

## Trigger

Activate when:
- Same operation fails 2+ times with similar errors
- Attempting to fix hooks using commands that trigger those hooks
- File operations fail with "modified unexpectedly" repeatedly
- Each fix attempt produces the same or similar failure

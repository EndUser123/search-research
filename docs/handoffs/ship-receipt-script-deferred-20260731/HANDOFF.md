# HANDOFF: ship_receipt.py — automated receipt generation

Session: 019fb3a8-42b6-7e81-91c9-1fad5f4130e6
Date: 2026-07-31
Status: deferred for next session

## Problem

The ship profile has a 15-field receipt template that agents fill by hand. This session proved it's error-prone:
- Emitted duplicate `rollback:` line
- Used `N/A` where gate says "always runs"
- Suggested dangerous `reset --hard` commands (would destroy concurrent-session work)

The issue isn't "try harder" — the template has too many conditional fields for reliable manual execution.

## Proposed solution

Build `ship_receipt.py` — a script that takes verify results as JSON input and emits the receipt mechanically. No room for the agent to put `reset --hard` in the rollback field.

### Input (JSON from ship Phase 0-3)
```json
{
  "repos": {"P:/": {"commits": 5, "pre_head": "abc123"}, "~/.grok": {"commits": 3, "pre_head": "def456"}},
  "branch": "feature/refactor-analyzer",
  "merge_performed": false,
  "review": {"verdict": "clean", "findings": 0},
  "verify": {"tests": "PASS", "lint": "clean", "types": "clean", "behavioral": "3/3"},
  "spec": {"type": "CONTRACT", "invariants": 5},
  "breaking": {"level": "none"},
  "handoff": "updated",
  "wiki": {"promoted": 3}
}
```

### Output: formatted SHIP DONE receipt

The script enforces:
- `rollback:` is `none` when `merge_performed: false` — NEVER emits `reset --hard`
- `spec:` is always one of PASS/CONTRACT/MISMATCH — never N/A
- No duplicate lines

## Why defer

This is a script-building task (~1-2 hours), not a template edit. Next session should implement it with proper tests.

## Files to touch
- Create: `~/.grok/skills/go/__lib/ship_receipt.py`
- Update: `/go` SKILL.md ship profile — replace manual receipt with script call
- Test: `~/.grok/skills/go/__lib/test_ship_receipt.py`

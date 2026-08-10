---
title: "R001 backslash-path PreToolUse hook — implementation ready"
status: OPEN
created: 2026-08-09
last_updated_at: 2026-08-09T20:30:00Z
assignee: unassigned
session_origin: 019fdf3d-a0bd-7062-abc4-24dcf064ae49
---

# R001 backslash-path PreToolUse hook

## Context

Session 019fdf3d designed a code-pattern-checking PreToolUse hook. After
evidence-based pattern selection (scanning 2,496 historical sessions), only
R001 (backslash paths in code) had sufficient incidence to justify a hook
(625 write-tool calls with the pattern). R002 (missing encoding) was dropped
(zero incidence).

The design doc is at: `C:/Users/brsth/AppData/Local/Temp/grok-design-de3d630b/grok-design-doc-de3d630b.md`
(temp — may be reaped by OS). The key decisions are captured below.

## What to build

A new PreToolUse hook (`PreToolUse_code_pattern_checks.py`, ~150 LOC) that:
- Fires on `write|search_replace|Write|Edit` tool calls
- Scans the incoming `new_string` content for backslash Windows paths in Python strings
- Blocks (exit 2) with an educational message citing `[[clickable-file-links-grok-tui-windows]]`
- Uses forward-slash recommendation in the block message

**No shadow period needed.** The evidence (625 incidents across 2,496 sessions)
justifies blocking from day one. Rollback is trivial (rename the JSON).

## Key design decisions (from the /design loop)

- **DEC-01:** New hook, NOT extension of `verify-before-write.py` (different concern: pattern detection vs. unverified constants)
- **DEC-02:** Inline patterns, NOT JSON registry (2-3 patterns doesn't justify registry infrastructure)
- **No shadow period:** Evidence justifies blocking immediately. 14-day shadow was dropped after historical scan.
- **No R002:** Missing-encoding pattern had zero incidence in 2,496 sessions. AGENTS.md prose rule is working.

## Files to create

- `~/.grok/hooks/PreToolUse_code_pattern_checks.py` (~150 LOC)
- `~/.grok/hooks/code-pattern-checks.json` (registration, ~10 LOC)
- `~/.grok/hooks/tests/test_code_pattern_checks.py` (~120 LOC)

## Acceptance criteria

- Hook blocks `open("C:\\folder\\file.txt")` in Python writes
- Hook passes `open("C:/folder/file.txt")` (forward slash)
- Hook passes prose that mentions backslash paths (not in code context)
- Hook fails open on malformed stdin
- All tests pass

## Related

- Design doc: `C:/Users/brsth/AppData/Local/Temp/grok-design-de3d630b/grok-design-doc-de3d630b.md`
- Wiki: `[[evidence-based-hook-pattern-selection]]` (the methodology lesson)
- Existing hook: `~/.grok/hooks/PreToolUse_verify_before_write.py` (the pattern to follow)
- Wiki: `[[clickable-file-links-grok-tui-windows]]` (the hazard this prevents)

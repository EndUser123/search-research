# ADR-20260324: SessionStart TLDR Hook

## Status

Proposed

## Context

After the `feature/chs-consolidation` merge, multiple hook files were orphaned — existing on disk but not registered in the dispatch chain. This was discovered reactively rather than through systematic detection. Additionally, session context is lost after `/compact` or session resume, leaving Claude without visibility into what was accomplished in the previous session.

The hook system currently has two SessionStart health checks:
- `SessionStart_hook_health_check.py` — validates wired hooks (AST parse + import)
- `SessionStart_hook_import_health.py` — validates UserPromptSubmit module imports

Neither detects **orphaned hooks** (files on disk not wired to settings.json).

Separately, a session summary on resume would prevent the "what was I doing?" context loss that happens after compaction.

## Reference Artifacts

- Yurukusa `proof-log-session.sh` (SessionStop → generates 5W1H markdown summary)
- Yurukusa `session-start-marker.sh` (SessionStart → records session start time for duration calc)
- Classmethod verification: SessionStart fires on `startup`, `resume`, `clear`, `compact` matchers
- Current gap: `SessionStart_hook_health_check.py` validates wired hooks only — no orphan detection

## Decision

Implement two Python hooks and one state file:

### Component 1: `SessionStart_tldr.py` (injects session summary)

Fires on all SessionStart matchers (`startup`, `resume`, `clear`, `compact`). Reads the previous session's summary file and injects it via stdout context injection.

**Output format:**
```
## Last Session Summary
**When:** 2026-03-24, 14:30–16:45
**Duration:** ~2h 15m
**Accomplished:**
- Restored PreToolUse_parent_directory_creator.py and Stop_deletion_verification_guard.py
- Fixed Stop_router.py HOOK_SEQUENCE registration
**Files changed:** Stop_router.py, settings.json
**Open items:** None

---
```

If no prior summary exists (first session or after `/clear`): outputs a brief session start marker with no prior context.

### Component 2: `SessionEnd_tldr.py` (writes session summary)

Fires on SessionEnd. Aggregates activity from the session ledger/state files and writes a summary to a shared location.

The summary is written to `P:/.claude/state/session_tldr/last_session.md`.

**Write format:**
```markdown
## Session Summary
**Started:** 2026-03-24T14:30:00Z
**Ended:** 2026-03-24T16:45:00Z
**Duration:** ~2h 15m
**Accomplished:**
- [bulleted list of accomplishments detected from session activity]
**Files changed:** [list of files modified]
**Open items:** [items not yet completed]
```

### Component 3: Session state tracking

Session start timestamp written to `P:/.claude/state/session_tldr/session_start.txt` by SessionStart hook, read by SessionEnd hook to calculate duration.

## Consequences

### Positive
- Eliminates "what was I doing?" context loss after `/compact` or session resume
- Detects orphan hooks (via separate health check hook — see below)
- Follows proven pattern from Yurukusa's 108-hour autonomous operation study

### Negative
- Two new hooks to register and maintain
- SessionEnd requires reliable session ledger data to generate meaningful summaries
- File I/O on session boundaries (mitigated: simple state file, not heavy processing)

## Related: Orphan Hook Detection

The health check gap (wired-only validation) should be addressed separately by extending `SessionStart_hook_health_check.py` to also scan for `.py` files in the hooks directory that are not wired in settings.json.

This can be added as a second pass in the same hook file — one pass validates wired hooks, second pass detects orphans.

## Precedent

- Yurukusa `proof-log-session.sh` / `session-start-marker.sh` — SessionStop + SessionStart coordination pattern
- Classmethod SessionStart verification — confirms `startup`, `resume`, `clear`, `compact` matchers work reliably
- Current `SessionStart_hook_health_check.py` — existing health check pattern to extend

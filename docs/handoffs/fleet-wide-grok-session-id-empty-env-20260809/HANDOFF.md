---
title: Fleet-wide GROK_SESSION_ID empty-env propagation
status: OPEN
created: 2026-08-09
last_updated_at: 2026-08-09T23:00:00Z
session: 019fe25d-6979-7892-82ae-ebf68232312a
host: grok
chronicity: chronic
---

# Fleet-wide GROK_SESSION_ID empty-env propagation

## Problem

`GROK_SESSION_ID` is documented as a runtime-provided env var for hooks and
subprocesses, but it is **NOT populated on Grok Build** (verified empirically
2026-08-09: empty in both PowerShell parent and Python subprocess). At least
16 files across 7 skills assume it propagates and silently fall back to
"unknown-session" / "nosess" / filesystem inference when it doesn't.

This is the same root cause class as the /todo session-scoping bug fixed this
session: [[caller-context-as-parameter-not-callee-discovery]]. Every one of
these callers is an LLM agent that has the session ID in its context but
passes `$env:GROK_SESSION_ID` (empty) instead of the literal.

## Affected files

### SKILL.md files (6 skills, 12 occurrences)

| Skill | File | Line | Pattern |
|-------|------|------|---------|
| close | SKILL.md | 103 | `$sess = $env:GROK_SESSION_ID; if (-not $sess) { $sess = $env:CLAUDE_SESSION_ID }` (both empty → fallback) |
| review | SKILL.md | 137 | `$sess = $env:GROK_SESSION_ID` |
| todo | SKILL.md | 313, 316 | `--session $env:GROK_SESSION_ID` (fallback section) |
| tp | SKILL.md | 387 | `$sid = $env:GROK_SESSION_ID` |
| design | SKILL.md | 354 | `session: $env:GROK_SESSION_ID` |
| maintain | SKILL.md | 113 | `$myTerm = $env:GROK_SESSION_ID` |
| dream | SKILL.md | 178 | lock file uses `$env:GROK_SESSION_ID` |
| model-web | SKILL.md | 381-384 | has a documented fallback (best of the bunch) |
| tp/reference | session-review-protocol.md | 23 | `$sid = $env:GROK_SESSION_ID` |

### Python scripts (10+ occurrences)

| Skill | File | Pattern |
|-------|------|---------|
| handoff | __lib/verify_handoff.py:251 | `getenv("GROK_SESSION_ID", "unknown")` |
| handoff | __lib/migrate_handoff.py:38 | `getenv("GROK_SESSION_ID")` |
| handoff | __lib/list_handoffs.py:42 | `getenv("GROK_SESSION_ID")` |
| handoff | __lib/claim_handoff.py:153 | `getenv("GROK_SESSION_ID", "unknown")` |
| close | __lib/validate_stop_narrative.py:46 | `getenv("GROK_SESSION_ID") or ... or "nosess"` |
| close | __lib/validate_close_receipt.py:45 | same pattern |
| close | __lib/coverage_scan.py:215 | `getenv("GROK_SESSION_ID", "") or getenv("CLAUDE_SESSION_ID")` |
| close | __lib/close_runner.py:49 | `getenv("GROK_SESSION_ID")` |
| aar | __lib/auto_capture.py:62 | `getenv("GROK_SESSION_ID")` |
| aar | __lib/reference_loader.py:46 | same "nosess" pattern |

## Impact

When `GROK_SESSION_ID` is empty:
- **Coverage scans** (`coverage_scan.py`) fall back to filesystem inference → may pick sibling session → wrong scope attribution
- **Handoff claims** (`claim_handoff.py`) record "unknown" as the claiming session → lost coordination signal
- **Close receipts** (`validate_close_receipt.py`) tag with "nosess" → receipts unattributable
- **AAR auto-capture** loses session provenance
- **Session review** (`/tp session`) can't find the session to review

## The fix pattern (consistent with /todo fix)

For each affected skill:

1. **SKILL.md:** change instructions from `$env:GROK_SESSION_ID` to
   "pass your session ID as a literal (the UUID in your session path)"
2. **Python scripts:** add a `--session` CLI arg (or accept it as a
   function parameter) that takes precedence over the env var lookup
3. **Fallback:** keep the env var check as secondary, and add the
   workspace-scoped filesystem inference as a recency-gated last resort
   (same pattern as `scanners/common.py::_filesystem_sid()`)

The agent always has the session ID — it appears in:
- Compaction segment paths
- Continuation prompts
- Session-start references
- The session path in any tool output that references the session dir

## Priority

**Chronic** (recurs every session, affects every skill that needs session
identity). The per-instance severity is low-medium (most scripts degrade
gracefully to "unknown"), but the aggregate cost is high: every session
review, every handoff claim, every close receipt on Grok Build is
unattributed or mis-attributed.

## Acceptance criteria

- [ ] All 9 SKILL.md files updated to instruct agent to pass literal session ID
- [ ] All 10 Python scripts accept `--session` arg or session_id parameter with precedence over env var
- [ ] Fallback chain documented per skill: literal arg → env var → filesystem inference (recency-gated)
- [ ] `/tp session` can resolve its own session ID without `$env:GROK_SESSION_ID`
- [ ] `/handoff list` shows correct claiming session (not "unknown")

## Approach

Batch fix — the pattern is identical across all skills. Either:
- (a) One wave touching all 9 SKILL.md + 10 .py files in parallel, OR
- (b) A shared resolver module (`session_resolver.py` already exists at
  `hooks/scripts/session_resolver.py`) that all skills import, with the
  literal-first / env-second / filesystem-last resolution chain.

Option (b) is the DRY fix and prevents recurrence — but it creates a
shared dependency. Option (a) is lower-risk but leaves the pattern
duplicated. Recommend (b) given the recurrence rate.

## Related

- Fix applied this session: `/todo` scanner (`scan_functions.py` + resolvers)
- Wiki: [[caller-context-as-parameter-not-callee-discovery]]
- Wiki: [[multi-terminal-isolation-stale-data-immunity]]
- Existing resolver: `C:/Users/brsth/.grok/hooks/scripts/session_resolver.py`
  (has the resolution chain but doesn't get the literal-first path right)

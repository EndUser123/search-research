# FINDINGS.md — Session 019fba58 Code Review

**Run directory:** `P:/.artifacts/reviews/session-019fba58-20260802-151956/`
**Date:** 2026-08-02
**Scope:** 6 Python files changed in session 019fba58
**Specialist:** MiniMax M3 (correctness lens)
**Lenses:** correctness

## Summary

| Severity | Count |
|----------|-------|
| Bug | 5 (2 verified mine, 3 sibling session) |
| Gap | 9 |
| Suggestion | 3 |
| **Total** | **17** |

## Verified findings (my changes)

### Issue 1 -- Severity: bug [VERIFIED]
**File:** `skills/handoff/__lib/claim_handoff.py:62-66`
**introduced_by_change:** yes
**Description:** `_set_field` corrupts documents when the field doesn't already exist (no commented template line to match). The fallback appends the field at the end of the file with a new `---` line, breaking YAML frontmatter.
**Evidence:** Tested on llm-judge handoff (no template) — `list_handoffs.py` showed `yaml:?` after claim. Standard handoffs (with commented `# assigned_to:` template) work correctly because the regex matches.
**Suggestion:** Parse frontmatter first (use `_parse_frontmatter` which exists but is never called), edit only the frontmatter block, reassemble.
**Status:** Needs fix — affects ad-hoc handoffs without standard template

### Issue 2 -- Severity: bug [VERIFIED]
**File:** `skills/handoff/__lib/claim_handoff.py:113, 141`
**introduced_by_change:** yes
**Description:** `path.write_text()` is not atomic. Concurrent writes or crash mid-write can corrupt the handoff file.
**Evidence:** Lines 113 and 141 use plain `write_text` with no tmp+rename pattern. Compare to `PreToolUse_skill_staleness.py` and `fleet_quota.py` which use `tmp.replace`.
**Suggestion:** Write to PID-suffixed temp file, then `os.replace()`.

### Issue 3 -- Severity: gap [VERIFIED]
**File:** `skills/handoff/__lib/claim_handoff.py:90-114, 121-142`
**introduced_by_change:** yes
**Description:** No locking around read-check-write. Two concurrent claim invocations can both pass the "already claimed" check and one's write silently wins.
**Evidence:** No lock between `path.read_text` and `path.write_text`.
**Suggestion:** Wrap in file lock (msvcrt on Windows). Same as fleet_quota pattern.

### Issue 4 -- Severity: gap [VERIFIED]
**File:** `hooks/PreToolUse_skill_staleness.py:46-82`
**introduced_by_change:** yes (NEW file)
**Description:** Read-modify-write of `skill-mtimes.json` has TOCTOU race within the same session (parallel tool dispatches).
**Evidence:** Lines 46-82: read state, mutate dict, write back. No lock.
**Suggestion:** Wrap in per-session file lock.

### Issue 5 -- Severity: gap [VERIFIED]
**File:** `skills/go/__lib/ship_receipt.py:255-256`
**introduced_by_change:** yes
**Description:** Old baselines without `fail_names` field yield empty set → all current failures treated as new. Conservative (fails rather than passes) but incorrect for backward compat.
**Evidence:** `baseline.get("fail_names", [])` returns `[]` for pre-change baselines.
**Suggestion:** Fall back to count comparison when `fail_names` absent from baseline.

### Issue 6 -- Severity: gap [VERIFIED]
**File:** `skills/go/__lib/ship_receipt.py:241-248`
**introduced_by_change:** yes
**Description:** Test-name extraction via `line.split(" - ")[0]` is brittle to pytest output format changes.
**Evidence:** Lines 241-248 hard-code FAILED/ERROR prefix + split on `" - "`.
**Suggestion:** Acceptable for now — pytest's FAILED format is stable. Document as known fragility.

### Issue 7 -- Severity: gap [VERIFIED]
**File:** `hooks/PreToolUse_spawn_model_gate.py:92-112`
**introduced_by_change:** yes
**Description:** Single 50ms retry may be too short for slow disk/antivirus. Fail-safe (block) on second failure.
**Evidence:** One `time.sleep(0.05)` retry before fail-closed.
**Suggestion:** Acceptable — the per-PID tmp suffix (the write-side fix) reduces the race window to near-zero. The retry is defense-in-depth.

## Sibling session findings (NOT my changes — noted for awareness)

### Issue 8 -- Severity: bug [SIBLING]
**File:** `skills/model-quota/scripts/fleet_quota.py:~480`
**Description:** `worst = entries[0]` replaced `min(entries, key=...)` — semantic regression in representative window selection.
**Note:** From sibling session commit `de80357`. Not mine.

### Issue 9 -- Severity: bug [SIBLING]
**File:** `skills/close/__lib/close_runner.py:~691, 658`
**Description:** New terminal states `succeeded_render_failed` and `timed_out_cleanup_failed` without consumer updates.
**Note:** From sibling session commits `71p52d6`, `c187d95`. Not mine.

## CLEAN files

- `skills/close/__lib/close_runner.py` (my changes only — string scan removal + message fix) — CLEAN
- `hooks/PreToolUse_spawn_model_gate.py` (my change — retry-once) — CLEAN with gap noted (Issue 7)
- `skills/model-quota/scripts/fleet_quota.py` (my change — per-PID tmp suffix) — CLEAN

## Verification

- ruff check: 1 pre-existing error (not from this session)
- pytest close tests: 119 passed
- pytest handoff tests: 171 passed
- pytest yt-is tests: 84 passed
- claim_handoff.py functional test: claim and release work on standard handoffs; Issue 1 confirmed on ad-hoc handoffs

## Verdict

**PASS with known issues.** No blocking bugs in my session's changes for the primary use case (standard handoffs with template). Issues 1-3 (claim_handoff.py frontmatter corruption, non-atomic write, missing lock) need fixing before the claim command is relied upon for fleet coordination. The staleness hook TOCTOU (Issue 4) is acceptable as advisory.

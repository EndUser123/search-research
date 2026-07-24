# /review — Session 019f7cc5 close/handoff skill changes

**Date:** 2026-07-23
**Target:** `/close` and `/handoff` skill changes from session 019f7cc5
**Verdict:** FAIL — 4 blocking issues + 8 non-blocking

## Blocking issues

### Issue 1 — bug: `git add` missing `--` separator (flag injection)
- **File:** `close_accounting.py:979`
- A file_path starting with `-` would be parsed as a git flag
- **Fix:** `["git", "add", "--"] + files_to_stage`

### Issue 2 — bug: "nothing to commit" checks stdout, git writes to stderr
- **File:** `close_accounting.py:991-995`
- Race-condition recovery unreliable on modern git
- **Fix:** Check combined stdout+stderr, or check returncode only

### Issue 3 — gap: auto-commit doesn't exclude directories or workspace root
- **File:** `close_accounting.py:957-973`
- A `file_path = "P:/"` or directory path would stage entire repo
- **Fix:** `if not p.is_file(): continue` + workspace boundary check

### Issue 4 — gap: scanner template still has other-sessions' bucket
- **File:** `close_accounting.py:1169`
- SKILL.md removed it but scanner still emits it
- **Fix:** Drop `| {counts['handoffs_other']} other-sessions'` from line 1169

### Issue 5 — gap: Decisions field removed from output template but still in scanner
- **File:** `close_accounting.py:1184` vs SKILL.md output template
- **Fix:** Either restore Decisions line in template, or remove from scanner

### Issue 6 — gap: Tier table lists WIP-commit as Tier 2 but git gate says Tier 1
- **File:** SKILL.md line 74 vs line 134
- **Fix:** Remove WIP-commit from Tier 2 examples

### Issue 7 — gap: Retrospective SKILL.md says "friction occurred" but scanner triggers on "substantive work"
- **File:** SKILL.md line 84 vs close_accounting.py:824
- **Fix:** Replace "friction occurred" with "substantive work happened"

### Issue 8 — bug: commit_sha regex requires branch name "main"
- **File:** `close_accounting.py:998`
- **Fix:** `r'\[[\w./-]+ ([a-f0-9]+)\]'`

## Non-blocking suggestions

- Combine two chat_history.jsonl passes into one (perf)
- Tighten `r"pytest"` to `r"\bpytest\b"` (false positive risk)
- Define `_EDIT_THEN_VERIFY_WINDOW_LINES = 10` as named constant
- Remove dead `event_type` variable
- Fix stale `remaining` count after auto-commit
- Add "when NOT to apply" scope clause to problem-first decomposition rule
- Use `WORKSPACE` constant instead of hardcoded `Path("P:/")`
- Include gate-level details (commit_sha, verify_count) in --format summary

## Sources
- Code review subagent: `019f8dc7-6c0b-7510-9383-41f4cdc4e8c6`
- Prose review subagent: `019f8dc7-afb2-7f60-b3d1-e00e30afbae9`

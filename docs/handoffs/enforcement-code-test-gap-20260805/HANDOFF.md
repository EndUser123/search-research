---
thread_id: a3f7c1e2-8b5d-4f2a-9e6c-1d0e3f5a7b9c
parent_handoff_path: none
current_session_id: 019fca0e-9f40-7110-919b-6ee89333f804
parent_session: none
current_terminal_id: c2a1f721-fb8f-4719-ae26-9f89
produced_at: 2026-08-05T00:15:00Z
last_updated_by: 019fca0e-9f40-7110-919b-6ee89333f804
last_updated_at: 2026-08-05T00:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: e6b10e7bfc0e5082016b92794324098af55ae65f
---

# Enforcement code test gap — ship_receipt.py + script_scan.py

## Objective

Add mechanical test coverage for enforcement code in `ship_receipt.py` and `script_scan.py` that currently has zero tests, and fix the highest-severity pre-existing bugs found by the specialist review.

**Scope bounds:** Work scope is 2 files (`ship_receipt.py`, `script_scan.py`) with ~16 findings. The broader fleet has many untested enforcement functions; this handoff covers only the two files touched by session 019fca0e.

## Status

OPEN

## Producing context

- Date: 2026-08-05
- Session: 019fca0e-9f40-7110-919b-6ee89333f804
- Terminal: c2a1f721-fb8f-4719-ae26-9f89
- Host: grok
- Source: `/ship` Phase 1 specialist review (explore subagent 019fd0ba, 2026-08-05)

## Read-first list

1. `P:/.data/wiki/concepts/enforcement-code-needs-its-own-mechanical-tests.md` — the meta-pattern and why this matters
2. `~/.grok/skills/ship/__lib/ship_receipt.py` — the enforcement code with bugs (lines 715-820 `check_skill_receipts`, 1095-1170 `verify_specialist_spawn`, 423-560 doc-check helpers, 125-130 git state collection, 551 rename regex, 770 stub detection, 868-895 `_clean_detail`)
3. `~/.grok/skills/ship/tests/test_ship_receipt.py` — existing tests (41 pass, but `check_skill_receipts` and `verify_specialist_spawn` not imported)
4. `~/.grok/skills/skill-dev/__lib/script_scan.py` — scanner with 8 checks, no tests directory exists
5. `~/.grok/skills/ship/SKILL.md` — the ship contract (what the enforcement code is supposed to gate)

## Verified facts

- [FACT] `check_skill_receipts()` has zero test coverage (ship_receipt.py:715-820, not in test_ship_receipt.py imports — verified by specialist subagent reading the import list at line 19)
- [FACT] `verify_specialist_spawn()` has zero test coverage (ship_receipt.py:1095-1170, not in test imports — verified by specialist)
- [FACT] `verify_specialist_spawn()` fails open when transcript not found (ship_receipt.py:1130,1135 — returns `(True, ...)`) — this is a security bypass
- [FACT] `script_scan.py` has no `tests/` directory (verified via `list_dir` — no tests exist)
- [FACT] `script_scan.py` Check 4 `"R" in body_str` is trivially True (script_scan.py:280 — AST dumps contain uppercase R in node names like "Return", "args")
- [FACT] `_resolve_renamed_file()` regex misses `RM`/`RD` status codes (ship_receipt.py:551 — regex `^R\d*\s+` doesn't match `RM old -> new`)
- [FACT] `collect_git_state()` uses inconsistent ranges: `HEAD~10..HEAD` for log but `HEAD~1..HEAD` for diff (ship_receipt.py:125-130)
- [FACT] 41 existing tests pass, lint clean on all 3 changed Python files (verified via `pytest` + `ruff`, 2026-08-05)

## Current state

### Already in place
- Session 019fca0e added `check_skill_receipts()`, Check 7 (LLM-fillable), Check 8 (craft quality) — code is committed and functional
- Wiki concept `enforcement-code-needs-its-own-mechanical-tests.md` documents the meta-pattern
- Specialist review (subagent 019fd0ba) produced the full findings list
- Existing test suite: 41 tests for `derive_verdict`, `validate_phase_log`, `render_receipt`, `_derive_ship_run_id`

### Not yet in place
- Tests for `check_skill_receipts()`, `verify_specialist_spawn()`, `_resolve_renamed_file()`, `_check_wikilinks()`, `_check_code_fences()`, `_check_frontmatter()`
- Tests for `script_scan.py` Checks 1-8
- Fix for `verify_specialist_spawn()` fail-open (bug #1)
- Fix for `script_scan.py` Check 4 dead heuristic (bug #2)
- Fix for `_resolve_renamed_file()` regex (bug #3)
- Fix for `collect_git_state()` range inconsistency (bug #5)
- Fix for `script_scan.py` Check 7 false-negative scope (bug #7)

## Task packets

### ENF-TEST-01: Add tests for check_skill_receipts()
- **goal:** 8 test cases covering positive/negative/stub/session-scoping/missing-dir
- **in scope:** `~/.grok/skills/ship/tests/test_check_skill_receipts.py` (new file)
- **out of scope:** `verify_specialist_spawn()` (separate task), `script_scan.py` (separate task)
- **files / anchors:** `ship_receipt.py:715-820` (the function under test)
- **acceptance:** `pytest tests/test_check_skill_receipts.py` passes with ≥8 test cases; all edge cases from the specialist's finding #17 are covered
- **falsifier:** any test case produces a false positive (FOUND when receipt doesn't exist) or false negative (MISSING when valid receipt exists)
- **verification level required:** UNIT_TEST
- **estimate:** ~30 min (8 test cases + fixture setup)

### ENF-TEST-02: Add tests for verify_specialist_spawn()
- **goal:** 5 test cases covering spawn detected / not detected / transcript missing / encoding mismatch / empty transcript
- **in scope:** `~/.grok/skills/ship/tests/test_verify_specialist_spawn.py` (new file)
- **out of scope:** the fail-open fix (ENF-FIX-01)
- **files / anchors:** `ship_receipt.py:1095-1170`
- **acceptance:** `pytest tests/test_verify_specialist_spawn.py` passes with ≥5 test cases
- **falsifier:** test passes for the fail-open case without documenting that it's testing current (broken) behavior vs desired (fail-closed) behavior
- **verification level required:** UNIT_TEST

### ENF-TEST-03: Add tests for script_scan.py
- **goal:** at least 1 fixture per check (8 checks = 8 minimum test cases)
- **in scope:** `~/.grok/skills/skill-dev/tests/test_script_scan.py` (new file + new tests/ dir)
- **out of scope:** fixing the Check 4 heuristic (ENF-FIX-02)
- **files / anchors:** `script_scan.py` (whole file — each check function)
- **acceptance:** `pytest tests/test_script_scan.py` passes; each check has at least one positive and one negative test
- **falsifier:** a check that should detect a pattern passes when the pattern is absent, or fails when present
- **verification level required:** UNIT_TEST

### ENF-FIX-01: Fix verify_specialist_spawn() fail-open
- **goal:** change fail-open to fail-closed; add `--no-transcript-verify` escape hatch
- **in scope:** `ship_receipt.py:1130,1135`
- **out of scope:** other enforcement functions
- **files / anchors:** `ship_receipt.py` function `verify_specialist_spawn`
- **acceptance:** when transcript not found, returns `(False, "transcript not found")`; escape hatch works when explicitly passed
- **falsifier:** any legitimate ship is blocked because transcript path encoding doesn't match either of the two tried variants
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR (test with real `/ship` invocation)
- **depends_on:** ENF-TEST-02 (tests must exist before changing the function)

### ENF-FIX-02: Fix script_scan.py Check 4 heuristic + Check 7 scope
- **goal:** replace `"R" in body_str` with AST-level check; limit Check 7 skip to skill-dev's own SKILL.md only
- **in scope:** `script_scan.py:280` (Check 4), `script_scan.py:467-478` (Check 7)
- **out of scope:** other checks
- **acceptance:** Check 4 correctly detects rename handling; Check 7 doesn't skip LLM-fillable detection for non-skill-dev SKILL.md files
- **falsifier:** Check 4 still fires trivially; Check 7 still skips for irrelevant files
- **verification level required:** UNIT_TEST
- **depends_on:** ENF-TEST-03

### ENF-FIX-03: Fix _resolve_renamed_file() regex + collect_git_state() range
- **goal:** regex matches RM/RD/RA; git log and diff use the same range
- **in scope:** `ship_receipt.py:551` (regex), `ship_receipt.py:125-130` (range)
- **out of scope:** other functions
- **acceptance:** `RM old.py -> new.py` is correctly parsed; receipt shows same commit count as files checked
- **falsifier:** renamed+modified file still skips inline doc-checks
- **verification level required:** UNIT_TEST

## Open decisions

None — the fixes are clearly correct per the specialist review. The only decision is priority order (tests first vs fixes first). Recommendation: tests first (ENF-TEST-01-03), then fixes (ENF-FIX-01-03), so the fixes can be verified by the tests.

## Hard constraints

- Do NOT change the fail-open behavior without adding the `--no-transcript-verify` escape hatch — some legitimate ship scenarios have no transcript
- Do NOT remove the Check 7 self-detection entirely — it's needed for skill-dev's own SKILL.md. Just narrow the scope.
- Tests must use real fixtures (anti-mock stance per AGENTS.md testing rules)

## Cross-reference couplings

- `ship_receipt.py:check_skill_receipts()` → reads `P:/.artifacts/` for `check-run.json` + `FINDINGS.md`. If artifacts dir is missing, function returns MISSING silently.
- `script_scan.py` Check 7 → references "Check 8" in SKILL.md to skip self-detection. If Check 8 documentation is removed, the skip breaks.
- Wiki concept `enforcement-code-needs-its-own-mechanical-tests.md` → documents the meta-pattern. If this handoff's fixes are applied, the concept should be updated with "resolved" status.
- `~/.grok/AGENTS.md` "Execution receipts for executable artifacts" → establishes the rule this handoff implements. No dangling reference.

## Other outstanding streams

- **`/close` meta_checkpoint deadlock** — scanner always emits `needs_llm_check` for meta_checkpoint, runner requires `pre_satisfied`. Scanner design bug, not a session gap. Low priority.
- **Push both repos** — unpushed commits in both P:/ and ~/.grok from this session + sibling sessions. Operator decision.

## Explicit non-goals

- Do NOT rewrite ship_receipt.py or script_scan.py — surgical fixes only
- Do NOT add tests for all fleet enforcement code — only the 2 files touched by session 019fca0e
- Do NOT change the receipt-file enforcement design — it's structurally sound, the bugs are in execution
- Do NOT fix all 7 suggestions from the specialist — those are improvements, not bugs

## Resumption protocol

1. Read `P:/.data/wiki/concepts/enforcement-code-needs-its-own-mechanical-tests.md` for context
2. Read the specialist findings in the AAR report at `P:/.artifacts/grok-aar/console_console_c2a1f721-fb8f-4719-ae26-9f89/20260804-222826/aar-report.md`
3. Start with ENF-TEST-01 (tests for `check_skill_receipts`) — it's the highest-value task because it verifies the session's key deliverable

## Suggested next invocation

```
/go Add tests for check_skill_receipts() in ship_receipt.py — 8 test cases covering positive/negative/stub/session-scoping/missing-dir. Read the specialist review at P:/.artifacts/grok-aar/console_console_c2a1f721-fb8f-4719-ae26-9f89/20260804-222826/aar-report.md for the full findings list. Start with ENF-TEST-01.
```

## Last user message (verbatim)

> "/handoff"

## Epistemic labels per claim

- [FACT] 7 bugs, 9 risks, 7 suggestions found by specialist subagent 019fd0ba (receipt: subagent output in transcript)
- [FACT] `check_skill_receipts()` and `script_scan.py` have zero test coverage (receipt: `list_dir` + import list inspection)
- [FACT] 41 existing tests pass (receipt: `pytest tests/test_ship_receipt.py` output)
- [INFERENCE] the fail-open in `verify_specialist_spawn()` is a bug, not a design choice — the escape hatch pattern suggests the intent was fail-closed with override
- [UNKNOWN] whether the encoding mismatch in `verify_specialist_spawn()` actually causes failures in practice — needs empirical testing against real Grok Build session paths

## Suggested skills for next session

- `/go` — 3 test-writing task packets + 3 fix task packets, all ready to execute
- `/check` — after tests are written, verify they catch the bugs they're supposed to
- `/review` — review the test quality (anti-mock stance, fixture realism)
- `/wiki` — update `enforcement-code-needs-its-own-mechanical-tests.md` with "resolved" status after fixes land

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-05T00:15 | 019fca0e | created |

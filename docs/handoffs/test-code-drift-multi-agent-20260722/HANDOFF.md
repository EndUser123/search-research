---
thread_id: test-code-drift-multi-agent-20260722
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T13:30:00Z
status: CLOSED
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: 642c7ab
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: Test-code drift on multi-agent hosts — structural fix needed

## Objective (one sentence)

Install a coverage gate so that concurrent-session code changes to `__lib/*.py` files automatically fail the test suite when coverage drops — preventing the 4-version test drift observed on `/close`'s scanner.

## The problem (verified, this session)

The `/close` skill evolved through 5 versions across 2 sessions in one day:

| Version | Code change | Tests updated? |
|---------|-------------|----------------|
| v1 | Prose /close + 10 tests for v1 helpers | ✅ |
| v2/v3 | Rewrote to scanner-based (22KB `close_accounting.py`) | ❌ |
| v4 | Added 3 new gates (temp, git, background) | ❌ |
| v5 | Added Decisions gate + auto-promotion | ❌ |
| Fix | Wrote 24 scanner tests | ✅ (only because operator asked) |

Tests were stale for **4 versions** before anyone noticed. The operator caught it, not any mechanism on the host. The scanner grew from 0 to 30KB of load-bearing runtime code with zero test coverage until this session's fix.

## Root cause

**Each session optimizes for its own changes without visibility into what other sessions' tests cover.** The concurrent session that wrote the scanner didn't know v1 tests existed, or that they'd become stale. v1 tests didn't know the scanner would replace them. Advisory rules ("edit-then-verify", ">80% coverage") fire on what you do, not on what you skip — and nothing fires on the *absence* of a paired test update when a different session changes the code.

This is the same structural gap as every other multi-agent coordination failure on this host: advisory rules work for single-agent work and silently fail when concurrent sessions edit the same artifact independently.

## What's done (verified)

- Scanner tests written: `tests/test_scanner.py` (24 tests covering `resolve_gates`, `compute_loop`, `_classify_handoff`, `_has_code_commits`, `_extract_work_status`, `scan_temp_files`, `_check_consolidation`)
- Combined suite: 34 tests, all pass in 0.19s
- Gap diagnosed with root cause documented

## What needs to be built

### Option A: Coverage gate (recommended)

Add `pytest --cov` enforcement so test runs FAIL when scanner coverage drops below a threshold.

**Implementation:**
1. Add a `pyproject.toml` or `pytest.ini` in the skill dir:
   ```toml
   [tool.pytest.ini_options]
   addopts = "--cov=close_accounting --cov-fail-under=80 --cov-report=term-missing"
   ```
2. Or add a `conftest.py` that enforces coverage on `__lib/*.py` modules
3. Verify: `python -m pytest tests/` fails if coverage < 80%

**Why this works mechanically:** doesn't care *who* changed the scanner or *why*. Just reports "this function has no test" and fails. Same pattern as the dynamic cap on `dgemma_read.py` — derive the constraint from the real requirement (coverage), not from a rule that depends on model compliance.

**Scope:** applies to `/close` initially. Once proven, extend the pattern to `/handoff`, `/aar`, `/review`, `/check` (all have `__lib/` code that evolved this session).

### Option B: PreToolUse hook (optional, on top of A)

Detect edits to any `__lib/*.py` file; if the corresponding `tests/test_*.py` wasn't also edited in the same session, warn: "code changed but tests may not be updated." Semi-mechanical — detects the *absence* of a paired edit. May be noisy for trivial edits.

**Implementation:**
- Hook script in `~/.grok/hooks/` that checks file paths on `write`/`search_replace` to `__lib/` patterns
- Checks whether `tests/` was touched in the same session (via session transcript or `.artifacts/` state)
- Warns (not blocks) if code was touched but tests weren't

### Option C: Skill convention (alone — NOT recommended)

Add to SKILL.md Hard Constraints: "Any edit to `__lib/*.py` requires updating or explicitly justifying the corresponding test." This is what we have now, and it failed for 4 versions. Advisory-only; weakest enforcement.

## Acceptance criteria

1. `python -m pytest tests/` in the `/close` skill dir includes coverage reporting
2. Coverage < 80% on `close_accounting.py` causes test failure (not just a warning)
3. The coverage gate catches the specific drift scenario: scanner gains a new function → test suite fails because the new function has no test
4. Pattern is documented so other skills (`/handoff`, `/aar`, `/review`, `/check`) can adopt it
5. Coverage threshold (80%) is justified, not arbitrary — cite what coverage the current 24 scanner tests actually achieve

## Multi-terminal notes

The coverage gate is session-agnostic — it runs in any session that runs the tests. It doesn't need terminal-scoped state. It catches drift regardless of which session caused it. This is the right layer for the fix.

## Resumption protocol

1. Read this handoff (the drift scenario + the 3 options)
2. Read the current scanner: `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py`
3. Read the current tests: `C:/Users/brsth/.grok/skills/close/tests/test_scanner.py`
4. Implement Option A (coverage gate via pyproject.toml/pytest.ini)
5. Run `python -m pytest tests/ -v` and confirm coverage reporting works
6. Optionally: temporarily remove one test to confirm the gate FAILS when coverage drops
7. Document the pattern for adoption by other skills

## Related artifacts

- Scanner: `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py` (30KB, 17 functions)
- Tests: `C:/Users/brsth/.grok/skills/close/tests/test_scanner.py` (24 tests)
- Wiki: `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` (adjacent: the tool-call capability dimension)
- Precedent: `dgemma_read.py` dynamic cap (same "derive constraint from real requirement" pattern)

## Falsifier

This fix is wrong if:
- Coverage threshold (80%) is too strict and causes false failures on legitimate code-only changes → lower threshold or use `--cov-fail-under` with a floor that allows infrastructure code without tests
- The coverage gate doesn't actually catch the drift scenario (new function added but not tested) → verify by adding a dummy function and confirming the gate fails
- The pattern doesn't generalize to other skills → each skill's `__lib/` structure may differ; adapt per skill

If any pattern appears within 3 months, iterate.

---
title: "close_runner.py Windows-path JSON-stringification bug — fix needed"
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
source_session: 019fb933-040b-7720-a257-e364f5df726f
produced_at: 2026-08-02T05:00:00Z
status: OPEN — not started
priority: HIGH
tags: [close-runner, windows, path-bug, winerror-123, gate-evaluation, pre-existing-defect]
accurate_as_of_head: needs_verification
---

# Handoff: close_runner.py Windows-path JSON-stringification bug — fix needed

## Objective

Fix the Windows-path handling bug in `close_runner.py` at line ~137 that crashes the close-gates scanner when `--session` is passed as a JSON object. The bug stringifies the JSON dict into a directory-name component, producing `P:/.artifacts/close-evidence/{model_a: ...}` which Windows rejects with OSError WinError 123. Until fixed, every close-check run on Windows with a JSON-dict `--session` argument reports "0 gates evaluated" (misleading state — no gates were actually produced, the scanner crashed).

## Status

OPEN — bug identified in session 019fb933 close-check sweep, fix not yet implemented.

## Producing context

- Date: 2026-08-02
- Session: `019fb933-040b-7720-a257-e364f5df726f` (close-check sweep, Remediate phase)
- Host: grok (Grok Build)

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/close-runner-windows-path-json-stringification-bug.md` — wiki concept with full RCA
2. `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — consumer workflow
3. `close_runner.py` line ~137 — the buggy site (path read or written)
4. `P:/.claude/scripts/close_runner.py` or `~/.grok/hooks/scripts/close_runner.py` (verify location)

## Verified facts

- [FACT] close_runner.py crashed with OSError WinError 123 when --session was a multi-key JSON dict (source: close-check journal for wf_019fc0c683807f8083b23cb2f04a6eee, mechanical-sweep agent output)
- [FACT] The crash produced a two-stage failure: `run_close_scanner` returned `_finish('blocked')` then `_finish('failed')`; both attempts to write the receipt also hit WinError 123 (source: same journal entry)
- [FACT] The visible result was "0 gates evaluated" — a misleading state where no gates were produced because the scanner crashed before evaluation (source: pre-close-report.md, close-gates check, [SESSION] finding)
- [FACT] The bug is pre-existing — it predates session 019fb933 by an unknown number of sessions (source: no commit in this session touches close_runner.py)
- [FACT] A wiki concept was created documenting the bug (source: P:/.data/wiki/concepts/close-runner-windows-path-json-stringification-bug.md)

## Current state

- Bug identified, root cause known (JSON-stringified path → Windows rejects curly braces)
- Wiki concept written
- Tool-fallbacks.md has a related entry for or-ling-3-flash-free single-agent non-completion
- close_runner.py not patched

## Task packets

### T1: Locate close_runner.py and identify the path-building line

- **id:** CR-01
- **goal:** Find the close_runner.py file in this workspace and read line ~137 (path construction site)
- **in scope:** Search for `close_runner.py` across `~/.grok/`, `P:/.claude/`, `P:/packages/`
- **out of scope:** Patching (T2)
- **acceptance:** File located, path-building line confirmed, current code quoted in handoff revision
- **falsifier:** File doesn't exist (then scope to close-runner equivalent; check workflow scripts)
- **verification level required:** STATIC_INSPECTION
- **estimate:** 10 minutes

### T2: Patch close_runner.py to Windows-safe the --session argument

- **id:** CR-02
- **goal:** Replace the JSON-stringified path with a sanitized/hashed form
- **in scope:** close_runner.py path construction (line ~137)
- **out of scope:** Other close_runner.py functionality
- **acceptance:** close-check produces non-zero gate evaluations on Windows with JSON-dict `--session` argument; WinError 123 no longer occurs
- **falsifier:** Same WinError 123 occurs after patch (then investigate other path-building sites)
- **verification level required:** LIVE_BEHAVIOR (run close-check on Windows, confirm gate count > 0)
- **proposed approach:** Hash `--session` to a 32-char SHA-256 prefix; build path as `P:/.artifacts/close-evidence/<hash>/`. Avoid embedding raw session identifiers in the path.

### T3: Re-run close-check and verify gate evaluation

- **id:** CR-03
- **goal:** Confirm the fix produces real gate evaluations (not "0 gates evaluated")
- **in scope:** close-check workflow run with same JSON-dict `--session` argument as session 019fb933
- **out of scope:** Other close-check improvements
- **acceptance:** pre-close-report.md shows `pre_satisfied/needs_attention/needs_llm_check/skip` gate counts > 0
- **falsifier:** "0 gates evaluated" persists (then dig deeper into the scanner logic)
- **verification level required:** LIVE_BEHAVIOR

## Open decisions

### OD-01: Path scheme after fix

- **Question:** After hashing --session, should the evidence dir name preserve any human-readable prefix (e.g., first 7 chars of session_id) for cross-referencing?
- **Options:** (1) Pure hash, no prefix [maximum safety, less readable] (2) `<7-char-prefix>-<hash>` [balances safety and readability] (3) Always sanitize and replace `{` `}` only [minimal change, retains other JSON chars]
- **Selection criterion:** path safety vs operator debuggability
- **Currently leads:** Option 2 (readable prefix + hash suffix)

## Hard constraints

- Do NOT modify close-check.rhai — the bug is in close_runner.py, not the workflow script
- Do NOT skip T3 verification — the LIVE_BEHAVIOR test is required to confirm the fix worked
- The patch must not break the close_runner.py behavior on POSIX (Linux/macOS); Windows-safe paths are a strict subset of POSIX-safe paths

## Cross-reference couplings

- `P:/.data/wiki/concepts/close-runner-windows-path-json-stringification-bug.md` — full RCA + receipts
- `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — consumer workflow
- `P:/docs/handoffs/close-check-lifecycle-019fb937-20260802/HANDOFF.md` — related close-check lifecycle work

## Resumption protocol

1. Read this handoff + the wiki concept (read-first list)
2. Run T1 (locate close_runner.py)
3. Implement T2 (patch path construction)
4. Run T3 (verify gate evaluation works)
5. Commit with message: `fix(close-runner): hash --session to Windows-safe path component`
6. Update the wiki concept with the patch SHA + add `[FIXED 2026-08-0X]` marker

## Suggested next invocation

```
/go CR-01 -- locate close_runner.py and quote line ~137
```

## Last user message (verbatim)

> "Run the /capture skill. Read ~/.grok/skills/capture/SKILL.md for the workflow format, then execute it using the pre-packed evidence below. The sweep already identified corrections, friction, and gaps — use that evidence to drive the 7-category scan."

## Epistemic labels per claim

- "close_runner.py crashed with WinError 123" — `[FACT]` (source: close-check journal entry)
- "The bug is at line ~137" — `[INFERENCE]` (line number cited in pre-close-report.md, exact line not yet read)
- "The bug is pre-existing" — `[FACT]` (source: no commit in this session touches close_runner.py)
- "Hash --session with SHA-256 prefix" — `[RECOMMENDATION]` (standard Windows-safe path handling)
- "Patch will not break POSIX" — `[INFERENCE]` (Windows-safe is a subset of POSIX-safe)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:00 | 019fb933... | created |
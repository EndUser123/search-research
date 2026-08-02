---
title: "close_runner.py Windows-path JSON-stringification bug"
created: 2026-08-01
source: session-019fb933
tags: [close-runner, windows, path-bug, winerror-123, near-miss, gate-evaluation, pre-existing-defect]
agent: grok
host: grok
cognitive_load: 2
verification: observed
---

## Summary

close_runner.py at line ~137 treats the --session JSON argument as a directory name component. When --session is a multi-key JSON dict, Python's json.dumps produces a string with curly braces (e.g., `{model_a: minimax-m3, ...}`). On Windows, curly braces are illegal in file paths, causing OSError WinError 123. This crashes the close-gates scanner entirely, producing "0 gates evaluated" — a misleading state where no gates were actually produced because the scanner crashed before evaluation.

## Why this matters

This is a pre-existing defect that blocks the close-check workflow on Windows whenever a JSON-dict session identifier is passed. The bug predates session 019fb933 by an unknown number of sessions. Every close-check run on Windows with a JSON-dict `--session` argument is silently broken.

## Evidence

- [FACT] close_runner.py crashed with OSError WinError 123 when --session was a multi-key JSON dict (source: close-check journal for wf_019fc0c683807f8083b23cb2f04a6eee)
- [FACT] The crash produced a two-stage failure: run_close_scanner returned _finish('blocked') then _finish('failed'); both attempts to write the receipt also hit WinError 123 (source: same journal entry)
- [FACT] The visible result was "0 gates evaluated" — a misleading state (source: pre-close-report.md, close-gates check)
- [FACT] The bug is pre-existing — no commit in session 019fb933 touches close_runner.py (source: git log)

## Related artifacts

- Handoff: `P:/docs/handoffs/close-runner-windows-path-bug-fix-20260802/HANDOFF.md`
- Wiki concept: `close-runner-json-arg-parsing-bug.md` (related but different bug — JSON arg parsing vs path stringification)

## Falsifier

If close_runner.py is patched to sanitize the --session argument for Windows path safety and the close-check workflow produces non-zero gate evaluations on Windows with a JSON-dict --session argument, this concept is resolved.

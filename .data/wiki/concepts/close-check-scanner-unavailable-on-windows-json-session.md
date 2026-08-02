---
title: "Close-check scanner unavailable on Windows with JSON session"
type: concept
tags: [close-check, windows, json-session, scanner]
created: 2026-08-02
source: session 019fa8f8, close-gates FAIL
---

# Close-check scanner unavailable on Windows with JSON session

## Summary

The close-check scanner is unavailable when the --session argument is a JSON dict on Windows. The close_runner.py path-building code stringifies JSON dict arguments into directory names, producing paths like `P:/.artifacts/close-evidence/{model_a: ...}` which Windows rejects with OSError WinError 123 (path too long or invalid characters).

## Context

The close-runner constructs file paths from the --session argument. When --session is a JSON dict (multi-key), the string representation includes colons, braces, and spaces that are invalid in Windows file paths. This causes WinError 123, which crashes the scanner and prevents all close-check operations from completing.

## Pattern

1. Session has multiple models in play (model_a, model_b, model_c)
2. Close-runner receives --session as a JSON dict
3. Path construction stringifies the dict into a directory name
4. Windows rejects the path with WinError 123
5. Scanner crashes, close-check returns CLOSE INCOMPLETE

## Implications

- All close-check runs on Windows with multi-model sessions will fail
- The evidence ledger cannot be generated
- Close gates cannot be assessed
- Static and runtime verification cannot be performed
- Persistence boundary cannot be assessed

## Remediation

1. Fix close_runner.py to use a hash or truncated session ID instead of stringifying the full JSON dict
2. Add path sanitization for Windows (replace invalid characters, truncate long paths)
3. Add a fallback path construction that works on Windows

## Related

- `close-runner-windows-path-json-stringification-bug.md` — root cause analysis
- `close-check-evidence-ledger-not-generated.md` — consequence of scanner crash

## Falsifier

If close-check runs successfully on Windows with a JSON-dict --session argument after the fix, the pattern is broken.

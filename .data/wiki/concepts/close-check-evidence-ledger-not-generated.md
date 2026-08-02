---
title: "Close-check evidence ledger not generated"
type: concept
tags: [close-check, evidence-ledger, windows-path-bug]
created: 2026-08-02
source: session 019fa8f8, close-gates FAIL
---

# Close-check evidence ledger not generated

## Summary

The close-check workflow's evidence ledger was not generated for session 019fa8f8. The close-gates were not assessed. This is a direct consequence of the close_runner Windows-path JSON-stringification bug — the scanner crashed before it could run any gate evaluations or write the evidence ledger.

## Context

The close-check workflow has a Phase 3 that generates an evidence ledger documenting all gate evaluations, test results, and verification receipts. When the close_runner crashes (WinError 123 on JSON-dict --session), Phase 3 never executes, so no ledger is written and no gates are assessed.

## Pattern

This is a known failure mode for close-check on Windows: when the close_runner path construction produces invalid paths (JSON dict stringified into directory names), the entire scanner pipeline aborts before any evidence is collected.

## Implications

- No evidence ledger means no audit trail for the close-check run
- No gate assessments means the session cannot be closed cleanly
- The close-runner bug must be fixed before any close-check run can produce usable output on Windows

## Related

- `close-runner-windows-path-json-stringification-bug.md` — root cause
- `close-check-workflow-replaces-close-for-session-readiness.md` — close-check workflow context

## Falsifier

If the close-runner bug is fixed and close-check is re-run, the evidence ledger should be generated and gates should be assessed.

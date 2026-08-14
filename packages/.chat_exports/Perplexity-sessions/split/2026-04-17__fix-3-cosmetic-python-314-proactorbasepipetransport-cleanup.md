---
title: "Fix 3 (Cosmetic) — Python 3.14 ProactorBasePipeTransport cleanup noise

  What's happening: On Windows, Python 3.14's "
date: "2026-04-17"
mode: "COPILOT"
uuid: "1f58067b-7000-413e-a6be-02ca9bda5d09"
entry_count: 1
---

## Human

Fix 3 (Cosmetic) — Python 3.14 ProactorBasePipeTransport cleanup noise

  What's happening: On Windows, Python 3.14's proactor event loop (asyncio.ProactorEventLoop) uses ProactorBasePipeTransport for subprocess
  pipes. When subprocesses terminate during asyncio's cleanup phase, the transport emits ResourceWarning about unclosed handles. This is stdlib
   internals, not application code.

  Source: notebooklm_backend.py calls  asyncio.create_subprocess_exec() — the subprocess API whose pipes go through the proactor transport. The
   warning fires when the transport is garbage-collected before the subprocess's pipes are fully drained.

  Can we fix it in the application?

  ┌─────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┬──────────────────────┐
  │                    Approach                     │                            Works?                            │         Cost         │
  ├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┼──────────────────────┤
  │ Explicit proc.wait() before GC                  │ Already done — proc.communicate() calls proc.wait()          │ N/A — already        │
  │                                                 │ internally                                                   │ correct              │
  ├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┼──────────────────────┤
  │ Suppress the warning via                        │ Yes, in the calling code                                     │ Minimal — one line   │
  │ warnings.filterwarnings                         │                                                              │                      │
  ├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┼──────────────────────┤
  │ Fix in stdlib                                   │ No — requires Python version change                          │ N/A                  │
  ├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┼──────────────────────┤
  │ Stop using subprocess                           │ No — yt-dlp/Selenium need it                                 │ N/A                  │
  └─────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┴──────────────────────┘

  Verdict: Documented cosmetic issue only. The subprocess is already waited on correctly. The warning is a Python 3.14 regression in the stdlib
   proactor transport layer, fixed in Python 3.14 patch builds. An application-level warnings.filterwarnings("ignore",
  category=ResourceWarning) suppression in the backend entry point is the pragmatic fix — but it suppresses a stdlib bug, not application code.

  Recommendation: Add warnings.filterwarnings("ignore", category=ResourceWarning) at module top in notebooklm_backend.py — or at process entry
  in the CLI runner. This is a one-liner with no downside beyond masking a legitimate stdlib bug in Python 3.14 Windows subprocess transport.


Is this true?

## Assistant

Yes, the diagnosis is accurate: Python 3.14's ProactorEventLoop (default on Windows) triggers ResourceWarning from _ProactorBasePipeTransport.__del__ during subprocess pipe cleanup/GC, even after correct wait() via communicate().[1][2]

## Issue Confirmation
This is a known stdlib behavior in Windows proactor loops (seen since 3.8+, persisting/reported in 3.14), where pipe transports emit warnings on destruction if handles appear unclosed during GC—despite proper app-level waits.  No 3.14-specific changelog fix for ProactorBasePipeTransport; it's cosmetic noise from internal transport finalization.[2][3][1]

## Fix Validity
- `warnings.filterwarnings("ignore", category=ResourceWarning)` at module top (notebooklm_backend.py) or CLI entry suppresses it precisely, with minimal cost/downside (masks stdlib noise only).[4]
- proc.communicate() already handles wait/drain correctly; explicit fixes redundant.[5]
- Alternatives (stdlib patch, no-subprocess) invalid as stated.[6]

## Actionable Steps
1. Add `import warnings; warnings.filterwarnings("ignore", category=ResourceWarning)` before asyncio/subprocess imports in notebooklm_backend.py.
2. Test: Run backend; confirm no warnings on subprocess exit (yt-dlp/Selenium).
3. Upgrade Python if feasible (monitor cpython issues for patches); current date (Apr 2026) suggests 3.14.x patches exist but unconfirmed for this.[7]

Confidence: High (matches GitHub issues/docs); assumes unpatched 3.14 base.[1]

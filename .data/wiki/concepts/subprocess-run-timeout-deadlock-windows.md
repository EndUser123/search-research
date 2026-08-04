---
title: "subprocess.run timeout deadlock on Windows: communicate() blocks after kill"
created: 2026-08-04
source: session-20260804
tags: [python, windows, subprocess, deadlock, debugging]
summary: >
  Python's subprocess.run(timeout=N) on Windows calls communicate() AFTER kill()
  with no timeout. If the killed process's pipe handles remain open (child processes,
  console hosts, or deferred I/O), communicate() blocks indefinitely. The fix is
  Popen + taskkill /F /T /PID (kill entire process tree) + communicate(timeout=5).
  Verified: subprocess.run(timeout=10) ran for 85+ seconds; Popen+taskkill returns in 11s.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - Python 3.14 subprocess.run source (CPython, inspected 2026-08-04)
relations:
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: complements
  - target: wiki/concepts/tool-fallbacks.md
    type: complements
---

# subprocess.run timeout deadlock on Windows

## Decision context

The `/model-benchmark` dispatch-path benchmark hung indefinitely when testing
GLM via OpenCode CLI. The `subprocess.run(timeout=30)` call never returned
even though the 30-second timeout should have killed the process. This caused
the benchmark to stall at 95/105 tasks for over an hour, requiring manual kills
and losing collected data.

The question: why does `subprocess.run(timeout=N)` hang on Windows, and what
is the correct pattern for bounded subprocess execution?

## Root cause

`subprocess.run()` calls `process.communicate(timeout=N)`. When the timeout
fires, it raises `TimeoutExpired`, then:

1. Calls `process.kill()` (sends `TerminateProcess` to the main process)
2. Calls `process.communicate()` **again** to collect remaining output

Step 2 has **no timeout**. On Windows, if the killed process's pipe handles
are still open (because a child process or console host inherited them),
`communicate()` blocks waiting for the pipes to close. Since the pipe-holding
process wasn't killed, this wait is indefinite.

Source receipt: CPython `Lib/subprocess.py`, `run()` function, lines 44-53:
```python
except TimeoutExpired as exc:
    process.kill()
    ...
    exc.stdout, exc.stderr = process.communicate()  # ← no timeout, blocks forever
```

## Evidence

Direct test: `subprocess.run(["pwsh", "-Command", "opencode run --model zai/glm-5.2 'test'"],
timeout=10)` — ran for 85+ seconds and never returned. The timeout fired at 10s,
`kill()` was called, but `communicate()` blocked indefinitely.

After applying the fix (Popen + taskkill /F /T): the same command returned in
11 seconds (10s timeout + 1s taskkill + pipe closure).

## Fix: _run_cli_with_timeout()

Replace `subprocess.run(timeout=N)` with:

```python
proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=DEVNULL, text=True)
try:
    stdout, stderr = proc.communicate(timeout=N)
    return stdout, stderr, proc.returncode
except TimeoutExpired:
    # Kill entire process tree — not just the parent
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                   capture_output=True, timeout=5)
    # Now pipes are released; collect with short timeout
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except Exception:
        stdout, stderr = "", ""
    return stdout, stderr, -1
```

`taskkill /F /T /PID` kills the process AND all its children, releasing all
inherited pipe handles. The subsequent `communicate(timeout=5)` then completes
because no process holds the pipes open.

## What this means for our workspace

Any skill that uses `subprocess.run()` with `timeout` on Windows is vulnerable.
The pattern appears in:
- `/model-benchmark` (benchmark.py) — all PI and OpenCode CLI calls
- Any future skill that shells out to external CLIs

The `_run_cli_with_timeout()` helper in `benchmark.py` should be extracted to
a shared utility for all subprocess-based skills.

This is the same failure class as [[replacement-before-investigation-pattern]]:
the agent restructured the caller (threading model, timeout handling) instead of
diagnosing the callee (subprocess pipe behavior). The [[tool-fallbacks]] wiki
should reference this entry for any subprocess-based tool that hangs on Windows.

Related: [[dedicated-quota-first-dispatch-routing]] — the routing decision that
motivated the benchmark work where this deadlock was discovered.

## Falsifier

If a future Python version (3.15+) fixes `subprocess.run()` to use process-tree
kill or adds a timeout to the post-kill `communicate()`, this workaround becomes
unnecessary. Check by running the test script in the new Python version — if it
returns within 15s with `timeout=10`, the fix is no longer needed.

## Receipts

- CPython source: `Lib/subprocess.py` `run()` function — verified 2026-08-04
- Test script: `P:/tmp/test_subprocess_timeout.py` — ran 85+ seconds, confirmed hang
- Fix verification: `P:/tmp/test_fix.py` — returned in 10.8 seconds after fix

## Auto-related

- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[windows-customization-and-enhancement-approaches]]
- [[hook-evidence-collection-cost-vs-timeout-tradeoff]]
- [[windows-platform-disruptions-and-transitions]]
- [[youtube-transcript-extraction-techniques]]


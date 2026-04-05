# Semantic Daemon Console Flash and Typing Capture

**Date:** 2026-03-14
**Severity:** High - User input interference
**Status:** Fixed in code, requires daemon restart to take effect

## Problem

On Windows, the semantic daemon startup chain could briefly show a blue console window and interfere with terminal typing in Claude Code.

## Symptoms

- Brief blue terminal or console flash during daemon auto-start
- Claude Code terminal appears to lose or "eat" some typed characters
- Issue appears around semantic daemon startup, not during normal pipe request handling

## Root Cause

The Windows background startup path was not fully detached from the active console.

Two problems existed:

1. `daemon_client.py` launched the keep-alive wrapper with `python.exe`, not `pythonw.exe`
2. The wrapper/child process tree did not explicitly redirect `stdin` to `DEVNULL`

That allowed the detached background process to inherit the active terminal's console input handle. On Windows, that can cause both:

- a visible console flash
- accidental interaction with the foreground terminal's input stream

`daemon_keep_alive.py` also launched the real daemon with inherited input and pipe-backed output handles that were not appropriate for a background service.

## Code Fix

Updated files:

- `P:/packages/search-research/contrib/semantic_daemon/daemon_client.py`
- `P:/packages/search-research/contrib/semantic_daemon/daemon_keep_alive.py`
- `P:/__csf/src/search/test_daemon_singleton.py`

### Changes made

- Use `pythonw.exe` for the keep-alive wrapper on Windows
- Set `stdin=subprocess.DEVNULL`
- Set `stdout=subprocess.DEVNULL`
- Set `stderr=subprocess.DEVNULL`
- Set `close_fds=True`

This ensures the daemon startup chain does not inherit the active Claude Code terminal handles.

## Operational Action

The code fix only affects newly started daemon processes. Existing daemon or keep-alive processes must be restarted.

### Restart command

Run in the Claude Code terminal:

```powershell
Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -match 'src\.daemons\.daemon_keep_alive' -or
    $_.CommandLine -match 'src\.daemons\.unified_semantic_daemon'
  } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Then continue using Claude Code normally. The daemon will auto-start again with the corrected launch behavior.

If the problem persists after restart, the flashing process is likely a different Windows background process and should be traced live when it reproduces.

## Verification Notes

- Syntax verification passed with `python -m py_compile`
- Focused runtime verification was limited by heavy local import/test startup behavior in this repository
- Regression tests were added to lock in the Windows detached startup contract

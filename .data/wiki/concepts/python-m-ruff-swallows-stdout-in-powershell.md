# python -m ruff swallows stdout in PowerShell

**Host:** grok
**Created:** 2026-08-01
**Session:** 019fba58

## Problem

On this Windows host, `python -m ruff check <file>` returns exit code 1 but produces **zero stdout and zero stderr**. The output is silently eaten by the PowerShell `python -m` wrapper. This caused a false "ruff is broken on this host" claim.

## Root cause

[UNKNOWN] — likely a Python 3.14 subprocess stdout handling issue specific to the `python -m` invocation path in PowerShell. The `ruff` binary itself works perfectly.

## Solution

Always run the `ruff` **binary directly**, not via `python -m`:

```powershell
# WRONG — silently eats output
python -m ruff check csf/transcript.py

# RIGHT — works correctly
ruff check csf/transcript.py
```

The binary is at `C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\ruff.exe` and resolves on PATH.

## Applies to

Any Python tool that has a console script entry point (ruff, pytest, black, mypy). If `python -m <tool>` produces no output, try the binary directly.

## Rule

Added to `~/.grok/AGENTS.md` as a permanent rule.

#!/usr/bin/env python3
"""Add subprocess focus stealing pattern to CKS."""
import sys
sys.path.insert(0, 'P:/__csf/src')

from knowledge.systems.cks.unified import ingest_pattern

# Pattern content
title = "Windows subprocess focus stealing prevention"
content = """
# Windows Subprocess Focus Stealing Pattern

## Problem
On Windows, calling subprocess commands like `tasklist.exe` and `wmic.exe` from Python causes console window flash and focus stealing, even with `STARTF_USESHOWWINDOW` and `SW_HIDE` flags.

## Root Cause
These Windows executables create console windows that briefly appear and grab focus before being hidden. The `SW_HIDE` flag applies to the parent process window, not the child process console.

## Solution
Use **psutil** (cross-platform process library) instead of subprocess calls:

| Replace | With |
|---------|------|
| `subprocess.run(['tasklist', '/FI', f'PID eq {pid}'])` | `psutil.pid_exists(pid)` |
| `subprocess.run(['wmic', 'process', 'get', '...'])` | `psutil.process_iter(['pid', 'name', 'cmdline'])` |
| `subprocess.run(['tasklist'])` to verify daemon | `psutil.Process(pid).is_running()` |

## Code Example
```python
# BAD: Causes console flash
result = subprocess.run(
    ['tasklist', '/FI', f'PID eq {pid}'],
    capture_output=True,
    creationflags=subprocess.CREATE_NO_WINDOW
)

# GOOD: No flash, cross-platform
import psutil
if psutil.pid_exists(pid):
    proc = psutil.Process(pid)
    return proc.name().lower() == 'pythonw.exe'
```

## Investigation Lesson
**Code-first pattern**: This issue persisted across multiple sessions because investigation focused on symptom speculation (voice-related theories) instead of reading the actual code. Reading `SessionStart_semantic_daemon.py` immediately revealed the subprocess calls causing the flash.

**Rule**: Always read the code before speculating on causes. Code reading takes 30 seconds; symptom speculation can waste multiple sessions.

## Evidence
- Fixed in: r`P:\.claude\hooks\SessionStart_semantic_daemon.py`
- Date: 2026-02-10
- Related: Terminal flash issue during Claude Code session start
"""

# Add to CKS
entry_id = ingest_pattern(
    title=title,
    content=content,
    entry_type="pattern",
    source="terminal_flash_fix",
    fix_date="2026-02-10",
    files_modified=["SessionStart_semantic_daemon.py"],
    keywords=["subprocess", "windows", "focus", "psutil", "console", "flash", "terminal"]
)

print(f"Added pattern to CKS: {entry_id}")

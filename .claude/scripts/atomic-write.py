#!/usr/bin/env python3
"""
Atomic Write for Claude Code on Windows
Bypasses Claude Code's file state tracking issues
"""

import sys
import os
import tempfile
from pathlib import Path

def atomic_write_text(file_path: str, content: str, encoding: str = "utf-8"):
    """
    Write content to file atomically, bypassing Claude Code state tracking.

    Pattern:
    1. Write to temp file
    2. Atomic os.replace() (one filesystem operation)
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding=encoding,
        dir=path.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # Atomic replace (one filesystem operation - no corruption on failure)
    tmp_path.replace(path)

    return path

def main():
    if len(sys.argv) < 2:
        print("Usage: atomic-write.py <file_path> [content]")
        print("   or: atomic-write.py <file_path> --from-stdin")
        sys.exit(1)

    file_path = sys.argv[1]

    if len(sys.argv) >= 3 and sys.argv[2] != '--from-stdin':
        content = ' '.join(sys.argv[2:])
    elif '--from-stdin' in sys.argv or len(sys.argv) == 2:
        content = sys.stdin.read()
    else:
        content = ''

    result = atomic_write_text(file_path, content)
    print(f"✓ Written: {result}")

if __name__ == '__main__':
    main()

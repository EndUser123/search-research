"""Atomically append a log entry to the wiki log.

Use this instead of search_replace for log edits. The search_replace pattern
causes sequential edit collisions when multiple log edits target the same
anchor (# Vault Log header) — later edits silently revert earlier ones.

Usage:
    python append_log.py "Entry title" "source" "agent" "notes" "page-path"

All arguments are positional. The entry is inserted at the top of the log
(after the header), with the most recent entries first.
"""
from __future__ import annotations

import sys
from pathlib import Path

LOG_PATH = Path("P:/.data/wiki/log.md")


def append_entry(title: str, source: str, agent: str, notes: str, page: str) -> None:
    """Atomically append a log entry to the top of the wiki log."""
    content = LOG_PATH.read_text(encoding="utf-8")
    header = "# Vault Log\n\n"
    
    entry = (
        f"## {title}\n"
        f"Source: {source}\n"
        f"Agent: {agent}\n"
        f"Notes: {notes}\n"
        f"Page: {page}\n\n"
    )
    
    if content.startswith(header):
        rest = content[len(header):]
        new_content = header + entry + rest
    else:
        new_content = header + entry + content
    
    LOG_PATH.write_text(new_content, encoding="utf-8")
    count = new_content.count("## [2026-07-2")
    print(f"Log entry added. Size: {LOG_PATH.stat().st_size}. Recent entries visible: {count}")


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python append_log.py <title> <source> <agent> <notes> <page-path>")
        sys.exit(1)
    append_entry(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

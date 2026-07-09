#!/usr/bin/env python3
"""PostToolUse advisory: syntax-check ANY .py file after Edit/Write/MultiEdit.

Motivation (2026-07-09): an Edit/Write silently truncated a hook file
mid-write and the tool still reported success; it was only caught by a
manual `ast.parse` afterwards. "The command ran" and "the result is
correct" are different facts. This gate makes the second fact checked
structurally, for every .py write anywhere — not just .claude/hooks/**
(which PostToolUse_hook_import_health.py already covers at import level).

Checks, cheapest first:
  1. File exists and is non-empty (catches silent truncation-to-zero).
  2. ast.parse succeeds (catches truncation mid-statement, bad escapes,
     re.sub replacement mangling, etc.).

Design constraints (mirrors PostToolUse_hook_import_health.py):
  - Advisory only. PostToolUse must never block; always exits 0.
  - Fail open. Internal errors => silent.
  - Cheap. ast.parse only, no imports, no subprocess. ~ms per fire.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


def _edited_py_file(data: dict) -> str | None:
    """Return the edited file path if it is a .py file, else None."""
    tool = data.get("tool_name", "") or data.get("name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        return None
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return None
    normalized = str(file_path).replace("\\", "/")
    if not normalized.endswith(".py"):
        return None
    return normalized


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # malformed input -> stay silent

    edited = _edited_py_file(data)
    if not edited:
        return

    try:
        p = Path(edited)
        if not p.exists():
            print(
                f"⚠️ PY SYNTAX GATE: {edited} does not exist after a "
                f"successful-looking write. The write likely failed silently."
            )
            return
        src = p.read_text(encoding="utf-8", errors="replace")
        if not src.strip():
            print(
                f"⚠️ PY SYNTAX GATE: {edited} is empty after the write. "
                f"Probable silent truncation — restore from backup/git before continuing."
            )
            return
        try:
            ast.parse(src, filename=edited)
        except SyntaxError as e:
            print(
                f"⚠️ PY SYNTAX GATE: {edited} no longer parses "
                f"(line {e.lineno}: {e.msg}). The write corrupted the file — "
                f"do NOT report this edit as complete; fix or restore it first."
            )
    except Exception:
        return  # fail open


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
qmd_shim.py — thin CLI shim that redirects `qmd search` to the FTS5 wrapper.

Replaces the qmd.exe binary with a redirect: `qmd search` calls go to
P:/.agents/scripts/wiki_search.py (the stdlib FTS5 wrapper). Other qmd
subcommands (update, document add, etc.) are passed through to the real
qmd if available, or fail gracefully.

This allows all existing callers (wiki_after_write.py, wiki_contradiction_scan.py,
plugin wiki_search.py, nlm-to-wiki reconcile.py) to keep calling
`qmd search --collection wiki ...` without modification.

INSTALLATION:
  1. Copy this file to the qmd.exe location, renaming:
     C:\\Users\\<user>\\AppData\\Roaming\\Python\\Python314\\Scripts\\qmd.exe
     → qmd_real.exe (backup)
  2. Create a qmd.cmd wrapper or replace the entry point.

Alternatively, install as a console_scripts entry point that overrides qmd's.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


FTS5_WRAPPER = os.environ.get(
    "WIKI_SEARCH_WRAPPER",
    str(Path(__file__).resolve().parent.parent.parent.parent / ".agents" / "scripts" / "wiki_search.py"),
)
# Fallback path
if not Path(FTS5_WRAPPER).exists():
    FTS5_WRAPPER = "P:/.agents/scripts/wiki_search.py"

REAL_QMD = os.environ.get("QMD_REAL_BINARY", "")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("qmd shim — redirects 'qmd search' to FTS5 wrapper", file=sys.stderr)
        print("Usage: qmd search --query <query> [--collection wiki] [--top-k N] [--format json]", file=sys.stderr)
        return 0

    command = argv[0]

    if command == "search":
        return _handle_search(argv[1:])
    elif command == "document" and len(argv) > 1 and argv[1] == "add":
        return _handle_document_add(argv[2:])
    elif command in ("update", "info", "collection", "list"):
        # These need the real qmd (indexing operations) — pass through if available
        return _passthrough(argv)
    else:
        # Unknown command — pass through to real qmd if available
        return _passthrough(argv)


def _handle_search(args: list[str]) -> int:
    """Redirect qmd search to the FTS5 wrapper CLI.

    qmd syntax: qmd search --collection <col> --query <query> --top-k N --format json
    wrapper syntax: python wiki_search.py --collection <col> search --query <query> --top-k N --format json
    Also handles positional queries (qmd allows bare query after flags).
    """
    wrapper_args = [sys.executable, FTS5_WRAPPER]
    search_args = ["search"]
    collection = None
    skip_next = False
    positional_parts = []

    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg == "--collection":
            if i + 1 < len(args):
                collection = args[i + 1]
            skip_next = True
        elif arg.startswith("--collection="):
            collection = arg.split("=", 1)[1]
        elif arg == "--rerank":
            continue
        elif arg.startswith("--filters"):
            if "=" not in arg:
                skip_next = True
            continue
        elif arg == "--query":
            if i + 1 < len(args):
                positional_parts.append(args[i + 1])
                skip_next = True
        elif arg.startswith("--query="):
            positional_parts.append(arg.split("=", 1)[1])
        elif arg in ("--top-k", "--limit", "--format"):
            search_args.append(arg)
            if i + 1 < len(args):
                search_args.append(args[i + 1])
                skip_next = True
        elif arg.startswith(("--top-k=", "--limit=", "--format=")):
            search_args.append(arg)
        else:
            # Bare positional — part of the query
            positional_parts.append(arg)

    if collection:
        wrapper_args.extend(["--collection", collection])

    # Reconstruct the query from positional parts
    if positional_parts:
        query = " ".join(positional_parts)
        search_args.extend(["--query", query])

    wrapper_args.extend(search_args)

    try:
        os.execv(sys.executable, wrapper_args)
        return 0
    except FileNotFoundError as e:
        print(f"qmd shim: FTS5 wrapper not found: {e}", file=sys.stderr)
        return 1


def _handle_document_add(args: list[str]) -> int:
    """Redirect qmd document add to the FTS5 wrapper's add_document."""
    # qmd: document add --collection wiki --document-id <slug> --markdown-file <path>
    # wrapper: add_document(doc_id, markdown_path) via Python API
    # For now, pass through to real qmd if available, else fail gracefully
    return _passthrough(["document", "add"] + args)


def _passthrough(args: list[str]) -> int:
    """Pass command through to the real qmd binary if available."""
    if not REAL_QMD:
        # Try to find the real qmd
        real_qmd = str(Path(sys.argv[0]).resolve().parent / "qmd_real.exe")
        if not Path(real_qmd).exists():
            print(f"qmd shim: real qmd not available and this command requires it: {' '.join(args)}", file=sys.stderr)
            print(f"  (indexing operations still need qmd until the wrapper adds an indexer)", file=sys.stderr)
            return 1
    else:
        real_qmd = REAL_QMD

    try:
        proc = subprocess.run([real_qmd] + args, timeout=300)
        return proc.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"qmd shim: real qmd failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

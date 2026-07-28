#!/usr/bin/env python3
"""
qmd — replacement entry point for wiki search and indexing.

This replaces the original qmd.exe binary. It redirects all commands to
the stdlib FTS5 wrapper (P:/.agents/scripts/wiki_search.py). The original
qmd Python package is no longer needed.

Commands supported:
  qmd search --collection <col> --query <q> [--top-k N] [--limit N] [--format json]
  qmd document add --collection <col> --document-id <id> --markdown-file <path>
  qmd document list --collection <col>
  qmd document delete --collection <col> --document-id <id>
  qmd document get --collection <col> --document-id <id>
  qmd collection info --collection <col>
  qmd collection list

This entry point is installed as qmd.exe (or qmd.cmd) in the Python
Scripts directory, replacing the original qmd console_scripts entry.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


WRAPPER = os.environ.get(
    "WIKI_SEARCH_WRAPPER",
    str(Path(__file__).resolve().parent.parent.parent / ".agents" / "scripts" / "wiki_search.py"),
)
# Fallback
if not Path(WRAPPER).exists():
    WRAPPER = "P:/.agents/scripts/wiki_search.py"

PY = sys.executable


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("qmd — FTS5 wiki search and indexing (stdlib, no qmd dependency)", file=sys.stderr)
        print("Usage: qmd search|document|collection ...", file=sys.stderr)
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "search":
        return _redirect(["search"] + _translate_search_args(rest))
    elif cmd == "document":
        sub = rest[0] if rest else ""
        if sub == "add":
            return _redirect(["add"] + _translate_doc_add_args(rest[1:]))
        elif sub == "list":
            return _redirect_search_list(rest[1:])
        elif sub == "delete":
            return _redirect_delete(rest[1:])
        elif sub == "get":
            return _redirect_get(rest[1:])
        else:
            print(f"Unknown document subcommand: {sub}", file=sys.stderr)
            return 1
    elif cmd == "collection":
        sub = rest[0] if rest else ""
        if sub == "info":
            return _redirect_info(rest[1:])
        elif sub == "list":
            print(json.dumps([{"name": "wiki", "document_count": "unknown"}]))
            return 0
        else:
            print(f"Unknown collection subcommand: {sub}", file=sys.stderr)
            return 1
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Supported: search, document (add/list/delete/get), collection (info/list)", file=sys.stderr)
        return 1


def _translate_search_args(args: list[str]) -> list[str]:
    """Translate qmd search flags to wrapper CLI flags."""
    out = []
    skip_next = False
    collection = "wiki"
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
        elif arg == "--rerank" or arg.startswith("--filters"):
            if "=" not in arg and arg == "--filters":
                skip_next = True
            continue
        elif arg in ("--query", "--top-k", "--limit", "--format"):
            out.append(arg)
            if i + 1 < len(args):
                out.append(args[i + 1])
                skip_next = True
        elif arg.startswith(("--query=", "--top-k=", "--limit=", "--format=")):
            out.append(arg)
        else:
            # Positional query — reconstruct
            out.extend(["--query", arg])
    out.insert(0, collection)
    return ["--collection"] + out


def _translate_doc_add_args(args: list[str]) -> list[str]:
    """Translate qmd document add flags to wrapper CLI flags."""
    out = []
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg == "--collection":
            skip_next = True  # wrapper uses top-level --collection
            continue
        elif arg.startswith("--collection="):
            continue
        elif arg == "--document-id":
            out.extend(["--doc-id"])
            if i + 1 < len(args):
                out.append(args[i + 1])
                skip_next = True
        elif arg == "--markdown-file":
            out.append(arg)
            if i + 1 < len(args):
                out.append(args[i + 1])
                skip_next = True
        elif arg.startswith("--document-id="):
            doc_id = arg.split("=", 1)[1]
            out.extend(["--doc-id", doc_id])
        elif arg.startswith("--markdown-file="):
            out.append(arg)
    return out


def _redirect(wrapper_subcommand: list[str]) -> int:
    """Run the wrapper CLI with the given subcommand args."""
    cmd = [PY, WRAPPER] + wrapper_subcommand
    try:
        result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


def _redirect_search_list(args: list[str]) -> int:
    """Handle 'qmd document list' — output JSON array of doc IDs."""
    collection = "wiki"
    for i, a in enumerate(args):
        if a == "--collection" and i + 1 < len(args):
            collection = args[i + 1]
    cmd = [PY, WRAPPER, "--collection", collection, "search", "--query", "", "--top-k", "0", "--format", "json"]
    # Actually just call list_documents via Python
    sys.path.insert(0, str(Path(WRAPPER).parent))
    try:
        from wiki_search import WikiSearch
        ws = WikiSearch(collection=collection)
        docs = ws.list_documents()
        print(json.dumps(docs))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


def _redirect_delete(args: list[str]) -> int:
    """Handle 'qmd document delete'."""
    collection = "wiki"
    doc_id = None
    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a == "--collection" and i + 1 < len(args):
            collection = args[i + 1]
            skip = True
        elif a == "--document-id" and i + 1 < len(args):
            doc_id = args[i + 1]
            skip = True
    if not doc_id:
        print(json.dumps({"error": "missing --document-id"}), file=sys.stderr)
        return 1
    sys.path.insert(0, str(Path(WRAPPER).parent))
    try:
        from wiki_search import WikiSearch
        ws = WikiSearch(collection=collection)
        ws.delete_document(doc_id)
        print(json.dumps({"ok": True, "document_id": doc_id}))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


def _redirect_get(args: list[str]) -> int:
    """Handle 'qmd document get'."""
    collection = "wiki"
    doc_id = None
    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a == "--collection" and i + 1 < len(args):
            collection = args[i + 1]
            skip = True
        elif a == "--document-id" and i + 1 < len(args):
            doc_id = args[i + 1]
            skip = True
    if not doc_id:
        print(json.dumps({"error": "missing --document-id"}), file=sys.stderr)
        return 1
    sys.path.insert(0, str(Path(WRAPPER).parent))
    try:
        from wiki_search import WikiSearch
        ws = WikiSearch(collection=collection)
        doc = ws.get_document(doc_id)
        print(json.dumps(doc))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


def _redirect_info(args: list[str]) -> int:
    """Handle 'qmd collection info'."""
    collection = "wiki"
    for i, a in enumerate(args):
        if a == "--collection" and i + 1 < len(args):
            collection = args[i + 1]
    sys.path.insert(0, str(Path(WRAPPER).parent))
    try:
        from wiki_search import WikiSearch
        ws = WikiSearch(collection=collection)
        info = ws.info()
        print(json.dumps(info))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

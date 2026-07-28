#!/usr/bin/env python3
"""
qmd_entry.py — qmd-compatible CLI entry point.

Provides the `qmd` console command that callers use via subprocess.
All commands redirect to the FTS5 wrapper at P:/.agents/scripts/wiki_search.py.
This replaces the original qmd package entirely.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _wrapper_path() -> str:
    env = os.environ.get("WIKI_SEARCH_WRAPPER")
    if env and Path(env).exists():
        return env
    candidates = [
        Path(__file__).resolve().parent.parent.parent / ".agents" / "scripts" / "wiki_search.py",
        Path("P:/.agents/scripts/wiki_search.py"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return "P:/.agents/scripts/wiki_search.py"


WRAPPER = None  # lazy-init


def _get_wrapper() -> str:
    global WRAPPER
    if WRAPPER is None:
        WRAPPER = _wrapper_path()
    return WRAPPER


def _run_wrapper(args: list[str]) -> int:
    cmd = [sys.executable, _get_wrapper()] + args
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


def _run_python(args: list[str]) -> int:
    """Run Python code directly (for commands that use the WikiSearch API)."""
    sys.path.insert(0, str(Path(_get_wrapper()).parent))
    cmd = [sys.executable] + args
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


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("qmd — FTS5 wiki search and indexing", file=sys.stderr)
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "search":
        return _handle_search(rest)
    elif cmd == "document":
        return _handle_document(rest)
    elif cmd == "collection":
        return _handle_collection(rest)
    elif cmd == "--help" or cmd == "-h":
        print("qmd — FTS5 wiki search and indexing")
        print("Commands: search, document (add/list/delete/get), collection (info/list)")
        return 0
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 1


def _handle_search(args: list[str]) -> int:
    collection = "wiki"
    query = None
    top_k = 5
    fmt = "json"

    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a == "--collection" and i + 1 < len(args):
            collection = args[i + 1]; skip = True
        elif a.startswith("--collection="):
            collection = a.split("=", 1)[1]
        elif a == "--query" and i + 1 < len(args):
            query = args[i + 1]; skip = True
        elif a.startswith("--query="):
            query = a.split("=", 1)[1]
        elif a == "--top-k" and i + 1 < len(args):
            top_k = int(args[i + 1]); skip = True
        elif a.startswith("--top-k="):
            top_k = int(a.split("=", 1)[1])
        elif a == "--limit" and i + 1 < len(args):
            top_k = int(args[i + 1]); skip = True
        elif a.startswith("--limit="):
            top_k = int(a.split("=", 1)[1])
        elif a == "--format" and i + 1 < len(args):
            fmt = args[i + 1]; skip = True
        elif a.startswith("--format="):
            fmt = a.split("=", 1)[1]
        elif a in ("--rerank",):
            continue
        elif a.startswith("--filters"):
            if "=" not in a:
                skip = True
            continue
        else:
            query = a  # positional

    if not query:
        print(json.dumps({"error": "no query provided"}), file=sys.stderr)
        return 1

    return _run_wrapper([
        "--collection", collection,
        "search",
        "--query", query,
        "--top-k", str(top_k),
        "--format", fmt,
    ])


def _handle_document(args: list[str]) -> int:
    if not args:
        print(json.dumps({"error": "missing document subcommand"}), file=sys.stderr)
        return 1

    sub = args[0]
    rest = args[1:]

    if sub == "add":
        collection = "wiki"
        doc_id = None
        md_file = None
        skip = False
        for i, a in enumerate(rest):
            if skip:
                skip = False
                continue
            if a == "--collection" and i + 1 < len(rest):
                collection = rest[i + 1]; skip = True
            elif a.startswith("--collection="):
                collection = a.split("=", 1)[1]
            elif a == "--document-id" and i + 1 < len(rest):
                doc_id = rest[i + 1]; skip = True
            elif a.startswith("--document-id="):
                doc_id = a.split("=", 1)[1]
            elif a == "--markdown-file" and i + 1 < len(rest):
                md_file = rest[i + 1]; skip = True
            elif a.startswith("--markdown-file="):
                md_file = a.split("=", 1)[1]
        if not doc_id or not md_file:
            print(json.dumps({"error": "missing --document-id or --markdown-file"}), file=sys.stderr)
            return 1
        rc = _run_wrapper([
            "--collection", collection,
            "add",
            "--doc-id", doc_id,
            "--markdown-file", md_file,
        ])
        if rc == 0:
            print(json.dumps({"ok": True, "document_id": doc_id}))
        return rc

    elif sub == "list":
        collection = "wiki"
        for i, a in enumerate(rest):
            if a == "--collection" and i + 1 < len(rest):
                collection = rest[i + 1]
        sys.path.insert(0, str(Path(_get_wrapper()).parent))
        try:
            from wiki_search import WikiSearch
            ws = WikiSearch(collection=collection)
            print(json.dumps(ws.list_documents()))
            return 0
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

    elif sub == "delete":
        collection = "wiki"
        doc_id = None
        skip = False
        for i, a in enumerate(rest):
            if skip:
                skip = False
                continue
            if a == "--collection" and i + 1 < len(rest):
                collection = rest[i + 1]; skip = True
            elif a == "--document-id" and i + 1 < len(rest):
                doc_id = rest[i + 1]; skip = True
        if not doc_id:
            print(json.dumps({"error": "missing --document-id"}), file=sys.stderr)
            return 1
        sys.path.insert(0, str(Path(_get_wrapper()).parent))
        try:
            from wiki_search import WikiSearch
            ws = WikiSearch(collection=collection)
            ws.delete_document(doc_id)
            print(json.dumps({"ok": True, "document_id": doc_id}))
            return 0
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

    elif sub == "get":
        collection = "wiki"
        doc_id = None
        skip = False
        for i, a in enumerate(rest):
            if skip:
                skip = False
                continue
            if a == "--collection" and i + 1 < len(rest):
                collection = rest[i + 1]; skip = True
            elif a == "--document-id" and i + 1 < len(rest):
                doc_id = rest[i + 1]; skip = True
        if not doc_id:
            print(json.dumps({"error": "missing --document-id"}), file=sys.stderr)
            return 1
        sys.path.insert(0, str(Path(_get_wrapper()).parent))
        try:
            from wiki_search import WikiSearch
            ws = WikiSearch(collection=collection)
            doc = ws.get_document(doc_id)
            print(json.dumps(doc))
            return 0
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

    else:
        print(f"Unknown document subcommand: {sub}", file=sys.stderr)
        return 1


def _handle_collection(args: list[str]) -> int:
    if not args:
        print(json.dumps({"error": "missing collection subcommand"}), file=sys.stderr)
        return 1

    sub = args[0]
    rest = args[1:]

    if sub == "info":
        collection = "wiki"
        for i, a in enumerate(rest):
            if a == "--collection" and i + 1 < len(rest):
                collection = rest[i + 1]
        sys.path.insert(0, str(Path(_get_wrapper()).parent))
        try:
            from wiki_search import WikiSearch
            ws = WikiSearch(collection=collection)
            print(json.dumps(ws.info()))
            return 0
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

    elif sub == "list":
        print(json.dumps([{"name": "wiki", "document_count": "unknown"}]))
        return 0

    else:
        print(f"Unknown collection subcommand: {sub}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

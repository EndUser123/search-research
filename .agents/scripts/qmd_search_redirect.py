#!/usr/bin/env python3
"""
qmd_search_redirect.py — re-apply the FTS5 search redirect to qmd's CLI.

The qmd CLI (qmd/cli/__main__.py in site-packages) is patched to redirect
'qmd search' to the FTS5 wrapper. This patch is lost when qmd is upgraded
via pip. Run this script after any qmd install/upgrade to re-apply it.

Usage:
    python P:/.agents/scripts/qmd_search_redirect.py

Idempotent: checks if the redirect is already present before patching.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def find_qmd_cli() -> Path | None:
    """Find qmd/cli/__main__.py in site-packages."""
    try:
        import qmd
        qmd_dir = Path(qmd.__file__).parent
        cli_main = qmd_dir / "cli" / "__main__.py"
        if cli_main.exists():
            return cli_main
    except ImportError:
        pass
    # Fallback: search common site-packages locations
    for sp in sys.path:
        candidate = Path(sp) / "qmd" / "cli" / "__main__.py"
        if candidate.exists():
            return candidate
    return None


REDIRECT_MARKER = "# FTS5 REDIRECT"


def is_patched(source: str) -> bool:
    """Check if the redirect is already present."""
    return REDIRECT_MARKER in source


def apply_patch(source: str) -> str:
    """Apply the search redirect patch to qmd/cli/__main__.py source.

    1. Makes --query optional (positional query supported)
    2. Adds --limit, --format, positional_query to search subparser
    3. Adds the search redirect in main()
    """
    # 1. Replace the search subparser definition
    old_search_parser = """    # search
    s = sub.add_parser("search")
    s.add_argument("--collection", required=True)
    s.add_argument("--query", required=True)
    s.add_argument("--top-k", type=int, default=5)
    s.add_argument("--rerank", action="store_true")
    s.add_argument("--filters", default=None)"""

    new_search_parser = """    # search
    s = sub.add_parser("search")
    s.add_argument("--collection", required=True)
    s.add_argument("--query", required=False)  # Made optional — positional query supported
    s.add_argument("--top-k", type=int, default=5)
    s.add_argument("--limit", type=int, default=None)  # Alias for --top-k
    s.add_argument("--format", default="json")  # Accepted but ignored (always JSON)
    s.add_argument("--rerank", action="store_true")
    s.add_argument("--filters", default=None)
    s.add_argument("positional_query", nargs="?", default=None)  # qmd compat: bare query"""

    if old_search_parser in source:
        source = source.replace(old_search_parser, new_search_parser)

    # 2. Replace main() to add the redirect
    old_main_start = """def main(argv: list[str] | None = None) -> int:
    ns = _build_parser().parse_args(argv)
    client = None
    try:
        client = connect(_resolve_db_path(ns))"""

    new_main_start = """def main(argv: list[str] | None = None) -> int:
    ns = _build_parser().parse_args(argv)

    # FTS5 REDIRECT: search commands go to the stdlib FTS5 wrapper, not qmd's
    # hybrid search. This replaces qmd's vector/RRF/expansion/reranking pipeline
    # with a pure FTS5 BM25 search using stdlib sqlite3 only.
    # Other commands (collection, document) still use the real qmd.
    if ns.cmd == "search":
        import subprocess as _sp
        wrapper = os.environ.get(
            "WIKI_SEARCH_WRAPPER",
            "P:/.agents/scripts/wiki_search.py"
        )
        query = ns.query or ns.positional_query or ""
        top_k = ns.limit if ns.limit else ns.top_k
        if not query:
            print(json.dumps({"error": "no query provided"}, ensure_ascii=False), file=sys.stderr)
            return 1
        wrapper_args = [
            sys.executable, wrapper,
            "--collection", ns.collection,
            "search",
            "--query", query,
            "--top-k", str(top_k),
            "--format", "json"
        ]
        try:
            result = _sp.run(wrapper_args, timeout=60, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout, end="")
            if result.returncode != 0 and result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        except Exception as e:
            print(json.dumps({"error": f"FTS5 wrapper failed: {e}"}, ensure_ascii=False), file=sys.stderr)
            return 1

    client = None
    try:
        client = connect(_resolve_db_path(ns))"""

    if old_main_start in source:
        source = source.replace(old_main_start, new_main_start)
    elif REDIRECT_MARKER not in source:
        # Can't find the anchor — source may have changed
        print("ERROR: cannot find main() anchor to patch. qmd source layout may have changed.", file=sys.stderr)
        print("Inspect the file manually and apply the redirect.", file=sys.stderr)
        return source  # return unmodified

    return source


def main() -> int:
    cli_path = find_qmd_cli()
    if not cli_path:
        print("qmd not found in site-packages. Install qmd first.", file=sys.stderr)
        return 1

    source = cli_path.read_text(encoding="utf-8")

    if is_patched(source):
        print(f"Already patched: {cli_path}")
        return 0

    print(f"Patching: {cli_path}")
    patched = apply_patch(source)

    if is_patched(patched):
        cli_path.write_text(patched, encoding="utf-8")
        print(f"Patch applied successfully: {cli_path}")
        return 0
    else:
        print("Patch failed — anchor not found. See ERROR above.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Idempotent patcher: apply FTS5 query-sanitization fix to installed qmd.

WHY THIS EXISTS
---------------
qmd's `_bm25_search` and `_check_strong_signal` pass the raw user query to
FTS5's MATCH operator without escaping FTS5 query-syntax characters. A query
like "build-vs-port" is misparsed by FTS5 (the `-` is treated as a syntax
operator), producing `no such column: vs` errors.

Root cause: FTS5 query parser, NOT SQL injection (the query was already
parameterized via `?`). The fix wraps the query in double quotes (phrase
query), disabling syntax interpretation.

This patch lives in site-packages and is LOST on `pip install --upgrade qmd`.
Run this script after any qmd upgrade to re-apply the fix:

    python P:/.agents/scripts/qmd_fts5_patch.py

The script is IDEMPOTENT: it detects whether the patch is already present
(checks for `_sanitize_fts5_query`) and exits 0 with "already patched" if so.

Receipt
-------
- Bug confirmed 2026-07-27 session 019fa48a: discriminating test showed
  "build vs port" (spaces) works, "build-vs-port" (hyphens) fails, "vs" alone
  works — isolating the trigger to FTS5 special-character interpretation.
- Fix verified same session: the failing query returned 3 results after patch.
- Handoff: P:/docs/handoffs/session-friction-fixes-20260727/HANDOFF.md (SF-01)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import qmd
except ImportError:
    print("ERROR: qmd is not installed in this Python environment.", file=sys.stderr)
    sys.exit(2)

COLLECTION_PY = Path(qmd.__file__).parent / "core" / "collection.py"
MARKER = "_sanitize_fts5_query"


def _read() -> str:
    return COLLECTION_PY.read_text(encoding="utf-8")


def _already_patched(src: str) -> bool:
    """Check if the patch is already applied — function definition AND call sites (CORR-002 fix)."""
    if MARKER not in src:
        return False
    # Verify call-site wiring, not just the function name
    call_site_count = src.count("_sanitize_fts5_query(query)")
    if call_site_count < 2:
        return False  # function defined but not wired at both call sites
    return True


def _apply(src: str) -> str:
    """Apply the patch to the source text. Assumes not already patched."""
    # 1. Insert the helper function after _vec_to_sqlite_literal
    # Use a minimal, stable anchor: the function signature + return line.
    # (MAINT-005 fix: full docstring anchor was fragile AND contained non-English text)
    old_vec_fn = (
        'def _vec_to_sqlite_literal(vec: list[float]) -> str:\n'
        '    return json.dumps(vec)\n'
    )
    new_vec_fn = old_vec_fn + (
        '\n\n'
        'def _sanitize_fts5_query(query: str) -> str:\n'
        '    """Escape FTS5 MATCH query-syntax by per-token quoting.\n'
        '\n'
        '    FTS5 MATCH interprets `-`, `:`, `^`, `"`, `*`, `(`, `)` as query-syntax\n'
        '    operators. Quotes each token individually to disable syntax interpretation\n'
        '    while preserving implicit-AND semantics.\n'
        '    """\n'
        '    if not query or not query.strip():\n'
        '        return \'""\'\n'
        '    tokens = query.split()\n'
        '    quoted = []\n'
        '    for token in tokens:\n'
        '        escaped = token.replace(\'"\', \'""\')\n'
        '        quoted.append(f\'"{escaped}"\')\n'
        '    return " ".join(quoted)\n'
    )
    if old_vec_fn not in src:
        print(
            "ERROR: could not find _vec_to_sqlite_literal anchor. qmd source layout may have changed.\n"
            "Inspect " + str(COLLECTION_PY) + " and apply the patch manually.",
            file=sys.stderr,
        )
        sys.exit(3)
    src = src.replace(old_vec_fn, new_vec_fn, 1)

    # 2. Patch _bm25_search: wrap query argument (CORR-002 fix: verify replacement)
    bm25_old = "(self.name, query, *filter_params, self.config.retrieval.bm25_top_k)"
    bm25_new = "(self.name, _sanitize_fts5_query(query), *filter_params, self.config.retrieval.bm25_top_k)"
    if bm25_old in src:
        src = src.replace(bm25_old, bm25_new, 1)
    elif bm25_new not in src:
        print("ERROR: could not find _bm25_search call site anchor. qmd source may have changed.", file=sys.stderr)
        sys.exit(6)

    # 3. Patch _check_strong_signal: wrap query argument (CORR-002 fix: verify replacement)
    strong_old = "(self.name, query, *filter_params)"
    strong_new = "(self.name, _sanitize_fts5_query(query), *filter_params)"
    if strong_old in src:
        src = src.replace(strong_old, strong_new, 1)
    elif strong_new not in src:
        print("ERROR: could not find _check_strong_signal call site anchor. qmd source may have changed.", file=sys.stderr)
        sys.exit(7)

    return src


def main() -> int:
    if not COLLECTION_PY.exists():
        print(f"ERROR: {COLLECTION_PY} does not exist.", file=sys.stderr)
        return 4

    src = _read()
    if _already_patched(src):
        print(f"OK: already patched ({COLLECTION_PY}).")
        return 0

    patched = _apply(src)

    # Atomic write
    tmp = COLLECTION_PY.with_suffix(".py.tmp")
    tmp.write_text(patched, encoding="utf-8")
    tmp.replace(COLLECTION_PY)

    # Verify
    if _already_patched(COLLECTION_PY.read_text(encoding="utf-8")):
        print(f"OK: patch applied to {COLLECTION_PY}.")
        print("Verify with: qmd search --collection wiki --query \"build-vs-port\" --top-k 1")
        return 0
    print("ERROR: patch did not persist after write.", file=sys.stderr)
    return 5


if __name__ == "__main__":
    sys.exit(main())

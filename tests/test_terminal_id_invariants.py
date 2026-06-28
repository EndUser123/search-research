"""Invariant: every canonical_terminal_id copy in the monorepo is byte-identical.

Drift here means someone hand-edited a copy instead of editing
``core/terminal_id.py`` + running ``scripts/sync_terminal_id.py``.
The test auto-discovers copies (so orphans are caught too) and reports each
path on failure with the resync command.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

_DEF_RE = re.compile(r"^def canonical_terminal_id\(", re.MULTILINE)

MARKETPLACE = Path(r"P:/packages/.claude-marketplace/plugins")
CANONICAL = (
    MARKETPLACE
    / "search-research"
    / "core"
    / "terminal_id.py"
)


def _discover_copies() -> list[Path]:
    """Every .py under the plugin marketplace defining canonical_terminal_id."""
    found: list[Path] = []
    for py in MARKETPLACE.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _DEF_RE.search(text):
            found.append(py)
    return sorted(found)


def _sha(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def test_canonical_source_exists():
    assert CANONICAL.is_file(), f"canonical source missing: {CANONICAL}"


def test_all_copies_byte_identical():
    copies = _discover_copies()
    assert copies, "no canonical_terminal_id copies found — discovery broken"
    # Canonical must be among the discovered files (self-contained check).
    assert CANONICAL in copies, (
        f"canonical source {CANONICAL} not in discovered set:\n"
        + "\n".join(f"  {p}" for p in copies)
    )

    by_hash: dict[str, list[Path]] = {}
    for p in copies:
        by_hash.setdefault(_sha(p), []).append(p)

    if len(by_hash) != 1:
        msgs = ["DRIFT: canonical_terminal_id copies diverge. Hash groups:"]
        for h, paths in sorted(by_hash.items()):
            msgs.append(f"  sha1 {h[:12]}:")
            for p in paths:
                msgs.append(f"    {p}")
        msgs.append(
            "\nFix: edit ONLY search-research/core/terminal_id.py, "
            "then run: python scripts/sync_terminal_id.py"
        )
        pytest.fail("\n".join(msgs))


def test_no_static_default_id():
    """The algorithm must NEVER return a static/constant id (hard requirement)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("canonical_tid", CANONICAL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Same env -> same id (deterministic), but two DIFFERENT env values must
    # yield two DIFFERENT ids. A static default would collapse them.
    import os

    os.environ["CLAUDE_TERMINAL_ID"] = "terminal-A"
    a = mod.canonical_terminal_id()
    os.environ["CLAUDE_TERMINAL_ID"] = "terminal-B-unique"
    b = mod.canonical_terminal_id()
    del os.environ["CLAUDE_TERMINAL_ID"]

    assert a != b, (
        f"uniqueness collapsed: two different env values gave same id ({a}); "
        "the algorithm is returning a static default"
    )
    assert a.startswith("console_") and b.startswith("console_")

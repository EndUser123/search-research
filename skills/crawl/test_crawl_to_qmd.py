#!/usr/bin/env python3
"""Self-checks for crawl_to_qmd. Run: python test_crawl_to_qmd.py

No framework. Covers the post-Change-A contract:
- T1: _exclude_self pure predicate (identity = file basename, never title)
- T2: entry-point --help smoke (catches a broken refactor that pytest would miss)
- strip-related idempotency + source-content preservation
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crawl_to_qmd import _exclude_self, _strip_related  # noqa: E402


def test_exclude_self_drops_own_record_by_basename() -> None:
    records = [
        {"title": "Self", "file": "wiki/sources/github.com/self.md"},
        {"title": "Other", "file": "wiki/sources/github.com/other.md"},
        {"title": "Sibling", "file": "wiki/sources/other.com/sibling.md"},
    ]
    out = _exclude_self(records, "self.md")
    assert len(out) == 2, f"expected 2 after self-exclusion, got {len(out)}"
    assert all(Path(r["file"]).name != "self.md" for r in out)


def test_exclude_self_keeps_same_title_sibling() -> None:
    # identity is file basename, NOT title — a sibling sharing a title must survive
    records = [
        {"title": "Same Title", "file": "wiki/a.md"},
        {"title": "Same Title", "file": "wiki/b.md"},
    ]
    assert len(_exclude_self(records, "a.md")) == 1


def test_strip_related_removes_injected_block_and_is_idempotent() -> None:
    body = "Content here.\n\n## Related\n[[X]]@related\n[[Y]]@related\n"
    stripped = _strip_related(body)
    assert "## Related" not in stripped
    assert "[[X]]@related" not in stripped
    assert "Content here." in stripped
    assert _strip_related(stripped) == stripped  # idempotent


def test_strip_related_preserves_source_authored_section() -> None:
    # A source-authored ## Related with prose body must NOT be stripped.
    prose = "Intro.\n\n## Related\nSome prose about related work.\nMore text.\n"
    assert "## Related" in _strip_related(prose)


def test_help_smoke() -> None:
    r = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "crawl_to_qmd.py"), "--help"],
        capture_output=True,
        timeout=20,
    )
    assert r.returncode == 0, f"--help exited {r.returncode}: {r.stderr.decode()[:200]}"


if __name__ == "__main__":
    test_exclude_self_drops_own_record_by_basename()
    print("PASS test_exclude_self_drops_own_record_by_basename")
    test_exclude_self_keeps_same_title_sibling()
    print("PASS test_exclude_self_keeps_same_title_sibling")
    test_strip_related_removes_injected_block_and_is_idempotent()
    print("PASS test_strip_related_removes_injected_block_and_is_idempotent")
    test_strip_related_preserves_source_authored_section()
    print("PASS test_strip_related_preserves_source_authored_section")
    test_help_smoke()
    print("PASS test_help_smoke")
    print("ALL PASS")

#!/usr/bin/env python3
"""
Orphan detection for Stop/Hook modules.

EXPERIMENTAL: Detects Stop/StopHook/stop/ modules that are neither
  (a) referenced in settings.json or imported into active hooks, nor
  (b) explicitly marked experimental/archived with the required docstring markers.
  wired: false
  review: TBD

Exit codes:
  0 — no orphans found
  1 — orphans detected (print names)
  2 — usage error
"""

from __future__ import annotations

import json
import re
import sys
from glob import glob
from pathlib import Path
from typing import NamedTuple


HOOKS_DIR = Path(__file__).resolve().parent.parent


class ModuleInfo(NamedTuple):
    path: Path
    rel: str  # relative to HOOKS_DIR
    is_experimental: bool
    is_archived: bool
    wired: bool
    docstring_snippet: str


def _read_docstring(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # Extract docstring
    match = re.match(r'(?s)^""".*?"""', text, re.MULTILINE)
    if match:
        return match.group()[:200]
    return ""


def _check_wired(path: Path, hooks_dir: Path) -> bool:
    """Return True if the module is referenced in settings.json or imported."""
    # Check settings.json
    settings = hooks_dir / ".claude" / "settings.json"
    if settings.exists():
        try:
            content = settings.read_text(encoding="utf-8")
            name = path.stem
            if name in content:
                return True
        except (OSError, json.JSONDecodeError):
            pass

    # Check imports in Stop.py
    stop_py = hooks_dir / "Stop.py"
    if stop_py.exists():
        try:
            text = stop_py.read_text(encoding="utf-8")
            name = path.stem
            # Match import statements: import X, from X import, import_hook("X")
            if re.search(rf'\bimport\s+{re.escape(name)}\b', text):
                return True
            if re.search(rf'\bfrom\s+[.\w]+\s+import\s+.*{re.escape(name)}', text):
                return True
            if re.search(rf'import_hook\s*\(\s*["\'].*{re.escape(name)}', text):
                return True
            # Match "from X import" inside _run_* functions (e.g., from Stop_safety_gate import ...)
            if re.search(rf'from\s+{re.escape(name)}\s+import', text):
                return True
            # Check SIDE_EFFECTS list entries (e.g., "Stop_cleanup_verifier.py" → name matches)
            if re.search(rf'["\']\s*{re.escape(name)}\.py\s*["\']', text):
                return True
        except OSError:
            pass

    # Check imports in PreToolUse.py
    pretooluse = hooks_dir / "PreToolUse.py"
    if pretooluse.exists():
        try:
            text = pretooluse.read_text(encoding="utf-8")
            name = path.stem
            if re.search(rf'\bimport\s+{re.escape(name)}\b', text):
                return True
        except OSError:
            pass

    return False


def _check_docstring_markers(docstring: str) -> tuple[bool, bool]:
    """Returns (is_experimental, is_archived)."""
    doc_lower = docstring.lower()
    is_experimental = (
        "experimental" in doc_lower
        and ("wired" in doc_lower or "review" in doc_lower or "archival" in doc_lower)
    )
    is_archived = "archived" in doc_lower
    return is_experimental, is_archived


def _scan_modules(hooks_dir: Path) -> list[ModuleInfo]:
    modules: list[ModuleInfo] = []

    # Patterns to scan
    locations = [
        hooks_dir / "Stop.py",
        hooks_dir / "StopHook_*.py",
        hooks_dir / "Stop_*.py",
        hooks_dir / "stop",
    ]

    seen: set[Path] = set()
    for loc in locations:
        if loc.is_file():
            candidates = [loc]
        else:
            candidates = list(glob(str(loc)))

        for path in candidates:
            path = Path(path).resolve()
            if path in seen:
                continue
            # Skip directories — only process files
            if path.is_dir():
                continue
            seen.add(path)

            # Exclude __init__.py, __pycache__, test files
            if (
                "__pycache__" in str(path)
                or "__init__" in path.name
                or path.name.startswith("test_")
                or "_test.py" in path.name
                or path.name.startswith("test")
            ):
                continue

            # Skip files outside hooks_dir (e.g., symlinks or cross-directory matches)
            try:
                rel = path.relative_to(hooks_dir)
            except ValueError:
                continue
            docstring = _read_docstring(path)
            is_experimental, is_archived = _check_docstring_markers(docstring)
            wired = _check_wired(path, hooks_dir)

            modules.append(
                ModuleInfo(
                    path=path,
                    rel=str(rel),
                    is_experimental=is_experimental,
                    is_archived=is_archived,
                    wired=wired,
                    docstring_snippet=docstring[:80],
                )
            )

    return modules


def _orphaned(modules: list[ModuleInfo]) -> list[ModuleInfo]:
    """Modules that are orphans: not wired AND not properly marked experimental/archived."""
    orphans = []
    for m in modules:
        if m.wired:
            continue
        if m.is_experimental or m.is_archived:
            continue
        orphans.append(m)
    return orphans


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv

    hooks_dir = HOOKS_DIR
    if len(argv) > 1:
        hooks_dir = Path(argv[1]).resolve()
        if not hooks_dir.is_dir():
            print(f"Error: {hooks_dir} is not a directory", file=sys.stderr)
            return 2

    modules = _scan_modules(hooks_dir)
    orphans = _orphaned(modules)

    if orphans:
        print(f"ORPHANED STOP/HOOK MODULES ({len(orphans)}):")
        for m in orphans:
            print(f"  {m.rel}")
            print(f"    docstring: {m.docstring_snippet!r}")
        print()
        print(
            "To fix: either (a) wire the module into Stop.py/settings.json/PreToolUse.py, "
            "or (b) move to stop/experimental/ or stop/archived/ with the required docstring markers."
        )
        return 1

    print("No orphaned modules found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
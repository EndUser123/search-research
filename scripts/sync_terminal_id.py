"""Regenerate every canonical_terminal_id copy from the source of truth.

Plugins must stay independent (no cross-plugin import), so the canonical
terminal_id algorithm is copied byte-for-byte into each plugin that needs it.
This script is the single edit point: change ``core/terminal_id.py``, run me,
and every copy updates. The invariant test fails on any drift.

    python scripts/sync_terminal_id.py          # write all copies
    python scripts/sync_terminal_id.py --check  # exit 1 if any copy drifted

Destination filenames differ per plugin to avoid colliding with each plugin's
own legacy ``terminal_id``/``terminal_detection`` modules. Content is identical;
the invariant test hashes content, not path.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = Path(r"P:/packages/.claude-marketplace/plugins")

CANONICAL = ROOT / "core" / "terminal_id.py"

# (plugin_dir, relpath_within_plugin). Add a row when a new plugin needs the id.
COPIES: list[tuple[str, str]] = [
    ("cc-skills-analysis", "__lib/terminal_id.py"),
    ("skill-guard", "src/skill_guard/utils/canonical_terminal_id.py"),
    ("snapshot", "scripts/hooks/__lib/canonical_terminal_id.py"),
]


def _dests() -> list[Path]:
    return [MARKETPLACE / plugin / rel for plugin, rel in COPIES]


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    if not CANONICAL.exists():
        print(f"FATAL: canonical source missing: {CANONICAL}", file=sys.stderr)
        return 2

    canonical_bytes = CANONICAL.read_bytes()
    exit_code = 0

    for dest in _dests():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() == canonical_bytes:
            print(f"ok      {dest}")
            continue
        if check_only:
            print(f"DRIFT   {dest}")
            exit_code = 1
            continue
        dest.write_bytes(canonical_bytes)
        print(f"synced  {dest}")

    if exit_code:
        print(
            "\nDrift detected. Re-run without --check to resync, "
            "or edit ONLY core/terminal_id.py then resync.",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

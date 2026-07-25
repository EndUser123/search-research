#!/usr/bin/env python3
"""List dirty git files with age in days, sorted oldest first.

Used by AAR Phase 8.5 check #6 (stale dirty files >7 days old).
Stable location: P:/.agents/scripts/dirty_age.py

For submodules (status `m` = dirty working tree inside), recurses into
the submodule and reports the age of the oldest dirty file within,
not the mtime of the submodule directory entry at the parent level
(which reflects checkout time, not modification time).
"""
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

CWD = Path(os.environ.get("DIRTY_AGE_ROOT", "P:/"))


def _git_status_lines(cwd: Path) -> list[str]:
    """Run git status --short and return non-empty lines.
    Do NOT strip the whole stdout — the leading space in the XY status
    column is significant. Stripping it shifts file paths by one char."""
    r = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd=str(cwd),
    )
    if not r.stdout:
        return []
    return [l for l in r.stdout.split("\n") if l.strip()]


def _max_age_of_files(file_paths: list[str], base: Path, now: datetime) -> int:
    """Return the maximum age (days) among the given relative paths."""
    max_age = -1
    for fp in file_paths:
        full = base / fp
        try:
            mtime = datetime.fromtimestamp(full.stat().st_mtime, tz=timezone.utc)
            age = (now - mtime).days
            if age > max_age:
                max_age = age
        except (OSError, FileNotFoundError):
            pass
    return max_age


now = datetime.now(timezone.utc)
rows = []

for line in _git_status_lines(CWD):
    status = line[:2]
    filepath = line[3:].strip()
    if not filepath:
        continue

    # Strip any quoting (git quotes paths with special chars)
    if filepath.startswith('"') and filepath.endswith('"'):
        filepath = filepath[1:-1]

    x, y = status[0], status[1]
    full_path = CWD / filepath

    # Second-column 'm' = submodule has modified content (dirty tree inside).
    # The parent gitlink has NOT moved — only first-column M/m means pointer
    # advanced. For dirty submodules, recurse to get the actual file ages.
    if y == 'm' and full_path.is_dir():
        sub_files = [l[3:].strip().strip('"') for l in _git_status_lines(full_path)]
        age_days = _max_age_of_files(sub_files, full_path, now) if sub_files else -1
    else:
        try:
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime, tz=timezone.utc)
            age_days = (now - mtime).days
        except (OSError, FileNotFoundError):
            age_days = -1

    rows.append((age_days, status.strip(), filepath))

rows.sort(key=lambda r: r[0], reverse=True)

print(f"{'Age (days)':>10}  {'Status':<4}  File")
print("-" * 80)
for age, status, filepath in rows:
    if age < 0:
        age_str = "???"
    elif age == 0:
        age_str = "<1"
    else:
        age_str = str(age)
    marker = " *** OLD" if age > 7 else ""
    print(f"{age_str:>10}  {status:<4}  {filepath}{marker}")

old = [r for r in rows if r[0] > 7]
print(f"\nTotal dirty files: {len(rows)}")
print(f"Older than 7 days: {len(old)}")
print(f"Older than 30 days: {len([r for r in rows if r[0] > 30])}")

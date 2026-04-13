"""Changelog reader/writer for skill activity tracking.

Writes skill activity entries to package CHANGELOG.md under ## [Unreleased].
Reads ## [Unreleased] to determine which skills have already run.

Format under ## [Unreleased]:
    ### Investigated
    - **/search** (2026-04-12): Identified FTS5 fallback issues in CHS backend
    - **/sqa** (2026-04-12): Full 11-layer quality analysis of search-research

    ### Fixed
    - **/refactor** (2026-04-12): Fixed FTS5 MATCH fallback in claude_history_backend.py

Each entry records: skill name, date, description of what was done.
GTO reads this to avoid re-recommending skills already run on a target.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ── Section constants ───────────────────────────────────────────────────────────

SECTIONS = [
    "Investigated",   # Diagnostic/investigation skills: /search, /sqa, /pre-mortem, /critique
    "Analyzed",       # Analysis skills: /rca, /diagnose
    "Fixed",          # Implementation skills: /refactor, /code, /tdd, /doc, /deps
    "Verified",       # Verification skills: /verify, /truth
    "Planned",        # Planning skills: /planning, /breakdown
]


# ── Types ─────────────────────────────────────────────────────────────────────


@dataclass
class ChangelogEntry:
    """A single skill activity entry in the changelog."""

    skill: str           # e.g., "/search", "/refactor"
    date: str            # ISO date string e.g., "2026-04-12"
    description: str     # What was done
    section: str         # Section name (Investigated, Fixed, etc.)


@dataclass
class ChangelogSection:
    """A section under ## [Unreleased]."""

    name: str                   # e.g., "Investigated"
    entries: list[ChangelogEntry]


# ── Section classification ─────────────────────────────────────────────────────


def _classify_skill_section(skill: str) -> str:
    """Map a skill name to the appropriate changelog section.

    Args:
        skill: Skill name e.g., "/search", "/refactor"

    Returns:
        Section name
    """
    skill_lower = skill.lower()

    investigated = {"/search", "/research", "/sqa", "/pre-mortem", "/critique",
                     "/diagnose", "/rca", "/gto", "/review_bundle"}
    analyzed     = {"/rca", "/diagnose", "/analyze"}
    fixed       = {"/refactor", "/code", "/tdd", "/doc", "/deps", "/git", "/push",
                   "/planning", "/breakdown"}
    verified    = {"/verify", "/truth", "/test"}

    if skill_lower in investigated:
        return "Investigated"
    if skill_lower in analyzed:
        return "Analyzed"
    if skill_lower in fixed:
        return "Fixed"
    if skill_lower in verified:
        return "Verified"
    return "Investigated"  # Default for diagnostic skills


# ── Low-level parsing ─────────────────────────────────────────────────────────


def _parse_entry(line: str) -> ChangelogEntry | None:
    """Parse a single bullet entry line into a ChangelogEntry.

    Expected formats:
      - **/search** (2026-04-12): Identified FTS5 issues
      - **/refactor** (2026-04-12): Fixed FTS5 MATCH fallback

    Args:
        line: A markdown bullet line

    Returns:
        ChangelogEntry or None if line doesn't match format
    """
    # Match: - **/skill** (YYYY-MM-DD): description
    m = re.match(r"^\s*-\s+\*\*(/\S+)\*\*\s+\((\d{4}-\d{2}-\d{2})\):\s+(.+)$", line)
    if not m:
        return None
    return ChangelogEntry(
        skill=m.group(1),
        date=m.group(2),
        description=m.group(3).strip(),
        section="",  # Section assigned by caller
    )


def _parse_unreleased(content: str) -> dict[str, list[ChangelogEntry]]:
    """Parse ## [Unreleased] section from changelog content.

    Args:
        content: Full changelog text

    Returns:
        Dict mapping section name -> list of entries
    """
    sections: dict[str, list[ChangelogEntry]] = {s: [] for s in SECTIONS}

    # Find ## [Unreleased] block
    unreleased_match = re.search(
        r"^##\s+\[Unreleased\](.*?)^(?=##\s+\[|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not unreleased_match:
        return sections

    block = unreleased_match.group(1)

    # Parse each section header and its entries
    current_section = ""
    for line in block.splitlines():
        # Section header: ### SectionName
        section_match = re.match(r"^###\s+(\w+)", line)
        if section_match:
            current_section = section_match.group(1)
            continue
        # Bullet entry
        if current_section and current_section in sections:
            entry = _parse_entry(line)
            if entry:
                entry.section = current_section
                sections[current_section].append(entry)

    return sections


# ── Reading ───────────────────────────────────────────────────────────────────


def read_package_changelog(changelog_path: Path) -> dict[str, list[ChangelogEntry]]:
    """Read all entries from a package's CHANGELOG.md.

    Args:
        changelog_path: Path to CHANGELOG.md

    Returns:
        Dict mapping section name -> entries found
    """
    if not changelog_path.exists():
        return {s: [] for s in SECTIONS}
    try:
        content = changelog_path.read_text(encoding="utf-8")
    except OSError:
        return {s: [] for s in SECTIONS}
    return _parse_unreleased(content)


def get_skills_run(changelog_path: Path) -> set[str]:
    """Get set of skills that have already run on a package.

    Args:
        changelog_path: Path to CHANGELOG.md

    Returns:
        Set of skill names already recorded
    """
    sections = read_package_changelog(changelog_path)
    skills: set[str] = set()
    for entries in sections.values():
        for entry in entries:
            skills.add(entry.skill)
    return skills


# ── Writing ───────────────────────────────────────────────────────────────────


def _build_section(name: str, entries: list[ChangelogEntry]) -> str:
    """Build a markdown section from entries."""
    if not entries:
        return f"### {name}\n"
    lines = [f"### {name}"]
    for e in entries:
        lines.append(f"- **{e.skill}** ({e.date}): {e.description}")
    lines.append("")  # Blank line after section
    return "\n".join(lines) + "\n"


def _entry_exists(
    entries: list[ChangelogEntry],
    skill: str,
    description: str,
    days_window: int = 7,
) -> bool:
    """Check if a similar entry already exists.

    Args:
        entries: Existing entries in the section
        skill: Skill name
        description: Description to match
        days_window: Treat as duplicate if same skill within N days

    Returns:
        True if entry is likely a duplicate
    """
    from datetime import datetime, timedelta

    for entry in entries:
        if entry.skill != skill:
            continue
        # Same skill — check recency
        try:
            entry_date = datetime.strptime(entry.date, "%Y-%m-%d").date()
            entry_age = (date.today() - entry_date).days
            if entry_age <= days_window:
                return True
        except ValueError:
            pass
    return False


def append_package_changelog(
    changelog_path: Path,
    skill: str,
    description: str,
    force: bool = False,
) -> bool:
    """Append a skill activity entry to a package's CHANGELOG.md.

    Adds entry under ## [Unreleased] > ### {section} in the appropriate section.
    Silently skips if a recent duplicate entry exists (same skill within 7 days).

    Args:
        changelog_path: Path to CHANGELOG.md (e.g., P:/packages/search-research/CHANGELOG.md)
        skill: Skill name e.g., "/search", "/refactor"
        description: Human-readable description of what was done
        force: Skip duplicate detection and write anyway

    Returns:
        True if entry was written (or is a fresh duplicate), False on error
    """
    section = _classify_skill_section(skill)
    new_entry = ChangelogEntry(
        skill=skill,
        date=date.today().isoformat(),
        description=description,
        section=section,
    )

    # Ensure parent dir exists
    try:
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    # Read existing content
    if changelog_path.exists():
        try:
            content = changelog_path.read_text(encoding="utf-8")
        except OSError:
            content = ""
    else:
        content = ""

    # Parse existing entries
    sections = _parse_unreleased(content)

    # Duplicate check (skip if same skill run recently, unless forced)
    if not force and _entry_exists(sections[section], skill, description):
        return True  # Not an error — just a duplicate

    # Add new entry
    sections[section].append(new_entry)

    # Rebuild the unreleased block
    unreleased_lines = ["## [Unreleased]", ""]
    for s in SECTIONS:
        unreleased_lines.append(_build_section(s, sections[s]).rstrip())

    # Replace or insert ## [Unreleased] section using LINE-BASED logic (not DOTALL regex)
    unreleased_block = "\n".join(unreleased_lines) + "\n"
    lines = content.splitlines(keepends=True)
    unreleased_idx = None
    section_end_idx = None

    # Find first ## [Unreleased] line
    for i, line in enumerate(lines):
        if re.match(r"^##\s+\[Unreleased\]", line):
            unreleased_idx = i
            # Find the next ## heading, --- separator, or end of file
            for j in range(i + 1, len(lines)):
                if re.match(r"^##\s+\[", lines[j]) or lines[j].startswith("---"):
                    section_end_idx = j
                    break
            else:
                section_end_idx = len(lines)
            break

    if unreleased_idx is not None:
        # Replace only the ## [Unreleased] section (line-based, no DOTALL)
        new_lines = lines[:unreleased_idx] + [unreleased_block] + lines[section_end_idx:]
        new_content = "".join(new_lines)
    else:
        # No ## [Unreleased] — prepend it
        new_content = unreleased_block + content

    # Atomic write
    try:
        tmp = changelog_path.with_suffix(".tmp")
        tmp.write_text(new_content, encoding="utf-8")
        tmp.replace(changelog_path)
    except OSError:
        return False
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    return True


# ── Convenience wrappers ───────────────────────────────────────────────────────


def record_investigation(package_root: Path, skill: str, description: str) -> bool:
    """Record a diagnostic/investigation skill run."""
    return append_package_changelog(
        changelog_path=package_root / "CHANGELOG.md",
        skill=skill,
        description=description,
    )


def record_fix(package_root: Path, skill: str, description: str) -> bool:
    """Record a fix/implementation skill run."""
    return append_package_changelog(
        changelog_path=package_root / "CHANGELOG.md",
        skill=skill,
        description=description,
    )


def record_verification(package_root: Path, skill: str, description: str) -> bool:
    """Record a verification skill run."""
    return append_package_changelog(
        changelog_path=package_root / "CHANGELOG.md",
        skill=skill,
        description=description,
    )

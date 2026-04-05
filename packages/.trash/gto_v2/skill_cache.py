#!/usr/bin/env python3
"""
Cached skill metadata for /gto recommendations.

This module provides skill metadata caching with delta detection to avoid
rescanning all skill files on every /gto invocation.

Cache file: .claude/skills/gto/.skill_cache.json
Invalidation: Delta detection (skill file mtime changes)
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Paths relative to this script location
_SCRIPT_DIR = Path(__file__).parent
CACHE_FILE = _SCRIPT_DIR / ".skill_cache.json"
SKILLS_DIR = _SCRIPT_DIR.parent  # Go up from gto/ to skills/


def load_skill_metadata(force_refresh: bool = False) -> list[dict[str, Any]]:
    """
    Load skill metadata from cache (refresh if stale).

    Args:
        force_refresh: Force cache rebuild even if not stale

    Returns:
        List of skill metadata dictionaries, each containing:
        - name: Skill name
        - description: Skill description
        - suggest: List of suggested skills
        - triggers: List of trigger patterns
        - category: Skill category
        - skill_path: Path to skill directory

    Raises:
        IOError: If cache file cannot be read
        json.JSONDecodeError: If cache file is corrupted
    """
    # Check cache exists
    if not force_refresh and CACHE_FILE.exists():
        try:
            cache_data = json.loads(CACHE_FILE.read_text())

            # Check if cache is stale (skills changed)
            if not _is_cache_stale(cache_data):
                return cache_data.get("skills", [])
        except (OSError, json.JSONDecodeError) as e:
            # Cache corrupted or unreadable, rebuild
            print(f"[GTO cache] Warning: Cache file corrupted ({e}), rebuilding...")

    # Rebuild cache
    return _rebuild_cache()


def _is_cache_stale(cache_data: dict[str, Any]) -> bool:
    """
    Check if any skill file is newer than cache.

    Args:
        cache_data: Cache data dictionary

    Returns:
        True if cache is stale (skills changed), False otherwise
    """
    cache_time = cache_data.get("cache_time", 0)

    # Check if any SKILL.md file is newer than cache
    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            if skill_file.stat().st_mtime > cache_time:
                return True
        except (FileNotFoundError, PermissionError):
            # Skill file inaccessible, treat as stale
            return True

    return False


def _rebuild_cache() -> list[dict[str, Any]]:
    """
    Scan all skills and build cache.

    Returns:
        List of skill metadata dictionaries

    Raises:
        IOError: If cache file cannot be written
    """
    skills = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        # Parse frontmatter
        metadata = _parse_skill_frontmatter(skill_file)
        if metadata:
            metadata["skill_path"] = str(skill_dir)
            skills.append(metadata)

    # Write cache
    cache_data = {
        "cache_time": time.time(),
        "skills": skills,
        "skill_count": len(skills),
    }

    # Ensure directory exists
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        CACHE_FILE.write_text(json.dumps(cache_data, indent=2))
    except OSError as e:
        print(
            f"[GTO cache] Warning: Cannot write cache file ({e}), using in-memory cache"
        )

    return skills


def _parse_skill_frontmatter(skill_file: Path) -> dict[str, Any] | None:
    """
    Extract name, description, suggest, triggers from SKILL.md frontmatter.

    Args:
        skill_file: Path to SKILL.md file

    Returns:
        Metadata dictionary or None if parsing fails

    Examples:
        >>> metadata = _parse_skill_frontmatter(Path(".claude/skills/g/SKILL.md"))
        >>> metadata['name']
        'gto'
        >>> metadata['suggest']
        ['/r', '/q', '/reflect']
    """
    try:
        content = skill_file.read_text()
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"[GTO cache] Warning: Cannot read {skill_file} ({e}), skipping")
        return None

    # Extract YAML frontmatter (between --- markers)
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)

    if not frontmatter_match:
        # No frontmatter found, use filename as name
        return {
            "name": skill_file.parent.name,
            "description": f"{skill_file.parent.name} skill",
            "suggest": [],
            "triggers": [],
            "category": "general",
        }

    try:
        import yaml  # Lazy import, only if needed

        frontmatter = yaml.safe_load(frontmatter_match.group(1))
    except yaml.YAMLError as e:
        print(
            f"[GTO cache] Warning: YAML parsing failed for {skill_file} ({e}), using defaults"
        )
        return {
            "name": skill_file.parent.name,
            "description": f"{skill_file.parent.name} skill",
            "suggest": [],
            "triggers": [],
            "category": "general",
        }

    # Extract fields with defaults
    return {
        "name": frontmatter.get("name", skill_file.parent.name),
        "description": frontmatter.get(
            "description", f"{skill_file.parent.name} skill"
        ),
        "suggest": frontmatter.get("suggest", []),
        "triggers": frontmatter.get("triggers", []),
        "category": frontmatter.get("category", "general"),
    }


def invalidate_cache() -> None:
    """
    Delete cache file to force rebuild on next load.

    Useful for testing or when cache corruption detected.
    """
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
        except (OSError, PermissionError) as e:
            print(f"[GTO cache] Warning: Cannot delete cache file ({e})")


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics for monitoring.

    Returns:
        Dictionary with cache stats:
        - cache_exists: bool
        - cache_age_seconds: float (age of cache in seconds)
        - skill_count: int (number of skills in cache)
        - cache_file: str (path to cache file)
    """
    stats = {
        "cache_exists": CACHE_FILE.exists(),
        "cache_file": str(CACHE_FILE),
        "skill_count": 0,
    }

    if CACHE_FILE.exists():
        try:
            cache_data = json.loads(CACHE_FILE.read_text())
            stats["cache_age_seconds"] = time.time() - cache_data.get("cache_time", 0)
            stats["skill_count"] = cache_data.get("skill_count", 0)
        except (OSError, json.JSONDecodeError):
            stats["cache_corrupted"] = True

    return stats


if __name__ == "__main__":
    # Test cache functionality
    print("Building skill cache...")
    skills = load_skill_metadata(force_refresh=True)

    print(f"\nCache stats: {get_cache_stats()}")
    print(f"\nFound {len(skills)} skills:")

    for skill in skills[:5]:  # Show first 5
        print(f"  - {skill['name']}: {skill['description'][:50]}...")
        if skill["suggest"]:
            print(f"    Suggests: {', '.join(skill['suggest'])}")
        if skill["triggers"]:
            print(f"    Triggers: {', '.join(skill['triggers'][:3])}...")

    if len(skills) > 5:
        print(f"  ... and {len(skills) - 5} more skills")

"""
validate.py — basic shape validation before audit runs.
"""

from pathlib import Path


def validate_shape(skill_path: Path) -> tuple[bool, str]:
    """
    Check that skill directory has minimum viable structure.
    Returns (is_valid, message).
    """
    if not skill_path.exists():
        return False, f"Skill path does not exist: {skill_path}"

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md missing"

    content = skill_md.read_text()
    if len(content) < 100:
        return False, "SKILL.md appears truncated (< 100 chars)"

    # Must have at least name and description in frontmatter
    has_name = "name:" in content
    has_desc = "description:" in content
    if not (has_name and has_desc):
        return False, "SKILL.md missing required frontmatter fields (name, description)"

    return True, "OK"

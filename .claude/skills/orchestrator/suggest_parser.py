"""
Suggest Field Parser

Extracts suggest fields from SKILL.md files and builds skill relationship graph.
These fields indicate which skills should be suggested after each skill completes.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set


class SuggestFieldParser:
    """Parse suggest fields from skill SKILL.md files."""

    SKILLS_PATH = Path("P:/.claude/skills")

    def __init__(self) -> None:
        self.skills_graph: Dict[str, List[str]] = {}
        self.loaded = False

    def load_all_skills(self) -> Dict[str, List[str]]:
        """Scan all skills and extract suggest fields."""
        if self.loaded:
            return self.skills_graph

        for skill_dir in self.SKILLS_PATH.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            skill_name = f"/{skill_dir.name}"
            suggests = self._parse_skill_file(skill_file)

            if suggests:
                self.skills_graph[skill_name] = suggests

        self.loaded = True
        return self.skills_graph

    def _parse_skill_file(self, skill_file: Path) -> List[str]:
        """Extract suggest field from SKILL.md frontmatter."""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.startswith('---'):
                return []

            end_marker = content.find('\n---\n', 3)
            if end_marker == -1:
                return []

            frontmatter = content[3:end_marker]
            metadata = yaml.safe_load(frontmatter)

            if not metadata:
                return []

            suggests = metadata.get('suggest', [])
            if isinstance(suggests, str):
                suggests = [suggests]

            # Normalize format: ensure leading /
            suggests = [s if s.startswith('/') else f'/{s}' for s in suggests]

            return suggests

        except Exception as e:
            import sys
            print(f"Error parsing {skill_file}: {e}", file=sys.stderr)
            return []

    def get_suggestions(self, skill_name: str) -> List[str]:
        """Get suggested next skills for a given skill."""
        if not self.loaded:
            self.load_all_skills()

        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        return self.skills_graph.get(skill_name, [])

    def get_skill_metadata(self, skill_name: str) -> Dict:
        """Get full metadata for a skill from its SKILL.md."""
        # Normalize skill name
        if skill_name.startswith('/'):
            skill_name = skill_name[1:]

        skill_dir = self.SKILLS_PATH / skill_name
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            return {}

        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.startswith('---'):
                return {}

            end_marker = content.find('\n---\n', 3)
            if end_marker == -1:
                return {}

            frontmatter = content[3:end_marker]
            return yaml.safe_load(frontmatter) or {}

        except Exception as e:
            import sys
            print(f"Error reading metadata for {skill_name}: {e}", file=sys.stderr)
            return {}

    def get_all_skills(self) -> Set[str]:
        """Get all skill names in the system that have suggest fields."""
        if not self.loaded:
            self.load_all_skills()

        return set(self.skills_graph.keys())

    def get_graph(self) -> Dict[str, List[str]]:
        """Get the complete skill relationship graph."""
        if not self.loaded:
            self.load_all_skills()

        return self.skills_graph.copy()


# Singleton instance for module-level use
suggest_parser = SuggestFieldParser()

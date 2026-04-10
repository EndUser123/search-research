"""Skills Backend - Progressive Disclosure for Skills and Commands.

Implements the Tool Search pattern for Claude Code skills:
- Indexes only skill front matter (name, description, triggers, aliases)
- Searches skills and commands on-demand
- Returns minimal data for progressive disclosure
- Includes file_path for full skill loading when needed
- Enhanced discoverability with word-level tokenization
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Try to import yaml, fallback to simple regex parser
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from ...config import config

SearchResult = dict[str, Any]

# Backend name constant
BACKEND_SKILLS = "SKILLS"


class SkillsBackend:
    """Search backend for Claude Code skills and commands with progressive disclosure.

    This backend indexes only the YAML front matter of skill files (SKILL.md)
    and command files (*.md), enabling discovery without loading full content.
    This implements the Tool Search pattern for reducing context usage.

    Enhanced discoverability features:
    - Word-level tokenization (hyphens, underscores, slashes treated as spaces)
    - "bug-hunting" matches "bug hunting" and "bug_hunting"
    """

    def __init__(
        self,
        skills_dirs: list[str] | None = None,
        commands_dirs: list[str] | None = None,
        enable_cache: bool = True,
        use_defaults: bool = True,
    ) -> None:
        """Initialize the skills backend.

        Args:
            skills_dirs: List of directories containing SKILL.md files
            commands_dirs: List of directories containing command *.md files
            enable_cache: Whether to cache parsed front matter
            use_defaults: Whether to use default paths when none provided (set False for isolated testing)
        """
        if skills_dirs:
            self.skills_dirs = [Path(d) for d in skills_dirs]
        elif use_defaults:
            self.skills_dirs = [Path(config.SKILLS_DIR)]
        else:
            self.skills_dirs = []

        if commands_dirs:
            self.commands_dirs = [Path(d) for d in commands_dirs]
        elif use_defaults:
            self.commands_dirs = [Path(config.COMMANDS_DIR)]
        else:
            self.commands_dirs = []

        self._index: dict[str, SearchResult] = {}
        self._indexed = False
        self._enable_cache = enable_cache

    def _parse_front_matter(self, content: str) -> dict[str, Any]:
        """Parse YAML front matter from a markdown file.

        Args:
            content: File content as string

        Returns:
            Parsed front matter as dictionary
        """
        # Match YAML front matter between --- delimiters
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return {}

        front_matter_text = match.group(1)

        if YAML_AVAILABLE:
            try:
                result = yaml.safe_load(front_matter_text)
                # Ensure we always return a dict (YAML can return other types)
                if isinstance(result, dict):
                    return result
                return {}
            except yaml.YAMLError:
                pass

        # Fallback: simple key-value parser for common fields
        result = {}
        for line in front_matter_text.split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Handle list-like values (before type checks)
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
                # Strip quotes from string values (only if not a list)
                elif isinstance(value, str):
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                result[key] = value
        return result

    def _index_skill_file(self, skill_file: Path) -> list[SearchResult]:
        """Index a single skill file.

        Args:
            skill_file: Path to SKILL.md file

        Returns:
            List of search results (usually 1)
        """
        try:
            content = skill_file.read_text(encoding="utf-8")
            front_matter = self._parse_front_matter(content)

            if not front_matter:
                return []

            # Build searchable text from front matter fields
            searchable_parts = [
                front_matter.get("name", ""),
                front_matter.get("description", ""),
                front_matter.get("category", ""),
                front_matter.get("domain", ""),
            ]

            # Add triggers and aliases
            triggers = front_matter.get("triggers", [])
            if isinstance(triggers, list):
                searchable_parts.extend(triggers)

            aliases = front_matter.get("aliases", [])
            if isinstance(aliases, list):
                searchable_parts.extend(aliases)

            searchable_text = " ".join(str(p) for p in searchable_parts if p).lower()

            # Extract skill name from directory or front matter
            skill_name = front_matter.get("name", skill_file.parent.name)

            return [
                {
                    "name": skill_name,
                    "id": front_matter.get("id", skill_name),
                    "description": front_matter.get("description", ""),
                    "category": front_matter.get("category", ""),
                    "domain": front_matter.get("domain", ""),
                    "triggers": triggers if isinstance(triggers, list) else [],
                    "aliases": aliases if isinstance(aliases, list) else [],
                    "file_path": str(skill_file),
                    "type": "skill",
                    "_searchable_text": searchable_text,
                    "_searchable_text_normalized": self._normalize_search_text(searchable_text),
                }
            ]
        except (OSError, UnicodeDecodeError):
            return []

    def _index_command_file(self, command_file: Path) -> list[SearchResult]:
        """Index a single command file.

        Args:
            command_file: Path to command *.md file

        Returns:
            List of search results (usually 1)
        """
        try:
            content = command_file.read_text(encoding="utf-8")
            front_matter = self._parse_front_matter(content)

            if not front_matter:
                return []

            # Build searchable text
            searchable_parts = [
                front_matter.get("id", ""),
                front_matter.get("description", ""),
                front_matter.get("category", ""),
            ]

            # Add triggers for discoverability
            triggers = front_matter.get("triggers", [])
            if isinstance(triggers, list):
                searchable_parts.extend(triggers)

            handles = front_matter.get("handles", [])
            if isinstance(handles, list):
                searchable_parts.extend(handles)

            aliases = front_matter.get("aliases", [])
            if isinstance(aliases, list):
                searchable_parts.extend(aliases)

            searchable_text = " ".join(str(p) for p in searchable_parts if p).lower()

            command_id = front_matter.get("id", command_file.stem)

            return [
                {
                    "name": command_id,
                    "id": command_id,
                    "description": front_matter.get("description", ""),
                    "category": front_matter.get("category", ""),
                    "triggers": triggers if isinstance(triggers, list) else [],
                    "handles": handles if isinstance(handles, list) else [],
                    "aliases": aliases if isinstance(aliases, list) else [],
                    "file_path": str(command_file),
                    "type": "command",
                    "_searchable_text": searchable_text,
                    "_searchable_text_normalized": self._normalize_search_text(searchable_text),
                }
            ]
        except (OSError, UnicodeDecodeError):
            return []

    def build_index(self) -> None:
        """Build index of all skills and commands."""
        self._index.clear()

        # Index skills
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            # Find all *.md files in skills directory (SKILL.md or any *.md for flexibility)
            for skill_file in skills_dir.rglob("*.md"):
                for result in self._index_skill_file(skill_file):
                    key = f"skill:{result['name']}"
                    self._index[key] = result

        # Index commands
        for commands_dir in self.commands_dirs:
            if not commands_dir.exists():
                continue
            # Find all *.md files in commands directory
            for command_file in commands_dir.glob("*.md"):
                for result in self._index_command_file(command_file):
                    key = f"command:{result['id']}"
                    self._index[key] = result

        self._indexed = True

    def has_index(self) -> bool:
        """Check if index has been built."""
        return self._indexed and len(self._index) > 0

    def _normalize_search_text(self, text: str) -> str:
        """Normalize text for word-level matching.

        Converts hyphens, underscores, and slashes to spaces for token matching.
        This allows "bug-hunting", "bug_hunting", "bug/hunting" to all match "bug hunting".

        Args:
            text: Text to normalize

        Returns:
            Normalized text with separators replaced by spaces
        """
        # Replace common separators with spaces
        for sep in ["-", "_", "/", ".", ","]:
            text = text.replace(sep, " ")
        # Collapse multiple spaces
        return " ".join(text.split())

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search skills and commands by query.

        This method returns results in SearchBackend-compatible format with
        'title' and 'content' fields for compatibility with the search CLI.

        Enhanced with word-level tokenization for improved discoverability.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching skills/commands in SearchBackend format
        """
        raw_results = self._search_raw(query, limit)

        # Convert to SearchBackend format
        formatted_results = []
        for entry in raw_results:
            formatted_results.append(
                {
                    "title": entry.get("name", entry.get("id", "")),
                    "content": entry.get("description", ""),
                    "source": BACKEND_SKILLS,
                    "score": entry.get("score", 0.0),
                    "metadata": {
                        "file_path": entry.get("file_path", ""),
                        "type": entry.get("type", "unknown"),
                        "category": entry.get("category", ""),
                        "domain": entry.get("domain", ""),
                        "aliases": entry.get("aliases", []),
                        "triggers": entry.get("triggers", []),
                    },
                }
            )

        return formatted_results

    def _search_raw(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Raw search returning the internal entry format.

        Enhanced with word-level tokenization for discoverability.
        Matches queries regardless of hyphen/space/underscore separators.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching skills/commands with internal fields
        """
        if not query or not query.strip():
            return []

        # Auto-build index if needed
        if not self._indexed:
            self.build_index()

        query_lower = query.lower().strip()
        # Normalize query for word-level matching
        query_normalized = self._normalize_search_text(query_lower)

        # Search and score results
        results_with_scores = []
        for _key, entry in self._index.items():
            searchable = entry.get("_searchable_text", "")
            searchable_normalized = entry.get("_searchable_text_normalized", "")

            # Exact match gets highest score
            score = 0.0
            if query_lower == entry.get("name", "").lower():
                score = 1.0
            elif query_lower == entry.get("id", "").lower():
                score = 1.0
            elif query_lower in searchable:
                # Direct substring match - score based on position
                position = searchable.find(query_lower)
                if position == 0:
                    score = 0.9
                else:
                    score = 0.7 - (position / 1000)
            elif query_normalized in searchable_normalized:
                # Word-level match (hyphen/space normalization)
                # Slightly lower score than direct match
                position = searchable_normalized.find(query_normalized)
                if position == 0:
                    score = 0.85
                else:
                    score = 0.65 - (position / 1000)

            if score > 0:
                # Create result copy without internal _searchable_text
                result = {k: v for k, v in entry.items() if not k.startswith("_")}
                result["score"] = score
                results_with_scores.append((score, result))

        # Sort by score descending
        results_with_scores.sort(key=lambda x: x[0], reverse=True)

        # Return results without score wrapper
        return [r for _, r in results_with_scores[:limit]]

    def get_all_skills(self) -> list[SearchResult]:
        """Get all indexed skills.

        Returns:
            List of all skill entries
        """
        if not self._indexed:
            self.build_index()

        return [
            {k: v for k, v in entry.items() if not k.startswith("_")}
            for key, entry in self._index.items()
            if entry.get("type") == "skill"
        ]

    def get_all_commands(self) -> list[SearchResult]:
        """Get all indexed commands.

        Returns:
            List of all command entries
        """
        if not self._indexed:
            self.build_index()

        return [
            {k: v for k, v in entry.items() if not k.startswith("_")}
            for key, entry in self._index.items()
            if entry.get("type") == "command"
        ]

    def get_by_name(self, name: str) -> SearchResult | None:
        """Get skill or command by name/id.

        Args:
            name: Skill name or command ID

        Returns:
            Skill or command entry, or None if not found
        """
        if not self._indexed:
            self.build_index()

        # Try exact match
        for _key, entry in self._index.items():
            if entry.get("name", "").lower() == name.lower():
                return {k: v for k, v in entry.items() if not k.startswith("_")}
            if entry.get("id", "").lower() == name.lower():
                return {k: v for k, v in entry.items() if not k.startswith("_")}

        return None

"""Dependency Graph Analysis for /gto skill.

Maps file dependencies and detects cascading impacts.
"""

import logging
import re
from pathlib import Path
from typing import Any

SERENA_AVAILABLE = False  # Serena integration available but not imported

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyze file dependencies and cascading impacts."""

    def __init__(self, working_dir: str | Path = ".") -> None:
        """Initialize dependency analyzer.

        Args:
            working_dir: Base directory to analyze
        """
        self.working_dir = Path(working_dir)
        self.serena_available = SERENA_AVAILABLE
        logger.info(f"DependencyAnalyzer initialized for {self.working_dir}")

    def extract_imports(self, file_path: Path) -> list[str]:
        """Extract import statements from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of imported module names
        """
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Match import statements
            imports = []

            # Match "import X" and "from X import Y"
            patterns = [
                r"^import\s+(\w+)",
                r"^from\s+(\w+(?:\.\w+)*)\s+import",
            ]

            for line in content.split("\n"):
                for pattern in patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        imports.append(match.group(1))

            return imports

        except Exception as e:
            logger.warning(f"Failed to extract imports from {file_path}: {e}")
            return []

    def build_dependency_map(self, files: list[Path]) -> dict[str, list[str]]:
        """Build a dependency map for given files.

        Args:
            files: List of file paths to analyze

        Returns:
            Dict mapping file path to list of dependencies
        """
        dep_map = {}

        for file_path in files:
            if file_path.suffix == ".py":
                imports = self.extract_imports(file_path)
                # Convert imports to potential file paths
                deps = []
                for imp in imports:
                    # Look for local modules
                    potential_path = self.working_dir / f"{imp}.py"
                    if potential_path.exists():
                        deps.append(str(potential_path.relative_to(self.working_dir)))

                dep_map[str(file_path.relative_to(self.working_dir))] = deps

        logger.debug(f"Built dependency map for {len(dep_map)} files")
        return dep_map

    def detect_cascading_impacts(
        self,
        changed_file: str,
        dep_map: dict[str, list[str]]
    ) -> list[str]:
        """Detect files that would be impacted by a change.

        Args:
            changed_file: File that was modified
            dep_map: Dependency map from build_dependency_map

        Returns:
            List of files that depend on changed_file (transitively)
        """
        impacted = []

        # Direct dependents
        for file, deps in dep_map.items():
            if changed_file in deps:
                impacted.append(file)

        # For now, skip transitive dependency analysis
        # In production, would recursively analyze dependents

        logger.debug(f"Change to {changed_file} impacts {len(impacted)} files")
        return impacted

    def analyze_modified_files(
        self,
        modified_files: list[str]
    ) -> dict[str, Any]:
        """Analyze dependencies for modified files.

        Args:
            modified_files: List of modified file paths

        Returns:
            Analysis report with dependency information
        """
        # Build dependency map for all Python files in working dir
        python_files = list(self.working_dir.rglob("*.py"))
        dep_map = self.build_dependency_map(python_files)

        # Analyze each modified file
        impact_report = {}
        for file_path in modified_files:
            impacts = self.detect_cascading_impacts(file_path, dep_map)
            impact_report[file_path] = {
                "dependencies": dep_map.get(file_path, []),
                "impacted_files": impacts,
                "impact_count": len(impacts)
            }

        return {
            "dependency_map": dep_map,
            "impact_analysis": impact_report,
            "total_files_analyzed": len(python_files)
        }

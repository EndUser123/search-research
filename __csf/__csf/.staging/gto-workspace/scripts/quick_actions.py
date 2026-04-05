"""Quick Actions Menu for /gto skill.

Generates one-command fixes for common gaps.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QuickActionsGenerator:
    """Generate one-command fixes for detected gaps."""

    def __init__(self, working_dir: str | Path = ".") -> None:
        """Initialize quick actions generator.

        Args:
            working_dir: Base directory for command execution
        """
        self.working_dir = Path(working_dir)
        logger.info(f"QuickActionsGenerator initialized for {self.working_dir}")

    def generate_todo_fixes(self, todos: list[str]) -> list[dict[str, Any]]:
        """Generate quick fix commands for TODO items.

        Args:
            todos: List of TODO strings

        Returns:
            List of action dicts with command and description
        """
        actions = []

        for todo in todos:
            # Extract file path if mentioned
            file_match = re.search(r"([\w./]+\.py)", todo)
            if file_match:
                file_path = file_match.group(1)
                actions.append({
                    "type": "edit_file",
                    "description": f"Address TODO: {todo}",
                    "command": f"edit {file_path}",
                    "priority": "medium"
                })

        return actions

    def generate_test_commands(self, test_gaps: list[str]) -> list[dict[str, Any]]:
        """Generate test creation commands.

        Args:
            test_gaps: List of modules missing tests

        Returns:
            List of action dicts for creating tests
        """
        actions = []

        for gap in test_gaps:
            # Extract module name
            module_match = re.search(r"(\w+(?:\.\w+)*)", gap)
            if module_match:
                module = module_match.group(1)
                actions.append({
                    "type": "create_test",
                    "description": f"Create tests for {module}",
                    "command": f"pytest-test-create {module}",
                    "priority": "high"
                })

        return actions

    def generate_commit_action(self, changed_files: list[str]) -> dict[str, Any]:
        """Generate commit command for changed files.

        Args:
            changed_files: List of modified file paths

        Returns:
            Action dict for committing changes
        """
        if not changed_files:
            return {}

        return {
            "type": "commit",
            "description": f"Commit {len(changed_files)} changed file(s)",
            "command": "git commit",
            "priority": "low"
        }

    def generate_all_actions(self, session_report: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate all applicable quick actions from session report.

        Args:
            session_report: Session analysis report

        Returns:
            List of prioritized action dicts
        """
        all_actions = []

        # Generate TODO fixes
        todos = session_report.get("todos", [])
        all_actions.extend(self.generate_todo_fixes(todos))

        # Generate test commands
        unfinished = session_report.get("unfinished_work", [])
        all_actions.extend(self.generate_test_commands(unfinished))

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_actions.sort(key=lambda a: priority_order.get(a.get("priority", "low"), 3))

        logger.info(f"Generated {len(all_actions)} quick actions")
        return all_actions

    def format_actions_menu(self, actions: list[dict[str, Any]]) -> str:
        """Format actions as a numbered menu.

        Args:
            actions: List of action dicts

        Returns:
            Formatted menu string
        """
        if not actions:
            return "No quick actions available."

        lines = ["Quick Actions Menu:", ""]
        for i, action in enumerate(actions, 1):
            priority_symbol = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(action.get("priority", "low"), "⚪")

            lines.append(
                f"{i}. {priority_symbol} {action['description']}\n"
                f"   Command: {action['command']}"
            )

        lines.append("\nExecute with: /gto --action <number>")
        return "\n".join(lines)

#!/usr/bin/env python3
from __future__ import annotations

"""
Variable Semantics Contract Protection

Prevents semantic swaps between confusable variables with different meanings.
Example: completed_count (all channels) vs successful_downloads (only with content)

This module extends the existing regression_prevention.py system.
"""

import re
from pathlib import Path
from typing import Any

# Type alias
type CheckResult = dict[str, Any] | None


class VariableSemanticsChecker:
    """Checks for variable semantic swap violations."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(".")
        self.contracts: list[dict] = []
        self._cache: dict[str, bool] = {}  # Cache for swap analysis

    def load_yaml_contracts(self) -> None:
        """Load all .contracts.yaml files from project.

        Searches for .contracts.yaml files alongside source code.
        """
        import yaml

        try:
            for contract_file in self.project_root.glob("**/.contracts.yaml"):
                try:
                    with open(contract_file) as f:
                        data = yaml.safe_load(f) or {}
                except Exception:
                    continue

                contract_dir = contract_file.parent

                for contract in data.get("contracts", []):
                    if contract.get("type") == "variable_semantics":
                        # Resolve relative file paths
                        file_path = contract.get("file_path", "")
                        if file_path and not Path(file_path).is_absolute():
                            # Normalize slashes
                            file_path = file_path.replace("\\", "/")

                            # Check if file_path already matches contract_dir structure
                            # If contract is in src/ and file_path starts with src/,
                            # don't double-nest the paths
                            contract_dir_name = contract_dir.name
                            if file_path.startswith(contract_dir_name + "/"):
                                # file_path already includes directory, use as-is relative to project_root
                                resolved = self.project_root / file_path
                            else:
                                resolved = (contract_dir / file_path).resolve()

                            # Store as relative path from project_root for easier matching
                            try:
                                contract["file_path"] = str(resolved.relative_to(self.project_root)).replace("\\", "/")
                            except ValueError:
                                # If not relative, use full path
                                contract["file_path"] = str(resolved).replace("\\", "/")
                        else:
                            contract["file_path"] = file_path.replace("\\", "/") if file_path else file_path
                        self.contracts.append(contract)
        except Exception:
            pass  # No contracts found is fine

    def find_contract_for_file(self, file_path: str) -> dict | None:
        """Find variable semantics contract for given file.

        Args:
            file_path: Path to source file

        Returns:
            Contract dict or None
        """
        file_path_normalized = str(file_path).replace("\\", "/").lstrip("./")

        for contract in self.contracts:
            contract_path = contract.get("file_path", "").replace("\\", "/").lstrip("./")

            if (file_path_normalized.endswith(contract_path) or
                file_path_normalized == contract_path):
                return contract

        return None

    def check_for_semantic_swap(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        source_content: str | None = None
    ) -> CheckResult:
        """Check if edit causes semantic variable swap.

        Args:
            file_path: Path to file being edited
            old_string: Content being replaced
            new_string: New content
            source_content: Full file content (optional, for deeper analysis)

        Returns:
            Blocking response dict if swap detected, None otherwise
        """
        contract = self.find_contract_for_file(file_path)
        if not contract:
            return None

        confusable_pairs = contract.get("confusable_pairs", [])
        usage_rules = contract.get("usage_rules", [])

        if not confusable_pairs or not usage_rules:
            return None

        # Check for swap in the new_string (line-by-line analysis)
        for rule in usage_rules:
            context = rule.get("context", "")
            must_use = rule.get("must_use", "")

            if not context or not must_use:
                continue

            # Check each line of new_string
            for line in new_string.split("\n"):
                if re.search(rf"\b{re.escape(context)}\b", line):
                    # Found context pattern - check if wrong variable is used
                    for pair in confusable_pairs:
                        var1, var2 = pair[0], pair[1]

                        # Determine which variable is wrong
                        wrong_var = None
                        if must_use == var1 and re.search(rf"\b{re.escape(var2)}\b", line):
                            # Check that correct var is NOT present
                            if not re.search(rf"\b{re.escape(var1)}\b", line):
                                wrong_var = var2
                        elif must_use == var2 and re.search(rf"\b{re.escape(var1)}\b", line):
                            if not re.search(rf"\b{re.escape(var2)}\b", line):
                                wrong_var = var1

                        if wrong_var:
                            return {
                                "allowed": False,
                                "reason": (
                                    f"Semantic variable swap detected: In '{context}' context, "
                                    f"'{wrong_var}' is used but '{must_use}' is required. "
                                    f"{rule.get('reason', '')}"
                                ),
                                "severity": "high",
                                "category": "variable_semantics_violation",
                                "context": context,
                                "wrong_variable": wrong_var,
                                "required_variable": must_use,
                                "contract_name": contract.get("name", ""),
                            }

        return None


# Singleton instances keyed by project root
_checkers: dict[str, VariableSemanticsChecker] = {}


def get_variable_semantics_checker(project_root: Path | str | None = None) -> VariableSemanticsChecker:
    """Get or create checker instance for given project root."""
    if project_root is None:
        project_root = Path(".")
    else:
        project_root = Path(project_root)

    root_key = str(project_root.resolve())
    global _checkers

    if root_key not in _checkers:
        checker = VariableSemanticsChecker(project_root=project_root)
        checker.load_yaml_contracts()
        _checkers[root_key] = checker

    return _checkers[root_key]


def _find_project_root_for_file(file_path: str) -> Path:
    """Find the likely project root for a given file.

    Looks for common project markers like .git, pyproject.toml, etc.
    """
    file_path = Path(file_path).resolve()

    # Walk up the directory tree looking for project markers
    current = file_path.parent
    for _ in range(10):  # Max 10 levels up
        markers = ['.git', 'pyproject.toml', 'setup.py', 'setup.cfg',
                   'Cargo.toml', 'package.json', '.contracts.yaml']
        if any((current / m).exists() for m in markers):
            return current
        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    # Fallback: return the directory containing the file
    return file_path.parent


def check_variable_semantics(
    file_path: str,
    old_string: str,
    new_string: str,
    source_content: str | None = None
) -> CheckResult:
    """Check for semantic variable swap violations.

    Public entry point for variable semantics checking.

    Args:
        file_path: Path to file being edited
        old_string: Content being replaced
        new_string: New content
        source_content: Full file content (optional)

    Returns:
        Blocking response dict if swap detected, None otherwise
    """
    # Dynamically find project root based on file being edited
    project_root = _find_project_root_for_file(file_path)
    checker = get_variable_semantics_checker(project_root)
    return checker.check_for_semantic_swap(file_path, old_string, new_string, source_content)

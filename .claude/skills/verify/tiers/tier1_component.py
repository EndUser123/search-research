#!/usr/bin/env python3
"""
Tier 1: Component Tests

Runs unit tests for the target component using pytest.
"""

import subprocess
from typing import Any, Dict


class Tier1Component:
    """Tier 1: Component test runner."""

    def run_tests(self, target_type: str, target_name: str) -> Dict[str, Any]:
        """
        Run component tests (pytest) for target.

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target

        Returns:
            Dict with status (pass/fail/skip), evidence, command
        """
        # Build pytest command based on target type
        if target_type == "skill":
            test_path = f".claude/skills/{target_name}/tests/"
        elif target_type == "hook":
            test_path = f".claude/hooks/tests/test_{target_name}.py"
        elif target_type == "feature":
            test_path = f"tests/ -k {target_name}"
        elif target_type == "code":
            # For code files, look for tests in tests/
            test_path = f"tests/ -k {target_name.replace('.py', '')}"
        else:
            return {
                "status": "skip",
                "evidence": f"Unknown target type: {target_type}",
                "command": ""
            }

        command = f"pytest {test_path} -v"

        try:
            # Run pytest
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            evidence = result.stdout.strip()

            if result.returncode == 0:
                return {
                    "status": "pass",
                    "evidence": evidence,
                    "command": command
                }
            else:
                return {
                    "status": "fail",
                    "evidence": evidence,
                    "command": command
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "fail",
                "evidence": "Test execution timed out after 30s",
                "command": command
            }
        except Exception as e:
            # Check if tests directory exists
            if "No such file or directory" in str(e):
                return {
                    "status": "skip",
                    "evidence": f"No tests found for {target_type}:{target_name}",
                    "command": command
                }

            return {
                "status": "fail",
                "evidence": f"Test execution error: {e}",
                "command": command
            }

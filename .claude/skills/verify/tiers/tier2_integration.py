#!/usr/bin/env python3
"""
Tier 2: Integration Check

Verifies hook/router integration works correctly.
"""

import subprocess
from pathlib import Path
from typing import Any

# Import deep lens verifier for deep analysis (when enabled)
from .deep_lens_verifier import DeepLensVerifier


class Tier2Integration:
    """Tier 2: Integration verification."""

    def __init__(self):
        """Initialize with deep lens verifier instance."""
        self.deep_lens_verifier = DeepLensVerifier()

    def check_integration(
        self, target_type: str, target_name: str, deep_lens: bool = False
    ) -> dict[str, Any]:
        """
        Check integration for target.

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target
            deep_lens: Enable 6-lens deep analysis (TASK-003 integration)

        Returns:
            Dict with status (pass/fail/skip), evidence
        """
        # For skills, check if skill exists
        if target_type == "skill":
            skill_path = Path(f"P:/.claude/skills/{target_name}/SKILL.md")
            if skill_path.exists():
                result = {
                    "status": "pass",
                    "evidence": f"Skill file exists: {skill_path}",
                    "checks": {"skill_file": "✓"},
                }

                # Run deep lens analysis if enabled
                if deep_lens:
                    lens_results = self._run_deep_lens_analysis(skill_path)
                    result["deep_lens"] = lens_results

                return result
            else:
                return {
                    "status": "fail",
                    "evidence": f"Skill file not found: {skill_path}",
                    "checks": {"skill_file": "✗"},
                }

        # For hooks, check hook registration and router
        elif target_type == "hook":
            return self._check_hook_integration(target_name, deep_lens=deep_lens)

        # For features and code, skip Tier 2 (no hook integration)
        else:
            return {
                "status": "skip",
                "evidence": f"Tier 2 not applicable for {target_type}",
                "checks": {},
            }

    def _run_deep_lens_analysis(self, target_path: Path) -> dict[str, Any]:
        """
        Run 6-lens deep analysis on target code.

        Args:
            target_path: Path to the file to analyze

        Returns:
            Dict with lens results from all 6 lenses
        """
        try:
            code_content = target_path.read_text()

            context = {"file_path": str(target_path), "file_name": target_path.name}

            return self.deep_lens_verifier.verify(code_content, context)

        except Exception as e:
            return {"status": "error", "error": f"Deep lens analysis failed: {e}", "lenses": {}}

    def check_hook_chain(self, hook_name: str) -> dict[str, Any]:
        """
        Check if hook chain executes without exceptions.

        Args:
            hook_name: Name of hook file

        Returns:
            Dict with status and evidence
        """
        # Find hook file
        hook_file = self._find_hook_file(hook_name)

        if not hook_file:
            return {"status": "fail", "evidence": f"Hook file not found: {hook_name}", "checks": {}}

        # Try to execute hook with test input
        try:
            test_input = '{"tool_name": "Test", "tool_input": {}}'

            result = subprocess.run(
                f"echo '{test_input}' | python {hook_file}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return {
                    "status": "pass",
                    "evidence": result.stdout.strip(),
                    "checks": {"hook_execution": "✓"},
                }
            else:
                return {
                    "status": "fail",
                    "evidence": result.stderr.strip() or result.stdout.strip(),
                    "checks": {"hook_execution": "✗"},
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "fail",
                "evidence": "Hook execution timed out",
                "checks": {"hook_execution": "✗"},
            }
        except Exception as e:
            return {
                "status": "fail",
                "evidence": f"Hook execution error: {e}",
                "checks": {"hook_execution": "✗"},
            }

    def _check_hook_integration(self, hook_name: str, deep_lens: bool = False) -> dict[str, Any]:
        """Internal: Check hook integration details."""
        hook_file = self._find_hook_file(hook_name)

        if not hook_file:
            return {
                "status": "fail",
                "evidence": f"Hook file not found: *{hook_name}*.py",
                "checks": {"hook_file": "✗"},
            }

        # Check if hook is registered in router
        checks = {"hook_file": "✓"}

        # Look for router files
        hooks_dir = Path("P:/.claude/hooks")
        routers = list(hooks_dir.glob("*_router.py"))

        registered = False
        for router in routers:
            try:
                router_content = router.read_text()
                if hook_name in router_content:
                    registered = True
                    checks["router_registration"] = "✓"
                    break
            except Exception:
                pass

        if not registered:
            checks["router_registration"] = "⚠ (may be direct registration)"

        result = {"status": "pass", "evidence": f"Hook file found: {hook_file}", "checks": checks}

        # Run deep lens analysis if enabled
        if deep_lens:
            lens_results = self._run_deep_lens_analysis(Path(hook_file))
            result["deep_lens"] = lens_results

        return result

    def _find_hook_file(self, hook_name: str) -> str:
        """Find hook file by name pattern."""
        hooks_dir = Path("P:/.claude/hooks")

        # Try exact match
        exact = hooks_dir / f"{hook_name}.py"
        if exact.exists():
            return str(exact)

        # Try pattern match
        matches = list(hooks_dir.glob(f"*{hook_name}*.py"))
        if matches:
            return str(matches[0])

        return None

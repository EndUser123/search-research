#!/usr/bin/env python3
"""
Integration Verifier Hook
=========================

PostToolUse hook that automatically verifies skill integration claims
in SKILL.md files to prevent "aspirational documentation" anti-pattern.

Problem: Documentation often claims integrations that don't actually exist.
Solution: Automatically verify that "suggest:" targets exist and reciprocate.

Architecture:
1. Triggers on Write/Edit operations for SKILL.md files
2. Parses YAML frontmatter to extract "suggest:" targets
3. Verifies each target skill exists and reciprocates the integration
4. Returns warnings via additionalContext for integration gaps

Based on plan-20260306-skill-integration-verification.md Task 1.1.
Implementing T-001 from approved plan.
"""

import re
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook


class IntegrationVerifier(PostToolUseHook):
    """
    Verifies skill integration claims match implementation reality.

    Prevents aspirational documentation by checking:
    - Each "suggest:" target skill exists (has SKILL.md file)
    - Each target skill reciprocates the suggestion
    """

    env_var = "INTEGRATION_VERIFIER_ENABLED"
    default_enabled = True
    tool_matcher = {"Write", "Edit"}

    def __init__(self):
        super().__init__()
        # Check multiple skills directories:
        # 1. System/framework skills (P: drive)
        # 2. User skills (home directory)
        self.skills_dirs = [
            Path(__file__).resolve().parent.parent.parent / "skills",  # P:\.claude\skills
            Path.home() / ".claude" / "skills",  # ~/.claude/skills (user skills)
        ]

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Verify skill integration claims.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool

        Returns:
            Dict with verification results. May include injection for integration gaps.
        """
        result = {
            "passed": True,
            "injection": None,
            "verified_integrations": [],
            "missing_integrations": [],
            "one_way_integrations": [],
        }

        # Extract file path
        file_path = self._extract_file_path(tool_input, tool_response)
        if not file_path:
            return result

        # Skip non-SKILL.md files
        if not file_path.endswith("SKILL.md"):
            return result

        # Read file content
        try:
            content = Path(file_path).read_text()
        except Exception:
            # Can't read file - skip verification (silent - no stderr per hook policy)
            return result

        # Extract skill name from file path
        skill_name = self._extract_skill_name(file_path)
        if not skill_name:
            return result

        # Parse suggest: targets
        suggested_targets = self._extract_suggest_targets(content)
        if not suggested_targets:
            # No suggest: field - nothing to verify
            return result

        # Verify each suggested target
        warnings = []
        for target in suggested_targets:
            target = target.strip()
            if not target.startswith("/"):
                continue

            target_skill_name = target.lstrip("/")

            # Check all skills directories for the target
            target_file = None
            found_location = None
            for skills_dir in self.skills_dirs:
                candidate = skills_dir / target_skill_name / "SKILL.md"
                if candidate.exists():
                    target_file = candidate
                    found_location = skills_dir
                    break

            # Check if target skill exists
            if not target_file:
                result["missing_integrations"].append(
                    {"target": target, "reason": "Target skill does not exist"}
                )
                warnings.append(
                    f"❌ MISSING: {target} skill does not exist\n"
                    f"   {skill_name} suggests {target}, but there is no {target_skill_name}/SKILL.md file in any skills directory"
                )
                continue

            # Check if target skill reciprocates
            try:
                target_content = target_file.read_text()
                if not self._reciprocates(target_content, skill_name):
                    result["one_way_integrations"].append(
                        {"target": target, "reason": "Target does not reciprocate"}
                    )
                    warnings.append(
                        f"⚠️  ONE-WAY: {skill_name} → {target}\n"
                        f"   {skill_name} suggests {target}, but {target} does not mention {skill_name}"
                    )
                    continue

                # Reciprocation verified
                result["verified_integrations"].append({"target": target, "reciprocates": True})
            except Exception:
                # Can't read target file - skip this verification (silent - no stderr per hook policy)
                continue

        # Generate injection if any gaps found
        if warnings:
            # Use visual formatter for better presentation
            try:
                # Add hooks to path for import
                import sys

                hooks_dir = Path(__file__).resolve().parent.parent
                if str(hooks_dir) not in sys.path:
                    sys.path.insert(0, str(hooks_dir))

                from __lib.verification_visualizer import VerificationVisualizer

                visualizer = VerificationVisualizer()

                # Format with visual formatter
                missing = [item["target"] for item in result["missing_integrations"]]
                one_way = [item["target"] for item in result["one_way_integrations"]]

                result["injection"] = visualizer.format_integration_warning(
                    skill_name=skill_name,
                    missing_targets=missing,
                    one_way_targets=one_way if one_way else None,
                )
            except ImportError:
                # Fallback to original formatting
                result["injection"] = (
                    "⚠️  INTEGRATION VERIFICATION WARNING\n\n"
                    "Skill integration claims don't match implementation reality:\n\n"
                    + "\n\n".join(warnings)
                    + f"\n\nFix: Either implement the integrations or remove them from {skill_name}/SKILL.md"
                )

        return result

    def _extract_file_path(
        self, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> str | None:
        """Extract file path from tool input/response."""
        if isinstance(tool_input, dict):
            path = (
                tool_input.get("file_path")
                or tool_input.get("path")
                or tool_input.get("filePath")
                or tool_input.get("target")
            )
            if path:
                return path

        # Try other fields
        if isinstance(tool_response, dict):
            return tool_response.get("file_path") or tool_response.get("path")

        return None

    def _extract_skill_name(self, file_path: str) -> str | None:
        """Extract skill name from file path (e.g., 'code' from '.../skills/code/SKILL.md')."""
        path = Path(file_path)
        if path.parent.name == "skills":
            return path.parent.name
        if path.parent.parent.name == "skills":
            return path.parent.name
        return None

    def _extract_suggest_targets(self, content: str) -> list[str]:
        """
        Extract suggest: targets from SKILL.md content.

        Tries YAML parsing first (on frontmatter only), falls back to regex extraction.
        """
        # Extract YAML frontmatter only (content between --- delimiters)
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
        else:
            frontmatter = content  # Fall back to full content if no frontmatter

        # Try YAML parsing first
        try:
            import yaml

            data = yaml.safe_load(frontmatter)
            if isinstance(data, dict) and "suggest" in data:
                suggest = data["suggest"]
                if isinstance(suggest, list):
                    return suggest
        except Exception:
            # YAML parsing failed, fall back to regex
            pass

        # Regex fallback: extract suggest: section
        # Matches lines like "  - /target-skill" after "suggest:"
        suggest_pattern = re.compile(r"^suggest:\s*\n((?:\s+-\s+/[^\n]+\n?)+)", re.MULTILINE)
        match = suggest_pattern.search(content)
        if match:
            # Extract all - /target entries
            target_pattern = re.compile(r"-\s+(/[^\s]+)")
            targets = target_pattern.findall(match.group(1))
            return targets

        return []

    def _reciprocates(self, target_content: str, skill_name: str) -> bool:
        """
        Check if target skill reciprocates the integration.

        A target reciprocates if it mentions skill_name in its suggest: section.
        """
        # Extract YAML frontmatter only (content between --- delimiters)
        frontmatter_match = re.match(r"^---\n(.*?)\n---", target_content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
        else:
            frontmatter = target_content  # Fall back to full content if no frontmatter

        # Try YAML parsing first
        try:
            import yaml

            data = yaml.safe_load(frontmatter)
            if isinstance(data, dict) and "suggest" in data:
                suggest = data["suggest"]
                if isinstance(suggest, list):
                    # Check if any entry mentions skill_name
                    for entry in suggest:
                        if f"/{skill_name}" in str(entry):
                            return True
        except Exception:
            # YAML parsing failed, fall back to regex
            pass

        # Regex fallback: search for /skill-name in suggest: section
        suggest_section = re.search(
            r"^suggest:.*?(?=^[a-z]+:|\Z)", target_content, re.MULTILINE | re.DOTALL
        )
        if suggest_section:
            return f"/{skill_name}" in suggest_section.group(0)

        return False

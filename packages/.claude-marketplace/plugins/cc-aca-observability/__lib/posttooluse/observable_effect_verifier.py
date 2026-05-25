#!/usr/bin/env python3
"""
Observable Effect Verifier Hook
================================

PostToolUse hook that verifies expected side effects from code changes.

Detects patterns in code (e.g., FileHandler for logging) and verifies that
the expected side effects actually occur (e.g., log files are created).

Architecture:
1. Reads file content after Edit/Write operations
2. Runs all registered effect verifiers
3. Returns warning via additionalContext for failed effects

Based on plan-20260304-observable-effect-verification.md Task 3.
Implementing T-003 from approved plan.
"""

from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook

# Import effect verifiers
from posttooluse.effects.logging_effect import LoggingEffectVerifier


class ObservableEffectVerifier(PostToolUseHook):
    """Verifies expected side effects from code changes."""

    env_var = "SEV_ENABLED"
    default_enabled = True
    tool_matcher = {"Edit", "Write"}

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent

        # Register effect verifiers
        self.verifiers = [
            LoggingEffectVerifier(enabled=True),
        ]

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Verify expected effects from code modifications.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool

        Returns:
            Dict with verification results. May include injection for failed effects.
        """
        result = {
            "passed": True,
            "injection": None,
            "verified_effects": [],
            "failed_effects": [],
        }

        # Extract file path
        file_path = self._extract_file_path(tool_input, tool_response)
        if not file_path:
            return result

        # Read file content
        try:
            content = Path(file_path).read_text()
        except Exception:
            # Can't read file - skip verification
            return result

        # Run all registered verifiers
        for verifier in self.verifiers:
            if not verifier.is_enabled():
                continue

            # Check if verifier should handle this file
            if not verifier.detect(tool_name, tool_input, tool_response):
                continue

            # Extract effect configuration
            effect_config = verifier.detect_config(content, file_path)
            if not effect_config:
                continue

            # Verify the effect
            verification_result = verifier.verify_config(effect_config, file_path)

            # Track results
            if verification_result.is_valid():
                result["verified_effects"].append({
                    "effect_type": verification_result.effect_type,
                    "config": effect_config,
                })
            else:
                result["failed_effects"].append({
                    "effect_type": verification_result.effect_type,
                    "config": effect_config,
                    "warning": verification_result.warning_message,
                    "suggestion": verification_result.suggestion,
                })

        # Generate injection if any effects failed
        if result["failed_effects"]:
            # Use visual formatter for better presentation
            try:
                # Add hooks to path for import
                import sys
                hooks_dir = Path(__file__).resolve().parent.parent
                if str(hooks_dir) not in sys.path:
                    sys.path.insert(0, str(hooks_dir))

                from __lib.verification_visualizer import VerificationVisualizer
                visualizer = VerificationVisualizer()

                # Format each failed effect with visual formatter
                warnings = []
                for failure in result["failed_effects"]:
                    warning = visualizer.format_observable_effect_warning(
                        effect_type=failure['effect_type'],
                        expected_effect=str(failure['config']),
                        verification_failed=failure['warning']
                    )
                    warnings.append(warning)

                result["injection"] = "\n\n".join(warnings)
            except ImportError:
                # Fallback to original formatting
                warnings = []
                for failure in result["failed_effects"]:
                    warnings.append(
                        f"⚠️ {failure['effect_type']} effect verification failed:\n"
                        f"   {failure['warning']}\n"
                        f"   Suggestion: {failure['suggestion']}"
                    )

                result["injection"] = "\n\n".join(warnings)

        return result

    def _extract_file_path(
        self,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any]
    ) -> str | None:
        """Extract file path from tool input/response."""
        if isinstance(tool_input, dict):
            path = (
                tool_input.get("file_path") or
                tool_input.get("path") or
                tool_input.get("filePath") or
                tool_input.get("target")
            )
            if path:
                return path

        # Try other fields
        if isinstance(tool_response, dict):
            return tool_response.get("file_path") or tool_response.get("path")

        return None

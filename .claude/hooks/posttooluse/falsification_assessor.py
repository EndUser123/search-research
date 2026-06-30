#!/usr/bin/env python3
from __future__ import annotations

"""
Falsification Assessment Hook
==============================

TWO PROTOCOLS IN ONE HOOK:

1. Falsification Assessment:
   Assesses execution results against expectations to detect mismatches
   that indicate pattern-matching overconfidence.

2. Post-Action Verification:
   Reminds Claude to verify actions succeeded after execution.
   Prevents the "I executed but didn't verify" gap.

PRINCIPLE: Compare expected vs actual outcomes to detect hidden assumptions.
PRINCIPLE: Verify actions worked before assuming success.

Extracted from PostToolUse_falsification_assessor.py for in-process execution.
"""

import re
import sys
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook

# Add hooks directory to path for falsification_orchestrator import
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

try:
    from falsification_orchestrator import get_orchestrator
    _ORCHESTRATOR_AVAILABLE = True
except ImportError:
    # Falsification orchestrator is archived - use minimal fallback
    _ORCHESTRATOR_AVAILABLE = False
    def get_orchestrator():
        return None


class FalsificationAssessor(PostToolUseHook):
    """
    Assesses outcomes against expectations and provides verification reminders.
    """

    env_var = "FALSIFICATION_ASSESSOR_ENABLED"
    default_enabled = True

    # Tools to assess
    ASSESSED_TOOLS = {"Edit", "Write", "Bash", "Read", "Grep"}

    # Signs of unexpected outcomes
    UNEXPECTED_INDICATORS = {
        "error": ["error", "failed", "exception", "traceback", "errno"],
        "not_found": ["not found", "no such file", "does not exist", "cannot find"],
        "permission": ["permission denied", "access denied", "unauthorized"],
        "empty": ["empty result", "no matches", "0 items", "[]"],
        "unexpected": ["unexpected", "invalid", "malformed"],
    }

    # State-changing tools that require post-action verification
    VERIFICATION_REQUIRED_TOOLS = {
        "Edit": "Read the file to confirm changes are present",
        "Write": "Read the file to confirm content was written correctly",
        "Bash": "Verify the output matches your intent (check exit code, stdout)",
    }

    # Whole-token error patterns for the post-action verification trigger.
    # Pre-lowered so _indicator_match can run against lowercased output directly.
    ERROR_PATTERNS = ["error", "exception", "failed", "traceback"]

    def __init__(self):
        super().__init__()
        self.orchestrator = get_orchestrator() if _ORCHESTRATOR_AVAILABLE else None

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Assess tool outcome against expectations.

        Returns dict with assessment results or verification reminder.
        """
        result = {
            "passed": True,
            "injection": None,
        }

        # Validate inputs - handle None tool_input gracefully
        if tool_input is None:
            tool_input = {}

        # Only assess specific tools
        if tool_name not in self.ASSESSED_TOOLS:
            return result

        # Extract expected outcome
        expected = self._extract_expected_outcome(tool_name, tool_input)
        actual = self._format_actual_outcome(tool_response)

        # Check for unexpected outcome
        unexpected = self._detect_unexpected_outcome(tool_response)

        # Record expectation for tracking (if orchestrator available)
        if self.orchestrator is not None:
            try:
                expectation_id = self.orchestrator.record_expectation(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    expected_outcome=expected
                )
            except Exception:
                expectation_id = None
        else:
            expectation_id = None

        if unexpected:
            # Mismatch detected
            indicator_type, _ = unexpected

            # Generate assessment message
            assessment_message = self._generate_assessment_message(
                tool_name, expected, actual, indicator_type
            )

            # Record the assessment (if orchestrator available)
            if self.orchestrator is not None:
                try:
                    self.orchestrator.assess_outcome(
                        expectation_id=expectation_id,
                        actual_outcome=actual,
                        assessment="mismatched"
                    )
                except Exception:
                    pass  # Don't fail hook if orchestrator fails

            result["injection"] = assessment_message
            result["falsification_assessment"] = {
                "expectation_id": expectation_id,
                "expected": expected,
                "actual": actual,
                "indicator_type": indicator_type,
                "assessment": "mismatched"
            }
            return result
        else:
            # Outcome matched expectations
            if self.orchestrator is not None:
                try:
                    self.orchestrator.assess_outcome(
                        expectation_id=expectation_id,
                        actual_outcome=actual,
                        assessment="matched"
                    )
                except Exception:
                    pass  # Don't fail hook if orchestrator fails

            # POST-ACTION VERIFICATION: Remind to verify successful operations
            exit_code = tool_response.get('exit_code', 0) if tool_response else 0
            if self._should_show_verification(tool_name, tool_response, exit_code):
                verification_message = self._generate_verification_reminder(tool_name, tool_input)
                result["injection"] = verification_message
                result["post_action_verification"] = {
                    "tool_name": tool_name,
                    "reminder": verification_message,
                    "assessment": "matched"
                }
                return result

        return result

    def _detect_unexpected_outcome(self, tool_response: dict[str, Any]) -> tuple[str, str] | None:
        """Detect if the tool output indicates an unexpected outcome."""
        if not tool_response:
            return None

        if isinstance(tool_response, dict):
            # Collect all relevant fields into list for single join
            parts = [
                str(tool_response.get("output", "")),
                str(tool_response.get("result", "")),
                str(tool_response.get("stderr", "")),
                str(tool_response.get("error", "")),
            ]
            output_content = " ".join(parts)
        else:
            output_content = str(tool_response)

        output_lower = output_content.lower()

        for indicator_type, patterns in self.UNEXPECTED_INDICATORS.items():
            matched = self._indicator_match(output_lower, patterns)
            if matched:
                return (indicator_type, matched)

        return None

    @staticmethod
    def _indicator_match(text_lower: str, patterns: list[str]) -> str | None:
        """Return the first pattern present as a whole token, else None.

        Lookaround (?<!\\w)...(?!\\w) instead of \\b: \\b requires a word char
        at the pattern edge, so non-word-edge patterns like '[]' silently fail
        to match. Underscore is a word char, so 'error_attribution_hook.py'
        does NOT match 'error'; 'an error occurred' does. A literal 'error.py'
        filename still matches (dot is non-word) — accepted residual, tested
        as xfail. Shared by _detect_unexpected_outcome and
        _should_show_verification so the two paths cannot drift again.
        """
        for pattern in patterns:
            if re.search(rf"(?<!\w){re.escape(pattern)}(?!\w)", text_lower):
                return pattern
        return None

    def _extract_expected_outcome(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Generate a description of what was expected from this operation."""
        # Handle None tool_input gracefully (could be missing in edge cases)
        if tool_input is None:
            return f"{tool_name} operation should succeed"

        if tool_name == "Edit":
            file_path = tool_input.get("file_path", tool_input.get("path", "unknown"))
            return f"Edit to {file_path} should succeed cleanly"
        elif tool_name == "Write":
            file_path = tool_input.get("file_path", tool_input.get("path", "unknown"))
            return f"Write to {file_path} should create/overwrite file successfully"
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            return f"Command '{command[:50]}...' should execute successfully"
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", tool_input.get("path", "unknown"))
            return f"Read of {file_path} should return file contents"
        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            return f"Grep for '{pattern}' should find matches"
        return f"{tool_name} operation should succeed"

    def _format_actual_outcome(self, tool_response: dict[str, Any]) -> str:
        """Format the actual outcome for assessment."""
        if isinstance(tool_response, dict):
            if "error" in tool_response:
                return f"Error: {tool_response['error']}"
            if "stderr" in tool_response and tool_response["stderr"]:
                return f"Stderr: {tool_response['stderr'][:200]}"
            if "result" in tool_response:
                return str(tool_response["result"])[:200]
            if "output" in tool_response:
                return str(tool_response["output"])[:200]
        return str(tool_response)[:200]

    def _generate_assessment_message(
        self, tool_name: str, expected: str, actual: str, unexpected_type: str
    ) -> str:
        """Generate an assessment message when outcomes don't match."""

        base = f"""🔄 FALSIFICATION ASSESSMENT: Unexpected Outcome

**Tool:** {tool_name}
**Expected:** {expected}
**Actual:** {actual}

**Learning:** This indicates a hidden assumption was wrong.
- What assumption led to this error?
- What should have been checked first?

**Recommendation:** Before retrying, verify:
1. Preconditions (file exists, permissions, correct path)
2. Dependencies (imports, modules, commands available)
3. Context (is this the right approach?)
"""
        return base

    def _should_show_verification(self, tool_name: str, tool_response: dict[str, Any] | None = None, exit_code: int | None = None) -> bool:
        """Determine if verification reminder should be shown."""
        # Extract exit_code from tool_response if not provided
        if exit_code is None and tool_response:
            exit_code = tool_response.get("exit_code", 0)
        elif exit_code is None:
            exit_code = 0

        # 1. If tool_name not in VERIFICATION_REQUIRED_TOOLS -> return False
        if tool_name not in self.VERIFICATION_REQUIRED_TOOLS:
            return False

        # 2. If exit_code != 0 -> return True
        if exit_code != 0:
            return True

        # 3. If tool_response contains error patterns -> return True
        if tool_response:
            parts = []
            # Check all relevant fields for error patterns
            for key in ("output", "result", "stderr", "error"):
                if key in tool_response and tool_response[key]:
                    parts.append(str(tool_response[key]))
            output_content = " ".join(parts)

            # ponytail: shared whole-token matcher — bare substring 'error' in
            # output fired VERIFICATION on benign paths like
            # error_attribution_hook.py. Same defect shape as
            # _detect_unexpected_outcome; one helper so they cannot diverge.
            if self._indicator_match(output_content.lower(), self.ERROR_PATTERNS):
                return True

        # 4. Otherwise -> return False
        return False

    def _generate_verification_reminder(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Generate a post-action verification reminder."""

        if tool_name == "Edit":
            file_path = tool_input.get("file_path", tool_input.get("path", "the file"))
            return f"""✓ Edit completed.

**VERIFICATION REQUIRED:**
Read the file to confirm your changes are present:
`Read "{file_path}"`

Check that:
- The exact changes you made are in the file
- No unintended modifications occurred
- The file structure is intact
"""

        elif tool_name == "Write":
            file_path = tool_input.get("file_path", tool_input.get("path", "the file"))
            return f"""✓ Write completed.

**VERIFICATION REQUIRED:**
Read the file to confirm content was written correctly:
`Read "{file_path}"`

Check that:
- The full content is present
- Encoding is correct (no corruption)
- File is in the expected location
"""

        elif tool_name == "Bash":
            return """✓ Bash command executed.

**VERIFICATION REQUIRED:**
Verify the output matches your intent:
- Check exit code (0 = success)
- Read stdout/stderr for errors
- For file operations: verify file state changed
"""

        return f"✓ {tool_name} completed. Verify the result."

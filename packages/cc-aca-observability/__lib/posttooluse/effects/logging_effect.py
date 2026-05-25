#!/usr/bin/env python3
"""
Logging Effect Verifier
=======================

Verifies that logging configuration produces actual log files.

Detects FileHandler patterns and verifies that:
1. Log file exists after code runs
2. Log file has recent content (<1 hour old)

Based on plan-20260304-observable-effect-verification.md Task 2.
"""

import re
import time
from pathlib import Path
from typing import Any

from .base_effect import BaseEffectVerifier, EffectVerificationResult


class LoggingEffectVerifier(BaseEffectVerifier):
    """Verifies logging configuration produces actual log files."""

    # TIGHT PATTERNS - Only exact patterns used in production
    FILE_HANDLER_PATTERNS = [
        # FileHandler with string path
        re.compile(r'FileHandler\(["\']([^"\']+)["\']\)'),
        # Variant with Path object
        re.compile(r'FileHandler\(Path\(["\']([^"\']+)["\']\)\)'),
    ]

    SKIP_PATTERNS = [
        # Conditional logging - user explicitly disabled
        re.compile(r"if\s+.*:\s*.*log", re.IGNORECASE),
        # Environment-based paths - dynamic configuration
        re.compile(r'os\.getenv\(["\']LOG', re.IGNORECASE),
        # Commented out examples
        re.compile(r"#.*FileHandler", re.IGNORECASE),
    ]

    def __init__(self, enabled: bool = True):
        """Initialize logging effect verifier.

        Args:
            enabled: Whether this verifier is active
        """
        super().__init__(enabled)

    @classmethod
    def detect_config(cls, content: str, file_path: str) -> dict[str, Any] | None:
        """Detect if logging effect exists in the file.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            Effect configuration dict if detected, None otherwise
        """
        # Skip non-code files
        if not file_path.endswith(".py"):
            return None

        # Check skip patterns first
        for pattern in cls.SKIP_PATTERNS:
            if pattern.search(content):
                return None

        # Detect FileHandler patterns
        for pattern in cls.FILE_HANDLER_PATTERNS:
            matches = pattern.finditer(content)
            for match in matches:
                log_path = match.group(1)
                return {
                    "effect_type": "logging",
                    "log_path": log_path,
                    "pattern_matched": match.group(0),
                    "line_number": content[: match.start()].count("\n") + 1,
                }

        return None

    @classmethod
    def verify_config(
        cls, effect_config: dict[str, Any], file_path: str
    ) -> EffectVerificationResult:
        """Verify that log file is created and configured correctly.

        Args:
            effect_config: Configuration extracted from detect_config()
            file_path: Path to file being verified

        Returns:
            EffectVerificationResult with verification outcome
        """
        log_path = effect_config.get("log_path", "")

        if not log_path:
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message="Logging configuration detected but log path not found",
                suggestion="Ensure FileHandler has explicit path argument",
            )

        # Resolve relative path
        hooks_dir = Path(file_path).parent
        full_log_path = hooks_dir / log_path

        # Check if log file exists
        if not full_log_path.exists():
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message=f"Logging configured for {log_path} but file doesn't exist",
                suggestion=f"1. Run code that writes logs\n2. Verify file created at {full_log_path}\n3. Check structlog.configure() includes FileHandler",
            )

        # Check file has recent content (modified in last hour)
        age_seconds = time.time() - full_log_path.stat().st_mtime
        if age_seconds > 3600:
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message=f"Log file exists but stale (last modified {age_seconds // 60} minutes ago)",
                suggestion="Run code that writes logs to verify logging works",
            )

        # All checks passed
        return EffectVerificationResult(
            effect_type="logging",
            detected=True,
            verified=True,
            matched_config=effect_config,
            warning_message="",
            suggestion="",
        )

    def detect(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> bool:
        """Detect if this verifier should apply to the given tool execution.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool

        Returns:
            True if this verifier should handle this tool execution
        """
        # Only check Write and Edit operations
        if tool_name not in ("Write", "Edit"):
            return False

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return False

        # Only check Python files
        if not file_path.endswith(".py"):
            return False

        # Read file content to check for logging patterns
        try:
            content = Path(file_path).read_text()
        except Exception:
            return False

        # Use classmethod for detection
        return self.detect_config(content, file_path) is not None

    def verify(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
        config: dict[str, Any],
    ) -> EffectVerificationResult:
        """Verify that the tool execution produced the expected effect.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool
            config: Configuration for effect verification

        Returns:
            EffectVerificationResult with detection and verification outcome
        """
        file_path = tool_input.get("file_path", "")

        # Read file content to extract logging configuration
        try:
            content = Path(file_path).read_text()
        except Exception as e:
            return EffectVerificationResult(
                effect_type="logging",
                detected=False,
                verified=False,
                matched_config={},
                warning_message=f"Failed to read file: {e}",
                suggestion="Ensure file is readable",
            )

        # Extract effect configuration
        effect_config = self.detect_config(content, file_path)

        if not effect_config:
            return EffectVerificationResult(
                effect_type="logging",
                detected=False,
                verified=False,
                matched_config={},
                warning_message="No FileHandler pattern detected",
                suggestion="",
            )

        # Verify the effect
        return self.verify_config(effect_config, file_path)

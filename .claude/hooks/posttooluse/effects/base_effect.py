#!/usr/bin/env python3
"""
Base Effect Verifier Class
==========================

Abstract base class for all effect verifiers.

Effect verifiers detect and verify expected side effects from tool execution.
For example, a Write tool should create/modify a file, and an Edit tool should
produce changes that match the edit intent.

Based on scanner pattern from:
P:\\.claude\\hooks\\scanners\\base_scanner.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EffectVerificationResult:
    """Result from an effect verification."""
    effect_type: str  # Type of effect (e.g., "file_write", "file_edit", "git_commit")
    detected: bool  # Whether the effect was detected
    verified: bool  # Whether the effect matches expected behavior
    matched_config: dict[str, Any]  # Configuration that matched this effect
    warning_message: str = ""  # Warning if detection/verification fails
    suggestion: str = ""  # Suggestion for fixing issues

    def is_valid(self) -> bool:
        """Returns True if effect was both detected and verified."""
        return self.detected and self.verified

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "effect_type": self.effect_type,
            "detected": self.detected,
            "verified": self.verified,
            "matched_config": self.matched_config,
            "warning_message": self.warning_message,
            "suggestion": self.suggestion,
        }


class BaseEffectVerifier(ABC):
    """Abstract base class for all effect verifiers."""

    def __init__(self, enabled: bool = True):
        """
        Initialize effect verifier.

        Args:
            enabled: Whether this verifier is active
        """
        self.enabled = enabled
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Get verifier name."""
        return self._name

    @abstractmethod
    def detect(self, tool_name: str, tool_input: dict, tool_response: dict) -> bool:
        """
        Detect if this verifier should apply to the given tool execution.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool

        Returns:
            True if this verifier should handle this tool execution
        """
        pass

    @abstractmethod
    def verify(self, tool_name: str, tool_input: dict, tool_response: dict, config: dict) -> EffectVerificationResult:
        """
        Verify that the tool execution produced the expected effect.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool
            config: Configuration for effect verification

        Returns:
            EffectVerificationResult with detection and verification outcome
        """
        pass

    def is_enabled(self) -> bool:
        """Check if verifier is enabled."""
        return self.enabled

    def enable(self) -> None:
        """Enable this verifier."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this verifier."""
        self.enabled = False

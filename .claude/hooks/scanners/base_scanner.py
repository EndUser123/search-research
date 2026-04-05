#!/usr/bin/env python3
"""
Base Scanner Class
==================

Abstract base class for all hook scanners.

Based on LLM Guard scanner pattern:
https://github.com/protectai/llm-guard
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ScanStatus(Enum):
    """Scan result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"  # Scanner not applicable or disabled


@dataclass
class ScanResult:
    """Result from a scanner validation."""
    status: ScanStatus
    scanner_name: str
    matched_text: str = ""
    reason: str = ""
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    suggestion: str = ""

    def is_valid(self) -> bool:
        """Returns True if scan passed."""
        return self.status in (ScanStatus.PASS, ScanStatus.SKIP)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "scanner_name": self.scanner_name,
            "matched_text": self.matched_text,
            "reason": self.reason,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class BaseScanner(ABC):
    """Abstract base class for all scanners."""

    def __init__(self, enabled: bool = True):
        """
        Initialize scanner.

        Args:
            enabled: Whether this scanner is active
        """
        self.enabled = enabled
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Get scanner name."""
        return self._name

    @abstractmethod
    def scan(self, text: str, context: dict = None) -> ScanResult:
        """
        Scan text for violations.

        Args:
            text: The text to scan
            context: Optional context (tool use, user prompt, etc.)

        Returns:
            ScanResult with validation outcome
        """
        pass

    def is_enabled(self) -> bool:
        """Check if scanner is enabled."""
        return self.enabled

    def enable(self) -> None:
        """Enable this scanner."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this scanner."""
        self.enabled = False

"""Base diagnostic checker for yt-fts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Status(Enum):
    """Diagnostic status levels."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    category: str
    status: Status
    message: str
    details: list[str]
    remediation: str | None = None
    auto_fix: Callable[[], Any] | None = None

    def __str__(self) -> str:
        """Format result for display."""
        icon = {
            Status.PASS: "✅",
            Status.WARN: "⚠️ ",
            Status.FAIL: "❌",
            Status.INFO: "ℹ️ ",
        }[self.status]
        return f"{icon} {self.category}: {self.message}"


class DiagnosticChecker:
    """Base class for diagnostic checkers."""

    def __init__(self) -> None:
        """
        Initialize the diagnostic checker.

        Creates an empty list to store diagnostic results.
        """
        self.results: list[DiagnosticResult] = []

    def add_result(
        self,
        category: str,
        status: Status,
        message: str,
        details: list[str] | None = None,
        remediation: str | None = None,
    ) -> None:
        """Add a diagnostic result."""
        self.results.append(
            DiagnosticResult(
                category=category,
                status=status,
                message=message,
                details=details or [],
                remediation=remediation,
            )
        )

    def run(self) -> list[DiagnosticResult]:
        """Run all diagnostic checks. Override in subclass."""
        raise NotImplementedError

    def try_fix(self) -> bool:
        """Attempt to fix issues. Returns True if any fixes were applied."""
        fixed = False
        for result in self.results:
            if result.status in (Status.WARN, Status.FAIL) and result.auto_fix:
                try:
                    result.auto_fix()
                    fixed = True
                except Exception:
                    pass
        return fixed

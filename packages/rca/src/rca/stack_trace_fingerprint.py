"""
Stack Trace Fingerprinting for RCA/Debug Workflow

Extracts precise fingerprints from error messages and stack traces for
instant matching to previous fixes.

A fingerprint captures:
- File path (relative to project root)
- Line number
- Error type
- Function name

This enables: "Error at download_handler.py:127? → Here's the fix that worked last time."
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StackTraceFingerprint:
    """A precise fingerprint of an error location."""

    file_path: str  # Relative to project root, e.g., "src/module/file.py"
    line_number: int
    error_type: str  # e.g., "AttributeError", "ImportError"
    function_name: str = ""  # Optional function context

    @property
    def fingerprint_hash(self) -> str:
        """Deterministic hash for quick lookup."""
        key = f"{self.file_path}:{self.line_number}:{self.error_type}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    @property
    def display_key(self) -> str:
        """Human-readable key for display."""
        func = f"@{self.function_name}" if self.function_name else ""
        return f"{Path(self.file_path).name}:{self.line_number}{func}:{self.error_type}"

    def matches(self, other: StackTraceFingerprint) -> bool:
        """Check if two fingerprints match (exact match)."""
        return (
            self.file_path == other.file_path
            and self.line_number == other.line_number
            and self.error_type == other.error_type
        )

    def similarity_to(self, other: StackTraceFingerprint) -> float:
        """
        Calculate similarity score (0.0 to 1.0) with another fingerprint.

        Scores:
        - 1.0: Exact match (file, line, error type)
        - 0.8: Same file + error type, different line
        - 0.6: Same file, different error type
        - 0.4: Different file, same error type
        - 0.0: No match
        """
        if self.matches(other):
            return 1.0

        score = 0.0

        # Same file and error type (likely related)
        if self.file_path == other.file_path and self.error_type == other.error_type:
            # Closer lines = higher similarity
            line_diff = abs(self.line_number - other.line_number)
            if line_diff <= 5:
                score = 0.8
            elif line_diff <= 20:
                score = 0.7
            else:
                score = 0.6

        # Same file, different error (might be related)
        elif self.file_path == other.file_path:
            score = 0.5

        # Same error type, different file (pattern match)
        elif self.error_type == other.error_type:
            score = 0.3

        return score


@dataclass
class FixRecord:
    """A previously applied fix for a fingerprinted error."""

    fingerprint: StackTraceFingerprint
    fix_description: str
    applied_at: str  # ISO timestamp
    verified: bool = False
    times_seen: int = 1
    last_seen: str = ""

    # Optional context
    error_message: str = ""
    commit_hash: str = ""
    related_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "fingerprint": {
                "file_path": self.fingerprint.file_path,
                "line_number": self.fingerprint.line_number,
                "error_type": self.fingerprint.error_type,
                "function_name": self.fingerprint.function_name,
            },
            "fix_description": self.fix_description,
            "applied_at": self.applied_at,
            "verified": self.verified,
            "times_seen": self.times_seen,
            "last_seen": self.last_seen,
            "error_message": self.error_message,
            "commit_hash": self.commit_hash,
            "related_files": self.related_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FixRecord:
        """Create from dictionary."""
        fp_data = data["fingerprint"]
        fingerprint = StackTraceFingerprint(
            file_path=fp_data["file_path"],
            line_number=fp_data["line_number"],
            error_type=fp_data["error_type"],
            function_name=fp_data.get("function_name", ""),
        )
        return cls(
            fingerprint=fingerprint,
            fix_description=data["fix_description"],
            applied_at=data["applied_at"],
            verified=data.get("verified", False),
            times_seen=data.get("times_seen", 1),
            last_seen=data.get("last_seen", ""),
            error_message=data.get("error_message", ""),
            commit_hash=data.get("commit_hash", ""),
            related_files=data.get("related_files", []),
        )


class FingerprintExtractor:
    """Extracts fingerprints from error messages and stack traces."""

    # Patterns for various error formats
    PATTERNS = [
        # Python traceback: "File \"path\", line N, in function"
        r'\s*File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in (?P<function>\w+))?',
        # Common error format: "path/to/file.py:N: error"
        r"(?P<path>[^:]+\.(?:py|js|ts|rs|go)):(?P<line>\d+):",
        # AttributeError: "module 'X' has no attribute 'Y'"
        r"(?P<path>\w+\.py):(?P<line>\d+):",
        # Import errors
        r"File \"(?P<path>[^\"]+)\", line (?P<line>\d+)",
    ]

    # Project root patterns to strip
    PROJECT_ROOTS = [
        "P:/",
        "P:\\",
        "/home/",
        "/Users/",
        "C:/",
        "C:\\",
    ]

    ERROR_TYPE_PATTERNS = [
        r"^(?P<type>\w+Error):",
        r"^(?P<type>\w+Exception):",
        r"^(?P<type>Traceback)",
    ]

    @classmethod
    def normalize_path(cls, path: str) -> str:
        """Normalize file path to be relative and consistent."""
        # Strip project root
        for root in cls.PROJECT_ROOTS:
            if path.startswith(root):
                path = path[len(root):]
                break

        # Convert backslashes to forward slashes
        path = path.replace("\\", "/")

        # Remove leading ./ if present
        if path.startswith("./"):
            path = path[2:]

        return path

    @classmethod
    def extract_error_type(cls, text: str) -> str:
        """Extract error type from error message."""
        text = text.strip()

        # Common error types
        for err_type in [
            "AttributeError",
            "ImportError",
            "ModuleNotFoundError",
            "TypeError",
            "ValueError",
            "KeyError",
            "IndexError",
            "RuntimeError",
            "NotImplementedError",
            "AssertionError",
            "SyntaxError",
            "IndentationError",
            "NameError",
            "UnboundLocalError",
            "FileNotFoundError",
            "PermissionError",
            "OSError",
            "ConnectionError",
            "TimeoutError",
            "HTTPError",
            "JSONDecodeError",
        ]:
            if err_type in text:
                return err_type

        # Try regex patterns
        for pattern in cls.ERROR_TYPE_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group("type")

        return "Error"

    @classmethod
    def extract_from_error_message(
        cls,
        error_message: str,
        default_file: str = "",
    ) -> list[StackTraceFingerprint]:
        """
        Extract fingerprints from an error message.

        Args:
            error_message: The full error message/stack trace
            default_file: Optional file path if not in error message

        Returns:
            List of fingerprints (most specific first)

        """
        fingerprints = []
        error_type = cls.extract_error_type(error_message)

        # Try each pattern
        for pattern in cls.PATTERNS:
            matches = re.finditer(pattern, error_message)
            for match in matches:
                file_path = cls.normalize_path(match.group("path"))
                line_number = int(match.group("line"))
                # Function group may not exist in all patterns
                function_name = match.groupdict().get("function") or ""

                fp = StackTraceFingerprint(
                    file_path=file_path,
                    line_number=line_number,
                    error_type=error_type,
                    function_name=function_name,
                )
                fingerprints.append(fp)

        # If no file found in error, use default
        if not fingerprints and default_file:
            fingerprints.append(
                StackTraceFingerprint(
                    file_path=cls.normalize_path(default_file),
                    line_number=0,
                    error_type=error_type,
                )
            )

        return fingerprints

    @classmethod
    def extract_from_problem_description(
        cls,
        description: str,
    ) -> StackTraceFingerprint | None:
        """
        Extract best-guess fingerprint from a problem description.

        This handles cases where the user describes a problem without
        providing a full stack trace.

        Args:
            description: User's problem description

        Returns:
            Best-guess fingerprint or None

        """
        # Look for "file.py:123" pattern
        file_line_match = re.search(r"(\w+\.py):(\d+)", description)
        if file_line_match:
            file_path = file_line_match.group(1)
            line_number = int(file_line_match.group(2))
            error_type = cls.extract_error_type(description)

            return StackTraceFingerprint(
                file_path=file_path,
                line_number=line_number,
                error_type=error_type,
            )

        # Look for file mentions without line numbers
        file_match = re.search(r"(\w+\.py)", description)
        if file_match:
            error_type = cls.extract_error_type(description)
            return StackTraceFingerprint(
                file_path=file_match.group(1),
                line_number=0,  # Unknown line
                error_type=error_type,
            )

        # Just extract error type
        error_type = cls.extract_error_type(description)
        if error_type != "Error":
            return StackTraceFingerprint(
                file_path="unknown",
                line_number=0,
                error_type=error_type,
            )

        return None


def fingerprint_from_error(
    error_message: str,
    file_path: str = "",
) -> StackTraceFingerprint | None:
    """
    Convenience function: extract the most specific fingerprint from an error.

    Args:
        error_message: The error message or stack trace
        file_path: Optional file path if not in error message

    Returns:
        The most specific fingerprint, or None if no info found

    """
    fingerprints = FingerprintExtractor.extract_from_error_message(
        error_message,
        default_file=file_path,
    )
    return fingerprints[0] if fingerprints else None


def fingerprint_from_description(description: str) -> StackTraceFingerprint | None:
    """Convenience function: extract fingerprint from problem description."""
    return FingerprintExtractor.extract_from_problem_description(description)


# CLI test function
def _test() -> None:
    """Run built-in tests."""
    print("Stack Trace Fingerprinting Tests")
    print("=" * 60)

    # Test 1: Full stack trace
    traceback1 = """
Traceback (most recent call last):
  File "src/yt_fts/download/download_handler.py", line 127, in get_vtt
    options = yt_dlp_options["format"]
AttributeError: 'NoneType' object has no attribute '__getitem__'
"""
    fps = FingerprintExtractor.extract_from_error_message(traceback1)
    print("Test 1 - Stack trace extraction:")
    print(f"  File: {fps[0].file_path}")
    print(f"  Line: {fps[0].line_number}")
    print(f"  Error: {fps[0].error_type}")
    print(f"  Function: {fps[0].function_name}")
    print(f"  Hash: {fps[0].fingerprint_hash}")
    print(f"  PASS: {fps[0].file_path == 'src/yt_fts/download/download_handler.py'}")
    print()

    # Test 2: Simple error message
    error2 = "AttributeError: module 'download_handler' has no attribute 'get_vtt'"
    fp = FingerprintExtractor.extract_from_problem_description(error2)
    print("Test 2 - Simple error:")
    print(f"  Error type: {fp.error_type if fp else 'None'}")
    print()

    # Test 3: File:line format
    desc3 = "Error in download_handler.py:127 - options is None"
    fp = FingerprintExtractor.extract_from_problem_description(desc3)
    print("Test 3 - File:line format:")
    print(f"  File: {fp.file_path if fp else 'None'}")
    print(f"  Line: {fp.line_number if fp else 'None'}")
    print(f"  PASS: {fp.file_path == 'download_handler.py' if fp else False}")
    print()

    # Test 4: Similarity scoring
    fp1 = StackTraceFingerprint("download_handler.py", 127, "AttributeError")
    fp2 = StackTraceFingerprint("download_handler.py", 130, "AttributeError")
    fp3 = StackTraceFingerprint("batch_downloader.py", 50, "TypeError")

    print("Test 4 - Similarity scoring:")
    print(f"  Same file, nearby line: {fp1.similarity_to(fp2):.1f}")
    print(f"  Different file/error: {fp1.similarity_to(fp3):.1f}")
    print(f"  Exact match: {fp1.similarity_to(fp1):.1f}")
    print()

    # Test 5: FixRecord serialization
    fix = FixRecord(
        fingerprint=fp1,
        fix_description="Initialize yt_dlp_options before use",
        applied_at="2025-12-27T02:00:00",
        verified=True,
        times_seen=3,
    )
    print("Test 5 - FixRecord serialization:")
    data = fix.to_dict()
    restored = FixRecord.from_dict(data)
    print(f"  Round-trip: {'PASS' if restored.fingerprint == fix.fingerprint else 'FAIL'}")
    print()


if __name__ == "__main__":
    _test()

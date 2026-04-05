"""
Error Signature Matching for RCA/Debug Workflow

Extracts pattern-level signatures from errors, independent of location.
Enables: "Same kind of error, different file? → Same solution."

Example:
- download_handler.py:127 AttributeError (NoneType dict access)
- batch_downloader.py:85 AttributeError (NoneType dict access)
→ Same signature: "null_dict_access"
→ Same solution: "Initialize dict or use .get() with default"

"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

# Error signature patterns
SIGNATURE_PATTERNS = {
    # None/Null access patterns
    "null_dict_access": r"AttributeError.*'NoneType'.*__getitem__|KeyError.*None.*dict",
    "null_attr_access": r"AttributeError.*'NoneType'.*has no attribute|AttributeError.*NoneType.*object",
    "null_function_call": r"TypeError.*NoneType.*not callable",

    # Missing/Empty patterns
    "missing_key": r"KeyError.*'(?!NoneType)[^']+'.*not found",
    "index_error": r"IndexError.*list.*out of range|IndexError.*list.*assignment",
    "missing_import": r"ImportError.*No module named|ModuleNotFoundError",

    # Type mismatches
    "type_not_subscriptable": r"TypeError.*'(int|str|float).*object.*not subscriptable",
    "type_not_iterable": r"TypeError.*'(int|float).*object.*not iterable",
    "type_wrong_arg": r"TypeError.*[A-Za-z]+.*takes.*argument.*but.*was given",

    # Attribute/Method errors
    "attr_not_found": r"AttributeError.*module.*has no attribute|AttributeError.*object.*has no attribute",
    "method_not_found": r"AttributeError.*'[A-Za-z_]+'.*object.*has no attribute",
    "attr_not_assigned": r"AttributeError.*can't set attribute|UnboundLocalError",

    # File/IO errors
    "file_not_found": r"FileNotFoundError.*No such file|FileNotFoundError.*[A-Za-z]:",
    "permission_denied": r"PermissionError.*[Pp]ermission denied",

    # Value/Format errors
    "value_error": r"ValueError.*invalid literal|ValueError.*could not convert",
    "json_decode_error": r"JSONDecodeError.*Expecting value",
    "yaml_error": r"YAMLError|YAMLLoadError",

    # Async/Concurrency
    "asyncio_error": r"RuntimeError.*Event loop.*closed|RuntimeError.*This event loop",
    "await_error": r"SyntaxError.*'await' outside.*async",

    # Configuration
    "config_missing": r"KeyError.*config|AttributeError.*config",

    # Collection/Iteration errors
    "set_changed_size": r"RuntimeError.*Set changed size during iteration|RuntimeError.*dictionary changed size",
    "list_changed_size": r"RuntimeError.*List changed size during iteration",

    # Network/Connection errors
    "connection_error": r"ConnectionError|ConnectionRefusedError|HTTPSConnectionPool.*failed",
    "timeout_error": r"TimeoutError|ReadTimeout|ConnectTimeout",

    # OS/System errors
    "os_error": r"OSError.*\[Errno",
    "process_lookup": r"ProcessLookupError",
}


# Pattern names to human-readable descriptions
SIGNATURE_DESCRIPTIONS = {
    "null_dict_access": "Accessing dict without None check (dict[key] on None)",
    "null_attr_access": "Accessing attribute on None object",
    "null_function_call": "Calling None as a function",
    "missing_key": "Dictionary key not found",
    "index_error": "List index out of range",
    "missing_import": "Module not found or not installed",
    "type_not_subscriptable": "Trying to index a non-subscriptable type",
    "type_not_iterable": "Trying to iterate over a non-iterable type",
    "type_wrong_arg": "Function called with wrong argument type",
    "attr_not_found": "Module/object missing expected attribute",
    "method_not_found": "Object missing expected method",
    "attr_not_assigned": "Local variable referenced before assignment",
    "file_not_found": "File path does not exist",
    "permission_denied": "Insufficient permissions for operation",
    "value_error": "Invalid value for conversion/operation",
    "json_decode_error": "Invalid JSON format",
    "yaml_error": "Invalid YAML format",
    "asyncio_error": "Event loop or async operation error",
    "await_error": "await used outside async function",
    "config_missing": "Configuration value missing",
    "set_changed_size": "Modifying collection during iteration",
    "list_changed_size": "Modifying list during iteration",
    "connection_error": "Network connection failed or refused",
    "timeout_error": "Operation timed out",
    "os_error": "Operating system error",
    "process_lookup": "Process not found",
}


# Default fix templates for each signature
FIX_TEMPLATES = {
    "null_dict_access": "Use dict.get(key, default) or check if dict is None first",
    "null_attr_access": "Check if object is None before accessing attribute: if obj is not None",
    "null_function_call": "Verify function is assigned before calling: func = func or default_func",
    "missing_key": "Use dict.get(key, default) or check 'key in dict' before access",
    "index_error": "Check list length before indexing or use enumerate/zip carefully",
    "missing_import": "Install package: pip install <package> or check import path",
    "type_not_subscriptable": "Convert to list/subscriptable type first: list(obj) or obj[...] if applicable",
    "type_not_iterable": "Convert to iterable: list(obj) or check type before iterating",
    "type_wrong_arg": "Check function signature: correct type and number of arguments",
    "attr_not_found": "Check module/object documentation for correct attribute name",
    "method_not_found": "Verify object has method: hasattr(obj, 'method') or check type",
    "attr_not_assigned": "Initialize variable before use or check scope",
    "file_not_found": "Check file path exists: Path(path).exists() or use absolute path",
    "permission_denied": "Check file permissions or use sudo/admin privileges",
    "value_error": "Validate input format before conversion or handle exception",
    "json_decode_error": "Validate JSON before parsing or check response encoding",
    "yaml_error": "Validate YAML syntax or check indentation/formatting",
    "asyncio_error": "Ensure event loop is running and not closed",
    "await_error": "Move async call to async function or use asyncio.create_task()",
    "config_missing": "Set config value in config file or use environment variable",
    "set_changed_size": "Convert to list before iterating: for item in list(my_set):",
    "list_changed_size": "Create copy before modifying: new_list = my_list.copy()",
    "connection_error": "Check internet connection or add retry logic with exponential backoff",
    "timeout_error": "Increase timeout or use async operations with cancellation",
    "os_error": "Check OS-specific error code and handle accordingly",
    "process_lookup": "Verify process is running before attempting to communicate",
}


@dataclass(frozen=True)
class ErrorSignature:
    """A pattern-level signature of an error, independent of location."""

    pattern_name: str  # e.g., "null_dict_access"
    error_type: str  # e.g., "AttributeError"

    @property
    def signature_hash(self) -> str:
        """Deterministic hash for pattern matching."""
        return hashlib.md5(f"{self.pattern_name}:{self.error_type}".encode()).hexdigest()[:12]

    @property
    def description(self) -> str:
        """Human-readable description of this signature."""
        return SIGNATURE_DESCRIPTIONS.get(self.pattern_name, self.pattern_name)

    @property
    def fix_template(self) -> str:
        """Default fix template for this signature."""
        return FIX_TEMPLATES.get(self.pattern_name, "Investigate the error pattern")

    def matches(self, error_message: str) -> bool:
        """Check if this signature matches the error message."""
        pattern = SIGNATURE_PATTERNS.get(self.pattern_name)
        if not pattern:
            return False
        return bool(re.search(pattern, error_message, re.IGNORECASE | re.DOTALL))


@dataclass
class SignatureMatch:
    """Result of matching an error to a signature."""

    signature: ErrorSignature
    confidence: float  # 0.0 to 1.0
    matched_text: str  # The text that matched
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "pattern_name": self.signature.pattern_name,
            "error_type": self.signature.error_type,
            "confidence": self.confidence,
            "matched_text": self.matched_text,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class PatternFixRecord:
    """A fix pattern that can be applied across locations."""

    signature: ErrorSignature
    fix_description: str
    fix_template: str
    code_diff: str = ""  # Optional: example code fix
    applied_count: int = 0
    locations_seen: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "pattern_name": self.signature.pattern_name,
            "error_type": self.signature.error_type,
            "fix_description": self.fix_description,
            "fix_template": self.fix_template,
            "code_diff": self.code_diff,
            "applied_count": self.applied_count,
            "locations_seen": self.locations_seen,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "verified": self.verified,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatternFixRecord:
        """Create from dictionary."""
        sig = ErrorSignature(
            pattern_name=data["pattern_name"],
            error_type=data["error_type"],
        )
        return cls(
            signature=sig,
            fix_description=data["fix_description"],
            fix_template=data["fix_template"],
            code_diff=data.get("code_diff", ""),
            applied_count=data.get("applied_count", 0),
            locations_seen=data.get("locations_seen", []),
            first_seen=data.get("first_seen", ""),
            last_seen=data.get("last_seen", ""),
            verified=data.get("verified", False),
        )


class ErrorSignatureExtractor:
    """Extracts pattern-level signatures from error messages."""

    @classmethod
    def extract_signatures(
        cls,
        error_message: str,
    ) -> list[ErrorSignature]:
        """
        Extract all matching signatures from an error message.

        Args:
            error_message: The error message or stack trace

        Returns:
            List of matching ErrorSignature objects

        """
        signatures = []

        # Extract error type
        error_type = cls._extract_error_type(error_message)

        # Check each pattern
        for pattern_name, pattern in SIGNATURE_PATTERNS.items():
            if re.search(pattern, error_message, re.IGNORECASE | re.DOTALL):
                sig = ErrorSignature(
                    pattern_name=pattern_name,
                    error_type=error_type,
                )
                signatures.append(sig)

        return signatures

    @classmethod
    def _extract_error_type(cls, text: str) -> str:
        """Extract error type from error message."""
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
            "FileNotFoundError",
            "PermissionError",
            "JSONDecodeError",
            "SyntaxError",
            "UnboundLocalError",
            "NameError",
            "AssertionError",
            "ConnectionError",
            "ConnectionRefusedError",
            "TimeoutError",
            "OSError",
            "ProcessLookupError",
        ]:
            if err_type in text:
                return err_type
        return "Error"

    @classmethod
    def get_best_match(
        cls,
        error_message: str,
    ) -> ErrorSignature | None:
        """
        Get the best matching signature for an error.

        Returns the most specific match (prioritizes more specific patterns).

        Args:
            error_message: The error message

        Returns:
            Best matching ErrorSignature or None

        """
        signatures = cls.extract_signatures(error_message)

        if not signatures:
            return None

        # Prioritize more specific patterns
        priority_order = [
            "null_dict_access",
            "missing_key",
            "missing_import",
            "file_not_found",
            "connection_error",
            "timeout_error",
            "set_changed_size",
            "null_attr_access",
            "index_error",
            "type_not_subscriptable",
            "type_not_iterable",
        ]

        for pattern_name in priority_order:
            for sig in signatures:
                if sig.pattern_name == pattern_name:
                    return sig

        # Return first match if no priority match
        return signatures[0] if signatures else None


# Convenience functions
def extract_signature(error_message: str) -> ErrorSignature | None:
    """Extract the best matching error signature."""
    return ErrorSignatureExtractor.get_best_match(error_message)


def match_to_pattern(
    error_message: str,
) -> SignatureMatch | None:
    """
    Match error to a signature with confidence score.

    Args:
        error_message: The error message

    Returns:
        SignatureMatch with confidence and suggested fix

    """
    sig = extract_signature(error_message)
    if not sig:
        return None

    # Calculate confidence based on match specificity
    confidence = 0.7  # Base confidence for pattern match

    # Higher confidence for very specific patterns
    specific_patterns = [
        "null_dict_access",
        "missing_import",
        "file_not_found",
        "connection_error",
        "set_changed_size",
    ]
    if sig.pattern_name in specific_patterns:
        confidence = 0.9

    return SignatureMatch(
        signature=sig,
        confidence=confidence,
        matched_text=error_message[:100],
        suggested_fix=sig.fix_template,
    )


# CLI test function
def _test() -> None:
    """Run built-in tests."""
    print("Error Signature Matching Tests")
    print("=" * 60)

    # Test 1: Dict access on None
    error1 = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
    sig1 = extract_signature(error1)
    print("Test 1 - Dict access on None:")
    print(f"  Signature: {sig1.pattern_name if sig1 else 'None'}")
    print(f"  Description: {sig1.description if sig1 else 'N/A'}")
    print(f"  Fix: {sig1.fix_template if sig1 else 'N/A'}")
    print()

    # Test 2: Same pattern, different file
    error2 = """
Traceback:
  File "download_handler.py", line 127, in get_vtt
    options = yt_dlp_options["format"]
AttributeError: 'NoneType' object has no attribute '__getitem__'
"""
    error3 = """
Traceback:
  File "batch_downloader.py", line 85, in download
    videos = channel["videos"]
KeyError: 'videos'
"""
    sig2 = extract_signature(error2)
    sig3 = extract_signature(error3)

    print("Test 2 - Same pattern, different errors:")
    print(f"  Error 2 signature: {sig2.pattern_name if sig2 else 'None'}")
    print(f"  Error 3 signature: {sig3.pattern_name if sig3 else 'None'}")
    print(f"  Same pattern: {sig2.pattern_name == sig3.pattern_name if sig2 and sig3 else 'N/A'}")
    print()

    # Test 3: Multiple signatures
    complex_error = "TypeError: 'int' object is not subscriptable"
    sig4 = extract_signature(complex_error)
    print("Test 3 - Type error:")
    print(f"  Signature: {sig4.pattern_name if sig4 else 'None'}")
    print(f"  Fix: {sig4.fix_template if sig4 else 'N/A'}")
    print()

    # Test 4: Unknown pattern
    unknown = "CustomError: something unexpected"
    sig5 = extract_signature(unknown)
    print("Test 4 - Unknown pattern:")
    print(f"  Signature: {sig5.pattern_name if sig5 else 'None'}")
    print()

    # Test 5: Match with confidence
    match = match_to_pattern(error2)
    print("Test 5 - Match with confidence:")
    if match:
        print(f"  Pattern: {match.signature.pattern_name}")
        print(f"  Confidence: {match.confidence}")
        print(f"  Suggested fix: {match.suggested_fix}")
    print()

    # Test 6: New patterns (set iteration, connection error)
    error6 = "RuntimeError: Set changed size during iteration"
    sig6 = extract_signature(error6)
    print("Test 6 - Set iteration error:")
    print(f"  Signature: {sig6.pattern_name if sig6 else 'None'}")
    print(f"  Fix: {sig6.fix_template if sig6 else 'N/A'}")
    print()

    error7 = "ConnectionError: HTTPSConnectionPool(host='api.example.com', port=443): Max retries exceeded"
    sig7 = extract_signature(error7)
    print("Test 7 - Connection error:")
    print(f"  Signature: {sig7.pattern_name if sig7 else 'None'}")
    print(f"  Fix: {sig7.fix_template if sig7 else 'N/A'}")
    print()

    print("All tests complete!")


if __name__ == "__main__":
    _test()

"""Hypothesis Generator - generates debugging hypotheses from error context.

This module provides functionality to generate debugging hypotheses based on
error types, messages, and evidence items. It supports systematic hypothesis
generation for common Python error patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class HypothesisCategory(Enum):
    """Categories of debugging hypotheses.

    Each category represents a common type of bug or error pattern
    that can be systematically investigated during debugging.
    """

    OFF_BY_ONE = "off_by_one"
    NULL_DEREFERENCE = "null_dereference"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_GUARD = "missing_guard"
    WRONG_OPERATOR = "wrong_operator"
    INCORRECT_RETURN = "incorrect_return"
    STATE_CORRUPTION = "state_corruption"
    RACE_CONDITION = "race_condition"
    RESOURCE_LEAK = "resource_leak"
    CONFIG_ERROR = "config_error"
    DEPENDENCY_VERSION = "dependency_version"
    ENCODING_ERROR = "encoding_error"


@dataclass
class Hypothesis:
    """A debugging hypothesis with supporting evidence and falsification test.

    Attributes:
        category: The type of hypothesis from HypothesisCategory enum.
        description: Human-readable explanation of the hypothesis.
        target_location: File or location where the bug is suspected.
        priority_weight: Initial confidence score (0.0 to 1.0).
        falsification_test: Test or investigation to disprove the hypothesis.
        supporting_evidence: Evidence items that support this hypothesis.
        contradicting_evidence: Evidence items that contradict this hypothesis.
        status: Current investigation status (e.g., "pending", "investigating", "confirmed").
    """

    category: HypothesisCategory
    description: str
    target_location: str
    priority_weight: float
    falsification_test: str
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    status: str = "pending"


@dataclass
class HypothesisSet:
    """A collection of hypotheses for a specific error signature.

    Attributes:
        error_signature: Unique identifier for the error being investigated.
        hypotheses: List of generated alternative hypotheses.
        null_hypothesis: The hypothesis that the error is external (default None).
    """

    error_signature: str
    hypotheses: list[Hypothesis]
    null_hypothesis: Hypothesis | None = None

    def rank_by_priority(self) -> list[Hypothesis]:
        """Return hypotheses sorted by priority weight in descending order."""
        return sorted(self.hypotheses, key=lambda h: h.priority_weight, reverse=True)


# Confidence calculation constants
SUPPORTING_EVIDENCE_BOOST: float = 0.1
CONTRADICTING_EVIDENCE_PENALTY: float = 0.26
NULL_HYPOTHESIS_WEIGHT: float = 0.3
GENERIC_LOG_ENTRY_WEIGHT: float = 0.6
ZERO_DIVISION_GUARD_WEIGHT: float = 0.95

# Error signature truncation length
MAX_ERROR_SIGNATURE_LENGTH: int = 100


DEFAULT_WEIGHTS: dict[str, float] = {
    "null_dereference": 1.0,
    "type_mismatch": 0.8,
    "off_by_one": 0.9,
    "missing_guard": 0.7,
    "dependency_version": 0.9,
    "config_error": 0.8,
    "race_condition": 0.7,
    "encoding_error": 0.85,
    "state_corruption": 0.85,
    "resource_leak": 0.8,
}


def generate_hypotheses(
    error_type: str,
    error_message: str,
    target_file: str,
    weights: Mapping[str, float] | None = None,
) -> HypothesisSet:
    """Generate debugging hypotheses based on error type and message.

    Analyzes the error type and message to create relevant hypotheses about
    potential root causes. Each hypothesis includes a category, description,
    priority weight, and falsification test.

    Args:
        error_type: The Python exception type (e.g., "AttributeError", "IndexError").
        error_message: The error message or exception text.
        target_file: The file where the error occurred.
        weights: Optional custom priority weights for hypothesis categories.
            Maps category names (str) to priority weights (float).

    Returns:
        HypothesisSet containing generated hypotheses and a null hypothesis.

    Examples:
        >>> result = generate_hypotheses(
        ...     error_type="AttributeError",
        ...     error_message="'NoneType' object has no attribute 'x'",
        ...     target_file="main.py"
        ... )
        >>> len(result.hypotheses)
        2
    """
    w = weights or DEFAULT_WEIGHTS
    hypotheses = []

    if error_type in ("AttributeError", "TypeError"):
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.NULL_DEREFERENCE,
                description="Object is None or uninitialized before attribute access",
                target_location=target_file,
                priority_weight=w.get("null_dereference", 1.0),
                falsification_test="Add logging before access to verify object state",
            )
        )
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.TYPE_MISMATCH,
                description="Object has unexpected type at runtime",
                target_location=target_file,
                priority_weight=w.get("type_mismatch", 0.8),
                falsification_test="Add isinstance check",
            )
        )

    if error_type == "IndexError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.OFF_BY_ONE,
                description="Index exceeds bounds",
                target_location=target_file,
                priority_weight=w.get("off_by_one", 0.9),
                falsification_test="Log len(collection) vs accessed index",
            )
        )
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.MISSING_GUARD,
                description="Missing empty collection check",
                target_location=target_file,
                priority_weight=w.get("missing_guard", 0.7),
                falsification_test="Add guard: if not collection: return",
            )
        )

    if error_type == "KeyError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.MISSING_GUARD,
                description="Dictionary access without existence check",
                target_location=target_file,
                priority_weight=w.get("missing_guard", 0.7),
                falsification_test="Use .get() or check key in dict",
            )
        )

    if "import" in error_message.lower() or error_type == "ModuleNotFoundError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.DEPENDENCY_VERSION,
                description="Module not installed or wrong version",
                target_location=target_file,
                priority_weight=w.get("dependency_version", 0.9),
                falsification_test="Run: pip show <module>",
            )
        )

    if error_type == "ValueError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.TYPE_MISMATCH,
                description="Invalid value passed to function expecting specific format",
                target_location=target_file,
                priority_weight=w.get("type_mismatch", 0.8),
                falsification_test="Log input value and expected format",
            )
        )
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.MISSING_GUARD,
                description="Missing input validation before processing",
                target_location=target_file,
                priority_weight=w.get("missing_guard", 0.7),
                falsification_test="Add input validation guard",
            )
        )

    if error_type == "FileNotFoundError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.CONFIG_ERROR,
                description="Path is incorrect or file was not created",
                target_location=target_file,
                priority_weight=w.get("config_error", 0.8),
                falsification_test="Log resolved path and check existence",
            )
        )

    if error_type == "PermissionError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.CONFIG_ERROR,
                description="Insufficient permissions for file/resource access",
                target_location=target_file,
                priority_weight=w.get("config_error", 0.8),
                falsification_test="Check file permissions and ownership",
            )
        )

    if error_type == "TimeoutError" or "timeout" in error_message.lower():
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.RACE_CONDITION,
                description="Operation took longer than expected timeout",
                target_location=target_file,
                priority_weight=w.get("race_condition", 0.7),
                falsification_test="Increase timeout and log elapsed time",
            )
        )

    if error_type == "ConnectionError" or "connection" in error_message.lower():
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.CONFIG_ERROR,
                description="Network endpoint unreachable or misconfigured",
                target_location=target_file,
                priority_weight=w.get("config_error", 0.8),
                falsification_test="Verify endpoint URL and network connectivity",
            )
        )

    if error_type in ("UnicodeDecodeError", "UnicodeEncodeError"):
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.ENCODING_ERROR,
                description="File or data encoding mismatch",
                target_location=target_file,
                priority_weight=w.get("encoding_error", 0.85),
                falsification_test="Check file encoding, try explicit encoding parameter",
            )
        )

    if "recursion" in error_message.lower() or error_type == "RecursionError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.STATE_CORRUPTION,
                description="Unbounded recursion due to missing base case",
                target_location=target_file,
                priority_weight=w.get("state_corruption", 0.9),
                falsification_test="Add recursion depth logging, verify base case",
            )
        )

    if error_type == "AssertionError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.STATE_CORRUPTION,
                description="Invariant or precondition violation",
                target_location=target_file,
                priority_weight=w.get("state_corruption", 0.85),
                falsification_test="Log state before assertion",
            )
        )

    if error_type == "ZeroDivisionError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.MISSING_GUARD,
                description="Division by zero due to missing zero-check",
                target_location=target_file,
                priority_weight=w.get("missing_guard", ZERO_DIVISION_GUARD_WEIGHT),
                falsification_test="Add guard: if divisor == 0: handle error",
            )
        )

    if error_type == "MemoryError":
        hypotheses.append(
            Hypothesis(
                category=HypothesisCategory.RESOURCE_LEAK,
                description="Memory exhaustion from unbounded allocation",
                target_location=target_file,
                priority_weight=w.get("resource_leak", 0.8),
                falsification_test="Profile memory usage, check for unbounded growth",
            )
        )

    null_hypothesis = Hypothesis(
        category=HypothesisCategory.CONFIG_ERROR,
        description=f"Error originates outside {target_file}",
        target_location="external",
        priority_weight=NULL_HYPOTHESIS_WEIGHT,
        falsification_test="Trace call stack",
    )

    return HypothesisSet(
        error_signature=f"{error_type}: {error_message[:MAX_ERROR_SIGNATURE_LENGTH]}",
        hypotheses=hypotheses,
        null_hypothesis=null_hypothesis,
    )


def generate_hypotheses_from_evidence(evidence: list[Mapping[str, str]]) -> HypothesisSet:
    """Generate debugging hypotheses from evidence items.

    Analyzes stack traces and log entries to create hypotheses about
    potential root causes. Each evidence item can contribute to
    hypothesis generation with supporting evidence.

    Args:
        evidence: List of evidence dictionaries with keys:
            - type: "stack_trace" or "log_entry"
            - message: Error or log message
            - file: Source file name
            - line: Line number (optional)

    Returns:
        HypothesisSet with generated hypotheses and null hypothesis.

    Examples:
        >>> evidence = [
        ...     {"type": "stack_trace", "message": "AttributeError: 'NoneType'", "file": "main.py"}
        ... ]
        >>> result = generate_hypotheses_from_evidence(evidence)
        >>> len(result.hypotheses)
        1
    """
    hypotheses = []

    for item in evidence:
        message = item.get("message", "")
        file_name = item.get("file", "unknown")
        evidence_type = item.get("type", "unknown")

        # Extract error type from message if available
        error_type = None
        if ":" in message:
            error_type = message.split(":")[0].strip()

        # Generate hypothesis based on evidence
        if error_type == "AttributeError" or "NoneType" in message:
            hyp = Hypothesis(
                category=HypothesisCategory.NULL_DEREFERENCE,
                description="Object is None or uninitialized",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("null_dereference", 1.0),
                falsification_test="Add logging to verify object state",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        elif error_type == "IndexError" or "index" in message.lower():
            hyp = Hypothesis(
                category=HypothesisCategory.OFF_BY_ONE,
                description="Index exceeds collection bounds",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("off_by_one", 0.9),
                falsification_test="Log collection length and index",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        elif error_type == "KeyError":
            hyp = Hypothesis(
                category=HypothesisCategory.MISSING_GUARD,
                description="Dictionary key accessed without existence check",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("missing_guard", 0.7),
                falsification_test="Use .get() or check key in dict",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        elif error_type == "TypeError":
            hyp = Hypothesis(
                category=HypothesisCategory.TYPE_MISMATCH,
                description="Type mismatch in operation",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("type_mismatch", 0.8),
                falsification_test="Add isinstance check",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        elif error_type == "ValueError":
            hyp = Hypothesis(
                category=HypothesisCategory.TYPE_MISMATCH,
                description="Invalid value for operation",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("type_mismatch", 0.8),
                falsification_test="Log input value and expected format",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        elif error_type == "ConnectionError" or "connection" in message.lower():
            hyp = Hypothesis(
                category=HypothesisCategory.CONFIG_ERROR,
                description="Network endpoint unreachable or misconfigured",
                target_location=file_name,
                priority_weight=DEFAULT_WEIGHTS.get("config_error", 0.8),
                falsification_test="Verify endpoint URL and network connectivity",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

        # For log entries, create hypotheses based on content
        elif evidence_type == "log_entry":
            if "None" in message or "not initialized" in message.lower():
                hyp = Hypothesis(
                    category=HypothesisCategory.NULL_DEREFERENCE,
                    description="Variable may be None based on log entry",
                    target_location=file_name,
                    priority_weight=DEFAULT_WEIGHTS.get("null_dereference", 1.0),
                    falsification_test="Add logging to verify object state",
                    supporting_evidence=[message],
                )
                hypotheses.append(hyp)
            elif "length" in message.lower() or "empty" in message.lower():
                hyp = Hypothesis(
                    category=HypothesisCategory.MISSING_GUARD,
                    description="Collection may be empty based on log entry",
                    target_location=file_name,
                    priority_weight=DEFAULT_WEIGHTS.get("missing_guard", 0.7),
                    falsification_test="Add guard for empty collection",
                    supporting_evidence=[message],
                )
                hypotheses.append(hyp)
            elif "type" in message.lower() or "check" in message.lower():
                hyp = Hypothesis(
                    category=HypothesisCategory.TYPE_MISMATCH,
                    description="Type-related issue based on log entry",
                    target_location=file_name,
                    priority_weight=DEFAULT_WEIGHTS.get("type_mismatch", 0.8),
                    falsification_test="Add type validation",
                    supporting_evidence=[message],
                )
                hypotheses.append(hyp)
            else:
                # Generic log entry - create a hypothesis anyway
                hyp = Hypothesis(
                    category=HypothesisCategory.CONFIG_ERROR,
                    description=f"Issue detected in {file_name}",
                    target_location=file_name,
                    priority_weight=GENERIC_LOG_ENTRY_WEIGHT,
                    falsification_test="Investigate log entry context",
                    supporting_evidence=[message],
                )
                hypotheses.append(hyp)

        # For generic stack traces without recognized error type
        elif evidence_type == "stack_trace" and error_type not in (
            "AttributeError", "TypeError", "IndexError", "KeyError",
            "ValueError", "ConnectionError"
        ):
            hyp = Hypothesis(
                category=HypothesisCategory.CONFIG_ERROR,
                description=f"Error detected in {file_name}",
                target_location=file_name,
                priority_weight=GENERIC_LOG_ENTRY_WEIGHT,
                falsification_test="Investigate stack trace context",
                supporting_evidence=[message],
            )
            hypotheses.append(hyp)

    # Create null hypothesis
    null_hypothesis = Hypothesis(
        category=HypothesisCategory.CONFIG_ERROR,
        description="Error originates outside codebase",
        target_location="external",
        priority_weight=NULL_HYPOTHESIS_WEIGHT,
        falsification_test="Trace call stack",
    )

    # Create error signature from evidence
    if evidence:
        first_msg = evidence[0].get("message", "") if evidence else ""
        error_signature = first_msg[:MAX_ERROR_SIGNATURE_LENGTH] if first_msg else "evidence-based"
    else:
        error_signature = "no evidence"

    return HypothesisSet(
        error_signature=error_signature,
        hypotheses=hypotheses,
        null_hypothesis=null_hypothesis,
    )


def calculate_hypothesis_confidence(hypothesis: Hypothesis) -> float:
    """Calculate confidence score for a hypothesis based on evidence.

    Confidence is calculated as:
    - Start with priority_weight as base confidence
    - Add SUPPORTING_EVIDENCE_BOOST for each supporting evidence item
    - Subtract CONTRADICTING_EVIDENCE_PENALTY for each contradicting evidence item
    - Clamp result to [0.0, 1.0]

    Args:
        hypothesis: Hypothesis to calculate confidence for.

    Returns:
        Confidence score between 0.0 and 1.0.

    Examples:
        >>> hyp = Hypothesis(
        ...     category=HypothesisCategory.NULL_DEREFERENCE,
        ...     description="Test",
        ...     target_location="file.py",
        ...     priority_weight=0.8,
        ...     falsification_test="test",
        ...     supporting_evidence=["ev1", "ev2"]
        ... )
        >>> confidence = calculate_hypothesis_confidence(hyp)
        >>> assert 0.0 <= confidence <= 1.0
    """
    # Start with priority weight as base confidence
    confidence = hypothesis.priority_weight

    # Adjust based on supporting evidence
    supporting_count = len(hypothesis.supporting_evidence)
    confidence += supporting_count * SUPPORTING_EVIDENCE_BOOST

    # Adjust based on contradicting evidence (penalty is higher)
    contradicting_count = len(hypothesis.contradicting_evidence)
    confidence -= contradicting_count * CONTRADICTING_EVIDENCE_PENALTY

    # Clamp to valid range
    confidence = max(0.0, min(1.0, confidence))

    return confidence

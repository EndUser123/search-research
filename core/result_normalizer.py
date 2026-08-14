"""Result normalization layer for unified search result validation.

This module provides the NormalizedResult protocol and normalize_result() function
to ensure runtime type safety and unified result validation across all backends.

The NormalizedResult protocol defines the required interface for all search results:
- id: Unique identifier for the result
- score: Relevance score in range [0.0, 1.0]
- source: Source/backend name that provided this result
- to_dict(): Method to convert result to dictionary representation

Protocol validation is performed at runtime through @runtime_checkable and a custom
metaclass that enables isinstance() checks for both objects and dicts.
"""

from typing import Any, Final, Protocol, runtime_checkable

# Score validation bounds
_MIN_SCORE: Final = 0.0
_MAX_SCORE: Final = 1.0

# Required fields for NormalizedResult protocol
_REQUIRED_FIELDS: Final = ("id", "score", "source", "to_dict")


class _NormalizedResultMeta(type(Protocol)):
    """Metaclass to enable isinstance() checks for dicts with NormalizedResult.

    This metaclass extends the standard Protocol instance checking to support
    dictionary instances that satisfy the NormalizedResult protocol structure.
    """

    def __instancecheck__(cls, instance: Any) -> bool:
        """Check if instance satisfies NormalizedResult protocol.

        Args:
            instance: Object to check

        Returns:
            True if instance satisfies the protocol, False otherwise
        """
        if isinstance(instance, dict):
            return all(
                field in instance and
                (field != "to_dict" or callable(instance["to_dict"]))
                for field in _REQUIRED_FIELDS
            )
        return type(Protocol).__instancecheck__(cls, instance)


@runtime_checkable
class NormalizedResult(Protocol, metaclass=_NormalizedResultMeta):
    """Protocol for normalized search results (runtime enforceable).

    This protocol defines the required interface for all search results
    from any backend provider. Using @runtime_checkable allows isinstance()
    checks to validate compliance at runtime.

    Attributes:
        id: Unique identifier for the result
        score: Relevance score in range [0.0, 1.0]
        source: Source/backend name that provided this result
    """

    id: str
    score: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary containing at least id, score, and source fields
        """
        ...


def _validate_score(score: Any) -> float:
    """Validate that a score value is within valid bounds.

    Args:
        score: Score value to validate

    Raises:
        ValueError: If score is outside [0.0, 1.0] range
    """
    if score < _MIN_SCORE:
        raise ValueError(f"score must be non-negative, got {score}")
    if score > _MAX_SCORE:
        raise ValueError(f"score must be <= 1.0, got {score}")


def _validate_source(source: Any) -> None:
    """Validate that a source value is a non-empty string.

    Args:
        source: Source value to validate

    Raises:
        TypeError: If source is not a string
        ValueError: If source is empty or whitespace-only
    """
    if not isinstance(source, str):
        raise TypeError(f"source must be string, got {type(source).__name__}")
    if not source or not source.strip():
        raise ValueError("source cannot be empty")


def _validate_dict_protocol(result: dict[str, Any]) -> None:
    """Validate that a dict satisfies NormalizedResult protocol.

    Args:
        result: Dictionary to validate

    Raises:
        TypeError: If required keys are missing
    """
    missing_keys = [
        key for key in _REQUIRED_FIELDS
        if key not in result or (key == "to_dict" and not callable(result.get(key)))
    ]

    if missing_keys:
        raise TypeError(
            f"Dict does not satisfy NormalizedResult protocol. "
            f"Missing required keys: {', '.join(missing_keys)}"
        )


def _validate_object_protocol(result: Any) -> None:
    """Validate that an object satisfies NormalizedResult protocol.

    Args:
        result: Object to validate

    Raises:
        TypeError: If required attributes are missing
    """
    missing_attrs = [
        attr for attr in _REQUIRED_FIELDS
        if not hasattr(result, attr) or
        (attr == "to_dict" and not callable(getattr(result, attr, None)))
    ]

    if missing_attrs:
        raise TypeError(
            f"Result does not satisfy NormalizedResult protocol. "
            f"Missing required attributes: {', '.join(missing_attrs)}"
        )


def _validate_dict_result(result: dict[str, Any]) -> None:
    """Perform full validation on a dict result.

    Args:
        result: Dictionary to validate

    Raises:
        TypeError: If protocol requirements not met
        ValueError: If score or source values are invalid
    """
    _validate_dict_protocol(result)
    _validate_score(result["score"])
    _validate_source(result["source"])


def _validate_object_result(result: Any) -> None:
    """Perform full validation on an object result.

    Args:
        result: Object to validate

    Raises:
        TypeError: If protocol requirements not met
        ValueError: If score or source values are invalid
    """
    _validate_object_protocol(result)
    _validate_score(result.score)
    _validate_source(result.source)


def normalize_result(result: Any) -> NormalizedResult:
    """Normalize any backend result to NormalizedResult protocol.

    This function validates that the input result satisfies the NormalizedResult
    protocol and performs runtime validation on score and source values.

    Args:
        result: Any backend result (SearchResult, dict, custom object)

    Returns:
        NormalizedResult instance (the input is returned if valid)

    Raises:
        TypeError: If result violates NormalizedResult protocol
        ValueError: If score or source values are invalid
    """
    if result is None:
        raise TypeError("Cannot normalize None value")

    if isinstance(result, dict):
        _validate_dict_result(result)
        return result

    # Reject primitive types that cannot satisfy the protocol
    if isinstance(result, (str, list, int, float, bool)):
        raise TypeError(
            f"Cannot normalize {type(result).__name__} to NormalizedResult"
        )

    _validate_object_result(result)
    return result

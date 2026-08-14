"""Validation module for project context operations.

Ported from MCP Memory Keeper validation patterns.
Provides comprehensive input validation with security considerations.

Constitutional Requirements:
- Solo developer optimization (clear error messages)
- Evidence-based validation (proven patterns from MCP Memory Keeper)
- Force multiplier (reusable validation functions)
- No enterprise bloat (direct Python, no complex frameworks)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationError(Exception):
    """Validation error with details."""

    message: str
    field: str | None = None


def validate_tsk_id(tsk_id: str) -> str:
    """Validate TSK ID format (e.g., TSK-ALT-PLATFORM-DOWNLOADING).

    Args:
        tsk_id: TSK ID to validate

    Returns:
        Validated and normalized TSK ID

    Raises:
        ValidationError: If TSK ID is invalid

    """
    if not tsk_id or not isinstance(tsk_id, str):
        raise ValidationError("TSK ID must be a non-empty string", "tsk_id")

    trimmed = tsk_id.strip()
    if trimmed != tsk_id:
        raise ValidationError("TSK ID cannot have leading/trailing whitespace", "tsk_id")

    if len(trimmed) > 255:
        raise ValidationError("TSK ID too long (max 255 characters)", "tsk_id")

    # TSK format: TSK-<NAME>-<OPTIONAL>
    # Example: TSK-ALT-PLATFORM-DOWNLOADING
    if not re.match(r"^TSK-[A-Z0-9]+(-[A-Z0-9]+)*$", trimmed):
        raise ValidationError(
            "TSK ID must match format: TSK-<NAME>-<OPTIONAL> "
            "(e.g., TSK-ALT-PLATFORM-DOWNLOADING, TSK-122225-GPUWorkloadIntegration-1457)",
            "tsk_id",
        )

    return trimmed


def validate_worktree_path(worktree_path: str) -> str:
    """Validate worktree path is safe.

    Args:
        worktree_path: Worktree path to validate

    Returns:
        Normalized absolute path

    Raises:
        ValidationError: If path is invalid or unsafe

    """
    if not worktree_path or not isinstance(worktree_path, str):
        raise ValidationError("Worktree path must be a non-empty string", "worktree_path")

    try:
        path = Path(worktree_path).resolve()

        # Check for path traversal
        if ".." in str(path):
            raise ValidationError("Path traversal detected", "worktree_path")

        # Check if path exists
        if not path.exists():
            raise ValidationError(f"Worktree path does not exist: {worktree_path}", "worktree_path")

        # Check if it's a directory
        if not path.is_dir():
            raise ValidationError(
                f"Worktree path is not a directory: {worktree_path}", "worktree_path"
            )

        return str(path)

    except OSError as e:
        raise ValidationError(f"Invalid worktree path: {e}", "worktree_path")


def validate_checkpoint_name(checkpoint_name: str) -> str:
    """Validate checkpoint name.

    Args:
        checkpoint_name: Checkpoint name to validate

    Returns:
        Validated checkpoint name

    Raises:
        ValidationError: If checkpoint name is invalid

    """
    if not checkpoint_name or not isinstance(checkpoint_name, str):
        raise ValidationError("Checkpoint name must be a non-empty string", "checkpoint_name")

    trimmed = checkpoint_name.strip()
    if len(trimmed) == 0:
        raise ValidationError("Checkpoint name cannot be empty", "checkpoint_name")

    if len(trimmed) > 255:
        raise ValidationError("Checkpoint name too long (max 255 characters)", "checkpoint_name")

    # Check for invalid characters
    if re.search(r'[<>:"|?*]', trimmed):
        raise ValidationError("Checkpoint name contains invalid characters", "checkpoint_name")

    return trimmed


def validate_operation_type(operation_type: str) -> str:
    """Validate operation type.

    Args:
        operation_type: Operation type to validate

    Returns:
        Validated operation type

    Raises:
        ValidationError: If operation type is invalid

    """
    valid_types = {"read", "edit", "write", "task", "bash", "glob"}

    if not operation_type or not isinstance(operation_type, str):
        raise ValidationError("Operation type must be a non-empty string", "operation_type")

    op_lower = operation_type.lower()
    if op_lower not in valid_types:
        raise ValidationError(
            f"Invalid operation type: {operation_type}. "
            f"Must be one of: {', '.join(sorted(valid_types))}",
            "operation_type",
        )

    return op_lower


def validate_operation_description(description: str) -> str:
    """Validate operation description.

    Args:
        description: Operation description to validate

    Returns:
        Validated description

    Raises:
        ValidationError: If description is invalid

    """
    if not description or not isinstance(description, str):
        raise ValidationError("Operation description must be a non-empty string", "description")

    trimmed = description.strip()
    if len(trimmed) == 0:
        raise ValidationError("Operation description cannot be empty", "description")

    if len(trimmed) > 10000:
        raise ValidationError(
            "Operation description too long (max 10000 characters)", "description"
        )

    return trimmed


def validate_operation_target(target: str) -> str:
    """Validate operation target (file path, command, etc.).

    Args:
        target: Operation target to validate

    Returns:
        Validated target

    Raises:
        ValidationError: If target is invalid

    """
    if not target or not isinstance(target, str):
        raise ValidationError("Operation target must be a non-empty string", "target")

    trimmed = target.strip()
    if len(trimmed) == 0:
        raise ValidationError("Operation target cannot be empty", "target")

    if len(trimmed) > 10000:
        raise ValidationError("Operation target too long (max 10000 characters)", "target")

    # Check for null bytes
    if "\0" in trimmed:
        raise ValidationError("Operation target contains null bytes", "target")

    return trimmed


def validate_description(description: str | None) -> str | None:
    """Validate optional description field.

    Args:
        description: Description to validate

    Returns:
        Validated description or None

    Raises:
        ValidationError: If description is invalid

    """
    if not description:
        return None

    if not isinstance(description, str):
        raise ValidationError("Description must be a string", "description")

    trimmed = description.strip()
    if len(trimmed) == 0:
        return None

    if len(trimmed) > 10000:
        raise ValidationError("Description too long (max 10000 characters)", "description")

    return trimmed


def validate_metadata(metadata: dict | None) -> str | None:
    """Validate and serialize metadata.

    Args:
        metadata: Metadata dictionary to validate

    Returns:
        JSON string or None

    Raises:
        ValidationError: If metadata is invalid

    """
    if not metadata:
        return None

    if not isinstance(metadata, dict):
        raise ValidationError("Metadata must be a dictionary", "metadata")

    try:
        import json

        return json.dumps(metadata)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid metadata (not JSON serializable): {e}", "metadata")


# Context detection helpers


def detect_context_from_path(file_path: str) -> str | None:
    """Detect project context from file path.

    Args:
        file_path: File path to analyze

    Returns:
        TSK ID if detected, None otherwise

    """
    if not file_path:
        return None

    path_lower = file_path.lower()

    # Platform context detection
    if (
        "yt-fts-alt-platforms" in path_lower
        or "alt-platform" in path_lower
        or ("platform" in path_lower and "odysee" in path_lower)
        or ("platform" in path_lower and "rumble" in path_lower)
        or ("platform" in path_lower and "bitchute" in path_lower)
    ):
        return "TSK-ALT-PLATFORM-DOWNLOADING"

    # GPU context detection
    if (
        ("gpu" in path_lower and "workload" in path_lower)
        or "gpuworkloaddataextractor" in path_lower
        or "gpu_workload" in path_lower
    ):
        return "TSK-122225-GPUWorkloadIntegration-1457"

    return None


def detect_context_from_operation(operation_type: str, description: str) -> str | None:
    """Detect project context from operation description.

    Args:
        operation_type: Type of operation
        description: Operation description

    Returns:
        TSK ID if detected, None otherwise

    """
    if not description:
        return None

    desc_lower = description.lower()

    # Platform context detection
    if "platform" in desc_lower:
        if "odysee" in desc_lower or "rumble" in desc_lower or "bitchute" in desc_lower:
            return "TSK-ALT-PLATFORM-DOWNLOADING"

    # GPU context detection
    if "gpu" in desc_lower and "workload" in desc_lower:
        return "TSK-122225-GPUWorkloadIntegration-1457"

    return None

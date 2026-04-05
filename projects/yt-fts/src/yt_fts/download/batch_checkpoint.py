"""Checkpoint management for batch download resume functionality.

This module provides functions to save, load, and reset checkpoints
for batch downloads, allowing resumption from the last processed channel.

The checkpoint API is polymorphic - it supports both simple integer checkpoints
(for backward compatibility) and structured RefactorCheckpoint dictionaries
(for complex refactoring operations).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import NotRequired, TypedDict, Union

logger = logging.getLogger(__name__)


class RefactorCheckpoint(TypedDict, total=False):
    """Structured checkpoint data for refactoring operations.

    All fields are optional to support partial checkpoint data.

    Attributes:
        refactor_id: Unique identifier for the refactoring operation
        layer: Refactoring layer (1-4)
        call_site: Optional call site identifier
        status: Current status of the refactoring
        timestamp: ISO format timestamp of checkpoint creation
    """
    refactor_id: str
    layer: int
    call_site: NotRequired[str | None]
    status: str
    timestamp: str


CheckpointData = Union[int, RefactorCheckpoint]


def save_checkpoint(data: CheckpointData, checkpoint_file: str) -> None:
    """Save checkpoint data to the checkpoint file.

    Polymorphic function that accepts either:
    - int: Legacy simple checkpoint (channel index)
    - RefactorCheckpoint: Structured checkpoint dict with metadata

    Args:
        data: Checkpoint data (int or RefactorCheckpoint dict)
        checkpoint_file: Path to the checkpoint file

    Raises:
        TypeError: If data is neither int nor dict

    Examples:
        # Legacy integer checkpoint
        save_checkpoint(5, "checkpoint.json")

        # Structured refactor checkpoint
        save_checkpoint({
            "refactor_id": "refactor_abc123",
            "layer": 1,
            "status": "in_progress",
            "timestamp": "2024-01-21T10:30:00"
        }, "checkpoint.json")
    """
    checkpoint_path = Path(checkpoint_file)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, int):
        # Legacy format: simple integer checkpoint
        checkpoint_data = {
            "type": "channel_index",
            "last_completed_index": data,
            "timestamp": datetime.now().isoformat()
        }
    elif isinstance(data, dict):
        # New format: structured RefactorCheckpoint
        # Ensure type field is present for serialization
        checkpoint_data = {**data, "type": "refactor_checkpoint"}
    else:
        raise TypeError(
            f"Checkpoint data must be int or RefactorCheckpoint dict, got {type(data).__name__}"
        )

    # CRITICAL FIX: Add error handling for file write operations
    # Previous code called write_text() without error handling. If disk is full
    # or permissions change, uncaught exception would crash the batch download.
    try:
        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))
    except OSError as e:
        logger.error("Failed to save checkpoint to %s: %s", checkpoint_path, e)
        raise  # Re-raise to caller - checkpoint save is critical for resume functionality


def load_checkpoint(checkpoint_file: str) -> CheckpointData | None:
    """Load the saved checkpoint data.

    Polymorphic return type:
    - int: Legacy simple checkpoint (channel index from "last_completed_index")
    - RefactorCheckpoint: Structured checkpoint dict
    - None: No checkpoint exists or invalid format

    Args:
        checkpoint_file: Path to the checkpoint file

    Returns:
        Checkpoint data (int or RefactorCheckpoint dict), or None if no checkpoint exists

    Examples:
        # Legacy format returns int
        checkpoint = load_checkpoint("checkpoint.json")
        if isinstance(checkpoint, int):
            print(f"Resume from channel {checkpoint}")

        # New format returns dict
        checkpoint = load_checkpoint("checkpoint.json")
        if isinstance(checkpoint, dict):
            print(f"Resume refactor {checkpoint.get('refactor_id')}")
    """
    checkpoint_path = Path(checkpoint_file)
    if not checkpoint_path.exists():
        return None
    try:
        data = json.loads(checkpoint_path.read_text())

        # Legacy format: has "last_completed_index" field
        if "last_completed_index" in data:
            return data.get("last_completed_index")

        # New format: structured RefactorCheckpoint
        # Return the full dict as CheckpointData
        return data

    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def reset_checkpoint(checkpoint_file: str) -> None:
    """Delete the checkpoint file.

    If the checkpoint file does not exist, this function does nothing.
    This graceful behavior allows safe cleanup without prior existence checks.

    Args:
        checkpoint_file: Path to the checkpoint file
    """
    checkpoint_path = Path(checkpoint_file)
    if checkpoint_path.exists():
        checkpoint_path.unlink()

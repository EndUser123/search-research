#!/usr/bin/env python3
"""
Helper module to create checkpoint files in the correct JSON format.
"""

import json
import os
from datetime import datetime


def create_checkpoint(
    checkpoint_name, completed_by, test_passes, implementation_complete, ready_for
):
    """
    Create a checkpoint file with the specified parameters.

    Args:
        checkpoint_name (str): Name of the checkpoint
        completed_by (str): Identifier of who completed the task
        test_passes (list): List of test names that pass
        implementation_complete (str): Description of implementation
        ready_for (list): List of tasks that can now proceed
    """
    # Create the checkpoint data structure
    checkpoint_data = {
        "checkpoint": checkpoint_name,
        "completed_by": completed_by,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verification": {
            "test_passes": test_passes,
            "implementation_complete": implementation_complete,
            "ready_for": ready_for,
        },
    }

    # Create checkpoints directory if it doesn't exist
    checkpoint_dir = os.path.join("dev", "refactors", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Write the checkpoint file
    filename = f"{checkpoint_name}.json"
    filepath = os.path.join(checkpoint_dir, filename)

    with open(filepath, "w") as f:
        json.dump(checkpoint_data, f, indent=2)

    return filepath

"""
/artifact-done command
Mark an artifact as complete for a tracked item.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from artifact_core import mark_artifact_done, find_project_root
from artifact_session import acquire_lock, release_lock
from artifact_init import ensure_schema


def mark_done(args=None) -> None:
    """
    Mark an artifact as done for a tracked item.

    Usage:
        artifact-done TSK-001 changelog
        artifact-done TSK-002 prd --force
    """
    parser = argparse.ArgumentParser(description="Mark artifact as complete")
    parser.add_argument("item_id", help="Item ID (e.g., TSK-001)")
    parser.add_argument("artifact_type", help="Artifact type: changelog, prd, ard, readme")
    parser.add_argument("--project-root", type=str, help="Project directory")
    parser.add_argument("--force", action="store_true", help="Skip mtime verification")
    parsed = parser.parse_args(args)

    # Validate artifact type
    valid_artifacts = ["changelog", "prd", "ard", "readme"]
    if parsed.artifact_type not in valid_artifacts:
        print(f"Error: artifact_type must be one of {valid_artifacts}")
        return

    # Ensure schema exists
    ensure_schema()

    # Find project root
    project_root = Path(parsed.project_root) if parsed.project_root else find_project_root()
    if not project_root:
        print("Error: Could not find project root")
        return

    # Acquire lock
    success, msg = acquire_lock(parsed.item_id, str(project_root))
    if not success:
        print(f"Lock error: {msg}")
        return

    try:
        # Mark artifact done
        success, msg = mark_artifact_done(
            project_root,
            parsed.item_id,
            parsed.artifact_type,
            skip_verify=parsed.force,
        )
        print(msg)

    finally:
        release_lock(parsed.item_id, str(project_root))


if __name__ == "__main__":
    mark_done()

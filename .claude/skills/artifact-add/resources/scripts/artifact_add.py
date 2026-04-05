"""
/artifact-add command
Manually add an item for artifact tracking.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from artifact_core import add_pending_item, find_project_root
from artifact_init import ensure_schema


def add_item(args=None) -> None:
    """
    Manually add an item for artifact tracking.

    Usage:
        artifact-add TSK-001 "Add user auth" feature src/api/auth.py
        artifact-add TSK-002 "Fix login bug" bug_fix src/auth/fix.py
        artifact-add TSK-003 "Update docs" docs README.md --no-files
    """
    parser = argparse.ArgumentParser(description="Add artifact tracking item")
    parser.add_argument("item_id", help="Item ID (e.g., TSK-001)")
    parser.add_argument("summary", help="Human-readable description")
    parser.add_argument("change_type", help="bug_fix, feature, refactor, breaking, docs")
    parser.add_argument("files", nargs="*", help="Files changed (relative paths)")
    parser.add_argument("--project-root", type=str, help="Project directory")
    parser.add_argument("--files-json", type=str, help="JSON array of files")
    parser.add_argument("--source", type=str, default="manual", help="Source: manual or taskmaster")
    parsed = parser.parse_args(args)

    # Validate change type
    valid_types = ['bug_fix', 'feature', 'refactor', 'breaking', 'docs']
    if parsed.change_type not in valid_types:
        print(f"Error: change_type must be one of {valid_types}")
        return

    # Parse files
    if parsed.files_json:
        try:
            files = json.loads(parsed.files_json)
        except json.JSONDecodeError:
            print("Error: --files-json must be valid JSON array")
            return
    else:
        files = parsed.files or []

    # Ensure schema exists
    ensure_schema()

    # Find project root
    project_root = Path(parsed.project_root) if parsed.project_root else find_project_root()
    if not project_root:
        print("Error: Could not find project root")
        return

    # Add pending item
    success, msg = add_pending_item(
        project_root,
        parsed.item_id,
        parsed.summary,
        parsed.change_type,
        files,
        source=parsed.source,
    )
    print(msg)


if __name__ == "__main__":
    add_item()

#!/usr/bin/env python3
"""PreToolUse hook: Backup settings.json before allowing Edit/Write operations."""

import json
import shutil
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = HOOKS_DIR.parent / "settings.json"


def backup_settings_json(settings_path: Path) -> tuple[bool, str]:
    """Create timestamped backup of settings.json.

    Returns:
        (success, message): Tuple of success status and message
    """
    try:
        # Generate timestamp: settings.backup_20260307_170933.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = settings_path.parent / f"settings.backup_{timestamp}.json"

        # Create backup
        shutil.copy2(settings_path, backup_path)

        # Verify backup exists and is valid JSON
        if not backup_path.exists():
            return False, f"Backup file not created: {backup_path}"

        with open(backup_path, encoding="utf-8") as f:
            json.load(f)  # Verify JSON validity

        return True, f"Backup created: {backup_path.name}"

    except Exception as e:
        return False, f"Backup failed: {type(e).__name__}: {e}"


def validate_json_syntax(json_path: Path) -> tuple[bool, str]:
    """Validate JSON syntax (warning only, don't block).

    Returns:
        (is_valid, message): Tuple of validity and message
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            json.load(f)
        return True, "JSON syntax valid"
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"


def run(data: dict) -> dict | None:
    """Hook entry point - backup settings.json before Edit/Write operations.

    Returns:
        None to allow, {"decision": "block"} to block
    """
    tool_name = data.get("tool_name", "")

    # Only process Edit and Write operations
    if tool_name not in ("Edit", "Write"):
        return None

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only process settings.json
    if not file_path or "settings.json" not in file_path:
        return None

    settings_path = Path(file_path)

    # Verify it's actually settings.json (not just contains the name)
    if settings_path.name != "settings.json":
        return None

    # Create backup before allowing edit
    success, message = backup_settings_json(settings_path)

    if not success:
        # BLOCK: Backup failed - safety first
        return {
            "decision": "block",
            "reason": (
                f"⛔ SETTINGS.JSON BACKUP FAILED\n\n"
                f"{message}\n\n"
                f"Edit blocked to prevent data loss. "
                f"Please check file permissions and try again."
            ),
            "blocking_hook": "PreToolUse_settings_backup.py"
        }

    # Backup succeeded - allow edit
    # Note: JSON validation happens in PostToolUse (after edit)
    return None


if __name__ == "__main__":
    import sys
    data = json.load(sys.stdin)
    result = run(data)

    if result and result.get("decision") == "block":
        print(json.dumps(result))
        sys.exit(2)

    sys.exit(0)

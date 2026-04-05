import json
import shutil
from pathlib import Path

SETTINGS_PATH = Path("P:/.claude/settings.json")
BACKUP_PATH = Path("P:/.claude/settings.json.bak_stderr_fix")

# Backup
if SETTINGS_PATH.exists():
    shutil.copy2(SETTINGS_PATH, BACKUP_PATH)
    print(f"Backed up settings to {BACKUP_PATH}")

with open(SETTINGS_PATH, encoding="utf-8") as f:
    data = json.load(f)

updated_count = 0
hooks_config = data.get("hooks", {})

# Target UserPromptSubmit specifically as it's the noisy one
if "UserPromptSubmit" in hooks_config:
    for group in hooks_config["UserPromptSubmit"]:
        for hook in group.get("hooks", []):
            cmd = hook.get("command", "")
            # Only append if not already redirected
            if cmd and "2>NUL" not in cmd and "2>" not in cmd:
                hook["command"] = f"{cmd} 2>NUL"
                updated_count += 1
                print(f"Updated: {hook['command']}")

with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Update complete. Modified {updated_count} hooks.")

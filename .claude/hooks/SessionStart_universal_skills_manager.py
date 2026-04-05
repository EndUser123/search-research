#!/usr/bin/env python3
"""
Universal Skills Manager - Auto-Load Config Hook

Automatically loads SKILLSMP_API_KEY from config.json at session start.
Eliminates need for manual Step 0 execution in Universal Skills Manager workflow.

Location: .claude/hooks/SessionStart_universal_skills_manager.py
Trigger: SessionStart hook (executed when Claude Code session starts)
"""

import json
import os
from pathlib import Path


def load_skillsmp_config():
    """
    Load SkillsMP API key from config.json and export to environment.

    This hook runs automatically at session start, so the SKILLSMP_API_KEY
    is always available without requiring manual eval() execution.

    Returns:
        dict: Environment variables to export (for SessionStart hook protocol)
    """
    # Locate Universal Skills Manager config
    skill_dir = Path.home() / ".claude/skills/universal-skills-manager"
    config_file = skill_dir / "config.json"

    # Check if config exists
    if not config_file.exists():
        return {}

    # Load config
    try:
        with open(config_file) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    # Extract API key
    api_key = config.get("skillsmp_api_key", "")
    if not api_key:
        return {}

    # Export to environment (persists for session)
    os.environ["SKILLSMP_API_KEY"] = api_key

    # Return for SessionStart hook protocol
    return {
        "SKILLSMP_API_KEY": api_key,
    }


if __name__ == "__main__":
    env_vars = load_skillsmp_config()

    if env_vars:
        # Output as environment exports for SessionStart
        for key, value in env_vars.items():
            print(f"{key}={value}")

#!/usr/bin/env python3
"""SessionStart hook: config walk-up and state initialization.

Reads current model from settings.json, performs config walk-up
(plugin-level -> user-level -> project-level), and writes resolved
config to state file at:
.claude/state/model-router/{terminal_id}/{session_id}/config.json
"""

import json
import os
import sys
import pathlib
from datetime import datetime


def get_state_path(terminal_id, session_id):
    """Compute state directory path."""
    state_root = pathlib.Path.cwd() / '.claude' / 'state' / 'model-router' / terminal_id / session_id
    return state_root


def load_config(plugin_root, cwd=None):
    """Load and merge configs with walk-up precedence: plugin < user < project.
    
    Args:
        plugin_root: Path to plugin root for default config.
        cwd: Working directory to search for project config (default: cwd).
    """
    config = {}

    # 1. Plugin-level default
    plugin_config_path = pathlib.Path(plugin_root) / 'claude-model-router.json'
    if plugin_config_path.exists():
        try:
            with open(plugin_config_path) as f:
                config = json.load(f)
        except Exception:
            pass

    # 2. User-level config: ~/.claude/hooks/claude-model-router.json
    user_config_path = pathlib.Path.home() / '.claude' / 'hooks' / 'claude-model-router.json'
    if user_config_path.exists():
        try:
            with open(user_config_path) as f:
                user_config = json.load(f)
                for key in user_config:
                    if key == '$schema':
                        continue
                    if isinstance(user_config[key], dict) and isinstance(config.get(key), dict):
                        config[key] = {**config[key], **user_config[key]}
                    else:
                        config[key] = user_config[key]
        except Exception:
            pass

    # 3. Project-level config: walk up from CWD for .claude/claude-model-router.json
    search_root = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    for parent in [search_root, *search_root.parents]:
        project_path = parent / '.claude' / 'claude-model-router.json'
        if project_path.exists():
            try:
                with open(project_path) as f:
                    project_config = json.load(f)
                for key in project_config:
                    if key == '$schema':
                        continue
                    if isinstance(project_config[key], dict) and isinstance(config.get(key), dict):
                        config[key] = {**config[key], **project_config[key]}
                    else:
                        config[key] = project_config[key]
            except Exception:
                pass
            break

    return config


def get_current_model():
    """Read current model from settings.json."""
    settings_path = pathlib.Path.home() / '.claude' / 'settings.json'
    try:
        with open(settings_path) as f:
            settings = json.load(f)
        return settings.get('model', '')
    except Exception:
        return ''


def write_state(state_path, data):
    """Write state file atomically."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    tmp.replace(state_path)


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        # No input is not an error for SessionStart
        print(json.dumps({'ok': True}))
        return

    terminal_id = input_data.get('terminal_id', 'default')
    session_id = input_data.get('session_id', 'default')

    # Determine plugin root from environment or this file's location
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', str(pathlib.Path(__file__).parent.parent.parent))

    # Load resolved config
    config = load_config(plugin_root)

    # Get current model
    current_model = get_current_model()

    # Determine current tier
    model_lower = current_model.lower()
    current_tier = 'unknown'
    if 'haiku' in model_lower:
        current_tier = 'haiku'
    elif 'sonnet' in model_lower:
        current_tier = 'sonnet'
    elif 'opus' in model_lower:
        current_tier = 'opus'

    # Build state
    state = {
        'terminal_id': terminal_id,
        'session_id': session_id,
        'current_model': current_model,
        'current_tier': current_tier,
        'config': config,
        'written_at': datetime.now().isoformat(),
    }

    # Write state file
    state_path = get_state_path(terminal_id, session_id) / 'config.json'
    write_state(state_path, state)

    # Output hook result
    output = {
        'ok': True,
        'terminal_id': terminal_id,
        'session_id': session_id,
        'current_tier': current_tier,
    }
    print(json.dumps(output))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Stop hook: read recommendation, atomic settings.json write, exit 2 to block.

Reads .claude/state/model-router/{terminal_id}/{session_id}/recommendation.json
If action_mode=autoswitch AND model differs:
  1. Atomic settings.json write
  2. Exit 2 to block response
TTL: 300s, fail-open
consumed: skip already-consumed recommendations
"""

import json
import os
import sys
import pathlib
from datetime import datetime, timedelta


def get_state_path(terminal_id, session_id):
    """Compute state directory path."""
    return pathlib.Path.cwd() / '.claude' / 'state' / 'model-router' / terminal_id / session_id


def load_recommendation(state_path):
    """Load recommendation state file."""
    rec_path = state_path / 'recommendation.json'
    if not rec_path.exists():
        return None
    try:
        with open(rec_path) as f:
            return json.load(f)
    except Exception:
        return None


def is_expired(rec_data, ttl=300):
    """Check if recommendation has expired."""
    written_at = rec_data.get('written_at', '')
    if not written_at:
        return True
    try:
        written_time = datetime.fromisoformat(written_at)
        age = (datetime.now() - written_time).total_seconds()
        return age > ttl
    except Exception:
        return True


def is_consumed(rec_data):
    """Check if recommendation already consumed."""
    return rec_data.get('consumed', False)


def atomic_write_settings(new_model):
    """Atomically write settings.json with new model."""
    settings_path = pathlib.Path.home() / '.claude' / 'settings.json'
    tmp = settings_path.with_suffix('.tmp')
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        settings['model'] = new_model
        with open(tmp, 'w') as f:
            json.dump(settings, f, indent=2)
        tmp.replace(settings_path)
        return True
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        return False


def mark_consumed(state_path):
    """Mark recommendation as consumed."""
    rec_path = state_path / 'recommendation.json'
    if not rec_path.exists():
        return
    try:
        with open(rec_path, 'r') as f:
            rec_data = json.load(f)
        rec_data['consumed'] = True
        tmp = rec_path.with_suffix('.tmp')
        with open(tmp, 'w') as f:
            json.dump(rec_data, f, indent=2)
        tmp.replace(rec_path)
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    terminal_id = data.get('terminal_id', 'default')
    session_id = data.get('session_id', 'default')

    state_path = get_state_path(terminal_id, session_id)

    rec_data = load_recommendation(state_path)
    if not rec_data:
        sys.exit(0)

    if is_expired(rec_data):
        sys.exit(0)

    if is_consumed(rec_data):
        sys.exit(0)

    action_mode = rec_data.get('action_mode', 'warn')
    if action_mode != 'autoswitch':
        sys.exit(0)

    recommended_model = rec_data.get('recommended_model', '')
    current_model = rec_data.get('current_model', '')

    if not recommended_model or recommended_model == current_model:
        sys.exit(0)

    base_recommended = recommended_model.split('[')[0]
    base_current = current_model.split('[')[0]

    if base_recommended == base_current:
        sys.exit(0)

    success = atomic_write_settings(recommended_model)

    mark_consumed(state_path)

    if success:
        print(f'[model-router] Auto-switched from {current_model} to {recommended_model} — press ↑ Enter to resend', file=sys.stderr)
        sys.exit(2)
    else:
        print(f'[model-router] Failed to auto-switch to {recommended_model}', file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()

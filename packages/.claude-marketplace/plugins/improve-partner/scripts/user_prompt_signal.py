#!/usr/bin/env python3
import sys, json, os, time
from pathlib import Path
plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
state_dir = plugin_root / '.state'
state_dir.mkdir(parents=True, exist_ok=True)
state_file = state_dir / 'session_signals.json'
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
state = {}
if state_file.exists():
    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
    except Exception:
        state = {}
state.setdefault('events', [])
state.setdefault('signals', {})
text = json.dumps(payload)
state['events'].append({'ts': int(time.time()), 'tool': 'UserPromptSubmit'})
for needle, key in [
    ('improve', 'improvement_intent'),
    ('review', 'improvement_intent'),
    ('what is missing', 'improvement_intent'),
    ('why is this fragile', 'improvement_intent'),
    ('hook', 'hook_context_mentioned'),
    ('plugin', 'plugin_context_mentioned'),
    ('prompt', 'prompt_context_mentioned'),
]:
    if needle.lower() in text.lower():
        state['signals'][key] = state['signals'].get(key, 0) + 1
state['event_count'] = len(state.get('events', []))
state['last_updated'] = int(time.time())
state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
print('prompt signal captured')

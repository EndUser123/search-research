#!/usr/bin/env python3
import sys, json, os, time, re, hashlib
from pathlib import Path

plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
state_dir = plugin_root / '.state'
state_dir.mkdir(parents=True, exist_ok=True)
state_file = state_dir / 'session_signals.json'

WRITE_TOOLS = {'Write', 'Edit', 'MultiEdit'}
READ_TOOLS = {'Read', 'Glob', 'Grep'}
BASH_TOOLS = {'Bash'}

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
state.setdefault('changed_files', {})
state.setdefault('read_files', {})
state.setdefault('recent_errors', [])
state.setdefault('tool_counts', {})
state.setdefault('signals', {})

now = int(time.time())
tool = payload.get('tool_name') or payload.get('tool') or payload.get('hook_event_name') or 'unknown'
tool_input = payload.get('tool_input', {}) or {}
tool_response = payload.get('tool_response', {}) or {}
transcript_path = payload.get('transcript_path') or payload.get('transcriptPath')
cwd = payload.get('cwd') or os.getcwd()

state['events'].append({
    'ts': now,
    'tool': tool,
    'cwd': cwd,
    'transcript_path': transcript_path,
})
state['tool_counts'][tool] = state['tool_counts'].get(tool, 0) + 1
if transcript_path:
    state['last_transcript_path'] = transcript_path

# Extract candidate paths from tool_input / tool_response
candidate_paths = []
for key in ['file_path', 'path', 'target_file', 'source_file']:
    v = tool_input.get(key)
    if isinstance(v, str):
        candidate_paths.append(v)
for key in ['files', 'paths']:
    v = tool_input.get(key)
    if isinstance(v, list):
        candidate_paths.extend([x for x in v if isinstance(x, str)])

# Normalize paths
norm_paths = []
for p in candidate_paths:
    pp = Path(p)
    if not pp.is_absolute():
        pp = Path(cwd) / pp
    try:
        norm_paths.append(str(pp.resolve()))
    except Exception:
        norm_paths.append(str(pp))

# Track reads/writes by tool type
for p in norm_paths:
    if tool in WRITE_TOOLS:
        entry = state['changed_files'].setdefault(p, {'count': 0, 'last_ts': 0, 'kinds': []})
        entry['count'] += 1
        entry['last_ts'] = now
        if tool not in entry['kinds']:
            entry['kinds'].append(tool)
    elif tool in READ_TOOLS:
        entry = state['read_files'].setdefault(p, {'count': 0, 'last_ts': 0})
        entry['count'] += 1
        entry['last_ts'] = now

text = json.dumps(payload)
for needle, key in [
    ('.claude/hooks/', 'hook_related'),
    ('SKILL.md', 'skill_related'),
    ('CLAUDE.md', 'claude_md_related'),
    ('settings.json', 'settings_related'),
    ('plugin.json', 'plugin_manifest_related'),
    ('timeout', 'timing_related'),
    ('latency', 'timing_related'),
    ('ThreadPoolExecutor', 'parallelism_related'),
    ('asyncio', 'parallelism_related'),
    ('assert', 'test_related'),
    ('pytest', 'test_related'),
]:
    if needle in text:
        state['signals'][key] = state['signals'].get(key, 0) + 1

# Capture errors from failed tool outputs if present
err_text = json.dumps(tool_response)
for bad in ['error', 'exception', 'traceback', 'failed']:
    if bad in err_text.lower():
        digest = hashlib.sha1(err_text[:2000].encode()).hexdigest()[:12]
        state['recent_errors'].append({'ts': now, 'digest': digest, 'tool': tool})
        break

state['event_count'] = len(state['events'])
state['last_updated'] = now
state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
print('captured')

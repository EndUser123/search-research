#!/usr/bin/env python3
import os, json, time, sys, subprocess
from pathlib import Path

plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
state_dir = plugin_root / '.state'
queue_dir = plugin_root / '.review-queue'
state_file = state_dir / 'session_signals.json'
review_meta_file = state_dir / 'review_meta.json'
config_file = plugin_root / 'config.json'
queue_dir.mkdir(parents=True, exist_ok=True)
state_dir.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    'mode': 'suggest',
    'threshold': 5,
    'cooldown_seconds': 900,
    'max_files': 12,
    'allow_force_mode': True,
    'force_only_when': {
        'explicit_mode': True,
        'safety_critical': False,
        'tests_failing_gate': False,
    },
}

try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}

cfg = DEFAULTS.copy()
if config_file.exists():
    try:
        loaded = json.loads(config_file.read_text(encoding='utf-8'))
        cfg.update({k:v for k,v in loaded.items() if k != 'force_only_when'})
        if isinstance(loaded.get('force_only_when'), dict):
            inner = DEFAULTS['force_only_when'].copy()
            inner.update(loaded['force_only_when'])
            cfg['force_only_when'] = inner
    except Exception:
        pass

if payload.get('stop_hook_active'):
    print(json.dumps({'decision':'allow','reason':'stop hook already active'}))
    sys.exit(0)
if not state_file.exists():
    print(json.dumps({'decision':'allow','reason':'no session state'}))
    sys.exit(0)

state = json.loads(state_file.read_text(encoding='utf-8'))
meta = {}
if review_meta_file.exists():
    try:
        meta = json.loads(review_meta_file.read_text(encoding='utf-8'))
    except Exception:
        meta = {}

now = int(time.time())
last_review_ts = meta.get('last_review_ts', 0)
if now - last_review_ts < int(cfg['cooldown_seconds']):
    print(json.dumps({'decision':'allow','reason':f'in cooldown ({now - last_review_ts}s < {cfg["cooldown_seconds"]}s)'}))
    sys.exit(0)

changed = state.get('changed_files', {})
read_files = state.get('read_files', {})
signals = state.get('signals', {})
errors = state.get('recent_errors', [])

score = 0
reasons = []
priority_files = []
for path, info in changed.items():
    pts = 1
    lower = path.lower()
    if '/.claude/' in lower or 'skill.md' in lower or 'claude.md' in lower:
        pts += 2
    if lower.endswith('settings.json') or lower.endswith('plugin.json') or '/hooks/' in lower:
        pts += 2
    if '/tests/' in lower or lower.endswith('_test.py') or lower.endswith('.spec.ts'):
        pts += 1
    if lower.endswith('.py') or lower.endswith('.ts') or lower.endswith('.js'):
        pts += 1
    score += min(pts, 4)
    priority_files.append((pts, path, info))
if errors:
    score += min(4, len(errors))
    reasons.append('errors or exceptions observed')
if signals.get('timing_related'):
    score += 2
    reasons.append('timing or latency signals present')
if signals.get('parallelism_related'):
    score += 1
    reasons.append('parallelism-related signals present')
if signals.get('test_related'):
    score += 1
    reasons.append('tests involved')
if state.get('event_count', 0) >= 8:
    score += 1
    reasons.append('many tool events')

if not changed and score < int(cfg['threshold']):
    print(json.dumps({'decision':'allow','reason':'no meaningful changed artifacts detected'}))
    sys.exit(0)
if score < int(cfg['threshold']):
    print(json.dumps({'decision':'allow','reason':f'score {score} below threshold {cfg["threshold"]}'}))
    sys.exit(0)

priority_files.sort(reverse=True)
selected_files = [p for _, p, _ in priority_files[:int(cfg['max_files'])]]
combined_text = []
for p in selected_files[:4]:
    try:
        combined_text.append(Path(p).read_text(encoding='utf-8', errors='replace')[:4000])
    except Exception:
        pass
classifier_path = plugin_root / 'scripts' / 'classify_domain.py'
domain_hint = {'domain':'code-workflow-review','confidence':'low','rationale':'classifier unavailable','alternative':None}
try:
    proc = subprocess.run(
        ['python3', str(classifier_path), '-'],
        input='\n\n'.join(combined_text),
        text=True,
        capture_output=True,
        timeout=8,
        check=False,
    )
    if proc.stdout.strip():
        domain_hint = json.loads(proc.stdout)
except Exception:
    pass

req = {
    'created_at': now,
    'score': score,
    'reasons': reasons,
    'domain_hint': domain_hint,
    'changed_files': selected_files,
    'read_files_sample': list(read_files.keys())[:8],
    'error_count': len(errors),
    'hook_mode': cfg['mode'],
    'mode': 'delegate-subagent',
    'suggested_command': '/improve mode=delegate-subagent',
    'notes': 'Read the changed artifacts first. Start with binding constraint. Use domain hint unless artifact evidence overrides it.',
    'raw_signals_path': str(state_file)
}
path = queue_dir / f'review-request-{req["created_at"]}.json'
path.write_text(json.dumps(req, indent=2), encoding='utf-8')
meta['last_review_ts'] = now
meta['last_review_request'] = str(path)
review_meta_file.write_text(json.dumps(meta, indent=2), encoding='utf-8')

message = (
    'Meaningful artifact change detected. Suggested next step: '
    f'run /improve using review request artifact: {path}. '
    f'Domain hint: {domain_hint.get("domain")} ({domain_hint.get("confidence")}). '
    'Read the listed changed files first, then produce the improvement review.'
)

force_mode = str(cfg.get('mode', 'suggest')).lower() == 'force' and bool(cfg.get('allow_force_mode', True))
if force_mode:
    print(json.dumps({'decision':'block','reason':message,'queued_review_request':str(path),'score':score,'domain_hint':domain_hint,'changed_files':selected_files}))
else:
    print(json.dumps({'decision':'allow','reason':message,'queued_review_request':str(path),'score':score,'domain_hint':domain_hint,'changed_files':selected_files}))

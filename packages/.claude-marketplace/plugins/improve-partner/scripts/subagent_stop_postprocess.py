#!/usr/bin/env python3
import sys, json, os, time
from pathlib import Path
plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
out_dir = plugin_root / '.subagent-results'
out_dir.mkdir(parents=True, exist_ok=True)
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
path = out_dir / f'subagent-stop-{int(time.time())}.json'
path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
print(json.dumps({'decision':'allow','saved_subagent_result':str(path)}))

---
description: Install all or specific marketplace plugins. Trigger when asked to "install plugins", "setup plugins", "plugin install", or "install marketplace plugins".
enforcement: advisory
workflow_steps:
  - Sync marketplace index
  - Detect stale and missing caches
  - Nuke stale caches
  - Reinstall from marketplace
  - Verify enabledPlugins registration
  - Reload plugins
---

# Plugin Install

Install all marketplace plugins or specific ones. Handles cache management and enabledPlugins registration.

## Usage

### Install all marketplace plugins
```bash
claude plugin marketplace update local
ls P:/packages/.claude-marketplace/plugins/
claude plugin install <name>@local
claude plugin marketplace update local
```

### Install specific plugin
```bash
claude plugin marketplace update local
claude plugin install <name>@local
claude plugin marketplace update local
```

## Full workflow (no action specified)

When invoked without a specific plugin name, run the complete check-fix-install workflow:

1. Audit all plugins for issues and auto-fix
2. Sync marketplace index
3. Detect stale + missing caches
4. Nuke stale caches
5. Reinstall from marketplace
6. Validate all plugins
7. Final sync + report

## Troubleshooting

**If install succeeds but plugin doesn't load:**
Check enabledPlugins registration:
```bash
python3 -c "
import json
from pathlib import Path
f = Path.home() / '.claude' / 'settings.json'
d = json.load(open(f))
key = '<name>@local'
if key not in d.get('enabledPlugins', {}):
    d.setdefault('enabledPlugins', {})[key] = True
    json.dump(d, open(f, 'w'), indent=2)
    print(f'FIXED: added {key} to enabledPlugins')
else:
    print(f'OK: {key} already in enabledPlugins')
"
```
Then `/reload-plugins`.
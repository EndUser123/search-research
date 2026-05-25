---
description: "Plugin structure, cache requirement, hook naming, import pattern, registration"
alwaysApply: false
---

# Plugin Development

## Structure

```
<plugin>/
  .claude-plugin/
    plugin.json          # Name, version, description, keywords
  hooks/
    hooks.json           # Hook registration (nested matcher+hooks format)
    <plugin>_<event>.py  # Namespaced hook scripts
  skills/
    <skill>/SKILL.md     # Skill definitions
  __lib/                 # Internal library (double underscore)
  CLAUDE.md              # Package-specific instructions
```

## Cache Requirement

After editing any plugin file, you MUST:
1. Bump version in `.claude-plugin/plugin.json`
2. Refresh the plugin cache (changes won't take effect without this)

## Hook Naming

All plugin hook scripts: `{plugin_name}_{EventName}.py`
Generic names collide across packages and with local hooks.

## Import Pattern

Every hook uses `_bootstrap.py` for path setup:

```python
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
```

## hooks.json Format

Must use nested `{matcher, hooks: [{type, command, timeout}]}` format.
See `packages/CLAUDE.md` for full specification.

## Marketplace

Plugins are junctioned: source at `P:/packages/<name>/`,
junction at `P:/packages/.claude-marketplace/plugins/<name>`.
Changes auto-pick up via junctions after cache refresh.

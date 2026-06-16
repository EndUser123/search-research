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

## Hook Registration (CRITICAL)

Plugin `hooks/hooks.json` has a known bug ([anthropics/claude-code#16288](https://github.com/anthropics/claude-code/issues/16288)):
it does NOT fire for non-SessionStart events because `loadPluginHooks()` is not awaited before dispatch.

**Plugin hooks MUST be registered in `settings.json`** via a router.py dispatch pattern:
`settings.json` → `router.py` → sub-hooks. The plugin `hooks.json` file should contain only `{"hooks": {}}` as a placeholder.

## Marketplace

Plugins live directly at `P:/packages/.claude-marketplace/plugins/<name>/`.
No junctions, no separate source directory. Changes to source take effect after cache refresh (version bump + `/reload-plugins`).

## hooks.json Format

If you must write to `hooks.json` (e.g., for a plugin that legitimately only uses SessionStart hooks),
use the nested `{matcher, hooks: [{type, command, timeout}]}` format.
See `packages/CLAUDE.md` for the full specification.

For all other events: use `settings.json` registration only.

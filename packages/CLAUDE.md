# packages/

Monorepo of Claude Code plugins and utility packages.

## Plugin Structure

Each plugin follows the `.claude-plugin/` convention:

```
<plugin>/
  .claude-plugin/
    plugin.json          # Name, version, description, keywords
  hooks/
    hooks.json           # Hook registration manifest (nested matcher+hooks format)
    <plugin>_<event>.py  # Hook scripts (namespaced, see below)
  skills/
    <skill>/SKILL.md     # Skill definitions
  CLAUDE.md              # Package-specific instructions
```

## Hook Naming Standard

All plugin hook scripts MUST use the `{plugin_name}_{event}.py` naming convention.

**Rule:** `hooks/<plugin_name>_<EventName>.py` or `hooks/<plugin_name>_<EventName>_<gate>.py`

**Why:** Generic names (`PreToolUse.py`, `PreCompact.py`) collide across packages AND with `P:/.claude/hooks/`. When both local settings.json and plugin hooks.json register hooks with the same filename, they fire twice. Namespacing makes ownership obvious and eliminates collisions.

**Examples:**

| Plugin | Event | Standard name |
|--------|-------|---------------|
| fact-guard | PreToolUse | `fact-guard_PreToolUse.py` |
| snapshot | PreCompact | `snapshot_PreCompact.py` |
| skill-guard | Stop | `skill-guard_Stop.py` |

**hooks.json command pattern:**
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "^(?:Edit|Write|MultiEdit)$",
      "hooks": [{
        "type": "command",
        "command": "python \"C:/Users/brsth/.claude/plugins/reason_openai/hooks/fact-guard_PreToolUse.py\"",
        "timeout": 5
      }]
    }]
  }
}
```

**When renaming an existing hook:**
1. Rename the script file
2. Update `hooks/hooks.json` command path
3. Update any sibling imports that reference the old filename
4. Update tests that assert the old filename
5. Run `plugin-audit-and-fix.py --bump <name>` to refresh cache

**Exceptions:**
- Local-only hooks in `P:/.claude/hooks/` (not in any plugin) keep their current names
- Skill-scoped hooks within `skills/{name}/hooks/` use `{skill_name}_{event}.py`
- Shared utility modules in `__lib/` are exempt (imported, not registered as hooks)

## hooks.json Format

Must use nested `{matcher, hooks: [{type, command, timeout}]}` format. See `plugin-hooks-json-format.md` in memory for details.

## Marketplace

Plugins live directly in `P:/packages/.claude-marketplace/plugins/<name>/`. After editing plugin files, bump the version and reload to propagate changes to the version-keyed cache.

## Artifacts Convention

Runtime artifacts write to `.claude/.artifacts/{terminal_id}/{skill_name}/`. Skills MUST NOT write state to their own directory or to the package root.

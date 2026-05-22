# Hook-System-to-Plugin Conversion

**Purpose**: Detect local hook systems and settings-based hook registration, migrate to canonical plugin structure.

---

## Detection Checklist

Run these checks before conversion:

### 1. Local `.claude/hooks/` Files (not in any plugin)

```bash
# Check for local hook files
ls P:\\.claude/hooks/*.py 2>/dev/null | head -20

# Filter out plugin-owned hooks (those owned by registered plugins)
# A hook is "plugin-owned" if it lives in a plugin's scripts/hooks/ directory
# and is registered via that plugin's hooks/hooks.json
```

**Detection signals**:
- `P:\\\\.claude/hooks/PreToolUse.py` (not `pluginname_PreToolUse.py`)
- `P:\\\\.claude/hooks/Stop.py` (not namespaced)
- Any `.py` file in `P:\\\\.claude/hooks/` that is not linked to a plugin

### 2. `settings.json` Hook Entries

```bash
# Check settings.json for hook registrations
python -c "
import json
settings = json.load(open('P:\\\\.claude/settings.json'))
hooks = settings.get('hooks', {})
print('Hook entries in settings.json:')
for event, entries in hooks.items():
    for entry in entries:
        cmd = entry.get('command', '')
        if 'P:\\\\' in cmd or '/.claude/hooks/' in cmd:
            print(f'  {event}: {cmd}')
"
```

**Detection signals**:
- `"command": "python P:\\\\.claude/hooks/SomeHook.py"` (local path)
- `"command": "python /Users/.../hooks/..."` (home directory path)
- `"command": "python C:/.../hooks/..."` (Windows absolute path)

### 3. Stale `core/` Directory

```bash
# Check for non-standard core/ directory
ls -la {{TARGET_DIR}}/core/ 2>/dev/null && echo "WARNING: core/ found — should be scripts/"
```

**Detection signals**:
- `{{TARGET_DIR}}/core/` directory exists (non-standard)
- `{{TARGET_DIR}}/core/hooks/` directory (non-standard)

### 4. Hardcoded Path Scan

```bash
# Scan Python files for hardcoded paths
python -c "
import os, re
from pathlib import Path
HARDCODE_PATTERNS = [
    r'P:\\\\\\\\',
    r'P:\\\\',
    r'C:\\\\\\\\',
    r'C:\\\\',
    r'/Users/',
    r'/home/',
    r'~'
]
found = []
for py in Path('{{TARGET_DIR}}').rglob('*.py'):
    if '__pycache__' in str(py): continue
    try:
        content = open(py, 'r', encoding='utf-8').read()
        for pat in HARDCODE_PATTERNS:
            if re.search(pat, content):
                found.append(str(py))
                break
    except: pass
if found:
    print('Hardcoded paths found:')
    for f in found: print(f'  {f}')
else:
    print('No hardcoded paths found')
"
```

---

## Canonical Migration Target

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Minimal manifest
├── hooks/
│   └── hooks.json            # Hook registration (NOT Python files)
├── scripts/
│   ├── __init__.py
│   └── hooks/
│       ├── __init__.py
│       ├── pluginname_PreToolUse.py
│       └── pluginname_Stop.py
├── skills/
│   └── skill-name/
│       └── SKILL.md
├── README.md
├── LICENSE
└── .gitignore
```

**Rule**: All Python code lives in `scripts/`. Hook implementations live in `scripts/hooks/`. Only `hooks/hooks.json` (registration) lives in `hooks/`.

---

## Conversion Workflow

### Step 1: Create Plugin Structure

```bash
mkdir -p {{TARGET_DIR}}/.claude-plugin
mkdir -p {{TARGET_DIR}}/scripts/hooks
mkdir -p {{TARGET_DIR}}/hooks
```

### Step 2: Create `plugin.json`

```json
{
  "name": "{{plugin_name}}",
  "description": "{{description}}",
  "author": {
    "name": "{{author_name}}"
  }
}
```

### Step 3: Create `hooks/hooks.json`

```json
{
  "{{hook_event}}": [{
    "matcher": "{{matcher_regex}}",
    "hooks": [{
      "type": "command",
      "command": "python \"$CLAUDE_PLUGIN_ROOT/scripts/hooks/{{plugin_name}}_{{hook_event}}.py\""
    }]
  }]
}
```

### Step 4: Move Hook Files

```bash
# Rename and move hook files
mv P:\\.claude/hooks/PreToolUse.py {{TARGET_DIR}}/scripts/hooks/{{plugin_name}}_PreToolUse.py

# Update file content to remove hardcoded paths
# Replace P:\\.claude/hooks/ with $CLAUDE_PLUGIN_ROOT/scripts/hooks/
```

### Step 5: Update `settings.json`

Remove hook entries that point to local `.claude/hooks/` files. They are now owned by the plugin.

```bash
# Show what to remove from settings.json
python -c "
import json
settings = json.load(open('P:\\\\.claude/settings.json'))
hooks = settings.get('hooks', {})
for event, entries in hooks.items():
    for entry in entries:
        cmd = entry.get('command', '')
        if '/.claude/hooks/' in cmd and 'scripts/hooks' not in cmd:
            print(f'Remove: {event} -> {cmd}')
"
```

### Step 6: Create Junction (Dev Deployment)

```bash
# Windows: Create junction for hooks
cmd /c "mklink {{plugin_name}}_PreToolUse.py P:\\\\\\packages\\{{plugin_name}}\\scripts\\hooks\\{{plugin_name}}_PreToolUse.py"
```

---

## Exception Cases

### Local-Only Hooks (Not in Any Plugin)

Hooks in `P:\\\\.claude/hooks/` that have no associated plugin are **local hooks**. These are NOT migrated — they remain in place but should be namespaced:

```
P:\\\\.claude/hooks/
├── local_PreToolUse.py    # Renamed from PreToolUse.py
├── local_Stop.py          # Renamed from Stop.py
```

### Brownfield Plugins

Existing plugins with `core/` directories should be migrated to `scripts/`:

```bash
# Migrate core/ to scripts/
mv {{TARGET_DIR}}/core/* {{TARGET_DIR}}/scripts/
rmdir {{TARGET_DIR}}/core
```

### Settings-Based Registration with Hardcoded Paths

If `settings.json` has `"command": "python P:\\\\.claude/hooks/SomeHook.py"`, convert to plugin-owned hook and update settings to remove the entry (plugin will register via its own `hooks/hooks.json`).

---

## Verification

After conversion:

1. **Hook fires correctly** — Run the hook trigger scenario and verify behavior is preserved
2. **No duplicate firing** — Ensure the hook is not registered in both `settings.json` AND `hooks/hooks.json`
3. **Path portability** — Verify hook uses `${CLAUDE_PLUGIN_ROOT}`, not hardcoded paths
4. **Plugin loads** — `python scripts/hooks/{{plugin_name}}_{{hook_event}}.py --version` works

---

## Reference

- **Plugin standards**: `resources/PLUGIN_STANDARDS.md`
- **Path portability**: `${CLAUDE_PLUGIN_ROOT}` — see `references/plugin-environment.md`
- **Hook naming**: `{plugin_name}_{event}.py` — prevents collision with local hooks
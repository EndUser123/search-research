---
description: Manage development plugins — audit, validate, install, sync, add, remove, refresh, bump, status. Trigger when asked to "setup plugins", "install plugins", "audit plugins", "validate plugin manifests", "add plugin to marketplace", "remove plugin from marketplace", or "check plugin status".
enforcement: advisory
workflow_steps:
  - Route to appropriate plugin-installer sub-skill (/audit, /validate, /install, /sync, /add, /remove, /refresh, /bump, /status)
  - Sub-skills handle execution
  - Report results
---

# Claude Code Plugin Manager

Manage, audit, validate, install, and sync all development plugins.

## Marketplace Architecture

All plugins are junctioned — source at `P:/packages/<name>/`, junction at `P:/packages/.claude-marketplace/plugins/<name>`. Changes to source auto-pick up — no sync needed.

## Full Setup (no action specified)

When invoked without an action, run the complete check-fix-install workflow. **All steps are mandatory — do not skip step 3 (cache sync check) even if steps 1 and 2 look clean.**

1. **Audit** all plugins for issues and auto-fix:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
   ```

2. **Sync marketplace index**:
   ```bash
   claude plugin marketplace update local
   ```

3. **⚠️ MANDATORY — Detect stale + missing caches** — compare source plugin.json version against installed cache version. **This is the most commonly skipped step and the most common source of "plugin installed but not loading" bugs.** Run this even when steps 1 and 2 report clean:
   ```bash
   python3 -c "
   import json
   from pathlib import Path

   installed = json.load(open('C:/Users/brsth/.claude/plugins/installed_plugins.json'))
   marketplace = Path('P:/packages/.claude-marketplace/plugins')
   stale, missing = [], []

   for plugin_dir in sorted(marketplace.iterdir()):
       name = plugin_dir.name
       if name.startswith('.') or not (plugin_dir / '.claude-plugin' / 'plugin.json').exists():
           continue
       src_ver = json.load(open(plugin_dir / '.claude-plugin' / 'plugin.json')).get('version', '?')
       entry = installed.get('plugins', {}).get(f'{name}@local')
       if not entry:
           missing.append((name, src_ver))
           continue
       cache_ver = entry[0].get('version', '?')
       if cache_ver != src_ver:
           stale.append((name, cache_ver, src_ver))

   if stale:
       print('STALE CACHES:')
       for name, cv, sv in stale:
           print(f'  {name}: cache v{cv} != source v{sv}')
   else:
       print('No stale caches.')

   if missing:
       print('NOT INSTALLED:')
       for name, sv in missing:
           print(f'  {name}: source v{sv}')
   else:
       print('All marketplace plugins installed.')

   print(f'Summary: {len(stale)} stale, {len(missing)} missing')
   "
   ```

4. **Nuke stale caches** — for each plugin where cache version != source version:
   ```bash
   # For each stale plugin:
   rm -rf "C:/Users/brsth/.claude/plugins/cache/local/<name>"
   # Remove stale entry from installed_plugins.json:
   python3 -c "
   import json
   f = 'C:/Users/brsth/.claude/plugins/installed_plugins.json'
   d = json.load(open(f))
   for name in [<stale_names>]:
       d['plugins'].pop(f'{name}@local', None)
   json.dump(d, open(f, 'w'), indent=2)
   "
   ```

5. **Reinstall all plugins** — covers both stale (nuked) and missing.
   Try `claude plugin install` first. If it fails with "source type not supported" (directory-source marketplaces in v2.1.126), fall back to Direct Registration:
   ```bash
   claude plugin marketplace update local
   ls P:/packages/.claude-marketplace/plugins/
   # For each missing/stale plugin:
   claude plugin install <name>@local
   ```
   **If install fails** (directory source not supported), use Direct Registration fallback for each failed plugin:
   ```bash
   python3 << 'PYEOF'
   import json, shutil
   from pathlib import Path
   from datetime import datetime, timezone

   plugins_to_install = ["<name>"]  # fill with failed plugin names
   cache_root = Path("C:/Users/brsth/.claude/plugins/cache/local")
   installed_file = Path("C:/Users/brsth/.claude/plugins/installed_plugins.json")
   settings_file = Path("C:/Users/brsth/.claude/settings.json")

   src_ver = json.load(open(f"P:/packages/{plugins_to_install[0]}/.claude-plugin/plugin.json")).get("version", "1.0.0")
   d = json.load(open(installed_file))
   now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

   for name in plugins_to_install:
       src = Path(f"P:/packages/{name}")
       ver = json.load(open(src / ".claude-plugin" / "plugin.json")).get("version", "1.0.0")
       dst = cache_root / name / ver
       if dst.exists():
           shutil.rmtree(dst)
       shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))
       d["plugins"][f"{name}@local"] = [{
           "scope": "user",
           "installPath": str(dst),
           "version": ver,
           "installedAt": now,
           "lastUpdated": now,
       }]
       print(f"Installed {name} v{ver} -> {dst}")

   json.dump(d, open(installed_file, "w"), indent=2)

   # Ensure enabledPlugins
   s = json.load(open(settings_file))
   for name in plugins_to_install:
       key = f"{name}@local"
       s.setdefault("enabledPlugins", {})[key] = True
   json.dump(s, open(settings_file, "w"), indent=2)
   print("Done. Run /reload-plugins.")
   PYEOF
   ```

6. **Validate** all plugins:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
   ```

7. **Final sync + report**:
   ```bash
   claude plugin marketplace update local
   claude plugin list
   ```
   ⚠️ **Then type `/reload-plugins` manually**.

## Actions

### `/plugin-installer audit [name]` — Audit plugin manifests

With no argument, audits all plugins:
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
```

With a plugin name, audits only that plugin:
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace" --plugins <name>
```

Then refresh:
```bash
claude plugin marketplace update local
```
⚠️ **Then type `/reload-plugins` manually**.

### `/plugin-installer validate [name]` — Validate plugins

With no argument, validates all:
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
```

With a plugin name, validates only that plugin:
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace" --plugins <name>
```

### `/plugin-installer install` — Install all marketplace plugins

```bash
claude plugin marketplace update local
ls P:/packages/.claude-marketplace/plugins/
# For each plugin, check entry type before install:
# - Junction → source auto-pickup, safe to install
# - Real dir → warn: non-junction plugin, source changes won't auto-propagate
#   If source exists at P:/packages/<name>/, suggest converting to junction instead
claude plugin install <name>@local
claude plugin marketplace update local
```
⚠️ **After each install, type `/reload-plugins` manually**, then:
```bash
claude plugin list
```

**Non-junction detection:** If a marketplace entry is a real directory AND the source exists at `P:/packages/<name>/`, the plugin should be a junction instead. Flag it and suggest:
```bash
# Convert real-dir to junction:
rm -rf P:/packages/.claude-marketplace/plugins/<name>
cmd /c mklink /J "P:\\packages\\.claude-marketplace\\plugins\\<name>" "P:\\packages\\<name>"
```

### `/plugin-installer sync` — Sync plugin-installer source to marketplace

plugin-installer should be a **junction** (not a real dir). If it is a real directory, convert it first:

```bash
# Check current type
test -L P:/packages/.claude-marketplace/plugins/plugin-installer && echo "junction" || echo "real-dir"
# If real-dir: convert to junction
rm -rf P:/packages/.claude-marketplace/plugins/plugin-installer
cmd /c mklink /J "P:\\packages\\.claude-marketplace\\plugins\\plugin-installer" "P:\\packages\\plugin-installer"
```

plugin-installer is now a junction — source changes auto-pick up, no manual sync needed. The cp block below is kept only for migrating from the old real-dir setup.

```bash
# Only needed if you previously used sync with a real-dir plugin-installer
# Source is now a junction, so changes propagate automatically
```

### `/plugin-installer add <name>` — Add a plugin to marketplace

**Check before creating a junction:**
1. Check if entry already exists: `ls -la P:/packages/.claude-marketplace/plugins/<name>`
2. If it's a junction → plugin already in marketplace, skip creation
3. If it's a real directory → warn user, junction would conflict
4. If no entry exists → ask user before creating junction

Adds a plugin via junction. Assumes source at `P:/packages/<name>/`:

```bash
cmd /c mklink /J "P:\\packages\\.claude-marketplace\\plugins\\<name>" "P:\\packages\\<name>"
claude plugin marketplace update local
claude plugin install <name>@local
claude plugin list
```
⚠️ **After install, type `/reload-plugins` manually**.

### `/plugin-installer remove <name>` — Remove a plugin from marketplace

Removes the junction from marketplace and uninstalls the plugin. Does NOT delete the source.

**Check first:** `ls -la P:/packages/.claude-marketplace/plugins/<name>` to confirm it's a junction (not a real directory).

```bash
cmd /c rmdir "P:\\packages\\.claude-marketplace\\plugins\\<name>"
claude plugin uninstall <name>@local
claude plugin marketplace update local
claude plugin list
```
⚠️ **After uninstall, type `/reload-plugins` manually**.

### `/plugin-installer status` — Check plugin status

```bash
claude plugin list
```

### `/plugin-installer refresh [name]` — Nuke stale cache and reinstall

Fixes the common issue where source edits don't appear in the running session because the plugin loads from a version-keyed cache, not source. The official Claude Code docs recommend clearing the cache and reinstalling.

**With a plugin name** — targeted nuke (preferred):
```bash
# 1. Remove stale cache for this plugin only
rm -rf "C:/Users/brsth/.claude/plugins/cache/local/<name>"

# 2. Remove from installed_plugins.json
python3 -c "
import json
f = 'C:/Users/brsth/.claude/plugins/installed_plugins.json'
d = json.load(open(f))
d['plugins'].pop('<name>@local', None)
json.dump(d, open(f, 'w'), indent=2)
"

# 3. Sync marketplace + reinstall
claude plugin marketplace update local
claude plugin install <name>@local
claude plugin marketplace update local

# 4. Verify enabledPlugins registration (critical — install silently skips this for some plugins)
python3 -c "
import json
f = 'C:/Users/brsth/.claude/settings.json'
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
⚠️ **After install, type `/reload-plugins` manually**.

**With no argument** — nuke all local plugin caches:
```bash
rm -rf "C:/Users/brsth/.claude/plugins/cache/local"
claude plugin marketplace update local
# Then reinstall each plugin:
ls P:/packages/.claude-marketplace/plugins/
claude plugin install <name>@local
```
⚠️ **After each install, type `/reload-plugins` manually**.

**When to use** (vs `bump`):
- `bump` — source files changed, want a clean new version dir. Keeps old cache.
- `refresh` — cache is corrupted, stale, or mismatched. Nukes and reinstalls from marketplace.
- If `bump` + `/reload-plugins` doesn't pick up changes, use `refresh`.

### `/plugin-installer bump <name>` — Bump plugin version

Bumps the patch version (e.g., `2.0.0` → `2.0.1`) in all three files that the plugin cache system reads:

```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --bump <name> --marketplace-root "P:/packages/.claude-marketplace"
```

After bumping, run:
1. `/plugin marketplace update local`
2. `/reload-plugins`

**When to use**: After editing any plugin source files under `P:/packages/<name>/` that should propagate to the running session. The plugin system loads from version-keyed cache, not source — without a version bump, changes are invisible.

## Troubleshooting

**If install succeeds but plugin doesn't load:**
`/plugin install` may silently fail to register the plugin in `enabledPlugins` in settings.json. Verify and fix:
```bash
python3 -c "
import json
f = 'C:/Users/brsth/.claude/settings.json'
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
Then `/reload-plugins`. This is the most common cause of "plugin installed but not loading."

**If install fails:**
1. Run `claude plugin marketplace update local` then type `/reload-plugins`
2. Validate the specific plugin: `claude plugin validate <path>`
3. Re-run audit: `/plugin-installer audit`

**To uninstall all marketplace plugins:**
```bash
# Discover what's installed:
claude plugin list
# Uninstall each:
claude plugin uninstall <name>@local
claude plugin marketplace update local
```
⚠️ **After uninstall, type `/reload-plugins` manually**.

**To add a new plugin to the marketplace:**
```bash
/plugin-installer add <plugin-name>
```

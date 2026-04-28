---
description: Manage development plugins (audit, validate, install, sync, add, remove, status)
enforcement: advisory
workflow_steps:
  - name: audit
    trigger: "/plugin-installer audit"
    description: "Runs plugin-audit-and-fix.py to scan and auto-fix manifest issues"
  - name: validate
    trigger: "/plugin-installer validate"
    description: "Runs claude plugin validate on each plugin"
  - name: install
    trigger: "/plugin-installer install"
    description: "Installs all marketplace plugins"
  - name: sync
    trigger: "/plugin-installer sync"
    description: "Syncs plugin-installer source changes to marketplace"
  - name: add
    trigger: "/plugin-installer add"
    description: "Adds a new plugin to the marketplace with a junction"
  - name: remove
    trigger: "/plugin-installer remove"
    description: "Removes a plugin junction from marketplace and uninstalls it"
  - name: status
    trigger: "/plugin-installer status"
    description: "Lists installed plugins and shows version info"
arguments:
  action:
    description: 'audit, validate, install, sync, add, remove, or status'
    type: string
    enum:
      - audit
      - validate
      - install
      - sync
      - add
      - remove
      - status
---

# Claude Code Plugin Manager

Manage, audit, validate, install, and sync all development plugins.

## Marketplace Architecture

All plugins are junctioned — source at `P:/packages/<name>/`, junction at `P:/packages/.claude-marketplace/plugins/<name>`. Changes to source auto-pick up — no sync needed.

## Full Setup (no action specified)

When invoked without an action, run the complete plugin setup workflow in order:

1. **Audit** all plugins for issues and auto-fix:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
   ```
   *Audit modifies source files. Since marketplace entries are junctions to source, the marketplace plugin folders update automatically.*

2. **Sync the JSON index to the updated plugin folders**, then **reload**:
   ```bash
   claude plugin marketplace update local
   ```
   ⚠️ **Then type `/reload-plugins` manually** — this slash command cannot be run via bash.

3. **Validate** all plugins:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
   ```

4. **Pre-install sync**, then **reload**:
   ```bash
   claude plugin marketplace update local
   ```
   ⚠️ **Then type `/reload-plugins` manually**.

5. **Discover** marketplace plugins, then **install each**:
   ```bash
   ls P:/packages/.claude-marketplace/plugins/
   # For each plugin in marketplace/plugins/:
   claude plugin install <name>@local
   ```

6. **Final sync + reload**, then **report status**:
   ```bash
   claude plugin marketplace update local
   ```
   ⚠️ **Then type `/reload-plugins` manually**, then:
   ```bash
   claude plugin list
   ```

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

## Troubleshooting

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

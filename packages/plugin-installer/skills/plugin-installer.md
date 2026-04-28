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

- **Junctioned plugins** (cc-skills-*, snapshot): Source at `P:/packages/<name>/`, junction at `P:/packages/.claude-marketplace/plugins/<name>`. Changes to source auto-pick up — no sync needed.
- **Real-dir plugin** (plugin-installer): Source and marketplace are separate copies. After editing source, run `/plugin-installer sync`.

## Full Setup (no action specified)

When invoked without an action, run the complete plugin setup workflow in order:

1. **Sync** plugin-installer source to marketplace:
   ```bash
   cp -r P:/packages/plugin-installer/skills/plugin-installer.md P:/packages/.claude-marketplace/plugins/plugin-installer/skills/
   cp -r P:/packages/plugin-installer/scripts/ P:/packages/.claude-marketplace/plugins/plugin-installer/
   /plugin marketplace update local
   /reload-plugins
   ```

2. **Audit** all plugins for issues and auto-fix:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
   /plugin marketplace update local
   /reload-plugins
   ```

3. **Validate** all plugins:
   ```bash
   python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
   ```

4. **Discover** marketplace plugins:
   ```bash
   ls P:/packages/.claude-marketplace/plugins/
   ```

5. **Install** each plugin:
   ```bash
   # For each plugin in marketplace/plugins/:
   /plugin install <name>@local
   /plugin marketplace update local
   /reload-plugins
   ```

6. Report final status with:
   ```bash
   /plugin list
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
/plugin marketplace update local
/reload-plugins
```

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
/plugin marketplace update local
/reload-plugins
ls P:/packages/.claude-marketplace/plugins/
# Install each discovered plugin:
/plugin install <name>@local
/plugin marketplace update local
/reload-plugins
/plugin list
```

### `/plugin-installer sync` — Sync plugin-installer source to marketplace

plugin-installer is a real directory (not a junction), so edits to source do not auto-propagate. Run after editing source:

```bash
cp -r P:/packages/plugin-installer/skills/plugin-installer.md P:/packages/.claude-marketplace/plugins/plugin-installer/skills/
cp -r P:/packages/plugin-installer/scripts/ P:/packages/.claude-marketplace/plugins/plugin-installer/
/plugin marketplace update local
/reload-plugins
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
/plugin marketplace update local
/reload-plugins
/plugin install <name>@local
/plugin list
```

### `/plugin-installer remove <name>` — Remove a plugin from marketplace

Removes the junction from marketplace and uninstalls the plugin. Does NOT delete the source.

**Check first:** `ls -la P:/packages/.claude-marketplace/plugins/<name>` to confirm it's a junction (not a real directory).

```bash
cmd /c rmdir "P:\\packages\\.claude-marketplace\\plugins\\<name>"
/plugin uninstall <name>@local
/plugin marketplace update local
/reload-plugins
/plugin list
```

### `/plugin-installer status` — Check plugin status

```bash
/plugin list
```

## Troubleshooting

**plugin-installer changes not picking up?**
plugin-installer is a real directory in marketplace (not a junction). After editing source, run:
```bash
/plugin-installer sync
```

**If install fails:**
1. Run `/plugin marketplace update local` then `/reload-plugins`
2. Validate the specific plugin: `/plugin-installer validate <name>`
3. Re-run audit: `/plugin-installer audit`

**To uninstall all marketplace plugins:**
```bash
# Discover what's installed:
/plugin list
# Uninstall each:
/plugin uninstall <name>@local
/plugin marketplace update local
/reload-plugins
```

**To add a new plugin to the marketplace:**
```bash
/plugin-installer add <plugin-name>
```

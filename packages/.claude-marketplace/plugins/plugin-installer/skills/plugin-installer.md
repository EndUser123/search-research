---
description: Manage development plugins (audit, validate, install, sync, add, status)
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
  - name: status
    trigger: "/plugin-installer status"
    description: "Lists installed plugins and shows version info"
arguments:
  action:
    description: 'audit, validate, install, sync, add, or status'
    type: string
    enum:
      - audit
      - validate
      - install
      - sync
      - add
      - status
---

# Claude Code Plugin Manager

Manage, audit, validate, install, and sync all development plugins.

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

### `/plugin-installer audit` — Audit and auto-fix plugin manifests

```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
```

Then refresh:
```bash
/plugin marketplace update local
/reload-plugins
```

### `/plugin-installer validate` — Validate all plugins

```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
```

### `/plugin-installer install` — Install all marketplace plugins

```bash
/plugin marketplace update local
/reload-plugins
# Discover plugins:
ls P:/packages/.claude-marketplace/plugins/
# Install each:
/plugin install <name>@local
/plugin marketplace update local
/reload-plugins
/plugin list
```

### `/plugin-installer sync` — Sync plugin-installer source to marketplace

plugin-installer source is at `P:/packages/plugin-installer/` (real dir, not a junction). Run after editing source:

```bash
cp -r P:/packages/plugin-installer/skills/plugin-installer.md P:/packages/.claude-marketplace/plugins/plugin-installer/skills/
cp -r P:/packages/plugin-installer/scripts/ P:/packages/.claude-marketplace/plugins/plugin-installer/
/plugin marketplace update local
/reload-plugins
```

### `/plugin-installer add <name>` — Add a new plugin to marketplace

**Check first** — before creating a junction:
1. Check if one already exists: `ls -la P:/packages/.claude-marketplace/plugins/<name>`
2. If it already exists as a junction, inform the user and skip creation
3. If it exists as a real directory, warn the user — a junction would conflict
4. If it does not exist, ask the user whether to create a junction before proceeding

Adds a plugin via junction. Assumes source at `P:/packages/<name>/`:

```bash
cmd /c mklink /J "P:\\packages\\.claude-marketplace\\plugins\\<name>" "P:\\packages\\<name>"
/plugin marketplace update local
/reload-plugins
/plugin install <name>@local
/plugin list
```

### `/plugin-installer status` — Check plugin status

```bash
/plugin list
```

## Plugins

| Plugin | Purpose |
|--------|---------|
| cc-skills-ai-api | Multi-provider LLM access |
| cc-skills-ai-cli | Command-line AI skills |
| cc-skills-media | Media processing |
| cc-skills-meta | Metadata extraction |
| cc-skills-sdlc | Software development lifecycle |
| cc-skills-utils | Utilities and helpers |
| snapshot | Session handoff documentation |

## Troubleshooting

**plugin-installer changes not picking up?**
plugin-installer source is a real directory in the marketplace (not a junction). After editing source, run:
```bash
/plugin-installer sync
```

**If install fails:**
1. Run `/plugin marketplace update local` then `/reload-plugins`
2. Validate manually: `claude plugin validate P:\packages\.claude-marketplace\plugins\<name>`
3. Re-run audit: `/plugin-installer audit`

**To uninstall and reinstall:**
```bash
for plugin in cc-skills-ai-api cc-skills-ai-cli cc-skills-media cc-skills-meta cc-skills-sdlc cc-skills-utils snapshot; do
  /plugin uninstall $plugin
done
/plugin marketplace update local
/reload-plugins
/plugin-installer install
```

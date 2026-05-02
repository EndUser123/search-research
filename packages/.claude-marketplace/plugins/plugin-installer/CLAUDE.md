# plugin-installer

Manage, audit, validate, install, and sync all development plugins.

## Skills (3)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `audit` | `/plugin-installer:audit` | Scan and auto-fix manifest issues |
| `validate` | `/plugin-installer:validate` | Validate plugin structure and compliance |
| `install` | `/plugin-installer:install` | Install/reinstall marketplace plugins |

## Structure

```
plugin-installer/
├── .claude-plugin/plugin.json   # Plugin manifest
├── commands/                     # (empty)
├── hooks/hooks.json              # Hook definitions
├── scripts/
│   └── plugin-audit-and-fix.py   # Audit/validate/bump script
└── skills/
    ├── audit/SKILL.md            # Standalone audit
    ├── validate/SKILL.md          # Standalone validate
    └── install/SKILL.md           # Standalone install
```

## Notes

- All skills are namespaced (`plugin-installer:<name>`) — use the full name to invoke
- Junction at `P:/packages/.claude-marketplace/plugins/plugin-installer`
- Source changes auto-propagate; no manual sync needed
- After install/uninstall: run `/plugin marketplace update local` then `/reload-plugins`
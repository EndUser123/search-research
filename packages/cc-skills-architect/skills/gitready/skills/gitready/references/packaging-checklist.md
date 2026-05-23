# Packaging Checklist

Reference for validating plugin bundle readiness. Used by PHASE 11.

---

## Always Included

These files MUST be present in every plugin:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # REQUIRED: name field at minimum
├── README.md              # REQUIRED: portfolio-quality docs
├── LICENSE                # REQUIRED: MIT recommended
└── .gitignore             # RECOMMENDED: excludes .local.md, temp files
```

---

## Bundle Contents (For Distribution)

### Required for All Plugins

| File/Dir | Reason |
|----------|--------|
| `.claude-plugin/plugin.json` | Plugin manifest |
| `README.md` | User-facing documentation |
| `LICENSE` | Legal distribution rights |

### Conditionally Included

| File/Dir | Condition | Reason |
|----------|-----------|--------|
| `hooks/hooks.json` | Plugin has hooks | Hook registration manifest |
| `scripts/` | Plugin has Python code | All Python code lives here |
| `commands/` | Plugin has slash commands | Command definitions |
| `agents/` | Plugin has subagents | Agent definitions |
| `skills/` | Plugin has skills | Skill definitions |
| `.mcp.json` | Plugin has MCP servers | Server configuration |
| `AGENTS.md` | Agent complexity warrants AI-maintained docs | Reference for agents |
| `CHANGELOG.md` | Version history | Change tracking |

### Never Included in Bundle (Excluded)

| Pattern | Reason |
|---------|--------|
| `pyproject.toml` | Plugins are not pip packages |
| `setup.py`, `setup.cfg` | Plugins use `.claude-plugin/` not distutils |
| `__pycache__/` | Python bytecode cache |
| `*.pyc`, `*.pyo` | Compiled Python files |
| `.pytest_cache/` | Test artifacts |
| `.ruff_cache/` | Linter artifacts |
| `.mypy_cache/` | Type checker artifacts |
| `.git/` | Version control data |
| `dist/`, `build/` | Build output |
| `*.egg-info/` | Package metadata |
| `.env`, `.env.*` | Environment secrets |
| `*.log` | Log files |
| `.coverage`, `coverage.json` | Coverage reports |
| `*.backup`, `*.old`, `*.bak` | Backup files |
| `README_NEW.md` | Draft files |
| `*_STRUCTURE.md`, `*_AUDIT*.md` | Historical architecture docs |
| `*_VALIDATION*.md`, `*_DATA*.md` | Historical validation docs |
| `*_IMPLEMENTATION*.md`, `*_PHASE*.md` | Phase documentation |
| `*_BREAKFIX*.md`, `*_FIX*.md` | Fix documentation |
| `*SUMMARY*.md`, `*REPORT*.md` | Report documents |
| `*CHECKLIST*.md` | Checklist documents |
| `*_TREE.txt` | Diagnostic tree output |

### Internal Dev-Only Files (Do Not Ship)

```
docs/                      # Developer documentation (not user-facing)
tests/                     # Test suite (may be included for source plugins)
.local.md                  # Personal notes
.playwright/              # E2E test artifacts
```

---

## Manifest Requirements

### Minimal `plugin.json`

```json
{
  "name": "plugin-name"
}
```

### Recommended Full `plugin.json`

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief explanation of plugin purpose",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/user/plugin-name",
  "license": "MIT",
  "keywords": ["testing", "automation"]
}
```

---

## Path Portability Rules

**Required**: All path references in Python files MUST use `${CLAUDE_PLUGIN_ROOT}`.

**Forbidden patterns**:
```python
# WRONG
path = "P:/packages/my-plugin/scripts"
path = "C:\\Users\\brsth\\.claude\hooks"
path = "/Users/brsth/.claude/skills"
path = "~/plugins/..."

# CORRECT
path = "${CLAUDE_PLUGIN_ROOT}/scripts/hooks"
```

---

## Bundle Creation

```bash
# Create distributable bundle (tarball or zip)
# Exclude everything in "Never Included" and "Internal Dev-Only"

# Example using PowerShell
Compress-Archive -Path ".\.claude-plugin",".\scripts",".\hooks",".\README.md",".\LICENSE" -DestinationPath "plugin-name.zip"

# Or using tar
tar --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='*.log' \
    -czf plugin-name.tar.gz \
    .claude-plugin scripts hooks README.md LICENSE
```

---

## Validation Checklist

Run before publishing:

- [ ] `.claude-plugin/plugin.json` exists with `name` field
- [ ] README.md exists with badges, installation instructions
- [ ] LICENSE file present (MIT recommended)
- [ ] No `pyproject.toml`, `setup.py`, or `setup.cfg`
- [ ] No `core/` directory (use `scripts/` instead)
- [ ] Python files use `${CLAUDE_PLUGIN_ROOT}` for all path references
- [ ] `hooks/hooks.json` uses correct nested format (if hooks exist)
- [ ] No `__pycache__`, `.pytest_cache`, `.ruff_cache` in bundle
- [ ] No `.git/` directory in bundle
- [ ] No hardcoded `P:/`, `C:/`, `/Users/`, `~` paths
- [ ] Hook scripts named `{plugin_name}_{event}.py` (not generic names)

---

## CI Validation

Run via `python scripts/validate_plugin_bundle.py`:

```bash
# All checks
python scripts/validate_plugin_bundle.py --all {{TARGET_DIR}}

# Individual checks
python scripts/validate_plugin_bundle.py --check-manifest {{TARGET_DIR}}
python scripts/validate_plugin_bundle.py --check-paths {{TARGET_DIR}}
python scripts/validate_plugin_bundle.py --check-bundle {{TARGET_DIR}}
python scripts/validate_plugin_bundle.py --smoke-test {{TARGET_DIR}}

# Auto-fix where possible
python scripts/validate_plugin_bundle.py --fix {{TARGET_DIR}}
```

---

## References

- Plugin standards: `resources/PLUGIN_STANDARDS.md`
- PHASE 11: `resources/phases/PHASE-11-packaging-readiness.md`
- Hook system conversion: `references/hook-system-conversion.md`
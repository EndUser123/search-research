# Damage Control Hooks

**PreToolUse security hooks that block destructive operations before execution.**

---

## Overview

Damage control hooks intercept tool invocations and block dangerous operations before they execute:

- **Destructive commands**: `rm -rf`, PowerShell deletions, dangerous patterns
- **Protected paths**: Zero-access files, read-only directories, no-delete zones
- **Exit codes**: 0 = ALLOW, 2 = BLOCK, JSON = ASK (confirmation prompt)

**Result:** The command that caused 158MB data loss (`rm -rf P:/projects/kg_builder/`) is now BLOCKED.

---

## Quick Start

### Files

| File | Purpose |
|------|---------|
| `bash-tool-damage-control.py` | Blocks dangerous Bash commands |
| `edit-tool-damage-control.py` | Blocks edits to protected paths |
| `write-tool-damage-control.py` | Blocks writes to protected paths |
| `patterns.yaml` | Active pattern set (generated from upstream + overlay) |
| `patterns.upstream.yaml` | Upstream snapshot (97 patterns) |
| `patterns.overlay.yaml` | CSF/Windows additions (28 patterns) |
| `merge-patterns.py` | Regenerate patterns.yaml from upstream + overlay |
| `test-damage-control.py` | Test runner |

### Testing

```bash
# Test CLI mode
uv run P:/.claude/hooks/damage-control/test-damage-control.py bash Bash "rm -rf /tmp" --expect-blocked

# Test safe command
uv run P:/.claude/hooks/damage-control/test-damage-control.py bash Bash "ls -la /tmp" --expect-allowed
```

---

## Configuration

### Pattern Sources

**patterns.yaml** is generated from two sources:

1. **patterns.upstream.yaml** (97 patterns from upstream repo)
   - Unix destructive commands (`rm -rf`, `dd`, etc.)
   - Git destructive operations (`git reset --hard`, `git clean -fd`)
   - SQL destructive (`DELETE`, `DROP` without WHERE)
   - System-level commands (`mkfs`, `format`)

2. **patterns.overlay.yaml** (28 CSF-specific additions)
   - Windows PowerShell (`Remove-Item -Recurse`, `rd /s`)
   - Windows cmd.exe (`del /s`, `erase`)
   - Windows permissions (`icacls`, `takeown`)
   - Windows registry (`reg delete HKLM`)

### Regenerating patterns.yaml

```bash
# Check if patterns.yaml is up to date
uv run P:/.claude/hooks/damage-control/merge-patterns.py --check

# Regenerate from upstream + overlay
uv run P:/.claude/hooks/damage-control/merge-patterns.py --base patterns.upstream.yaml --write
```

### Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `DAMAGE_CONTROL_ASK_MODE` | `ask` / `block` | `block` | If `ask`, prompts for confirmation on ask-pattern commands |

---

## Protected Paths

### zeroAccessPaths (37 entries)
**No operations allowed** - blocks all access including reads

| Pattern Type | Examples |
|--------------|----------|
| Environment files | `.env`, `.env.*`, `*.env` |
| Private keys | `*.pem`, `*.key`, `id_rsa`, `id_ed25519` |
| Credentials | `credentials.json`, `secrets.yaml`, `serviceAccountKey.json` |
| SSH directories | `~/.ssh/`, `~/.aws/credentials` |

### readOnlyPaths (43 entries)
**Reads allowed, writes/edits blocked**

| Pattern Type | Examples |
|--------------|----------|
| System configs | `/etc/hosts`, `/etc/ssh/` |
| Lock files | `*.lock`, `*.pid` |
| Dependency locks | `package-lock.json`, `yarn.lock` |
| Git directories | `.git/`, `.git/config` |

### noDeletePaths (37 entries)
**Reads/writes/edits allowed, only deletes blocked**

| CSF-Specific Paths |
|-------------------|
| `P:/.claude/` |
| `P:/projects/kg_builder/` |
| `P:/projects/*/knowledge_graph_output/` |
| `P:/__csf/` |
| `P:/__csf/` |
| `P:/.claude/session_data/` |
| `P:/.claude/state/` |
| `P:/.claude/sessions/` |

---

## Settings Configuration

Hooks are registered in `P:/.claude/settings.json`:

```json
{
  "matcher": "^Bash$",
  "hooks": [{
    "type": "command",
    "command": "uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py",
    "timeout": 5,
    "layer": "-1_damage_control_bash",
    "critical": true,
    "description": "Damage Control - Block dangerous bash commands"
  }]
}

{
  "matcher": "^(Edit|MultiEdit)$",
  "hooks": [{
    "type": "command",
    "command": "uv run P:/.claude/hooks/damage-control/edit-tool-damage-control.py",
    "timeout": 5,
    "layer": "-1_damage_control_edit",
    "critical": true,
    "description": "Damage Control - Block edits to protected paths"
  }]
}

{
  "matcher": "^Write$",
  "hooks": [{
    "type": "command",
    "command": "uv run P:/.claude/hooks/damage-control/write-tool-damage-control.py",
    "timeout": 5,
    "layer": "-1_damage_control_write",
    "critical": true,
    "description": "Damage Control - Block writes to protected paths"
  }]
}
```

**Key settings:**
- **layer: -1** - Runs before most other hooks (early intervention)
- **critical: true** - Hook failure blocks the tool operation
- **timeout: 5** - Max seconds before hook is killed

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | ALLOW | Operation permitted, continue |
| 1 | ERROR | Hook execution failed, blocks operation |
| 2 | BLOCK | Operation blocked by security policy |

---

## Ask Patterns (Confirmation Prompts)

Some operations require confirmation instead of hard blocking:

| Pattern | Reason |
|---------|--------|
| `git checkout -- .` | Discards all uncommitted changes |
| `git branch -D` | Force deletes branch (even if unmerged) |
| `git push --delete` | Deletes remote branch |
| `DELETE FROM ... WHERE id =` | SQL DELETE with specific ID |

**To enable confirmation prompts:**
```bash
export DAMAGE_CONTROL_ASK_MODE=ask
# Then restart Claude Code
```

---

## Allowlist Patterns (YAML Regex)

`allowCommandPatterns` permits narrow, explicit commands that would otherwise be blocked (e.g., clearing `P:\.git\index.lock`). It only applies to **single commands**; chained commands (`&&`, `;`, `|`, `&`) are blocked with guidance to run the cleanup separately.

**YAML regex escaping tip:** use **single-quoted strings** with **single backslashes**. Double-escaping (`\\b`) turns into a literal backslash and won’t match.

Example:
```yaml
allowCommandPatterns:
  - pattern: '^\s*(del|erase|rm)\b[^\r\n]*\.git[\\/]index\.lock\b'
    reason: Allow clearing stale git index.lock
```

After edits, regenerate:
```bash
uv run P:/.claude/hooks/damage-control/merge-patterns.py --base patterns.upstream.yaml --write
```

---

## Windows Path Handling

All hooks support case-insensitive and slash-agnostic matching on Windows:

| Variant | Matches |
|---------|---------|
| `P:/projects/kg_builder/` | ✅ |
| `P:\projects\kg_builder\` | ✅ |
| `p:/projects/kg_builder/` | ✅ |
| `p:\projects\kg_builder\` | ✅ |

This is implemented via `normalize_case_slash()` and `escape_for_regex()` functions.

---

## Testing Results

**Date:** 2026-01-17
**Tests:** 36 total, 36 passed (100%)

Full test report: `P:/__csf/reports/damage-control-testing-20260117.md`

---

## Maintenance

### Adding New Patterns

1. Edit `patterns.overlay.yaml` for CSF-specific patterns
2. Or edit `patterns.upstream.yaml` for general patterns
3. Regenerate: `uv run merge-patterns.py --base patterns.upstream.yaml --write`
4. Test: `uv run test-damage-control.py -i`

### Updating from Upstream

The upstream repository is at: https://github.com/disler/claude-code-damage-control

To sync upstream changes:
1. Download new `patterns.yaml` from upstream
2. Save as `patterns.upstream.yaml`
3. Regenerate merge

---

## Troubleshooting

### Hook not blocking commands

1. Verify hook is in settings.json with correct matcher
2. Check hook file is executable
3. Test directly: `echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}' | uv run bash-tool-damage-control.py`
4. Restart Claude Code (hooks only load on startup)

### Path not being protected

1. Check if path is in `patterns.yaml`
2. Verify path uses forward slashes (config normalization)
3. Test with exact path: `uv run test-damage-control.py edit Edit ".env" --expect-blocked`

### Merge script produces empty lists

This was fixed in merge-patterns.py (lines 57-72). Ensure you're using the updated version.

---

## References

- **Upstream repo:** https://github.com/disler/claude-code-damage-control
- **Test report:** `P:/__csf/reports/damage-control-testing-20260117.md`
- **Handover doc:** `P:/.claude/hooks/damage-control/HANDOVER.md`
- **Solution design:** `P:/.claude/hooks/damage-control/SOLUTION_DESIGN.md`

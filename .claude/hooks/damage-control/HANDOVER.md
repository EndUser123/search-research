# Damage Control Integration - Handover Document

**Project:** Claude Code Security Framework (CSF) - Damage Control Integration
**Date:** 2026-01-17
**Status:** Implemented - Awaiting Agent Restart
**Handover To:** Another LLM / Human Reviewer

---

## Quick Start

### What Was Done

Integrated [disler/claude-code-damage-control](https://github.com/disler/claude-code-damage-control) to block destructive commands before they execute.

**Key Result:** The command that deleted 158MB of data (`rm -rf P:/projects/kg_builder/`) will now be **BLOCKED** before execution.

### Files Modified/Created

| Path | Type | Purpose |
|------|------|---------|
| `P:/.claude/hooks/damage-control/bash-tool-damage-control.py` | Created | Blocks dangerous Bash commands |
| `P:/.claude/hooks/damage-control/edit-tool-damage-control.py` | Created | Blocks edits to protected paths |
| `P:/.claude/hooks/damage-control/write-tool-damage-control.py` | Created | Blocks writes to protected paths |
| `P:/.claude/hooks/damage-control/patterns.yaml` | Modified | Active pattern set used by hooks |
| `P:/.claude/hooks/damage-control/patterns.upstream.yaml` | Created | Upstream snapshot for long-term maintenance |
| `P:/.claude/hooks/damage-control/patterns.overlay.yaml` | Created | CSF/Windows additions layered on upstream |
| `P:/.claude/hooks/damage-control/merge-patterns.py` | Created | Merge tool to regenerate patterns.yaml |
| `P:/.claude/settings.json` | Modified | Added damage-control to PreToolUse (layer -1) |

### Immediate Action Required

**YOU MUST RESTART YOUR CLAUDE CODE AGENT FOR HOOKS TO TAKE EFFECT.**

After restart, test with:
```bash
# This should be BLOCKED
rm -rf P:/projects/kg_builder/

# This should be BLOCKED (Windows)
rd /s /q P:/projects/test

# This should be ALLOWED
ls -la P:/projects/
```

---

## 1. Implementation Summary

### 1.1 What Is Damage Control?

A PreToolUse hook system that:
- Loads patterns from `patterns.yaml` (declarative config)
- Matches Bash commands against regex patterns
- Checks file paths against protection lists
- Returns exit code 0 (ALLOW), 2 (BLOCK), or JSON (ASK)

### 1.2 Why This Approach?

| Alternative | Rejected Because |
|-------------|------------------|
| Custom Python hook | Re-inventing upstream pattern set and maintenance workflow |
| settings.json permissions.deny | Not pattern-based, can't block `rm -rf` generically |
| Constitutional text injection | Advisory only, agents ignore text |
| TDD enforcement | Prevents bugs, not destructive commands on existing data |

### 1.3 Integration Strategy

**Minimal integration, maximum reuse:**
1. Copied 3 Python hooks from repo (no modifications)
2. Added patterns maintenance files: `patterns.upstream.yaml`, `patterns.overlay.yaml`, `merge-patterns.py`
3. Kept `patterns.yaml` as the active pattern set (regenerate via merge script when needed)
4. Added hooks at layer -1 (run before existing CSF guards)

---

## 2. File Structure

```
P:/.claude/
|-- hooks/
|   `-- damage-control/
|       |-- bash-tool-damage-control.py    # Blocks dangerous Bash commands
|       |-- edit-tool-damage-control.py    # Blocks edits to protected files
|       |-- write-tool-damage-control.py   # Blocks writes to protected paths
|       |-- patterns.yaml                  # Active pattern set
|       |-- patterns.upstream.yaml         # Upstream snapshot
|       |-- patterns.overlay.yaml          # CSF/Windows additions
|       |-- merge-patterns.py              # Merge helper
|       |-- test-damage-control.py         # Interactive tester
|       |-- SOLUTION_DESIGN.md             # Architecture document
|       |-- HANDOVER.md                    # This document
|       `-- VERIFICATION_CHECKLIST.md      # Verification steps
`-- settings.json                          # Modified: hooks added at layer -1
```

---

## 3. Configuration Details

### 3.1 patterns.yaml - CSF Customizations
CSF additions live in `patterns.overlay.yaml`; `patterns.yaml` is the active file (regenerate via `merge-patterns.py --base patterns.upstream.yaml --write`).


**CSF-Specific noDeletePaths (added to base patterns):**

```yaml
noDeletePaths:
  # Knowledge graph data (158MB loss scenario)
  - "P:/projects/kg_builder/"
  - "P:/projects/*/knowledge_graph_output/"

  # CSF data (migration from __csf to __csf)
  - "P:/__csf/"
  - "P:/__csf/"  # Legacy during migration

  # Session data (context continuity)
  - "P:/.claude/session_data/"
  - "P:/.claude/state/"
  - "P:/.claude/sessions/"
```

**Windows Destructive Commands (added to base patterns):**

```yaml
bashToolPatterns:
  # PowerShell
  - pattern: '\bRemove-Item\s+.*-Recurse'
    reason: Remove-Item with -Recurse flag (PowerShell rm -rf equivalent)

  # cmd
  - pattern: '\brd\s+/s'
    reason: rd /s (recursive directory delete)

  - pattern: '\bdel\s+/[fF]'
    reason: del /f (force delete)
```

### 3.2 settings.json Integration

**Hooks inserted at TOP of PreToolUse array (layer -1):**

```json
"PreToolUse": [
  {
    "matcher": "^Bash$",
    "hooks": [{
      "command": "uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py",
      "layer": "-1_damage_control_bash"
    }]
  },
  {
    "matcher": "^(Edit|Write)$",
    "hooks": [{
      "command": "uv run P:/.claude/hooks/damage-control/edit-tool-damage-control.py",
      "layer": "-1_damage_control_edit"
    }]
  },
  {
    "matcher": "^Write$",
    "hooks": [{
      "command": "uv run P:/.claude/hooks/damage-control/write-tool-damage-control.py",
      "layer": "-1_damage_control_write"
    }]
  },
  // ... existing hooks at layer 0+
]
```

---

## 4. Testing Results

### 4.1 Automated Tests Passed

| Test | Command | Expected | Result |
|------|---------|----------|--------|
| rm -rf blocking | `rm -rf P:/projects/kg_builder` | Exit 2, stderr "SECURITY: Blocked" | **PASS** |
| Windows rd /s | `rd /s /q P:/projects/test` | Exit 2, stderr "SECURITY: Blocked" | **PASS** |
| noDeletePaths | `rm P:/projects/kg_builder/file.txt` | Exit 2, "no-delete path" | **PASS** |
| Safe command | `ls -la P:/projects/` | Exit 0, no output | **PASS** |

### 4.2 Manual Testing Required (After Agent Restart)

1. **Test destructive command blocking:**
   ```
   In Claude Code: "delete all files in P:/projects/test recursively"
   Expected: Command blocked, agent sees error
   ```

2. **Test safe commands still work:**
   ```
   In Claude Code: "list files in P:/projects/"
   Expected: Command executes normally
   ```

3. **Test path protection:**
   ```
   In Claude Code: "delete P:/projects/kg_builder"
   Expected: Command blocked (noDeletePaths)
   ```

---

## 5. Known Limitations

### 5.1 Path Normalization (Medium Severity)

**Issue:** Hooks don't fully normalize Windows backslashes. `P:\projects\test` may not match `P:/projects/test`.

**Impact:** Some Windows paths might slip through pattern matching.

**Workaround:** Always use forward slashes in patterns.yaml.

**Future Fix:** Add `os.path.normpath()` in hooks.

### 5.2 MultiEdit Covered (Low Severity)

**Update:** `edit-tool-damage-control.py` now accepts `MultiEdit` and applies the same path checks as `Edit`.

### 5.3 UV Runtime Dependency (Low Impact)

**Issue:** Hooks require `uv run` (adds ~100ms per invocation).

**Impact:** Minor performance overhead on every tool use.

**Workaround:** None. Acceptable for security-critical path.

---

## 6. Troubleshooting

### 6.1 Hook Not Firing

**Symptom:** Destructive commands not blocked.

**Diagnosis:**
```bash
# Check hooks are registered
cat P:/.claude/settings.json | grep -A 5 "damage-control"

# Test hook directly
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
# Should output "SECURITY: Blocked" and exit with code 2
```

**Resolution:**
1. Verify hooks are in `P:/.claude/hooks/damage-control/`
2. Verify hooks are in settings.json PreToolUse array
3. **Restart your Claude Code agent** (hooks only load on startup)

### 6.2 False Positive - Safe Command Blocked

**Symptom:** Legitimate command blocked.

**Diagnosis:**
```bash
# Test the specific command
echo '{"tool_name":"Bash","tool_input":{"command":"YOUR_COMMAND"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```

**Resolution:**
1. Identify which pattern is matching (check stderr)
2. If truly safe, add exception to patterns.yaml OR remove the pattern
3. Consider using `ask: true` for confirmation dialog instead of hard block

### 6.3 False Negative - Dangerous Command Allowed

**Symptom:** Destructive command not blocked.

**Diagnosis:**
```bash
# Test the specific command
echo '{"tool_name":"Bash","tool_input":{"command":"YOUR_COMMAND"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```

**Resolution:**
1. Add pattern to `bashToolPatterns` in patterns.yaml
2. Test with regex101.com to verify pattern matches
3. Restart agent after modifying patterns.yaml

---

## 7. Maintenance

### 7.1 Adding New Protected Paths

Edit `P:/.claude/hooks/damage-control/patterns.yaml`:

```yaml
noDeletePaths:
  - "YOUR/PROTECTED/PATH/"

zeroAccessPaths:
  - "YOUR/SECRET/FILE"

readOnlyPaths:
  - "YOUR/CONFIG/FILE"
```

**Restart agent after editing.**

### 7.2 Adding New Command Patterns

Edit `P:/.claude/hooks/damage-control/patterns.yaml`:

```yaml
bashToolPatterns:
  - pattern: '\bDANGEROUS_COMMAND\s+.*DANGEROUS_FLAG'
    reason: What this command does
    # Optional: ask: true  # Shows confirmation dialog instead of blocking
```

**Test before using:**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"DANGEROUS_COMMAND args"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```

### 7.3 Updating Hooks from Upstream

```bash
cd P:/projects
git clone https://github.com/disler/claude-code-damage-control.git damage-control-repo
cp damage-control-repo/.claude/skills/damage-control/hooks/damage-control-python/*.py \
   P:/.claude/hooks/damage-control/
# Review patterns.yaml changes, merge as needed
```

---

## 8. Rollback Procedure

If issues require rollback:

```bash
# 1. Remove hooks from settings.json
python << 'EOF'
import json
with open('P:/.claude/settings.json', 'r') as f:
    settings = json.load(f)
# Remove damage-control entries (keep all others)
settings['hooks']['PreToolUse'] = [
    h for h in settings['hooks']['PreToolUse']
    if h.get('layer', '') != '-1_damage_control'
]
with open('P:/.claude/settings.json', 'w') as f:
    json.dump(settings, f, indent=2)
EOF

# 2. Remove hook files (optional)
rm -rf P:/.claude/hooks/damage-control/

# 3. Restart agent
```

---

## 9. Next Steps for Reviewer

1. **Verify Implementation:**
   - [ ] Read `SOLUTION_DESIGN.md` for architecture
   - [ ] Review `patterns.yaml` for CSF-specific paths
   - [ ] Check `settings.json` for hook ordering (layer -1)

2. **Test After Agent Restart:**
   - [ ] Test `rm -rf P:/projects/test/` is blocked
   - [ ] Test `rd /s P:\projects\test` is blocked
   - [ ] Test `rm P:/projects/kg_builder/file.txt` is blocked
   - [ ] Verify safe commands still work (`ls`, `git status`)

3. **Decide on Future Enhancements:**
  - [ ] Verify MultiEdit coverage (Edit hook accepts MultiEdit)
   - [ ] Improve Windows path normalization
   - [ ] Add case-insensitive matching for Windows paths

4. **Provide Feedback:**
   - [ ] Report any false positives/negatives
   - [ ] Suggest additional CSF paths to protect
   - [ ] Propose new command patterns to block

---

## 10. Contact & Resources

| Resource | Location |
|----------|----------|
| Upstream repo | https://github.com/disler/claude-code-damage-control |
| Local hooks | `P:/.claude/hooks/damage-control/` |
| Patterns file | `P:/.claude/hooks/damage-control/patterns.yaml` |
| Architecture doc | `P:/.claude/hooks/damage-control/SOLUTION_DESIGN.md` |
| Interactive tester | `uv run P:/.claude/hooks/damage-control/test-damage-control.py -i` |

---

**Handover Status:** Complete
**Ready For:** Agent Restart + End-to-End Testing
**Reviewer Instructions:** Start with section 9 (Next Steps)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-17
**Author:** CSF Implementation Team

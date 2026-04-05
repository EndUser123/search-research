# Damage Control Integration - Verification Checklist

**Purpose:** Systematic verification that damage-control integration is complete and functional.
**Reviewer:** Another LLM / Human
**Date:** 2026-01-17

---

## Part 1: File Existence Verification

### 1.1 Hook Files Present

| File | Expected Location | Status | Notes |
|------|-------------------|--------|-------|
| bash-tool-damage-control.py | `P:/.claude/hooks/damage-control/` | [ ] | ~11KB, 309 lines |
| edit-tool-damage-control.py | `P:/.claude/hooks/damage-control/` | [ ] | ~4.5KB, 144 lines |
| write-tool-damage-control.py | `P:/.claude/hooks/damage-control/` | [ ] | ~4.5KB, 142 lines |
| patterns.yaml | `P:/.claude/hooks/damage-control/` | [ ] | active pattern set |
| patterns.upstream.yaml | `P:/.claude/hooks/damage-control/` | [ ] | upstream snapshot |
| patterns.overlay.yaml | `P:/.claude/hooks/damage-control/` | [ ] | CSF/Windows additions |
| merge-patterns.py | `P:/.claude/hooks/damage-control/` | [ ] | merge helper |
| test-damage-control.py | `P:/.claude/hooks/damage-control/` | [ ] | ~14KB (interactive tester) |

**Verification Command:**
```bash
ls -la P:/.claude/hooks/damage-control/
```

**Expected Output:** 8 files listed above (plus documentation)

---

## Part 2: Configuration Verification

### 2.1 settings.json Integration

| Check | Expected | Status |
|-------|----------|--------|
| Damage-control hooks at TOP of PreToolUse | Yes | [ ] |
| Layer value is -1 | Yes | [ ] |
| Three hooks: Bash, Edit, Write | Yes | [ ] |
| Command uses `uv run` | Yes | [ ] |
| Timeout is 5 seconds | Yes | [ ] |
| Critical is true | Yes | [ ] |

**Verification Command:**
```bash
grep -A 10 "damage_control" P:/.claude/settings.json | head -30
```

**Expected Output:**
```json
{
  "matcher": "^Bash$",
  "hooks": [
    {
      "type": "command",
      "command": "uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py",
      "timeout": 5,
      "layer": "-1_damage_control_bash",
      "critical": true,
      "description": "Damage Control - Block dangerous bash commands"
    }
  ]
}
```

### 2.2 patterns.yaml Content

| Pattern Category | Present | Count |
|------------------|---------|-------|
| Unix destructive (rm -rf, etc.) | [ ] | ~6 patterns |
| Windows PowerShell (Remove-Item) | [ ] | ~5 patterns |
| Windows cmd (rd, del) | [ ] | ~7 patterns |
| Git destructive operations | [ ] | ~12 patterns |
| SQL destructive (DELETE, DROP) | [ ] | ~7 patterns |
| zeroAccessPaths (.env, *.pem, etc.) | [ ] | ~30 entries |
| readOnlyPaths (/etc/, lock files, etc.) | [ ] | ~35 entries |
| noDeletePaths (claude config, git, etc.) | [ ] | ~25 entries |
| **CSF-Specific paths** | **[ ]** | **~6 entries** |

**CSF-Specific Paths to Verify:**
```yaml
noDeletePaths:
  - "P:/.claude/"              # [ ] Present
  - "P:/projects/kg_builder/"  # [ ] Present
  - "P:/projects/*/knowledge_graph_output/"  # [ ] Present
  - "P:/__csf/"                # [ ] Present
  - "P:/__csf/"            # [ ] Present (legacy)
  - "P:/.claude/session_data/" # [ ] Present
  - "P:/.claude/state/"        # [ ] Present
```

**Verification Command:**
```bash
grep -E "(kg_builder|ckd|session_data|__csf)" P:/.claude/hooks/damage-control/patterns.yaml
```

---

## Part 2.3 Pattern Merge Maintenance

| Check | Expected | Status |
|-------|----------|--------|
| Upstream snapshot present | `patterns.upstream.yaml` exists | [ ] |
| Overlay present | `patterns.overlay.yaml` exists | [ ] |
| Merge check passes | `merge-patterns.py --check` exit 0 | [ ] |

**Verification Command:**
```bash
uv run P:/.claude/hooks/damage-control/merge-patterns.py --check
```

**Expected Output:**
- Exit code 0
- "OK: patterns file matches base + overlay"
**Optional upstream sync check:**
```bash
uv run P:/.claude/hooks/damage-control/merge-patterns.py --base patterns.upstream.yaml --check
```


**If Out of Date (sync to upstream):**
```bash
uv run P:/.claude/hooks/damage-control/merge-patterns.py --base patterns.upstream.yaml --write
```

---

## Part 3: Functional Testing (Direct Hook Invocation)

### 3.1 Destructive Command Blocking

**Test 1: Unix rm -rf**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "SECURITY: Blocked"
- [ ] Stderr contains: "rm with recursive or force flags"

**Test 2: Windows rd /s**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rd /s /q C:\\test"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "rd /s"

**Test 3: PowerShell Remove-Item**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"Remove-Item -Recurse -Force /tmp/test"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "Remove-Item with -Recurse"

### 3.2 Path Protection

**Test 4: noDeletePaths - kg_builder**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm P:/projects/kg_builder/test.txt"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "no-delete path"
- [ ] Stderr contains: "kg_builder"

**Test 5: zeroAccessPaths - .env**
```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":".env"}}' | \
  uv run P:/.claude/hooks/damage-control/edit-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "zero-access"

**Test 6: readOnlyPaths - package-lock.json**
```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"package-lock.json"}}' | \
  uv run P:/.claude/hooks/damage-control/write-tool-damage-control.py
```
- [ ] Exit code: 2 (BLOCK)
- [ ] Stderr contains: "read-only path"

### 3.3 Safe Commands Allowed

**Test 7: Read-only command**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la /tmp"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 0 (ALLOW)
- [ ] No stderr output

**Test 8: Safe file operation**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm /tmp/test.txt"}}' | \
  uv run P:/.claude/hooks/damage-control/bash-tool-damage-control.py
```
- [ ] Exit code: 0 (ALLOW) - single file delete is OK
- [ ] No stderr output

---

## Part 4: End-to-End Testing (After Agent Restart)

**CRITICAL:** These tests require restarting your Claude Code agent first.

### 4.1 Agent-Level Destructive Command Test

**Prompt to agent:**
```
Delete all files in P:/projects/test recursively
```

**Expected behavior:**
- [ ] Agent reports: "SECURITY: Blocked" error
- [ ] Command is NOT executed
- [ ] Agent sees stderr from damage-control hook

**Verification:**
```bash
# Check directory still exists
ls P:/projects/test/
```
- [ ] Directory still exists (not deleted)

### 4.2 Agent-Level Safe Command Test

**Prompt to agent:**
```
List files in P:/projects/
```

**Expected behavior:**
- [ ] Command executes normally
- [ ] Files are listed
- [ ] No security errors

### 4.3 kg_builder Protection Test

**Prompt to agent:**
```
Delete P:/projects/kg_builder
```

**Expected behavior:**
- [ ] Agent reports: "SECURITY: Blocked" error
- [ ] Error mentions "no-delete path"
- [ ] kg_builder directory still exists

---

## Part 5: Regression Verification

### 5.1 Existing Hooks Still Work

| Existing Hook | Test | Status |
|---------------|------|--------|
| shell_complexity_gate.py | Try complex heredoc (should block) | [ ] |
| unparseable_command_gate.py | Try `python -c "exec(...)"` (should block) | [ ] |
| recursive_failure_detector.py | N/A (automatic) | [ ] |
| skill_enforcement_gate.py | Trigger slash command | [ ] |

### 5.2 Hook Ordering Verification

**Verification:** Damage-control hooks run FIRST (before layer 0 hooks).

**Test:**
```bash
grep -E "(layer.*damage_control|layer.*0_)" P:/.claude/settings.json | head -10
```

**Expected:**
- [ ] damage_control appears BEFORE layer 0 hooks
- [ ] layer value is -1 (negative = earlier)

---

## Part 6: Documentation Verification

| Document | Location | Complete | Accurate |
|----------|----------|----------|----------|
| SOLUTION_DESIGN.md | `P:/.claude/hooks/damage-control/` | [ ] | [ ] |
| HANDOVER.md | `P:/.claude/hooks/damage-control/` | [ ] | [ ] |
| VERIFICATION_CHECKLIST.md | `P:/.claude/hooks/damage-control/` | [ ] | [ ] |
| patterns.yaml (self-documenting) | `P:/.claude/hooks/damage-control/` | [ ] | [ ] |

---

## Part 7: Rollback Verification (Dry Run)

**Purpose:** Ensure rollback procedure is documented and tested.

| Rollback Step | Documented | Tested (dry run) |
|---------------|------------|------------------|
| Remove hooks from settings.json | [ ] | [ ] |
| Remove hook files | [ ] | [ ] |
| Restart agent | [ ] | [ ] |

**Rollback command (for reference):**
```bash
# Remove damage-control from settings.json
python << 'EOF'
import json
with open('P:/.claude/settings.json', 'r') as f:
    settings = json.load(f)
settings['hooks']['PreToolUse'] = [
    h for h in settings['hooks']['PreToolUse']
    if h.get('layer', '') != '-1_damage_control'
]
with open('P:/.claude/settings.json', 'w') as f:
    json.dump(settings, f, indent=2)
EOF
```

---

## Part 8: Sign-Off

### 8.1 Implementation Sign-Off

| Item | Verified By | Date | Notes |
|------|-------------|------|-------|
| Hooks installed | | | |
| Configuration correct | | | |
| Direct tests pass | | | |
| E2E tests pass | | | |
| Documentation complete | | | |

### 8.2 Reviewer Sign-Off

| Reviewer | Status | Date | Comments |
|----------|--------|------|----------|
| LLM Reviewer | [ ] Pass / [ ] Fail | | |
| Human Reviewer | [ ] Pass / [ ] Fail | | |

### 8.3 Critical Findings

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| | | | |

---

## Summary Checklist

- [ ] **Part 1:** All 5 hook files present
- [ ] **Part 2:** Configuration correct in settings.json
- [ ] **Part 2:** CSF-specific paths in patterns.yaml
- [ ] **Part 3:** All 8 direct hook tests pass
- [ ] **Part 4:** Agent restarted and E2E tests pass
- [ ] **Part 5:** Existing hooks still functional
- [ ] **Part 6:** Documentation complete and accurate
- [ ] **Part 7:** Rollback procedure verified
- [ ] **Part 8:** Sign-off complete

**Overall Status:** [ ] PASS / [ ] FAIL

---

**Checklist Version:** 1.0
**Last Updated:** 2026-01-17
**Next Review:** After agent restart + E2E testing

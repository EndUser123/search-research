# Adversarial Review Summary: `plan-20260318-user-directive-obligation-tracker.md`

**Status:** OK
**Total Findings:** 48
**High Severity:** 0
**Shown:** 20 of 48

## Findings

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/stop/Stop_gto_checklist_gate.py:127`

Function exceeds 50 lines (63 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py:58`

Function exceeds 50 lines (52 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py:144`

Function exceeds 50 lines (116 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py:260`

Function exceeds 50 lines (72 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py:372`

Function exceeds 50 lines (157 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py:529`

Function exceeds 50 lines (57 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/Stop_router.py:81`

Function exceeds 50 lines (76 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/Stop_router.py:259`

Function exceeds 50 lines (57 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/Stop_router.py:334`

Function exceeds 50 lines (51 lines)

### 🟡 [MEDIUM] adversarial-quality: Long Function Detected
**Location:** `/.claude/hooks/Stop_router.py:530`

Function exceeds 50 lines (81 lines)

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `/.claude/hooks/UserPromptSubmit_modules/base.py`

Source file /.claude/hooks/UserPromptSubmit_modules/base.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `/.claude/hooks/Stop_router.py`

Source file /.claude/hooks/Stop_router.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `turn_marker.py`

Source file turn_marker.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `user_directive_obligation.py`

Source file user_directive_obligation.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `/.claude/hooks/stop/Stop_gto_checklist_gate.py`

Source file /.claude/hooks/stop/Stop_gto_checklist_gate.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `StopHook_directive_obligation.py`

Source file StopHook_directive_obligation.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `declaration_reminder.py`

Source file declaration_reminder.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `/.claude/hooks/UserPromptSubmit_modules/registry.py`

Source file /.claude/hooks/UserPromptSubmit_modules/registry.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `/.claude/hooks/UserPromptSubmit_modules/user_directive_obligation.py`

Source file /.claude/hooks/UserPromptSubmit_modules/user_directive_obligation.py lacks corresponding test

### 🟡 [MEDIUM] adversarial-testing: Missing Test File
**Location:** `stop/StopHook_directive_obligation.py`

Source file stop/StopHook_directive_obligation.py lacks corresponding test

---

## Detailed Reports

Full findings for each agent are available in:

- State directory: `.claude\state\terminals\console_f7b72efa-d166-4f34-a80b-a0471543d3ac\adversarial-reviews`

To view detailed findings for a specific agent:
```bash
python .claude/skills/plan-workflow/__lib/adversarial_runner.py ".claude/hooks/plans/plan-20260318-user-directive-obligation-tracker.md" --show <agent>
```

Available agents: compliance, quality, security, testing, qa, critic

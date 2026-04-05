# Plan: Skill Enforcement Enhancement - 3-Layer Defense

**Created**: 2026-03-12
**Status**: READY-FOR-IMPLEMENTATION
**Objective**: Implement 3-layer defense for skill execution based on architecture analysis

---

## Problem Statement

Current skill enforcement uses suggestion format ("You MUST call Skill() first") which has ~0% effectiveness. The AI frequently ignores suggestions and provides prose analysis instead of executing skill workflows.

**Proposed Solution**: 3-Layer Defense
1. **Layer 1**: Instruction format enforcement (50% improvement)
2. **Layer 2**: Bypass detection restoration (additional 30% improvement)
3. **Layer 3**: Pre-execute router (optional, +15%, high complexity)

---

## Implementation Tasks

### T-001: Update Instruction Format (Priority: CRITICAL)

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\skill_enforcer.py`
**Lines**: 24-37, 279-287

**Current Format** (suggestion - 0% success):
```python
SLASH_EXECUTION_LANE = """
## SKILL EXECUTION LANE — MANDATORY

You MUST call `Skill("{command}")` first to load the skill instructions.
...
"""
```

**New Format** (instruction - 50% success):
```python
SLASH_EXECUTION_LANE = """
INSTRUCTION: Execute skill {command}

Step 1: Call Skill("{command}") to load workflow
Step 2: Follow the skill's documented procedure exactly

Do NOT substitute your own analysis or improvise.
"""
```

**Acceptance**: Format changed to explicit "INSTRUCTION:" prefix with numbered steps

### T-002: Restore Bypass Detection Hook (Priority: CRITICAL)

**Source**: `P:\.claude\hooks\_archived\StopHook_skill_execution_gate.py`
**Destination**: `P:\.claude\hooks\StopHook_skill_execution_gate.py`

**Action**: Copy from archive to active hooks directory

**Acceptance**: File exists in hooks directory

### T-003: Register Stop Hook (Priority: CRITICAL)

**File**: `P:\.claude\settings.json`

**Add to hooks.Stop section**:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/StopHook_skill_execution_gate.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Acceptance**: Hook registered in settings.json

### T-004: Add Environment Variables (Priority: MEDIUM)

**File**: `P:\.claude\settings.json`

**Add to env section**:
```json
{
  "env": {
    "SKILL_BYPASS_DETECTION_ENABLED": "true",
    "SKILL_BYPASS_DETECTION_MODE": "warn"
  }
}
```

**Acceptance**: Environment variables added

### T-005: Update Documentation (Priority: LOW)

**File**: `P:\.claude\hooks\CLAUDE.md`

**Add section under "Constitutional Hooks"**:
```markdown
### Skill Enforcement (v3.5 - Enhanced)

**Three-Layer Defense**:
1. **Instruction Format**: "INSTRUCTION:" prefix with explicit steps (UserPromptSubmit)
2. **Bypass Detection**: Detects when user types /command but AI responds with prose (Stop)
3. **Pattern Gate**: Real-time blocking of unauthorized tool usage (PreToolUse)

**Configuration**:
- `SKILL_BYPASS_DETECTION_ENABLED` - Enable/disable bypass detection
- `SKILL_BYPASS_DETECTION_MODE` - "warn" (advisory) or "block" (hard blocking)
```

**Acceptance**: Documentation updated

### T-006: Integration Testing (Priority: CRITICAL)

**Test scenarios**:
1. Slash command triggers instruction format
2. Prose response to slash command is blocked
3. Skill tool invocation allows execution
4. Knowledge skills are not blocked

**Acceptance**: All scenarios pass

---

## Expected Outcomes

**Baseline (current)**:
- Skills not invoked: ~40% of requests
- Skills invoked but not used: ~20% of requests

**After T-001 through T-006**:
- Skills not invoked: ~20% (50% improvement from instruction format)
- Skills invoked but not used: ~6% (70% improvement from bypass detection)

---

## Rollback Plan

If issues occur:
1. Restore original `SLASH_EXECUTION_LANE` format from git
2. Remove `StopHook_skill_execution_gate.py` from hooks directory
3. Remove hook registration from settings.json
4. Remove environment variables from settings.json

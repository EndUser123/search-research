# Skill Enforcement System v2.1

**Updated:** 2026-01-24

## Purpose

Forces CC to use the `Skill()` tool before executing slash commands, preventing:
- Direct Bash/Edit execution bypassing skill instructions
- Investigation/searching behavior instead of execution
- Skill output simulation via `python -c`

## Architecture

```
    │
    ├─► UserPromptSubmit Router (priority 1)
    │   └─► skill_enforcement injection
    │
    ├─► PreToolUse Gate (fallback)
    │   └─► Blocks Bash/Edit/Write until Skill used
    │
    └─► PostToolUse Handler
        └─► Clears state OR allows Bash for execution skills
```

## Files

| File | Purpose |
|------|---------|
| `skill_enforcement_gate.py` | Core logic: state management, blocking, allowances |
| `UserPromptSubmit_router.py` | Injects skill directive (priority 1) |
| `settings.json` PreToolUse | Fallback blocking hook |
| `settings.json` PostToolUse | State clearing after Skill use |

## Hook Priority (Critical)

**Problem solved (v2.1):** Skill enforcement was priority 7, appearing AFTER `unified_injector` (priority 6) which outputs verbose command directives. CC processed the first context it saw and ignored the later skill enforcement message.

**Fix:** Moved skill_enforcement to **priority 1** so it appears FIRST in context.

```python
HOOK_PRIORITY = {
    "consent_granter": 0,
    "skill_enforcement": 1,  # ← NOW RUNS EARLY
    "value_check_injection": 2,
    "tdd_eval": 3,
    ...
    "unified_injector": 7,   # ← Verbose output comes AFTER
}
```

## Injection Message

The injection is visually prominent to ensure CC sees it:

```
🔴 CRITICAL TOOL CONSTRAINT 🔴
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


⛔ BLOCKED until Skill tool used:
   - Bash, Edit, Write, Task, Grep, WebSearch

✓ After Skill is read, follow its instructions.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## State Machine

```
         ┌─────────────┐
         │   IDLE      │
         └──────┬──────┘
                │ /skill detected
                ▼
         ┌─────────────┐
         │  PENDING    │ ← Bash/Edit BLOCKED
         └──────┬──────┘
                │ Skill() tool used
                ▼
         ┌─────────────┐
         │   READ      │ ← Bash ALLOWED (for execution skills)
         └──────┬──────┘
                │ 120s timeout OR clear
                ▼
         ┌─────────────┐
         │   IDLE      │
         └─────────────┘
```

## Execution Skills

Skills that provide CLI commands get Bash allowance after Skill is read:

```python
SKILLS_WITH_BASH_EXECUTION = {
    "git": ["Bash"],   # Git/worktree sync
}
```

## State Files

Per-instance state files prevent cross-session interference:

```
P:/.claude/hooks/state/pending_skill_{instance_id}.json
```

Instance ID = MD5 hash of CWD (first 8 chars).

## Monitoring

```bash
# Health check (last 24h stats)
python P:/.claude/hooks/check_skill_enforcement.py

# Raw logs
tail -20 P:/.claude/logs/skill_enforcement.jsonl
```

**Expected metrics:**
- Block rate: <5% (most invocations should succeed first try)
- Blocks per invocation: ~0 (injection prevents bad tool selection)

**Alert thresholds:**
- >5 blocks/day suggests optimization degraded
- Block rate >10% needs investigation

## Debugging

```bash
# Enable debug logging
export SKILL_ENFORCEMENT_DEBUG=1

# Test flow
# Should see:
# 1. Injection in context (priority 1)
# 3. PostToolUse allows Bash
```

## Configuration

| Env Var | Default | Purpose |
|---------|---------|---------|
| `SKILL_ENFORCEMENT_ENABLED` | `true` | Master enable/disable |
| `SKILL_ENFORCEMENT_DEBUG` | `0` | Verbose stderr logging |

## Changelog

**v2.1 (2026-01-24)**
- Moved hook priority from 7 → 1 to appear before unified_injector
- Enhanced injection message with visual prominence
- Root cause fix for 175% block rate

**v2.0 (2026-01-23)**
- Added post-read execution directive injection
- Added SKILLS_WITH_BASH_EXECUTION allowances
- Instance isolation via CWD hash

**v1.0 (2026-01-22)**
- Initial implementation with PreToolUse blocking

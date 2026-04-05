# Process Decision: Domain-Aware Planning Checkpoint

**Date:** 2026-03-11
**Status:** ✅ IMPLEMENTED - Active in /code and /plan-workflow

---

## Decision

**Add domain mechanics checkpoint before creating implementation phases.**

**Rationale:** Generic software project templates don't fit all domains. Skills, hooks, and config files are file-based changes, not service deployments. Applying deployment phases to file changes creates confusion and unnecessary documentation.

---

## Implementation

### Checkpoint Question (Before Final Phase)

```
For any implementation plan, before finalizing phases:

1. "What does 'deploy' mean for this specific domain?"
   - If "File exists = deployed": Skip deployment phases
   - If "Service restart required": Include deployment phases
   - If "Config change only": Skip rollout phases

2. "What phases are actually needed?"
   - List ONLY phases that map to real mechanics
   - Remove phases that don't match domain reality

3. "Is there a rollback path?"
   - If yes: Document rollback (1 file edit)
   - If no: Skip rollback plan
```

### Domain Mechanics Mapping

| Domain | Mechanics | Deployment Needed | Phases to Skip |
|--------|-----------|-------------------|---------------|
| **Skills** (SKILL.md) | File exists = live | No | Staging, phased rollout, deployment monitoring |
| **Hooks** (.py files) | File exists = active | No (may need restart) | Staging, gradual rollout |
| **Services** (daemons) | Process restart needed | Yes | None (full deployment) |
| **Configs** (YAML/JSON) | Reload on change | No (usually) | Deployment monitoring |
| **Databases** (migrations) | Schema change | Yes (rollback needed) | None (full deployment) |

### Process Integration

**Location:** Before Phase 5 (or final phase) in any plan

**When to apply:** Any implementation plan that includes "deployment" or "rollout" phases

**How to apply:**
1. Read current plan draft
2. Run checkpoint questions
3. Remove non-matching phases
4. Keep only phases that map to actual mechanics

---

## Examples

### Example 1: Skills (Current Case)

**Question:** "What does 'deploy' mean for skills?"
**Answer:** SKILL.md file exists → skill is live

**Phases to remove:**
- ❌ Phased rollout (Day 1-4)
- ❌ Staging environment
- ❌ Deployment monitoring (infrastructure doesn't exist)

**Phases to keep:**
- ✅ Testing (unit, functional, performance)
- ✅ Rollback plan (how to revert file change)
- ✅ Documentation updates

**Result:** Phase 5 becomes "Verification & Documentation" not "Rollout & Monitoring"

---

### Example 2: Service Deployment (Hypothetical)

**Question:** "What does 'deploy' mean for services?"
**Answer:** Process restart needed → deployment required

**Phases to keep:**
- ✅ Staging environment
- ✅ Phased rollout (10% → 50% → 100%)
- ✅ Deployment monitoring
- ✅ Rollback plan

**Result:** Full deployment process appropriate

---

## Success Criteria

✅ **No more deployment theater** for file-based systems
✅ **Phases match actual mechanics** of domain
✅ **User doesn't need to ask** "why is this a step?"
✅ **Planning is faster** (skip unnecessary documentation)

---

## Confidence

**Confidence: 85%**

**Evidence basis:**
- Research confirms config changes ≠ code deployment
- User caught mismatch immediately (strong signal)
- Skills are files, not services (verified mechanics)

**Gap:**
- Haven't tested checkpoint in real workflow
- May miss hybrid cases (code + config together)

---

---

**END OF DECISION**

## Implementation Record

**Implemented:** 2026-03-11

**Changes Made:**
1. **`/code` skill** (Phase 9: DONE)
   - Added section 9.3 "Domain Mechanics Checkpoint" before deployment guidance
   - Location: `P:\.claude\skills\code\SKILL.md` line ~1431
   - Logic: Check path patterns for skills/hooks/configs vs services/databases

2. **`/plan-workflow` skill** (Builder Contract)
   - Added "Domain Mechanics Checkpoint" section before deployment tasks
   - Location: `P:\.claude\skills\plan-workflow\SKILL.md` in Builder Contract
   - Logic: Same pattern-based detection for file vs service domains

**Result:**
- File-based systems (skills, hooks, configs) skip deployment phases automatically
- Service-based systems (services, databases, APIs) get deployment planning as before
- Simple `if` statement prevents deployment theater for file changes

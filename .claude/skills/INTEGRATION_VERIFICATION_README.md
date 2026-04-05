# Skill Integration Verification - Process Gap Fix

## The Problem

You had to ask "is async-bugs added to all skills that can take advantage of it?" to discover that:
- async-bugs SKILL.md **claimed** integration with /code and /refactor (lines 107-109)
- But those integrations **didn't actually exist**
- Documentation was aspirational, not factual

## Root Cause

**Documentation before implementation:**
```python
# WRONG ORDER:
1. Write SKILL.md with integration claims
2. Implement skill
3. ✗ Never verify claims exist
4. Document becomes aspirational
```

**Missing verification step:**
- No automated check for "do claimed integrations exist?"
- No validation after skill implementation
- No integration test in skill development workflow

## Process Fix

### 1. Integration Verification Checklist

**Add to skill development workflow (MANDATORY):**

```yaml
After implementing any skill:
  ✅ Tests pass
  ✅ Documentation written
  ✅ INTEGRATION VERIFICATION ← NEW STEP
     For each "suggest:" target:
       - Check if target skill exists
       - Check if target skill mentions this skill
       - Verify integration code exists
     For each claimed integration:
       - Verify actual implementation exists
       - Document only what's real, not what's planned
```

### 2. Documentation-Last Policy

**Before (wrong):**
```python
Write SKILL.md with claims → Implement skill → Never verify
```

**After (correct):**
```python
Implement skill → Verify integrations → Document reality
```

### 3. Automatic Verification via IntegrationVerifier Hook

**The IntegrationVerifier hook runs automatically on every SKILL.md edit:**

- ✅ Parses SKILL.md frontmatter for `suggest:` field
- ✅ Checks that suggested targets exist in skills directory
- ✅ Verifies bidirectional integration (A suggests B → B should suggest A)
- ✅ Warns when gaps found (configurable: warn or block mode)

**Configuration:**
```json
{
  "env": {
    "INTEGRATION_VERIFIER_ENABLED": "true",
    "INTEGRATION_VERIFIER_MODE": "warn"
  }
}
```

**No manual command needed** - the hook runs automatically after every SKILL.md write/edit operation.

## Memory Entry

**Write this to MEMORY.md:**

```markdown
## Integration Verification Gap

**Problem:** async-bugs SKILL.md claimed /code and /refactor integration, but those integrations didn't exist. User had to explicitly ask to discover gap.

**Root cause:** Documentation written before implementation verification. No validation step.

**Fix:**
1. Integration verification checklist after skill implementation
2. Documentation-last policy (document what exists, not aspirations)
3. IntegrationVerifier hook (automatic verification on SKILL.md edits)
4. Configurable mode: warn (default) or block

**Workflow:**
Implement → Edit SKILL.md → **Automatic Hook Verification** → Commit

**Prevents:** Aspirational documentation, unverified claims, integration gaps
```

## Immediate Actions

1. **Run verification on all existing skills:**
   ```bash
   for skill in P:/.claude/skills/*/; do
     name=$(basename "$skill")
     bash verify-skill-integration.sh "$name"
   done
   ```

2. **Add verification to skill development workflow:**
   - Update /skill-development SKILL.md
   - Add to /testing-skills validation checklist

3. **Document this gap in memory:**
   - Write to MEMORY.md
   - Add to lazy_patterns.md (anti-pattern: aspirational documentation)

## Testing the Fix

**After implementing a new skill:**

```bash
# 1. Implement skill
# 2. Write tests
# 3. RUN VERIFICATION
bash verify-skill-integration.sh my-new-skill

# 4. If verification passes:
#    - Document integrations
#    - Commit

# 5. If verification fails:
#    - Fix gaps
#    - Re-verify
#    - Then document
```

## Success Criteria

**Before this fix:**
- ❌ Documentation can claim non-existent integrations
- ❌ User must explicitly ask to discover gaps
- ❌ No verification step in workflow

**After this fix:**
- ✅ Verification catches integration gaps automatically
- ✅ Documentation matches implementation reality
- ✅ Mandatory verification step in workflow
- ✅ Pre-commit check prevents aspirational docs

## Related Anti-Patterns

From `lazy_patterns.md`:
- **"Accept bugs as features"** → Similar to "accept aspirational docs as reality"
- **"Documentation workaround"** → Writing docs instead of implementing

**Integration verification is the "truthfulness" pattern for skill documentation.**

# Ralph Loop Rollback Guide

**Version**: 1.0
**Last Updated**: 2026-03-15
**Applies to**: loop-core v0.5.0+

---

## Overview

This guide provides step-by-step procedures for rolling back the Ralph Loop platform rollout. The Ralph Loop platform introduced policy-based exit conditions, verification integration, and observability features. This guide covers two rollback scenarios:

1. **Quick Rollback**: Disable new behavior via configuration flag
2. **Full Rollback**: Complete removal of all Ralph Loop components

---

## Quick Rollback (Recommended First Step)

### Purpose

Disable enforcement mode while keeping all files in place. This is the safest first step if issues arise.

### Procedure

#### Step 1: Disable Enforcement Mode

Edit `.claude/loop/config.yaml`:

```yaml
enforcement:
  enabled: false  # Change from true to false
```

#### Step 2: Verify Rollback

Check that the loop now uses minimal policy:

```bash
# The loop should now exit with only:
# - EXIT_SIGNAL: true in RALPH_STATUS
# - completion_indicators >= min_completion_indicators
# (ignores task completion and verification)
```

#### Step 3: Test Loop Behavior

Run a test loop to confirm minimal policy is active:

```bash
/loop-code plan.md
```

Expected behavior:
- Loop may exit even with incomplete tasks
- Loop may exit even without verification pass
- Loop still requires EXIT_SIGNAL and completion_indicators

### Reverting Quick Rollback

To re-enable enforcement mode:

```yaml
enforcement:
  enabled: true  # Change back to true
```

---

## Full Rollback (Complete Removal)

### Purpose

Remove all Ralph Loop platform components and restore pre-rollup behavior.

### Files Created by Ralph Loop Rollout

#### Core Configuration
- `.claude/loop/config.yaml` - Loop policy configuration
- `.claude/loop/plan.md` - Default plan file

#### New Python Modules
- `scripts/loop_policy.py` - Policy enforcement logic
- `scripts/loop_observability.py` - Logging and metrics
- `scripts/ralph_loop_entry.py` - /ralph-loop skill wrapper

#### Skills
- `skills/loop-code/SKILL.md` - Updated /loop-code skill
- `.claude/skills/loop-code/` - Skill junction (if installed)

#### Tests
- `tests/test_enforcement_flag.py` - TASK-018 enforcement tests
- `tests/test_loop_policy.py` - Policy module tests
- `tests/test_observability.py` - Observability tests (if created)

#### Documentation
- `docs/ralph-worktrees.md` - Worktree workflow guide
- `docs/worktree-quick-reference.md` - Quick reference
- `docs/verify-worktree-setup.sh` - Verification script
- `docs/loop-rollout.md` - This file

#### State Directories (may exist)
- `.claude/state/terminals/*/loop_state.json` - Loop execution state
- `.claude/state/terminals/*/logs/decision.log` - Decision logs
- `.claude/state/terminals/*/loop_metrics.json` - Metrics

---

### Rollback Steps

#### Phase 1: Stop Running Loops

1. **Identify active loops**:

```bash
# Check for running loop processes
ps aux | grep -i "loop-core\|ralph-loop"

# Check for lock files
find .claude/state/terminals -name "*.lock" -type f
```

2. **Stop active loops**:

```bash
# Kill identified processes (use PIDs from above)
kill <PID>

# Or force kill if needed
kill -9 <PID>
```

#### Phase 2: Remove Configuration Files

```bash
# Remove loop configuration directory
rm -rf .claude/loop/

# Remove default plan
rm -f .claude/loop/plan.md
```

#### Phase 3: Remove Python Modules

```bash
# Remove new modules
rm -f scripts/loop_policy.py
rm -f scripts/loop_observability.py
rm -f scripts/ralph_loop_entry.py
```

#### Phase 4: Remove or Restore Skills

**Option A: Remove skill junction only**

```bash
# Remove skill junction (keeps original skill)
rm -rf .claude/skills/loop-code/
```

**Option B: Revert to original /loop-code skill**

If you have a backup of the original `/loop-code` skill:

```bash
# Restore from backup
cp backup/original-loop-code-SKILL.md skills/loop-code/SKILL.md

# Remove skill junction
rm -rf .claude/skills/loop-code/
```

#### Phase 5: Remove Tests

```bash
# Remove new test files
rm -f tests/test_enforcement_flag.py
rm -f tests/test_loop_policy.py
rm -f tests/test_observability.py
```

#### Phase 6: Remove Documentation

```bash
# Remove Ralph Loop documentation
rm -f docs/ralph-worktrees.md
rm -f docs/worktree-quick-reference.md
rm -f docs/verify-worktree-setup.sh
rm -f docs/loop-rollout.md  # This file
```

#### Phase 7: Clean Up State (Optional)

**WARNING**: This removes all loop state. Only do this if you don't need to resume any loops.

```bash
# Remove all loop state directories
rm -rf .claude/state/terminals/*/loop_state.json
rm -rf .claude/state/terminals/*/logs/decision.log
rm -rf .claude/state/terminals/*/loop_metrics.json
rm -rf .claude/state/terminals/*/logs/

# Or remove entire terminal state (more aggressive)
# rm -rf .claude/state/terminals/*
```

#### Phase 8: Update Imports (If Used)

If any code imports the removed modules:

```bash
# Find files that import removed modules
grep -r "from scripts.loop_policy" . --include="*.py"
grep -r "from scripts.loop_observability" . --include="*.py"
grep -r "import loop_policy" . --include="*.py"
grep -r "import loop_observability" . --include="*.py"

# Remove or update those imports
```

---

## Verification Steps

### After Quick Rollback

1. **Check config file**:

```bash
cat .claude/loop/config.yaml | grep "enabled:"
```

Expected output: `enabled: false`

2. **Test loop behavior**:

```bash
/loop-code plan.md
```

Expected: Loop exits with minimal conditions

### After Full Rollback

1. **Verify files removed**:

```bash
# Check that key files are gone
ls scripts/loop_policy.py 2>&1 | grep "No such file"
ls scripts/loop_observability.py 2>&1 | grep "No such file"
ls .claude/loop/config.yaml 2>&1 | grep "No such file"
```

2. **Verify no imports broken**:

```bash
# Run tests (if any remain)
pytest tests/ -v

# Or check syntax
python -m py_compile scripts/*.py
```

3. **Verify skill junction removed**:

```bash
ls .claude/skills/loop-code/ 2>&1 | grep "No such file"
```

---

## Troubleshooting Rollback Issues

### Issue: Config File Won't Delete

**Symptom**: `rm: cannot remove '.claude/loop/config.yaml': Permission denied`

**Solution**:

```bash
# Check file permissions
ls -la .claude/loop/config.yaml

# Change permissions if needed
chmod 644 .claude/loop/config.yaml

# Try again
rm .claude/loop/config.yaml
```

### Issue: Loop Still Using New Behavior

**Symptom**: Quick rollback didn't change behavior

**Possible Causes**:

1. **Config cached**: Restart terminal or Python process
2. **Wrong config file**: Check path is correct
3. **Config syntax error**: Verify YAML is valid

**Solution**:

```bash
# Verify config file
cat .claude/loop/config.yaml

# Check for syntax errors
python -c "import yaml; yaml.safe_load(open('.claude/loop/config.yaml'))"

# Restart terminal/IDE
```

### Issue: Import Errors After Full Rollback

**Symptom**: `ModuleNotFoundError: No module named 'scripts.loop_policy'`

**Solution**:

```bash
# Find files with imports
grep -r "loop_policy\|loop_observability" . --include="*.py"

# Remove or comment out those imports
```

### Issue: Tests Fail After Rollback

**Symptom**: Tests fail because they expect removed modules

**Solution**:

```bash
# Remove tests that require removed modules
rm tests/test_enforcement_flag.py
rm tests/test_loop_policy.py
rm tests/test_observability.py

# Or update tests to skip removed functionality
```

---

## Partial Rollback Scenarios

### Scenario 1: Keep Observability, Remove Policy

Remove policy enforcement but keep logging:

```bash
# Remove policy module
rm scripts/loop_policy.py

# Keep observability module
# (keep scripts/loop_observability.py)

# Update /loop-code skill to not use policy
# (edit skills/loop-code/SKILL.md manually)
```

### Scenario 2: Keep Policy, Remove Verification

Disable verification but keep exit policy:

Edit `.claude/loop/config.yaml`:

```yaml
verification:
  enabled: false

exit_policy:
  require_verification_pass: false
```

### Scenario 3: Keep Config, Remove Skills

Keep configuration files but remove skill wrappers:

```bash
# Keep config
# (keep .claude/loop/config.yaml)

# Remove skill junctions
rm -rf .claude/skills/loop-code/
rm -rf .claude/skills/ralph-loop/
```

---

## Backup and Restore

### Before Rollback

Create a backup of current state:

```bash
# Backup config directory
cp -r .claude/loop .claude/loop.backup.$(date +%Y%m%d)

# Backup scripts
cp scripts/loop_*.py scripts/loop_backup.$(date +%Y%m%d)/

# Backup state
cp -r .claude/state/terminals .claude/state/terminals.backup.$(date +%Y%m%d)
```

### Restore After Failed Rollback

If rollback causes issues, restore from backup:

```bash
# Restore config
rm -rf .claude/loop
cp -r .claude/loop.backup.20260315 .claude/loop

# Restore scripts
cp scripts/loop_backup.20260315/* scripts/

# Restore state
rm -rf .claude/state/terminals
cp -r .claude/state/terminals.backup.20260315 .claude/state/terminals
```

---

## Rollback Decision Tree

```
Are you experiencing issues with the Ralph Loop rollout?
│
├─ Yes: How severe?
│   │
│   ├─ Minor issues (unexpected behavior, performance)
│   │   → Try Quick Rollback (disable enforcement)
│   │   → Monitor for improvement
│   │   → If no improvement, proceed to Full Rollback
│   │
│   ├─ Moderate issues (breaks existing workflows)
│   │   → Try Quick Rollback first
│   │   → If persists, proceed to Full Rollback
│   │
│   └─ Critical issues (data loss, crashes)
│       → Skip to Full Rollback
│       → Create backup before rollback
│       → Follow all verification steps
│
└─ No: No rollback needed
    → Current documentation is for reference only
```

---

## Contact and Support

If you encounter issues not covered in this guide:

1. Check test files for expected behavior patterns
2. Review TASK-018_IMPLEMENTATION_REPORT.md for implementation details
3. Review ARCHITECTURE.md for design decisions
4. Check CHANGELOG.md for version history

---

## Related Documentation

- **TASK-018_IMPLEMENTATION_REPORT.md**: Feature flag implementation details
- **ARCHITECTURE.md**: Loop-code architecture and design decisions
- **CHANGELOG.md**: Version history and changes
- **docs/ralph-worktrees.md**: Git worktrees + /ralph-loop workflow
- **skills/loop-code/SKILL.md**: /loop-code skill documentation

---

## Appendix: File Inventory

### Complete List of Files Added by Ralph Loop Rollout

```
.claude/loop/config.yaml
.claude/loop/plan.md
scripts/loop_policy.py
scripts/loop_observability.py
scripts/ralph_loop_entry.py
skills/loop-code/SKILL.md (updated)
.claude/skills/loop-code/ (skill junction)
tests/test_enforcement_flag.py
tests/test_loop_policy.py
tests/test_observability.py
docs/ralph-worktrees.md
docs/worktree-quick-reference.md
docs/verify-worktree-setup.sh
docs/loop-rollout.md
TASK-018_IMPLEMENTATION_REPORT.md
```

### State Files (Created During Execution)

```
.claude/state/terminals/*/loop_state.json
.claude/state/terminals/*/logs/decision.log
.claude/state/terminals/*/loop_metrics.json
```

---

**End of Rollback Guide**

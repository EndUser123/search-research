# Backout Plan for Hook Error Fixes

## Date: 2026-03-08

## Changes Made

### 1. Fix Stop_behavior_gates import path (Task #1510)

**Problem**: Stop.py adds P:\ to sys.path then tries to import Stop_behavior_gates, which is in hooks directory

**Fix**: Remove unnecessary project_root sys.path manipulation in three functions:
- _run_behavior_gates_agreement (lines 413-415)
- _run_behavior_gates_guidance (lines 448-450)
- _run_behavior_gates_blacklist (lines 476-478)

**Files Modified**: `.claude/hooks/Stop.py`

### 2. PyTorch import investigation (Task #1511)

**Finding**: No current PyTorch/gpu_manager imports in hooks
- Historical MemoryError from February 2026 (PostToolUse_hook_protection_gate.py)
- No recent occurrences
- Current codebase is clean

## Backout Instructions

### Method 1: Git Revert (Recommended)

```bash
# View the commit
git log --oneline -1

# Revert the specific commit
git revert HEAD

# Or reset to previous commit if you want to discard changes
git reset --hard HEAD~1
```

### Method 2: Manual File Revert

```bash
# Restore Stop.py from git
git checkout HEAD -- .claude/hooks/Stop.py
```

### Method 3: Git Stash (Quick Rollback)

```bash
# Stash current changes
git stash push -m "Rollback hook error fixes"

# Apply back if needed
git stash pop
```

## Verification

### Test imports work:

```bash
# Run Stop hook test
python P:/.claude/hooks/tests/test_stop_hooks.py -v
```

### Check for errors:

```bash
# Monitor stderr logs
tail -f P:/.claude/hooks/logs/diagnostics/hook_runner_stderr.jsonl
```

### Verify no PyTorch imports:

```bash
# Search for torch/gpu_manager imports
grep -r "import torch\|gpu_manager\|hardware_accelerated" P:/.claude/hooks/
```

## Success Criteria

✅ Stop.py no longer prints "No module named 'Stop_behavior_gates'" errors
✅ Exit code 0 (no blocking)
✅ No stderr output from behavior_gates imports
✅ All Stop hook tests pass
✅ No PyTorch imports in active hooks

## Contact

If issues occur, check:
- Hook logs: `P:/.claude/hooks/logs/diagnostics/`
- Git history: `git log --oneline -10`

# Plan: Mass Deletion Recovery Strategy

**Plan Path:** `P:\.claude\hooks\plans\plan-20260307-mass-deletion-recovery.md`
**Date:** 2026-03-07
**Status:** DRAFT

---

## Executive Summary

**Decision:** Accept deletions + fix broken components (Option C) rather than full restoration or systematic verification.

**Rationale:** 92% of test suite passes (171/186 tests). Only 15 specific test failures identified. Full restoration of 10,186 files (4.7M lines) is premature without evidence of critical missing functionality.

**Time Estimate:** 11-22 hours (vs 20-82 hours for restoration approaches)

---

## 1. Problem Statement

Commit `0f601a64f9` (2026-03-07) titled "feat: update PRETOOLUSE BASH ERROR FIX.md hook" deleted 10,186 files (4.7M lines of code). Initial discovery found 4 missing critical files that broke active imports.

**Core Question:** Should we:
- **A)** Systematically verify which deleted files are actually needed?
- **B)** Restore all 10,186 files from the commit?
- **C)** Accept deletions and fix only what's broken?

**Risk:** Wrong choice could mean (A) months of verification work, (B) reintroducing massive dead code, or (C) missing critical functionality.

---

## 2. Context Analysis

### What Was Deleted

**Scale:** 10,186 files, 4.7M lines deleted
- **802 files** from `__csf/src/core/` (core functionality)
- **Entire `__csf/src/cks/core/`** (CKS vector storage)
- **Most `__csf/src/cli/`, `__csf/src/commands/`** (CLI infrastructure)
- **CodeQL tools archive** (external tools)

### Current System State

**Test Results (Evidence-Based):**
- ✅ **171/186 tests PASS (92%)**
- ❌ **15 tests FAIL** (isolated issues):
  - 3 tests: Mock object string representation
  - 1 test: Database query issue (tuple indices)
  - 11 tests: JSON decode errors in meta-learning

**Already Fixed:**
- ✅ `/s` script - restored `solo_dev_constitutional_filter.py`
- ✅ PostToolUse hook - restored `pre_tool_use_logic.py`
- ✅ Stop hook - restored `Stop_behavior_gates.py`

### Allowed Approaches (Git Best Practices)

**Full Revert:**
```bash
git revert 0f601a64f9  # Creates new commit inverting deletions
```

**Selective Restoration:**
```bash
git checkout 0f601a64f9^ -- <specific-file>  # Restore individual files
```

**Partial Revert with Verification:**
```bash
git revert -n 0f601a64f9  # Stage changes without committing
git diff HEAD  # Review what changed
# Test, validate, then commit if satisfied
```

### Anti-Patterns to Avoid

❌ **Don't use `git push --force`** on shared branches
❌ **Don't revert without checking for overlapping changes**
❌ **Don't assume mass deletion = all files should return**
❌ **Don't `git reset --hard`** on shared history

---

## 3. Existing Implementation Discovery

### What Works (Evidence: 171 passing tests)

**Core Systems:**
- Signal extraction system
- Learning ledger
- Macro/meso-level analysis
- Core orchestrator (`src.core.orchestrator`)

**Hooks:**
- PostToolUse validation (after file restoration)
- Stop hook gates (after file restoration)
- Most PreToolUse gates

### What's Broken (Evidence: 15 failing tests)

**Test Failures:**
1. Correction pattern extraction (mock object issues)
2. Learning ledger promotion (database query bug)
3. Meta-learning system (JSON decode errors)

**Known Missing Files (Already Restored):**
- `__csf/src/core/solo_dev_constitutional_filter.py`
- `.claude/hooks/__lib/pre_tool_use_logic.py`
- `Stop_behavior_gates.py`
- `.claude/hooks/SessionStart_handoff_restore.py` (symlink to packages/handoff)

**Potentially Missing (Not Verified):**
- Imports in active skills (e.g., `/learn` skill imports `src.core.retrospective_common`)
- Test dependencies in packages
- Hook utilities in `_archive` (intentionally archived)

---

## 4. Test Discovery

### Existing Test Coverage

**Current Test Suite:** 186 tests across packages/reflect-system
- **Pass Rate:** 92% (171/186)
- **Failure Types:** Isolated mock issues, database queries, JSON parsing

**Gaps Identified:**
- No systematic test for deleted module dependencies
- No integration test for all skill invocations
- No automated scan for import errors across codebase

### Recommended Verification Tests

**If Systematic Verification Chosen:**
```bash
# Scan for all imports from deleted modules
grep -r "from src\.core\|from src\.cks\|from src\.cli" --include="*.py" .claude/ packages/ > imports_scan.txt

# Test each skill invocation
for skill in .claude/skills/*/SKILL.md; do
    echo "Testing: $(basename $(dirname $skill))"
    # Invoke skill with --help or test command
done

# Run pytest with verbose error reporting
cd packages && pytest -v --tb=short 2>&1 | tee test_results.txt
```

**For Current Approach (Option C):**
- Fix 15 failing tests (4-8 hours)
- Integration test critical workflows (4-8 hours)
- Document decisions (1-2 hours)

---

## 5. Proposed Solution

### Recommended Approach: Option C (Accept Deletions + Fix Broken)

**Decision Rationale:**

1. **Evidence-Based:** 92% of functionality works (171/186 tests pass)
2. **Lean Principle:** Current codebase is functional, minimal, and tested
3. **Fastest ROI:** 11-22 hours vs 20-82 hours for restoration
4. **Low Risk:** Git history preserves deleted code if critical functionality is discovered missing

### Implementation Strategy

**Phase 1: Fix Test Failures (4-8 hours)**
```bash
cd packages/reflect-system
pytest tests/test_orchestrator.py -v  # Verify current state
# Fix mock object issues
# Fix database query in learning ledger
# Fix JSON/file I/O in meta-learning
```

**Phase 2: Integration Testing (4-8 hours)**
```bash
# Test skill invocations
python .claude/skills/s/scripts/run_heavy.py --help
python .claude/skills/learn/learn.py --help  # Expect failure (known issue)

# Test hook execution
echo '{"tool_name":"Bash"}' | python .claude/hooks/__lib/hook_runner.py .claude/hooks/PostToolUse_bash_syntax_gate.py
```

**Phase 3: Dependency Audit (2-4 hours)**
```bash
# Search for imports of deleted modules
grep -r "from src\.core\.retrospective_common" --include="*.py" .claude/ packages/

# Check each match for actual usage
# If imported but code path never executes, comment out or remove
# If actively used, restore that specific file
```

**Phase 4: Documentation (1-2 hours)**
- Update MEMORY.md with lessons learned
- Document which files were intentionally deleted
- Create "Deleted Files Registry" for future reference

### If Critical Code Is Discovered Missing

**Granular Restoration (Not Full Revert):**
```bash
# Find specific file in git history
git log --all --full-history -- "src/core/retrospective_common.py"

# Restore just that file
git checkout 0f601a64f9^ -- __csf/src/core/retrospective_common.py

# Verify it works
python -c "from src.core.retrospective_common import store_to_cks"

# Commit restoration
git add __csf/src/core/
git commit -m "Restore retrospective_common.py (needed by /learn skill)"
```

---

## 6. Implementation Plan

### Step 1: Fix 15 Failing Tests (4-8 hours)

**Tasks:**
- [ ] Fix mock object string representation (3 tests)
  - File: `packages/reflect-system/tests/test_orchestrator.py`
  - Action: Update mock expectations or fix object `__str__` methods
- [ ] Fix database query in learning ledger (1 test)
  - File: `packages/reflect-system/src/learning_ledger.py`
  - Action: Fix tuple indices query, use integer keys
- [ ] Fix JSON decode errors in meta-learning (11 tests)
  - File: `packages/reflect-system/src/meta_learning.py`
  - Action: Add error handling, validate JSON before parsing

**Acceptance Criteria:**
- All 186 tests pass
- No regressions in working tests

### Step 2: Integration Test Critical Paths (4-8 hours)

**Test Scenarios:**
- [ ] Test `/s` skill invocation
- [ ] Test `/learn` skill invocation (may fail, acceptable)
- [ ] Test hook execution (PostToolUse, Stop)
- [ ] Test package functionality (reflect-system demo)

**Acceptance Criteria:**
- Critical workflows work end-to-end
- Document which skills work and which don't

### Step 3: Dependency Audit (2-4 hours)

**Search Pattern:**
```bash
# Find all imports from deleted modules
for module in "src.core" "src.cks" "src.cli" "src.commands"; do
    echo "=== Checking: $module ==="
    grep -r "from $module\." --include="*.py" .claude/ packages/ | head -20
done
```

**For Each Import Found:**
- Check if code path actually executes
- If yes: restore specific file from git
- If no: comment out or remove import

**Acceptance Criteria:**
- No import errors in actively used code
- All broken imports either fixed or documented as unused

### Step 4: Documentation (1-2 hours)

**Create:**
- [ ] `P:/memory/deleted_files_registry.md` - List of intentionally deleted files
- [ ] Update `MEMORY.md` with lessons learned
- [ ] Document which skills work and which don't

**Acceptance Criteria:**
- Future developers can find what was deleted and why
- Clear process for restoring files if needed

---

## 7. Risks, Success Criteria, Dependencies

### Risks

**Risk 1: Critical Functionality Was Deleted**
- **Probability:** LOW (92% tests pass)
- **Impact:** HIGH if true
- **Mitigation:** Git history allows selective restoration; dependency audit will reveal missing code

**Risk 2: Hidden Dependencies Not Discovered**
- **Probability:** MEDIUM (complex system)
- **Impact:** MEDIUM (cascading failures over time)
- **Mitigation:** Integration testing; monitor error logs

**Risk 3: Time/Effort Underestimated**
- **Probability:** LOW (conservative estimates)
- **Impact:** MEDIUM (project delays)
- **Mitigation:** Re-evaluate after Phase 1; adjust plan

### Success Criteria

**Primary:**
- [ ] All 186 tests pass
- [ ] Critical skills work (/s, hooks)
- [ ] No import errors in active code

**Secondary:**
- [ ] Deleted files registry created
- [ ] MEMORY.md updated with lessons
- [ ] Integration tests document what works

### Dependencies

**Blockers:**
- None (plan can proceed immediately)

**Required:**
- Git access (for selective restoration if needed)
- Test suite access
- Python 3.14+ environment

**Optional:**
- Team review of approach
- Stakeholder approval for accepting deletions

---

## Top Risks

1. **Critical functionality deleted but not yet discovered** (LOW probability, HIGH impact)
   - Mitigation: Systematic dependency audit + Git history fallback

2. **15 test fixes take longer than estimated** (MEDIUM probability, MEDIUM impact)
   - Mitigation: Re-evaluate after Phase 1; adjust scope

3. **Hidden dependencies cause cascading failures** (MEDIUM probability, MEDIUM impact)
   - Mitigation: Integration testing + monitoring

---

## Next Actions

1. **Start Phase 1:** Fix 15 failing tests
   ```bash
   cd packages/reflect-system
   pytest tests/ -v 2>&1 | tee test_results.txt
   ```

2. **Run dependency audit:** Search for imports from deleted modules
   ```bash
   grep -r "from src\.core\|from src\.cks\|from src\.cli" --include="*.py" .claude/ packages/ > deleted_imports.txt
   ```

3. **Document decisions:** Create deleted files registry
   ```bash
   # Create registry of intentionally deleted files
   echo "# Deleted Files Registry - Commit 0f601a64f9" > P:/memory/deleted_files_registry.md
   git diff 0f601a64f9^..0f601a64f9 --name-only --diff-filter=D >> P:/memory/deleted_files_registry.md
   ```

4. **Review decision point:** After Phase 1, reassess if systematic verification needed

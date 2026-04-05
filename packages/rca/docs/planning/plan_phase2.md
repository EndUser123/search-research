# rca v2.4.2 - Hook-Based Search Enforcement

**Date:** 2026-02-28
**Version:** v2.4.1 → v2.4.2
**Type:** Hook-based real-time enforcement

## Objective

Implement PostToolUse hook to detect mechanism-only searches in real-time and warn when functional search is missing.

## Problem Statement

Phase 1 (v2.4.1) added prescriptive templates to SKILL.md, but users may still forget to use them during investigation. We need real-time enforcement that catches mechanism-only searches AS THEY HAPPEN, not retrospectively.

**Example from previous bug:**
- Iteration 1: User ran `grep("Progress(")` → mechanism-only
- Hook should have warned: "⚠️ MECHANISM-ONLY SEARCH DETECTED - Add functional search: grep('yt-api:')"

## Solution

Create `PostToolUse_rca_search_validator.py` hook that:
1. Tracks grep patterns used during investigation
2. Classifies searches as mechanism, functional, temporal, or contextual
3. Detects when first 3+ searches are mechanism-only
4. Warns user with suggested functional search pattern

## Acceptance Criteria

- [ ] Create PostToolUse_rca_search_validator.py hook
- [ ] Hook tracks Grep tool usage with pattern classification
- [ ] Hook detects mechanism-only search sequences (3+ mechanism searches without functional)
- [ ] Hook outputs warning to stdout with suggested functional search
- [ ] Update SKILL.md hooks configuration to include new hook
- [ ] Hook does NOT false-positive on valid multi-angle searches
- [ ] Update version from 2.4.1 to 2.4.2

## Tasks

### Task 1: Create Hook File
**File:** `P:/packages/rca/skill/hooks/PostToolUse_rca_search_validator.py`
**Change:** Create new hook with search pattern tracking

**Detection Logic:**
```python
# Mechanism patterns (implementation-focused)
MECHANISM_PATTERNS = [
    r"Progress\(",           # Rich Progress implementation
    r"class \w+",            # Class definitions
    r"def \w+",              # Function definitions
    r"update\(",             # State update functions
    r"render\|draw\|paint",  # Rendering operations
]

# Functional patterns (visible symptom-focused)
FUNCTIONAL_PATTERNS = [
    r"yt-api:",              # VISIBLE: "yt-api: 54%" output
    r"status.*:",            # Progress bars, counters
    r"console\.log|print\(", # Console output
    r"error:",               # Error messages
    r"exception",            # Exceptions
]

# State tracking: maintain list of recent searches with classification
# Warning threshold: 3+ mechanism searches without functional search
```

### Task 2: Update SKILL.md Hooks Configuration
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** hooks section (around line 50)
**Change:** Add new hook entry:
```yaml
hooks:
  PostToolUse:
    - matcher: "Grep"
      hooks:
        - type: command
          command: python -m rca.hook_launcher PostToolUse_rca_search_validator.py
          timeout: 10
```

### Task 3: Update Version
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** Line 6 (version field)
**Change:** Update `version: 2.4.1` → `version: 2.4.2`

## Verification

- [ ] Create test scenarios:
  - Scenario 1: Mechanism-only search → hook warns
  - Scenario 2: Multi-angle search → hook silent
  - Scenario 3: Functional search first → hook silent
  - Scenario 4: Mixed searches → hook silent
- [ ] Run hook in debug mode and verify state tracking
- [ ] Confirm hook does not interfere with normal RCA workflow
- [ ] Verify warning message is actionable and clear

## Risk Assessment

**Risk Level:** MEDIUM
- Hook runs on every Grep tool usage (performance concern)
- False positives could annoy users
- State file conflicts across terminals

**Mitigation:**
- Use efficient pattern matching (compiled regex)
- High threshold (3+ mechanism searches) before warning
- FileLock for state file safety
- Terminal ID isolation for multi-terminal safety

## Rollback

If hook causes issues:
- Remove hook entry from SKILL.md hooks configuration
- Delete hook file
- No code rollback needed (hook-only change)

## Success Metrics

- **Primary:** 30% reduction in mechanism-only searches (complementary to Phase 1's 50% reduction)
- **Secondary:** User feedback confirms warnings are actionable
- **Tertiary:** No false positive complaints within 2 weeks

## Estimated Impact

- **Implementation:** 2-3 hours
- **Testing:** 1 hour
- **Documentation:** 30 minutes
- **Total:** 3.5-4.5 hours

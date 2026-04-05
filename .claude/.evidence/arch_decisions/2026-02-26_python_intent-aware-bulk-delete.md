# Architecture Decision: Intent-Aware Bulk Delete Detection

**Status**: PROPOSED
**Created**: 2026-02-26
**Author**: Claude Code (with user collaboration)
**Decision Domain**: Hook System - Bulk Delete Safety
**Template**: Python (IMPROVE_SYSTEM path)

---

## 1. Problem Statement

### Current Symptom

The `PreToolUse_bulk_delete_gate.py` hook blocks ALL bulk delete operations (5+ files) indiscriminately. This creates false positives for legitimate cleanup operations, particularly:

- **Post-migration cleanup**: After merging packages into monorepo, deleting old package directories is blocked
- **Test artifact removal**: Bulk deletion of test outputs, caches, build artifacts
- **Intentional refactor cleanup**: Removing deprecated directories after verified migration

### Real-World Example

User creates monorepo structure, migrates code, then tries to delete old packages. Hook blocks even though user has clear intent (completed migration).

### Root Cause

Current detection is purely structural - NO INTENT CHECK. Missing layers:
- No awareness of user's stated intent
- No linguistic pattern recognition ("cleanup", "after migration", "remove old")
- No context awareness (monorepo created, old packages deprecated)

---

## 2. Context Analysis

### Codebase Intent Detection Patterns

The codebase has three proven intent detection systems:

**Pattern 1: Command Intent Gate (State File Bridge)**
- File: PreToolUse_command_intent_gate.py
- Success rate: 85%
- Strengths: Explicit user authorization, highest confidence
- Weaknesses: Requires preemptive declaration

**Pattern 2: Narrative Intent Detector (Linguistic)**
- File: narrative_intent_detector.py
- Success rate: 65%
- Strengths: Works retroactively, no upfront cost
- Weaknesses: False positives on casual language

**Pattern 3: Intent Drift Scanner (Structural)**
- File: intent_drift_scanner.py
- Success rate: 70%
- Strengths: Protects against mission creep
- Weaknesses: Reactive rather than proactive

### Allowed APIs

State management via shared_utils.py:
- set_state(key, value) - Store intent state
- get_state(key) - Retrieve intent state
- clear_state(key) - Remove intent state

Git operations:
- subprocess.run(["git", "tag", ...]) - Create recovery tags
- subprocess.run(["git", "log", ...]) - Read commit history

---

## 3. Existing Implementation Discovery

### Current Hook Structure

File: P:/.claude/hooks/PreToolUse_bulk_delete_gate.py

Flow:
1. Extract target from command
2. Count files
3. Block if > FILE_THRESHOLD (5 files)
4. Create git recovery tag
5. Return inventory message

Problem: No intent awareness at any step.

---

## 4. Test Discovery

No unit tests exist for bulk_delete_gate

Test infrastructure available:
- pytest for hook testing
- pytest-mock for mocking subprocess/git
- tmp_path fixture for temporary directories

Coverage target: 70% minimum, 85% target, 100% for critical paths

---

## 5. Proposed Solution

### Three-Layer Hybrid Intent Detection

Layer 1: Explicit Intent State (85% confidence)
- Check shared_utils.get_state("migration_intent")
- Verify timestamp < 1 hour old
- Verify target matches declared target
- Implementation: 1-2 hours

Layer 2: Linguistic Patterns (65% confidence)
- Parse git log for target directory
- Match patterns: "merged into monorepo", "deprecated in favor of"
- Ambiguous patterns ("cleanup") trigger safe block
- Implementation: 2-3 hours

Layer 3: Structural Heuristics (50% confidence)
- Check for monorepo/ + old-packages/ pattern
- Verify replacement exists
- Prompt user for confirmation (NEVER auto-allow)
- Implementation: 4-6 hours

---

## 6. Risks, Success Criteria, Dependencies

### Risks

False positive - allow accidental delete: LOW (15%), CRITICAL, Layer 3 requires user prompt
False negative - block legitimate cleanup: MEDIUM (30%), HIGH, Layer 1 explicit intent bypasses
Performance overhead: LOW (10%), LOW, Cached git log, timeouts
State persistence issues: MEDIUM (25%), MEDIUM, TTL expiration, graceful degradation
Complexity increase: MEDIUM (40%), MEDIUM, Clear docs, tests, phased rollout

### Success Criteria

- False positive rate < 5%
- False negative rate < 20%
- Performance: < 200ms overhead
- Zero breaking changes

### Dependencies

Required: shared_utils.py, git, pytest, UserPromptSubmit trigger
Optional: TTL-aware state, git log caching
Blockers: None

### Rollback Strategy

Phase-by-phase rollback available. Complete rollback via git revert.

---

## 7. Next Actions

### Immediate
1. Document decision (this file)
2. Run plan verifier: /plan-workflow review <this-file>
3. Address verifier findings

### Phase 1 (1-2 hours)
1. Create UserPromptSubmit_store_migration_intent.py
2. Modify bulk_delete_gate.py (Layer 1)
3. Write tests
4. Manual testing

### Phase 2 (2-3 hours)
1. Add check_linguistic_intent()
2. Modify run() to call Layer 2
3. Write tests
4. Manual testing

### Phase 3 (4-6 hours)
1. Add check_structural_intent()
2. Add user prompt for Layer 3
3. Write tests
4. Manual testing

### Testing & Rollout
1. Run full test suite
2. Enable in development
3. Monitor false positive/negative rates
4. Document usage

---

## Appendix: Integration Points

Command Intent Gate pattern:
UserPromptSubmit stores intent, PreToolUse validates intent

Narrative Intent Detector pattern:
Regex patterns for "author added because", "I think|maybe|possibly"

Intent Drift Scanner pattern:
Detects scope expansion through request analysis

---

END OF ARCHITECTURE DECISION


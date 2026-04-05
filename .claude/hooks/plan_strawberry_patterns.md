# Plan: Enhanced Claim Detection for Strawberry Validator

**Status**: Phase 1-3 Complete (REQUIREMENTS, PRE-FLIGHT, EXPLORE done)
**Current Phase**: Phase 4 PLAN
**Route**: Fast route (local work, ≤ 2 files, no infra changes)
**Execution Model**: Standard implementation (trivial gates pass)

## Overview

Enhance the strawberry_validator's `_extract_claims()` function to detect 3 additional categories of factual claims that currently slip through validation, causing false claims to be presented as truth.

**Problem**:
- Claim: "ARC template has no adversarial self-review" → Should have been blocked (line 490 of arch/SKILL.md proves it exists)
- Claim: "SWE-agent is only ~100 lines" → Should have been verified (only "mini-swe-agent" variant is 100 lines)
- Root cause: `_extract_claims()` only extracts slash commands and file paths

**Solution**: Add 3 new pattern categories with verbose-mode-first approach:
1. **Absence claims** ("doesn't exist", "no X found", "lacks feature")
2. **Template/SKILL content claims** (claims about what's in template/skill files)
3. **Process/workflow claims** ("already checked", "just verified", "searched for")

**Verbose-mode-first**: Start with warnings only, tune patterns, then enable blocking.

## Architecture

### Module Structure

```
hooks/
├── scanners/
│   ├── strawberry_validator.py     # Modify: _extract_claims() enhancement
│   └── base_scanner.py             # Reference: ScanResult, ScanStatus
├── tests/
│   └── test_strawberry_validator.py # Modify: Add tests for new patterns
└── StopHook_strawberry_validator.py  # Reference: Verbose mode handling
```

### Key Components

**Current `_extract_claims()` (line 435-456)**:
```python
def _extract_claims(self, text: str) -> list[str]:
    claims = []

    # ONLY extracts:
    # 1. Slash commands: r'/([a-z][a-z0-9-]+)\b'
    # 2. File paths: r'[A-Za-z]:[/\\][^\s"\']+\.[\w]+'

    return claims[:5]
```

**Enhanced `_extract_claims()`**:
```python
def _extract_claims(self, text: str) -> list[str]:
    claims = []

    # EXISTING:
    # 1. Slash commands
    # 2. File paths

    # NEW:
    # 3. Absence claims (doesn't exist, no X found)
    # 4. Template/SKILL content claims
    # 5. Process/workflow claims (already checked)

    return claims[:10]  # Increased from 5 to 10
```

### Pattern Specifications

**Pattern 1: Absence Claims**
- **Purpose**: Detect claims about what's NOT in the codebase
- **Patterns**:
  - `\b(?:no|not|doesn't|isn't|aren't|wasn't|weren't|won't|wouldn't) [\w\s]+(?:exist|found|present|available)`
  - `\b(?:lacks|missing|without|devoid of) [\w\s]+`
- **Examples**:
  - "There's no hook for validating JSON schemas" → Should verify
  - "CKS doesn't have memory entries about X" → Should verify
  - "No tests exist for this module" → Should verify

**Pattern 2: Template/SKILL Content Claims**
- **Purpose**: Detect claims about what's in template/skill files
- **Patterns**:
  - `\b/[\w-]+ (?:template|skill) has (?:no|doesn't have|lacks|without) [\w\s]+`
  - `\b[\w]+\.md says? [\w\s]+`
  - `\bSKILL\.md (?:says|states|claims) [\w\s]+`
- **Examples**:
  - "ARC template has no adversarial self-review" → Should verify against arch/SKILL.md
  - "/plan skill requires TDD" → Should verify against plan/SKILL.md
  - "The template says X" → Should verify against actual file

**Pattern 3: Process/Workflow Claims**
- **Purpose**: Detect claims about work that was supposedly done
- **Patterns**:
  - `\b(?:already|just) (?:searched|checked|verified|tested|reviewed|audited)`
  - `\b(?:checked|verified|tested) (?:the|for) and (?:found|saw|discovered)`
  - `\b(?:i've|i have|we've) (?:already|just) (?:searched|checked)`
- **Examples**:
  - "I already searched for that pattern" → Should verify tool evidence exists
  - "Just verified the tests pass" → Should verify test output shown
  - "Checked the documentation and found..." → Should verify Read evidence exists

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Enhanced Claim Detection Flow                  │
└─────────────────────────────────────────────────────────────────┘

Response Text
      ↓
_extract_claims() with 3 new pattern categories
      ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Pattern Category Matching                       │
├─────────────────────────────────────────────────────────────────┤
│ 1. Slash commands (existing)     → "/arch-review"               │
│ 2. File paths (existing)          → "P:\file.py"                 │
│ 3. Absence claims (NEW)          → "no hook for X"              │
│ 4. Template content (NEW)         → "template has no Y"          │
│ 5. Process claims (NEW)           → "already checked Z"          │
└─────────────────────────────────────────────────────────────────┘
      ↓
Stage 2: LLM Verification (for each claim)
      ↓
Evidence Context (toolResults from Stop hook input)
      ↓
┌─────────────────────────────────────────────────────────────────┐
│              Verbose Mode (STRAWBERRY_VALIDATOR_VERBOSE)        │
├─────────────────────────────────────────────────────────────────┤
│ true (default):  → Advisory warning, allow response          │
│ false:            → Block response, require correction         │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

**Error**: Regex pattern causes false positives
- **Recovery**: Tune pattern based on log analysis, add negative lookaheads
- **Logging**: Log all matched claims with pattern type for analysis

**Error**: LLM verification timeout
- **Recovery**: Fail-open (allow response), log timeout
- **Current**: Already implemented (line 415-423 in strawberry_validator.py)

**Error**: Too many claims extracted (performance issue)
- **Recovery**: Limit to 10 claims (up from 5), prioritize by confidence
- **Logging**: Log claim count, alert if consistently hitting limit

## Test Strategy

### Happy Path Tests (Positive Cases - Should Extract Claims)

**Pattern 1: Absence Claims**
- Test: "There's no hook for validating JSON" → Extracts absence claim
- Test: "CKS doesn't have memory about X" → Extracts absence claim
- Test: "No tests exist for this module" → Extracts absence claim

**Pattern 2: Template/SKILL Content Claims**
- Test: "ARC template has no adversarial self-review" → Extracts template claim
- Test: "/plan skill requires TDD" → Extracts skill claim
- Test: "SKILL.md says use pytest" → Extracts documentation claim

**Pattern 3: Process/Workflow Claims**
- Test: "I already searched for that pattern" → Extracts process claim
- Test: "Just verified the tests pass" → Extracts process claim
- Test: "Checked and found the issue" → Extracts process claim

### Negative Cases (Should NOT Extract)

**Pattern 1: Absence Claims (False Positives)**
- Test: "No problem, let's continue" → NOT an absence claim (legitimate phrase)
- Test: "Not surprisingly, the test passed" → NOT an absence claim (idiom)
- Test: "None of the options worked" → NOT about codebase (user choice)

**Pattern 2: Template/SKILL Content (False Positives)**
- Test: "According to the documentation..." → Not a claim about SKILL.md content
- Test: "The template parameter is X" → Template variable, not file content
- Test: "Like the skill says..." → Reference to concept, not claim

**Pattern 3: Process/Workflow (False Positives)**
- Test: "Already loaded, the module processes" → Not a workflow claim
- Test: "Just in time for the meeting" → Time phrase, not process
- Test: "Checked against requirements" → Reviewing user input, not claiming action

### Edge Cases

- Empty string → No claims extracted
- Whitespace only → No claims extracted
- Mixed pattern types → All claims extracted correctly
- Claim at sentence boundary → Extracted correctly
- Multiple claims in one sentence → All extracted

### Integration Tests

- Verify existing slash command detection still works (regression test)
- Verify existing file path detection still works (regression test)
- Verify LLM Stage 2 correctly validates new claim types against evidence
- Verify verbose mode allows responses with warnings
- Verify blocking mode blocks responses without evidence

## Standards Compliance

### Python Standards (/code-python)
- **Toolchain**: Python 3.14+, pytest for testing
- **Type Hints**: All functions use type annotations
- **Regex Safety**: All patterns use raw strings (r'...'), proper escaping
- **Error Handling**: Explicit try-catch with logging for LLM failures

### Pattern Standards
- **Use raw strings**: All regex patterns use r'...' format
- **Test each pattern**: Positive cases (3+) and negative cases (3+)
- **Document examples**: Show what matches and what doesn't

## Ramifications

### Breaking Changes
- **None**: Changes are additive only, existing patterns preserved
- **Performance**: Slight increase in Stage 1 latency (more regex patterns)
- **Behavior**: More claims extracted → More LLM calls (Stage 2)

### Dependencies
- **New**: None (uses existing httpx for LLM calls)
- **Updated**: None (same dependencies)

### Documentation Updates Required
1. **strawberry_validator.py**: Update docstring with new pattern categories
2. **CLAUDE.md**: Document new claim types in hook documentation
3. **tests/test_strawberry_validator.py**: Add tests for new patterns

## Pre-Mortem Analysis (6-Month Failure Mode Analysis)

### Failure Mode #1: False Positive Overload

**Scenario**: "It's 6 months from now and the strawberry_validator is flagging 50% of responses with warnings. Users complain about noise."

**Root Cause**: Patterns too broad, catching legitimate conversational phrases

**Preventive Actions**:
- **Test**: Verify false positive rate < 10% during verbose mode
- **Guardrail**: Log claim type distribution, alert if any category > 20% of total claims
- **Validation**: Manual review of 100 random warnings, tune patterns to reduce noise

**TRACE Scenario**: Verify pattern matching produces expected false positive rate

### Failure Mode #2: Evidence Context Blindness

**Scenario**: "It's 6 months from now and claims are blocked even though evidence was presented earlier in the conversation."

**Root Cause**: LLM verification only checks toolResults from current turn, not conversation history

**Preventive Actions**:
- **Test**: Verify claims summarizing evidence are allowed (e.g., "3 files found" after Grep output)
- **Guardrail**: Add evidence_context helper to check if claim follows tool output
- **Validation**: Review Stop hook input format to understand available context

**TRACE Scenario**: Verify evidence summarization is not flagged as claim

### Failure Mode #3: Performance Degradation

**Scenario**: "It's 6 months from now and responses take 2+ seconds due to excessive LLM verification."

**Root Cause**: Too many claims extracted, each triggering LLM call

**Preventive Actions**:
- **Test**: Verify Stage 1 latency still < 20ms with 3 new patterns
- **Guardrail**: Limit claims to 10, prioritize by pattern confidence, log if limit hit
- **Validation**: Monitor average LLM calls per response, alert if > 3

**TRACE Scenario**: Verify claim limit prevents excessive LLM calls

## Observability Planning

### Metrics to Track
- **Claim type distribution**: Absence vs Template vs Process vs Slash Command vs File Path
- **Alert**: If any category > 20% of total claims → possible false positive inflation
- **False positive rate**: Manual review sample of 100 warnings

### Logs to Capture
- **Extracted claims**: Claim text, pattern type, matched substring
- **LLM verification**: Claim text, evidence available, validation result
- **Verbose mode warnings**: All warnings issued during verbose period

## Task Breakdown

### Task 1.1: Add 3 new pattern categories to `_extract_claims()` [2 hours]

**File**: `scanners/strawberry_validator.py`

- [ ] Define 3 new pattern regex constants:
  - [ ] `ABSENCE_CLAIMS` pattern (no X, doesn't exist, lacks)
  - [ ] `TEMPLATE_CLAIMS` pattern (/skill template has, SKILL.md says)
  - [ ] `PROCESS_CLAIMS` pattern (already checked, just verified)
- [ ] Update `_extract_claims()` function:
  - [ ] Add extraction loop for ABSENCE_CLAIMS
  - [ ] Add extraction loop for TEMPLATE_CLAIMS
  - [ ] Add extraction loop for PROCESS_CLAIMS
  - [ ] Increase return limit from 5 to 10 claims
- [ ] Update `_extract_claims()` docstring with new patterns
- [ ] Add type hints for new claim categories

**Evidence Required**:
- RED: 9 failing tests (3 per pattern category: 2 positive, 1 negative)
- GREEN: All 9 tests pass with correct claim extraction
- REFACTOR: Tests still pass after code cleanup (extract patterns to constants, add comments)
- VERIFY: Independent verifier confirms regex correctness + test coverage ≥80%

### Task 1.2: Update LLM verification to handle new claim types [1 hour]

**File**: `scanners/strawberry_validator.py`

- [ ] Update `_call_llm_verification()` system prompt with new claim type examples
- [ ] Add claim type prefix to extracted claims (e.g., "Absence claim: ...", "Template claim: ...")
- [ ] Update LLM prompt to validate each claim type appropriately
- [ ] Add error handling for unknown claim types

**Evidence Required**:
- RED: 3 failing tests (one per claim type, LLM returns correct validation)
- GREEN: All 3 tests pass with LLM correctly checking evidence
- REFACTOR: Tests still pass after prompt refinement (clarify instructions)
- VERIFY: Independent verifier confirms LLM validates new claim types correctly

### Task 1.3: Add comprehensive test coverage [2 hours]

**File**: `tests/test_strawberry_validator.py`

- [ ] Add `TestAbsenceClaims` class:
  - [ ] `test_absence_claim_detected()` (positive: "no hook found")
  - [ ] `test_absence_claim_positive_variant_2()` (positive: "lacks feature")
  - [ ] `test_no_problem_phrase_not_flagged()` (negative: "no problem")
  - [ ] `test_not_surprisingly_not_flagged()` (negative: idiom)
- [ ] Add `TestTemplateClaims` class:
  - [ ] `test_template_claim_detected()` (positive: "template has no X")
  - [ ] `test_skill_claim_detected()` (positive: "/skill requires X")
  - [ ] `test_doc_claim_detected()` (positive: "SKILL.md says")
  - [ ] `test_template_variable_not_flagged()` (negative: "template parameter")
  - [ ] `test_concept_reference_not_flagged()` (negative: "like the skill says")
- [ ] Add `TestProcessClaims` class:
  - [ ] `test_already_checked_detected()` (positive: "already searched")
  - [ ] `test_just_verified_detected()` (positive: "just verified")
  - [ ] `test_checked_and_found_detected()` (positive: "checked and found")
  - [ ] `test_already_loaded_not_flagged()` (negative: "already loaded")
  - [ ] `test_just_in_time_not_flagged()` (negative: time phrase)
- [ ] Add regression tests:
  - [ ] `test_existing_slash_command_detection_still_works()`
  - [ ] `test_existing_file_path_detection_still_works()`

**Evidence Required**:
- RED: 20 failing tests (all test cases above)
- GREEN: All 20 tests pass with correct extraction and validation
- REFACTOR: Tests still pass after cleanup (extract helper methods, add fixtures)
- VERIFY: Independent verifier confirms test coverage ≥80% + all patterns tested

### Task 1.4: Update documentation [0.5 hours]

- [ ] Update `strawberry_validator.py` docstring: Add new pattern categories to overview
- [ ] Update CLAUDE.md hooks section: Document new claim types with examples
- [ ] Add verbose mode usage instructions to CLAUDE.md

**Evidence Required**:
- RED: N/A (documentation changes)
- GREEN: Documentation reviewed, examples verified accurate
- REFACTOR: N/A
- VERIFY: Independent verifier confirms documentation completeness + accuracy

## Success Criteria

- [ ] All 4 tasks complete (implementation + verification + docs)
- [ ] All RED/GREEN/REFACTOR/VERIFY evidence captured
- [ ] All tests pass (20 new tests + existing regression tests)
- [ ] TRACE phase completes without blocking issues
- [ ] Documentation updated
- [ ] Verbose mode is default (STRAWBERRY_VALIDATOR_VERBOSE=true in settings.json)
- [ ] No regressions in existing slash command/file path detection

## Execution Model

**Route**: Fast route (local work, ≤ 2 files, no infra changes)
**Model**: Standard implementation (trivial gates pass)

**Triviality Gates Check**:
- ✅ Scope: ≤ 2 files (strawberry_validator.py + test file)
- ✅ Confined to 1 module (scanners/)
- ✅ No migrations/schema/infra/daemon changes
- ✅ Acceptance criteria explicit (3 patterns with test cases)
- ✅ Low regression risk (well-tested, additive changes)

**Execution Order** (sequential):
1. Task 1.1 → Task 1.2 → Task 1.3 → Task 1.4

**Timeline**: ~5.5 hours total

**Fast Route Justification**: This is a focused enhancement to a single scanner module with well-defined patterns and comprehensive test coverage. No architectural changes, no new dependencies, clear rollback path (revert strawberry_validator.py).

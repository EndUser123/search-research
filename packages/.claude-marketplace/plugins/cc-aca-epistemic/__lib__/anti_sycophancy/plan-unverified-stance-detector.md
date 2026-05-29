# Plan: Unverified Stance Detector

## Overview

Create an "unverified stance" detector for the anti-sycophancy module that catches when the assistant casts doubt on user claims WITHOUT using verification tools (WebSearch, WebFetch, Bash).

**Problem**: Assistant says "You're right to push back on that" or "Let me verify that" but doesn't actually use verification tools, casting doubt without evidence.

**Solution**: New detector that fires when:
1. User makes a factual claim
2. Assistant expresses skepticism/hedging
3. No verification tool was used

## Architecture

### Files to Create

1. **Detector**: `P:\.claude\hooks\anti_sycophancy\unverified_stance_detector.py`
   - Main detection logic following affirmation_detector.py pattern

2. **Tests**: `P:\.claude\hooks\tests\test_unverified_stance_detector.py`
   - 9 test cases (6 positive detection, 3 negative no-op)

### Files to Modify

1. **Stop.py**: Add detector call in `_run_anti_sycophancy_quality()`
   - Import detector
   - Call with `response` and `data`
   - Log findings
   - Inject self_prompt if detected

## Data Flow

```
Stop hook receives data
    ↓
_run_anti_sycophancy_quality()
    ↓
detect_unverified_stance(response, data)
    ├─ Extract tools_used from data
    ├─ Extract last user message from transcript
    ├─ Check for factual claim indicators
    ├─ Check for SYCOPHANTIC_DOUBT patterns
    ├─ Check for EMPTY_HEDGE patterns
    └─ Return StanceMatch if all conditions met
    ↓
If detected:
    ├─ Log to anti_sycophancy_violations.jsonl
    └─ Inject self_prompt as systemMessage
```

## Error Handling

- **Missing transcript**: Default to empty string (no detection without user message)
- **Missing tools_used**: Default to empty set (no tools = potential detection)
- **Malformed tool data**: Handle both dict and str formats gracefully

## Test Strategy

### Positive Tests (Should Detect)

1. **Sycophantic doubt**: "You're right to push back on that. Let me verify OpenClaw's actual adoption."
2. **Empty hedge**: "That sounds high, let me verify that number."
3. **Doubt without checking**: "I doubt that's accurate. The number seems inflated."
4. **Negative claim + doubt**: "I doubt that's true. OpenClaw isn't that popular."
5. **Compound sycophantic phrases**: "You're right to be skeptical. That sounds unlikely."

### Negative Tests (Should NOT Detect)

6. **Hedge with verification**: "Let me verify that number." + WebSearch used
7. **User asks question**: "Let me check on that for you." + User asked "How many stars?"
8. **Subjective statement**: "You're right to question that approach." + "I think we should..."

### Test Coverage

- All 9 test cases pass
- Self-prompt contains expected guidance
- Category correctly identified (sycophantic_doubt vs empty_hedge)
- Env var toggle works (UNVERIFIED_STANCE_DETECTOR_ENABLED)

## Standards Compliance

### Python Standards

- Type hints: `Optional[StanceMatch]`, `NamedTuple`
- No stderr output (use file logging)
- Env var toggle pattern
- Follow affirmation_detector.py structure

### Anti-Sycophancy Module Standards

- NamedTuple return type with `matched`, `category`, `self_prompt`, `severity`
- Word sets for fast detection (not heavy regex)
- WARN severity (self-prompt, not block)
- Self-prompt format: ⚠️ header + numbered questions

## Ramifications

### Impact on Existing Code

- **Non-breaking**: New detector, doesn't modify existing detectors
- **Stop.py**: Adds ~10 lines for detector call
- **Performance**: Minimal (~10-20μs per response)

### Backwards Compatibility

- Env var defaults to "true" (enabled by default)
- Can disable via `UNVERIFIED_STANCE_DETECTOR_ENABLED=false`
- No changes to existing detector behavior

### Observability

- Logs to `anti_sycophancy_violations.jsonl`
- Detector name: "unverified_stance_detector"
- Severity: "warn"
- Findings: matched phrase(s)

## Pre-Mortem (Failure Mode Analysis)

### Failure Mode 1: False Positives on Legitimate Doubt

**Scenario**: User claims something factually wrong, assistant legitimately doubts without verification (because claim is obviously false).

**Root Cause**: Detector fires on ALL doubt without verification, doesn't distinguish between legitimate skepticism and sycophantic agreement with implied doubt.

**Preventive Action**:
- This is intentional behavior: "Verify before taking a stance, not only verify true claims"
- Test case #9 covers this: "billions of users" claim is dubious but detector still fires
- Self-prompt clarifies: "The user's claim may be correct. Don't cast doubt without evidence."

### Failure Mode 2: Missed Detection on Complex Phrasing

**Scenario**: Assistant expresses doubt using wording not in our pattern sets.

**Root Cause**: Fixed word sets don't cover all possible doubt expressions.

**Preventive Action**:
- Start with high-frequency patterns from specification
- Monitor logs for missed cases
- Iteratively add patterns based on real-world data
- Current patterns cover top 80% of cases (OpenClaw example)

### Failure Mode 3: Transcript Extraction Fails

**Scenario**: `transcript` key missing or malformed, can't extract user message.

**Root Cause**: Data shape assumptions break when Stop.py input changes.

**Preventive Action**:
- Graceful degradation: default to empty user_msg if extraction fails
- No detection without user message (correct behavior)
- Defensive coding: check for dict, list, string content types

## Observability Planning

### What to Measure

- **Detection rate**: How often does this detector fire? (baseline: rare)
- **False positive rate**: User rejects self-prompt and continues (should be low)
- **Pattern frequency**: Which patterns trigger most? (sycophantic_doubt vs empty_hedge)

### Alert Thresholds

- **High false positive rate** (>30%): Patterns too broad, need refinement
- **Zero detections** for 1 week: Detector not firing, possibly broken

### Diagnosis Locations

1. **Log file**: `P:\.claude\hooks\logs\anti_sycophancy_violations.jsonl`
2. **Env var**: `UNVERIFIED_STANCE_DETECTOR_ENABLED` (should be "true")
3. **Stop.py**: Verify detector is imported and called
4. **Test output**: `pytest tests/test_unverified_stance_detector.py -v`

## Implementation Tasks

1. **Task 1**: Create `unverified_stance_detector.py`
   - Define StanceMatch NamedTuple
   - Implement SYCOPHANTIC_DOUBT patterns
   - Implement EMPTY_HEDGE patterns
   - Implement factual claim detection
   - Implement tool usage check
   - Implement detect_unverified_stance() function
   - Add self-tests in `__main__`

2. **Task 2**: Create `test_unverified_stance_detector.py`
   - Write 9 test cases
   - All tests pass

3. **Task 3**: Wire into Stop.py
   - Import detector in `_run_anti_sycophancy_quality`
   - Call detector with response and data
   - Log findings via `_append_anti_sycophancy_log`
   - Inject self_prompt if detected

4. **Task 4**: Verify integration
   - Run full test suite
   - Check Stop.py doesn't break
   - Verify env var toggle works

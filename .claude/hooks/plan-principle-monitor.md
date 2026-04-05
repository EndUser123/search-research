# Principle-Based Behavior Monitoring System

**Status**: DRAFT - Phase 4 (PLAN)
**Created**: 2026-03-07
**Phase**: /code workflow

## Overview

Implement a principle-based behavior monitoring system for Claude Code that observes model behavior against defined behavioral principles. The system tracks violations per session, logs events to JSONL for analysis, and provides soft, one-time suggestions per session when thresholds are exceeded. Never blocks or interferes with normal operation.

**Evolved from**: Perplexity discussion about lazy closure patterns → refined to principle-based approach after user feedback about avoiding "therapy for broken people" framing.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│ MEMORY.md                                                    │
│ ├── Principles: context_reuse, grounded_changes, etc.       │
│ └── Defines expected behavior (non-blocking)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Stop Hook: principle_monitor.py                              │
│ ├── Reads last_assistant_message from Stop payload           │
│ ├── Detects principle violations (heuristic patterns)       │
│ ├── Increments per-session counters                          │
│ ├── Logs events to JSONL                                     │
│ └── Emits one-time suggestion when threshold >= 5            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ State & Logs                                                  │
│ ├── .claude/state/behavior-counters.json (per-session)      │
│ └── .claude/logs/principle-events.jsonl (event log)         │
└─────────────────────────────────────────────────────────────┘
```

### Hook Integration

**Registration**: `P:\.claude\settings.json` Stop hooks array (position: LAST)
```json
{
  "hooks": {
    "Stop": [
      ...existing hooks...,
      {
        "type": "command",
        "command": "python P:/.claude/hooks/principle_monitor.py",
        "timeout": 2
      }
    ]
  }
}
```

**In-Process Option**: Add to `Stop.py` `IN_PROCESS_GATES` list for better performance (optional)

## Data Flow

```
1. Stop Event Triggers
   ↓
2. principle_monitor.py Reads Payload
   ├── session_id
   └── last_assistant_message
   ↓
3. Pattern Detection (4 event types)
   ├── context_grounding_violation
   ├── change_without_evidence
   ├── redundant_broad_question
   └── opaque_uncertainty
   ↓
4. Update State
   ├── Load behavior-counters.json
   ├── Increment counters for detected events
   └── Save behavior-counters.json
   ↓
5. Log Event (JSONL)
   └── Append to principle-events.jsonl
   ↓
6. Check Thresholds
   ├── If count >= 5 AND not already suggested
   └── Emit {"note": "suggestion text"}
   ↓
7. Never Block
   └── Always allow response (exit 0, allow=true)
```

## Error Handling

**Failure Modes**:
1. **JSON parse error** → Return `{}`, allow (fail-safe)
2. **Missing fields** → Return `{}`, allow (fail-safe)
3. **State file I/O error** → Log to stderr, continue without state
4. **JSONL write error** → Log to stderr, continue without logging

**No Blocking Conditions**: This hook NEVER blocks responses, only observes and suggests.

## Test Strategy

### Unit Tests (TDD)

**Test Files**: `P:\.claude\hooks\tests\test_principle_monitor.py`

#### Test Coverage

**Pattern Detection Tests**:
1. `test_context_grounding_violation_detected()`
   - Input: "Can you remind me what the project root is?"
   - Expected: Detects `context_grounding_violation`

2. `test_change_without_evidence_detected()`
   - Input: "You're right. Let me fix that." (no evidence cited)
   - Expected: Detects `change_without_evidence`

3. `test_redundant_broad_question_detected()`
   - Input: "What should we do next?" (broad, context available)
   - Expected: Detects `redundant_broad_question`

4. `test_opaque_uncertainty_detected()`
   - Input: "That looks correct." (unclear if verified)
   - Expected: Detects `opaque_uncertainty`

5. `test_evidence_citation_prevents_violation()`
   - Input: "You're right. The log shows line 42 has the error."
   - Expected: No violation (evidence cited)

**State Management Tests**:
6. `test_state_file_created_on_first_detection()`
   - Initial state: No state file
   - Expected: Creates state file with counter=1

7. `test_counters_increment_across_calls()`
   - Multiple detections in same session
   - Expected: Counters increment correctly

8. `test_suggestion_shown_flag_prevents_repeat()`
   - After suggestion emitted
   - Expected: No further suggestions that session

**Threshold Tests**:
9. `test_suggestion_emitted_at_threshold()`
   - 5 violations of same type
   - Expected: Suggestion emitted

10. `test_no_suggestion_below_threshold()`
    - 4 violations of same type
    - Expected: No suggestion

**Integration Tests**:
11. `test_stop_hook_integration()`
    - Full Stop payload simulation
    - Expected: Hook processes correctly, returns allow

**Pattern Validation** (per /code requirements):
12. `test_agreement_patterns_positive_cases()` - 3+ examples
13. `test_agreement_patterns_negative_cases()` - 3+ examples
14. `test_agreement_patterns_edge_cases()` - empty, whitespace, malformed

## Standards Compliance

### Python Standards

**Reference**: `/code-python` skill

**Requirements**:
- **Type Hints**: All functions use proper type annotations
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Explicit exception handling with specific exception types
- **Imports**: Grouped (stdlib, third-party, local), sorted alphabetically
- **Code Style**: ruff compliance, mypy type checking

**Toolchain**:
- `ruff check` - linting
- `mypy` - type checking
- `pytest` - testing

### Universal Principles

**Reference**: `/code-standards` skill

**Requirements**:
- **DRY**: Detection patterns defined once, reused
- **Separation of Concerns**: State management, detection, logging separated
- **YAGNI**: Conservative threshold (5), no complex features
- **Testing**: TDD RED → GREEN → REFACTOR cycle

## Ramifications

### Impact on Existing Code

**Modified Files**:
1. `P:\.claude\settings.json` - Add hook registration (Stop array)
2. `P:\.claude\hooks\Stop.py` (optional) - Add to `IN_PROCESS_GATES` if in-process execution desired

**New Files**:
1. `P:\.claude\hooks\principle_monitor.py` - Main hook implementation
2. `P:\.claude\hooks\tests\test_principle_monitor.py` - Test suite
3. `P:\.claude\state\behavior-counters.json` - Runtime state file (auto-created)
4. `P:\.claude\logs\principle-events.jsonl` - Event log (auto-created)
5. `C:\Users\brsth\.claude\projects\P--\memory\MEMORY.md` - Add principles section

**Backwards Compatibility**: ✅ No breaking changes. Hook is additive only.

### Migration Path

**None Required**: New system, standalone from existing hooks.

### Performance

**Overhead**:
- Pattern matching: O(n) where n = message length (typically < 10KB)
- State file I/O: One read/write per Stop event
- JSONL append: One append per detection
- Timeout: 2 seconds (conservative)

**Estimated Latency**: <50ms per Stop event (well within timeout)

## Pre-Mortem Analysis (Step 4.5)

### Potential Failure Modes

**1. Pattern False Positives**
- **Failure Mode**: Hook flags legitimate responses as violations
- **Impact**: User annoyance, ignored suggestions
- **Prevention**: Conservative threshold (5), evidence citation exemptions, soft wording
- **Detection**: Monitor JSONL logs for false positive patterns
- **Observability**: `unevidenced_agreement` vs `actually_evidenced_but_we_missed` ratio

**2. State File Corruption**
- **Failure Mode**: JSON parse error in state file
- **Impact**: Lost counters, repeated suggestions
- **Prevention**: Exception handling, fallback to empty state, atomic writes
- **Detection**: Log state file errors to stderr
- **Observability**: Error counter in logs

**3. JSONL Write Failures**
- **Failure Mode**: Permission denied, disk full
- **Impact**: No event logging, but hook continues
- **Prevention**: Try/except around JSONL writes, log errors to stderr
- **Detection**: Check stderr for JSONL error messages
- **Observability**: Log file existence check

**4. Session ID Collision**
- **Failure Mode**: Multiple sessions with same ID
- **Impact**: Cross-session state pollution
- **Prevention**: Use full session_id from Stop payload (UUID)
- **Detection**: Monitor state file for duplicate session_ids
- **Observability**: Session count vs. expected count

**5. Suggestion Spam**
- **Failure Mode**: Suggestion shown repeatedly in same session
- **Impact**: User frustration, ignores system
- **Prevention**: `suggestion_shown` flag per principle per session
- **Detection**: Check JSONL for multiple suggestions per session
- **Observability**: Suggestion count per session

### Observability Plan

**Metrics to Track**:
1. Violation rate per principle (events per session)
2. False positive rate (user feedback)
3. Suggestion frequency (suggestions per session)
4. Hook execution time (latency)

**Alerting**:
- **Error spike**: >10% hook failures → Investigate state file/JSONL issues
- **Suggestion spam**: >1 suggestion per session per principle → Fix `suggestion_shown` logic
- **Latency spike**: >500ms average → Optimize patterns

**Diagnosis Tools**:
```bash
# Analyze violations by principle
cat .claude/logs/principle-events.jsonl | jq -r '.principle' | sort | uniq -c

# Check suggestion frequency
cat .claude/logs/principle-events.jsonl | jq -r 'select(.note != null) | .session_id' | uniq -c

# Monitor hook errors
grep "principle_monitor" .claude/logs/*.log | tail -20
```

## Execution Path Verification (Step 4.5)

### Scope Check

**Linear Flow?** No - This is a stateful hook with conditional branches:
- Pattern detection (multiple branches)
- State file I/O (can fail)
- Threshold checking (conditional)
- Suggestion emission (once per session)

**Verification Required**: ✅ Yes, non-linear flow

### TRACE Verification

**Main Flow** (principle_monitor.py main()):

```
1. Read stdin → Parse JSON
   ├─ Exception? → Return {}, exit 0 (fail-safe)
   ↓
2. Validate event_type == "Stop"
   └─ Not Stop? → Return {}, exit 0
   ↓
3. Extract session_id, last_assistant_message
   └─ Missing? → Return {}, exit 0
   ↓
4. Detect patterns (4 detection functions)
   └─ Each: check regex, return bool
   ↓
5. Load state file
   ├─ Exception? → Log stderr, use empty state
   ↓
6. Update counters
   └─ Increment for each detected event
   ↓
7. Save state file
   ├─ Exception? → Log stderr, continue without state
   ↓
8. Log events to JSONL
   ├─ Exception? → Log stderr, continue without logging
   ↓
9. Check thresholds
   ├─ count >= 5 AND not suggestion_shown?
   │   └─ Yes: Set suggestion_shown, save state, emit note
   └─ No: Emit {}
   ↓
10. Return JSON, exit 0
```

### Reachability Check

**All Branches Reachable?** ✅ Yes
- Exception handlers: All return/exit cleanly
- Threshold check: Both branches (emit note vs. emit {})
- State file: Exists → use, doesn't exist → create

**Multi-Turn Lifecycle**:
- Turn 1: Detection → state[count=1]
- Turn 2-4: Detections → state[count=2,3,4]
- Turn 5: Detection → count=5 → emit suggestion → state[suggestion_shown=true]
- Turn 6+: Detection → count=6 but suggestion_shown=true → no note

**State Persistence**: ✅ State file persists between Stop events within session

**Marker Conflicts**: None - No special markers used, only standard JSON

### Cleanup

**Cleanup Required**: None - State file auto-created, suggestions one-time

**Session End**: State file remains (historical record), but suggestion_shown prevents repeat suggestions

## Pattern Validation (Step 4.6)

**Detector Module**: `principle_monitor.py` contains 4 event detection functions

### Pattern 1: Agreement Detection

**Purpose**: Detect agreement phrases without evidence citation

**Patterns**:
```python
AGREE_PATTERNS = frozenset([
    "you're right",
    "you are right",
    "good point",
    "i agree",
    "exactly",
    "fair point"
])
```

**Positive Examples** (should trigger):
1. "You're right about that." (no evidence)
2. "I agree, let's do it." (no evidence)
3. "Exactly. Let me fix it." (no evidence)

**Negative Examples** (should NOT trigger):
1. "You're right. The log shows line 42 has the error." (has evidence)
2. "I agree with your assessment in file config.yaml." (has evidence)
3. "Good point. Line 10 confirms this." (has evidence)

**Edge Cases**:
- Empty string → No match
- Whitespace only → No match
- Case sensitivity → Case-insensitive matching
- Partial match → "You're right about X, as shown in Y" → Has evidence, should not trigger

**Pattern Soundness**:
- ✅ Specific enough: Targets agreement phrases
- ✅ Not too broad: Has evidence exemption
- ⚠️ False positives possible: "You're right" may be used legitimately (but evidence check catches most)
- ⚠️ False negatives possible: Other agreement phrases not in list ("That's correct", "True")

### Pattern 2: Context Grounding

**Purpose**: Detect questions about info present in recent context

**Pattern**: Question mark + length threshold
```python
def is_lazy_question_candidate(text: str) -> bool:
    t = text.strip()
    return len(t) > 30 and t.endswith("?")
```

**Positive Examples** (should trigger):
1. "Can you remind me what the project root is?" (>30 chars, ends with ?)
2. "What was the API key again?" (>30 chars, ends with ?)
3. "Where did we put the config file?" (>30 chars, ends with ?)

**Negative Examples** (should NOT trigger):
1. "How do I fix this?" (<=30 chars)
2. "What's next?" (<=30 chars)
3. "Should we proceed?" (<=30 chars)

**Edge Cases**:
- No question mark → No match
- Exactly 30 chars → No match (strict >)
- Whitespace variations → Stripped before check

**Pattern Soundness**:
- ✅ Simple, fast heuristic
- ⚠️ High false positive rate: Any question >30 chars flagged
- ⚠️ High false negative rate: Short questions missed
- Rationale: Conservative "check everything" approach, threshold filters

### Pattern 3: Evidence Citation

**Purpose**: Check if message cites concrete evidence

**Markers**:
```python
EVIDENCE_MARKERS = [
    "see the", "in file", "line ", "log shows",
    "output shows", "test shows", "as shown in",
    "according to", "based on", "the error above"
]
```

**Positive Examples** (should return True):
1. "See the error above for details."
2. "In file config.yaml, line 42..."
3. "The log shows the issue."
4. "As shown in the diff..."

**Negative Examples** (should return False):
1. "I think this is correct."
2. "Let's fix that now."
3. "That looks wrong."

**Edge Cases**:
- Case sensitivity → Case-insensitive
- Partial matches → "see" alone doesn't trigger, needs "see the" or "in file"
- Overlapping markers → Multiple markers OK

**Pattern Soundness**:
- ✅ Covers common evidence citation patterns
- ⚠️ May miss unconventional citations: "Test X confirms" without marker
- ⚠️ May false positive: "I see the problem" (not actual citation)

## Implementation Plan (Tasks)

### Task 1: Create Principle Monitor Hook
**File**: `P:\.claude\hooks\principle_monitor.py`
- Implement detection functions for 4 event types
- Implement state management (load/save)
- Implement JSONL logging
- Implement threshold checking
- Implement suggestion emission
- Add comprehensive error handling
- Add type hints and docstrings

### Task 2: Add Principles to MEMORY.md
**File**: `C:\Users\brsth\.claude\projects\P--\memory\MEMORY.md`
- Add principles section: context_reuse, grounded_changes, minimal_redundancy, transparent_uncertainty
- Use neutral, principle-focused language
- Reference system-level expectations

### Task 3: Write Tests (TDD)
**File**: `P:\.claude\hooks\tests\test_principle_monitor.py`
- RED phase: Write failing tests for all detection functions
- GREEN phase: Implement minimal code to pass tests
- REFACTOR phase: Clean up code while tests pass
- Add pattern validation tests (positive/negative/edge cases)

### Task 4: Register Hook in settings.json
**File**: `P:\.claude\settings.json`
- Add hook to Stop hooks array (position: LAST)
- Set timeout=2 seconds
- Verify registration with test

### Task 5: Documentation and Cleanup
- Add DEBUG_HOOK_README-style documentation for usage/removal
- Remove debug hooks (debug_payload_hook.py)
- Verify all tests pass
- Run ruff and mypy checks

### Task 6: Integration Verification
- Manual testing with sample responses
- Verify JSONL logging works
- Verify state file persistence
- Verify suggestion threshold behavior
- Verify no blocking occurs

## Success Criteria

- [ ] All 4 event types detected correctly
- [ ] State file persists counters across Stop events
- [ ] JSONL logging captures all events
- [ ] Suggestion emitted at threshold=5, once per principle per session
- [ ] No blocking (all responses allowed)
- [ ] Tests pass (unit + integration)
- [ ] ruff linting passes
- [ ] mypy type checking passes
- [ ] Manual TRACE verification passes
- [ ] Debug hooks removed

## Next Steps

**Proceed to Phase 5 (TDD)**: Implement tasks following RED → GREEN → REFACTOR cycle.

**Execution Model**: Standard implementation (all tasks local to hooks directory, no cross-module changes beyond settings.json and MEMORY.md).

**Task List**: Will create task list after plan approval.

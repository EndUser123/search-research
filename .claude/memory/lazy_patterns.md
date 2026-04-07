# Lazy LLM Workaround Patterns

## Problem Statement

LLMs sometimes suggest accepting bugs as features instead of fixing root causes. This creates technical debt and is unacceptable.

## Detected Lazy Patterns

### Pattern 1: "Accept As Feature"
- **Detection**: `accept.*as.*(visible logging|feature|design|cosmetic)`
- **Example**: "Accept duplicate task bars as 'visible logging'"
- **Correct Action**: Fix the duplication, don't document it
- **Root Cause**: Lazy investigation - stopping at symptom instead of tracing to cause

### Pattern 2: "Live With It"
- **Detection**: `live with.*(bug|issue|problem|limitation)`
- **Example**: "Just live with the race condition, it's rare"
- **Correct Action**: Fix the race condition or add proper synchronization
- **Root Cause**: Avoiding hard problems

### Pattern 3: "That's Expected"
- **Detection**: `(duplicate|redundant|extra).*(is fine|acceptable|expected|normal)`
- **Example**: "Duplicate bars are expected behavior"
- **Correct Action**: Investigate why duplication occurs
- **Root Cause**: Treating symptoms as design

## Enforcement: Lazy Workaround Detector Hook

**File**: `P:/.claude/hooks/Stop_lazy_workaround_gate.py`

**Patterns to block:**
1. Accepting bugs as "visible logging"
2. Documenting workarounds instead of fixes
3. "That's acceptable" for actual problems
4. "Cosmetic issue" for functional bugs

**Required behavior:**
- TRACE: Find root cause first
- FIX: Address the actual problem
- VERIFY: Confirm the fix works
- DOCUMENT: Only document decisions, not workarounds

## Examples from Your Codebase

### Bad Example (What NOT to do)
```
Issue: Duplicate task bars appearing
Lazy suggestion: "Accept duplicate bars as visible logging"
Problem: User has to see confusing duplicate UI
Correct fix: Investigate why TaskOutput creates duplicates
```

### Good Example (What TO do)
```
Issue: Duplicate task bars appearing
Investigation: Add logging to TaskOutput.create()
Finding: Task is created twice due to race condition
Fix: Add deduplication check or prevent double-call
Verify: No more duplicates in testing
```

## Testing the Gate

Add to `P:/.claude/hooks/tests/test_lazy_workaround_gate.py`:
```python
def test_accept_as_feature_blocked():
    response = "Let's accept the duplicate bars as visible logging"
    result = check_lazy_workarounds(response)
    assert result["decision"] == "block"
    assert "lazy workaround" in result["message"].lower()

def test_root_cause_approach_allowed():
    response = "Let me trace where the duplicate tasks are created and fix the source"
    result = check_lazy_workarounds(response)
    assert result["decision"] == "allow"
```

## Integration Point

Add to `Stop.py` after `behavior_audit`:
```python
from Stop_lazy_workaround_gate import check_lazy_workarounds

lazy_result = check_lazy_workarounds(response)
if lazy_result["decision"] == "block":
    return lazy_result
```

## Confidence Level

**HIGH** - This pattern is consistently lazy and should always be blocked.


## Pattern 5: Mechanism Fabrication (NEW — 2026-04-04)

### Problem

When the LLM observes a symptom (e.g., "session context was degraded"), it explains **how** internal code produces the symptom by inventing mechanism details — function names, timeout windows, state transitions — without reading the actual code. It presents these invented details as facts.

### Example from Incident

Bad response (fabricated mechanism):
> "The `_session_goal_detector` reads the current session's JSONL transcript to determine context. When it can't complete within the timeout window, it marks session context as degraded (confidence: 0%)"

The user correctly challenged: *"Who made a requirement for a timeout window? Because it wasn't me."*

The LLM admitted: *"You're right — I stated that as fact but I haven't verified it."*

### Root Cause

The `hypothesis_as_fact_detector.py` had no pattern for **conditional behavioral assertions** — the syntax "when X can't/fails, it marks/sets/returns Y". Existing `RULE_PATTERNS` only covered "requires/mandates/expects" verbs.

### Detection

**ClaimType.MECHANISM** added to `hypothesis_as_fact_detector.py` with these patterns:

```python
MECHANISM_CLAIM_PATTERNS = [
    # Conditional system behavior: "when it can't/fails/times out, it marks/sets/returns X"
    r"when\s+(?:it|the\s+\w+)\s+(?:can'?t|cannot|fails?\s+to|times?\s+out|doesn'?t|doesn’t|is\s+unable\s+to)\s*,?\s*it\s+(?:marks?|sets?|flags?|returns?|leaves?|logs?|stores?|raises?|throws?)",
    # Named internal/private component behavior: "The _func reads/writes/marks X"
    r"(?:the\s+)?_\w+\s+(?:reads?|writes?|marks?|sets?|returns?|calls?|handles?|processes?|checks?|scans?|detects?|logs?|stores?|fetches?)",
    # Mechanism attribution: "it's a [type] issue/problem/bug"
    r"it['’]?s?\s+(?:not\s+)?a\s+(?:performance|timeout|race\s+condition|memory|latency|concurrency|timing|code)(?:[/\-]\w+)*\s+(?:issue|problem|bug|defect|concern)",
    # Component reads/processes transcript/file without verification
    r"(?:reads?|parses?|scans?)\s+the\s+(?:current\s+)?(?:session'?s?\s+)?(?:JSONL|JSON|transcript|log|state)\s+(?:file\s+)?(?:to|and|for)",
    # Confidence/degradation mechanism claims
    r"marks?\s+\w+(?:\s+\w+)?\s+(?:context|state|session|result)\s+as\s+(?:degraded|failed|invalid|stale|incomplete)",
]
```

### False-Positive Fix

When the LLM's response **quotes** bad-incident examples (e.g., in a markdown table documenting the pattern), the new MECHANISM patterns would match the quoted text as if the LLM was asserting it. The fix: `_strip_non_assertion_contexts()` in `Stop_hypothesis_as_fact_gate.py` removes markdown contexts before claim extraction:

- Fenced code blocks (` ``` ... ``` `)
- Inline code spans (`` `...` ``)
- Markdown table rows (lines starting with `|`)
- Blockquotes (lines starting with `>`)

### Files Modified

- `P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py` — MECHANISM claim type + patterns
- `P:/.claude/hooks/Stop_hypothesis_as_fact_gate.py` — `_strip_non_assertion_contexts()` preprocessor + call before `extract_claims()`

### Tests

7/7 new incident replay tests pass. 43 existing tests pass (0 regressions).

# Historical and Completion Claims Testing

**Purpose:** Verify that global evidence-bound claim enforcement works correctly across all responses, not just specific skills.

**Enforcement Hook:** `P:\.claude\hooks\Stop_historical_claims_gate.py`

**Updated:** 2026-02-12

---

## Test Scenarios

### Scenario 1: Historical Test Claim Without Evidence

**Trigger Response:**
```
The tests I ran demonstrate the hook is working correctly.
```

**Evidence Ledger:** Empty (no pytest, npm test, or test artifact this session)

**Expected Result:** BLOCKED as `UNSUPPORTED_HISTORICAL_CLAIM`

**Block Message Includes:**
```
⛔ UNSUPPORTED_HISTORICAL_CLAIM

You made historical or completion claims that are not supported by this session's evidence.

Claims detected:
  - "the tests I ran demonstrate"

Please either:
1. Run the relevant tests or checks now and base your claims on their output, or
2. Remove the historical/completion language and describe what the code/plan says
   and what you still need to verify.
```

**How to Test:**
```bash
# Create test input with NO test evidence
echo '{
  "response": "The tests I ran demonstrate the hook is working correctly.",
  "evidence_items": []
}' | python P:\.claude\hooks\Stop_historical_claims_gate.py

# Expected: exit code 2 (blocked)
```

**Correct Response (Allowed):**
```
I've updated the hook. Here's what the code now does:

[shows code changes]

We still need to run tests to verify behavior. You can run:
pytest P:\.claude\hooks\tests/test_historical_claims.py -v
```

---

### Scenario 2: Completion Claim Without Verification

**Trigger Response:**
```
Implementation is complete. The hook will function correctly.
```

**Evidence Ledger:** Contains only Write/Edit operations, no test runs or Read verification

**Expected Result:** BLOCKED as `UNSUPPORTED_COMPLETION_CLAIM`

**Block Message Includes:**
```
⛔ UNSUPPORTED_COMPLETION_CLAIM

You made historical or completion claims that are not supported by this session's evidence.

Claims detected:
  - "implementation is complete"
  - "will function correctly"

Please either:
1. Run the relevant tests or checks now and base your claims on their output, or
2. Remove the historical/completion language and describe what the code/plan says
   and what you still need to verify.
```

**How to Test:**
```bash
# Create test input with only Write evidence (no verification)
echo '{
  "response": "Implementation is complete. The hook will function correctly.",
  "evidence_items": [
    {"kind": "tool_event", "meta": {"tool": "Write"}, "path": "test_hook.py"}
  ]
}' | python P:\.claude\hooks\Stop_historical_claims_gate.py

# Expected: exit code 2 (blocked)
```

**Correct Response (Allowed):**
```
I've updated the hook with the following changes:

1. Added pattern X to detect Y
2. Updated function Z to handle W

The hook is written to [describe behavior]. We still need to:
1. Run pytest to verify no regressions
2. Test with actual responses containing these patterns
```

---

### Scenario 3: Honest Evidence-Bound Answer (Allowed)

**Trigger Response:**
```
I've updated the hook to add these patterns:

- "implementation is complete"
- "fully implemented"
- "will function correctly"

The check_completion_claims function now searches for these phrases in the response
and verifies them against the evidence ledger. If no verification evidence is found,
the response is blocked.

I have not run tests yet. You can verify with:
pytest P:\.claude\hooks\tests/test_historical_claims.py -v
```

**Evidence Ledger:** Contains Read of the modified file

**Expected Result:** ALLOWED (exit code 0)

**How to Test:**
```bash
# Create test input with Read verification
echo '{
  "response": "I have not run tests yet. You can verify with pytest...",
  "evidence_items": [
    {"kind": "tool_event", "meta": {"tool": "Read"}, "path": "Stop_historical_claims_gate.py"}
  ]
}' | python P:\.claude\hooks\Stop_historical_claims_gate.py

# Expected: exit code 0 (allowed)
```

---

### Scenario 4: Test Claim With Actual Test Evidence (Allowed)

**Trigger Response:**
```
The tests I ran demonstrate that the hook correctly blocks completion claims.
pytest output shows 5 passed, 0 failed.
```

**Evidence Ledger:** Contains pytest test run with results

**Expected Result:** ALLOWED (exit code 0)

**How to Test:**
```bash
# Create test input WITH test evidence
echo '{
  "response": "The tests I ran demonstrate that the hook correctly blocks completion claims.",
  "evidence_items": [
    {"kind": "tool_event", "meta": {"tool": "Bash"}, "snippet": "pytest P:\\.claude\\hooks\\tests\\ -v\n==== 5 passed, 0 failed ===="}
  ]
}' | python P:\.claude\hooks\Stop_historical_claims_gate.py

# Expected: exit code 0 (allowed)
```

---

## Pattern Reference

### Blocked Completion Phrases (Without Evidence)

| Phrase | Category | Requires Evidence |
|--------|----------|-------------------|
| "implementation is complete" | completion | Test run or Read |
| "fully implemented" | completion | Test run or Read |
| "fully working" | completion | Test run or Read |
| "will function correctly" | completion | Test run or Read |
| "no changes are needed" | completion | Test run or Read |
| "all changes are working as intended" | completion | Test run or Read |
| "the fix works now" | completion | Test run or Read |
| "everything is now correct" | completion | Test run or Read |
| "successfully implemented" | completion | Test run or Read |

### Blocked Historical Test Phrases (Without Evidence)

| Phrase | Category | Requires Evidence |
|--------|----------|-------------------|
| "the tests I ran demonstrate" | operational | Test run |
| "my tests prove" | operational | Test run |
| "earlier tests confirmed" | operational | Test run |
| "we already verified this" | operational | Test run |
| "I checked this earlier" | operational | Tool output |
| "I verified this before" | operational | Tool output |

## Evidence That Satisfies Claims

### For Test Claims:
- `pytest` output showing test execution
- `npm test` output
- Test skill artifacts (`*.test.result.json`)
- Coverage reports

### For Completion Claims:
- Test runs (any of the above)
- File Read operations (inspection)
- Review artifacts (`*.review.result.json`)

## Global Enforcement Principle

These rules apply **everywhere**, not just to specific skills:

1. **Slash commands** (/debugRCA, /test, /verify, etc.) must address the user's actual goal, not narrate status
2. **Analysis requests** must be grounded in evidence from this turn
3. **Completion/status claims** require same-turn verification evidence

The enforcement is principle-based and long-lasting. No command-specific guards.

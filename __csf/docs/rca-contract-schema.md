# RCA Contract Schema v2

## Required Fields (9 total)

All RCA responses MUST include these 9 sections. Missing any field will cause the StopHook_rca_contract to block.

### 1. Symptom

What is the problem? Describe the error, crash, or unexpected behavior.

**Format:**
```markdown
## Symptom

User's claim: [summary of what user reported]
Observed behavior: [what actually happened]
```

### 2. Evidence

What data supports this investigation? Include:
- Current-turn tool citations (Read, Grep, Bash outputs)
- File paths and line numbers
- Tier labels: `[current-state]`, `[transcript-time]`, `[inference]`

**Format:**
```markdown
## Evidence

| Source | Finding |
|--------|---------|
| file.py:123 | Read showed X |
| Grep output | Found pattern Y |
```

**CRITICAL:** At least one evidence item must be from the current turn (actual tool usage this session).

### 3. Executed Path

Step-by-step execution trace showing:
- Function calls with line numbers
- Variable state at each step
- Resource acquisition/release
- All three scenarios: happy path, error path, edge case

**Format:**
```markdown
## Executed Path

1. Function A() at line X calls Function B()
2. Function B() at line Y returns value Z
3. [... continue tracing ...]
```

### 4. Alternative Hypothesis

What other causes were considered? List >=2 hypotheses (unless single root cause confirmed).

**Format:**
```markdown
## Alternative Hypothesis

H1: [first hypothesis]
H2: [second hypothesis]
```

### 5. Falsifier

What evidence disproves each alternative hypothesis?

**Format:**
```markdown
## Falsifier

The executed path shows [...]. This disproves H1 because [...].
```

### 6. Ruled Out

**REQUIRED:** Document what alternatives were considered and why each was rejected.

This is a SEPARATE field from Falsifier. Falsifier explains WHY an alternative is wrong. Ruled Out documents the COMPLETE set of alternatives that were considered.

**Format:**
```markdown
## Ruled Out

- Hypothesis A: [reason rejected]
- Hypothesis B: [reason rejected]
- N/A (if only one hypothesis found)
```

**Most common error:** Omitting this section entirely. The hook will BLOCK without it.

### 7. Root Cause

What is the actual cause? Must be reachable from Executed Path (identifiers in Root Cause must appear in Executed Path).

**Format:**
```markdown
## Root Cause

[clear statement of actual cause]
```

### 8. Fix

What changes will resolve the issue? Include file paths and code.

**Format:**
```markdown
## Fix

[specific changes to make]
```

### 9. Verification

How will we confirm the fix works? Include specific commands or tests.

**Format:**
```markdown
## Verification

1. [verification step 1]
2. [verification step 2]
```

---

## Common Pitfalls

1. **Missing "Ruled Out" section** - Most common block reason
2. **Root Cause not reachable from Executed Path** - Identifiers don't match
3. **No current-turn evidence** - All evidence is from transcript, not this turn
4. **Alternative Hypothesis missing** - Only presented one hypothesis

---

## Complete Example

See `P:\__csf/docs/rca-examples.md` for validated RCA examples.

**Hook location:** `P:\.claude\hooks\StopHook_rca_contract.py`
**Schema definition:** Lines 93-103 define REQUIRED_FIELDS

# Diagnostic Question Pattern - Edge Cases & Rationale

## Problem

The original broad pattern `r"\b(?:why\s+(?:is|does|did|...))"` caught ALL "why" questions, including meta-questions about the conversation itself.

## False Positives (Original Pattern)

| Question | Type | Why It's Wrong |
|----------|------|----------------|
| "why did you say that" | Meta-question | About my output, not system state |
| "why did you recommend X" | Meta-question | About my recommendation |
| "why are you triggering this" | Meta-question | About hook behavior |
| "why is this happening" | Ambiguous | Could be conversation meta |
| "why did this happen" | Ambiguous | Could be conversation meta |

## Solution: Positive Pattern

```python
r"\bwhy\s+(?:is|did|does)\s+(?:the|this|that|my|your)\s+(?:file|code|hook|test|function|class|system|config|daemon|service|api)"
```

**Why it works:**
- Targets specific system-state nouns (file, code, hook, test, function, etc.)
- Requires determiner (the, this, that, my, your) before the noun
- "your code/function/test" = system state ✓
- "you say/said/claim" = no matching noun ✗

## Test Results

Test corpus: 13 real user questions

| Pattern | TP | FP | FN | Errors |
|---------|----|----|----|--------|
| Original (broad) | 8 | 5 | 0 | 5/13 |
| Positive (v2) | 8 | 0 | 0 | **0/13** ✓ |

## Edge Cases Handled

### "why is your code broken" ✓
- Contains "your" but IS legitimate diagnostic
- Pattern accepts "your" + system-state noun
- Distinguished from "your" + verb ("you said")

### Ambiguous cases ("why is this happening") ✗
- Not matched by positive pattern
- User can clarify if meant as diagnostic
- Better to under-detect than spam with false warnings

## Two-Tier Alternative (Rejected)

```python
# Broad pattern + negative exclusion
broad = r"\bwhy\s+(?:is|did|does|are)"
exclude = r"\b(?:you|your|said|say|claim|output|response|trigger)"
```

**Rejected because:**
- 3/13 errors (vs 0/13 for positive)
- "why is your code broken" incorrectly excluded
- More complex, harder to maintain

## When to Update This Pattern

If a new false positive/negative is found:
1. Add to test corpus in `test_diagnostic_patterns.py`
2. Re-run test to verify regression
3. Adjust pattern if trend emerges
4. Document rationale here

## Test File

```bash
python P:\.claude\hooks\test_diagnostic_patterns.py
```

Last updated: 2026-02-03 (positive pattern v2, 0/13 errors)

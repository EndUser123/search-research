# Success Theater Detection

**Purpose**: Detect fake success metrics that mask problems.

**Problem**: "Tests pass, system broken." Success theater creates false confidence through impressive-looking metrics that don't reflect reality.

## Success Theater Patterns to Check

### 📊 Fake Test Coverage
- "95% test coverage, but tests don't validate actual behavior"
- "All tests pass, but edge cases untested"
- "Unit tests pass, integration fails"
- **Detection**: Are tests checking behavior or just syntax? Do tests validate failure paths?

### ✅ Empty Validation Gates
- "Code review passed" (but reviewer only checked formatting)
- "Linting passed" (but critical logic bugs ignored)
- "Architecture approved" (but no actual implementation reviewed)
- **Detection**: What did validation actually check? Did it verify behavior or just appearance?

### 📈 Vanity Metrics
- "Lines of code written" (not "lines that work")
- "Number of tests added" (not "tests that catch bugs")
- "Documentation pages created" (not "docs that are accurate")
- **Detection**: Does metric correlate with actual success, or just activity?

### 🎭 "Looks Good" Anti-Patterns
- "Tests pass but system crashes in production" (happy path only)
- "Code is clean but doesn't solve the problem" (refactored into irrelevance)
- "Documentation exists but is outdated" (docs written once, never updated)
- **Detection**: Does the artifact work in practice, or just in theory?

## Integration

Run this step AFTER Step 3.5 (Reference Class Forecasting) and BEFORE Step 3.8 (Operational Verification). This ensures success theater detection happens before final risk rating.

## Real-World Example

First two pre-mortems approved a fix based on "architecture looks good" without testing. Third pre-mortem had actual test results that revealed the implementation gap.

## Example: Concrete Success Theater Patterns to Check

```
❌ BAD (Too vague):
   - "Tests might be fake" (What does this look like?)
   - "Validation might be empty" (How do you detect this?)
   - "Metrics might be vanity" (Which metrics? Why?)

✅ GOOD (Specific anti-patterns):
   - "95% test coverage, but 0 tests for error paths or edge cases"
   - "All 20 tests pass, but test only happy path (no failure scenarios)"
   - "Code review approved, but reviewer only checked formatting (lint-level review)"
   - "Architecture approved, but no implementation code reviewed (design-only review)"
   - "Documentation exists but was written 6 months ago (may be outdated)"
   - "1,000 lines of code written, but feature doesn't actually work yet"
```

**Note**: Adapt these patterns to your project context. The specificity matters more than the exact examples.

## Validation: Does Step 3.6 Actually Work?

### Test Case

Apply Step 3.6 to the skill pattern gate fix approval (the real-world example above).

```
Scenario: First two pre-mortems approved skill pattern gate fix
because "architecture looks good." Later testing revealed it
introduced a registry validation gap.

Apply Step 3.6 questions:

Q: Would "Empty Validation Gates" detection have caught this?
A: YES ✅
   - Detection question: "What did validation actually check?"
   - Answer: "Architecture approved" (design-only review)
   - Flag: "No implementation code reviewed" → SUCCESS THEATER DETECTED

Q: Would "Looks Good Anti-Patterns" detection have caught this?
A: YES ✅
   - Detection question: "Does it work in practice, or just in theory?"
   - Answer: "Architecture looks good in theory" (no testing)
   - Flag: "Tests pass but system crashes in production" → SUCCESS THEATER DETECTED

Conclusion: Step 3.6 WOULD have caught the success theater pattern.
Enhancement is validated against known case.
```

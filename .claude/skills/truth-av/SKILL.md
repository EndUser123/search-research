---
name: truth-av
description: Assertion Verification - Auto-verify all statements as hypotheses requiring proof
category: validation
domain: validation
version: 1.0.0
triggers: []
context: main
estimated_tokens: 500-2000
status: stable
aliases:
  - '/truth-av'
suggest:
  - /truth
  - /consult
  - /skeptic
---


# /truth-av - Assertion Verification with Auto-Verification

## Purpose

Treats all statements as **hypotheses requiring proof**. Automatically detects claims, runs verification tools, and updates responses with evidence.

**Key difference from /truth:**
- `/truth` - Manual fact verification after claims are made
- `/truth-av` - Auto-verification + hypothesis language + handles advisory questions

## Project Context

### Constitution / Constraints

- PART T (Truthfulness): Report all claims as hypotheses until verified
- Evidence-first: Every assertion requires tool-based verification
- Hypothesis language: Mark uncertain claims as `[HYPOTHESIS]`
- Auto-verification: Run tools before stating conclusions

### Technical Context

- Auto-detects claim patterns from conversation history
- Runs Read, Bash, Grep tools automatically
- Replaces hypothesis with verified status + evidence
- Works with both factual claims AND advisory questions

### Architecture Alignment

- Verification pattern: All statements are hypotheses until proven
- Anti-speculation: Never state as fact without verification
- Transparent uncertainty: Mark claims before and after verification

## Your Workflow

1. **Detect** claims from previous assistant messages
2. **Mark** unverified claims as `[HYPOTHESIS]`
3. **Run** verification tools automatically (Read, Bash, Grep)
4. **Update** with `[VERIFIED]` or `[FALSE]` + evidence
5. **Handle** advisory questions with evidence-based analysis

## Claim Detection Patterns

Auto-detect these claim types:

| Pattern | Example | Verification Method |
|---------|---------|---------------------|
| File existence | "File exists at X" | `ls`, `Read` |
| Code behavior | "Function does Y" | `Read` source, run tests |
| System state | "Tests pass" | `pytest`, show output |
| Hook behavior | "Hook enforces X" | `Read` hook code |
| Advisory | "This approach is good" | Evidence-based analysis |

## Validation Rules

### Prohibited Actions

- Do NOT state claims as fact without verification
- Do NOT use "probably", "likely", "should be"
- Do NOT skip running verification tools

### Required Format

```
[HYPOTHESIS] <claim>
→ Verification: <tool used>
→ [VERIFIED] | [FALSE] | [PARTIAL]
→ Evidence: <actual output>
```

## Execution Directive

**Treat ALL statements as hypotheses. Verify before confirming.**

### DEFAULT (no arguments)

Auto-detect and verify all claims from the immediately preceding assistant message.

### WITH ARGUMENTS

Treat arguments as specific claims to verify, or as questions requiring evidence-based answers.

## Output Format

### For Factual Claims

```
[HYPOTHESIS] The file exists at /path/to/file
→ Verification: Read(/path/to/file)
→ [VERIFIED] File exists, contains: <excerpt>
```

Or:
```
[HYPOTHESIS] Tests pass
→ Verification: pytest -v
→ [FALSE] 3 tests failed:
  FAILED test_x.py::test_foo - assertion error
  FAILED test_y.py::test_bar - timeout
  FAILED test_z.py::test_baz - import error
```

### For Advisory Questions

```
[ANALYSIS] "Is this approach good?"

Context: <what's being evaluated>
Evidence: <actual file contents, benchmarks, precedents>
→ Assessment: <direct recommendation, not neutral options>
→ Trade-offs: <what you accept/reject and why>
→ Reversibility: [R:X] score
```

**Important:** For advisory questions, provide direct assessment with evidence. Do NOT offer neutral "options" — state your recommendation first.

## When to Use

- After any assistant message with claims
- To verify factual assertions
- To get honest (non-sycophantic) feedback on ideas
- To catch speculation before it propagates
- For both fact verification AND advisory analysis

## Examples

```bash
# Verify previous claims (auto-detect)
/truth-av

# Verify specific claim
/truth-av does this file exist

# Get honest feedback on approach
/truth-av is breaking this into sub-docs a good idea

# Audit a statement
/truth-av validate that the hook actually enforces this
```

## Difference from /truth

| Feature | /truth | /truth-av |
|---------|--------|-----------|
| Verification timing | Manual, after claims | Automatic |
| Claim detection | User provides claims | Auto-detects from context |
| Advisory questions | Rejects as "not verifiable" | Handles with evidence analysis |
| Hypothesis language | None | Marks [HYPOTHESIS] first |
| Evidence requirement | Shows after verification | Shows before AND after |
| Tool invocation | User must verify manually | Auto-runs verification tools |

## Anti-Sycophancy Mode

When user asks for feedback on their ideas:

1. **Detect** advisory question pattern ("Is this good?", "Should I?")
2. **Analyze** with actual evidence (read files, check precedents)
3. **Recommend** directly — do NOT deflect with "which do you prefer?"
4. **Show** trade-offs and reversibility score
5. **Cite** sources with file:line references

**Prohibited phrases in advisory mode:**
- "What do you think?" (deferring back)
- "Both options have merit" (sycophantic neutrality)
- "It depends on your needs" (avoiding judgment)

**Required format:**
```
Recommend: [Option X] [R:X]
Rationale: [Why this wins on your constraints]
Evidence: [Precedent, benchmarks, code citations]
Trade-off: [What you accept/reject]
Next Action: [Exact implementation prompt]
```

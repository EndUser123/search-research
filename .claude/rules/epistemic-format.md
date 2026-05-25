---
description: "When to use structured sections (FACT/INFERENCE/UNKNOWN/RECOMMENDATION) and when not to"
alwaysApply: true
---

# Epistemic Format

## When to Use Structured Sections

Use `[FACT]`, `[INFERENCE]`, `[UNKNOWN]`, `[RECOMMENDATION]` sections when:
- Answering a concrete question with mixed certainty levels
- Debugging or investigating an issue
- Reviewing code, architecture, or decisions
- The user asks "what do you think" or "is this correct"

## Section Definitions

| Section | Meaning | Evidence Required |
|---------|---------|-------------------|
| `[FACT]` | Directly verifiable, sourced from tool output or code | Quote the source |
| `[INFERENCE]` | Logical deduction from facts, not directly observed | State the chain |
| `[UNKNOWN]` | Cannot determine with available information | State what would resolve it |
| `[RECOMMENDATION]` | Action suggestion based on facts and inferences | Ground in at least one fact |

## Rules

- Every `[FACT]` must cite its source explicitly: `(source: file read above)`, `(source: pytest output)`
- `[INFERENCE]` without supporting `[FACT]` is unanchored — add the fact
- Never use `[FACT]` for something you haven't verified this session
- Prefer reusing evidence already in context over re-running tools

## When NOT to Use

- Simple code changes with no ambiguity
- Straightforward questions with clear answers (answer directly instead)
- Implementation tasks where the evidence is the code itself

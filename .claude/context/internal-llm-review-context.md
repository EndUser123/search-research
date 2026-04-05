# Internal LLM Review Context

**Purpose**: This document explains what helps Claude (internal LLM) provide better architectural reviews and solutions.

---

## What Makes Reviews Better

### 1. Concrete Artifacts Over Descriptions

**❌ Less Helpful**:
```
"The cognitive frameworks system needs improvement."
```

**✅ More Helpful**:
```
"Review this file: P:/.claude/hooks/cognitive_enhancers_config.json
Current issue: Enhancer selection doesn't consider token budget.
Constraint: Must stay stateless, no external deps.
Goal: Select optimal enhancers within token limits."
```

**Why**: I can read actual files and identify specific gaps. Descriptions force me to guess.

---

### 2. Explicit Requirements and Constraints

**❌ Less Helpful**:
```
"Make the 5W1H framework work well."
```

**✅ More Helpful**:
```
"Requirements for 5W1H enhancer:
- Must not trigger in fast mode
- Must coexist with Socratic for diagnostic prompts
- Must add <80 tokens to injection
- Must be disableable via config
- Must have 30-day observability trial

Constraints:
- Hooks are stateless
- No new dependencies
- >80% test coverage required"
```

**Why**: Explicit acceptance criteria let me verify completeness instead of guessing what "works well" means.

---

### 3. Existing Context and Background

**❌ Less Helpful**:
```
"Why isn't this working?"
```

**✅ More Helpful**:
```
"I'm debugging hook execution. Here's what I've tried:
1. Checked UserPromptSubmit hook - fires correctly
2. Verified config file - JSON valid
3. Added observability logging - shows no selection

Suspect issue: Intent detection in cognitive_enhancers.py line 142
File: P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py
Line 142: _detect_intent() not returning expected boolean"
```

**Why**: Investigation context shows me what you've already ruled out. I can focus on the remaining uncertainty.

---

### 4. Specific Failure Modes to Evaluate

**❌ Less Helpful**:
```
"Review this architecture for issues."
```

**✅ More Helpful**:
```
"Review this 5W1H proposal focusing on:
1. Will it trigger too often on simple prompts? (false positive risk)
2. Does the Socratic suppression rule make sense?
3. Is 30-day observability sufficient for validation?
4. What happens if token budget is exceeded?
5. Can we rollback easily if it fails?"
```

**Why**: Specific concerns let me target analysis instead of generic "looks good."

---

### 5. Design Documents or Proposals

**❌ Less Helpful**:
```
"Should I add a planner agent?"
```

**✅ More Helpful**:
```
"Here's my design proposal for a Planner enhancer:
[Attach design doc or detailed proposal]

I want you to:
1. Evaluate against system_landscape.md constraints
2. Check for duplicates with existing workflow skills
3. Identify gaps in the proposal
4. Assess integration complexity

Context: I know /plan-workflow exists. This is different because:
[Explain specific distinction]"
```

**Why**: Design documents let me evaluate complete thoughts instead of brainstorming from scratch.

---

## Optimal Query Patterns for Internal LLM

### Pattern 1: Code Review with Specific Focus
```
"Review this file: [path]
Focus on: [performance | security | maintainability | bugs]
Context: [what this code does, why it matters"
```

### Pattern 2: Architecture Evaluation
```
"Evaluate this proposal: [attach proposal or describe]

Checklist:
- [ ] Aligns with system_landscape.md?
- [ ] Violates any "Common Pitfalls"?
- [ ] Specifies exact files to change?
- [ ] Includes concrete test cases?
- [ ] Defines rollback plan?

Concerns to evaluate:
- [Specific concern 1]
- [Specific concern 2]"
```

### Pattern 3: Root Cause Analysis
```
"Symptom: [what's failing]
Investigation so far:
- [X] Ruled out cause A
- [X] Ruled out cause B
- [ ] Suspect cause C

Files involved:
- [path1]
- [path2]

Help me: [diagnose | verify hypothesis | design fix]"
```

### Pattern 4: Implementation Guidance
```
"I want to implement: [specific feature]

Current state:
- Existing code: [path]
- Tests: [test path]
- Coverage: [X]%

Target state:
- Acceptance criteria: [what "done" looks like]
- Constraints: [platform, dependencies, etc.]

Request:
1. Confirm my understanding is correct
2. Identify gaps in my plan
3. Suggest implementation order
4. Highlight risks I missed"
```

---

## What I Can Do Well

### ✅ Strengths
- **Read actual files**: I can analyze code, configs, tests
- **Identify gaps**: Missing error handling, edge cases, validation
- **Compare alternatives**: Trade-offs between approaches A and B
- **Verify completeness**: Check all required sections are present
- **Trace execution**: Follow code paths to find bugs
- **Apply standards**: Check against TDD, >80% coverage, solo-dev patterns

### ⚠️ Limitations
- **No runtime execution**: I can't run code to see actual behavior
- **Limited context window**: Large codebases require focused queries
- **No historical awareness**: I don't remember previous conversations unless referenced
- **Can't access external systems**: No web search, no external APIs

---

## Anti-Patterns: What to Avoid

### ❌ Vague Questions
```
"Is this good?"
"How do I fix this?"
"What should I do?"
```
**Problem**: No context, no constraints, no acceptance criteria.

**Better**: "Evaluate [specific file/design] against [specific standard/concern]."

### ❌ Fishing Expeditions
```
"Just tell me everything wrong with this system."
```
**Problem**: Too broad, produces laundry list, no prioritization.

**Better**: "Focus on [specific concern: performance/security/maintainability] in [specific module]."

### ❌ Premature Optimization
```
"How do I make this 10x faster?"
```
**Problem**: No baseline measurement, may not be bottleneck.

**Better**: "Profile shows [X] is slow. Help optimize [specific code path]."

### ❌ Context-Free Questions
```
"Should I use Redis or Memcached?"
```
**Problem**: Ignores platform constraints (we use SQLite/file-based only).

**Better**: "Within [constraint: file-based, no cloud], how should I [solve specific problem]?"

---

## Working With Me Effectively

### 1. Be Specific About What You Need
```
Instead of: "Review this code"
Try: "Review this code for [security issues | race conditions | missing error handling]"
```

### 2. Provide Context Upfront
```
Instead of: "Why is this broken?"
Try: "This code worked until [change]. Now [symptom]. I've checked [A, B, C]."
```

### 3. Reference Existing Systems
```
Instead of: "How do I add memory?"
Try: "system_landscape.md says we have CKS/CHS. How do I integrate [feature] with them?"
```

### 4. Use Structure for Complex Requests
```
For architecture reviews:
1. Attach design doc/proposal
2. List specific concerns
3. Reference constraints (system_landscape.md)
4. Ask for structured output (findings table, risk summary)
```

### 5. Iterate on Gaps, Not Starting Over
```
Instead of: "Give me a better solution"
Try: "Your proposal missed [gap]. Revise only that section."
```

---

## Quick Reference: Optimal Query Structure

```
[CONTEXT]
- What I'm working on: [file/feature/system]
- What I've tried: [investigation done so far]
- Constraints: [platform limits, existing systems]

[REQUEST]
- Specific question: [what I need help with]
- Focus area: [performance | security | architecture | debugging]
- Output format: [findings table | step-by-step | code diff]

[CONCERNS] (optional)
- Risk 1: [specific worry]
- Risk 2: [specific worry]
- Gap to address: [what's missing]
```

---

## Summary: What Helps Me Help You

1. **Show me the actual code** (not just descriptions)
2. **Tell me what you've tried** (not just "it's broken")
3. **Be specific about concerns** (not "review everything")
4. **Reference constraints** (system_landscape.md, platform, etc.)
5. **Provide complete proposals** (not "should I add X?")
6. **Ask structured questions** (not vague "is this good?")

**The golden rule**: More context → better answers. Less context → generic advice.

---

**When in doubt**, attach the relevant file and say:
```
"Here's the file: [path]
Context: [what it does, what's wrong]
Focus: [specific concern]
What do you think?"
```

This gives me enough to provide targeted, useful feedback.

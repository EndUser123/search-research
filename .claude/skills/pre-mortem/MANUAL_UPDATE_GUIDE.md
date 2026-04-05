# Manual Update Instructions for /pre-mortem SKILL.md

## Goal
Replace three detailed sections with concise references to reduce SKILL.md from 1019 → ~819 lines (200 line reduction).

## Changes Needed

### 1. Replace Step 2.5 (lines 114-153)

**Find this text:**
```markdown
### Step 2.5: Second-Order Effects (Important + ENHANCED + MANDATORY)
**Purpose**: Most failure analysis stops at first-order effects. Real disasters come from cascading consequences.

**Technique**: Ask "And then what?" 3-5 times for each high-likelihood cause.

**Required (v3.6)**:
For each risk with score ≥ 6 (High or Medium-High):
- ✅ **Trace cascade to minimum 3 steps**
- ✅ **Classify cascade depth** (Shallow/Medium/Deep)
- ✅ **Boost priority for Deep cascades** (even if likelihood is Medium)

**IF cascade depth < 3**: INCOMPLETE ANALYSIS - Continue tracing until minimum depth reached.

**Example**:
```
First order: "Skip writing tests"
→ Second order: "Bugs slip into production"
→ Third order: "Fixing bugs takes 10x longer than writing tests"
→ Fourth order: "Project delays accumulate, we rush even more"
→ Fifth order: "Vicious cycle of tech debt and shortcuts"

CASCADE DEPTH: DEEP (5 steps)
PRIORITY BOOST: Even if likelihood is Medium, Deep cascade → High priority
```

**Pattern to look for**:
- Compensating behaviors that create new problems
- Time borrowing (trading quality for speed → paying back with interest)
- Hidden feedback loops (fixes that make the root cause worse)

**Cascade Depth Classification**:
- **Shallow** (1-2 steps): Localized failure, easy to recover
- **Medium** (3-4 steps): Affects multiple subsystems
- **Deep** (5+ steps): System-wide collapse, prioritize prevention

**Output**: Add cascade depth classification to each high-risk item:
```
[RISK:6] [Failure cause] - CASCADE: DEEP (5 steps)
```
```

**Replace with:**
```markdown
### Step 2.5: Second-Order Effects (Important + ENHANCED)
**Purpose**: Most failure analysis stops at first-order effects. Real disasters come from cascading consequences.

**See**: `references/second-order-effects.md` for detailed methodology, examples, and cascade depth classification.

**Quick Reference**:
- **Technique**: Ask "And then what?" 3-5 times for each high-likelihood cause
- **Required**: For risks with score ≥ 6, trace cascade to minimum 3 steps, classify depth (Shallow/Medium/Deep), boost priority for Deep cascades
- **IF cascade depth < 3**: INCOMPLETE ANALYSIS - Continue tracing until minimum depth reached
- **Output format**: `[RISK:6] [Failure cause] - CASCADE: DEEP (5 steps)`
```

---

### 2. Replace Step 2.6 (lines 154-218)

**Find** (entire section from "### Step 2.6:" to "**Note**: Adapt these patterns..." on line 218)

**Replace with:**
```markdown
### Step 2.6: AI/LLM-Specific Failure Modes (NEW - v3.7)
**Purpose**: Detect failure modes unique to AI/LLM-augmented workflows.

**Problem**: Traditional failure analysis assumes human developers. AI/LLM workflows introduce new failure patterns.

**See**: `references/ai-llm-failures.md` for complete catalog of AI/LLM-specific risks including:
- LLM Hallucination & Confabulation
- Context Overflow & Attention Drift
- Tool Misuse & Misunderstanding
- Subagent Coordination Failures
- Skill Substitution Attacks
- Generated Code Quality Issues

**Integration**: Run this step AFTER Step 2.5 (Second-Order Effects) and BEFORE Step 3 (Categorize). Add AI/LLM-specific risks to the brainstorm list.

**Real-world example**: Skill pattern gate bug was exactly this type of failure - AI misinterpreted registry validation gap as "skill doesn't exist" because it used general knowledge instead of checking actual registry state.
```

---

### 3. Replace Step 3.6 (lines 254-333)

**Find** (entire section from "### Step 3.6:" to "Enhancement is validated against known case."`` on line 332)

**Replace with:**
```markdown
### Step 3.6: Success Theater Detection (NEW - v3.7)
**Purpose**: Detect fake success metrics that mask problems.

**Problem**: "Tests pass, system broken." Success theater creates false confidence through impressive-looking metrics that don't reflect reality.

**See**: `references/success-theater.md` for detailed patterns including:
- Fake Test Coverage
- Empty Validation Gates
- Vanity Metrics
- "Looks Good" Anti-Patterns

**Integration**: Run this step AFTER Step 3.5 (Reference Class Forecasting) and BEFORE Step 3.8 (Operational Verification).

**Real-world example**: First two pre-mortems approved a fix based on "architecture looks good" without testing. Third pre-mortem had actual test results that revealed the implementation gap.
```

## Result

**Lines saved**: ~200 lines
**New total**: ~819 lines (20% closer to 500-line target)
**Progressive disclosure**: Detailed content now in reusable reference files
**Maintained functionality**: All content preserved, better organized

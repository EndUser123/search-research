# AI/LLM-Specific Failure Modes

**Purpose**: Detect failure modes unique to AI/LLM-augmented workflows.

## Failure Mode Taxonomy

When analyzing failures, consider these four domains:

| Failure Domain | Question | Example |
|----------------|----------|---------|
| **DATA** | What state could be missing or wrong? | Capture buffer overflow, missing breadcrumb trail |
| **SEMANTIC** | Is the captured message the task itself or a reference to it? | Clarification "you told me earlier" captured as goal instead of actual task |
| **LOGIC** | Could state transitions be wrong? | Wrong step kind inferred from tool name |
| **SECURITY** | Could we leak or corrupt data? | Credential exposure in handoff transcript |

**Why SEMANTIC matters**: Pre-mortems traditionally ask "what if state is wrong/missing?" but miss "what if the message semantic TYPE is wrong?" — the message is captured correctly but classified incorrectly. The clarification message problem (ADR-20260327) was this exact failure mode.

**Problem**: Traditional failure analysis assumes human developers. AI/LLM workflows introduce new failure patterns: hallucination, context overflow, tool misuse, subagent coordination failures, skill substitution attacks.

## AI/LLM-Specific Risks to Consider

### 🤖 LLM Hallucination & Confabulation
- "AI confidently invents non-existent APIs or libraries"
- "AI generates code that looks correct but uses hallucinated functions"
- "AI provides plausible-sounding but technically impossible solutions"
- **Warning sign**: Generated code doesn't import from known libraries, uses undocumented parameters

### 📚 Context Overflow & Attention Drift
- "LLM loses track of critical constraints from early in conversation"
- "Context window exceeds, earlier requirements dropped"
- "AI forgets previous decisions, contradicts itself"
- **Warning sign**: AI asks "what was the requirement again?" after long context

### 🛠️ Tool Misuse & Misunderstanding
- "AI calls wrong tool for the task (Read vs. Grep vs. Glob)"
- "AI uses Edit when Write is needed, creating file conflicts"
- "AI misinterprets tool results, draws wrong conclusions"
- **Warning sign**: Same tool called repeatedly with similar failed arguments

### 🤝 Subagent Coordination Failures
- "Multiple agents work at cross-purposes, undo each other's work"
- "Agent A assumes Agent B completed task, but B failed silently"
- "Race condition: Two agents edit same file simultaneously"
- **Warning sign**: Git conflicts, repeated edits to same section

### 🔄 Skill Substitution Attacks
- "AI provides analysis instead of executing skill workflow (bypasses skill validation)"
- "AI generates code directly instead of using /code skill (skips TDD, verification)"
- "AI answers from training data instead of checking current documentation (stale knowledge)"
- **Warning sign**: Skill mentioned but not invoked via Skill tool

### 📊 Generated Code Quality Issues
- "AI generates tests that always pass (false positive coverage)"
- "AI writes code that passes tests but violates architectural constraints"
- "AI generates documentation that doesn't match actual implementation"
- **Warning sign**: Tests pass but integration fails, docs contradict code

## Integration

Run this step AFTER Step 2.5 (Second-Order Effects) and BEFORE Step 3 (Categorize). Add AI/LLM-specific risks to the brainstorm list.

## Real-World Example

Skill pattern gate bug was exactly this type of failure - AI misinterpreted registry validation gap as "skill doesn't exist" because it used general knowledge instead of checking actual registry state.

## Example: Concrete AI/LLM Risks to Check

```
❌ BAD (Too generic):
   - "AI might hallucinate" (What does this look like?)
   - "Context might get lost" (When does this happen?)
   - "Tools might be misused" (Which tools? How?)

✅ GOOD (Specific patterns):
   - "AI invents non-existent library functions: `import pandas.nlp()` (hallucinated)"
   - "AI forgets requirement from 50 turns ago and contradicts earlier decision"
   - "AI uses Edit tool when Write needed, creates merge conflicts with parallel edits"
   - "AI generates analysis instead of calling /code skill (bypasses TDD verification)"
   - "AI answers from 2023 training data, ignores current documentation"
   - "AI generates tests that pass but miss edge cases (false confidence)"
```

**Note**: Adapt these patterns to your project context. The specificity matters more than the exact examples.

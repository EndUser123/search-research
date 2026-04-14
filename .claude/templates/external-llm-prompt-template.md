# External LLM Prompt Template

**Purpose**: Use this template when querying external LLMs (Perplexity, Claude, GLM, etc.) for architectural advice. This ensures they have complete context and follow the MVA structure.

---

## Pre-Prompt (Always Include)

```
You are providing architectural advice for a sophisticated AI development system.

MANDATORY READING:
1. Read the system context: P:/.claude/context/system_landscape.md
2. Use the MVA template: P:/.claude/templates/architecture_proposal.md
3. Read the behavior contract: P:/.claude/templates/llm_behavior_contract.md

CRITICAL RULES:
- Assume everything in system_landscape.md is TRUE and COMPLETE
- DO NOT suggest anything that violates "Common Pitfalls" in system_landscape.md
- Your response MUST follow the MVA template structure exactly
- If ANY MVA section is incomplete, mark it "NEEDS CLARIFICATION" and STOP
- Do NOT suggest implementation until all MVA sections are complete
- Apply the behavior contract self-check before finalizing your answer

VIOLATION PROTOCOL:
If you ignore system_landscape.md or propose "add memory/planner mode/cloud":
1. I will reject your response immediately
2. I will ask you to re-read system_landscape.md
3. I will not proceed until you acknowledge existing systems

COMPLETENESS CHECKLIST:
Before submitting your proposal, verify:
- References CKS/CHS correctly (not "add memory")
- Specifies exact files to change
- Includes concrete test cases
- Defines rollback procedure
- Quantifies thresholds
- Addresses token budget impact
```

---

## Example Query Format

```
[Copy pre-prompt above]

MY QUESTION:
[Your architectural question here]

CONTEXT:
- Attach relevant code snippets or review bundles if needed
- Specify which part of the system this affects (hooks, skills, CKS, CHS)

REQUIRED OUTPUT FORMAT:
Use the MVA template (architecture_proposal.md) section by section.
Mark incomplete sections as "NEEDS CLARIFICATION: [what's missing]"
```

---

## Example: Good Query

```
[Pre-prompt]

MY QUESTION:
I want to add a 5W1H cognitive enhancer for context gathering.
How should this integrate with existing Socratic Decomposition?
What files need to change?
How do we validate this works?

CONTEXT:
- Current cognitive frameworks: Cynefin, Socratic, Devil's Advocate, etc.
- Conflict arbiter enforces max 3 enhancers
- Hooks are stateless, CKS/CHS provide memory
- Target: diagnostic and design prompts that lack context

REQUIRED OUTPUT FORMAT:
Complete MVA template with all sections filled.
```

---

## Example: Bad Query (AVOID THIS)

```
❌ "How do I make my LLM smarter?"
❌ "What cognitive frameworks should I add?"
❌ "Should I implement a planner agent?"
❌ "How do I add memory to my system?"

WHY THESE ARE BAD:
- Too vague, no specific problem
- Ignore existing systems (we already have planning/workflow/memory)
- Violate "Common Pitfalls" in system_landscape.md
- Result: Generic advice that doesn't fit your architecture
```

---

## Post-Response Validation

After receiving external LLM response, check:

### ✅ Accept If:
- All MVA sections are complete or marked "NEEDS CLARIFICATION"
- References CKS/CHS correctly
- Specifies exact files
- Includes test cases
- Defines rollback
- Quantifies thresholds

### ⚠️ Reject If:
- Suggests "add memory" or "case recall"
- Suggests "planner reasoning mode"
- Suggests cloud services/Docker
- Violates anti-bloat philosophy
- Leaves sections vague ("add proper testing" without concrete cases)
- Doesn't specify files or rollback plan

### 🔄 Revision Request Template:
```
Thank you for the initial response. However, the following sections need clarification:

NEEDS CLARIFICATION:
- [Section X]: [What's missing or vague]
- [Section Y]: [What's missing or vague]

Please revise ONLY the incomplete sections above. Keep other sections as-is.
```

---

## Quick Reference: Common External LLM Pitfalls

### ❌ "Add Case-Based Memory"
**Your Response**: "We have CKS (492 entries) and CHS. Integrate with those instead."

### ❌ "Add Planner Reasoning Mode"
**Your Response**: "We have /plan-workflow, /code, /arch skills. Enhance those instead."

### ❌ "Use Redis/MongoDB for Caching"
**Your Response**: "Platform constraint: Windows 11, file-based persistence only (SQLite, JSONL)."

### ❌ "Implement Multi-Agent Coordination"
**Your Response**: "Solo development context. No team/multi-user features needed."

### ❌ "Add Comprehensive Testing Framework"
**Your Response**: "We use pytest with >80% coverage requirement. Extend existing tests."

---

## Integration with Your Workflow

### Before Querying External LLM:
1. Read system_landscape.md yourself to remind context
2. Open architecture_proposal.md to see what sections you need
3. Craft specific question with "My question affects [X] system"

### After Receiving Response:
1. Check completeness against MVA template
2. Validate against system_landscape.md constraints
3. If gaps found, request revision for specific sections only
4. Once complete, you can proceed to implementation with confidence

### During Implementation:
1. Follow the MVA spec exactly (files, tests, rollback)
2. Update system_landscape.md if architecture changes significantly
3. Add lessons learned to CKS after implementation

---

## Advanced Usage: Batched Architecture

For complex multi-component changes, request batched specs:

```
[Pre-prompt]

MY QUESTION:
I need Cognitive Control v2 with three changes:
1. 5W1H enhancer for context gathering
2. Calibrated Confidence → Devil's Advocate coupling
3. Enhanced observability with user outcome tracking

REQUIRED OUTPUT FORMAT:
Provide ONE MVA template that covers ALL THREE changes together.
Show how they integrate as a cohesive system, not three separate proposals.
```

This prevents "piece-by-piece" solutions and forces holistic thinking.

---

**Remember**: The goal is FEWER iterations with MORE complete specs, not faster back-and-forth on incomplete ideas. Enforce the template, reject vague responses, and iterate only on specific gaps.

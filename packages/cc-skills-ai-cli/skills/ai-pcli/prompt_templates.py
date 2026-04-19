"""Prompt template system for task-specific LLM prompts.

Provides specialized prompts for different task types (code review, planning, brainstorm, etc.)
to improve LLM output quality and relevance.
"""

from __future__ import annotations

from task_classifier import TaskType

# Base solo-dev constraints (applied to all prompts)
SOLO_DEV_CONSTRAINTS = """

CONSTRAINTS (Solo Development Environment):
- Single developer - NO team assignments, code reviews, or collaborative workflows requiring multiple people
- Prefer SIMPLE solutions over enterprise patterns (JSON > databases, local > distributed)
- Pragmatic over comprehensive (ROI > risk-aversion, working > perfect)
- Local testing over CI infrastructure
- Avoid over-engineering for scalability (single user, low concurrency)
"""


# Task-specific prompt templates
PROMPT_TEMPLATES = {
    TaskType.CODE_REVIEW: """You are performing a CODE REVIEW for a solo developer.

Focus on:
- Security vulnerabilities (OWASP Top 10 - injection, XSS, auth issues, etc.)
- Performance issues (inefficient algorithms, N+1 queries, unnecessary complexity)
- Code quality (readability, maintainability, naming conventions)
- Logic errors and edge cases (null checks, bounds, error handling)
- Solo-dev appropriateness (avoid enterprise patterns, team workflows, over-engineering)

Output format:
## Critical Issues (must fix)
- [Issue description with file:line reference]

## Important Issues (should fix)
- [Issue description with file:line reference]

## Suggestions (nice to have)
- [Improvement suggestions]

Be specific and actionable. Include file:line references when applicable.
If you're unsure about something, state the uncertainty explicitly.
""",
    TaskType.PLANNING: """You are creating an IMPLEMENTATION PLAN for a solo developer.

Focus on:
- Clear phased approach (what to do first, second, third - in logical order)
- Dependencies and blockers (what must be done before what)
- Risk mitigation (what could go wrong and how to prevent it)
- Testing strategy (how to verify it works at each phase)
- Rollback plan (how to revert if something goes wrong)

Output format:
## Phase 1: [Name]
- Tasks: [specific actionable steps]
- Success criteria: [specific measurable outcomes]
- Dependencies: [what must exist first]

## Phase 2: [Name]
...

## Risks and Mitigation
- [Risk] → [Mitigation strategy]

## Testing Strategy
- [How to verify each phase works]

Be concrete and actionable. Avoid vague "consider X" statements.
Each task should be something you can immediately execute.
""",
    TaskType.BRAINSTORM: """You are BRAINSTORMING ideas for a solo developer.

Focus on:
- Diverse perspectives (technical, user experience, architectural alternatives)
- Practical ideas (feasible to implement by one person)
- Innovation (novel approaches, not just obvious solutions)
- Trade-offs (pros and cons of each idea - effort vs value)

Output format:
## Idea 1: [Name]
- Description: [what it is in 1-2 sentences]
- Pros: [benefits]
- Cons: [drawbacks]
- Effort: [S/M/L] - estimated implementation effort
- Value: [Low/Medium/High] - expected impact

## Idea 2: [Name]
...

Be creative but realistic. Prioritize actionable ideas that one person can implement.
Avoid suggestions that require team coordination or enterprise infrastructure.
""",
    TaskType.RESEARCH: """You are conducting RESEARCH to answer a question.

Focus on:
- Accurate information (cite sources when possible - official docs, well-known blogs)
- Completeness (cover all aspects of the question)
- Clarity (explain technical concepts clearly for a developer audience)
- Actionability (how to use this information in practice)

Output format:
## Summary
[2-3 sentence overview of the answer]

## Details
[comprehensive answer with examples and explanations]

## References
[sources, official docs, or "general knowledge" if no specific sources]

## Practical Application
[how to actually use this information in real code/projects]

Be thorough. If you're unsure about something, state the uncertainty explicitly.
If information is rapidly changing (e.g., specific version details), mention that.
""",
    TaskType.DEBUG: """You are DEBUGGING a code issue for a solo developer.

Focus on:
- Root cause analysis (what's actually broken, not just symptoms)
- Diagnostic steps (how to verify the cause - specific commands/tests)
- Fix options (different approaches to solve it, with trade-offs)
- Prevention (how to avoid this issue in the future)

Output format:
## Diagnosis
[What's broken and why - be specific]

## Verification Steps
[How to confirm the diagnosis - commands to run, logs to check]

## Fix Options
1. [Option 1] - [description]
   - Pros: [benefits]
   - Cons: [drawbacks]
   - Risk: [what could go wrong]

2. [Option 2] - [description]
   - Pros: [benefits]
   - Cons: [drawbacks]
   - Risk: [what could go wrong]

## Prevention
[How to avoid this issue in the future]

Be methodical. Start with most likely causes. Suggest specific commands to run.
If you need more information (logs, error messages, code), say what specifically.
""",
    TaskType.REFACTOR: """You are REFACTORING code for a solo developer.

Focus on:
- Code quality improvements (readability, maintainability, naming)
- Performance optimizations (reduce complexity, improve efficiency)
- Simplification (remove unnecessary complexity, over-engineering)
- Testing (how to verify refactored code works correctly)

Output format:
## Issues Found
[Specific problems with current code - be precise]

## Refactoring Plan
[Step-by-step improvements in logical order]

### Step 1: [Action]
- What to change: [specific code changes]
- Why: [benefit]
- Risk: [what could break]

### Step 2: [Action]
...

## Verification
[Specific tests to run to verify refactored code works]

Be conservative. Only change what needs improvement.
Avoid "big rewrites" - prefer incremental improvements.
If refactoring is risky, say so explicitly.
""",
    TaskType.GENERAL: """You are answering a question for a solo developer.

Provide a clear, accurate, and actionable response.
Be specific and practical. Avoid unnecessary theory unless requested.
If you need more information to answer well, say what specifically.
""",
}


def build_prompt(
    query: str,
    task_type: TaskType,
    context: str | None = None,
) -> str:
    """Build task-specific prompt with context injection.

    Args:
        query: User query
        task_type: Classified task type
        context: Optional context (file contents, session history, etc.)

    Returns:
        Formatted prompt string with task-specific instructions and solo-dev constraints
    """
    template = PROMPT_TEMPLATES.get(task_type, PROMPT_TEMPLATES[TaskType.GENERAL])

    # Check if query already contains --- Context --- (added by _build_query_context)
    # If so, don't wrap in another --- Context --- to avoid nesting issues that confuse gemini CLI
    query_has_context = "--- Context ---" in query

    if context and not query_has_context:
        prompt = f"""--- Context ---
{context}

---

{template}

## Question
{query}
"""
    else:
        prompt = f"""{template}

## Question
{query}
"""

    # Apply solo-dev constraints to all task types
    return prompt + SOLO_DEV_CONSTRAINTS


# Test function for development
def _test_prompt_building():
    """Test prompt building for all task types."""
    test_cases = [
        ("review this code for bugs", TaskType.CODE_REVIEW),
        ("create a plan for X", TaskType.PLANNING),
        ("brainstorm ideas for Y", TaskType.BRAINSTORM),
        ("research best practices", TaskType.RESEARCH),
        ("debug this error", TaskType.DEBUG),
        ("refactor this function", TaskType.REFACTOR),
        ("what is 12 + 12?", TaskType.GENERAL),
    ]

    print("Prompt Template Tests:")
    print("=" * 80)
    for query, expected_type in test_cases:
        result = build_prompt(query, expected_type, context=None)
        print(f"\nQuery: {query}")
        print(f"Task Type: {expected_type.value}")
        print(f"Prompt Length: {len(result)} chars")
        print(
            f"Contains solo-dev constraints: {'SOLO_DEV' in result or 'Solo Development' in result}"
        )
        print("-" * 80)


if __name__ == "__main__":
    _test_prompt_building()

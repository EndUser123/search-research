"""Task type classifier for LLM CLI queries.

Classifies user queries into task types (code_review, planning, brainstorm, etc.)
using keyword matching. Provides confidence scoring and matched keywords for analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """LLM task types for classification and routing.

    Each task type maps to specific prompt templates for better LLM responses.
    """

    CODE_REVIEW = "code_review"
    PLANNING = "planning"
    BRAINSTORM = "brainstorm"
    RESEARCH = "research"
    DEBUG = "debug"
    REFACTOR = "refactor"
    GENERAL = "general"


@dataclass
class ClassificationResult:
    """Result of task classification.

    Attributes:
        task_type: The classified task type
        confidence: Confidence score 0.0 to 1.0 based on keyword matches
        matched_keywords: List of keywords that triggered this classification
        reasoning: Human-readable explanation of the classification
    """

    task_type: TaskType
    confidence: float
    matched_keywords: list[str]
    reasoning: str


# Keyword patterns for each task type
# Based on /llm-route documented patterns and enhanced for comprehensive coverage
TASK_PATTERNS = {
    TaskType.CODE_REVIEW: [
        "review",
        "analyze",
        "audit",
        "gaps",
        "opportunities",
        "findings",
        "inspect",
        "examine",
        "assess",
        "evaluate code",
        "code review",
        "what's wrong with",
        "improve this code",
    ],
    TaskType.PLANNING: [
        "plan",
        "strategy",
        "roadmap",
        "architecture",
        "design",
        "approach",
        "outline",
        "structure",
        "organize",
        "implementation plan",
        "steps to",
        "how should i implement",
    ],
    TaskType.BRAINSTORM: [
        "brainstorm",
        "ideas",
        "suggest",
        "creative",
        "innovative",
        "explore",
        "what if",
        "alternatives",
        "options",
        "come up with",
        "think of",
        "different ways to",
    ],
    TaskType.RESEARCH: [
        "research",
        "investigate",
        "find information",
        "lookup",
        "search",
        "explain",
        "what is",
        "how does",
        "compare",
        "tell me about",
        "describe",
        "documentation",
    ],
    TaskType.DEBUG: [
        "debug",
        "fix",
        "error",
        "bug",
        "issue",
        "problem",
        "not working",
        "broken",
        "failure",
        "crash",
        "why is this failing",
        "what's wrong",
        "troubleshoot",
    ],
    TaskType.REFACTOR: [
        "refactor",
        "improve",
        "optimize",
        "clean up",
        "simplify",
        "restructure",
        "reorganize",
        "make better",
        "make this more readable",
        "reduce complexity",
    ],
}


def classify_task(query: str) -> ClassificationResult:
    """Classify query into task type using keyword matching.

    Uses deterministic keyword matching (not ML-based) to ensure
    consistent, explainable classifications. Logs all matched keywords
    for performance analysis.

    Args:
        query: User query string

    Returns:
        ClassificationResult with task type, confidence, and reasoning
    """
    query_lower = query.lower()

    # Score each task type by keyword matches
    scores = {}
    matched = {}
    for task_type, keywords in TASK_PATTERNS.items():
        matches = [kw for kw in keywords if kw in query_lower]
        if matches:
            scores[task_type] = len(matches)
            matched[task_type] = matches

    if not scores:
        return ClassificationResult(
            task_type=TaskType.GENERAL,
            confidence=0.0,
            matched_keywords=[],
            reasoning="No task type keywords detected",
        )

    # Return highest-scoring task type
    best_task = max(scores.items(), key=lambda x: x[1])[0]
    match_count = scores[best_task]

    # Confidence: 0.2 per keyword match, max 1.0 at 5+ matches
    confidence = min(match_count * 0.2, 1.0)

    return ClassificationResult(
        task_type=best_task,
        confidence=confidence,
        matched_keywords=matched[best_task],
        reasoning=f"Matched {match_count} keywords for {best_task.value}: {', '.join(matched[best_task][:3])}{'...' if len(matched[best_task]) > 3 else ''}",
    )


# Test function for development
def _test_classification():
    """Test task classification with sample queries."""
    test_queries = [
        ("review this code for bugs", TaskType.CODE_REVIEW),
        ("create a plan for implementing X", TaskType.PLANNING),
        ("brainstorm ideas for feature Y", TaskType.BRAINSTORM),
        ("research best practices for Z", TaskType.RESEARCH),
        ("debug this error in module.py", TaskType.DEBUG),
        ("refactor this function for clarity", TaskType.REFACTOR),
        ("what is 12 + 12?", TaskType.GENERAL),
    ]

    print("Task Classification Tests:")
    print("-" * 60)
    for query, expected in test_queries:
        result = classify_task(query)
        status = "✓" if result.task_type == expected else "✗"
        print(f"{status} {query}")
        print(f"  → {result.task_type.value} (confidence: {result.confidence:.2f})")
        print(f"  → {result.reasoning}")
        print()


if __name__ == "__main__":
    _test_classification()

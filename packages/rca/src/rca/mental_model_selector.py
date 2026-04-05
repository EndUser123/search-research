#!/usr/bin/env python3
"""
Mental Model Selector - Tool-ify the Logic

Moves the mental model selection from pseudo-code in the prompt
to an executable Python tool. Saves LLM tokens and ensures consistent
model selection based on problem characteristics.

Author: CSF Development Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelCategory(Enum):
    """Categories of mental models"""

    MENTAL_MODEL = "Mental Model"
    REASONING_STRATEGY = "Reasoning Strategy"
    BIAS_CHECK = "Bias Awareness"


class MentalModel(Enum):
    """Available mental models for RCA"""

    SYSTEMS_THINKING = "Systems Thinking"
    FIRST_PRINCIPLES = "First Principles"
    SCIENTIFIC_METHOD = "Scientific Method"
    FIVE_WHYS = "Five Whys"
    ISHIKAWA = "Ishikawa (Fishbone)"
    INVERSION = "Inversion"
    OCCAMS_RAZOR = "Occam's Razor"
    SECOND_ORDER_THINKING = "Second-Order Thinking"
    MARGIN_OF_SAFETY = "Margin of Safety"
    OPPORTUNITY_COST = "Opportunity Cost"
    PARETO = "Pareto Principle (80/20)"
    ANTIFRAGILITY = "Antifragility"
    LEVERAGE_POINTS = "Leverage Points"
    ASYMMETRIC_UPSIDE = "Asymmetric Upside"
    NETWORK_EFFECTS = "Network Effects"
    OPTIONALITY = "Optionality"
    FLYWHEEL = "Flywheel Effect"
    SCAMPER = "SCAMPER (Innovation)"
    CHAIN_OF_THOUGHT = "Chain of Thought (CoT)"
    TREE_OF_THOUGHTS = "Tree of Thoughts (ToT)"
    SELF_CONSISTENCY = "Self-Consistency (Verbal Sampling)"
    ANALOGICAL_REASONING = "Analogical Reasoning"
    # Bias Awareness
    CONFIRMATION_BIAS = "Confirmation Bias Check"
    SURVIVORSHIP_BIAS = "Survivorship Bias Check"
    LOSS_AVERSION = "Loss Aversion Check"
    CIRCLE_OF_COMPETENCE = "Circle of Competence Check"
    # Debugging Techniques
    BINARY_SEARCH = "Binary Search Debugging"
    RUBBER_DUCK = "Rubber Duck Debugging"


MODEL_CATEGORIES = {
    MentalModel.SYSTEMS_THINKING: ModelCategory.MENTAL_MODEL,
    MentalModel.FIRST_PRINCIPLES: ModelCategory.MENTAL_MODEL,
    MentalModel.SCIENTIFIC_METHOD: ModelCategory.MENTAL_MODEL,
    MentalModel.FIVE_WHYS: ModelCategory.MENTAL_MODEL,
    MentalModel.ISHIKAWA: ModelCategory.MENTAL_MODEL,
    MentalModel.INVERSION: ModelCategory.MENTAL_MODEL,
    MentalModel.OCCAMS_RAZOR: ModelCategory.MENTAL_MODEL,
    MentalModel.SECOND_ORDER_THINKING: ModelCategory.MENTAL_MODEL,
    MentalModel.MARGIN_OF_SAFETY: ModelCategory.MENTAL_MODEL,
    MentalModel.OPPORTUNITY_COST: ModelCategory.MENTAL_MODEL,
    MentalModel.PARETO: ModelCategory.MENTAL_MODEL,
    MentalModel.ANTIFRAGILITY: ModelCategory.MENTAL_MODEL,
    MentalModel.LEVERAGE_POINTS: ModelCategory.MENTAL_MODEL,
    MentalModel.ASYMMETRIC_UPSIDE: ModelCategory.MENTAL_MODEL,
    MentalModel.NETWORK_EFFECTS: ModelCategory.MENTAL_MODEL,
    MentalModel.OPTIONALITY: ModelCategory.MENTAL_MODEL,
    MentalModel.FLYWHEEL: ModelCategory.MENTAL_MODEL,
    MentalModel.SCAMPER: ModelCategory.MENTAL_MODEL,
    MentalModel.CHAIN_OF_THOUGHT: ModelCategory.REASONING_STRATEGY,
    MentalModel.TREE_OF_THOUGHTS: ModelCategory.REASONING_STRATEGY,
    MentalModel.SELF_CONSISTENCY: ModelCategory.REASONING_STRATEGY,
    MentalModel.ANALOGICAL_REASONING: ModelCategory.REASONING_STRATEGY,
    MentalModel.CONFIRMATION_BIAS: ModelCategory.BIAS_CHECK,
    MentalModel.SURVIVORSHIP_BIAS: ModelCategory.BIAS_CHECK,
    MentalModel.LOSS_AVERSION: ModelCategory.BIAS_CHECK,
    MentalModel.CIRCLE_OF_COMPETENCE: ModelCategory.BIAS_CHECK,
    MentalModel.BINARY_SEARCH: ModelCategory.REASONING_STRATEGY,
    MentalModel.RUBBER_DUCK: ModelCategory.REASONING_STRATEGY,
}


@dataclass
class ModelRecommendation:
    mental_model: MentalModel
    reason: str
    confidence_boost: int
    trigger_pattern: str


# Trigger patterns for each model
TRIGGER_PATTERNS = {
    MentalModel.SYSTEMS_THINKING: [
        "works alone but fails together",
        "intermittent",
        "race condition",
        "timing issue",
        "concurrent",
        "interaction between",
        "system behavior",
        "emergent",
        "cross-component",
        "distributed system",
        "feedback loop",
    ],
    MentalModel.FIRST_PRINCIPLES: [
        "never seen this",
        "unusual",
        "novel",
        "edge case",
        "fundamental",
        "unknown",
        "first time",
        "bizarre",
    ],
    MentalModel.SCIENTIFIC_METHOD: [
        "could be either",
        "or maybe",
        "uncertain",
        "multiple causes",
        "hypothesis",
        "theory",
        "might be",
        "possibly",
        "test whether",
    ],
    MentalModel.FIVE_WHYS: [
        "why does",
        "why is",
        "why did",
        "chain of",
        "straightforward",
        "linear cause",
        "direct cause",
    ],
    MentalModel.ISHIKAWA: [
        "complex",
        "many factors",
        "categories",
        "multiple causes",
        "fishbone",
        "several",
    ],
    MentalModel.INVERSION: [
        "prevent",
        "avoid",
        "what if wrong",
        "failure mode",
        "how could fail",
        "risk",
    ],
    MentalModel.OCCAMS_RAZOR: [
        "complex explanation",
        "simplest",
        "overthinking",
        "too complicated",
    ],
    MentalModel.SECOND_ORDER_THINKING: [
        "after",
        "side effects",
        "downstream",
        "ripple",
        "consequence",
        "then what",
    ],
    MentalModel.MARGIN_OF_SAFETY: [
        "buffer",
        "capacity",
        "load",
        "unknowns",
        "failure point",
        "robustness",
        "resilience",
        "safety factor",
    ],
    MentalModel.OPPORTUNITY_COST: [
        "trade-off",
        "instead of",
        "versus",
        "budget",
        "resources",
        "allocation",
        "what else",
        "alternative",
    ],
    MentalModel.PARETO: [
        "80/20",
        "optimization",
        "efficiency",
        "most important",
        "critical few",
        "focus",
        "impact",
        "leverage",
    ],
    MentalModel.ANTIFRAGILITY: [
        "volatility",
        "stress",
        "shock",
        "chaos",
        "disorder",
        "adapt",
        "strength",
        "grow",
    ],
    MentalModel.LEVERAGE_POINTS: [
        "leverage",
        "intervention",
        "small change",
        "big impact",
        "high-impact",
        "influence",
        "amplify",
    ],
    MentalModel.ASYMMETRIC_UPSIDE: [
        "option",
        "upside",
        "limited downside",
        "unlimited upside",
        "convex",
        "positive skew",
        "bet",
    ],
    MentalModel.NETWORK_EFFECTS: [
        "network",
        "user",
        "data",
        "metcalfe",
        "platform",
        "marketplace",
        "multi-sided",
        "viral",
    ],
    MentalModel.OPTIONALITY: [
        "reversible",
        "option",
        "flexibility",
        "preserve",
        "keep open",
        "deferral",
        "wait",
        "modular",
    ],
    MentalModel.FLYWHEEL: [
        "reinforcing",
        "feedback",
        "loop",
        "momentum",
        "compounding",
        "self-sustaining",
        "flywheel",
        "virtuous",
    ],
    MentalModel.SCAMPER: [
        "innovate",
        "brainstorm",
        "creative",
        "new idea",
        "redesign",
        "refactor",
        "ideation",
        "feature",
    ],
    MentalModel.CHAIN_OF_THOUGHT: [
        "step-by-step",
        "reasoning",
        "logic",
        "explain",
        "process",
        "derivation",
        "trace",
    ],
    MentalModel.TREE_OF_THOUGHTS: [
        "options",
        "paths",
        "branches",
        "alternatives",
        "possibilities",
        "explore",
        "scenarios",
    ],
    MentalModel.SELF_CONSISTENCY: [
        "verify",
        "confidence",
        "double check",
        "sample",
        "consensus",
        "validate",
        "sure",
    ],
    MentalModel.ANALOGICAL_REASONING: [
        "similar to",
        "metaphor",
        "analogy",
        "compare",
        "pattern match",
    ],
    MentalModel.CONFIRMATION_BIAS: [
        "confirm",
        "believe",
        "assume",
        "expectation",
        "bias",
        "preconceived",
    ],
    MentalModel.SURVIVORSHIP_BIAS: [
        "success story",
        "worked for",
        "case study",
        "successful",
        "winner",
        "example of",
    ],
    MentalModel.LOSS_AVERSION: [
        "lose",
        "losing",
        "sunk cost",
        "invested",
        "already spent",
        "give up",
    ],
    MentalModel.CIRCLE_OF_COMPETENCE: [
        "expertise",
        "unfamiliar",
        "new domain",
        "don't know",
        "learning",
        "outside my",
    ],
    MentalModel.BINARY_SEARCH: [
        "narrow down",
        "isolate",
        "bisect",
        "half",
        "which half",
        "divide and conquer",
        "git bisect",
    ],
    MentalModel.RUBBER_DUCK: [
        "explain",
        "stuck",
        "confused",
        "don't understand",
        "walk through",
        "talk through",
        "describe",
    ],
}

MODEL_INSTRUCTIONS = {
    MentalModel.SYSTEMS_THINKING: "Identify feedback loops, time delays, and causal circles. How does the system structure create this behavior?",
    MentalModel.FIRST_PRINCIPLES: "Deconstruct the problem to fundamental truths (physics/logic) and build up. Discard all analogies.",
    MentalModel.SCIENTIFIC_METHOD: "Formulate a falsifiable hypothesis. Design an experiment to disprove it. Measure results.",
    MentalModel.FIVE_WHYS: "Ask 'Why?' 5 times to drill down from symptom to root cause.",
    MentalModel.ISHIKAWA: "Categorize potential causes into: Man, Machine, Method, Material, Measurement, Environment.",
    MentalModel.INVERSION: "Invert the problem: What would GUARANTEE failure? How do we avoid those conditions?",
    MentalModel.OCCAMS_RAZOR: "Choose the explanation with the fewest assumptions.",
    MentalModel.SECOND_ORDER_THINKING: "Ask 'And then what?' Trace the consequences of consequences (3rd/4th order effects).",
    MentalModel.MARGIN_OF_SAFETY: "Identify the breaking point. Ensure a 2x buffer (redundancy, capacity) exists.",
    MentalModel.OPPORTUNITY_COST: "Evaluate what is being given up. What is the 'Next Best Alternative'?",
    MentalModel.PARETO: "Identify the 20% of factors driving 80% of the impact. Focus only on those.",
    MentalModel.ANTIFRAGILITY: "Design the system to get STRONGER under stress (e.g., auto-scaling, immune response).",
    MentalModel.LEVERAGE_POINTS: "Find places where small interventions create outsized impact. Where is the system most sensitive to change?",
    MentalModel.ASYMMETRIC_UPSIDE: "Look for opportunities with bounded downside but unbounded upside. What has positive convexity?",
    MentalModel.NETWORK_EFFECTS: "Does this get more valuable as more people/use it? Identify network, data, or platform effects.",
    MentalModel.OPTIONALITY: "Does this preserve future options? Prefer reversible decisions and deferrable commitments.",
    MentalModel.FLYWHEEL: "Is there a self-reinforcing loop? Output that becomes input for the next cycle, creating momentum.",
    MentalModel.SCAMPER: "Ideate: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse.",
    MentalModel.CHAIN_OF_THOUGHT: "Think step-by-step. Show every logical hop explicitly.",
    MentalModel.TREE_OF_THOUGHTS: "Explore 3 distinct reasoning branches. Evaluate each branch's promise before proceeding.",
    MentalModel.SELF_CONSISTENCY: "Generate 3 internal drafts of the answer. Output the consensus/median view.",
    MentalModel.ANALOGICAL_REASONING: "Find a structural similarity in a different domain (e.g., biology, architecture) and map the solution.",
    MentalModel.CONFIRMATION_BIAS: "Actively search for evidence that DISPROVES your current hypothesis.",
    MentalModel.SURVIVORSHIP_BIAS: "Ask: 'What data is missing because it died?' (e.g., closed tickets, failed API calls).",
    MentalModel.LOSS_AVERSION: "Ignore sunk costs. Frame the decision as if starting from scratch today.",
    MentalModel.CIRCLE_OF_COMPETENCE: "Acknowledge boundaries of knowledge. Defer 'guesses' to verified experts/docs.",
    MentalModel.BINARY_SEARCH: "Comment out or disable half the system. If bug persists, it's in the remaining half. Repeat.",
    MentalModel.RUBBER_DUCK: "Explain the code/problem line-by-line out loud. The moment you stumble = the bug location.",
}

CONFIDENCE_BOOSTS = {
    MentalModel.SYSTEMS_THINKING: 15,
    MentalModel.FIRST_PRINCIPLES: 20,
    MentalModel.SCIENTIFIC_METHOD: 10,
    MentalModel.FIVE_WHYS: 5,
    MentalModel.ISHIKAWA: 12,
    MentalModel.INVERSION: 8,
    MentalModel.OCCAMS_RAZOR: 5,
    MentalModel.SECOND_ORDER_THINKING: 10,
    MentalModel.MARGIN_OF_SAFETY: 12,
    MentalModel.OPPORTUNITY_COST: 15,
    MentalModel.PARETO: 10,
    MentalModel.ANTIFRAGILITY: 15,
    MentalModel.LEVERAGE_POINTS: 20,
    MentalModel.ASYMMETRIC_UPSIDE: 22,
    MentalModel.NETWORK_EFFECTS: 18,
    MentalModel.OPTIONALITY: 15,
    MentalModel.FLYWHEEL: 17,
    MentalModel.SCAMPER: 20,
    MentalModel.CHAIN_OF_THOUGHT: 25,
    MentalModel.TREE_OF_THOUGHTS: 25,
    MentalModel.SELF_CONSISTENCY: 18,
    MentalModel.ANALOGICAL_REASONING: 12,
    MentalModel.CONFIRMATION_BIAS: 20,
    MentalModel.SURVIVORSHIP_BIAS: 15,
    MentalModel.LOSS_AVERSION: 18,
    MentalModel.CIRCLE_OF_COMPETENCE: 22,
    MentalModel.BINARY_SEARCH: 20,
    MentalModel.RUBBER_DUCK: 15,
}


def select_mental_models(
    problem_description: str,
    initial_evidence: str = "",
    max_models: int = 3,
) -> list[ModelRecommendation]:
    """
    Auto-select appropriate mental models based on problem characteristics.

    Args:
        problem_description: The problem being investigated
        initial_evidence: Any initial evidence or context
        max_models: Maximum number of models to recommend

    Returns:
        List of ModelRecommendation sorted by confidence boost

    """
    combined_text = f"{problem_description} {initial_evidence}".lower()

    recommendations = []

    for model, patterns in TRIGGER_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in combined_text:
                recommendations.append(
                    ModelRecommendation(
                        mental_model=model,
                        reason=f"Triggered by pattern: '{pattern}'",
                        confidence_boost=CONFIDENCE_BOOSTS[model],
                        trigger_pattern=pattern,
                    )
                )
                break  # Only add each model once

    # Sort by confidence boost
    recommendations.sort(key=lambda r: r.confidence_boost, reverse=True)

    # Default to Five Whys for simple issues
    if not recommendations:
        recommendations.append(
            ModelRecommendation(
                mental_model=MentalModel.FIVE_WHYS,
                reason="Default model for straightforward issues",
                confidence_boost=5,
                trigger_pattern="default",
            )
        )

    return recommendations[:max_models]


def format_recommendations(recommendations: list[ModelRecommendation]) -> str:
    """Format recommendations for display."""
    lines = ["## Mental Model Selection", ""]
    for rec in recommendations:
        category = MODEL_CATEGORIES.get(rec.mental_model, ModelCategory.MENTAL_MODEL)
        instruction = MODEL_INSTRUCTIONS.get(rec.mental_model, "Apply key principles.")

        lines.append(
            f"### [{category.value}] {rec.mental_model.value} (+{rec.confidence_boost}%)"
        )
        lines.append(f"- **Reason:** {rec.reason}")
        lines.append(f"- **Trigger:** {rec.trigger_pattern}")
        lines.append(f"- **Action:** {instruction}")
        lines.append("")
    return "\n".join(lines)


def get_all_models() -> dict[str, list[str]]:
    """
    Return all available models grouped by category.
    Useful for documentation and debugging.
    """
    result: dict[str, list[str]] = {}
    for model in MentalModel:
        category = MODEL_CATEGORIES.get(model, ModelCategory.MENTAL_MODEL)
        cat_name = category.value
        if cat_name not in result:
            result[cat_name] = []
        result[cat_name].append(model.value)
    return result


def select_by_category(
    category: ModelCategory,
    problem_description: str = "",
    max_models: int = 3,
) -> list[ModelRecommendation]:
    """
    Select models filtered to a specific category.

    Args:
        category: The ModelCategory to filter by (MENTAL_MODEL, REASONING_STRATEGY, BIAS_CHECK)
        problem_description: Optional problem text for pattern matching
        max_models: Maximum number of models to return

    Returns:
        List of ModelRecommendation for the specified category

    """
    if problem_description:
        # Get all recommendations, then filter
        all_recs = select_mental_models(problem_description, max_models=10)
        filtered = [
            r for r in all_recs if MODEL_CATEGORIES.get(r.mental_model) == category
        ]
        return filtered[:max_models]
    # Return all models of that category (no pattern matching)
    result = []
    for model, cat in MODEL_CATEGORIES.items():
        if cat == category:
            result.append(
                ModelRecommendation(
                    mental_model=model,
                    reason=f"Category: {category.value}",
                    confidence_boost=CONFIDENCE_BOOSTS[model],
                    trigger_pattern="category_filter",
                )
            )
    result.sort(key=lambda r: r.confidence_boost, reverse=True)
    return result[:max_models]


# CLI interface for direct execution
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print(json.dumps(get_all_models(), indent=2))
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python mental_model_selector.py '<problem_description>'")
        print("       python mental_model_selector.py --list")
        sys.exit(1)

    problem = sys.argv[1]
    evidence = sys.argv[2] if len(sys.argv) > 2 else ""

    recommendations = select_mental_models(problem, evidence)
    print(format_recommendations(recommendations))

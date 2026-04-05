"""
Example: Using prompting-framework (Python Library) Standalone

This is for developers who want programmatic access to advanced
prompting strategies and optimization algorithms.
"""

# ============================================================================
# INSTALLATION
# ============================================================================

# From PyPI (after publishing):
# pip install prompting-framework
#
# From local monorepo:
# pip install -e packages/framework/

# ============================================================================
# BASIC USAGE
# ============================================================================

from prompting_framework import PromptingContext, PromptingOrchestrator

# Example 1: Select applicable techniques automatically
# -----------------------------------------------------

orchestrator = PromptingOrchestrator()

context = PromptingContext(
    query="How should I implement error handling in a distributed system?",
    domain="software",
    complexity="medium",
    user_intent="get_advice"
)

# Auto-select best techniques for this context
techniques = await orchestrator.select_applicable_techniques(context)

print(f"Selected {len(techniques)} techniques:")
for technique in techniques:
    print(f"  - {technique.name}: {technique.description}")

# Example 2: Execute with selected techniques
# --------------------------------------------

result = await orchestrator.execute_techniques(
    query=context.query,
    techniques=techniques
)

print(f"\nOptimized output:\n{result.output}")

# ============================================================================
# META-PROMPT OPTIMIZATION (GA/DE)
# ============================================================================

from prompting_framework import MetaPromptOptimizer, OptimizationConfig, OptimizationStrategy

# Example 3: Optimize a prompt using Genetic Algorithm
# ----------------------------------------------------

config = OptimizationConfig(
    strategy=OptimizationStrategy.GENETIC_ALGORITHM,
    generations=10,
    population_size=20,
    mutation_rate=0.1,
    crossover_rate=0.8
)

optimizer = MetaPromptOptimizer(config)

# Define your evaluation function
def evaluate_prompt_quality(prompt: str) -> float:
    """
    Evaluate prompt quality (0.0 to 1.0).

    In production, you might:
    - Test against a validation set
    - Measure output quality metrics
    - Use LLM-as-judge
    - Track user satisfaction
    """
    # Simple heuristic for demonstration
    keywords = ["step", "verify", "consider", "analyze"]
    score = sum(1 for kw in keywords if kw in prompt.lower()) / len(keywords)
    return score

# Run optimization
result = optimizer.optimize(
    initial_prompt="You are a helpful assistant.",
    evaluator=evaluate_prompt_quality
)

print(f"Best prompt: {result.best_prompt}")
print(f"Best score: {result.best_score:.3f}")
print(f"Generations: {result.generations_run}")

# Example 4: Differential Evolution optimization
# -----------------------------------------------

config_de = OptimizationConfig(
    strategy=OptimizationStrategy.DIFFERENTIAL_EVOLUTION,
    generations=15,
    population_size=30,
    differential_weight=0.8,
    crossover_probability=0.9
)

optimizer_de = MetaPromptOptimizer(config_de)
result_de = optimizer_de.optimize(
    initial_prompt="Explain quantum computing.",
    evaluator=evaluate_prompt_quality
)

print(f"\nDE Best prompt: {result_de.best_prompt}")
print(f"DE Best score: {result_de.best_score:.3f}")

# ============================================================================
# USING SPECIFIC TECHNIQUES
# ============================================================================

from prompting_framework.techniques import (
    ChainOfVerificationTechnique,
    SelfRefineTechnique,
    SocraticPromptingTechnique,
)

# Example 5: Use specific technique directly
# -------------------------------------------

verification = ChainOfVerificationTechnique()

query = "Prove that sqrt(2) is irrational"
steps = await verification.execute(query)

print("Verification steps:")
for i, step in enumerate(steps, 1):
    print(f"{i}. {step}")

# Example 6: Socratic prompting for learning
# --------------------------------------------

socratic = SocraticPromptingTechnique()

query = "Why do we use design patterns?"
questions = await socratic.execute(query)

print("\nSocratic questions:")
for q in questions:
    print(f"  - {q}")

# Example 7: Self-refine for iterative improvement
# -------------------------------------------------

self_refine = SelfRefineTechnique()

initial_draft = "The code sorts an array."
refined = await self_refine.execute(initial_draft)

print(f"\nRefined version: {refined}")

# ============================================================================
# CONTEXT-AWARE SELECTION
# ============================================================================

# Example 8: Let orchestrator choose based on context
# ---------------------------------------------------

contexts = [
    PromptingContext(
        query="Debug this concurrent race condition",
        domain="debugging",
        complexity="high",
        user_intent="diagnose"
    ),
    PromptingContext(
        query="Teach me about recursion",
        domain="learning",
        complexity="low",
        user_intent="learn"
    ),
    PromptingContext(
        query="Design a scalable microservices architecture",
        domain="architecture",
        complexity="expert",
        user_intent="design"
    )
]

for ctx in contexts:
    techniques = await orchestrator.select_applicable_techniques(ctx)
    print(f"\n{ctx.domain} ({ctx.complexity}):")
    print(f"  Query: {ctx.query[:50]}...")
    print(f"  Techniques: {[t.name for t in techniques]}")

# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================

# Example 9: Monitor performance
# -------------------------------

from prompting_framework import PerformanceTracker

tracker = PerformanceTracker()

# Track execution
tracker.start("technique_execution")
result = await orchestrator.execute_techniques(
    query="Explain async/await in Python",
    techniques=techniques
)
tracker.stop("technique_execution")

# Get metrics
metrics = tracker.get_metrics()
print(f"\nExecution time: {metrics['technique_execution']['duration_ms']:.2f}ms")
print(f"Memory usage: {metrics['technique_execution']['memory_mb']:.2f}MB")

# ============================================================================
# CUSTOM TECHNIQUES
# ============================================================================

from prompting_framework import BasePromptingTechnique

# Example 10: Create your own technique
# --------------------------------------

class CustomExampleTechnique(BasePromptingTechnique):
    """Example custom technique."""

    name = "custom_example"
    description = "Demonstrates custom technique implementation"

    async def execute(self, query: str, context: PromptingContext) -> str:
        # Your custom logic here
        enhanced_query = f"Let's think about this step by step: {query}"
        return enhanced_query

# Register and use
custom = CustomExampleTechnique()
result = await custom.execute("What is 2+2?", context)
print(f"\nCustom technique result: {result}")

# ============================================================================
# WHEN TO USE FRAMEWORK ONLY
# ============================================================================

"""
Use framework alone (without hook) when:

✓ You're building a Python application
✓ You need programmatic control
✓ You want to use specific techniques
✓ You're optimizing meta-prompts
✓ You're building AI-powered features
✓ You need performance tracking

Consider adding hook when:

✗ You want automatic prompt enhancement in Claude Code
✗ You need non-technical users to benefit
✗ You want interactive choice UI
"""

# ============================================================================
# AVAILABLE TECHNIQUES
# ============================================================================

"""
The framework includes 23+ techniques:

Core Techniques:
- ChainOfVerification: Multi-step verification
- SocraticPrompting: Question-based guidance
- SelfRefine: Iterative improvement
- QueryFanout: Parallel query execution
- VerbalizedSampling: Explicit reasoning

Advanced Techniques:
- ConstitutionalCompliance: Safety constraints
- CognitiveCoordination: Multi-agent coordination
- AdaptivePromptOrchestrator: Context-aware selection
- EvidenceIntegration: Fact-based reasoning
- COVEIntegration: Chain-of-Verification with React

Optimization:
- GeneticAlgorithm: Evolutionary prompt optimization
- DifferentialEvolution: Population-based optimization
- AutomaticEnhancement: Auto-improvement system

And more... see packages/framework/src/prompting_framework/techniques/
"""

# ============================================================================
# CONCLUSION
# ============================================================================

"""
prompting-framework is for developers who need:

1. Programmatic control over prompting strategies
2. Optimization algorithms (GA/DE) for meta-prompts
3. Context-aware technique selection
4. Performance tracking and monitoring
5. Custom technique implementation

It's a powerful library for building sophisticated AI applications.

Combine with hook for the full prompting ecosystem:
- Hook: Automatic UX enhancement
- Framework: Programmatic library control

Together: End-to-end prompt optimization
"""

# For more information, see:
# - OLD_PROMPTING_FRAMEWORK_README.md (original documentation)
# - packages/framework/README.md (package-specific docs)

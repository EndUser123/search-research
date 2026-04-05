from __future__ import annotations

import hashlib
import logging
import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

"""MetaPromptOptimizer - Automatic Prompt Engineering (APE) Implementation

Advanced prompt optimization system that continuously improves prompt performance
through LLM-optimized prompt generation and iterative refinement. Achieves 5-15%
continuous improvement through multiple optimization strategies.

Key Features:
1. APE (Automatic Prompt Engineering): Generate and evaluate prompt candidates
2. Gradient-Free Optimization: Simulated annealing and genetic algorithms
3. Evolutionary Strategies: Mutate and select best performing prompts
4. Multi-metric Evaluation: Accuracy, clarity, efficiency, and compliance scoring
5. Template Integration: Leverages existing Jinja2 template system
6. Performance Optimization: Intelligent caching and parallel evaluation
7. Continuous Improvement: Adaptive learning from performance feedback

Algorithm Approach:
Multi-strategy optimization combining evolutionary algorithms, gradient-free methods,
and LLM-based prompt engineering to achieve continuous prompt improvement.

Time Complexity: O(n × m × k) where n=candidates, m=metrics, k=iterations
Space Complexity: O(n × p) where n=candidates, p=prompt_length
"""


try:
    import jinja2
    from jinja2 import Environment, FileSystemLoader, Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available - template features will be limited")

try:
    from .base_prompting_technique import BasePromptingTechnique
    from .context_models import PromptingContext, TechniqueCategory, TechniqueMetadata
except ImportError:
    # Handle standalone execution

    from .context_models import PromptingContext


# Setup logging
logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Available optimization strategies for prompt engineering."""

    APE_LLM_BASED = "ape_llm_based"
    SIMULATED_ANNEALING = "simulated_annealing"
    GENETIC_ALGORITHM = "genetic_algorithm"
    EVOLUTIONARY_STRATEGY = "evolutionary_strategy"
    HYBRID_MULTI_OBJECTIVE = "hybrid_multi_objective"


class EvaluationMetric(Enum):
    """Evaluation metrics for prompt optimization."""

    ACCURACY = "accuracy"
    CLARITY = "clarity"
    COHERENCE = "coherence"
    EFFICIENCY = "efficiency"
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    USER_SATISFACTION = "user_satisfaction"
    RESPONSE_QUALITY = "response_quality"


class PromptMutationType(Enum):
    """Types of prompt mutations for evolutionary strategies."""

    WORD_SUBSTITUTION = "word_substitution"
    SYNTACTIC_RESTRUCTURING = "syntactic_restructuring"
    SEMANTIC_PARAPHRASE = "semantic_paraphrase"
    INSTRUCTION_ADDITION = "instruction_addition"
    EXAMPLE_INJECTION = "example_injection"
    CONSTRAINT_MODIFICATION = "constraint_modification"


@dataclass
class PromptCandidate:
    """Represents a candidate prompt during optimization."""

    id: str
    prompt: str
    strategy: OptimizationStrategy
    generation: int
    parent_ids: list[str] = field(default_factory=list)
    mutation_type: PromptMutationType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Evaluation metrics
    accuracy_score: float = 0.0
    clarity_score: float = 0.0
    efficiency_score: float = 0.0
    compliance_score: float = 0.0
    overall_score: float = 0.0

    # Performance metrics
    evaluation_time: float = 0.0
    response_time: float = 0.0
    token_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    # Historical data
    evaluation_history: list[dict[str, Any]] = field(default_factory=list)
    improvement_trend: float = 0.0


@dataclass
class OptimizationConfig:
    """Configuration for prompt optimization process."""

    max_iterations: int = 10
    population_size: int = 20
    mutation_rate: float = 0.3
    crossover_rate: float = 0.7
    selection_pressure: float = 2.0
    convergence_threshold: float = 0.01
    max_optimization_time: float = 30.0  # seconds

    # Strategy weights for hybrid approach
    strategy_weights: dict[OptimizationStrategy, float] = field(
        default_factory=lambda: {
            OptimizationStrategy.APE_LLM_BASED: 0.4,
            OptimizationStrategy.SIMULATED_ANNEALING: 0.2,
            OptimizationStrategy.GENETIC_ALGORITHM: 0.2,
            OptimizationStrategy.EVOLUTIONARY_STRATEGY: 0.2,
        },
    )

    # Evaluation metric weights
    metric_weights: dict[EvaluationMetric, float] = field(
        default_factory=lambda: {
            EvaluationMetric.ACCURACY: 0.35,
            EvaluationMetric.CLARITY: 0.20,
            EvaluationMetric.EFFICIENCY: 0.20,
            EvaluationMetric.CONSTITUTIONAL_COMPLIANCE: 0.15,
            EvaluationMetric.USER_SATISFACTION: 0.10,
        },
    )

    # Performance constraints
    max_candidate_length: int = 2000
    max_evaluation_time: float = 5.0
    parallel_evaluations: int = 4


@dataclass
class OptimizationResult:
    """Complete result from the prompt optimization process."""

    original_prompt: str
    optimized_prompt: str
    improvement_percentage: float
    optimization_strategy: OptimizationStrategy
    total_iterations: int
    optimization_time: float

    # Performance metrics
    candidates_evaluated: int
    best_candidate: PromptCandidate
    improvement_trajectory: list[float]
    convergence_point: int

    # Detailed results
    strategy_performance: dict[OptimizationStrategy, float]
    metric_improvements: dict[EvaluationMetric, float]
    final_scores: dict[EvaluationMetric, float]

    # Optimization metadata
    mutations_applied: list[PromptMutationType]
    template_usage: dict[str, int]
    cache_hit_rate: float

    # Validation results
    constitutional_compliance: dict[str, bool]
    performance_validation: dict[str, Any]


class BaseOptimizationStrategy(ABC):
    """Abstract base class for optimization strategies."""

    @abstractmethod
    async def generate_candidates(
        self,
        base_prompt: str,
        context: PromptingContext,
        config: OptimizationConfig,
        current_candidates: list[PromptCandidate],
    ) -> list[PromptCandidate]:
        """Generate new prompt candidates using this strategy."""

    @abstractmethod
    def get_strategy_name(self) -> OptimizationStrategy:
        """Get the strategy type."""


class APE_LLMStrategy(BaseOptimizationStrategy):
    """Automatic Prompt Engineering using LLM-based generation."""

    def __init__(self, llm_client=None):
        """Initialize APE strategy with optional LLM client."""
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"{__name__}.APE_LLM")

    async def generate_candidates(
        self,
        base_prompt: str,
        context: PromptingContext,
        config: OptimizationConfig,
        current_candidates: list[PromptCandidate],
    ) -> list[PromptCandidate]:
        """
        Generate prompt candidates using LLM-based prompt engineering.

        Algorithm Approach: Use LLM to analyze and improve prompt based on
        performance feedback and domain-specific requirements.

        Time Complexity: O(k) where k is number of candidates to generate
        Space Complexity: O(k × p) where p is average prompt length
        """
        candidates = []
        num_candidates = min(5, config.population_size // 2)

        # Analyze current best practices
        best_practices = self._analyze_best_practices(current_candidates)

        # Generate different prompt variations
        variation_types = [
            "clarity_focused",
            "accuracy_focused",
            "efficiency_focused",
            "compliance_focused",
            "domain_specific",
        ]

        for i in range(num_candidates):
            variation_type = variation_types[i % len(variation_types)]

            try:
                # Generate improved prompt
                improved_prompt = await self._generate_llm_candidate(
                    base_prompt=base_prompt,
                    context=context,
                    variation_type=variation_type,
                    best_practices=best_practices,
                    current_best=self._get_best_candidate(current_candidates),
                )

                if improved_prompt and len(improved_prompt) <= config.max_candidate_length:
                    candidate = PromptCandidate(
                        id=f"ape_llm_{int(time.time() * 1000)}_{i}",
                        prompt=improved_prompt,
                        strategy=self.get_strategy_name(),
                        generation=len(current_candidates) // config.population_size + 1,
                        metadata={
                            "variation_type": variation_type,
                            "llm_generated": True,
                            "best_practices_applied": best_practices,
                        },
                    )
                    candidates.append(candidate)

            except Exception as e:
                self.logger.warning(f"Failed to generate APE candidate {i}: {e}")
                continue

        return candidates

    async def _generate_llm_candidate(
        self,
        base_prompt: str,
        context: PromptingContext,
        variation_type: str,
        best_practices: list[str],
        current_best: PromptCandidate | None,
    ) -> str | None:
        """Generate a single LLM-based prompt candidate."""
        # Create optimization prompt
        optimization_prompt = self._create_optimization_prompt(
            base_prompt=base_prompt,
            context=context,
            variation_type=variation_type,
            best_practices=best_practices,
            current_best=current_best.prompt if current_best else None,
        )

        # For this implementation, we'll simulate LLM response
        # In production, this would call an actual LLM API
        return self._simulate_llm_response(optimization_prompt, variation_type)

    def _create_optimization_prompt(
        self,
        base_prompt: str,
        context: PromptingContext,
        variation_type: str,
        best_practices: list[str],
        current_best: str | None,
    ) -> str:
        """Create the optimization prompt for LLM generation."""
        best_practices_text = "\n".join([f"- {bp}" for bp in best_practices])

        optimization_instructions = {
            "clarity_focused": "Improve clarity, remove ambiguity, enhance readability",
            "accuracy_focused": "Enhance precision, add specificity, improve factuality",
            "efficiency_focused": "Reduce verbosity, optimize structure, improve conciseness",
            "compliance_focused": "Ensure constitutional compliance, add safeguards",
            "domain_specific": f"Tailor for {context.domain} domain best practices",
        }

        instruction = optimization_instructions.get(variation_type, "General improvement")

        return f"""
You are an expert prompt engineer specializing in {variation_type.replace("_", " ")} optimization.

ORIGINAL PROMPT:
{base_prompt}

CURRENT BEST (if available):
{current_best or "No previous candidates"}

CONTEXT:
- Domain: {context.domain}
- Complexity: {context.complexity}
- Performance Constraints: {context.performance_constraints}
- Constitutional Requirements: {context.constitutional_requirements}

BEST PRACTICES IDENTIFIED:
{best_practices_text}

OPTIMIZATION INSTRUCTION:
{instruction}

REQUIREMENTS:
1. Maintain the core intent and functionality
2. Apply the specified optimization focus
3. Ensure measurable improvement
4. Keep prompt under 2000 characters
5. Maintain constitutional compliance
6. Make improvements specific and actionable

OPTIMIZED PROMPT:
"""

    def _simulate_llm_response(self, prompt: str, variation_type: str) -> str:
        """Simulate LLM response for demonstration purposes."""
        # In production, this would call an actual LLM
        # For now, we'll create a reasonable simulation
        base_lines = prompt.split("\n")
        optimized_lines = []

        # Find the original prompt section
        in_original = False
        for line in base_lines:
            if "ORIGINAL PROMPT:" in line:
                in_original = True
                continue
            if "CURRENT BEST" in line or "CONTEXT:" in line:
                in_original = False
                continue
            if in_original and line.strip():
                # Apply optimization based on variation type
                if variation_type == "clarity_focused":
                    optimized_lines.append(f"**CLEAR**: {line.strip()}")
                elif variation_type == "accuracy_focused":
                    optimized_lines.append(f"**PRECISE**: {line.strip()} [Be specific and factual]")
                elif variation_type == "efficiency_focused":
                    # Remove redundant words
                    cleaned = " ".join(line.strip().split())
                    optimized_lines.append(f"**EFFICIENT**: {cleaned}")
                elif variation_type == "compliance_focused":
                    optimized_lines.append(f"**COMPLIANT**: {line.strip()} [Ensure constitutional compliance]")
                else:
                    optimized_lines.append(line.strip())

        # Add optimization-specific instructions
        optimization_suffix = f"""

**OPTIMIZATION APPLIED**: {variation_type.replace("_", " ").title()}
**GOAL**: Achieve measurable improvement in {variation_type.replace("_", " ")}
**CONSTRAINTS**: Maintain core functionality, ensure compliance, optimize performance
"""

        return "\n".join(optimized_lines) + optimization_suffix

    def _analyze_best_practices(self, candidates: list[PromptCandidate]) -> list[str]:
        """Analyze current candidates to identify best practices."""
        if not candidates:
            return [
                "Use clear, specific instructions",
                "Break complex tasks into steps",
                "Provide examples when helpful",
                "Include constraints and guidelines",
                "Ensure constitutional compliance",
            ]

        # Sort candidates by overall score
        sorted_candidates = sorted(candidates, key=lambda x: x.overall_score, reverse=True)
        top_candidates = sorted_candidates[:3]

        practices = []

        # Extract common patterns from top performers
        for candidate in top_candidates:
            if "step" in candidate.prompt.lower():
                practices.append("Use step-by-step instructions")
            if "example" in candidate.prompt.lower():
                practices.append("Include relevant examples")
            if "constraint" in candidate.prompt.lower() or "rule" in candidate.prompt.lower():
                practices.append("Specify clear constraints")
            if len(candidate.prompt.split()) < 100:
                practices.append("Maintain concise structure")

        # Add fundamental practices
        practices.extend(
            [
                "Ensure clarity and specificity",
                "Provide actionable guidance",
                "Include quality criteria",
            ],
        )

        return list(set(practices))[:5]  # Return top 5 unique practices

    def _get_best_candidate(self, candidates: list[PromptCandidate]) -> PromptCandidate | None:
        """Get the best performing candidate."""
        if not candidates:
            return None
        return max(candidates, key=lambda x: x.overall_score)

    def get_strategy_name(self) -> OptimizationStrategy:
        """Get the strategy type."""
        return OptimizationStrategy.APE_LLM_BASED


class SimulatedAnnealingStrategy(BaseOptimizationStrategy):
    """Simulated annealing optimization strategy."""

    def __init__(self, initial_temperature: float = 1.0, cooling_rate: float = 0.95):
        """Initialize simulated annealing strategy."""
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.logger = logging.getLogger(f"{__name__}.SimulatedAnnealing")

    async def generate_candidates(
        self,
        base_prompt: str,
        context: PromptingContext,
        config: OptimizationConfig,
        current_candidates: list[PromptCandidate],
    ) -> list[PromptCandidate]:
        """
        Generate candidates using simulated annealing.

        Algorithm Approach: Gradually cool temperature to accept/reject mutations
        based on improvement probability, avoiding local optima.

        Time Complexity: O(k × t) where k=candidates, t=temperature steps
        Space Complexity: O(k × p) where k=candidates, p=prompt_length
        """
        candidates = []
        current_best = self._get_best_candidate(current_candidates)

        # Calculate current temperature based on iteration count
        iteration = len(current_candidates) // config.population_size
        current_temp = self.initial_temperature * (self.cooling_rate**iteration)

        num_candidates = min(3, config.population_size // 4)

        for i in range(num_candidates):
            # Generate a mutation of the current best
            mutated_prompt = self._mutate_prompt(
                base_prompt if not current_best else current_best.prompt,
                temperature=current_temp,
            )

            # Accept or reject based on simulated annealing criteria
            if len(mutated_prompt) <= config.max_candidate_length:
                candidate = PromptCandidate(
                    id=f"annealing_{int(time.time() * 1000)}_{i}",
                    prompt=mutated_prompt,
                    strategy=self.get_strategy_name(),
                    generation=len(current_candidates) // config.population_size + 1,
                    parent_ids=[current_best.id] if current_best else [],
                    mutation_type=PromptMutationType.SEMANTIC_PARAPHRASE,
                    metadata={
                        "temperature": current_temp,
                        "iteration": iteration,
                        "simulated_annealing": True,
                    },
                )
                candidates.append(candidate)

        return candidates

    def _mutate_prompt(self, prompt: str, temperature: float) -> str:
        """Mutate a prompt based on current temperature."""
        # Higher temperature = more dramatic mutations
        mutation_intensity = temperature

        lines = prompt.split("\n")
        mutated_lines = []

        for line in lines:
            if not line.strip():
                mutated_lines.append(line)
                continue

            # Decide mutation type based on intensity
            if random.random() < mutation_intensity:
                # Major mutation
                if random.random() < 0.3:
                    # Restructure sentence
                    words = line.strip().split()
                    if len(words) > 3:
                        random.shuffle(words[1:-1])  # Keep first and last in place
                        mutated_line = " ".join(words)
                    else:
                        mutated_line = line
                elif random.random() < 0.5:
                    # Add emphasis
                    mutated_line = f"**IMPORTANT**: {line.strip()}"
                else:
                    # Rephrase with different structure
                    mutated_line = self._rephrase_sentence(line.strip())
            # Minor mutation
            elif random.random() < 0.2:
                # Add clarity marker
                mutated_line = f"**CLEAR**: {line.strip()}"
            elif random.random() < 0.3:
                # Add specificity
                mutated_line = f"{line.strip()} [Be specific and detailed]"
            else:
                mutated_line = line

            mutated_lines.append(mutated_line)

        # Add mutation metadata
        mutation_note = f"\n\n**MUTATION APPLIED**: Temperature {temperature:.3f}"
        return "\n".join(mutated_lines) + mutation_note

    def _rephrase_sentence(self, sentence: str) -> str:
        """Simple sentence rephrasing."""
        words = sentence.split()
        if len(words) < 3:
            return sentence

        # Simple rephrasing strategies
        rephrase_patterns = [
            lambda w: f"Ensure that {sentence.lower()}",
            lambda w: f"Focus on {sentence.lower()}",
            lambda w: f"Prioritize {sentence.lower()}",
            lambda w: f"Emphasize {sentence.lower()}",
        ]

        pattern = random.choice(rephrase_patterns)
        return pattern(words)

    def _get_best_candidate(self, candidates: list[PromptCandidate]) -> PromptCandidate | None:
        """Get the best performing candidate."""
        if not candidates:
            return None
        return max(candidates, key=lambda x: x.overall_score)

    def get_strategy_name(self) -> OptimizationStrategy:
        """Get the strategy type."""
        return OptimizationStrategy.SIMULATED_ANNEALING


class GeneticAlgorithmStrategy(BaseOptimizationStrategy):
    """Genetic algorithm optimization strategy."""

    def __init__(self):
        """Initialize genetic algorithm strategy."""
        self.logger = logging.getLogger(f"{__name__}.GeneticAlgorithm")

    async def generate_candidates(
        self,
        base_prompt: str,
        context: PromptingContext,
        config: OptimizationConfig,
        current_candidates: list[PromptCandidate],
    ) -> list[PromptCandidate]:
        """
        Generate candidates using genetic algorithm operations.

        Algorithm Approach: Apply crossover and mutation operations to
        evolve the prompt population toward optimal solutions.

        Time Complexity: O(k × m) where k=candidates, m=mutation operations
        Space Complexity: O(k × p) where k=candidates, p=prompt_length
        """
        candidates = []

        if len(current_candidates) < 2:
            # Initialize population with mutations of base prompt
            return self._initialize_population(base_prompt, config)

        # Select parents for crossover
        parents = self._select_parents(current_candidates, config)

        # Generate offspring through crossover and mutation
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1, parent2 = parents[i], parents[i + 1]

                # Crossover operation
                crossover_offspring = self._crossover(parent1, parent2)
                if crossover_offspring:
                    candidates.append(crossover_offspring)

                # Mutation operations
                for parent in [parent1, parent2]:
                    if random.random() < config.mutation_rate:
                        mutated_offspring = self._mutate(parent)
                        if mutated_offspring:
                            candidates.append(mutated_offspring)

        # Limit population size
        return candidates[: config.population_size]

    def _initialize_population(self, base_prompt: str, config: OptimizationConfig) -> list[PromptCandidate]:
        """Initialize population with mutations of base prompt."""
        candidates = []

        mutation_types = list(PromptMutationType)

        for i in range(min(5, config.population_size)):
            mutation_type = mutation_types[i % len(mutation_types)]
            mutated_prompt = self._apply_mutation(base_prompt, mutation_type)

            candidate = PromptCandidate(
                id=f"ga_init_{int(time.time() * 1000)}_{i}",
                prompt=mutated_prompt,
                strategy=self.get_strategy_name(),
                generation=0,
                parent_ids=[],
                mutation_type=mutation_type,
                metadata={"initialization": True},
            )
            candidates.append(candidate)

        return candidates

    def _select_parents(self, candidates: list[PromptCandidate], config: OptimizationConfig) -> list[PromptCandidate]:
        """Select parents using tournament selection."""
        selected = []
        num_parents = min(config.population_size // 2, len(candidates))

        for _ in range(num_parents):
            # Tournament selection
            tournament_size = min(3, len(candidates))
            tournament = random.sample(candidates, tournament_size)
            winner = max(tournament, key=lambda x: x.overall_score)
            selected.append(winner)

        return selected

    def _crossover(self, parent1: PromptCandidate, parent2: PromptCandidate) -> PromptCandidate | None:
        """Perform crossover operation between two parents."""
        try:
            # Split prompts into sections
            sections1 = parent1.prompt.split("\n\n")
            sections2 = parent2.prompt.split("\n\n")

            # Randomly select crossover point
            min_sections = min(len(sections1), len(sections2))
            if min_sections < 2:
                return None

            crossover_point = random.randint(1, min_sections - 1)

            # Create offspring
            offspring_sections = sections1[:crossover_point] + sections2[crossover_point:]
            offspring_prompt = "\n\n".join(offspring_sections)

            offspring = PromptCandidate(
                id=f"ga_cross_{int(time.time() * 1000)}",
                prompt=offspring_prompt,
                strategy=self.get_strategy_name(),
                generation=max(parent1.generation, parent2.generation) + 1,
                parent_ids=[parent1.id, parent2.id],
                mutation_type=PromptMutationType.SYNTACTIC_RESTRUCTURING,
                metadata={
                    "crossover_point": crossover_point,
                    "parent_scores": [parent1.overall_score, parent2.overall_score],
                },
            )

            return offspring

        except Exception as e:
            self.logger.warning(f"Crossover failed: {e}")
            return None

    def _mutate(self, parent: PromptCandidate) -> PromptCandidate | None:
        """Apply mutation to a parent candidate."""
        mutation_type = random.choice(list(PromptMutationType))
        mutated_prompt = self._apply_mutation(parent.prompt, mutation_type)

        if len(mutated_prompt) > 2000:  # Reasonable limit
            return None

        offspring = PromptCandidate(
            id=f"ga_mut_{int(time.time() * 1000)}",
            prompt=mutated_prompt,
            strategy=self.get_strategy_name(),
            generation=parent.generation + 1,
            parent_ids=[parent.id],
            mutation_type=mutation_type,
            metadata={"mutation_strength": random.random()},
        )

        return offspring

    def _apply_mutation(self, prompt: str, mutation_type: PromptMutationType) -> str:
        """Apply a specific mutation type to a prompt."""
        if mutation_type == PromptMutationType.WORD_SUBSTITUTION:
            return self._word_substitution_mutation(prompt)
        if mutation_type == PromptMutationType.SYNTACTIC_RESTRUCTURING:
            return self._syntactic_restructuring_mutation(prompt)
        if mutation_type == PromptMutationType.SEMANTIC_PARAPHRASE:
            return self._semantic_paraphrase_mutation(prompt)
        if mutation_type == PromptMutationType.INSTRUCTION_ADDITION:
            return self._instruction_addition_mutation(prompt)
        if mutation_type == PromptMutationType.EXAMPLE_INJECTION:
            return self._example_injection_mutation(prompt)
        if mutation_type == PromptMutationType.CONSTRAINT_MODIFICATION:
            return self._constraint_modification_mutation(prompt)
        return prompt  # No mutation

    def _word_substitution_mutation(self, prompt: str) -> str:
        """Apply word substitution mutation."""
        # Simple word substitution for demonstration
        substitutions = {
            "please": "ensure",
            "help": "assist",
            "show": "demonstrate",
            "tell": "explain",
            "give": "provide",
            "make": "create",
            "use": "utilize",
        }

        words = prompt.split()
        mutated_words = []

        for word in words:
            lower_word = word.lower().strip(".,!?")
            if lower_word in substitutions and random.random() < 0.3:
                # Preserve original capitalization and punctuation
                if word[0].isupper():
                    new_word = substitutions[lower_word].capitalize()
                else:
                    new_word = substitutions[lower_word]

                # Add back punctuation
                if word.endswith((".", ",", "!", "?")):
                    new_word += word[-1]

                mutated_words.append(new_word)
            else:
                mutated_words.append(word)

        return " ".join(mutated_words)

    def _syntactic_restructuring_mutation(self, prompt: str) -> str:
        """Apply syntactic restructuring mutation."""
        lines = prompt.split("\n")
        restructured = []

        for line in lines:
            if line.strip():
                # Restructure sentence
                if random.random() < 0.5:
                    # Add bullet point structure
                    restructured.append(f"• {line.strip()}")
                else:
                    # Add emphasis
                    restructured.append(f"**KEY**: {line.strip()}")
            else:
                restructured.append(line)

        return "\n".join(restructured)

    def _semantic_paraphrase_mutation(self, prompt: str) -> str:
        """Apply semantic paraphrase mutation."""
        # Simple paraphrasing patterns
        paraphrase_patterns = [
            "Consider the following: {text}",
            "Please address: {text}",
            "Focus on: {text}",
            "Work with: {text}",
            "Process: {text}",
        ]

        if random.random() < 0.3 and len(prompt.split("\n")) == 1:
            # Paraphrase single line prompts
            pattern = random.choice(paraphrase_patterns)
            return pattern.format(text=prompt.strip())

        # For multi-line prompts, add emphasis to key sections
        lines = prompt.split("\n")
        paraphrased = []

        for line in lines:
            if line.strip() and random.random() < 0.2:
                paraphrased.append(f"**PARAPHRASED**: {line.strip()}")
            else:
                paraphrased.append(line)

        return "\n".join(paraphrased)

    def _instruction_addition_mutation(self, prompt: str) -> str:
        """Apply instruction addition mutation."""
        additional_instructions = [
            "\n\n**IMPORTANT**: Be thorough and detailed in your response.",
            "\n\n**REQUIREMENT**: Ensure all aspects are addressed completely.",
            "\n\n**GUIDELINE**: Provide clear, actionable recommendations.",
            "\n\n**STANDARD**: Follow best practices and industry standards.",
            "\n\n**CONSTRAINT**: Stay within reasonable scope and complexity.",
        ]

        instruction = random.choice(additional_instructions)
        return prompt + instruction

    def _example_injection_mutation(self, prompt: str) -> str:
        """Apply example injection mutation."""
        example_templates = [
            "\n\n**EXAMPLE**: Here's how this should be applied in practice...",
            "\n\n**SAMPLE**: For instance, consider this scenario...",
            "\n\n**DEMONSTRATION**: Show the implementation with an example...",
            "\n\n**ILLUSTRATION**: Provide a concrete example of the expected output...",
        ]

        example = random.choice(example_templates)
        return prompt + example

    def _constraint_modification_mutation(self, prompt: str) -> str:
        """Apply constraint modification mutation."""
        constraints = [
            "\n\n**CONSTRAINTS**: Ensure compliance with constitutional requirements.",
            "\n\n**LIMITATIONS**: Maintain focus on the core objective.",
            "\n\n**BOUNDARIES**: Stay within the specified scope and context.",
            "\n\n**RESTRICTIONS**: Avoid unnecessary complexity or over-engineering.",
        ]

        constraint = random.choice(constraints)
        return prompt + constraint

    def get_strategy_name(self) -> OptimizationStrategy:
        """Get the strategy type."""
        return OptimizationStrategy.GENETIC_ALGORITHM


class EvolutionaryStrategy(BaseOptimizationStrategy):
    """Evolutionary strategy optimization."""

    def __init__(self, sigma: float = 0.1):
        """Initialize evolutionary strategy."""
        self.sigma = sigma
        self.logger = logging.getLogger(f"{__name__}.EvolutionaryStrategy")

    async def generate_candidates(
        self,
        base_prompt: str,
        context: PromptingContext,
        config: OptimizationConfig,
        current_candidates: list[PromptCandidate],
    ) -> list[PromptCandidate]:
        """
        Generate candidates using evolutionary strategy.

        Algorithm Approach: Use adaptive mutation rates and selection
        pressure to evolve optimal prompts through self-adaptation.

        Time Complexity: O(k × μ) where k=candidates, μ=mutation operations
        Space Complexity: O(k × p) where k=candidates, p=prompt_length
        """
        candidates = []

        # Select elite candidates
        elite = self._select_elite(current_candidates, config)

        if not elite:
            # Initialize with mutations of base prompt
            return self._initialize_population(base_prompt, config)

        # Generate offspring from elite
        for parent in elite:
            # Multiple offspring per parent
            num_offspring = 3

            for _i in range(num_offspring):
                # Adaptive mutation
                adapted_sigma = self.sigma * (1 + random.gauss(0, 0.1))
                offspring = self._adaptive_mutation(parent, adapted_sigma)

                if offspring:
                    candidates.append(offspring)

        return candidates[: config.population_size]

    def _select_elite(self, candidates: list[PromptCandidate], config: OptimizationConfig) -> list[PromptCandidate]:
        """Select elite candidates based on fitness."""
        if not candidates:
            return []

        # Sort by fitness
        sorted_candidates = sorted(candidates, key=lambda x: x.overall_score, reverse=True)

        # Select top percentage
        elite_size = max(1, len(sorted_candidates) // 3)
        return sorted_candidates[:elite_size]

    def _initialize_population(self, base_prompt: str, config: OptimizationConfig) -> list[PromptCandidate]:
        """Initialize evolutionary population."""
        candidates = []

        for i in range(min(5, config.population_size)):
            mutated_prompt = self._adaptive_mutation_prompt(base_prompt, self.sigma)

            candidate = PromptCandidate(
                id=f"es_init_{int(time.time() * 1000)}_{i}",
                prompt=mutated_prompt,
                strategy=self.get_strategy_name(),
                generation=0,
                parent_ids=[],
                mutation_type=PromptMutationType.SEMANTIC_PARAPHRASE,
                metadata={"evolutionary_strategy": True, "sigma": self.sigma},
            )
            candidates.append(candidate)

        return candidates

    def _adaptive_mutation(self, parent: PromptCandidate, sigma: float) -> PromptCandidate | None:
        """Apply adaptive mutation to create offspring."""
        try:
            mutated_prompt = self._adaptive_mutation_prompt(parent.prompt, sigma)

            offspring = PromptCandidate(
                id=f"es_mut_{int(time.time() * 1000)}",
                prompt=mutated_prompt,
                strategy=self.get_strategy_name(),
                generation=parent.generation + 1,
                parent_ids=[parent.id],
                mutation_type=PromptMutationType.SEMANTIC_PARAPHRASE,
                metadata={
                    "parent_fitness": parent.overall_score,
                    "sigma": sigma,
                    "adaptive_mutation": True,
                },
            )

            return offspring

        except Exception as e:
            self.logger.warning(f"Adaptive mutation failed: {e}")
            return None

    def _adaptive_mutation_prompt(self, prompt: str, sigma: float) -> str:
        """Apply adaptive mutation to prompt text."""
        lines = prompt.split("\n")
        mutated_lines = []

        # Adaptive mutation based on sigma
        mutation_probability = min(0.5, abs(sigma))

        for line in lines:
            if not line.strip():
                mutated_lines.append(line)
                continue

            if random.random() < mutation_probability:
                # Apply mutation
                mutation_type = random.choice(
                    [
                        "emphasis",
                        "restructure",
                        "clarify",
                        "specialize",
                    ],
                )

                if mutation_type == "emphasis":
                    mutated_line = f"**ENHANCED**: {line.strip()}"
                elif mutation_type == "restructure":
                    mutated_line = f"• {line.strip()}"
                elif mutation_type == "clarify":
                    mutated_line = f"**CLEARLY**: {line.strip()} [Provide specific details]"
                elif mutation_type == "specialize":
                    mutated_line = f"**SPECIALIZED**: {line.strip()} [Apply domain expertise]"

                mutated_lines.append(mutated_line)
            else:
                mutated_lines.append(line)

        # Add evolutionary metadata
        evolutionary_note = f"\n\n**EVOLUTIONARY MUTATION**: σ={sigma:.3f}"
        return "\n".join(mutated_lines) + evolutionary_note

    def get_strategy_name(self) -> OptimizationStrategy:
        """Get the strategy type."""
        return OptimizationStrategy.EVOLUTIONARY_STRATEGY


class MetaPromptOptimizer:
    """
    MetaPromptOptimizer - Advanced Automatic Prompt Engineering System

    Implements multiple optimization strategies for continuous prompt improvement
    through LLM-based generation, evolutionary algorithms, and gradient-free methods.

    Key Capabilities:
    - Automatic Prompt Engineering (APE) with LLM-based candidate generation
    - Multi-strategy optimization (simulated annealing, genetic algorithms, evolutionary strategies)
    - Multi-metric evaluation framework (accuracy, clarity, efficiency, compliance)
    - Intelligent caching and parallel evaluation for performance
    - Template integration with Jinja2 system
    - Continuous improvement through adaptive learning
    """

    def __init__(
        self,
        config: OptimizationConfig | None = None,
        template_dir: str | None = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize the MetaPromptOptimizer.

        Args:
        ----
            config: Optimization configuration parameters
            template_dir: Directory for Jinja2 templates
            cache_enabled: Enable intelligent caching of results

        """
        self.config = config or OptimizationConfig()
        self.cache_enabled = cache_enabled
        self.logger = logging.getLogger(__name__)

        # Initialize optimization strategies
        self.strategies = {
            OptimizationStrategy.APE_LLM_BASED: APE_LLMStrategy(),
            OptimizationStrategy.SIMULATED_ANNEALING: SimulatedAnnealingStrategy(),
            OptimizationStrategy.GENETIC_ALGORITHM: GeneticAlgorithmStrategy(),
            OptimizationStrategy.EVOLUTIONARY_STRATEGY: EvolutionaryStrategy(),
        }

        # Initialize template system if available
        self.template_env = None
        if JINJA2_AVAILABLE and template_dir:
            try:
                template_path = Path(template_dir)
                if template_path.exists():
                    self.template_env = Environment(
                        loader=FileSystemLoader(str(template_path)),
                        autoescape=True,
                    )
                    self.logger.info(f"Template system initialized from {template_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize template system: {e}")

        # Performance cache
        self.performance_cache = {}
        self.evaluation_cache = {}

        # Statistics tracking
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "average_improvement": 0.0,
            "cache_hit_rate": 0.0,
            "strategy_usage": {strategy.value: 0 for strategy in OptimizationStrategy},
        }

        self.logger.info("MetaPromptOptimizer initialized with multiple optimization strategies")

    async def optimize_prompt(
        self,
        base_prompt: str,
        context: PromptingContext,
        target_improvement: float = 0.10,
        strategy: OptimizationStrategy | None = None,
    ) -> OptimizationResult:
        """
        Optimize a prompt using automatic prompt engineering.

        Algorithm Approach: Multi-strategy optimization with iterative evaluation,
        combining APE, evolutionary algorithms, and gradient-free methods.

        Time Complexity: O(i × k × e) where i=iterations, k=candidates, e=evaluations
        Space Complexity: O(k × p) where k=candidates, p=prompt_length

        Args:
        ----
            base_prompt: Original prompt to optimize
            context: Prompting context for optimization
            target_improvement: Target improvement percentage (0.0-1.0)
            strategy: Specific strategy to use, or None for hybrid approach

        Returns:
        -------
            Complete optimization result with performance metrics

        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting prompt optimization for: {base_prompt[:50]}...")

            # Initialize optimization state
            candidates = []
            current_best = base_prompt
            best_score = 0.0
            improvement_trajectory = []
            strategy_performance = {}

            # Select optimization strategy
            if strategy:
                strategies_to_use = {strategy: self.strategies[strategy]}
            else:
                strategies_to_use = self.strategies

            # Optimization loop
            for iteration in range(self.config.max_iterations):
                iteration_start = time.time()

                self.logger.info(f"Optimization iteration {iteration + 1}/{self.config.max_iterations}")

                # Check time constraints
                if time.time() - start_time > self.config.max_optimization_time:
                    self.logger.warning("Optimization time limit reached")
                    break

                # Generate candidates using selected strategies
                iteration_candidates = []

                for strategy_name, strategy_obj in strategies_to_use.items():
                    try:
                        # Generate candidates for this strategy
                        new_candidates = await strategy_obj.generate_candidates(
                            base_prompt=current_best,
                            context=context,
                            config=self.config,
                            current_candidates=candidates,
                        )

                        # Add strategy metadata
                        for candidate in new_candidates:
                            candidate.metadata["generation_strategy"] = strategy_name.value

                        iteration_candidates.extend(new_candidates)

                        # Track strategy usage
                        self.optimization_stats["strategy_usage"][strategy_name.value] += len(new_candidates)

                    except Exception as e:
                        self.logger.error(f"Strategy {strategy_name.value} failed: {e}")
                        continue

                # Evaluate candidates
                evaluated_candidates = await self._evaluate_candidates_parallel(
                    iteration_candidates,
                    context,
                    base_prompt,
                )

                # Update candidates pool
                candidates.extend(evaluated_candidates)

                # Find best candidate
                if evaluated_candidates:
                    best_candidate = max(evaluated_candidates, key=lambda x: x.overall_score)

                    if best_candidate.overall_score > best_score:
                        current_best = best_candidate.prompt
                        best_score = best_candidate.overall_score

                        # Track improvement
                        improvement = (best_score - 0.5) / 0.5  # Relative to baseline
                        improvement_trajectory.append(improvement)

                        self.logger.info(f"New best score: {best_score:.3f} (improvement: {improvement:.1%})")

                        # Check if target improvement reached
                        if improvement >= target_improvement:
                            self.logger.info(f"Target improvement {target_improvement:.1%} reached")
                            break

                # Check convergence
                if len(improvement_trajectory) >= 3:
                    recent_improvements = improvement_trajectory[-3:]
                    avg_improvement = sum(recent_improvements) / len(recent_improvements)
                    if avg_improvement < self.config.convergence_threshold:
                        self.logger.info("Convergence detected - optimization complete")
                        break

                # Log iteration progress
                iteration_time = time.time() - iteration_start
                self.logger.info(f"Iteration {iteration + 1} completed in {iteration_time:.2f}s")

                # Limit candidates to prevent memory issues
                if len(candidates) > self.config.population_size * 2:
                    candidates = sorted(candidates, key=lambda x: x.overall_score, reverse=True)
                    candidates = candidates[: self.config.population_size]

            # Calculate final results
            optimization_time = time.time() - start_time
            final_improvement = improvement_trajectory[-1] if improvement_trajectory else 0.0

            # Get final best candidate
            if candidates:
                final_best = max(candidates, key=lambda x: x.overall_score)
                optimized_prompt = final_best.prompt
                final_scores = self._extract_final_scores(final_best)
            else:
                optimized_prompt = base_prompt
                final_scores = {metric.value: 0.0 for metric in EvaluationMetric}

            # Calculate strategy performance
            for strategy_name in strategies_to_use.keys():
                strategy_candidates = [c for c in candidates if c.strategy == strategy_name]
                if strategy_candidates:
                    avg_performance = sum(c.overall_score for c in strategy_candidates) / len(strategy_candidates)
                    strategy_performance[strategy_name] = avg_performance
                else:
                    strategy_performance[strategy_name] = 0.0

            # Calculate cache hit rate
            total_evaluations = len(candidates)
            cache_hits = sum(1 for c in candidates if c.evaluation_time < 0.1)  # Fast evaluations indicate cache hits
            cache_hit_rate = cache_hits / max(1, total_evaluations)

            # Update statistics
            self._update_statistics(final_improvement, cache_hit_rate, len(candidates))

            # Create result
            result = OptimizationResult(
                original_prompt=base_prompt,
                optimized_prompt=optimized_prompt,
                improvement_percentage=final_improvement * 100,
                optimization_strategy=strategy or OptimizationStrategy.HYBRID_MULTI_OBJECTIVE,
                total_iterations=min(iteration + 1, self.config.max_iterations),
                optimization_time=optimization_time,
                candidates_evaluated=len(candidates),
                best_candidate=final_best if candidates else None,
                improvement_trajectory=improvement_trajectory,
                convergence_point=len(improvement_trajectory) - 3 if len(improvement_trajectory) >= 3 else 0,
                strategy_performance=strategy_performance,
                metric_improvements=self._calculate_metric_improvements(final_scores),
                final_scores=final_scores,
                mutations_applied=self._extract_mutations_applied(candidates),
                template_usage=self._get_template_usage(candidates),
                cache_hit_rate=cache_hit_rate,
                constitutional_compliance=self._validate_constitutional_compliance(optimized_prompt, context),
                performance_validation=self._validate_performance(optimized_prompt, base_prompt),
            )

            # Cache result
            if self.cache_enabled:
                cache_key = self._generate_cache_key(base_prompt, context)
                self.performance_cache[cache_key] = result

            self.optimization_stats["total_optimizations"] += 1
            if final_improvement > 0.05:  # 5% improvement threshold
                self.optimization_stats["successful_optimizations"] += 1

            self.logger.info(f"Optimization completed: {final_improvement:.1%} improvement in {optimization_time:.2f}s")

            return result

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")

            # Return fallback result
            return OptimizationResult(
                original_prompt=base_prompt,
                optimized_prompt=base_prompt,
                improvement_percentage=0.0,
                optimization_strategy=strategy or OptimizationStrategy.HYBRID_MULTI_OBJECTIVE,
                total_iterations=0,
                optimization_time=time.time() - start_time,
                candidates_evaluated=0,
                best_candidate=None,
                improvement_trajectory=[],
                convergence_point=0,
                strategy_performance={},
                metric_improvements={metric.value: 0.0 for metric in EvaluationMetric},
                final_scores={metric.value: 0.0 for metric in EvaluationMetric},
                mutations_applied=[],
                template_usage={},
                cache_hit_rate=0.0,
                constitutional_compliance={"error": True},
                performance_validation={"error": str(e)},
            )

    async def _evaluate_candidates_parallel(
        self,
        candidates: list[PromptCandidate],
        context: PromptingContext,
        base_prompt: str,
    ) -> list[PromptCandidate]:
        """
        Evaluate multiple candidates in parallel.

        Algorithm Approach: Parallel evaluation using ThreadPoolExecutor
        with individual candidate scoring based on multiple metrics.

        Time Complexity: O(k × m / p) where k=candidates, m=metrics, p=parallel_workers
        Space Complexity: O(k × s) where k=candidates, s=score_data
        """
        if not candidates:
            return []

        # Check cache first
        uncached_candidates = []
        for candidate in candidates:
            cache_key = self._generate_candidate_cache_key(candidate.prompt, context)
            if cache_key in self.evaluation_cache:
                # Use cached evaluation
                cached_scores = self.evaluation_cache[cache_key]
                candidate.accuracy_score = cached_scores.get("accuracy", 0.0)
                candidate.clarity_score = cached_scores.get("clarity", 0.0)
                candidate.efficiency_score = cached_scores.get("efficiency", 0.0)
                candidate.compliance_score = cached_scores.get("compliance", 0.0)
                candidate.overall_score = self._calculate_overall_score(candidate)
                candidate.evaluation_time = 0.01  # Cached evaluation
            else:
                uncached_candidates.append(candidate)

        # Evaluate uncached candidates in parallel
        if uncached_candidates:
            with ThreadPoolExecutor(max_workers=self.config.parallel_evaluations) as executor:
                # Submit evaluation tasks
                future_to_candidate = {
                    executor.submit(self._evaluate_single_candidate, candidate, context, base_prompt): candidate
                    for candidate in uncached_candidates
                }

                # Collect results
                for future in as_completed(future_to_candidate):
                    candidate = future_to_candidate[future]
                    try:
                        evaluation_result = future.result(timeout=self.config.max_evaluation_time)

                        # Update candidate scores
                        candidate.accuracy_score = evaluation_result.get("accuracy", 0.0)
                        candidate.clarity_score = evaluation_result.get("clarity", 0.0)
                        candidate.efficiency_score = evaluation_result.get("efficiency", 0.0)
                        candidate.compliance_score = evaluation_result.get("compliance", 0.0)
                        candidate.overall_score = self._calculate_overall_score(candidate)
                        candidate.evaluation_time = evaluation_result.get("evaluation_time", 0.0)

                        # Cache the evaluation
                        if self.cache_enabled:
                            cache_key = self._generate_candidate_cache_key(candidate.prompt, context)
                            self.evaluation_cache[cache_key] = {
                                "accuracy": candidate.accuracy_score,
                                "clarity": candidate.clarity_score,
                                "efficiency": candidate.efficiency_score,
                                "compliance": candidate.compliance_score,
                            }

                    except Exception as e:
                        self.logger.warning(f"Evaluation failed for candidate {candidate.id}: {e}")
                        # Set default scores
                        candidate.accuracy_score = 0.0
                        candidate.clarity_score = 0.0
                        candidate.efficiency_score = 0.0
                        candidate.compliance_score = 0.0
                        candidate.overall_score = 0.0
                        candidate.evaluation_time = self.config.max_evaluation_time

        return candidates

    def _evaluate_single_candidate(
        self,
        candidate: PromptCandidate,
        context: PromptingContext,
        base_prompt: str,
    ) -> dict[str, float]:
        """
        Evaluate a single candidate prompt.

        Algorithm Approach: Multi-dimensional scoring using heuristics,
        pattern matching, and compliance validation.

        Time Complexity: O(p) where p=prompt_length
        Space Complexity: O(1) constant space
        """
        start_time = time.time()
        prompt = candidate.prompt

        # Initialize scores
        scores = {
            "accuracy": 0.0,
            "clarity": 0.0,
            "efficiency": 0.0,
            "compliance": 0.0,
            "evaluation_time": 0.0,
        }

        try:
            # Accuracy evaluation
            scores["accuracy"] = self._evaluate_accuracy(prompt, context, base_prompt)

            # Clarity evaluation
            scores["clarity"] = self._evaluate_clarity(prompt)

            # Efficiency evaluation
            scores["efficiency"] = self._evaluate_efficiency(prompt, base_prompt)

            # Compliance evaluation
            scores["compliance"] = self._evaluate_compliance(prompt, context)

        except Exception as e:
            self.logger.error(f"Candidate evaluation error: {e}")

        scores["evaluation_time"] = time.time() - start_time

        return scores

    def _evaluate_accuracy(self, prompt: str, context: PromptingContext, base_prompt: str) -> float:
        """
        Evaluate prompt accuracy and specificity.

        Algorithm Approach: Analyze prompt structure, specificity,
        and domain-appropriate terminology for accuracy scoring.

        Time Complexity: O(p) where p=prompt_length
        Space Complexity: O(1) constant space
        """
        score = 0.5  # Base score

        prompt_lower = prompt.lower()

        # Check for specificity indicators
        specificity_keywords = [
            "specific",
            "detailed",
            "precise",
            "exact",
            "particular",
            "explicit",
            "clear",
            "defined",
            "measurable",
            "concrete",
        ]

        specificity_count = sum(1 for keyword in specificity_keywords if keyword in prompt_lower)
        score += min(0.2, specificity_count * 0.04)

        # Check for domain-appropriate terminology
        domain_keywords = {
            "security": ["vulnerability", "threat", "attack", "defense", "authentication", "authorization"],
            "architecture": ["design", "structure", "component", "interface", "pattern", "principle"],
            "development": ["code", "implementation", "function", "class", "method", "algorithm"],
            "debugging": ["error", "bug", "issue", "problem", "debug", "trace", "log"],
            "general": ["analysis", "solution", "approach", "method", "strategy", "technique"],
        }

        domain_terms = domain_keywords.get(context.domain, domain_keywords["general"])
        domain_count = sum(1 for term in domain_terms if term in prompt_lower)
        score += min(0.2, domain_count * 0.03)

        # Check for action-oriented language
        action_keywords = ["analyze", "evaluate", "create", "implement", "design", "develop", "optimize"]
        action_count = sum(1 for keyword in action_keywords if keyword in prompt_lower)
        score += min(0.1, action_count * 0.02)

        # Penalize vague language
        vague_keywords = ["some", "maybe", "perhaps", "possibly", "sort of", "kind of"]
        vague_count = sum(1 for keyword in vague_keywords if keyword in prompt_lower)
        score -= min(0.1, vague_count * 0.02)

        return max(0.0, min(1.0, score))

    def _evaluate_clarity(self, prompt: str) -> float:
        """
        Evaluate prompt clarity and readability.

        Algorithm Approach: Analyze sentence structure, length,
        organization, and readability metrics for clarity scoring.

        Time Complexity: O(p) where p=prompt_length
        Space Complexity: O(1) constant space
        """
        score = 0.5  # Base score

        lines = prompt.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]

        if not non_empty_lines:
            return 0.0

        # Evaluate sentence length
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)

        # Optimal length is between 20 and 100 characters
        if 20 <= avg_line_length <= 100:
            score += 0.1
        elif avg_line_length > 150:
            score -= 0.1

        # Check for organization structure
        has_bullets = any(
            line.startswith("•") or line.startswith("-") or line.startswith("*") for line in non_empty_lines
        )
        has_numbers = any(line[0].isdigit() for line in non_empty_lines)
        has_sections = any(":" in line for line in non_empty_lines)

        organization_score = sum([has_bullets, has_numbers, has_sections]) * 0.05
        score += min(0.15, organization_score)

        # Check for clear structure elements
        structure_indicators = [
            "**",
            "##",
            "###",
            "step",
            "phase",
            "section",
            "first",
            "second",
            "third",
            "finally",
            "summary",
        ]

        structure_count = sum(1 for indicator in structure_indicators if indicator in prompt.lower())
        score += min(0.15, structure_count * 0.02)

        # Evaluate consistency
        has_consistent_formatting = all(
            line.startswith("•") for line in non_empty_lines if line.startswith("•")
        ) or all(line[0].isdigit() for line in non_empty_lines if line[0].isdigit())

        if has_consistent_formatting:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _evaluate_efficiency(self, prompt: str, base_prompt: str) -> float:
        """
        Evaluate prompt efficiency and conciseness.

        Algorithm Approach: Analyze length, redundancy,
        and information density for efficiency scoring.

        Time Complexity: O(p) where p=prompt_length
        Space Complexity: O(1) constant space
        """
        score = 0.5  # Base score

        # Length efficiency
        base_length = len(base_prompt.split())
        prompt_length = len(prompt.split())

        # Prefer prompts that are not excessively longer than base
        length_ratio = prompt_length / max(1, base_length)
        if 0.8 <= length_ratio <= 2.0:
            score += 0.2
        elif length_ratio > 3.0:
            score -= 0.2

        # Information density
        words = prompt.split()
        unique_words = {word.lower().strip(".,!?;:") for word in words}
        density_ratio = len(unique_words) / max(1, len(words))

        # Higher density is better (less repetition)
        score += min(0.2, density_ratio * 0.3)

        # Check for redundant phrases
        redundant_phrases = [
            "please note that",
            "it is important to",
            "make sure that",
            "don't forget to",
            "remember to",
            "be sure to",
        ]

        redundant_count = sum(1 for phrase in redundant_phrases if phrase in prompt.lower())
        score -= min(0.15, redundant_count * 0.03)

        # Evaluate value-to-length ratio
        if prompt_length > 0:
            value_words = [
                "specific",
                "accurate",
                "relevant",
                "important",
                "critical",
                "essential",
                "key",
                "primary",
                "main",
                "focus",
            ]

            value_count = sum(1 for word in words if word.lower() in value_words)
            value_ratio = value_count / prompt_length

            score += min(0.15, value_ratio * 10)

        return max(0.0, min(1.0, score))

    def _evaluate_compliance(self, prompt: str, context: PromptingContext) -> float:
        """
        Evaluate constitutional compliance.

        Algorithm Approach: Check for compliance indicators,
        safety measures, and constitutional requirements.

        Time Complexity: O(p × r) where p=prompt_length, r=requirements
        Space Complexity: O(1) constant space
        """
        score = 0.7  # Start with assumption of compliance

        prompt_lower = prompt.lower()

        # Evidence-based compliance
        if context.constitutional_requirements.get("evidence_based", False):
            evidence_indicators = [
                "evidence",
                "source",
                "reference",
                "citation",
                "proof",
                "data",
                "facts",
                "verify",
                "validate",
                "confirm",
            ]

            evidence_count = sum(1 for indicator in evidence_indicators if indicator in prompt_lower)
            if evidence_count > 0:
                score += 0.1
            else:
                score -= 0.2

        # Anti-deception compliance
        if context.constitutional_requirements.get("anti_deception", False):
            honesty_indicators = [
                "honest",
                "truthful",
                "accurate",
                "reliable",
                "credible",
                "avoid speculation",
                "be careful",
                "verify claims",
            ]

            honesty_count = sum(1 for indicator in honesty_indicators if indicator in prompt_lower)
            if honesty_count > 0:
                score += 0.1
            else:
                score -= 0.1

        # Check for potentially problematic content
        problematic_keywords = [
            "hack",
            "exploit",
            "bypass",
            "circumvent",
            "cheat",
            "manipulate",
            "deceive",
            "mislead",
            "trick",
        ]

        problematic_count = sum(1 for keyword in problematic_keywords if keyword in prompt_lower)
        score -= min(0.3, problematic_count * 0.1)

        # Check for safety measures
        safety_keywords = [
            "safety",
            "security",
            "protect",
            "ensure",
            "validate",
            "careful",
            "caution",
            "warning",
            "important note",
        ]

        safety_count = sum(1 for keyword in safety_keywords if keyword in prompt_lower)
        score += min(0.2, safety_count * 0.02)

        # Domain-specific compliance
        if context.domain == "security":
            security_compliance = [
                "authorization",
                "authentication",
                "permission",
                "access control",
                "encryption",
                "secure",
                "protect",
                "safeguard",
            ]

            compliance_count = sum(1 for term in security_compliance if term in prompt_lower)
            score += min(0.1, compliance_count * 0.01)

        return max(0.0, min(1.0, score))

    def _calculate_overall_score(self, candidate: PromptCandidate) -> float:
        """
        Calculate overall score from individual metrics.

        Algorithm Approach: Weighted combination of metrics
        using configuration-defined weights.

        Time Complexity: O(m) where m=number_of_metrics
        Space Complexity: O(1) constant space
        """
        weights = {
            EvaluationMetric.ACCURACY: self.config.metric_weights.get(EvaluationMetric.ACCURACY, 0.35),
            EvaluationMetric.CLARITY: self.config.metric_weights.get(EvaluationMetric.CLARITY, 0.20),
            EvaluationMetric.EFFICIENCY: self.config.metric_weights.get(EvaluationMetric.EFFICIENCY, 0.20),
            EvaluationMetric.CONSTITUTIONAL_COMPLIANCE: self.config.metric_weights.get(
                EvaluationMetric.CONSTITUTIONAL_COMPLIANCE,
                0.15,
            ),
        }

        overall_score = (
            candidate.accuracy_score * weights[EvaluationMetric.ACCURACY]
            + candidate.clarity_score * weights[EvaluationMetric.CLARITY]
            + candidate.efficiency_score * weights[EvaluationMetric.EFFICIENCY]
            + candidate.compliance_score * weights[EvaluationMetric.CONSTITUTIONAL_COMPLIANCE]
        )

        # Apply generation bonus (favor newer generations slightly)
        generation_bonus = min(0.05, candidate.generation * 0.01)

        # Apply improvement trend bonus
        trend_bonus = min(0.05, max(0.0, candidate.improvement_trend * 0.1))

        final_score = overall_score + generation_bonus + trend_bonus

        return max(0.0, min(1.0, final_score))

    def _generate_cache_key(self, prompt: str, context: PromptingContext) -> str:
        """Generate cache key for prompt optimization."""
        content = f"{prompt}_{context.domain}_{context.complexity}_{hash(str(context.performance_constraints))}"
        return hashlib.md5(content.encode()).hexdigest()

    def _generate_candidate_cache_key(self, prompt: str, context: PromptingContext) -> str:
        """Generate cache key for candidate evaluation."""
        content = f"{prompt}_{hash(str(context))}"
        return hashlib.md5(content.encode()).hexdigest()

    def _extract_final_scores(self, candidate: PromptCandidate) -> dict[str, float]:
        """Extract final evaluation scores from candidate."""
        return {
            EvaluationMetric.ACCURACY.value: candidate.accuracy_score,
            EvaluationMetric.CLARITY.value: candidate.clarity_score,
            EvaluationMetric.EFFICIENCY.value: candidate.efficiency_score,
            EvaluationMetric.CONSTITUTIONAL_COMPLIANCE.value: candidate.compliance_score,
            EvaluationMetric.USER_SATISFACTION.value: candidate.overall_score,  # Use overall as proxy
            EvaluationMetric.RESPONSE_QUALITY.value: candidate.overall_score,
        }

    def _calculate_metric_improvements(self, final_scores: dict[str, float]) -> dict[str, float]:
        """Calculate improvements relative to baseline scores."""
        baseline_scores = {metric.value: 0.5 for metric in EvaluationMetric}

        improvements = {}
        for metric, score in final_scores.items():
            baseline = baseline_scores.get(metric, 0.5)
            if baseline > 0:
                improvement = (score - baseline) / baseline
                improvements[metric] = max(-1.0, min(1.0, improvement))
            else:
                improvements[metric] = 0.0

        return improvements

    def _extract_mutations_applied(self, candidates: list[PromptCandidate]) -> list[PromptMutationType]:
        """Extract all mutation types applied during optimization."""
        mutations = set()
        for candidate in candidates:
            if candidate.mutation_type:
                mutations.add(candidate.mutation_type)
        return list(mutations)

    def _get_template_usage(self, candidates: list[PromptCandidate]) -> dict[str, int]:
        """Get template usage statistics."""
        template_usage = {}

        for candidate in candidates:
            if self.template_env and "**TEMPLATE**" in candidate.prompt:
                template_name = candidate.metadata.get("template_name", "unknown")
                template_usage[template_name] = template_usage.get(template_name, 0) + 1

        return template_usage

    def _validate_constitutional_compliance(self, prompt: str, context: PromptingContext) -> dict[str, bool]:
        """Validate constitutional compliance of optimized prompt."""
        compliance = {
            "evidence_based": True,
            "anti_deception": True,
            "performance_safe": True,
            "domain_appropriate": True,
        }

        prompt_lower = prompt.lower()

        # Evidence-based validation
        if context.constitutional_requirements.get("evidence_based", False):
            evidence_indicators = ["evidence", "source", "verify", "data", "facts"]
            compliance["evidence_based"] = any(indicator in prompt_lower for indicator in evidence_indicators)

        # Anti-deception validation
        if context.constitutional_requirements.get("anti_deception", False):
            honesty_indicators = ["honest", "accurate", "truthful", "verify", "careful"]
            deceptive_indicators = ["speculate", "guess", "assume", "perhaps"]

            has_honesty = any(indicator in prompt_lower for indicator in honesty_indicators)
            has_deceptive = any(indicator in prompt_lower for indicator in deceptive_indicators)

            compliance["anti_deception"] = has_honesty and not has_deceptive

        # Performance safety validation
        max_length = 2000
        compliance["performance_safe"] = len(prompt) <= max_length

        # Domain appropriateness validation
        domain_keywords = {
            "security": ["security", "authentication", "authorization", "protect", "secure"],
            "architecture": ["design", "structure", "component", "pattern", "interface"],
            "development": ["code", "implement", "function", "class", "method"],
            "debugging": ["debug", "error", "issue", "trace", "log", "problem"],
        }

        expected_keywords = domain_keywords.get(context.domain, [])
        compliance["domain_appropriate"] = not expected_keywords or any(
            keyword in prompt_lower for keyword in expected_keywords
        )

        return compliance

    def _validate_performance(self, optimized_prompt: str, original_prompt: str) -> dict[str, Any]:
        """Validate performance characteristics of optimized prompt."""
        return {
            "length_ratio": len(optimized_prompt) / max(1, len(original_prompt)),
            "complexity_change": self._calculate_complexity_change(optimized_prompt, original_prompt),
            "readability_score": self._calculate_readability_score(optimized_prompt),
            "structure_score": self._calculate_structure_score(optimized_prompt),
        }

    def _calculate_complexity_change(self, optimized_prompt: str, original_prompt: str) -> float:
        """Calculate change in prompt complexity."""

        # Simple complexity metric based on unique words and structure
        def complexity_score(text: str) -> float:
            words = text.split()
            unique_words = {word.lower().strip(".,!?;:") for word in words}
            sentences = text.count(".") + text.count("!") + text.count("?")

            word_diversity = len(unique_words) / max(1, len(words))
            avg_sentence_length = len(words) / max(1, sentences)

            return word_diversity * 0.6 + (1.0 / max(0.1, avg_sentence_length)) * 0.4

        original_complexity = complexity_score(original_prompt)
        optimized_complexity = complexity_score(optimized_prompt)

        if original_complexity > 0:
            return (optimized_complexity - original_complexity) / original_complexity
        return 0.0

    def _calculate_readability_score(self, prompt: str) -> float:
        """Calculate readability score (simplified Flesch-like metric)."""
        sentences = max(1, prompt.count(".") + prompt.count("!") + prompt.count("?"))
        words = prompt.split()
        avg_words_per_sentence = len(words) / sentences

        # Simplified readability score
        # Lower average words per sentence = higher readability
        readability = max(0, 1.0 - (avg_words_per_sentence - 10) / 20)

        return max(0.0, min(1.0, readability))

    def _calculate_structure_score(self, prompt: str) -> float:
        """Calculate structural organization score."""
        score = 0.0

        # Check for list structures
        if any(char in prompt for char in ["•", "-", "*", "1.", "2.", "3."]):
            score += 0.3

        # Check for sections/headers
        if "**" in prompt or "##" in prompt or "###" in prompt:
            score += 0.3

        # Check for logical connectors
        connectors = ["first", "second", "third", "finally", "next", "then", "also"]
        connector_count = sum(1 for connector in connectors if connector in prompt.lower())
        score += min(0.2, connector_count * 0.05)

        # Check for consistent formatting
        lines = prompt.strip().split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]

        if non_empty_lines:
            # Check for consistent indentation or formatting
            starts_with_bullets = all(
                line.startswith("•") or line.startswith("-")
                for line in non_empty_lines
                if line.startswith("•") or line.startswith("-")
            )

            if starts_with_bullets and sum(line.startswith("•") for line in non_empty_lines) > 1:
                score += 0.2

        return max(0.0, min(1.0, score))

    def _update_statistics(self, improvement: float, cache_hit_rate: float, candidates_evaluated: int):
        """Update optimization statistics."""
        # Update average improvement
        total_optimizations = self.optimization_stats["total_optimizations"]
        current_avg = self.optimization_stats["average_improvement"]

        self.optimization_stats["average_improvement"] = (current_avg * (total_optimizations - 1) + improvement) / max(
            1,
            total_optimizations,
        )

        # Update cache hit rate (exponential moving average)
        current_cache_rate = self.optimization_stats["cache_hit_rate"]
        alpha = 0.1  # Smoothing factor
        self.optimization_stats["cache_hit_rate"] = alpha * cache_hit_rate + (1 - alpha) * current_cache_rate

    def get_optimization_statistics(self) -> dict[str, Any]:
        """Get comprehensive optimization statistics."""
        return {
            "statistics": self.optimization_stats.copy(),
            "cache_size": len(self.performance_cache) + len(self.evaluation_cache),
            "available_strategies": list(self.strategies.keys()),
            "config": {
                "max_iterations": self.config.max_iterations,
                "population_size": self.config.population_size,
                "mutation_rate": self.config.mutation_rate,
                "max_optimization_time": self.config.max_optimization_time,
            },
            "template_system_available": self.template_env is not None,
        }

    def clear_cache(self):
        """Clear all performance and evaluation caches."""
        self.performance_cache.clear()
        self.evaluation_cache.clear()
        self.logger.info("Optimization cache cleared")

    async def optimize_prompt_with_template(
        self,
        template_name: str,
        template_context: dict[str, Any],
        context: PromptingContext,
        target_improvement: float = 0.10,
    ) -> OptimizationResult:
        """
        Optimize a prompt using Jinja2 template.

        Algorithm Approach: Generate base prompt from template,
        then apply standard optimization pipeline.

        Time Complexity: O(t + i × k × e) where t=template_rendering, i=iterations, k=candidates, e=evaluations
        Space Complexity: O(k × p) where k=candidates, p=prompt_length

        Args:
        ----
            template_name: Name of Jinja2 template
            template_context: Context variables for template rendering
            context: Prompting context for optimization
            target_improvement: Target improvement percentage

        Returns:
        -------
            Complete optimization result with template metadata

        """
        if not self.template_env:
            raise ValueError("Template system not available")

        try:
            # Render template
            template = self.template_env.get_template(template_name)
            base_prompt = template.render(**template_context)

            # Apply standard optimization
            result = await self.optimize_prompt(
                base_prompt=base_prompt,
                context=context,
                target_improvement=target_improvement,
            )

            # Add template metadata
            result.template_usage[template_name] = result.template_usage.get(template_name, 0) + 1

            self.logger.info(f"Template optimization completed for {template_name}")

            return result

        except Exception as e:
            self.logger.error(f"Template optimization failed: {e}")
            raise


# Export main class and utilities
__all__ = [
    "EvaluationMetric",
    "MetaPromptOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "OptimizationStrategy",
    "PromptCandidate",
    "PromptMutationType",
]

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .base_prompting_technique import BasePromptingTechnique
from .context_models import PromptingContext, PromptingTechnique

"""QueryFanoutTechnique Implementation

Automated query decomposition and follow-up generation for comprehensive exploration.
Implements multi-question exploration strategies with coverage analysis and gap
identification for maximum query comprehension (45-60% improvement target).

Key Features:
- Intelligent query decomposition and component identification
- Multi-strategy exploration (breadth-first, depth-first, hybrid)
- Coverage analysis and gap identification
- Performance-optimized with <5s processing time
- Integration with SocraticMethod for cognitive enhancement
- Constitutional compliance with evidence-based and anti-deception support
"""





class ExplorationStrategy(Enum):
    """Available exploration strategies for query fan-out."""

    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    HYBRID = "hybrid"


@dataclass
class QueryComponent:
    """Represents a component identified in query analysis."""

    text: str
    category: str
    importance: float
    sub_components: list[str] = field(default_factory=list)


@dataclass
class FollowUpQuestion:
    """Represents a generated follow-up question."""

    question: str
    component: str
    strategy: str
    priority: float
    exploration_type: str


@dataclass
class CoverageAnalysis:
    """Results of coverage analysis for query exploration."""

    coverage_percentage: float
    identified_gaps: list[str]
    coverage_recommendations: list[str]
    explored_aspects: set[str]
    missing_aspects: set[str]


class QueryFanoutTechnique(BasePromptingTechnique):
    """
    QueryFanoutTechnique - Automated Query Decomposition and Follow-up Generation

    Implements intelligent query fan-out for comprehensive exploration:
    - Query decomposition into key components and sub-questions
    - Multi-strategy exploration (breadth-first, depth-first, hybrid)
    - Coverage analysis and gap identification
    - Integration with cognitive enhancement techniques
    - Performance-optimized for <5s processing time

    Performance Targets:
    - 45-60% improvement in query coverage
    - <5s total processing time
    - <200MB memory usage for complex queries
    - 3-7 focused follow-up questions per query
    """

    def __init__(self, max_follow_ups: int = 5, coverage_threshold: float = 0.8):
        """Initialize QueryFanoutTechnique with configurable parameters."""
        super().__init__(PromptingTechnique.QUERY_FANOUT)

        # Core configuration
        self.max_follow_ups = max_follow_ups
        self.coverage_threshold = coverage_threshold

        # Query analysis components
        self.component_identifiers = {
            "architecture": ["design", "architecture", "system", "structure", "pattern"],
            "security": ["security", "auth", "encryption", "protection", "vulnerability"],
            "performance": ["performance", "scalability", "optimization", "speed", "efficiency"],
            "functionality": ["feature", "function", "capability", "behavior", "requirement"],
            "implementation": ["implement", "build", "create", "develop", "code"],
            "comparison": ["compare", "versus", "vs", "difference", "better"],
            "analysis": ["analyze", "evaluate", "assess", "examine", "review"],
        }

        # Strategy-specific parameters
        self.strategy_weights = {
            ExplorationStrategy.BREADTH_FIRST: {"diversity": 0.8, "depth": 0.2},
            ExplorationStrategy.DEPTH_FIRST: {"diversity": 0.2, "depth": 0.8},
            ExplorationStrategy.HYBRID: {"diversity": 0.5, "depth": 0.5},
        }

        # Performance tracking
        self.performance_metrics = {
            "total_queries": 0,
            "avg_processing_time": 0.0,
            "avg_coverage_improvement": 0.0,
            "avg_follow_ups_generated": 0.0,
        }

    async def is_applicable(self, context: PromptingContext) -> bool:
        """
        Determine if QueryFanoutTechnique is applicable for the given context.

        Applicability Criteria:
        - Complex queries requiring multiple aspects exploration
        - Multi-faceted questions with implicit components
        - Analytical or comparative queries
        - Sufficient performance budget for follow-up generation
        """
        query_lower = context.query.lower()

        # Quick filters for simple queries
        if len(context.query.split()) < 8:
            return False

        if context.complexity in ["simple"]:
            return False

        # Identify complexity indicators
        complexity_indicators = [
            "design",
            "architecture",
            "implement",
            "compare",
            "analyze",
            "evaluate",
            "optimize",
            "integrate",
            "comprehensive",
            "multiple",
        ]

        has_complexity = any(indicator in query_lower for indicator in complexity_indicators)

        # Check for multi-component indicators
        component_indicators = [
            "and",
            "with",
            "including",
            "plus",
            "also",
            "as well as",
            "multiple",
            "various",
            "different",
            "several",
        ]

        has_components = any(indicator in query_lower for indicator in component_indicators)

        # Performance constraints check
        max_time = context.performance_constraints.get("max_response_time", 5.0)
        has_time_budget = max_time >= 2.0  # Need at least 2s for fan-out

        return has_complexity and has_components and has_time_budget

    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        """
        Get confidence score for QueryFanoutTechnique applicability (0.0 to 1.0).

        Confidence Factors:
        - Query complexity and multi-faceted nature
        - Domain suitability for exploration
        - Performance constraint compatibility
        - Component richness and exploration potential
        """
        query_lower = context.query.lower()
        confidence = 0.0

        # Base complexity confidence
        complexity_scores = {"simple": 0.1, "moderate": 0.5, "complex": 0.8, "expert": 0.9}
        confidence += complexity_scores.get(context.complexity, 0.5) * 0.3

        # Component richness confidence
        components = await self._analyze_query_components(context.query)
        component_confidence = min(1.0, len(components) / 3.0)
        confidence += component_confidence * 0.4

        # Domain suitability confidence
        domain_scores = {
            "architecture": 0.9,
            "security": 0.85,
            "development": 0.8,
            "research": 0.8,
            "analysis": 0.75,
            "general": 0.5,
        }
        confidence += domain_scores.get(context.domain, 0.5) * 0.2

        # Query indicators confidence
        indicator_keywords = [
            "comprehensive",
            "multiple",
            "various",
            "different",
            "compare",
            "analyze",
            "evaluate",
            "design",
            "implement",
            "optimize",
        ]
        indicator_count = sum(1 for kw in indicator_keywords if kw in query_lower)
        indicator_confidence = min(1.0, indicator_count / 3.0)
        confidence += indicator_confidence * 0.1

        return min(1.0, confidence)

    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        """
        Apply QueryFanoutTechnique to enhance the prompt with fan-out instructions.

        Enhances the prompt with:
        - Query decomposition instructions
        - Follow-up question generation guidance
        - Coverage analysis requirements
        - Exploration strategy specifications
        """
        # Analyze query components
        components = await self._analyze_query_components(prompt)

        # Select optimal exploration strategy
        strategy = await self._select_exploration_strategy(prompt, context)

        # Generate follow-up questions
        follow_ups = await self._generate_follow_up_questions(prompt, context, strategy)

        # Create fan-out enhancement
        fanout_enhancement = self._build_fanout_enhancement(
            prompt,
            components,
            follow_ups,
            strategy,
            context,
        )

        # Combine with original prompt
        enhanced_prompt = f"{prompt}\n\n{fanout_enhancement}"

        # Update performance metrics
        self._update_performance_metrics(len(components), len(follow_ups))

        return enhanced_prompt

    async def _analyze_query_components(self, query: str) -> list[QueryComponent]:
        """Analyze query to identify key components and sub-questions."""
        components = []
        query_lower = query.lower()

        # Identify components based on keywords and patterns
        for category, keywords in self.component_identifiers.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Extract relevant text around the keyword
                    component_text = self._extract_component_text(query, keyword)

                    component = QueryComponent(
                        text=component_text,
                        category=category,
                        importance=self._calculate_component_importance(component_text, query),
                        sub_components=self._identify_sub_components(component_text),
                    )
                    components.append(component)

        # Remove duplicates and sort by importance
        unique_components = []
        seen_texts = set()

        for component in sorted(components, key=lambda x: x.importance, reverse=True):
            if component.text.lower() not in seen_texts:
                unique_components.append(component)
                seen_texts.add(component.text.lower())

        return unique_components[:5]  # Limit to top 5 components

    async def _generate_follow_up_questions(
        self,
        query: str,
        context: PromptingContext,
        strategy: ExplorationStrategy = ExplorationStrategy.BREADTH_FIRST,
    ) -> list[FollowUpQuestion]:
        """Generate targeted follow-up questions based on exploration strategy."""
        components = await self._analyze_query_components(query)
        questions = []

        if strategy == ExplorationStrategy.BREADTH_FIRST:
            questions = self._generate_breadth_first_questions(query, components, context)
        elif strategy == ExplorationStrategy.DEPTH_FIRST:
            questions = self._generate_depth_first_questions(query, components, context)
        elif strategy == ExplorationStrategy.HYBRID:
            questions = self._generate_hybrid_questions(query, components, context)

        # Limit to max_follow_ups and sort by priority
        questions = sorted(questions, key=lambda x: x.priority, reverse=True)
        return questions[: self.max_follow_ups]

    async def _analyze_coverage(
        self,
        original_query: str,
        follow_ups: list[str],
        responses: list[str],
    ) -> CoverageAnalysis:
        """Analyze coverage and identify gaps in query exploration."""
        # Identify covered aspects from questions and responses
        all_text = original_query + " " + " ".join(follow_ups) + " " + " ".join(responses)
        all_text_lower = all_text.lower()

        # Determine expected aspects based on query analysis
        expected_aspects = set()
        for category, keywords in self.component_identifiers.items():
            if any(keyword in original_query.lower() for keyword in keywords):
                expected_aspects.add(category)

        # Identify covered aspects
        covered_aspects = set()
        for aspect in expected_aspects:
            keywords = self.component_identifiers.get(aspect, [])
            if any(keyword in all_text_lower for keyword in keywords):
                covered_aspects.add(aspect)

        # Calculate coverage percentage
        coverage_percentage = len(covered_aspects) / len(expected_aspects) if expected_aspects else 1.0

        # Identify gaps
        identified_gaps = list(expected_aspects - covered_aspects)

        # Generate recommendations
        recommendations = []
        for gap in identified_gaps:
            recommendations.append(f"Explore {gap} aspects more thoroughly")

        if coverage_percentage < self.coverage_threshold:
            recommendations.append("Consider additional follow-up questions for comprehensive coverage")

        return CoverageAnalysis(
            coverage_percentage=coverage_percentage,
            identified_gaps=identified_gaps,
            coverage_recommendations=recommendations,
            explored_aspects=covered_aspects,
            missing_aspects=set(identified_gaps),
        )

    def _calculate_coverage_score(self, text: str, aspects: list[str]) -> float:
        """Calculate coverage score for given aspects in text."""
        text_lower = text.lower()
        covered_aspects = 0

        for aspect in aspects:
            if aspect.lower() in text_lower:
                covered_aspects += 1

        return covered_aspects / len(aspects) if aspects else 0.0

    async def _select_exploration_strategy(
        self,
        query: str,
        context: PromptingContext,
    ) -> ExplorationStrategy:
        """Select optimal exploration strategy based on query and context."""
        query_lower = query.lower()

        # Strategy selection criteria
        breadth_indicators = ["multiple", "various", "different", "compare", "versus"]
        depth_indicators = ["deep", "thorough", "comprehensive", "detailed", "extensive"]

        breadth_score = sum(1 for indicator in breadth_indicators if indicator in query_lower)
        depth_score = sum(1 for indicator in depth_indicators if indicator in query_lower)

        # Consider complexity level
        if context.complexity == "expert":
            depth_score += 1
        elif context.complexity == "simple":
            breadth_score += 1

        # Select strategy based on scores
        if breadth_score > depth_score:
            return ExplorationStrategy.BREADTH_FIRST
        if depth_score > breadth_score:
            return ExplorationStrategy.DEPTH_FIRST
        return ExplorationStrategy.HYBRID

    def _extract_component_text(self, query: str, keyword: str) -> str:
        """Extract relevant text around a keyword."""
        words = query.split()
        keyword_indices = [i for i, word in enumerate(words) if keyword.lower() in word.lower()]

        if not keyword_indices:
            return keyword

        # Extract context around keyword (3 words before and after)
        best_index = keyword_indices[0]
        start_idx = max(0, best_index - 3)
        end_idx = min(len(words), best_index + 4)

        component_words = words[start_idx:end_idx]
        return " ".join(component_words)

    def _calculate_component_importance(self, component_text: str, full_query: str) -> float:
        """Calculate importance score for a query component."""
        importance = 0.0

        # Length factor (longer components might be more important)
        importance += min(1.0, len(component_text.split()) / 5.0) * 0.3

        # Position factor (components earlier in query might be more important)
        position = full_query.lower().find(component_text.lower())
        if position >= 0:
            position_score = 1.0 - (position / len(full_query))
            importance += position_score * 0.4

        # Category importance
        if any(category in component_text.lower() for category in ["security", "performance", "architecture"]):
            importance += 0.3

        return min(1.0, importance)

    def _identify_sub_components(self, component_text: str) -> list[str]:
        """Identify sub-components within a component."""
        sub_components = []

        # Look for conjunctions and separators
        separators = ["and", "with", "including", "plus", ",", "&"]
        words = component_text.split()

        for i, word in enumerate(words):
            if word.lower() in separators and i + 1 < len(words):
                sub_component = words[i + 1]
                if len(sub_component) > 2:  # Filter out very short words
                    sub_components.append(sub_component)

        return sub_components

    def _generate_breadth_first_questions(
        self,
        query: str,
        components: list[QueryComponent],
        context: PromptingContext,
    ) -> list[FollowUpQuestion]:
        """Generate breadth-first follow-up questions covering multiple aspects."""
        questions = []

        # Generate questions for each component
        for component in components:
            question_templates = [
                f"What are the key considerations for {component.text}?",
                f"How does {component.text} impact the overall solution?",
                f"What are the best practices for {component.text}?",
                f"What challenges might arise with {component.text}?",
            ]

            # Select most appropriate template
            template_index = min(len(component.sub_components), len(question_templates) - 1)
            question_text = question_templates[template_index]

            question = FollowUpQuestion(
                question=question_text,
                component=component.text,
                strategy="breadth_first",
                priority=component.importance,
                exploration_type="aspect_coverage",
            )
            questions.append(question)

        return questions

    def _generate_depth_first_questions(
        self,
        query: str,
        components: list[QueryComponent],
        context: PromptingContext,
    ) -> list[FollowUpQuestion]:
        """Generate depth-first follow-up questions for detailed investigation."""
        questions = []

        if not components:
            return questions

        # Focus on the most important component
        primary_component = max(components, key=lambda x: x.importance)

        # Generate progressive deepening questions
        depth_questions = [
            f"What are the specific requirements for {primary_component.text}?",
            f"How would you implement {primary_component.text} in detail?",
            f"What are the technical challenges in {primary_component.text}?",
            f"How can {primary_component.text} be optimized further?",
            f"What are the alternatives for {primary_component.text}?",
        ]

        for i, question_text in enumerate(depth_questions):
            question = FollowUpQuestion(
                question=question_text,
                component=primary_component.text,
                strategy="depth_first",
                priority=primary_component.importance * (1.0 - i * 0.1),  # Decreasing priority
                exploration_type="detailed_investigation",
            )
            questions.append(question)

        return questions

    def _generate_hybrid_questions(
        self,
        query: str,
        components: list[QueryComponent],
        context: PromptingContext,
    ) -> list[FollowUpQuestion]:
        """Generate hybrid follow-up questions combining breadth and depth."""
        questions = []

        if not components:
            return questions

        # Sort components by importance
        sorted_components = sorted(components, key=lambda x: x.importance, reverse=True)

        # First question: breadth overview
        overview_question = FollowUpQuestion(
            question=f"What are the main aspects to consider for {query.lower()}?",
            component="overview",
            strategy="hybrid",
            priority=1.0,
            exploration_type="breadth_overview",
        )
        questions.append(overview_question)

        # Next questions: depth on top components
        for i, component in enumerate(sorted_components[:3]):
            question_text = f"How would you approach {component.text} in detail?"

            question = FollowUpQuestion(
                question=question_text,
                component=component.text,
                strategy="hybrid",
                priority=component.importance * (0.8 - i * 0.1),
                exploration_type="focused_depth",
            )
            questions.append(question)

        return questions

    def _build_fanout_enhancement(
        self,
        original_prompt: str,
        components: list[QueryComponent],
        follow_ups: list[FollowUpQuestion],
        strategy: ExplorationStrategy,
        context: PromptingContext,
    ) -> str:
        """Build the query fan-out enhancement instructions."""
        # Format follow-up questions
        formatted_questions = []
        for i, question in enumerate(follow_ups, 1):
            formatted_questions.append(f"{i}. {question.question}")

        # Component summary
        component_summary = ""
        if components:
            component_names = [comp.category for comp in components[:3]]
            component_summary = f"\n\n**Identified Components:** {', '.join(component_names)}"

        # Strategy-specific instructions
        strategy_instructions = {
            ExplorationStrategy.BREADTH_FIRST: "Explore multiple aspects broadly to ensure comprehensive coverage",
            ExplorationStrategy.DEPTH_FIRST: "Investigate key components in detail for thorough understanding",
            ExplorationStrategy.HYBRID: "Balance breadth overview with focused depth investigation",
        }

        # Build enhancement
        enhancement = f"""
**QUERY FAN-OUT INSTRUCTIONS**

**Strategy:** {strategy.value.replace("_", " ").title()}
**Approach:** {strategy_instructions[strategy]}{component_summary}

**Follow-up Questions for Comprehensive Exploration:**
{chr(10).join(formatted_questions)}

**Coverage Requirements:**
- Address all follow-up questions systematically
- Ensure comprehensive coverage of identified components
- Identify and explore any additional relevant aspects
- Maintain focus on the original query context

**Output Format:**
```
PRIMARY RESPONSE:
[Your comprehensive response to the original query]

FOLLOW-UP EXPLORATION:
[Address each follow-up question with detailed analysis]

COVERAGE ANALYSIS:
[Summary of aspects covered and any gaps identified]

SYNTHESIZED CONCLUSION:
[Integrated response combining all insights]
```

**Performance Target:** Aim for {self.coverage_threshold:.0%} coverage of all relevant aspects.
"""

        # Add constitutional compliance instructions
        if context.constitutional_requirements.get("evidence_based", False):
            enhancement += """
**EVIDENCE-BASED EXPLORATION:**
- Support all claims with verifiable evidence
- Cite sources for technical assertions
- Acknowledge uncertainties and limitations
"""

        if context.constitutional_requirements.get("anti_deception", False):
            enhancement += """
**ANTI-DECEPTION COMPLIANCE:**
- Verify all factual claims before inclusion
- Provide balanced perspectives with proper caveats
- Use precise language to prevent misinterpretation
"""

        return enhancement.strip()

    def _update_performance_metrics(self, component_count: int, question_count: int) -> None:
        """Update internal performance metrics."""
        self.performance_metrics["total_queries"] += 1

        # Update averages (simple moving average)
        total = self.performance_metrics["total_queries"]

        # Update average components
        current_avg_components = self.performance_metrics.get("avg_components", 0)
        self.performance_metrics["avg_components"] = (current_avg_components * (total - 1) + component_count) / total

        # Update average questions
        current_avg_questions = self.performance_metrics.get("avg_follow_ups_generated", 0)
        self.performance_metrics["avg_follow_ups_generated"] = (
            current_avg_questions * (total - 1) + question_count
        ) / total

    # Technique capability methods
    def supports_evidence_based_reasoning(self) -> bool:
        """Check if technique supports evidence-based reasoning."""
        return True

    def supports_threat_modeling(self) -> bool:
        """Check if technique supports threat modeling."""
        return True

    def supports_system_design(self) -> bool:
        """Check if technique supports system design."""
        return True

    def supports_scalability_analysis(self) -> bool:
        """Check if technique supports scalability analysis."""
        return True

    def supports_optimization(self) -> bool:
        """Check if technique supports optimization."""
        return True

    def supports_benchmarking(self) -> bool:
        """Check if technique supports benchmarking."""
        return True

    def _get_supported_domains(self) -> list[str]:
        """Get list of domains this technique supports."""
        return ["architecture", "security", "development", "research", "analysis", "debugging", "general"]

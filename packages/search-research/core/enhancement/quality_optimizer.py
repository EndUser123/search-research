"""
Quality Predictor and Cost-Benefit Optimizer for Research Methodology Selection
Ensures optimal balance between research quality and resource efficiency
"""

from dataclasses import dataclass

from .enhanced_dependency_analyzer import QueryDependencies, ResearchDepth
from .mode_relationship_mapper import ModeCombination, ResearchMode


@dataclass
class OptimizationResult:
    """Result of cost-benefit optimization"""
    recommended_combination: ModeCombination
    alternatives: list[ModeCombination]
    optimization_reasoning: str
    budget_usage: float
    quality_vs_cost_tradeoff: str

class QualityPredictor:
    """Predicts research quality for different methodology combinations"""

    def __init__(self) -> None:
        # Weight factors for different quality aspects
        self.quality_weights = {
            "relevance": 0.35,      # How relevant modes are to query needs
            "completeness": 0.25,   # How completely modes cover all aspects
            "authority": 0.20,      # Authority and reliability of sources
            "freshness": 0.10,      # Recency and relevance of information
            "efficiency": 0.10,     # How efficiently modes work together
        }

        # Mode authority scores (how reliable/authoritative sources are)
        self.mode_authority_scores = {
            ResearchMode.OCTOCODE: 0.85,    # GitHub repos are authoritative for code
            ResearchMode.WEB: 0.70,         # Variable authority on web
            ResearchMode.MULTI_MODEL: 0.75, # Multiple AI perspectives
            ResearchMode.COGNITIVE: 0.90,   # Deep analysis is highly authoritative
        }

        # Mode freshness scores (how current information tends to be)
        self.mode_freshness_scores = {
            ResearchMode.OCTOCODE: 0.80,    # GitHub tends to be current
            ResearchMode.WEB: 0.85,         # Web can be very current
            ResearchMode.MULTI_MODEL: 0.65, # AI models have knowledge cutoffs
            ResearchMode.COGNITIVE: 0.70,   # Analysis may not reflect latest trends
        }

        # Domain-specific quality adjustments
        self.domain_quality_adjustments = {
            "technical": {
                ResearchMode.OCTOCODE: 0.10,  # Bonus for technical queries
                ResearchMode.COGNITIVE: 0.05,
            },
            "academic": {
                ResearchMode.WEB: 0.15,      # Bonus for academic queries
                ResearchMode.MULTI_MODEL: 0.05,
            },
            "analysis": {
                ResearchMode.MULTI_MODEL: 0.10,  # Bonus for analysis queries
                ResearchMode.COGNITIVE: 0.15,
            },
            "implementation": {
                ResearchMode.OCTOCODE: 0.15,  # Bonus for implementation queries
                ResearchMode.WEB: 0.05,
            }
        }

    def predict_combination_quality(self, combination: ModeCombination,
                                   dependencies: QueryDependencies,
                                   domain: str | None = None) -> float:
        """Predict overall quality of a methodology combination"""

        if not combination.modes:
            return 0.0

        # Calculate individual quality aspects
        relevance_score = self._calculate_relevance(combination, dependencies)
        completeness_score = self._calculate_completeness(combination, dependencies)
        authority_score = self._calculate_authority(combination)
        freshness_score = self._calculate_freshness(combination)
        efficiency_score = self._calculate_efficiency(combination, dependencies)

        # Apply domain-specific adjustments
        if domain:
            relevance_score, completeness_score, authority_score = self._apply_domain_adjustments(
                combination, domain, relevance_score, completeness_score, authority_score
            )

        # Weighted combination of all quality aspects
        predicted_quality = (
            relevance_score * self.quality_weights["relevance"] +
            completeness_score * self.quality_weights["completeness"] +
            authority_score * self.quality_weights["authority"] +
            freshness_score * self.quality_weights["freshness"] +
            efficiency_score * self.quality_weights["efficiency"]
        )

        return min(max(predicted_quality, 0.0), 1.0)

    def _calculate_relevance(self, combination: ModeCombination,
                           dependencies: QueryDependencies) -> float:
        """Calculate how relevant the modes are to the dependencies"""
        total_relevance = 0.0
        covered_dependencies = 0
        total_dependencies = 0

        # Map dependencies to relevant modes
        dependency_relevance_map = {
            ("code", ResearchMode.OCTOCODE): 0.9,
            ("code", ResearchMode.WEB): 0.6,
            ("github", ResearchMode.OCTOCODE): 0.95,
            ("github", ResearchMode.WEB): 0.4,
            ("documentation", ResearchMode.WEB): 0.9,
            ("documentation", ResearchMode.OCTOCODE): 0.5,
            ("academic", ResearchMode.WEB): 0.8,
            ("academic", ResearchMode.MULTI_MODEL): 0.3,
            ("ai_perspectives", ResearchMode.MULTI_MODEL): 0.9,
            ("ai_perspectives", ResearchMode.COGNITIVE): 0.7,
            ("tutorials", ResearchMode.WEB): 0.85,
            ("tutorials", ResearchMode.OCTOCODE): 0.7,
        }

        dependency_checks = [
            ("code", dependencies.requires_code),
            ("github", dependencies.requires_github),
            ("documentation", dependencies.requires_documentation),
            ("academic", dependencies.requires_academic),
            ("ai_perspectives", dependencies.requires_ai_perspectives),
            ("tutorials", dependencies.requires_tutorials),
        ]

        for dep_name, is_needed in dependency_checks:
            if is_needed:
                total_dependencies += 1
                max_relevance = 0.0
                for mode in combination.modes:
                    relevance = dependency_relevance_map.get((dep_name, mode), 0.1)
                    max_relevance = max(max_relevance, relevance)

                if max_relevance > 0.3:  # Threshold for considering dependency "covered"
                    total_relevance += max_relevance
                    covered_dependencies += 1

        # Return average relevance, penalizing uncovered dependencies
        avg_relevance = total_relevance / max(total_dependencies, 1)

        # Penalize for missing coverage
        coverage_penalty = (total_dependencies - covered_dependencies) * 0.2
        final_relevance = max(avg_relevance - coverage_penalty, 0.0)

        return min(final_relevance, 1.0)

    def _calculate_completeness(self, combination: ModeCombination,
                              dependencies: QueryDependencies) -> float:
        """Calculate how completely the modes cover all research aspects"""
        if dependencies.research_depth == ResearchDepth.BASIC:
            # For basic research, single mode should be sufficient
            return 0.9 if len(combination.modes) >= 1 else 0.4

        elif dependencies.research_depth == ResearchDepth.INTERMEDIATE:
            # For intermediate research, benefit from multiple modes
            if len(combination.modes) >= 2:
                return 0.9
            elif len(combination.modes) >= 1:
                return 0.6
            else:
                return 0.3

        else:  # ADVANCED
            # For advanced research, need comprehensive coverage
            if len(combination.modes) >= 3:
                return 0.9
            elif len(combination.modes) >= 2:
                return 0.7
            elif len(combination.modes) >= 1:
                return 0.5
            else:
                return 0.2

    def _calculate_authority(self, combination: ModeCombination) -> float:
        """Calculate average authority of the selected modes"""
        if not combination.modes:
            return 0.0

        total_authority = sum(
            self.mode_authority_scores.get(mode, 0.5)
            for mode in combination.modes
        )

        return total_authority / len(combination.modes)

    def _calculate_freshness(self, combination: ModeCombination) -> float:
        """Calculate average freshness of the selected modes"""
        if not combination.modes:
            return 0.0

        total_freshness = sum(
            self.mode_freshness_scores.get(mode, 0.7)
            for mode in combination.modes
        )

        return total_freshness / len(combination.modes)

    def _calculate_efficiency(self, combination: ModeCombination,
                            dependencies: QueryDependencies) -> float:
        """Calculate how efficiently the modes work together"""
        if len(combination.modes) <= 1:
            return 1.0  # Single mode is always efficient

        # Start with base efficiency and reduce for complexity
        base_efficiency = 1.0

        # Penalty for mode count (more modes = more coordination overhead)
        mode_count_penalty = min(len(combination.modes) * 0.05, 0.2)

        # Bonus for complementary modes (low redundancy)
        redundancy_bonus = (1.0 - combination.redundancy_score) * 0.2

        # Bonus for high coverage (efficient use of modes)
        coverage_bonus = combination.coverage_score * 0.1

        efficiency = (
            base_efficiency
            - mode_count_penalty
            + redundancy_bonus
            + coverage_bonus
        )

        return min(max(efficiency, 0.0), 1.0)

    def _apply_domain_adjustments(self, combination: ModeCombination,
                                domain: str, relevance: float,
                                completeness: float, authority: float) -> tuple[float, float, float]:
        """Apply domain-specific quality adjustments"""
        if domain not in self.domain_quality_adjustments:
            return relevance, completeness, authority

        adjustments = self.domain_quality_adjustments[domain]

        for mode in combination.modes:
            bonus = adjustments.get(mode, 0.0)
            authority += bonus * 0.1  # Apply bonus to authority

        return relevance, completeness, min(authority, 1.0)

class CostBenefitOptimizer:
    """Optimizes methodology selection based on cost-benefit analysis"""

    def __init__(self) -> None:
        self.quality_predictor = QualityPredictor()

        # Cost factors (relative to baseline)
        self.cost_factors = {
            ResearchMode.WEB: 1.0,           # Baseline cost
            ResearchMode.OCTOCODE: 1.5,      # GitHub API + web search
            ResearchMode.MULTI_MODEL: 3.0,   # Multiple AI model calls
            ResearchMode.COGNITIVE: 2.5,     # Sequential processing
        }

        # Value factors (relative benefit)
        self.value_factors = {
            ResearchMode.WEB: 1.0,
            ResearchMode.OCTOCODE: 1.8,      # High value for code
            ResearchMode.MULTI_MODEL: 1.5,   # Good value for perspectives
            ResearchMode.COGNITIVE: 2.0,     # High value for deep analysis
        }

    def optimize_for_budget(self, combinations: list[ModeCombination],
                          dependencies: QueryDependencies,
                          budget_limit: float,
                          domain: str | None = None) -> OptimizationResult:
        """Find optimal combination within budget constraints"""

        # Predict quality for all combinations
        scored_combinations = []
        for combination in combinations:
            quality = self.quality_predictor.predict_combination_quality(
                combination, dependencies, domain
            )
            combination.predicted_quality = quality
            scored_combinations.append(combination)

        # Filter combinations within budget
        affordable_combinations = [
            comb for comb in scored_combinations
            if comb.estimated_cost <= budget_limit
        ]

        if not affordable_combinations:
            # No combinations within budget - find best value for money
            return self.optimize_for_value(scored_combinations, budget_limit, dependencies)

        # Sort by quality (descending)
        affordable_combinations.sort(key=lambda x: x.predicted_quality, reverse=True)

        # Select best combination
        best_combination = affordable_combinations[0]

        # Generate alternatives
        alternatives = affordable_combinations[1:3]  # Top 2 alternatives

        return OptimizationResult(
            recommended_combination=best_combination,
            alternatives=alternatives,
            optimization_reasoning=self._generate_reasoning(
                best_combination, affordable_combinations, budget_limit
            ),
            budget_usage=best_combination.estimated_cost / budget_limit,
            quality_vs_cost_tradeoff=self._analyze_tradeoff(best_combination, affordable_combinations)
        )

    def optimize_for_value(self, combinations: list[ModeCombination],
                         budget_limit: float,
                         dependencies: QueryDependencies) -> OptimizationResult:
        """Optimize for best value when budget is exceeded"""

        # Calculate value scores (quality/cost ratio) and store with combinations
        combination_values = []
        for combination in combinations:
            value_score = (
                combination.predicted_quality *
                sum(self.value_factors.get(mode, 1.0) for mode in combination.modes) /
                combination.estimated_cost
            )
            combination_values.append((value_score, combination))

        # Sort by value score
        combination_values.sort(key=lambda x: x[0], reverse=True)
        sorted_combinations = [comb for _, comb in combination_values]

        best_value_combination = sorted_combinations[0]

        # Suggest budget adjustment
        suggested_budget = best_value_combination.estimated_cost * 1.1  # 10% buffer

        return OptimizationResult(
            recommended_combination=best_value_combination,
            alternatives=sorted_combinations[1:3],
            optimization_reasoning=f"Selected for best value. Suggested budget: {suggested_budget:.1f}",
            budget_usage=best_value_combination.estimated_cost / budget_limit,
            quality_vs_cost_tradeoff="High value, exceeds current budget"
        )

    def _generate_reasoning(self, selected: ModeCombination,
                          alternatives: list[ModeCombination],
                          budget_limit: float) -> str:
        """Generate reasoning for the optimization decision"""
        reasoning_parts = []

        reasoning_parts.append(
            f"Selected {len(selected.modes)} mode(s) with predicted quality of {selected.predicted_quality:.2f}"
        )

        if len(alternatives) > 0:
            best_alternative = alternatives[0]
            quality_diff = selected.predicted_quality - best_alternative.predicted_quality
            if quality_diff > 0.05:
                reasoning_parts.append(
                    f"Outperforms next best alternative by {quality_diff:.2f} quality points"
                )

        budget_efficiency = selected.estimated_cost / budget_limit
        if budget_efficiency < 0.7:
            reasoning_parts.append("Uses budget efficiently with room to spare")
        elif budget_efficiency < 0.9:
            reasoning_parts.append("Makes good use of available budget")
        else:
            reasoning_parts.append("Maximizes use of available budget")

        return ". ".join(reasoning_parts)

    def _analyze_tradeoff(self, selected: ModeCombination,
                        alternatives: list[ModeCombination]) -> str:
        """Analyze the quality vs cost tradeoff"""
        if not alternatives:
            return "No alternatives available for comparison"

        # Calculate average quality and cost of alternatives
        avg_alt_quality = sum(alt.predicted_quality for alt in alternatives) / len(alternatives)
        avg_alt_cost = sum(alt.estimated_cost for alt in alternatives) / len(alternatives)

        quality_diff = selected.predicted_quality - avg_alt_quality
        cost_diff = selected.estimated_cost - avg_alt_cost

        if quality_diff > 0.1 and cost_diff <= 0:
            return "Higher quality at lower cost - excellent value"
        elif quality_diff > 0.1 and cost_diff > 0:
            return f"Higher quality (+{quality_diff:.2f}) but higher cost (+{cost_diff:.1f}x)"
        elif quality_diff <= 0.05 and cost_diff < 0:
            return "Similar quality at lower cost - efficient choice"
        else:
            return "Balanced quality and cost tradeoff"

# Test cases
if __name__ == "__main__":
    from .enhanced_dependency_analyzer import SimplifiedDependencyAnalyzer
    from .mode_relationship_mapper import ModeCombination, ModeRelationshipMapper

    # Initialize components
    analyzer = SimplifiedDependencyAnalyzer()
    mapper = ModeRelationshipMapper()
    quality_predictor = QualityPredictor()
    optimizer = CostBenefitOptimizer()

    # Test scenarios
    test_cases = [
        {
            "query": "react hooks implementation example",
            "budget": 2.0,
            "domain": "technical"
        },
        {
            "query": "enterprise microservices security patterns comparison",
            "budget": 5.0,
            "domain": "analysis"
        },
        {
            "query": "academic papers on machine learning ethics",
            "budget": 2.5,
            "domain": "academic"
        }
    ]

    print("=== Quality Prediction and Cost Optimization Test Cases ===")
    for test_case in test_cases:
        query: str = test_case["query"]  # type: ignore[assignment]
        budget: float = test_case["budget"]  # type: ignore[assignment]
        domain: str = test_case["domain"]  # type: ignore[assignment]

        # Analyze dependencies
        deps = analyzer.analyze_dependencies(query)

        # Get candidate combinations
        candidate_modes = mapper._get_candidate_modes(deps)  # type: ignore[attr-defined]
        combinations = mapper._generate_combinations(candidate_modes, deps)  # type: ignore[attr-defined]

        # Score combinations
        scored_combinations = []
        for combo_modes in combinations:
            # Create a ModeCombination object
            temp_combination = ModeCombination(
                modes=combo_modes,
                predicted_quality=0.0,
                estimated_cost=sum(optimizer.cost_factors.get(mode, 1.0) for mode in combo_modes),
                redundancy_score=0.0,
                coverage_score=0.0
            )

            # Calculate coverage and redundancy for completeness
            temp_combination.coverage_score = mapper._calculate_coverage_score(combo_modes, deps)  # type: ignore[attr-defined]
            temp_combination.redundancy_score = mapper._calculate_redundancy_score(combo_modes)  # type: ignore[attr-defined]

            scored_combinations.append(temp_combination)

        # Optimize
        result = optimizer.optimize_for_budget(scored_combinations, deps, budget, domain)

        print(f"\nQuery: {query}")
        print(f"Domain: {domain}, Budget: {budget}")
        print(f"Recommended: {', '.join([m.value for m in result.recommended_combination.modes])}")
        print(f"Predicted Quality: {result.recommended_combination.predicted_quality:.2f}")
        print(f"Cost: {result.recommended_combination.estimated_cost:.1f}x")
        print(f"Budget Usage: {result.budget_usage:.1%}")
        print(f"Reasoning: {result.optimization_reasoning}")

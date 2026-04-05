"""
Mode Relationship Mapper for Research Methodology Selection
Intelligent selection and optimization of research mode combinations
"""

from dataclasses import dataclass
from enum import Enum

from .enhanced_dependency_analyzer import QueryDependencies, ResearchDepth


class ResearchMode(Enum):
    OCTOCODE = "octocode"
    WEB = "web"
    MULTI_MODEL = "multi-model"
    COGNITIVE = "cognitive-enhanced"

@dataclass
class ModeCombination:
    """Represents a combination of research modes with metadata"""
    modes: list[ResearchMode]
    predicted_quality: float
    estimated_cost: float
    redundancy_score: float
    coverage_score: float

class ModeRelationshipMapper:
    """Maps relationships between research modes and optimizes combinations"""

    def __init__(self):
        # Define primary strengths of each mode
        self.mode_strengths = {
            ResearchMode.OCTOCODE: {
                "primary": ["code_examples", "github_repos", "implementation", "source_code"],
                "secondary": ["tutorials", "discussions", "community_answers"],
                "weak": ["academic_papers", "formal_analysis"],
                "unique_value": 4  # High unique value for code
            },
            ResearchMode.WEB: {
                "primary": ["documentation", "tutorials", "news", "articles", "blogs"],
                "secondary": ["academic_papers", "case_studies", "best_practices"],
                "weak": ["source_code", "implementation_details"],
                "unique_value": 2  # Moderate unique value
            },
            ResearchMode.MULTI_MODEL: {
                "primary": ["diverse_perspectives", "opinions", "analysis", "comparison"],
                "secondary": ["cross_validation", "evaluation", "recommendations"],
                "weak": ["source_code", "implementation", "academic_papers"],
                "unique_value": 3  # High unique value for diverse perspectives
            },
            ResearchMode.COGNITIVE: {
                "primary": ["deep_analysis", "complex_reasoning", "synthesis", "fact_checking"],
                "secondary": ["verification", "comprehensive_review"],
                "weak": ["source_code", "quick_answers"],
                "unique_value": 5  # Highest unique value for deep analysis
            }
        }

        # Redundancy matrix (0.0 = no overlap, 1.0 = complete overlap)
        self.redundancy_matrix = {
            (ResearchMode.OCTOCODE, ResearchMode.WEB): 0.3,  # Some overlap (docs/tutorials)
            (ResearchMode.MULTI_MODEL, ResearchMode.WEB): 0.4,  # Moderate overlap (analysis)
            (ResearchMode.MULTI_MODEL, ResearchMode.COGNITIVE): 0.2,  # Low overlap
            (ResearchMode.COGNITIVE, ResearchMode.WEB): 0.3,  # Some overlap (analysis)
            (ResearchMode.COGNITIVE, ResearchMode.OCTOCODE): 0.1,  # Minimal overlap
        }

        # Cost factors (relative to baseline)
        self.cost_factors = {
            ResearchMode.WEB: 1.0,  # Baseline
            ResearchMode.OCTOCODE: 1.5,  # GitHub API + web
            ResearchMode.MULTI_MODEL: 3.0,  # Multiple AI models
            ResearchMode.COGNITIVE: 2.5,  # Sequential processing
        }

        # Dependency to mode mapping
        self.dependency_mode_mapping = {
            "code_examples": [ResearchMode.OCTOCODE, ResearchMode.WEB],
            "github_repos": [ResearchMode.OCTOCODE],
            "implementation": [ResearchMode.OCTOCODE],
            "documentation": [ResearchMode.WEB],
            "tutorials": [ResearchMode.WEB, ResearchMode.OCTOCODE],
            "academic_papers": [ResearchMode.WEB],
            "diverse_perspectives": [ResearchMode.MULTI_MODEL],
            "opinions": [ResearchMode.MULTI_MODEL],
            "analysis": [ResearchMode.MULTI_MODEL, ResearchMode.COGNITIVE],
            "deep_analysis": [ResearchMode.COGNITIVE],
            "fact_checking": [ResearchMode.COGNITIVE],
        }

    def find_optimal_combination(self, dependencies: QueryDependencies,
                               budget_limit: float = None) -> ModeCombination:
        """Find optimal mode combination using heuristic optimization"""

        # Step 1: Get candidate modes based on dependencies
        candidate_modes = self._get_candidate_modes(dependencies)

        # Step 2: Generate and evaluate all possible combinations
        combinations = self._generate_combinations(candidate_modes, dependencies)

        # Step 3: Score and rank combinations
        scored_combinations = self._score_combinations(combinations, dependencies)

        # Step 4: Apply budget constraints
        if budget_limit:
            scored_combinations = self._apply_budget_filter(scored_combinations, budget_limit)

        # Step 5: Select best combination
        if not scored_combinations:
            # Fallback to single web mode
            return ModeCombination(
                modes=[ResearchMode.WEB],
                predicted_quality=0.6,
                estimated_cost=self.cost_factors[ResearchMode.WEB],
                redundancy_score=0.0,
                coverage_score=0.7
            )

        best_combination = max(scored_combinations, key=lambda x: x.predicted_quality)
        return best_combination

    def _get_candidate_modes(self, dependencies: QueryDependencies) -> list[ResearchMode]:
        """Get list of candidate modes based on dependencies"""
        candidate_modes = set()

        # Map dependencies to modes
        dependency_list = [
            ("code_examples", dependencies.requires_code),
            ("github_repos", dependencies.requires_github),
            ("implementation", dependencies.requires_code),
            ("documentation", dependencies.requires_documentation),
            ("tutorials", dependencies.requires_tutorials),
            ("academic_papers", dependencies.requires_academic),
            ("diverse_perspectives", dependencies.requires_ai_perspectives),
            ("opinions", dependencies.requires_ai_perspectives),
            ("analysis", dependencies.requires_ai_perspectives),
            ("deep_analysis", dependencies.research_depth == ResearchDepth.ADVANCED),
            ("fact_checking", dependencies.complexity_score > 0.6),
        ]

        for dep_type, is_required in dependency_list:
            if is_required:
                modes = self.dependency_mode_mapping.get(dep_type, [])
                candidate_modes.update(modes)

        # Add complexity-based modes
        if dependencies.complexity_score > 0.7:
            candidate_modes.add(ResearchMode.COGNITIVE)

        if dependencies.requires_ai_perspectives and dependencies.complexity_score > 0.4:
            candidate_modes.add(ResearchMode.MULTI_MODEL)

        # Default fallback
        if not candidate_modes:
            candidate_modes.add(ResearchMode.WEB)

        return list(candidate_modes)

    def _generate_combinations(self, modes: list[ResearchMode],
                             dependencies: QueryDependencies) -> list[list[ResearchMode]]:
        """Generate all meaningful combinations of modes"""
        combinations = []

        # Single mode combinations
        for mode in modes:
            combinations.append([mode])

        # Two-mode combinations (if research depth warrants it)
        if dependencies.research_depth in [ResearchDepth.INTERMEDIATE, ResearchDepth.ADVANCED]:
            for i, mode1 in enumerate(modes):
                for mode2 in modes[i+1:]:
                    combination = [mode1, mode2]
                    if self._is_combination_worthwhile(combination):
                        combinations.append(combination)

        # Three-mode combinations (only for advanced research)
        if dependencies.research_depth == ResearchDepth.ADVANCED:
            for i, mode1 in enumerate(modes):
                for j, mode2 in enumerate(modes[i+1:], i+1):
                    for mode3 in modes[j+1:]:
                        combination = [mode1, mode2, mode3]
                        if self._is_combination_worthwhile(combination):
                            combinations.append(combination)

        # Four-mode combination (only for highly complex research)
        if dependencies.research_depth == ResearchDepth.ADVANCED and dependencies.complexity_score > 0.8:
            if len(modes) == 4:
                combinations.append(modes)

        return combinations

    def _is_combination_worthwhile(self, combination: list[ResearchMode]) -> bool:
        """Check if a combination is worthwhile based on redundancy"""
        if len(combination) <= 1:
            return True

        # Calculate total redundancy
        total_redundancy = 0.0
        for i, mode1 in enumerate(combination):
            for mode2 in combination[i+1:]:
                redundancy = self._get_redundancy(mode1, mode2)
                total_redundancy += redundancy

        avg_redundancy = total_redundancy / (len(combination) * (len(combination) - 1) / 2)

        # Allow combinations with moderate redundancy
        return avg_redundancy < 0.6

    def _get_redundancy(self, mode1: ResearchMode, mode2: ResearchMode) -> float:
        """Get redundancy score between two modes"""
        return self.redundancy_matrix.get(
            (mode1, mode2),
            self.redundancy_matrix.get((mode2, mode1), 0.1)  # Default low redundancy
        )

    def _score_combinations(self, combinations: list[list[ResearchMode]],
                          dependencies: QueryDependencies) -> list[ModeCombination]:
        """Score each combination based on quality, cost, and coverage"""
        scored_combinations = []

        for combination in combinations:
            # Calculate coverage score
            coverage_score = self._calculate_coverage_score(combination, dependencies)

            # Calculate redundancy score
            redundancy_score = self._calculate_redundancy_score(combination)

            # Calculate estimated cost
            estimated_cost = sum(self.cost_factors[mode] for mode in combination)

            # Calculate predicted quality (simple heuristic)
            predicted_quality = self._calculate_predicted_quality(
                combination, coverage_score, redundancy_score, dependencies
            )

            scored_combination = ModeCombination(
                modes=combination,
                predicted_quality=predicted_quality,
                estimated_cost=estimated_cost,
                redundancy_score=redundancy_score,
                coverage_score=coverage_score
            )
            scored_combinations.append(scored_combination)

        return scored_combinations

    def _calculate_coverage_score(self, combination: list[ResearchMode],
                                dependencies: QueryDependencies) -> float:
        """Calculate how well the combination covers the dependencies"""
        covered_aspects = set()
        total_aspects_needed = set()

        # Map dependencies to aspects
        dependency_aspects = [
            ("code_examples", dependencies.requires_code),
            ("github_repos", dependencies.requires_github),
            ("documentation", dependencies.requires_documentation),
            ("academic_papers", dependencies.requires_academic),
            ("diverse_perspectives", dependencies.requires_ai_perspectives),
            ("tutorials", dependencies.requires_tutorials),
        ]

        for aspect, needed in dependency_aspects:
            if needed:
                total_aspects_needed.add(aspect)

        # Check coverage by each mode
        for mode in combination:
            mode_strengths = self.mode_strengths[mode]
            covered_aspects.update(mode_strengths["primary"])

        coverage_score = len(covered_aspects.intersection(total_aspects_needed)) / max(len(total_aspects_needed), 1)
        return min(coverage_score, 1.0)

    def _calculate_redundancy_score(self, combination: list[ResearchMode]) -> float:
        """Calculate average redundancy in the combination"""
        if len(combination) <= 1:
            return 0.0

        total_redundancy = 0.0
        pair_count = 0

        for i, mode1 in enumerate(combination):
            for mode2 in combination[i+1:]:
                total_redundancy += self._get_redundancy(mode1, mode2)
                pair_count += 1

        return total_redundancy / pair_count if pair_count > 0 else 0.0

    def _calculate_predicted_quality(self, combination: list[ResearchMode],
                                   coverage_score: float, redundancy_score: float,
                                   dependencies: QueryDependencies) -> float:
        """Calculate predicted quality score for the combination"""
        # Base quality from coverage
        base_quality = coverage_score

        # Penalty for redundancy
        redundancy_penalty = redundancy_score * 0.3

        # Bonus for mode diversity (more modes = better coverage for complex queries)
        diversity_bonus = min(len(combination) * 0.1, 0.3)

        # Complexity adjustment (complex queries benefit from multiple modes)
        complexity_bonus = dependencies.complexity_score * min(len(combination) - 1, 2) * 0.1

        # Research depth adjustment
        if dependencies.research_depth == ResearchDepth.ADVANCED and len(combination) >= 3:
            depth_bonus = 0.2
        elif dependencies.research_depth == ResearchDepth.INTERMEDIATE and len(combination) >= 2:
            depth_bonus = 0.1
        else:
            depth_bonus = 0.0

        # Calculate final quality
        predicted_quality = (
            base_quality
            - redundancy_penalty
            + diversity_bonus
            + complexity_bonus
            + depth_bonus
        )

        return min(max(predicted_quality, 0.0), 1.0)

    def _apply_budget_filter(self, combinations: list[ModeCombination],
                           budget_limit: float) -> list[ModeCombination]:
        """Filter combinations that exceed budget"""
        return [comb for comb in combinations if comb.estimated_cost <= budget_limit]

    def explain_selection(self, combination: ModeCombination,
                         dependencies: QueryDependencies) -> dict:
        """Explain why a particular combination was selected"""
        explanation = {
            "selected_modes": [mode.value for mode in combination.modes],
            "reasoning": [],
            "benefits": [],
            "considerations": []
        }

        for mode in combination.modes:
            mode_strengths = self.mode_strengths[mode]
            benefits = []

            # Match mode strengths to dependencies
            if dependencies.requires_code and "code_examples" in mode_strengths["primary"]:
                benefits.append("Provides code examples and implementation details")

            if dependencies.requires_github and "github_repos" in mode_strengths["primary"]:
                benefits.append("Access to GitHub repositories and source code")

            if dependencies.requires_documentation and "documentation" in mode_strengths["primary"]:
                benefits.append("Comprehensive documentation and guides")

            if dependencies.requires_academic and "academic_papers" in mode_strengths["secondary"]:
                benefits.append("Academic research and papers")

            if dependencies.requires_ai_perspectives and "diverse_perspectives" in mode_strengths["primary"]:
                benefits.append("Multiple AI perspectives and opinions")

            if benefits:
                explanation["benefits"].append(f"{mode.value}: {', '.join(benefits)}")

        # Coverage explanation
        explanation["reasoning"].append(
            f"Coverage score: {combination.coverage_score:.2f} (how well modes match your needs)"
        )

        # Quality explanation
        explanation["reasoning"].append(
            f"Predicted quality: {combination.predicted_quality:.2f}"
        )

        # Cost explanation
        explanation["reasoning"].append(
            f"Estimated cost: {combination.estimated_cost:.1f}x relative to baseline"
        )

        # Redundancy considerations
        if combination.redundancy_score > 0.4:
            explanation["considerations"].append(
                f"Some overlap between modes (redundancy: {combination.redundancy_score:.2f})"
            )
        else:
            explanation["considerations"].append(
                "Low redundancy - modes complement each other well"
            )

        return explanation

# Test cases
if __name__ == "__main__":
    from .enhanced_dependency_analyzer import SimplifiedDependencyAnalyzer

    mapper = ModeRelationshipMapper()
    analyzer = SimplifiedDependencyAnalyzer()

    test_scenarios = [
        "react hooks implementation example",
        "github repository microservices architecture comparison",
        "machine learning research papers best practices",
        "docker production deployment enterprise security",
    ]

    print("=== Mode Selection Test Cases ===")
    for query in test_scenarios:
        deps = analyzer.analyze_dependencies(query)
        combination = mapper.find_optimal_combination(deps)
        explanation = mapper.explain_selection(combination, deps)

        print(f"\nQuery: {query}")
        print(f"Selected Modes: {', '.join(explanation['selected_modes'])}")
        print(f"Predicted Quality: {combination.predicted_quality:.2f}")
        print(f"Estimated Cost: {combination.estimated_cost:.1f}x")
        print("Key Benefits:")
        for benefit in explanation["benefits"]:
            print(f"  • {benefit}")

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .base_prompting_technique import BasePromptingTechnique
from .context_models import PromptingContext, TechniqueCategory, TechniqueMetadata

"""Verbalized Sampling (VS) Technique Implementation

Based on: "Verbalized Sampling: Training-Free Uncertainty Quantification for Language Models"
Addresses: Mode collapse and typicality bias through probability-guided diverse reasoning paths
"""




@dataclass
class VSResult:
    """Result from Verbalized Sampling execution"""

    chosen_path: str
    alternative_paths: list[str]
    probability_estimate: float
    reasoning_steps: list[str]
    confidence_distribution: dict[str, float]
    mode_collapse_detected: bool
    typicality_bias_detected: bool
    execution_metadata: dict[str, Any]


@dataclass
class VSPathProbability:
    """Probability estimate for a reasoning path"""

    path: str
    probability: float
    confidence: float
    reasoning_quality: int  # 1-5 scale


class VerbalizedSamplingTechnique(BasePromptingTechnique):
    """
    Verbalized Sampling (VS) Technique

    Training-free technique to address mode collapse and typicality bias.
    Forces LLMs to estimate probabilities for multiple reasoning paths,
    then samples according to their probability distribution.
    """

    def __init__(self):
        # Import here to avoid circular imports
        from .context_models import PromptingTechnique

        super().__init__(PromptingTechnique.VERBALIZED_SAMPLING)
        self.technique_name = "verbalized_sampling"
        self.category = TechniqueCategory.EXPLORATION
        self.supports_modes = ["analysis", "generation", "decision_making", "problem_solving"]

        # VS-specific parameters
        self.num_paths = 3  # Number of alternative paths to generate
        self.temperature = 0.8  # Temperature for probability-guided sampling
        self.mode_collapse_threshold = 0.85  # Threshold to detect mode collapse
        self.typicality_threshold = 0.75  # Threshold to detect typicality bias

        # VS templates for different probability formats
        self.probability_templates = {
            "numerical": "Probability: {{probability}}",
            "percentage": "Confidence: {{percentage}}%",
            "natural": "Likelihood: {{likelihood}} ({{scale}}/5)",
            "ordinal": "Ranking: {{rank}}/{{total}} most likely",
        }

        # Mode collapse detection patterns
        self.mode_collapse_patterns = [
            r"probability:\s*(0\.[9-9][0-9]*|1\.0)",  # Always near 1.0
            r"confidence:\s*(9[0-9]|100)%",  # Always 90-100%
            r"certainly|definitely|always",  # Absolute language
        ]

        # Typicality bias detection patterns
        self.typicality_patterns = [
            r"most likely|most common|usually",  # Always choosing typical answers
            r"obviously|clearly|naturally",  # Assuming typicality
            r"standard|normal|conventional",  # Preferring standard options
        ]

    async def get_metadata(self) -> TechniqueMetadata:
        """Get technique metadata"""
        return TechniqueMetadata(
            name=self.technique_name,
            category=self.category,
            description="Training-free uncertainty quantification through probability-guided diverse reasoning paths",
            capabilities=[
                "Mode collapse prevention",
                "Typicality bias mitigation",
                "Probability-guided path sampling",
                "Training-free uncertainty quantification",
                "Diverse reasoning path generation",
            ],
            performance_impact="medium",
            complexity_score="medium",
            success_rate=0.82,
            avg_processing_time=2.5,
            applicable_contexts=["analysis", "generation", "decision_making", "exploration"],
            limitations=[
                "Requires probability estimation capability",
                "Can increase response time for multiple paths",
                "May struggle with very complex reasoning",
                "Quality depends on probability calibration",
            ],
        )

    async def validate_applicability(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check if VS is applicable to current context"""
        query = context.get("query", "")
        query_lower = query.lower()

        # Applicability factors
        applicability_factors = {
            "exploration_keywords": any(
                kw in query_lower
                for kw in [
                    "alternative",
                    "different",
                    "another",
                    "other",
                    "various",
                    "multiple",
                ]
            ),
            "uncertainty_keywords": any(
                kw in query_lower
                for kw in [
                    "uncertain",
                    "unsure",
                    "probability",
                    "confidence",
                    "likelihood",
                ]
            ),
            "decision_context": any(
                kw in query_lower
                for kw in [
                    "decide",
                    "choose",
                    "select",
                    "recommend",
                    "pick",
                ]
            ),
            "analysis_context": any(
                kw in query_lower
                for kw in [
                    "analyze",
                    "evaluate",
                    "compare",
                    "assess",
                    "examine",
                ]
            ),
            "generation_context": any(
                kw in query_lower
                for kw in [
                    "generate",
                    "create",
                    "produce",
                    "develop",
                    "design",
                ]
            ),
        }

        # Calculate overall applicability score (0-1)
        applicable_keywords = sum(applicability_factors.values())
        max_keywords = len(applicability_factors)

        # Additional considerations
        query_complexity = len(query.split())
        suitable_length = 10 <= query_complexity <= 200

        overall_applicability = min(1.0, (applicable_keywords / max_keywords) * 0.8 + (0.2 if suitable_length else 0))

        is_applicable = overall_applicability > 0.4

        return {
            "is_applicable": is_applicable,
            "applicability_score": overall_applicability,
            "confidence": 0.75,
            "applicability_factors": applicability_factors,
            "recommended_usage": (
                "high" if overall_applicability > 0.7 else "medium" if overall_applicability > 0.5 else "low"
            ),
            "considerations": (
                [
                    "VS is particularly useful for decisions with multiple valid paths",
                    "Effective when uncertainty needs to be quantified",
                    "Valuable for preventing overconfident single-path responses",
                ]
                if is_applicable
                else [
                    "Consider using VS when exploring multiple reasoning paths",
                    "VS can help avoid premature convergence on single solutions",
                ]
            ),
        }

    async def enhance_prompt(self, prompt: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Enhance prompt with Verbalized Sampling instructions"""
        applicability_result = await self.validate_applicability(context)

        if not applicability_result["is_applicable"]:
            return prompt, {"enhancement_applied": False, "reason": "not_applicable"}

        # Determine optimal VS configuration based on context
        num_paths = self._calculate_optimal_paths(context)
        probability_format = self._select_probability_format(context)

        # Build VS enhancement
        vs_enhancement = self._build_vs_enhancement(num_paths, probability_format, context)

        enhanced_prompt = f"""{prompt}

{vs_enhancement}

Remember: Your probability estimates should reflect genuine uncertainty.
Consider multiple valid approaches and estimate their relative likelihoods honestly."""

        enhancement_metadata = {
            "enhancement_applied": True,
            "num_paths": num_paths,
            "probability_format": probability_format,
            "vs_technique": "verbalized_sampling",
            "mode_collapse_prevention": True,
            "typicality_bias_mitigation": True,
            "enhancement_confidence": applicability_result["applicability_score"],
        }

        return enhanced_prompt, enhancement_metadata

    def _calculate_optimal_paths(self, context: dict[str, Any]) -> int:
        """Calculate optimal number of reasoning paths based on context"""
        query = context.get("query", "")
        query_length = len(query.split())
        complexity_indicators = len([w for w in query.split() if w in ["analyze", "evaluate", "compare", "consider"]])

        # Dynamic path calculation based on query complexity
        if query_length < 20:
            base_paths = 2
        elif query_length < 50:
            base_paths = 3
        else:
            base_paths = 4

        # Add paths for complex queries
        if complexity_indicators >= 2:
            base_paths += 1

        return min(base_paths, 5)  # Cap at 5 paths to avoid excessive generation

    def _select_probability_format(self, context: dict[str, Any]) -> str:
        """Select optimal probability format for the context"""
        query = context.get("query", "").lower()

        if any(kw in query for kw in ["percent", "%", "chance"]):
            return "percentage"
        if any(kw in query for kw in ["number", "value", "score"]):
            return "numerical"
        if any(kw in query for kw in ["likely", "unlikely", "probability"]):
            return "natural"
        return "ordinal"  # Default to ranking format

    def _build_vs_enhancement(self, num_paths: int, probability_format: str, context: dict[str, Any]) -> str:
        """Build Verbalized Sampling enhancement instructions"""
        probability_template = self.probability_templates[probability_format]

        vs_instructions = f"""
**VERBALIZED SAMPLING INSTRUCTIONS**

To ensure thorough exploration and avoid mode collapse, please consider {num_paths} distinct reasoning paths:

1. **Generate {num_paths} Alternative Paths:**
   - Each path should offer a genuinely different approach
   - Avoid minor variations of the same idea
   - Include both conventional and creative approaches

2. **Estimate Probabilities:**
   For each path, provide a probability estimate using this format:
   {probability_template}

   Your probability estimates should:
   - Sum to approximately 1.0 (or 100%)
   - Reflect genuine uncertainty
   - Avoid overconfidence (no path should be >0.9 unless absolutely certain)

3. **Select Primary Path:**
   - Choose one path as your primary recommendation
   - Explain your reasoning for the selection
   - Briefly mention why you didn't choose the others

4. **Probability Justification:**
   - Briefly explain your probability estimates
   - Identify key factors that increase/decrease each path's likelihood
   - Note any uncertainties that affect your estimates

**Output Format:**
```
PATH ANALYSIS:

Path 1: [Brief description]
[Detailed reasoning for this path]
{probability_template.replace("{{probability}}", "[Your estimate]")}

Path 2: [Brief description]
[Detailed reasoning for this path]
{probability_template.replace("{{probability}}", "[Your estimate]")}

... (continue for all {num_paths} paths)

SELECTED PATH: Path [X]
SELECTION REASONING: [Why you chose this path]
PROBABILITY JUSTIFICATION: [How you arrived at your estimates]
```"""

        return vs_instructions

    async def process_response(self, response: str, enhancement_metadata: dict[str, Any]) -> VSResult:
        """Process VS-enhanced response to extract probability information and detect biases"""
        if not enhancement_metadata.get("enhancement_applied"):
            return VSResult(
                chosen_path=response,
                alternative_paths=[],
                probability_estimate=1.0,
                reasoning_steps=[response],
                confidence_distribution={},
                mode_collapse_detected=False,
                typicality_bias_detected=False,
                execution_metadata={"vs_not_applied": True},
            )

        # Parse the VS response
        parsed_paths = self._parse_vs_response(response)

        # Detect mode collapse
        mode_collapse_detected = self._detect_mode_collapse(parsed_paths)

        # Detect typicality bias
        typicality_bias_detected = self._detect_typicality_bias(response)

        # Calculate probability distribution
        probability_distribution = self._calculate_probability_distribution(parsed_paths)

        # Extract reasoning steps
        reasoning_steps = [path.get("reasoning", "") for path in parsed_paths]

        # Determine chosen path
        chosen_path = self._extract_chosen_path(response, parsed_paths)

        # Generate alternative paths list
        alternative_paths = [
            path.get("description", "") for path in parsed_paths if path.get("description", "") != chosen_path
        ]

        return VSResult(
            chosen_path=chosen_path,
            alternative_paths=alternative_paths,
            probability_estimate=parsed_paths[0].get("probability", 1.0) if parsed_paths else 1.0,
            reasoning_steps=reasoning_steps,
            confidence_distribution=probability_distribution,
            mode_collapse_detected=mode_collapse_detected,
            typicality_bias_detected=typicality_bias_detected,
            execution_metadata={
                "vs_applied": True,
                "num_paths_parsed": len(parsed_paths),
                "probability_format": enhancement_metadata.get("probability_format"),
                "parsing_successful": len(parsed_paths) > 0,
                "bias_detection": {
                    "mode_collapse": mode_collapse_detected,
                    "typicality_bias": typicality_bias_detected,
                },
            },
        )

    def _parse_vs_response(self, response: str) -> list[dict[str, Any]]:
        """Parse VS response to extract path information and probabilities"""
        paths = []

        # Look for path sections
        path_pattern = (
            r"Path\s+(\d+):\s*([^\n]+)\n([^Path]*?)(?:Probability:|Confidence:|Likelihood:|Ranking:)\s*([^\n]+)"
        )
        matches = re.findall(path_pattern, response, re.IGNORECASE | re.DOTALL)

        for match in matches:
            path_num, description, reasoning, prob_text = match
            probability = self._extract_probability_from_text(prob_text)

            paths.append(
                {
                    "path_number": int(path_num),
                    "description": description.strip(),
                    "reasoning": reasoning.strip(),
                    "probability_text": prob_text.strip(),
                    "probability": probability,
                },
            )

        # If structured parsing fails, try to extract any probability estimates
        if not paths:
            paths = self._fallback_probability_extraction(response)

        return paths

    def _extract_probability_from_text(self, prob_text: str) -> float:
        """Extract numerical probability from probability text"""
        # Try different formats
        patterns = [
            r"([0-9]*\.?[0-9]+)",  # Decimal numbers
            r"([0-9]+)%",  # Percentages
            r"([1-5])\s*/\s*5",  # X/5 scale
            r"rank\s*([0-9]+)",  # Ranking
        ]

        for pattern in patterns:
            match = re.search(pattern, prob_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))

                # Normalize to 0-1 range
                if "%" in prob_text:
                    return value / 100.0
                if "/5" in prob_text:
                    return value / 5.0
                if "rank" in prob_text.lower():
                    # For ranking, inverse is the probability (lower rank = higher probability)
                    return 1.0 / (value + 1)
                return min(1.0, max(0.0, value))

        return 0.5  # Default probability if extraction fails

    def _fallback_probability_extraction(self, response: str) -> list[dict[str, Any]]:
        """Fallback method to extract any probability-like information"""
        paths = []

        # Split by common delimiters that might indicate different paths
        sections = re.split(r"\n\n|Path\s*\d+|Alternative\s*\d+", response)

        for i, section in enumerate(sections, 1):
            if len(section.strip()) < 10:  # Skip very short sections
                continue

            # Look for probability indicators in the section
            prob_match = re.search(
                r"(?:probability|confidence|likelihood|chance)[:\s]*([0-9]*\.?[0-9]+)",
                section,
                re.IGNORECASE,
            )
            probability = (
                float(prob_match.group(1)) / 100
                if prob_match and "." in prob_match.group(1)
                else (float(prob_match.group(1)) if prob_match else 0.5)
            )

            if probability <= 1.0:
                probability = probability
            elif probability > 1.0:
                probability = probability / 100.0

            paths.append(
                {
                    "path_number": i,
                    "description": f"Alternative {i}",
                    "reasoning": section.strip(),
                    "probability_text": f"Estimated probability: {probability:.2f}",
                    "probability": probability,
                },
            )

        return paths[:3]  # Limit to first 3 paths in fallback

    def _detect_mode_collapse(self, parsed_paths: list[dict[str, Any]]) -> bool:
        """Detect if mode collapse is occurring (all probabilities clustered)"""
        if len(parsed_paths) < 2:
            return True  # Single path indicates potential mode collapse

        probabilities = [path.get("probability", 0.5) for path in parsed_paths]

        # Check if all probabilities are very high (indicating overconfidence)
        all_high = all(p > self.mode_collapse_threshold for p in probabilities)

        # Check if probabilities are very similar (indicating lack of discrimination)
        prob_range = max(probabilities) - min(probabilities)
        very_similar = prob_range < 0.1

        # Check if sum is too high (indicating poor probability calibration)
        prob_sum = sum(probabilities)
        sum_too_high = prob_sum > 1.2

        return all_high or very_similar or sum_too_high

    def _detect_typicality_bias(self, response: str) -> bool:
        """Detect if typicality bias is present (preferring typical answers)"""
        typicality_count = 0
        total_words = len(response.split())

        for pattern in self.typicality_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            typicality_count += len(matches)

        # Calculate typicality ratio
        typicality_ratio = typicality_count / max(total_words, 1)

        return typicality_ratio > 0.02  # More than 2% typicality indicators

    def _calculate_probability_distribution(self, parsed_paths: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate probability distribution across paths"""
        distribution = {}

        for path in parsed_paths:
            path_id = path.get("description", f"Path {path.get('path_number', '?')}")
            probability = path.get("probability", 0.0)
            distribution[path_id] = probability

        return distribution

    def _extract_chosen_path(self, response: str, parsed_paths: list[dict[str, Any]]) -> str:
        """Extract the primary chosen path from response"""
        # Look for explicit selection indicators
        selection_patterns = [
            r"SELECTED\s+PATH:\s*Path\s*(\d+)",
            r"CHOSEN\s+PATH:\s*Path\s*(\d+)",
            r"PRIMARY\s+PATH:\s*Path\s*(\d+)",
            r"I\s+(?:choose|select|prefer)\s*Path\s*(\d+)",
            r"Path\s*(\d+)\s+(?:is\s+)?(?:the\s+)?(?:best|optimal|preferred)",
        ]

        for pattern in selection_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                selected_num = int(match.group(1))

                # Find the corresponding path
                for path in parsed_paths:
                    if path.get("path_number") == selected_num:
                        return path.get("description", f"Path {selected_num}")

        # If no explicit selection, use the path with highest probability
        if parsed_paths:
            best_path = max(parsed_paths, key=lambda p: p.get("probability", 0))
            return best_path.get("description", "Highest probability path")

        # Fallback: return first part of response
        lines = response.split("\n")
        return lines[0] if lines else response[:100]

    async def get_technique_specific_metrics(self) -> dict[str, Any]:
        """Get VS-specific performance metrics"""
        return {
            "vs_technique": "verbalized_sampling",
            "target_issues": ["mode_collapse", "typicality_bias", "overconfidence"],
            "probability_formats": list(self.probability_templates.keys()),
            "detection_thresholds": {
                "mode_collapse": self.mode_collapse_threshold,
                "typicality_bias": self.typicality_threshold,
            },
            "path_generation": {
                "default_paths": self.num_paths,
                "max_paths": 5,
                "min_paths": 2,
            },
            "calibration_needs": [
                "probability_estimation_accuracy",
                "uncertainty_quantification",
                "bias_detection_sensitivity",
            ],
        }

    # Implementation of required abstract methods from BasePromptingTechnique
    async def is_applicable(self, context: PromptingContext) -> bool:
        """Determine if Verbalized Sampling technique is applicable for the given context."""
        # Convert PromptingContext to dict format for our existing validation logic
        context_dict = {
            "query": getattr(context, "query", ""),
            "domain": getattr(context, "domain", "general"),
            "complexity": getattr(context, "complexity", "moderate"),
            "user_intent": getattr(context, "user_intent", "get_advice"),
        }

        applicability_result = await self.validate_applicability(context_dict)
        return applicability_result["is_applicable"]

    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        """Get confidence score for VS technique applicability (0.0 to 1.0)."""
        # Convert PromptingContext to dict format for our existing validation logic
        context_dict = {
            "query": getattr(context, "query", ""),
            "domain": getattr(context, "domain", "general"),
            "complexity": getattr(context, "complexity", "moderate"),
            "user_intent": getattr(context, "user_intent", "get_advice"),
        }

        applicability_result = await self.validate_applicability(context_dict)
        return applicability_result["applicability_score"]

    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        """Apply the Verbalized Sampling technique to enhance the prompt."""
        # Convert PromptingContext to dict format for our existing enhancement logic
        context_dict = {
            "query": getattr(context, "query", prompt),
            "domain": getattr(context, "domain", "general"),
            "complexity": getattr(context, "complexity", "moderate"),
            "user_intent": getattr(context, "user_intent", "get_advice"),
            "available_context": getattr(context, "available_evidence", []),
        }

        enhanced_prompt, _ = await self.enhance_prompt(prompt, context_dict)
        return enhanced_prompt

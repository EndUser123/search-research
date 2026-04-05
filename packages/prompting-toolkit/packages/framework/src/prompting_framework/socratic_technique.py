from __future__ import annotations

from .base_prompting_technique import BasePromptingTechnique
from .context_models import PromptingContext, PromptingTechnique

"""SocraticTechnique Implementation - Mock for Integration Testing

Implements Socratic questioning technique for cognitive enhancement.
This is a simplified mock implementation for integration testing with QueryFanoutTechnique.
"""




class SocraticTechnique(BasePromptingTechnique):
    """
    Mock Socratic Technique for integration testing.

    Implements Socratic questioning to enhance critical thinking and
    deeper analysis through guided questioning.
    """

    def __init__(self):
        """Initialize SocraticTechnique."""
        super().__init__(PromptingTechnique.SOCRATIC)

    async def is_applicable(self, context: PromptingContext) -> bool:
        """Determine if Socratic technique is applicable."""
        # Generally applicable for analytical queries
        return context.complexity in ["moderate", "complex", "expert"]

    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        """Get confidence score for Socratic technique applicability."""
        confidence_scores = {"simple": 0.3, "moderate": 0.7, "complex": 0.9, "expert": 0.95}
        return confidence_scores.get(context.complexity, 0.5)

    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        """Apply Socratic questioning technique to enhance prompt."""
        socratic_enhancement = """
**SOCRATIC QUESTIONING INSTRUCTIONS**

Apply Socratic questioning to deepen analysis:
- Question assumptions and underlying beliefs
- Explore implications and consequences
- Consider alternative perspectives
- Examine evidence and reasoning

**Socratic Questions to Consider:**
- Why do you believe this approach is optimal?
- What assumptions are you making?
- What evidence supports your position?
- What are the potential counterarguments?
- How might this approach fail?

**Critical Analysis Framework:**
1. Identify key assumptions
2. Question the validity of each assumption
3. Explore implications of assumptions
4. Consider alternative viewpoints
5. Synthesize reasoned conclusions

**Output Structure:**
[Your response with explicit questioning of assumptions and reasoning]
"""

        return f"{prompt}\n\n{socratic_enhancement.strip()}"

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

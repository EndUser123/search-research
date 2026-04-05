"""
Basic usage example for arch architecture advisor.

Demonstrates getting architectural recommendations for a simple web service.
"""

from arch.core.advisor import ArchitectureAdvisor
from arch.models import ProjectContext, Scale, Complexity

# Define your project context
context = ProjectContext(
    name="e-commerce-api",
    team_size=3,
    scale=Scale.SMALL,
    complexity=Complexity.MEDIUM,
    requirements=[
        "RESTful API",
        "Database persistence",
        "Authentication required",
        "Low traffic expected (< 1000 req/day)"
    ],
    constraints=[
        "Single region deployment",
        "Budget conscious",
        "Python-based team"
    ]
)

# Get architecture recommendation
advisor = ArchitectureAdvisor()
recommendation = advisor.recommend(context)

print(f"Recommended Pattern: {recommendation.pattern}")
print(f"Rationale: {recommendation.reason}")
print(f"\nSuggested Structure:")
print(recommendation.project_structure)

print(f"\nKey Decisions:")
for decision in recommendation.key_decisions:
    print(f"  - {decision}")

print(f"\nTrade-offs:")
for tradeoff in recommendation.tradeoffs:
    print(f"  - {tradeoff}")

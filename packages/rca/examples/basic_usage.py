#!/usr/bin/env python3
"""Basic rca usage example."""

from rca.simple_rca_engine import SimpleRCAEngine

# Initialize the RCA engine
engine = SimpleRCAEngine()

# Analyze a simple issue
analysis = engine.analyze_issue(
    issue="Application crashes on startup with NullReferenceError"
)

# View the top hypotheses
print("Top 3 Hypotheses:")
for i, hypothesis in enumerate(analysis.ranked_hypotheses[:3], 1):
    print(f"{i}. {hypothesis['description']} (confidence: {hypothesis['confidence']:.2f})")

# View actionable recommendations
print("\nRecommendations:")
for rec in analysis.actionable_recommendations[:3]:
    print(f"  - {rec}")

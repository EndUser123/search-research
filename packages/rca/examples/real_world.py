#!/usr/bin/env python3
"""Real-world rca debugging scenario."""

from rca.simple_rca_engine import SimpleRCAEngine
from rca.session import Session

# Create a new debugging session
session = Session(
    issue_title="Payment processing failures in checkout",
    context={
        "service": "checkout-api",
        "environment": "production",
        "affected_users": "high_priority",
        "business_impact": "revenue_loss"
    }
)

# Initialize engine with session context
engine = SimpleRCAEngine(session=session)

# Run comprehensive analysis
analysis = engine.analyze_issue(
    issue="Payment processing failures increasing over last 2 hours. Error rate: 12%, usually 0.5%."
)

print(f"=== RCA Analysis Report ===")
print(f"Issue: {session.issue_title}")
print(f"Confidence: {analysis.confidence:.1%}")
print(f"Root Cause Identified: {analysis.root_cause if hasattr(analysis, 'root_cause') else 'Pending'}")

print("\n=== Top Hypotheses ===")
for i, hyp in enumerate(analysis.ranked_hypotheses[:5], 1):
    print(f"\n{i}. {hyp['description']}")
    print(f"   Confidence: {hyp['confidence']:.2f}")
    print(f"   Evidence Count: {hyp.get('evidence_count', 0)}")
    if hyp.get('recent_changes'):
        print(f"   Recent Changes: {len(hyp['recent_changes'])} commits match")

print("\n=== Actionable Recommendations ===")
for rec in analysis.actionable_recommendations[:5]:
    priority = "HIGH" if "[Recent Change]" in rec else "MEDIUM"
    print(f"  [{priority}] {rec}")

# Save session for later review
session.save("debugging_session_20260227.json")
print("\nSession saved to debugging_session_20260227.json")

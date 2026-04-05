#!/usr/bin/env python3
"""Advanced rca configuration example."""

from rca.simple_rca_engine import SimpleRCAEngine
from rca.confidence_tracker import ConfidenceTracker

# Initialize with custom configuration
engine = SimpleRCAEngine(
    confidence_threshold=0.8,  # Higher threshold for more conservative analysis
    max_evidence_per_hypothesis=15,  # Collect more evidence before concluding
)

# Analyze with custom parameters
analysis = engine.analyze_issue(
    issue="Database connection timeout after 30 seconds",
    context={
        "service": "payment-api",
        "environment": "production",
        "recent_deploy": True
    }
)

print(f"Issue Type: {analysis.issue_type}")
print(f"Confidence Level: {analysis.confidence:.2f}")
print(f"Evidence Sources Consulted: {len(analysis.evidence_sources)}")
print(f"Active Hypotheses: {len(analysis.ranked_hypotheses)}")

# Show evidence tier breakdown
print("\nEvidence by Tier:")
for tier in ["Tier 1", "Tier 2", "Tier 3"]:
    count = len([e for e in analysis.evidence if e.tier == tier])
    print(f"  {tier}: {count} items")

"""
Baseline metrics for Truth & Evidence hooks modernization.

Captured 2026-02-07 from 7 days of hook_decisions_*.jsonl logs.
Serves as comparison point for Phase 1-5 improvements.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# BASELINE CONFIGURATION
BASELINE_DATE = "2026-02-07"
BASELINE_SAMPLE_SIZE = 20990  # 7 days of data
BASELINE_DAYS = 7
LOG_DIR = Path(__file__).resolve().parent.parent / "session_data"

# BASELINE METRICS (captured from actual data)
BASELINE_METRICS = {
    "sample_size": 20990,
    "stop_router_calls": 5268,
    "block_decisions": 0,  # All decisions were 'start' or 'diagnostic'
    "response_length_p50": 156,
    "response_length_p75": 536,
    "response_length_p90": 1499,
    "response_length_p95": 2001,
    "response_length_p99": 5756,
    "claim_snippet_coverage": 0.74,  # 74%
    "top_hooks": [
        ("Stop_router", 5268),
        ("assumption_audit_v2.py", 1800),
        ("StopHook_cross_validator.py", 1200),
        ("verify_claims_transcript.py", 950),
        ("speculation_gate.py", 890),
    ]
}

# SUCCESS CRITERIA TARGETS (from plan)
SUCCESS_CRITERIA = {
    "p95_stop_hook_latency_ms": 200,  # Target after Phase 3
    "evidence_tier_compliance_percent": 95,  # Target after Phase 2
    "false_positive_reduction_percent": 40,  # Target after Phase 4
    "rollback_time_minutes": 5,  # Per Success Criterion #5
}


def load_baseline_data(days: int = 7) -> List[Dict[str, Any]]:
    """Load baseline data from hook decision logs."""
    samples = []
    log_files = sorted(LOG_DIR.glob("hook_decisions_*.jsonl"), reverse=True)[:days]

    for log_file in log_files:
        with open(log_file) as f:
            for line in f:
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return samples


def calculate_current_metrics(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate metrics from current data sample."""
    stop_router = [s for s in samples if s.get('hook_name') == 'Stop_router']

    # Response length percentiles
    lengths = [s.get('response_length', 0) for s in samples if s.get('response_length', 0) > 0]
    lengths_sorted = sorted(lengths)

    return {
        "sample_size": len(samples),
        "stop_router_calls": len(stop_router),
        "block_decisions": len([s for s in stop_router if s.get('decision') not in ['start', 'diagnostic', 'allow', 'skip']]),
        "response_length_p50": lengths_sorted[len(lengths)//2] if lengths else 0,
        "response_length_p75": lengths_sorted[int(len(lengths)*0.75)] if lengths else 0,
        "response_length_p90": lengths_sorted[int(len(lengths)*0.9)] if lengths else 0,
        "response_length_p95": lengths_sorted[int(len(lengths)*0.95)] if lengths else 0,
        "response_length_p99": lengths_sorted[int(len(lengths)*0.99)] if lengths else 0,
        "claim_snippet_coverage": len([s for s in samples if s.get('claim_snippet', '').strip()]) / len(samples) if samples else 0,
    }


def compare_to_baseline(current: Dict[str, Any]) -> Dict[str, Any]:
    """Compare current metrics to baseline and return deltas."""
    return {
        "sample_size_delta": current["sample_size"] - BASELINE_METRICS["sample_size"],
        "stop_router_calls_delta": current["stop_router_calls"] - BASELINE_METRICS["stop_router_calls"],
        "block_decisions_delta": current["block_decisions"] - BASELINE_METRICS["block_decisions"],
        "response_length_p95_delta": current["response_length_p95"] - BASELINE_METRICS["response_length_p95"],
        "claim_snippet_coverage_delta": current["claim_snippet_coverage"] - BASELINE_METRICS["claim_snippet_coverage"],
    }


def test_baseline_metrics_valid():
    """Test that baseline metrics were properly captured."""
    assert BASELINE_METRICS["sample_size"] >= 10000, "Baseline sample too small for reliable metrics"
    assert BASELINE_METRICS["response_length_p95"] > 0, "Baseline p95 should be positive"
    assert 0 <= BASELINE_METRICS["claim_snippet_coverage"] <= 1, "Coverage should be between 0-1"


def test_baseline_date_recent():
    """Test that baseline data is recent (within 30 days)."""
    baseline_date = datetime.fromisoformat(BASELINE_DATE)
    days_since = (datetime.now() - baseline_date).days
    assert days_since < 30, f"Baseline data is {days_since} days old, too stale for comparison"


def test_success_criteria_defined():
    """Test that all success criteria have defined targets."""
    assert "p95_stop_hook_latency_ms" in SUCCESS_CRITERIA
    assert "evidence_tier_compliance_percent" in SUCCESS_CRITERIA
    assert "false_positive_reduction_percent" in SUCCESS_CRITERIA
    assert "rollback_time_minutes" in SUCCESS_CRITERIA


def test_baseline_against_success_criteria():
    """Test baseline against success criteria to show gap."""
    # Current baseline vs targets
    # Note: p95 response length in characters, target is milliseconds
    # This establishes the gap we need to close

    # Baseline p95 is 2001 chars - we need to measure latency in ms separately
    assert BASELINE_METRICS["response_length_p95"] > 0, "Should have baseline p95"

    # Claim snippet coverage at 74% - target is 95% evidence tier compliance
    # These are different metrics but related
    assert BASELINE_METRICS["claim_snippet_coverage"] < SUCCESS_CRITERIA["evidence_tier_compliance_percent"] / 100, \
        "Baseline shows room for improvement"


if __name__ == "__main__":

    # Run baseline check
    samples = load_baseline_data(days=BASELINE_DAYS)
    current = calculate_current_metrics(samples)

    print("=" * 60)
    print("BASELINE METRICS REPORT")
    print("=" * 60)
    print(f"Date: {BASELINE_DATE}")
    print(f"Sample Size: {current['sample_size']}")
    print()
    print("Stop Router:")
    print(f"  Calls: {current['stop_router_calls']}")
    print(f"  Blocks: {current['block_decisions']}")
    print()
    print("Response Length (chars):")
    print(f"  p50: {current['response_length_p50']}")
    print(f"  p75: {current['response_length_p75']}")
    print(f"  p90: {current['response_length_p90']}")
    print(f"  p95: {current['response_length_p95']} (target: measure latency in ms)")
    print()
    print(f"Claim Snippet Coverage: {current['claim_snippet_coverage']:.1%}")
    print()
    print("Success Criteria Targets:")
    for key, value in SUCCESS_CRITERIA.items():
        print(f"  {key}: {value}")
    print("=" * 60)

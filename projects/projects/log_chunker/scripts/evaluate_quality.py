#!/usr/bin/env python3
"""
Quality evaluation script for log_chunker intelligence reports.
Compares generated reports against golden dataset and scores quality.

Usage:
    python scripts/evaluate_quality.py --golden golden_dataset/sample_intelligence_report.json --test test_output/intelligence_report.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json_report(file_path: Path) -> dict[str, Any]:
    """Load intelligence report from JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)


def calculate_error_pattern_score(
    golden: list[dict], test: list[dict]
) -> tuple[float, str]:
    """Calculate quality score for error pattern detection."""
    if not golden and not test:
        return 1.0, "Both empty - perfect match"

    if not golden:
        return 0.5, f"Golden empty but test found {len(test)} patterns"

    if not test:
        return 0.0, f"Test empty but golden has {len(golden)} patterns"

    # Score based on pattern matching
    golden_templates = {p.get("template", "") for p in golden}
    test_templates = {p.get("template", "") for p in test}

    intersection = golden_templates.intersection(test_templates)
    union = golden_templates.union(test_templates)

    if not union:
        return 1.0, "No patterns to compare"

    jaccard_score = len(intersection) / len(union)
    details = f"Matched {len(intersection)}/{len(golden_templates)} patterns"

    return jaccard_score, details


def calculate_semantic_cluster_score(
    golden: list[dict], test: list[dict]
) -> tuple[float, str]:
    """Calculate quality score for semantic clustering."""
    if not golden and not test:
        return 1.0, "Both empty - perfect match"

    golden_count = len(golden)
    test_count = len(test)

    if golden_count == 0:
        return 0.5, f"Golden empty but test found {test_count} clusters"

    if test_count == 0:
        return 0.0, f"Test empty but golden has {golden_count} clusters"

    # Score based on cluster count similarity (rough approximation)
    count_ratio = min(test_count, golden_count) / max(test_count, golden_count)
    details = f"Cluster count: golden={golden_count}, test={test_count}, ratio={count_ratio:.2f}"

    return count_ratio, details


def calculate_timeline_score(golden: list[dict], test: list[dict]) -> tuple[float, str]:
    """Calculate quality score for timeline events."""
    if not golden and not test:
        return 1.0, "Both empty - perfect match"

    golden_count = len(golden)
    test_count = len(test)

    if golden_count == 0:
        return 0.5, f"Golden empty but test found {test_count} events"

    if test_count == 0:
        return 0.0, f"Test empty but golden has {golden_count} events"

    # Score based on event count and types
    golden_types = {e.get("event_type", "") for e in golden}
    test_types = {e.get("event_type", "") for e in test}

    type_intersection = golden_types.intersection(test_types)
    type_union = golden_types.union(test_types)

    if not type_union:
        return 1.0, "No event types to compare"

    type_score = len(type_intersection) / len(type_union)
    count_ratio = min(test_count, golden_count) / max(test_count, golden_count)

    combined_score = (type_score + count_ratio) / 2
    details = f"Event types: {len(type_intersection)}/{len(golden_types)} matched, count ratio: {count_ratio:.2f}"

    return combined_score, details


def calculate_overall_quality_score(
    golden_report: dict[str, Any], test_report: dict[str, Any]
) -> dict[str, Any]:
    """Calculate comprehensive quality score comparing test against golden dataset."""

    scores = {}

    # Error Pattern Analysis
    error_score, error_details = calculate_error_pattern_score(
        golden_report.get("error_patterns", []), test_report.get("error_patterns", [])
    )
    scores["error_patterns"] = {"score": error_score, "details": error_details}

    # Semantic Clustering
    semantic_score, semantic_details = calculate_semantic_cluster_score(
        golden_report.get("semantic_clusters", []),
        test_report.get("semantic_clusters", []),
    )
    scores["semantic_clusters"] = {"score": semantic_score, "details": semantic_details}

    # Timeline Analysis
    timeline_score, timeline_details = calculate_timeline_score(
        golden_report.get("timeline", []), test_report.get("timeline", [])
    )
    scores["timeline"] = {"score": timeline_score, "details": timeline_details}

    # Correlations (basic count comparison)
    golden_corr_count = len(golden_report.get("correlations", []))
    test_corr_count = len(test_report.get("correlations", []))

    if golden_corr_count == 0 and test_corr_count == 0:
        corr_score = 1.0
        corr_details = "Both empty - perfect match"
    elif golden_corr_count == 0:
        corr_score = 0.5
        corr_details = f"Golden empty but test found {test_corr_count} correlations"
    elif test_corr_count == 0:
        corr_score = 0.0
        corr_details = f"Test empty but golden has {golden_corr_count} correlations"
    else:
        corr_score = min(test_corr_count, golden_corr_count) / max(
            test_corr_count, golden_corr_count
        )
        corr_details = (
            f"Correlation count: golden={golden_corr_count}, test={test_corr_count}"
        )

    scores["correlations"] = {"score": corr_score, "details": corr_details}

    # Anomalies (basic count comparison)
    golden_anom_count = len(golden_report.get("anomalies", []))
    test_anom_count = len(test_report.get("anomalies", []))

    if golden_anom_count == 0 and test_anom_count == 0:
        anom_score = 1.0
        anom_details = "Both empty - perfect match"
    elif golden_anom_count == 0:
        anom_score = 0.5
        anom_details = f"Golden empty but test found {test_anom_count} anomalies"
    elif test_anom_count == 0:
        anom_score = 0.0
        anom_details = f"Test empty but golden has {golden_anom_count} anomalies"
    else:
        anom_score = min(test_anom_count, golden_anom_count) / max(
            test_anom_count, golden_anom_count
        )
        anom_details = (
            f"Anomaly count: golden={golden_anom_count}, test={test_anom_count}"
        )

    scores["anomalies"] = {"score": anom_score, "details": anom_details}

    # Calculate weighted overall score
    weights = {
        "error_patterns": 0.3,
        "semantic_clusters": 0.25,
        "timeline": 0.2,
        "correlations": 0.15,
        "anomalies": 0.1,
    }

    overall_score = sum(scores[key]["score"] * weights[key] for key in weights)

    return {
        "overall_score": overall_score,
        "component_scores": scores,
        "weights_used": weights,
        "quality_grade": get_quality_grade(overall_score),
    }


def get_quality_grade(score: float) -> str:
    """Convert numeric score to quality grade."""
    if score >= 0.9:
        return "A+ (Excellent)"
    elif score >= 0.8:
        return "A (Very Good)"
    elif score >= 0.7:
        return "B (Good)"
    elif score >= 0.6:
        return "C (Acceptable)"
    elif score >= 0.5:
        return "D (Poor)"
    else:
        return "F (Failed)"


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate log_chunker intelligence report quality"
    )
    parser.add_argument(
        "--golden", type=Path, required=True, help="Path to golden dataset JSON file"
    )
    parser.add_argument(
        "--test", type=Path, required=True, help="Path to test output JSON file"
    )
    parser.add_argument("--output", type=Path, help="Path to save evaluation results")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed comparison"
    )

    args = parser.parse_args()

    if not args.golden.exists():
        print(f"Error: Golden dataset file not found: {args.golden}")
        sys.exit(1)

    if not args.test.exists():
        print(f"Error: Test file not found: {args.test}")
        sys.exit(1)

    print(f"Loading golden dataset: {args.golden}")
    golden_report = load_json_report(args.golden)

    print(f"Loading test report: {args.test}")
    test_report = load_json_report(args.test)

    print("\nCalculating quality scores...")
    evaluation_results = calculate_overall_quality_score(golden_report, test_report)

    # Display results
    print("\n" + "=" * 60)
    print("LOG CHUNKER INTELLIGENCE QUALITY EVALUATION")
    print("=" * 60)
    print(f"Overall Score: {evaluation_results['overall_score']:.3f}")
    print(f"Quality Grade: {evaluation_results['quality_grade']}")
    print("\nComponent Scores:")
    print("-" * 40)

    for component, data in evaluation_results["component_scores"].items():
        weight = evaluation_results["weights_used"][component]
        print(f"{component:20s}: {data['score']:.3f} (weight: {weight:.2f})")
        if args.verbose:
            print(f"                     {data['details']}")

    # Save results if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(evaluation_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {args.output}")

    # Exit with appropriate code
    if evaluation_results["overall_score"] >= 0.7:
        print("\n✅ Quality evaluation PASSED")
        sys.exit(0)
    else:
        print("\n❌ Quality evaluation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

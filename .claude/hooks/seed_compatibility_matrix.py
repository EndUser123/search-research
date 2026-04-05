#!/usr/bin/env python3
"""Seed compatibility matrix with high-value combinations from CKS analysis.

This script adds 10-15 initial matrix entries based on cross-category pattern
analysis from TASK-001 (P:/.claude/hooks/analysis/cross_category_patterns_20260315.md).
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).parent
sys.path.insert(0, str(hooks_dir))


from UserPromptSubmit_modules.unified_detection import (
    _COGNITIVE_FRAMEWORKS,
    _REASONING_MODES,
    _THINK_PROFILES,
    CompatibilityMatrixMetadata,
    create_matrix_entry,
    load_matrix_from_disk,
    save_matrix_to_disk,
    validate_matrix,
)


def main():
    """Seed compatibility matrix with high-value combinations."""

    # Load existing matrix from disk
    existing_matrix = load_matrix_from_disk() or {}
    print(f"Loaded {len(existing_matrix)} existing entries from disk")

    # Define new entries based on CKS analysis
    new_entries = {
        # Priority 1: High-frequency combinations (>10 occurrences)

        # 1. AST + Regex + Batch (21 occurrences)
        ("assumption_surfacing", "sequential", "multi_file_refactor"): create_matrix_entry(
            framework="assumption_surfacing",
            mode="sequential",
            profile="multi_file_refactor",
            enhancement="systematic_assumption_surfacing",
            evidence_source="CKS analysis: 21 occurrences in batch refactoring (cross_category_patterns_20260315.md)",
            rationale="Sequential assumption surfacing prevents batch refactoring errors by validating assumptions one file at a time",
        ),

        # 2. Git + Multi-terminal (16 occurrences)
        ("chestertons_fence", "multi_agent", "architecture"): create_matrix_entry(
            framework="chestertons_fence",
            mode="multi_agent",
            profile="architecture",
            enhancement="distributed_state_management",
            evidence_source="CKS analysis: 16 occurrences, documented in questioning_patterns.md (cross_category_patterns_20260315.md)",
            rationale="Multi-agent coordination prevents race conditions in shared VCS state across terminals",
        ),

        # Priority 2: Medium-frequency combinations (5-10 occurrences)

        # 3. AST + Regex + Verify + Batch (8 occurrences)
        ("socratic_decomposition", "sequential", "multi_file_refactor"): create_matrix_entry(
            framework="socratic_decomposition",
            mode="sequential",
            profile="multi_file_refactor",
            enhancement="integration_verification_qa",
            evidence_source="CKS analysis: 8 occurrences in integration verification (cross_category_patterns_20260315.md)",
            rationale="Socratic questioning in sequential mode ensures all integration points are verified before batch changes",
        ),

        # 4. AST + Parallel (7 occurrences)
        ("assumption_surfacing", "multi_agent", "architecture"): create_matrix_entry(
            framework="assumption_surfacing",
            mode="multi_agent",
            profile="architecture",
            enhancement="parallel_assumption_validation",
            evidence_source="CKS analysis: 7 occurrences in Agent tool patterns (cross_category_patterns_20260315.md)",
            rationale="Multi-agent parallel assumption surfacing prevents blind spots in architecture design",
        ),

        # 5. Git + Parallel (4 occurrences)
        ("chestertons_fence", "multi_agent", "pre_commit_risk"): create_matrix_entry(
            framework="chestertons_fence",
            mode="multi_agent",
            profile="pre_commit_risk",
            enhancement="concurrent_git_workflow_safety",
            evidence_source="CKS analysis: 4 occurrences in constitution.md (cross_category_patterns_20260315.md)",
            rationale="Multi-agent review of Git state prevents concurrent workflow conflicts",
        ),

        # 6. AST + Verify + Parallel (8 occurrences)
        ("outcome_anchoring", "multi_agent", "debug_rca"): create_matrix_entry(
            framework="outcome_anchoring",
            mode="multi_agent",
            profile="debug_rca",
            enhancement="parallel_verification_debugging",
            evidence_source="CKS analysis: 8 occurrences in debugging cognition (cross_category_patterns_20260315.md)",
            rationale="Parallel multi-agent verification with outcome anchoring accelerates root cause analysis",
        ),

        # 7. Verify + Batch (8 occurrences)
        ("calibrated_confidence", "sequential", "multi_file_refactor"): create_matrix_entry(
            framework="calibrated_confidence",
            mode="sequential",
            profile="multi_file_refactor",
            enhancement="batch_verification_confidence",
            evidence_source="CKS analysis: 8 occurrences in generic verification (cross_category_patterns_20260315.md)",
            rationale="Sequential verification with calibrated confidence ensures batch operations don't overreach",
        ),

        # 8. Git + Pytest + Regex + Verify + Batch (8 occurrences) - Full testing stack
        ("chestertons_fence", "sequential", "security_review"): create_matrix_entry(
            framework="chestertons_fence",
            mode="sequential",
            profile="security_review",
            enhancement="comprehensive_test_validation",
            evidence_source="CKS analysis: 8 occurrences in batch refactoring validation (cross_category_patterns_20260315.md)",
            rationale="Sequential validation of Git+pytest+regex+verify stack prevents batch refactoring failures",
        ),

        # 9. AST + Git + Pytest + Regex + Batch (7 occurrences) - Four-layer refactoring
        ("socratic_decomposition", "sequential", "architecture"): create_matrix_entry(
            framework="socratic_decomposition",
            mode="sequential",
            profile="architecture",
            enhancement="four_layer_refactoring",
            evidence_source="CKS analysis: 7 occurrences in refactoring planning (cross_category_patterns_20260315.md)",
            rationale="Sequential socratic decomposition coordinates AST+Git+pytest+regex for safe refactoring",
        ),

        # 10. AST + Git + Regex + Batch (7 occurrences) - Minimal refactoring stack
        ("inversion_prompting", "sequential", "multi_file_refactor"): create_matrix_entry(
            framework="inversion_prompting",
            mode="sequential",
            profile="multi_file_refactor",
            enhancement="minimal_refactoring_validation",
            evidence_source="CKS analysis: 7 occurrences in refactoring workflows (cross_category_patterns_20260315.md)",
            rationale="Inversion prompting validates AST+Git+regex changes in sequential mode for safe minimal refactoring",
        ),

        # 11. AST + Git + Search + Verify + Multi-terminal (5 occurrences)
        ("outcome_anchoring", "multi_agent", "debug_rca"): create_matrix_entry(
            framework="outcome_anchoring",
            mode="multi_agent",
            profile="debug_rca",
            enhancement="multi_terminal_search_coordination",
            evidence_source="CKS analysis: 5 occurrences in learning patterns (cross_category_patterns_20260315.md)",
            rationale="Multi-agent outcome anchoring coordinates search+verify+Git across terminals for complex debugging",
        ),

        # Priority 3: Specialized patterns with strong rationale

        # 12. Performance optimization pattern (from existing hardcoded entries)
        ("inversion_prompting", "graph", "performance_analysis"): create_matrix_entry(
            framework="inversion_prompting",
            mode="graph",
            profile="performance_analysis",
            enhancement="failure_mode_dependency_analysis",
            evidence_source="Production pattern: 30% optimization success rate (CLAUDE.md)",
            rationale="Graph reasoning + inversion finds performance bottlenecks by analyzing failure modes",
        ),

        # 13. Security review pattern (from existing hardcoded entries)
        ("devils_advocate", "multi_agent", "security_review"): create_matrix_entry(
            framework="devils_advocate",
            mode="multi_agent",
            profile="security_review",
            enhancement="adversarial_threat_modeling",
            evidence_source="Production pattern: 25% vulnerability detection improvement (CLAUDE.md)",
            rationale="Devil's advocate + multi-agent provides diverse threat models for security review",
        ),

        # 14. Pre-commit risk assessment pattern
        ("calibrated_confidence", "two_stage", "pre_commit_risk"): create_matrix_entry(
            framework="calibrated_confidence",
            mode="two_stage",
            profile="pre_commit_risk",
            enhancement="evidence_based_risk_assessment",
            evidence_source="Production pattern: 60% rollback reduction (CLAUDE.md)",
            rationale="Two-stage reasoning with calibrated confidence improves pre-commit risk assessment",
        ),

        # 15. Tradeoff decision pattern
        ("socratic_decomposition", "multi_agent", "tradeoff_decision"): create_matrix_entry(
            framework="socratic_decomposition",
            mode="multi_agent",
            profile="tradeoff_decision",
            enhancement="structured_tradeoff_analysis",
            evidence_source="Production pattern: improves complex decision quality (CLAUDE.md)",
            rationale="Socratic questioning + multi-agent improves tradeoff analysis by exploring multiple perspectives",
        ),
    }

    print(f"Created {len(new_entries)} new entries from CKS analysis")

    # Merge with existing matrix (new entries take precedence)
    merged_matrix = {**existing_matrix, **new_entries}

    # Validate the merged matrix
    try:
        validate_matrix(
            merged_matrix,
            set(_COGNITIVE_FRAMEWORKS.keys()),
            set(_REASONING_MODES.keys()),
            set(_THINK_PROFILES.keys()),
        )
        print("✓ Matrix validation passed")
    except ValueError as e:
        print(f"✗ Matrix validation failed: {e}")
        return 1

    # Save to disk with metadata
    metadata = CompatibilityMatrixMetadata(
        version="1.0.0",
        schema_version="1.0",
        last_updated=datetime.now(UTC).isoformat(),
        total_entries=len(merged_matrix),
        maintenance_target=50,
    )
    save_matrix_to_disk(merged_matrix, metadata)
    print(f"✓ Saved {len(merged_matrix)} total entries to disk")

    # Show statistics
    print("\n=== Matrix Statistics ===")
    print(f"Total entries: {len(merged_matrix)}")
    print(f"New entries added: {len(new_entries)}")

    # Group by framework
    framework_counts = {}
    for (fw, _, _) in merged_matrix.keys():
        framework_counts[fw] = framework_counts.get(fw, 0) + 1

    print("\nEntries by cognitive framework:")
    for fw, count in sorted(framework_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {fw}: {count}")

    # Group by mode
    mode_counts = {}
    for (_, mode, _) in merged_matrix.keys():
        mode_counts[mode] = mode_counts.get(mode, 0) + 1

    print("\nEntries by reasoning mode:")
    for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {mode}: {count}")

    # Group by profile
    profile_counts = {}
    for (_, _, profile) in merged_matrix.keys():
        profile_counts[profile] = profile_counts.get(profile, 0) + 1

    print("\nEntries by think profile:")
    for profile, count in sorted(profile_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {profile}: {count}")

    print("\n✓ Compatibility matrix seeding complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

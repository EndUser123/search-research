#!/usr/bin/env python3
"""
Speckit Execute Command - v6 Flow Orchestrator Integration

This script provides the main entry point for executing speckit workflows
through the v6 Flow Orchestrator with real FeatureLoopEngine and TrustValidationEngine integration.
"""

import argparse
import sys
from pathlib import Path


def parse_arguments():
    """Parse speckit arguments with v6 defaults."""
    parser = argparse.ArgumentParser(
        description="Execute v6 Flow Orchestrator through speckit interface"
    )

    # Core execution parameters
    parser.add_argument(
        "--engine",
        default="dev6",
        choices=["dev6"],
        help="Engine to use (v6 Flow Orchestrator)",
    )
    parser.add_argument(
        "--feature-dir",
        type=str,
        required=True,
        help="Path to feature directory for execution",
    )
    parser.add_argument(
        "--feature-name",
        type=str,
        help="Feature name (derived from directory if not provided)",
    )

    # v6 FlowOrchestrator execution modes
    parser.add_argument(
        "--mode",
        type=str,
        default="orchestrated",
        choices=["sequential", "feedback_driven", "orchestrated"],
        help="v6 execution mode (default: orchestrated)",
    )

    # v6 trust gate configuration
    parser.add_argument(
        "--trust-threshold",
        type=float,
        default=0.65,
        help="Minimum trust score for gates (default: 0.65)",
    )
    parser.add_argument(
        "--constitution-threshold",
        type=float,
        default=0.75,
        help="Constitution gate minimum score (default: 0.75)",
    )
    parser.add_argument(
        "--implementation-threshold",
        type=float,
        default=0.65,
        help="Implementation gate minimum score (default: 0.65)",
    )
    parser.add_argument(
        "--final-threshold",
        type=float,
        default=0.75,
        help="Final gate minimum score (default: 0.75)",
    )

    # v6 engine configuration
    parser.add_argument(
        "--max-feedback-loops",
        type=int,
        default=3,
        help="Maximum feedback loops for correction attempts",
    )
    parser.add_argument(
        "--tdd-strategy",
        type=str,
        default="single_wave",
        choices=["single_wave", "sequential_waves", "parallel_stages"],
        help="TDD strategy for FeatureLoopEngine",
    )
    parser.add_argument(
        "--max-tdd-waves",
        type=int,
        default=3,
        help="Maximum TDD waves for sequential_waves strategy",
    )

    # Evidence and validation
    parser.add_argument(
        "--save-evidence",
        action="store_true",
        default=True,
        help="Save evidence files to .taskmaster/evidence/",
    )
    parser.add_argument(
        "--constitution-validate",
        action="store_true",
        default=True,
        help="Run constitution gate validation",
    )
    parser.add_argument(
        "--enable-specialist-coordination",
        action="store_true",
        default=True,
        help="Enable CSF NIP specialist coordination",
    )
    parser.add_argument(
        "--enable-security-validation",
        action="store_true",
        default=True,
        help="Enable security validation and threat modeling",
    )

    # Performance and timeout
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=3600,
        help="Execution timeout in seconds (default: 1 hour)",
    )
    parser.add_argument(
        "--max-concurrent-systems",
        type=int,
        default=4,
        help="Maximum concurrent systems for orchestrated mode",
    )

    return parser.parse_args()


def main():
    """Main entry point for speckit execute command."""
    args = parse_arguments()

    # TODO: Implement v6 Flow Orchestrator integration
    print("Speckit Execute - v6 Flow Orchestrator")
    print(f"Feature Directory: {args.feature_dir}")
    print(f"Execution Mode: {args.mode}")
    print(f"Trust Threshold: {args.trust_threshold}")

    # Import and initialize v6 Flow Orchestrator
    try:
        # Add CSF NIP project root to Python path
        # Use path_utils for dynamic path detection
        try:
            csf_nip_root = Path(__file__).parent / "../../__csf"
            # Check if __csf directory exists
            if csf_nip_root.exists() and csf_nip_root.is_dir():
                if str(csf_nip_root) not in sys.path:
                    sys.path.insert(0, str(csf_nip_root))
            else:
                # Fallback: try to detect project root dynamically
                project_root = Path(__file__).parent / "../../.."
                csf_nip_root = project_root / "__csf"
                if csf_nip_root.exists() and csf_nip_root.is_dir():
                    if str(csf_nip_root) not in sys.path:
                        sys.path.insert(0, str(csf_nip_root))
        except Exception as e:
            print(f"Warning: Could not detect __csf path: {e}", file=sys.stderr)
            # Fallback to hardcoded path as last resort
            csf_nip_root = Path("C:/_Python/_Projects/__csf")
            if str(csf_nip_root) not in sys.path:
                sys.path.insert(0, str(csf_nip_root))

        # Import v6 FlowOrchestrator
        from src.modules.development_framework.v6_flow_orchestrator.feature_loop_engine.engine import (
            TDDStrategy,
        )
        from src.modules.development_framework.v6_flow_orchestrator.flow_orchestrator import (
            ExecutionMode,
            FlowOrchestrator,
            FlowOrchestratorConfig,
        )

        print("✅ v6 Flow Orchestrator imported successfully")

        # TODO: Initialize and run the orchestrator with provided arguments
        print("🚀 Execution would start here...")

    except ImportError as e:
        print(f"❌ v6 Flow Orchestrator not available: {e}")
        print("Please ensure the v6 Flow Orchestrator is properly installed in CSF NIP")
        sys.exit(1)


if __name__ == "__main__":
    main()

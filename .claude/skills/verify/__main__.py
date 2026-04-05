#!/usr/bin/env python3
"""
/verify - Verification Orchestrator

Combines /trace + /testing-skills into unified 3-tier workflow.

Usage:
    python __main__.py "skill:arch"
    python __main__.py "hook:breadcrumb_init"
    python __main__.py "feature:e2e"
    python __main__.py "src/handoff.py"  # Auto-detect
"""

import argparse
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.verifier import Verifier
from report import VerificationReport


def main():
    """Main entry point for /verify skill."""
    parser = argparse.ArgumentParser(
        description="Verification orchestrator - 3-tier verification workflow"
    )
    parser.add_argument(
        "target", help='Target to verify (format: "type:name" or just "name" for auto-detect)'
    )
    parser.add_argument(
        "--session-id",
        help="Session ID for E2E tracking (default: CLAUDE_SESSION_ID env var)",
        default=None,
    )
    parser.add_argument("--terminal-id", help="Terminal ID for E2E tracking", default=None)
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed evidence from all tiers"
    )
    parser.add_argument(
        "--deep-lens",
        action="store_true",
        help="Enable 6-lens deep analysis (state/edge-case, invariants, I/O, concurrency, errors, tests)",
    )
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Enable 9-agent adversarial review (7 specialized reviewers + 1 meta-analyzer)",
    )

    args = parser.parse_args()

    # Resolve session_id
    session_id = args.session_id or os.environ.get("CLAUDE_SESSION_ID", "unknown")
    terminal_id = args.terminal_id or "unknown"

    # Create verifier and run verification
    verifier = Verifier()

    try:
        report = verifier.verify(
            target=args.target,
            session_id=session_id,
            terminal_id=terminal_id,
            deep_lens=args.deep_lens,
            adversarial=args.adversarial,
        )

        # Generate output
        generator = VerificationReport()

        if args.output == "markdown":
            output = generator.generate_markdown(report)
            print(output)
        elif args.output == "json":
            output = generator.generate_json(report)
            print(output)

        # Exit with error code if verification failed
        if report["overall_status"] == "failed":
            sys.exit(1)

    except ValueError as e:
        print(f"[VERIFY] Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[VERIFY] Verification interrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[VERIFY] Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

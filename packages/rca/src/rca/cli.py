#!/usr/bin/env python3
"""Command-line interface for rca package."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# State file paths (same as hooks use)
CLAUDE_HOME = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
STATE_DIR = Path(os.environ.get("DEBUG_RCA_STATE_DIR", CLAUDE_HOME / "state" / "rca"))
STATE_FILE = STATE_DIR / "rca_workflow.json"

VALID_OUTCOMES = ("resolved", "failed", "partial")


def parse_backends(backend_str: str | None) -> list[str] | None:
    """Parse and normalize backend filter from command line.

    Converts lowercase backend names to uppercase and maps aliases.
    Matches the behavior of search_enhanced.py CLI.

    Args:
        backend_str: Comma-separated backend names (e.g., "cds,grep,chs")

    Returns:
        List of normalized backend names, or None if no valid backends provided
    """
    if not backend_str:
        return None

    # Backend names must match unified_router constants exactly
    valid_backends = {
        "CHS", "CKS", "CDS", "Grep", "CODE", "DOCS", "SKILLS",
        "HDMA", "MULTILANG", "LSP", "HNSW", "RLM", "RLM_INTERNET",
        "CALL_GRAPH", "CPG", "DEPENDENCY",
    }
    backends = [b.strip().upper() for b in backend_str.split(",")]

    # Map aliases to exact backend constant names
    backend_map = {
        "CODE": "CDS",      # Alias for CDS
        "GREP": "Grep",     # Map to exact constant name
    }

    # Filter and map to valid backends
    result = []
    for b in backends:
        mapped = backend_map.get(b, b)
        if mapped in valid_backends:
            result.append(mapped)

    return result if result else None


def _record_to_cks(
    session_id: str,
    outcome: str,
    problem: str,
    root_cause: str,
    fix: str,
    files: list[str],
    notes: str,
) -> dict[str, bool | str | None]:
    """Record finding to CKS (Correction Knowledge System).

    Args:
        session_id: Unique identifier for the debugging session
        outcome: Resolution outcome ("resolved", "failed", or "partial")
        problem: Description of the problem that was addressed
        root_cause: Root cause analysis or suspected cause
        fix: Fix that was applied or attempted
        files: List of files that were changed
        notes: Additional context or lessons learned

    Returns:
        Dictionary with keys:
        - "cks_stored": bool indicating if storage was successful
        - "entry_type": str indicating "correction" or "negative_correction"
        - "error": str with error message if storage failed
        - "should_fail": bool indicating if this should trigger non-zero exit code
    """
    try:
        from rca.cks_auto_extractor import get_cks_auto_extractor

        extractor = get_cks_auto_extractor()

        if outcome == "resolved":
            success = extractor.extract_and_store(
                session_id=session_id,
                problem_description=problem,
                root_cause=root_cause,
                fix_applied=fix,
                files_changed=files,
                lesson=notes if notes else None,
            )
            return {"cks_stored": success, "entry_type": "correction", "should_fail": False}
        else:
            # Failed/partial: store as negative knowledge
            success = extractor.store_negative_learning(
                session_id=session_id,
                problem_description=problem,
                attempted_fix=fix,
                why_it_failed=root_cause,
                notes=notes,
            )
            return {"cks_stored": success, "entry_type": "negative_correction", "should_fail": False}
    except ImportError:
        # CKS not available - this is expected if not installed
        return {"cks_stored": False, "error": "CKS not available", "should_fail": False}
    except Exception as e:
        # Unexpected CKS failure - should trigger non-zero exit code
        return {"cks_stored": False, "error": str(e), "should_fail": True}


def _record_to_outcome_db(
    session_id: str,
    outcome: str,
    notes: str,
) -> bool:
    """Record outcome to SQLite outcome database.

    Args:
        session_id: Unique identifier for the debugging session
        outcome: Resolution outcome ("resolved", "failed", or "partial")
        notes: Additional context or notes about the outcome

    Returns:
        True if recording was successful, False otherwise
    """
    try:
        from rca.outcome_recorder import Outcome, record_outcome

        outcome_enum = {
            "resolved": Outcome.RESOLVED,
            "failed": Outcome.FAILED,
            "partial": Outcome.PARTIAL,
        }[outcome]

        return record_outcome(
            session_id=session_id,
            outcome=outcome_enum,
            notes=notes,
            verification_method="rca record CLI",
        )
    except Exception:
        return False


def _get_session_id(provided_session: str | None) -> str:
    """Get or generate a session ID for the RCA workflow.

    Args:
        provided_session: Optional session ID provided by the user

    Returns:
        Session ID to use (either provided, from state file, or newly generated)
    """
    # If session provided, use it
    if provided_session:
        return provided_session

    # Try to get from active workflow state
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            if session_id := state.get("session_id", ""):
                return session_id
        except json.JSONDecodeError as e:
            # State file is corrupted - warn user and continue
            print("⚠️  Warning: State file is corrupted (invalid JSON). Using fallback session ID.", file=sys.stderr)
            print(f"   Error: {e}", file=sys.stderr)
            print(f"   File: {STATE_FILE}", file=sys.stderr)
            # Rename corrupted file for recovery
            backup_path = STATE_FILE.with_suffix(".json.corrupted")
            try:
                STATE_FILE.rename(backup_path)
                print(f"   Corrupted file backed up to: {backup_path}", file=sys.stderr)
            except Exception:
                pass  # Best-effort backup
        except OSError as e:
            print(f"⚠️  Warning: Could not read state file: {e}", file=sys.stderr)

    # Generate new session ID
    return f"rca_{int(datetime.now().timestamp())}"


def _update_workflow_state(
    session_id: str,
    outcome: str,
    root_cause: str,
    fix: str,
) -> bool:
    """Update RCA workflow state file with root cause and outcome.

    Args:
        session_id: Unique identifier for the debugging session
        outcome: Resolution outcome ("resolved", "failed", or "partial")
        root_cause: Root cause analysis or suspected cause
        fix: Fix that was applied or attempted

    Returns:
        True if state was updated successfully, False otherwise
    """
    if not STATE_FILE.exists():
        return False

    try:
        state = json.loads(STATE_FILE.read_text())

        # Only update if session matches (or no session filter)
        if session_id and state.get("session_id") and state["session_id"] != session_id:
            return False

        state["root_cause"] = root_cause
        state["root_cause_found"] = True
        state["outcome_recorded"] = True
        state["outcome"] = outcome
        state["fix_applied"] = fix
        state["updated_at"] = datetime.now().isoformat()

        STATE_FILE.write_text(json.dumps(state, indent=2))
        return True
    except (OSError, json.JSONDecodeError):
        return False


def cmd_record(args: argparse.Namespace) -> int:
    """Handle the `record` subcommand.

    Args:
        args: Parsed command-line arguments with attributes:
            - outcome: Resolution outcome ("resolved", "failed", or "partial")
            - problem: Description of the problem
            - root_cause: Root cause analysis
            - fix: Fix that was applied or attempted
            - files: Comma-separated list of changed files
            - notes: Additional context or lessons learned
            - session: Optional session ID

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    outcome = args.outcome
    problem = args.problem
    root_cause = args.root_cause
    fix = args.fix
    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    notes = args.notes or ""

    # Get or generate session ID
    session_id = _get_session_id(args.session)

    results = {"session_id": session_id, "outcome": outcome}

    # 1. Update workflow state file (so SessionEnd hook knows outcome was recorded)
    state_updated = _update_workflow_state(session_id, outcome, root_cause, fix)
    results["state_updated"] = state_updated

    # 2. Record to outcome database
    outcome_recorded = _record_to_outcome_db(session_id, outcome, notes or f"{problem} -> {fix}")
    results["outcome_recorded"] = outcome_recorded

    # 3. Record to CKS
    cks_result = _record_to_cks(session_id, outcome, problem, root_cause, fix, files, notes)
    results["cks"] = cks_result

    # Report
    print(json.dumps(results, indent=2))

    if cks_result.get("cks_stored"):
        if outcome == "resolved":
            print(f"\nStored to CKS: {problem[:60]}... -> {fix[:60]}...")
        else:
            print(f"\nStored negative knowledge: {fix[:60]}... did NOT fix {problem[:60]}...")
    elif cks_result.get("error"):
        error_msg = cks_result['error']
        if error_msg == "CKS not available":
            print("\nCKS not available - finding recorded to outcome database only")
        else:
            print(f"\n❌ CKS storage failed: {error_msg}")
            # Return non-zero exit code for unexpected CKS failures
            if cks_result.get("should_fail"):
                return 1
    else:
        print("\nCKS not available - finding recorded to outcome database only")

    return 0


def cmd_evidence_classify(args: argparse.Namespace) -> int:
    """Handle the `evidence classify` subcommand.

    Args:
        args: Parsed command-line arguments with attributes:
            - source_type: Type of evidence (e.g., failing_test, stack_trace)
            - description: Optional description of the evidence
            - citation: Optional citation/reference for the evidence

    Returns:
        Exit code (0 for success)
    """
    from rca import classify_evidence

    source = classify_evidence(
        args.source_type,
        description=args.description or "",
        citation=args.citation or "",
    )

    result = {
        "source_type": source.source_type,
        "tier": source.tier.name,
        "tier_value": int(source.tier),
        "confidence_ceiling": source.confidence_ceiling,
        "description": source.description,
    }

    print(json.dumps(result, indent=2))

    # Human-readable summary
    print(f"\nEvidence Type: {source.source_type}")
    print(f"Tier: {source.tier.name} (value: {int(source.tier)})")
    print(f"Confidence Ceiling: {source.confidence_ceiling*100:.0f}%")

    if source.is_unverified():
        print("⚠️  WARNING: This is unverified evidence (Tier 4)")

    return 0


def cmd_evidence_ceiling(args: argparse.Namespace) -> int:
    """Handle the `evidence ceiling` subcommand.

    Args:
        args: Parsed command-line arguments with attributes:
            - source: List of evidence sources as "type:description:citation"
            - json: JSON array of evidence sources
            - confidence: Optional proposed confidence level (0.0 to 1.0)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from rca import (
        apply_ceiling,
        classify_evidence,
        get_confidence_ceiling,
    )

    # Parse evidence sources from JSON or individual args
    sources = []

    if args.json:
        # Load from JSON array
        try:
            data = json.loads(args.json)
            for item in data:
                sources.append(classify_evidence(
                    item.get("source_type", "unknown"),
                    item.get("description", ""),
                    item.get("citation", ""),
                ))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            return 1
    else:
        # Build from individual --source arguments
        for src in args.source or []:
            parts = src.split(":", 2)
            if len(parts) < 2:
                print(f"Invalid source format: {src}. Use 'type:description'", file=sys.stderr)
                return 1
            source_type = parts[0]
            description = parts[1] if len(parts) > 1 else ""
            citation = parts[2] if len(parts) > 2 else ""
            sources.append(classify_evidence(source_type, description, citation))

    if not sources:
        print("No evidence sources provided. Use --source or --json", file=sys.stderr)
        return 1

    # Calculate ceiling
    ceiling = get_confidence_ceiling(sources)

    # Apply to confidence if provided
    if args.confidence is not None:
        capped = apply_ceiling(args.confidence, sources)
        print(f"Proposed confidence: {args.confidence*100:.0f}%")
        print(f"Confidence ceiling: {ceiling*100:.0f}%")
        print(f"Capped confidence: {capped*100:.0f}%")

        if capped < args.confidence:
            print(f"⚠️  Confidence reduced by {(args.confidence - capped)*100:.0f}%")
    else:
        print(f"Confidence ceiling: {ceiling*100:.0f}%")

    # Show evidence summary
    from rca import format_evidence_summary
    print("\n" + format_evidence_summary(sources))

    return 0


def cmd_evidence_tiers(args: argparse.Namespace) -> int:
    """Handle the `evidence tiers` subcommand - list all tier definitions.

    Args:
        args: Parsed command-line arguments (unused)

    Returns:
        Exit code (0 for success)
    """
    from rca import SOURCE_TYPE_TIERS, EvidenceTier

    print("Evidence Tier Definitions:")
    print("=" * 60)

    # Group by tier
    by_tier = {
        EvidenceTier.TIER_1: [],
        EvidenceTier.TIER_2: [],
        EvidenceTier.TIER_3: [],
        EvidenceTier.TIER_4: [],
    }

    for source_type, tier in SOURCE_TYPE_TIERS.items():
        by_tier[tier].append(source_type)

    for tier in EvidenceTier:
        print(f"\n{tier.name} ({tier.confidence_ceiling()*100:.0f}% ceiling):")
        if by_tier[tier]:
            for source in sorted(by_tier[tier]):
                print(f"  - {source}")
        else:
            print("  (none)")

    print("\n" + "=" * 60)
    print("Confidence cannot exceed the ceiling of the lowest-tier evidence.")
    print("Mixed tiers: ceiling = lowest tier used")
    print("Tier 4 alone: flag as [UNVERIFIED]")

    return 0


def _display_arch_context(context: dict[str, list]) -> None:
    """Display architectural context search results in a formatted way.

    Args:
        context: Search results dictionary containing keys:
            - components: List of component findings
            - dependencies: List of dependency findings
            - anti_patterns: List of anti-pattern findings
            - similar_issues: List of similar chat issues
            - code_patterns: List of code pattern findings
    """
    # Components
    if context["components"]:
        print(f"📦 Components ({len(context['components'])}):")
        for comp in context["components"][:5]:
            title = comp.get("title", "Unknown")
            score = comp.get("score", 0)
            backend = comp.get("backend", "")
            print(f"  - {title} [{backend} #{score:.2f}]")
        print()

    # Dependencies
    if context["dependencies"]:
        print(f"🔗 Dependencies ({len(context['dependencies'])}):")
        for dep in context["dependencies"][:5]:
            title = dep.get("title", "Unknown")
            print(f"  - {title}")
        print()

    # Anti-patterns
    if context["anti_patterns"]:
        print(f"⚠️  Anti-Patterns ({len(context['anti_patterns'])}):")
        for ap in context["anti_patterns"][:3]:
            title = ap.get("title", "Unknown")
            severity = ap.get("metadata", {}).get("severity", "unknown")
            print(f"  - {title} [{severity.upper()}]")
        print()

    # Similar issues from chat history
    if context["similar_issues"]:
        print(f"💬 Similar Issues from Chat ({len(context['similar_issues'])}):")
        for issue in context["similar_issues"][:3]:
            title = issue.get("title", issue.get("content", ""))[:60]
            score = issue.get("score", 0)
            print(f"  - {title}... [#{score:.2f}]")
        print()

    # Code patterns
    if context["code_patterns"]:
        print(f"📝 Code Patterns ({len(context['code_patterns'])}):")
        for pattern in context["code_patterns"][:5]:
            title = pattern.get("title", "Unknown")
            file_path = pattern.get("metadata", {}).get("file_path", "")
            if file_path:
                print(f"  - {title} ({file_path})")
            else:
                print(f"  - {title}")
        print()

    if not any(context.values()):
        print("  No architectural context found.")
        print("  Tip: Try HDMA backend with queries like 'components', 'dependencies', 'anti-patterns'")


def cmd_arch_search(args: argparse.Namespace) -> int:
    """Handle the `arch` subcommand - architectural context search via Meta-RAG.

    Args:
        args: Parsed command-line arguments with attributes:
            - query: Search query for architectural context
            - component: Optional component to focus on
            - backends: Optional comma-separated list of backends
            - limit: Maximum results per backend (default: 10)
            - json: Output as JSON if True

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from rca import SimpleRCAEngine

    query = " ".join(args.query)
    component = getattr(args, "component", None)
    backends_raw = getattr(args, "backends", None)
    as_json = getattr(args, "json", False)

    # Normalize backend names (lowercase -> uppercase, aliases)
    backends = parse_backends(backends_raw)

    print(f"Searching architectural context: {query}")
    if component:
        print(f"  Component focus: {component}")
    if backends:
        print(f"  Backends: {', '.join(backends)}")

    try:
        # Initialize RCA engine with unified search
        engine = SimpleRCAEngine()

        # Search for architectural context
        context = engine.search_architectural_context(
            issue=query,
            component_name=component,
            backends=backends,
        )

        if as_json:
            print(json.dumps(context, indent=2))
            return 0

        # Display results by category
        print()
        _display_arch_context(context)

        return 0

    except ImportError as e:
        # Expected error: CSF search module not available
        print(f"Error: Unified search not available: {e}")
        print("  Ensure CSF search module is accessible: P:/__csf/src/search/")
        return 1
    except (AttributeError, TypeError, KeyError) as e:
        # Expected errors: Data structure issues from search backends
        print(f"Error: Invalid search result format: {e}")
        print("  This may indicate a backend API change. Try fewer backends or check backend configuration.")
        return 1
    except Exception as e:
        # Unexpected errors: Everything else (network issues, disk full, etc.)
        print(f"Unexpected error during search: {type(e).__name__}: {e}")
        print("  Check system resources and backend connectivity.")
        return 1


def main() -> int:
    """Main entry point for the rca CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog="rca",
        description="AI-assisted Root Cause Analysis",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )
    subparsers = parser.add_subparsers(dest="command")

    # record subcommand
    record_parser = subparsers.add_parser(
        "record",
        help="Record a debugging finding (resolved, failed, or partial)",
    )
    record_parser.add_argument(
        "--outcome", required=True, choices=VALID_OUTCOMES,
        help="What happened: resolved, failed, or partial",
    )
    record_parser.add_argument(
        "--problem", required=True,
        help="What the problem was",
    )
    record_parser.add_argument(
        "--root-cause", required=True, dest="root_cause",
        help="Why it happened (or what you thought caused it, for failed attempts)",
    )
    record_parser.add_argument(
        "--fix", required=True,
        help="What fix was applied (or attempted)",
    )
    record_parser.add_argument(
        "--files", default="",
        help="Comma-separated list of files changed",
    )
    record_parser.add_argument(
        "--notes", default="",
        help="Additional context or lesson learned",
    )
    record_parser.add_argument(
        "--session", default="",
        help="RCA session ID (auto-detected from active session if omitted)",
    )

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a problem statement")
    analyze_parser.add_argument("problem", nargs="+", help="Problem description")

    # hypothesis subcommand
    hyp_parser = subparsers.add_parser("hypothesis", help="Generate hypotheses")
    hyp_parser.add_argument("description", nargs="+", help="Problem description")

    # search subcommand
    search_parser = subparsers.add_parser("search", help="Search similar issues")
    search_parser.add_argument("query", nargs="+", help="Search query")

    # doctor subcommand
    subparsers.add_parser("doctor", help="Run hook launcher health checks")

    # evidence subcommand (Task #988)
    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Evidence tiering operations",
    )
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command")

    # evidence classify
    classify_parser = evidence_subparsers.add_parser(
        "classify",
        help="Classify an evidence source and determine its tier",
    )
    classify_parser.add_argument(
        "source_type",
        help="Type of evidence (e.g., failing_test, stack_trace, speculation)",
    )
    classify_parser.add_argument(
        "--description", "-d", default="",
        help="Description of the evidence",
    )
    classify_parser.add_argument(
        "--citation", "-c", default="",
        help="Citation/reference for the evidence",
    )

    # evidence ceiling
    ceiling_parser = evidence_subparsers.add_parser(
        "ceiling",
        help="Calculate confidence ceiling from evidence sources",
    )
    ceiling_parser.add_argument(
        "--source", "-s", action="append", dest="source",
        help="Evidence source as 'type:description' (can be repeated)",
    )
    ceiling_parser.add_argument(
        "--json", "-j", default="",
        help='JSON array of evidence sources: [{"source_type": "...", "description": "..."}]',
    )
    ceiling_parser.add_argument(
        "--confidence", type=float, default=None,
        help="Proposed confidence level (0.0 to 1.0) to cap",
    )

    # evidence tiers
    evidence_subparsers.add_parser(
        "tiers",
        help="List all evidence tier definitions",
    )

    # arch subcommand (Task #987 - Meta-RAG)
    arch_parser = subparsers.add_parser(
        "arch",
        help="Architectural context search via Meta-RAG",
    )
    arch_parser.add_argument(
        "query",
        nargs="+",
        help="Search query for architectural context (e.g., 'authentication timeout')",
    )
    arch_parser.add_argument(
        "--component", "-c",
        help="Specific component to focus on",
    )
    arch_parser.add_argument(
        "--backends", "-b",
        help="Comma-separated list of backends (e.g., cds,grep,chs,cks,hdma). Case-insensitive.",
    )
    arch_parser.add_argument(
        "--limit", "-l", type=int, default=10,
        help="Maximum results per backend",
    )
    arch_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON",
    )

    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse calls sys.exit() on errors
        # Return the exit code (2 for errors, 0 for --help/--version)
        return e.code if e.code is not None else 2

    # Handle --version flag
    if args.version:
        # Try to get version from package metadata
        try:
            from importlib.metadata import version
            ver = version("rca")
        except Exception:
            ver = "unknown"
        print(f"rca {ver}")
        return 0

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "record":
        return cmd_record(args)

    if args.command == "analyze":
        problem = " ".join(args.problem)
        print(f"Analyzing: {problem}")
        from rca.session import (
            classify_problem_type,
            detect_error_type,
            run_regression_check,
        )
        problem_type = classify_problem_type(problem)
        error_type = detect_error_type(problem)
        print(f"  Problem Type: {problem_type.value}")
        print(f"  Error Type: {error_type}")
        warning = run_regression_check(problem)
        if warning:
            print(f"  {warning}")
        return 0

    if args.command == "hypothesis":
        desc = " ".join(args.description)
        print(f"Hypothesis generation for: {desc}")
        from rca.hypothesis_generator import generate_hypotheses

        # The function requires error_type, error_message, target_file
        # Use reasonable defaults for CLI usage
        hypothesis_set = generate_hypotheses(
            error_type="generic_error",
            error_message=desc,
            target_file="unknown",
        )
        for i, hyp in enumerate(hypothesis_set.hypotheses, 1):
            print(f"  {i}. {hyp.description}")
        return 0

    if args.command == "search":
        query = " ".join(args.query)
        print(f"Searching for: {query}")
        from rca.session import search_cks_history
        results = search_cks_history(query)
        print(f"  Status: {results.get('status', 'unknown')}")
        print(f"  Count: {results.get('count', 0)}")
        return 0

    if args.command == "doctor":
        from rca.hook_launcher import main as hook_launcher_main
        return hook_launcher_main(["--doctor"])

    if args.command == "evidence":
        if args.evidence_command == "classify":
            return cmd_evidence_classify(args)
        if args.evidence_command == "ceiling":
            return cmd_evidence_ceiling(args)
        if args.evidence_command == "tiers":
            return cmd_evidence_tiers(args)

    if args.command == "arch":
        return cmd_arch_search(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""GTO Orchestrator - Chat Session Gap Analysis

This script orchestrates subagents for gap detection, health calculation,
and git context extraction to protect orchestrator context from verbose output.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import sys
import time
from pathlib import Path

# Add lib directory to path
lib_dir = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_dir))

# Add handoff package to path for chain traversal
handoff_package = Path(__file__).resolve().parents[2] / "packages" / "handoff"
if str(handoff_package) not in sys.path:
    sys.path.insert(0, str(handoff_package))

from result_envelope import EVIDENCE_DIR, read_artifact

from lib.monitor import SubagentMonitor
from lib.subagents import (
    GapFinderSubagent,
    GitContextSubagent,
    HealthCalculatorSubagent,
)

# Artifact cleanup configuration
ARTIFACT_MAX_AGE_DAYS = 7  # Delete artifacts older than 7 days

# Maximum sessions to traverse in handoff chain (prevents infinite loops)
MAX_CHAIN_DEPTH = 50

# Circuit breaker: stop after detecting this many circular references across all calls
CIRCUIT_BREAKER_THRESHOLD = 3
_circular_detection_count = 0  # Module-level counter for circuit breaker


def timeout_handler(func):
    """Decorator to add timeout to functions that may hang.

    Uses threading.Timer for cross-platform compatibility (Windows/Unix).

    Args:
        func: Function to wrap with timeout

    Returns:
        Wrapped function that raises TimeoutError after timeout_seconds
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import threading

        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[1] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

        # Wait for thread with timeout
        thread.join(timeout=5)

        if thread.is_alive():
            # Thread is still running - timeout occurred
            raise TimeoutError(f"Function {func.__name__} timed out after 5 seconds")

        if exception[1]:
            raise exception[1]

        return result[0]

    return wrapper


def get_all_transcript_paths(
    terminal_id: str, project_root: Path | None = None
) -> list[Path]:
    """Get all transcript paths by following the handoff chain.

    Traverses from current session back to the first session by:
    1. Loading the handoff file for the terminal
    2. Extracting transcript_path from resume_snapshot
    3. Reading that transcript to find the previous session's reference
    4. Repeating until no more previous sessions exist

    Args:
        terminal_id: Terminal identifier (e.g., "console_abc123")
        project_root: Project root directory (defaults to current working directory)

    Returns:
        List of transcript paths from current to first session (oldest first)
    """
    if project_root is None:
        project_root = Path.cwd()

    # Track visited sessions to prevent infinite loops
    visited_session_ids = set()
    transcript_paths = []

    # Import handoff utilities
    try:
        from scripts.hooks.__lib.handoff_files import HandoffFileStorage
    except ImportError:
        # Handoff package not available, fall back to single transcript
        fallback_path = _get_fallback_transcript_path()
        if fallback_path:
            transcript_paths.append(fallback_path)
        return transcript_paths

    # Load handoff file for this terminal
    storage = HandoffFileStorage(project_root, terminal_id)
    handoff = storage.load_raw_handoff()

    if not handoff:
        # No handoff file - try fallback
        fallback_path = _get_fallback_transcript_path()
        if fallback_path:
            transcript_paths.append(fallback_path)
        return transcript_paths

    # Extract transcript path from handoff
    current_transcript_path = handoff.get("resume_snapshot", {}).get("transcript_path")
    if not current_transcript_path:
        # No transcript path in handoff - try fallback
        fallback_path = _get_fallback_transcript_path()
        if fallback_path:
            transcript_paths.append(fallback_path)
        return transcript_paths

    # Follow the chain
    depth = 0
    circular_detected_this_run = False
    global _circular_detection_count

    while current_transcript_path and depth < MAX_CHAIN_DEPTH:
        transcript_path = Path(current_transcript_path)

        # Skip if we've seen this session before (circular reference check)
        session_id = transcript_path.stem
        if session_id in visited_session_ids:
            print(
                f"⚠️ Circular reference detected: {session_id}, stopping chain traversal",
                file=sys.stderr,
            )
            circular_detected_this_run = True
            break

        visited_session_ids.add(session_id)
        transcript_paths.insert(
            0, transcript_path
        )  # Insert at beginning for oldest-first order

        # Look for previous session reference in this transcript
        try:
            previous_transcript_path = _extract_previous_transcript_path(
                transcript_path
            )
        except TimeoutError:
            print(
                f"⚠️ Timeout extracting previous transcript path from {session_id}, stopping chain traversal",
                file=sys.stderr,
            )
            break

        if not previous_transcript_path:
            # No more sessions in chain
            break

        current_transcript_path = previous_transcript_path
        depth += 1

    # Circuit breaker: track circular detections across runs
    if circular_detected_this_run:
        _circular_detection_count += 1
        if _circular_detection_count >= CIRCUIT_BREAKER_THRESHOLD:
            print(
                f"⚠️ Circuit breaker triggered: {_circular_detection_count} circular detections in recent calls",
                file=sys.stderr,
            )
    else:
        # Reset counter on successful traversal (decay)
        _circular_detection_count = max(0, _circular_detection_count - 1)

    if depth >= MAX_CHAIN_DEPTH:
        print(
            f"⚠️ Reached maximum chain depth ({MAX_CHAIN_DEPTH}), stopping traversal",
            file=sys.stderr,
        )

    return transcript_paths


@timeout_handler
def _extract_previous_transcript_path(transcript_path: Path) -> str | None:
    """Extract previous session's transcript path from a transcript file.

    Searches the first 100 lines of the transcript for a SessionStart message
    containing handoff context with a reference to a previous session's transcript.

    Has 5-second timeout to prevent hangs on large or malformed transcripts.

    Args:
        transcript_path: Path to the transcript file

    Returns:
        Previous session's transcript path or None if not found
    """
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 100:  # Only check first 100 lines
                    break
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    # Look for system message with SessionStart context
                    message = entry.get("message", {})
                    if isinstance(message, str):
                        # Search for UUID pattern in message content
                        import re

                        match = re.search(
                            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.jsonl",
                            message,
                        )
                        if match:
                            previous_uuid = match.group(1)
                            # Make sure it's not the current transcript
                            if previous_uuid not in transcript_path.stem:
                                # Construct the path (same directory as current transcript)
                                return str(
                                    transcript_path.parent / f"{previous_uuid}.jsonl"
                                )
                except json.JSONDecodeError:
                    continue
    except (OSError, FileNotFoundError):
        pass

    return None


def _get_fallback_transcript_path() -> Path | None:
    """Get fallback transcript path from environment or standard locations.

    Returns:
        Path to transcript file or None if not found
    """
    # Check environment variable first
    transcript_path = os.environ.get("TRANSCRIPT_PATH")
    if transcript_path and Path(transcript_path).exists():
        return Path(transcript_path)

    # Fallback to standard locations
    cwd = Path.cwd()
    for transcript_name in ["transcript.jsonl", "transcript.json"]:
        transcript_file = cwd / transcript_name
        if transcript_file.exists():
            return transcript_file

    return None


def get_transcript_path(terminal_id: str) -> Path | None:
    """Get transcript path for terminal.

    Args:
        terminal_id: Terminal identifier

    Returns:
        Path to transcript file or None if not found
    """
    # SessionStart hook provides transcript_path via environment

    transcript_path = os.environ.get("TRANSCRIPT_PATH")
    if transcript_path and Path(transcript_path).exists():
        return Path(transcript_path)

    # Fallback: check standard locations
    cwd = Path.cwd()
    for transcript_name in ["transcript.jsonl", "transcript.json"]:
        transcript_file = cwd / transcript_name
        if transcript_file.exists():
            return transcript_file

    return None


def detect_scope(transcript_path: Path) -> str:
    """Detect analysis scope from transcript size.

    Args:
        transcript_path: Path to transcript file

    Returns:
        "session" for large transcripts, "terminal" for small
    """
    size = transcript_path.stat().st_size
    # Large transcripts (>1MB) get session scope
    return "session" if size > 1024 * 1024 else "terminal"


def get_working_directory() -> str:
    """Get working directory for analysis.

    Returns:
        Current working directory path
    """

    return os.environ.get("PROJECT_ROOT", str(Path.cwd()))


def cleanup_old_artifacts(
    evidence_dir: Path, max_age_days: int = ARTIFACT_MAX_AGE_DAYS
) -> int:
    """Remove old artifacts to prevent disk bloat.

    Args:
        evidence_dir: Path to .evidence directory
        max_age_days: Maximum age in days (default: 7)

    Returns:
        Number of artifacts cleaned
    """
    if not evidence_dir.exists():
        return 0

    cleaned_count = 0
    max_age_seconds = max_age_days * 24 * 60 * 60
    current_time = time.time()

    for artifact_path in evidence_dir.glob("gto_*.md"):
        try:
            artifact_age = current_time - artifact_path.stat().st_mtime
            if artifact_age > max_age_seconds:
                artifact_path.unlink()
                cleaned_count += 1
        except OSError:
            # Skip files that can't be accessed
            continue

    return cleaned_count


def run_analysis(
    terminal_id: str,
    verbose: bool = False,
) -> dict:
    """Run full gap analysis using subagents.

    Args:
        terminal_id: Terminal identifier for artifact naming
        verbose: Whether to include verbose details

    Returns:
        Analysis results dictionary
    """
    # Initialize subagent monitor
    monitor = SubagentMonitor(log_dir=EVIDENCE_DIR)

    # Get all transcript paths from handoff chain
    transcript_paths = get_all_transcript_paths(terminal_id)
    working_dir = get_working_directory()

    if not transcript_paths:
        return {
            "status": "no_transcript",
            "message": "No transcript found for analysis",
            "findings": [],
        }

    # Report chain discovery
    chain_length = len(transcript_paths)
    print(f"🔗 Discovered {chain_length} session(s) in handoff chain", file=sys.stderr)
    for i, path in enumerate(transcript_paths, 1):
        print(f"  {i}. {path.name}", file=sys.stderr)

    # Detect scope from most recent (last) transcript
    scope = detect_scope(transcript_paths[-1])

    # Collect gaps from all transcripts
    all_gaps = []
    gap_results = []

    print(
        f"🔍 Detecting gaps in {scope} scope across {chain_length} session(s)...",
        file=sys.stderr,
    )
    for i, transcript_path in enumerate(transcript_paths):
        print(
            f"  [{i + 1}/{chain_length}] Analyzing {transcript_path.name}...",
            file=sys.stderr,
        )

        gap_finder = GapFinderSubagent()
        gap_monitor_result = monitor.execute_with_retry(
            f"GapFinder_{i}",
            gap_finder.run,
            transcript_path=str(transcript_path),
            scope=scope,
            terminal_id=terminal_id,
            working_dir=working_dir,
        )
        gap_result = gap_monitor_result.envelope
        gap_results.append(gap_result)

        # Parse and collect gaps
        if gap_result["status"] == "done":
            gap_artifact = read_artifact(gap_result["artifact"])
            gaps = parse_gaps_from_artifact(gap_artifact)
            all_gaps.extend(gaps)

    # Merge gap results (use most recent as primary)
    merged_gap_result = gap_results[-1] if gap_results else {"status": "failed"}
    if all_gaps:
        merged_gap_result["metrics"] = merged_gap_result.get("metrics", {})
        merged_gap_result["metrics"]["gaps_found"] = len(all_gaps)

    # Run GitContext subagent with retry logic (optional - may fail in non-git repos)
    print("🌳 Checking git context...", file=sys.stderr)
    git_agent = GitContextSubagent()
    git_monitor_result = monitor.execute_with_retry(
        "GitContext",
        git_agent.run,
        working_directory=working_dir,
        terminal_id=terminal_id,
    )
    git_result = git_monitor_result.envelope

    # Run HealthCalculator subagent with retry logic
    print("💓 Calculating health score...", file=sys.stderr)

    # Parse git context from GitContext artifact
    git_context = None
    if git_result["status"] == "done":
        git_context = parse_git_context_from_artifact(
            read_artifact(git_result["artifact"])
        )

    health_agent = HealthCalculatorSubagent()
    health_monitor_result = monitor.execute_with_retry(
        "HealthCalculator",
        health_agent.run,
        gaps=all_gaps,  # Use all gaps from all transcripts
        git_context=git_context,
        terminal_id=terminal_id,
    )
    health_result = health_monitor_result.envelope

    # Log health report
    monitor.log_health_report()

    # Check for health alerts
    alerts = monitor.check_health_alerts()
    if alerts:
        print("⚠️ Health Alerts:", file=sys.stderr)
        for alert in alerts:
            print(f"  {alert}", file=sys.stderr)

    # Compile results
    results = {
        "status": "done",
        "transcripts": [str(p) for p in transcript_paths],  # All transcripts in chain
        "chain_length": chain_length,
        "scope": scope,
        "gaps": merged_gap_result,
        "git": git_result,
        "health": health_result,
    }

    # Add artifact paths for selective reading
    results["artifacts"] = {
        "gaps": merged_gap_result.get("artifact", ""),
        "git": git_result.get("artifact", ""),
        "health": health_result.get("artifact", ""),
    }

    # Add metrics summary
    results["summary"] = {
        "gaps_found": len(all_gaps),
        "health_score": health_result["metrics"].get("overall_score", 0),
        "git_dirty": not git_context.get("is_clean", True) if git_context else False,
    }

    # Add monitoring metrics (use most recent gap result for monitoring)
    results["monitoring"] = {
        "gap_finder": {
            "attempts": gap_results[-1]["attempts"] if gap_results else 0,
            "duration_ms": sum(r.get("duration_ms", 0) for r in gap_results),
            "sessions_analyzed": len(gap_results),
            "status": "done" if gap_results else "failed",
        },
        "git_context": {
            "attempts": git_monitor_result.attempts,
            "duration_ms": git_monitor_result.duration_ms,
            "status": git_monitor_result.status.value,
        },
        "health_calculator": {
            "attempts": health_monitor_result.attempts,
            "duration_ms": health_monitor_result.duration_ms,
            "status": health_monitor_result.status.value,
        },
    }

    return results


def parse_gaps_from_artifact(artifact_content: str) -> list[dict]:
    """Parse gaps from GapFinder artifact markdown.

    Args:
        artifact_content: Markdown content from artifact

    Returns:
        List of gap dictionaries
    """
    gaps = []
    current_severity = None
    current_turn = None
    current_type = None

    for line in artifact_content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Detect severity headers
        if line.startswith("## ") and "Gaps" in line:
            severity = line.split()[1].lower()  # "## Critical Gaps" -> "critical"
            current_severity = severity
            continue

        # Detect turn entries
        if line.startswith("### Turn ") and ":" in line:
            parts = line.split(":")
            current_turn = int(parts[0].split()[-1])
            current_type = parts[1].strip()
            continue

        # Collect message content
        if current_severity and current_turn and current_type:
            if line and not line.startswith("#"):
                gaps.append(
                    {
                        "severity": current_severity,
                        "turn": current_turn,
                        "type": current_type,
                        "message": line,
                    }
                )
                current_turn = None
                current_type = None

    return gaps


def parse_git_context_from_artifact(artifact_content: str) -> dict | None:
    """Parse git context from GitContext artifact markdown.

    Args:
        artifact_content: Markdown content from artifact

    Returns:
        Git context dictionary or None
    """
    context = {}

    for line in artifact_content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Parse key-value pairs
        if line.startswith("**") and ":" in line:
            key = line.split("**")[1].split(":")[0].strip().lower()
            value = line.split(":", 1)[1].strip().rstrip("*").strip()
            context[key] = value

    return context if context else None


def print_compact_snapshot(results: dict) -> None:
    """Print compact snapshot format (default output).

    Args:
        results: Analysis results from run_analysis()
    """
    if results.get("status") == "no_transcript":
        print("=== GTO SNAPSHOT ===")
        print(
            "- Status: ℹ️  No transcript found — session just started or no history available"
        )
        print()
        print("**Recommended Next Steps**")
        print()
        print("No next steps required - session just started.")
        print()
        print("0 - Nothing left to do")
        return

    summary = results["summary"]
    health_score = summary["health_score"]
    gaps_found = summary["gaps_found"]
    git_dirty = summary["git_dirty"]
    chain_length = results.get("chain_length", 1)

    # Status emoji
    if health_score >= 80:
        status_emoji = "✅"
    elif health_score >= 60:
        status_emoji = "🟡"
    else:
        status_emoji = "🔴"

    print("=== GTO SNAPSHOT ===")
    print(f"- Sessions analyzed: {chain_length}")
    print(
        f"- Status: {status_emoji} Health {health_score}/100, {gaps_found} gaps found"
    )
    if git_dirty:
        print("- Git: dirty (uncommitted changes)")
    else:
        print("- Git: clean")

    # Show transcript chain
    transcripts = results.get("transcripts", [])
    if transcripts:
        print()
        print("**Transcript Chain:**")
        for i, path in enumerate(transcripts, 1):
            print(f"  {i}. {Path(path).name}")

    # Show artifact paths for selective reading
    print()
    print("**Detailed Analysis Artifacts:**")
    if results["artifacts"]["gaps"]:
        print(f"- Gaps: {results['artifacts']['gaps']}")
    if results["artifacts"]["git"]:
        print(f"- Git: {results['artifacts']['git']}")
    if results["artifacts"]["health"]:
        print(f"- Health: {results['artifacts']['health']}")


def print_verbose_analysis(results: dict) -> None:
    """Print verbose analysis with full details.

    Args:
        results: Analysis results from run_analysis()
    """
    print_compact_snapshot(results)

    print()
    print("**Gap Details:**")
    if results["artifacts"]["gaps"]:
        gaps_content = read_artifact(results["artifacts"]["gaps"])
        # Show first 50 lines of gaps
        lines = gaps_content.split("\n")[:50]
        for line in lines:
            print(line)
        if len(gaps_content.split("\n")) > 50:
            print("... (truncated, see artifact for full details)")


def main():
    """Main entry point for GTO orchestrator."""
    parser = argparse.ArgumentParser(
        description="Chat Session Gap Analysis Orchestrator"
    )
    parser.add_argument(
        "--terminal-id",
        default="console",
        help="Terminal identifier for artifact naming",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose analysis output",
    )
    parser.add_argument(
        "--format",
        choices=["compact", "verbose"],
        default="compact",
        help="Output format",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help=f"Clean artifacts older than {ARTIFACT_MAX_AGE_DAYS} days",
    )

    args = parser.parse_args()

    # Run cleanup if requested
    if args.cleanup:
        from result_envelope import EVIDENCE_DIR

        cleaned = cleanup_old_artifacts(EVIDENCE_DIR)
        print(f"🧹 Cleaned {cleaned} old artifact(s)", file=sys.stderr)
        return

    # Run analysis
    results = run_analysis(
        terminal_id=args.terminal_id,
        verbose=args.verbose or args.format == "verbose",
    )

    # Output results
    if args.json:
        # Convert Path objects to strings for JSON serialization
        json_results = json.loads(json.dumps(results, default=str))
        print(json.dumps(json_results, indent=2))
    elif args.format == "verbose":
        print_verbose_analysis(results)
    else:
        print_compact_snapshot(results)


if __name__ == "__main__":
    main()

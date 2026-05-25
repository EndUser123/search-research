#!/usr/bin/env python3
"""
Adversarial subagent output aggregator with multi-terminal isolation.

Aggregates findings from parallel adversarial subagents and saves summary.
Uses terminal-scoped state directories for multi-terminal safety.

Architecture:
- State files: .claude/state/terminals/{terminal_id}/adversarial-{type}-{datetime}.json
- Aggregated output: .claude/state/terminals/{terminal_id}/adversarial-review-latest.json
- Falls back to shared state if terminal_id unavailable
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Structured logging to diagnostics directory (avoids stderr triggering hook error)
_DIAG_DIR = Path(__file__).resolve().parent / 'logs' / 'diagnostics'
_DIAG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _DIAG_DIR / 'adversarial_aggregator.log'
_logger = logging.getLogger('adversarial_aggregator')
_handler = logging.FileHandler(_LOG_FILE, encoding='utf-8')
_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from __lib.runtime_env import get_terminal_id
from __lib.state_paths import get_shared_state_dir, get_terminal_state_dir

# Adversarial subagent types
SUBAGENTS = [
    "security",
    "performance",
    "compliance",
    "quality",
    "testing",
    "qa",
    "rca",
    "failure-modes"
]

# Pattern for file discovery (datetime wildcard)
PATTERN_TEMPLATE = "adversarial-{subagent}-*.json"


def discover_subagent_files(state_dir: Path) -> list[Path]:
    """Discover all adversarial subagent JSON files in state directory."""
    files = []
    for subagent in SUBAGENTS:
        pattern = PATTERN_TEMPLATE.format(subagent=subagent)
        files.extend(state_dir.glob(pattern))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def aggregate_findings(files: list[Path]) -> list[dict]:
    """Aggregate findings from all subagent files."""
    all_findings = []

    for filepath in files:
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            # Extract agent name from filename
            # Format: adversarial-{subagent}-{datetime}.json
            filename = filepath.stem
            parts = filename.split("-")
            if len(parts) >= 2:
                agent_name = f"adversarial-{'-'.join(parts[1:-1])}"
            else:
                agent_name = filename

            for finding in data.get("findings", []):
                finding["agent_name"] = agent_name
                finding["source_file"] = filepath.name
                all_findings.append(finding)

        except (json.JSONDecodeError, OSError) as e:
            _logger.warning(f"Failed to read {filepath}: {e}")

    return all_findings


def group_by_location(findings: list[dict]) -> dict[str, list[dict]]:
    """Group findings by file:line location for consensus detection."""
    groups: dict[str, list[dict]] = {}

    for finding in findings:
        location = finding.get("location", finding.get("file", "unknown"))
        if location not in groups:
            groups[location] = []
        groups[location].append(finding)

    return groups


def calculate_consensus(groups: dict[str, list[dict]]) -> dict:
    """Calculate consensus level for each finding location."""
    consensus = {}

    for location, location_findings in groups.items():
        severity_counts = {}
        for f in location_findings:
            sev = f.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        consensus[location] = {
            "count": len(location_findings),
            "agents": list(set(f.get("agent_name", "unknown") for f in location_findings)),
            "severity_breakdown": severity_counts,
            "highest_severity": max(
                severity_counts.keys(),
                key=lambda s: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}.get(s, 0)
            )
        }

    return consensus


def identify_blocking_issues(consensus: dict, threshold: int = 5) -> list[dict]:
    """Identify issues where multiple agents agree on CRITICAL severity."""
    blocking = []

    for location, data in consensus.items():
        if data["highest_severity"] == "CRITICAL" and data["count"] >= threshold:
            blocking.append({
                "location": location,
                "agreement_count": data["count"],
                "agents": data["agents"]
            })

    return blocking


def format_summary(findings: list[dict], consensus: dict, blocking: list[dict]) -> str:
    """Format aggregation summary for display."""
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for f in findings:
        sev = f.get("severity", "UNKNOWN")
        if sev in severity_counts:
            severity_counts[sev] += 1

    lines = [
        "## ADVERSARIAL REVIEW AGGREGATION",
        "",
        "### Findings Summary",
        f"- Total findings: {len(findings)}",
        f"- CRITICAL: {severity_counts['CRITICAL']}",
        f"- HIGH: {severity_counts['HIGH']}",
        f"- MEDIUM: {severity_counts['MEDIUM']}",
        f"- LOW: {severity_counts['LOW']}",
        "",
        "### Consensus Analysis",
        f"- Unique locations: {len(consensus)}",
        f"- Multi-agent agreement (2+): {sum(1 for c in consensus.values() if c['count'] >= 2)}",
    ]

    if blocking:
        lines.extend([
            "",
            "### ⚠️ BLOCKING ISSUES (5+ agents agree on CRITICAL)",
        ])
        for issue in blocking:
            lines.append(f"- {issue['location']}: {issue['agreement_count']} agents ({', '.join(issue['agents'][:3])}...)")

    lines.extend([
        "",
        "### Files Analyzed",
        f"- {len(set(f.get('source_file', 'unknown') for f in findings))} subagent reports",
    ])

    return "\n".join(lines)


def main():
    """Main aggregation entry point."""
    # Get terminal ID for terminal-scoped state
    terminal_id = get_terminal_id()

    # Determine state directory (terminal-scoped or shared fallback)
    if terminal_id:
        state_dir = get_terminal_state_dir(terminal_id)
    else:
        state_dir = get_shared_state_dir()
        _logger.info(f"No terminal ID, using shared state: {state_dir}")

    # Discover subagent files
    files = discover_subagent_files(state_dir)

    if not files:
        _logger.info("No adversarial subagent files found to aggregate")
        return 0

    _logger.info(f"Found {len(files)} subagent files in {state_dir}")

    # Aggregate findings
    findings = aggregate_findings(files)

    if not findings:
        _logger.info("No findings to aggregate")
        return 0

    # Calculate consensus
    groups = group_by_location(findings)
    consensus = calculate_consensus(groups)

    # Identify blocking issues
    blocking = identify_blocking_issues(consensus)

    # Format and print summary
    summary = format_summary(findings, consensus, blocking)
    print(summary)

    # Save aggregated results
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "terminal_id": terminal_id,
        "total_findings": len(findings),
        "findings": findings,
        "consensus": consensus,
        "blocking_issues": blocking
    }

    output_path = state_dir / "adversarial-review-latest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    _logger.info(f"Aggregated results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

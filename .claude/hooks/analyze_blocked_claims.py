#!/usr/bin/env python3
"""
Analyze Blocked Skill Claims - Review false positive patterns

This tool analyzes the skill_claim_blocks.log file to identify patterns
in blocked claims, helping tune the validation system and reduce false positives.

Usage:
    python analyze_blocked_claims.py [options]

Options:
    --days N         Show last N days (default: 7)
    --weekly         Show week-over-week trends
    --patterns       Show most common claim patterns
    --format FORMAT  Output format: text, json, csv
"""

import argparse
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Constants
LOG_FILE = Path("P:/.claude/state/logs/skill_claim_blocks.log")
DEFAULT_DAYS = 7


def parse_log_entry(line: str) -> dict | None:
    """Parse a log entry into components.

    Format: TIMESTAMP | CLAIM | Evidence: N | Similar: /skill-name

    Args:
        line: Raw log line

    Returns:
        Dictionary with parsed components or None if parsing fails
    """
    try:
        # Split by pipe separator
        parts = line.strip().split('|')
        if len(parts) < 3:
            return None

        timestamp_str = parts[0].strip()
        claim = parts[1].strip()
        evidence_part = parts[2].strip()
        similar_part = parts[3].strip() if len(parts) > 3 else "Similar: None"

        # Parse evidence count
        evidence_match = re.search(r'Evidence:\s*(\d+)', evidence_part)
        evidence_count = int(evidence_match.group(1)) if evidence_match else 0

        # Parse similar skill
        similar_match = re.search(r'Similar:\s*/?([\w-]+)?', similar_part)
        similar_skill = similar_match.group(1) if similar_match and similar_match.group(1) != 'None' else None

        return {
            'timestamp': datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'),
            'claim': claim,
            'evidence_count': evidence_count,
            'similar_skill': similar_skill,
            'raw': line.strip()
        }
    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse line: {line.strip()} - {e}")
        return None


def load_entries(days: int = DEFAULT_DAYS) -> list[dict]:
    """Load log entries from the specified time period.

    Args:
        days: Number of days to look back

    Returns:
        List of parsed log entries
    """
    if not LOG_FILE.exists():
        logger.warning(f"Log file not found: {LOG_FILE}")
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    entries = []

    with open(LOG_FILE, encoding='utf-8') as f:
        for line in f:
            entry = parse_log_entry(line)
            if entry and entry['timestamp'] >= cutoff_date:
                entries.append(entry)

    logger.info(f"Loaded {len(entries)} entries from last {days} days")
    return entries


def show_statistics(entries: list[dict]) -> None:
    """Display summary statistics.

    Args:
        entries: List of log entries
    """
    if not entries:
        logger.info("No entries to analyze")
        return

    # Count by skill name
    claimed_skills = []
    for entry in entries:
        # Extract skill name from claim (e.g., "/library is not a real skill" -> "library")
        skill_match = re.search(r'/([\w-]+)', entry['claim'])
        if skill_match:
            claimed_skills.append(skill_match.group(1))

    skill_counter = Counter(claimed_skills)
    evidence_counter = Counter(e['evidence_count'] for e in entries)
    similar_counter = Counter(e['similar_skill'] for e in entries if e['similar_skill'])

    print("\n📊 STATISTICS")
    print("=" * 60)
    print(f"Total blocked claims: {len(entries)}")
    print(f"Unique skills mentioned: {len(skill_counter)}")
    print(f"Average evidence count: {sum(e['evidence_count'] for e in entries) / len(entries):.1f}")
    print("\nTop 5 Most Blocked Skills:")
    for skill, count in skill_counter.most_common(5):
        print(f"  /{skill}: {count} times")

    print("\nEvidence Distribution:")
    for count, num_entries in sorted(evidence_counter.items()):
        print(f"  {count} tools: {num_entries} claims")

    if similar_counter:
        print("\nTop 5 Suggested Alternatives:")
        for skill, count in similar_counter.most_common(5):
            print(f"  /{skill}: suggested {count} times")


def show_patterns(entries: list[dict]) -> None:
    """Display common patterns in blocked claims.

    Args:
        entries: List of log entries
    """
    print("\n🔍 PATTERN ANALYSIS")
    print("=" * 60)

    # Claim pattern analysis
    claim_patterns = Counter()
    for entry in entries:
        claim_lower = entry['claim'].lower()
        if 'not a real skill' in claim_lower:
            claim_patterns['not a real skill'] += 1
        elif 'does not exist' in claim_lower:
            claim_patterns['does not exist'] += 1
        elif 'no skill called' in claim_lower:
            claim_patterns['no skill called'] += 1
        else:
            claim_patterns['other'] += 1

    print("Claim Type Distribution:")
    for pattern, count in claim_patterns.most_common():
        print(f"  \"{pattern}\": {count} occurrences")

    # False positive indicators
    no_evidence = [e for e in entries if e['evidence_count'] == 0]
    print(f"\n⚠️  Claims with NO evidence: {len(no_evidence)} / {len(entries)} ({len(no_evidence)/len(entries)*100:.1f}%)")

    # Success rate of suggestions
    with_suggestion = [e for e in entries if e['similar_skill']]
    print(f"\n💡 Claims with suggestions: {len(with_suggestion)} / {len(entries)} ({len(with_suggestion)/len(entries)*100:.1f}%)")


def show_weekly_trends(entries: list[dict]) -> None:
    """Display week-over-week trends.

    Args:
        entries: List of log entries
    """
    print("\n📈 WEEKLY TRENDS")
    print("=" * 60)

    # Group by week
    weekly_data = {}
    for entry in entries:
        week_start = entry['timestamp'] - timedelta(days=entry['timestamp'].weekday())
        week_key = week_start.strftime('%Y-W%U')

        if week_key not in weekly_data:
            weekly_data[week_key] = []
        weekly_data[week_key].append(entry)

    print("Blocks per week:")
    for week_key in sorted(weekly_data.keys())[-4:]:  # Last 4 weeks
        week_entries = weekly_data[week_key]
        print(f"  {week_key}: {len(week_entries)} blocks")


def export_format(entries: list[dict], format_type: str) -> str:
    """Export entries in specified format.

    Args:
        entries: List of log entries
        format_type: Export format (json, csv)

    Returns:
        Formatted string
    """
    if format_type == 'json':
        return json.dumps([{
            'timestamp': e['timestamp'].isoformat(),
            'claim': e['claim'],
            'evidence_count': e['evidence_count'],
            'similar_skill': e['similar_skill']
        } for e in entries], indent=2)

    elif format_type == 'csv':
        lines = ['timestamp,claim,evidence_count,similar_skill']
        for e in entries:
            lines.append(f"{e['timestamp'].isoformat()},{e['claim']},{e['evidence_count']},{e['similar_skill'] or ''}")
        return '\n'.join(lines)

    else:  # text
        return '\n'.join(e['raw'] for e in entries)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze blocked skill claims')
    parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help='Days to look back (default: 7)')
    parser.add_argument('--weekly', action='store_true', help='Show week-over-week trends')
    parser.add_argument('--patterns', action='store_true', help='Show common patterns')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text', help='Output format')
    parser.add_argument('--output', help='Output file (optional)')

    args = parser.parse_args()

    # Load entries
    entries = load_entries(args.days)

    if not entries:
        logger.info("No log entries found. Nothing to analyze.")
        return

    # Display requested information
    show_statistics(entries)

    if args.patterns:
        show_patterns(entries)

    if args.weekly:
        show_weekly_trends(entries)

    # Export if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        formatted = export_format(entries, args.format)
        output_path.write_text(formatted, encoding='utf-8')

        logger.info(f"\n✅ Exported to: {output_path}")


if __name__ == '__main__':
    main()

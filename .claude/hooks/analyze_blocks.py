#!/usr/bin/env python3
"""
analyze_blocks.py - Analyze constitutional hook block patterns
Run this to see what's being blocked and adjust sensitivity/whitelists.

Features:
- Shows block statistics by hook, reason, and command
- Tracks last review date and reminds if review is due
- Warns if thresholds exceeded (suggests adjustment needed)
"""

import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

TRACKING_DIR = Path(__file__).resolve().parent / "logs"
REVIEW_MARKER = TRACKING_DIR / ".last_review"
REVIEW_CHECKLIST = Path(__file__).resolve().parent / "hook-review-checklist.md"


# Terminal-scoped log files for multi-terminal isolation
def get_tracking_files() -> list[Path]:
    """Get all terminal-scoped tracking log files."""
    pattern = "constructional_blocks_*.jsonl"
    return sorted(TRACKING_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


# Thresholds for triggering "action needed" warnings
WARN_THRESHOLD = 5  # Warn if any pattern triggers this many times
REVIEW_INTERVAL_DAYS = 7  # Suggest review weekly

# Test patterns to exclude from suggestions (these are deliberate test probes)
TEST_PATTERNS = [
    'eval("evil")',
    "eval('evil')",
    'exec("evil")',
    "exec('evil')",
    'open("test.py"',
    "open('test.py'",
    'open("settings.json"',
    "open('settings.json'",
    'open(".env"',
    "open('.env'",
    ".write('test')",
    '.write("test")',
]


def is_test_command(command: str) -> bool:
    """Check if command is a test pattern (exclude from suggestions)."""
    cmd_lower = command.lower()
    return any(pattern.lower() in cmd_lower for pattern in TEST_PATTERNS)


def get_last_review() -> datetime | None:
    """Get the last review date from marker file."""
    if not REVIEW_MARKER.exists():
        return None
    try:
        with open(REVIEW_MARKER) as f:
            content = f.read().strip()
            return datetime.fromisoformat(content)
    except:
        return None


def update_review_marker():
    """Update the last review marker to now."""
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_MARKER, "w") as f:
        f.write(datetime.now().isoformat())


def show_review_reminder(entry_count: int):
    """Show reminder if review is due or thresholds exceeded."""
    last_review = get_last_review()
    now = datetime.now()
    needs_review = False
    reasons = []

    # Check if review is overdue
    if last_review:
        days_since = (now - last_review).days
        if days_since >= REVIEW_INTERVAL_DAYS:
            needs_review = True
            reasons.append(
                f"Last review was {days_since} days ago (every {REVIEW_INTERVAL_DAYS} days recommended)"
            )
    else:
        needs_review = True
        reasons.append("No previous review recorded")

    # Check if thresholds exceeded
    if entry_count >= WARN_THRESHOLD:
        needs_review = True
        reasons.append(f"Total blocks ({entry_count}) exceeds threshold ({WARN_THRESHOLD})")

    if needs_review:
        print("\n" + "=" * 60)
        print("  REVIEW REMINDER")
        print("=" * 60)
        for reason in reasons:
            print(f"  {reason}")
        print(f"\n  Run the checklist: {REVIEW_CHECKLIST}")
        print("  This reminder will clear after review completes.")
        print("=" * 60 + "\n")


def analyze_blocks():
    """Analyze blocked operations and generate recommendations."""
    tracking_files = get_tracking_files()
    if not tracking_files:
        print("No block data found. Hooks may not have blocked anything yet.")
        print(f"Expected pattern: {TRACKING_DIR / 'constructional_blocks_*.jsonl'}")
        print("\nNote: With log-only mode, blocks may be warnings instead.")
        return

    entries = []
    for tracking_file in tracking_files:
        try:
            with open(tracking_file) as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except:
                        pass
        except OSError:
            pass  # Skip files that can't be read

    if not entries:
        print("No blocks recorded yet.")
        return

    # Show review reminder first
    show_review_reminder(len(entries))

    print(f"=== ANALYSIS OF {len(entries)} BLOCKED/WARNED OPERATIONS ===\n")

    # By hook
    print("## BY HOOK")
    by_hook = Counter(e["hook"] for e in entries)
    for hook, count in by_hook.most_common():
        status = "  ACTION" if count >= WARN_THRESHOLD else ""
        print(f"  {hook}: {count}{status}")

    # By reason
    print("\n## BY REASON")
    by_reason = Counter(e["reason"] for e in entries)
    for reason, count in by_reason.most_common():
        status = "  ACTION" if count >= WARN_THRESHOLD else ""
        print(f"  {count}x: {reason}{status}")

    # Unique commands
    print("\n## UNIQUE COMMANDS")
    unique_cmds = {e["command"] for e in entries}
    print(f"  Total unique: {len(unique_cmds)}")

    # Show recent blocks
    print("\n## RECENT (last 10)")
    for e in entries[-10:]:
        print(f"  [{e['timestamp']}] {e['hook']}")
        print(f"    Reason: {e['reason']}")
        cmd_preview = e["command"][:60].replace("\n", "\\n")
        print(f"    Command: {cmd_preview}...")
        print()

    # Whitelist suggestions (exclude test patterns)
    print("\n## SUGGESTIONS")
    freq_cmds = Counter(e["command"] for e in entries)
    suggestions_made = 0
    for cmd, count in freq_cmds.most_common(10):
        if count >= 2 and not is_test_command(cmd):
            print(f"  Blocked {count}x: {cmd[:50].replace(chr(10), ' ')}...")
            print("    Consider: Add to SAFE_PATTERNS if this is safe")
            suggestions_made += 1

    if suggestions_made == 0:
        print("  No repeated patterns detected. Current tuning looks good.")

    # Review info
    last_review = get_last_review()
    if last_review:
        print(f"\n  Last review: {last_review.date()}")
    else:
        print("\n  Last review: Never")

    print(f"\n  Full data: {TRACKING_DIR / 'constructional_blocks_*.jsonl'}")
    print(f"  Checklist: {REVIEW_CHECKLIST}")


def mark_reviewed():
    """Mark this review as complete (updates the marker)."""
    update_review_marker()
    print("Review marked complete.")
    print(f"Next review due: {(datetime.now() + timedelta(days=REVIEW_INTERVAL_DAYS)).date()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--mark-reviewed":
        mark_reviewed()
    else:
        analyze_blocks()
        print("\n---")
        print("When done reviewing, run: python analyze_blocks.py --mark-reviewed")

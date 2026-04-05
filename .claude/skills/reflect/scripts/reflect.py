#!/usr/bin/env python3
"""
Main reflection orchestration engine.
Coordinates signal extraction, skill updates, and user review.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extract_signals import extract_signals
from learning_ledger import LearningLedger
from output_formatter import OutputFormatter
from present_review import present_review
from show_queue import format_queue_table
from update_skill import update_skill


def check_pending_premortems(memory_dir: str | None = None, days_threshold: int = 30) -> list[str]:
    """Check for pending pre-mortem validations that need attention.

    Integrates with PreMortemFeedbackLoop to check for kill criteria thresholds.
    This helps enforce abandonment criteria for solo dev projects.

    Args:
        memory_dir: Directory for pre-mortem records (uses default if None)
        days_threshold: Days after which to prompt for validation (default: 30)

    Returns:
        List of pending validation messages
    """
    pending_messages = []

    try:
        # Import pre-mortem feedback loop
        import sys
        from pathlib import Path

        # Add pre-mortem lib to path
        pre_mortem_lib = Path("C:/Users/brsth/.claude/skills/pre-mortem/__lib")
        if pre_mortem_lib.exists():
            sys.path.insert(0, str(pre_mortem_lib))

        from feedback_loop import PreMortemFeedbackLoop

        # Initialize feedback loop
        feedback = PreMortemFeedbackLoop(memory_dir=Path(memory_dir) if memory_dir else None)

        # Get pending validations
        pending_files = feedback.get_pending_validations(days_threshold=days_threshold)

        for filepath in pending_files:
            # Extract project name from filename
            stem = filepath.stem
            # Format: premortem_{project}_{timestamp}
            parts = stem.split("_")
            project_name = parts[1] if len(parts) > 1 else "unknown"

            # Get file age
            import os

            file_age_days = (os.path.getmtime(filepath) - os.path.getmtime(os.getcwd())) / 86400

            pending_messages.append(
                f"⚠️  Pre-mortem pending validation: '{project_name}' "
                f"({file_age_days:.0f} days old)"
            )

    except ImportError:
        # Pre-mortem skill not available - skip this check
        pass
    except Exception as e:
        # Don't block reflect if check fails
        pending_messages.append(f"Note: Pre-mortem check skipped: {e}")

    return pending_messages


def store_lessons_to_cks(changes):
    """Extract and store key lessons from approved changes to CKS.

    Args:
        changes: List of approved change dictionaries from reflection

    Returns:
        Number of lessons successfully stored
    """
    try:
        # Try to import CKS (may not be available)
        sys.path.insert(0, "P:/__csf/src")
        from knowledge.systems.cks.unified import CKS
    except ImportError:
        print("Note: CKS not available, skipping lesson storage")
        return 0

    stored_count = 0

    # Extract lessons from each change
    for change in changes:
        skill_name = change.get("skill_name", "unknown")
        proposed = change.get("proposed_updates", {})

        # Process high and medium confidence signals as lessons
        for confidence_level in ["high_confidence", "medium_confidence"]:
            for signal in proposed.get(confidence_level, []):
                content = signal.get("content", "")
                if not content or len(content) < 20:
                    continue

                # Extract lesson content
                lesson_text = content.strip()

                # Determine category and severity
                signal_type = signal.get("type", "correction")
                confidence = signal.get("confidence_score", 0.5)

                # Map signal types to CKS categories
                category_map = {
                    "correction": "CORRECTION",
                    "approval": "FIX",
                    "tool_error": "DEBUG",
                    "question": "WORKFLOW",
                }
                category = category_map.get(signal_type, "DISCOVERY")

                # Map confidence to severity
                if confidence >= 0.85:
                    severity = "critical"
                elif confidence >= 0.70:
                    severity = "important"
                else:
                    severity = "nice-to-know"

                # Create lesson entry
                entry = f"{lesson_text}\n\nContext: {skill_name} skill reflection"

                try:
                    with CKS() as cks:
                        result = cks.ingest_pattern(
                            title=f"Reflection: {skill_name}",
                            content=entry,
                            metadata={
                                "category": category,
                                "severity": severity,
                                "source": "reflect_system",
                                "skill_name": skill_name,
                                "signal_type": signal_type,
                                "confidence": confidence,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                        stored_count += 1
                        print(f"  → Stored: {lesson_text[:50]}...")
                except Exception as e:
                    print(f"  Warning: Failed to store lesson: {e}")
                    continue

    return stored_count


def main():
    """Main reflection workflow"""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Reflect on session transcripts")
    parser.add_argument(
        "--concise", action="store_true", help="Show concise output without decorations"
    )
    parser.add_argument(
        "--scan-history",
        action="store_true",
        help="Scan historical transcripts and add to queue before processing",
    )
    parser.add_argument(
        "transcript",
        nargs="?",
        help="Path to transcript file (or set TRANSCRIPT_PATH env var)",
    )
    args = parser.parse_args()

    # Determine output mode
    output_mode = "concise" if args.concise else "verbose"
    formatter = OutputFormatter(mode=output_mode)

    # 1. Get transcript path from env or argument
    transcript_path = os.getenv("TRANSCRIPT_PATH") or args.transcript

    if output_mode == "verbose":
        print("🧠 Reflection Analysis Starting...")

    # 1.5. Scan history if --scan-history flag is set
    if args.scan_history:
        if output_mode == "verbose":
            print("\n📜 Scanning historical transcripts...")

        try:
            summary = scan_history.scan_sessions()

            if output_mode == "verbose":
                print("\nScan Results:")
                print(f"  Sessions scanned: {summary['scanned']}")
                print(f"  Signals found: {summary['signals_found']}")
                print(f"  Added to queue: {summary['added']}")
                print(f"  Skipped (duplicates): {summary['skipped']}")
                if summary.get("errors", 0) > 0:
                    print(f"  Errors: {summary['errors']}")
                if "message" in summary:
                    print(f"  Note: {summary['message']}")
                print()
        except Exception as e:
            if output_mode == "verbose":
                print(f"✗ Error scanning history: {e}")
                print("Continuing with normal reflection...\n")

    # 1.6. Check for pending queue items and display them
    try:
        ledger = LearningLedger()
        stats = ledger.get_stats()
        pending_count = stats.get("by_status", {}).get("pending", 0)

        if pending_count > 0:
            print(f"\n⚠️  You have {pending_count} pending learning(s) in the queue:")
            print()

            # Display queue table
            queue_table = format_queue_table()
            print(queue_table)
            print()

            print(
                "💡 Tip: Process pending learnings before continuing with new transcript analysis"
            )
            print("   Use /reflect --process-queue to handle queue items")
            print()
    except Exception as e:
        # Don't block reflect if queue check fails
        if output_mode == "verbose":
            print(f"Note: Queue check skipped: {e}")

    # 1.7. Check for pending pre-mortem validations (kill criteria enforcement)
    try:
        pending_premortems = check_pending_premortems(days_threshold=30)

        if pending_premortems:
            print(
                f"\n⚠️  Kill Criteria Check: {len(pending_premortems)} pre-mortem(s) pending validation:"
            )
            print()

            for msg in pending_premortems:
                print(f"  {msg}")
            print()

            print(
                "💡 Tip: Solo dev projects need abandonment criteria to prevent sunk cost fallacy"
            )
            print("   Review pending pre-mortems and consider pivoting or abandoning")
            print()
    except Exception as e:
        # Don't block reflect if pre-mortem check fails
        if output_mode == "verbose":
            print(f"Note: Pre-mortem check skipped: {e}")

    # 2. Extract signals from transcript
    signals_by_skill = None
    try:
        signals_by_skill = extract_signals(transcript_path)
    except Exception as e:
        if output_mode == "verbose":
            print(f"✗ Error extracting signals: {e}")
        return 1

    if not signals_by_skill:
        if output_mode == "verbose":
            print("✓ No improvement suggestions found")
        return 0

    if output_mode == "verbose":
        print(f"Found signals in {len(signals_by_skill)} skill(s)")

    # 3. Present for review
    try:
        approved_changes = present_review(signals_by_skill)
    except KeyboardInterrupt:
        print("\n\nReview interrupted by user")
        return 1
    except Exception as e:
        print(f"✗ Error during review: {e}")
        return 1

    if not approved_changes:
        print("\nNo changes approved")
        return 0

    # 4. Apply changes with backups
    success_count = 0
    for change in approved_changes:
        try:
            if update_skill(change):
                success_count += 1
        except Exception as e:
            print(f"✗ Error updating {change['skill_name']}: {e}")

    if success_count == 0:
        print("\n✗ No skills were updated successfully")
        return 1

    # 5. Git commit
    try:
        commit_changes(approved_changes)
    except Exception as e:
        print(f"Warning: Git commit failed: {e}")
        print("Changes were applied but not committed. Commit manually if needed.")

    print(f"\n✓ {success_count} skill(s) updated successfully")

    # 6. Update reflection timestamp
    update_last_reflection_timestamp()

    # 7. Cleanup stale learnings
    try:
        from learning_ledger import LearningLedger

        ledger = LearningLedger()
        result = ledger.cleanup_stale_learnings(days_threshold=180)
        if result["removed_count"] > 0:
            print(f"\n🧹 Cleaned up {result['removed_count']} stale learning(s)")
        elif result["checked_count"] > 0:
            print(f"\n✓ {result['checked_count']} learning(s) checked, none stale")
    except Exception as e:
        print(f"Warning: Learning cleanup failed: {e}")

    # 8. Store lessons to CKS
    stored_lessons = 0
    try:
        stored_lessons = store_lessons_to_cks(approved_changes)
        if stored_lessons > 0 and output_mode == "verbose":
            print(f"\n✓ Stored {stored_lessons} lesson(s) to CKS")
    except Exception as e:
        if output_mode == "verbose":
            print(f"Warning: Lesson storage failed: {e}")

    # 9. Print final summary
    formatter.format_final_summary(
        skills_updated=success_count,
        lessons_stored=stored_lessons,
        signals_by_skill=signals_by_skill,
        approved_changes=approved_changes,
    )

    return 0


def commit_changes(changes):
    """Commit skill updates to git"""
    skills_dir = Path.home() / ".claude" / "skills"

    # Check if git repo exists
    if not (skills_dir / ".git").exists():
        print("\nNote: Skills directory is not a git repository")
        print("Initialize with: cd ~/.claude/skills && git init")
        return

    skill_names = [c["skill_name"] for c in changes]

    # Build commit message
    message_lines = ["refactor(skills): apply reflection learnings\n"]
    message_lines.append("Signals detected:")

    for change in changes:
        proposed = change.get("proposed_updates", {})
        high_count = len(proposed.get("high_confidence", []))
        medium_count = len(proposed.get("medium_confidence", []))
        low_count = len(proposed.get("low_confidence", []))

        if high_count:
            message_lines.append(f"- HIGH ({high_count}): {change['skill_name']}")
        if medium_count:
            message_lines.append(f"- MEDIUM ({medium_count}): {change['skill_name']}")
        if low_count:
            message_lines.append(f"- LOW ({low_count}): {change['skill_name']}")

    message_lines.append(f"\nSkills updated: {', '.join(skill_names)}\n")

    # Add session info if available
    session_id = os.getenv("SESSION_ID", "unknown")
    auto_reflected = os.getenv("AUTO_REFLECTED", "false")
    message_lines.append(f"Session: {session_id}")
    message_lines.append(f"Auto-reflected: {auto_reflected}\n")

    message_lines.append("🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    message_lines.append("Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>")

    commit_message = "\n".join(message_lines)

    try:
        # Stage all changes in skills directory
        subprocess.run(["git", "add", "."], cwd=skills_dir, check=True, capture_output=True)

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=skills_dir,
            check=True,
            capture_output=True,
        )

        print("\n✓ Changes committed to git")

        # Note: We don't auto-push for safety
        # User can push manually if they want
        print("  (Run 'cd ~/.claude/skills && git push' to push to remote)")

    except subprocess.CalledProcessError as e:
        # Check if it's just "nothing to commit"
        if b"nothing to commit" in e.stdout or b"nothing to commit" in e.stderr:
            print("\nNote: Git reported nothing to commit (files may be unchanged)")
        else:
            raise


def update_last_reflection_timestamp():
    """Update the last reflection timestamp to prevent duplicates"""
    timestamp_file = (
        Path.home() / ".claude" / "skills" / "reflect" / ".state" / "last-reflection.timestamp"
    )
    try:
        with open(timestamp_file, "w") as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        print(f"Warning: Could not update timestamp: {e}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nReflection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

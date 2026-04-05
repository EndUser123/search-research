#!/usr/bin/env python3
from __future__ import annotations

# Import auto-logging decorator
from __lib.hook_base import hook_main

"""
SessionStart Timeline Hook
==========================

Shows recent work activity on session start.

Displays:
- Recent files worked on
- Session summary (edits, tests, etc.)
- Last checkpoint reference
"""
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add CSF NIP to path
sys.path.insert(0, str(PROJECT_ROOT / "__csf" / "src"))


def get_timeline_summary(limit: int = 10) -> str:
    """Get recent timeline summary."""
    try:
        from features.checkpoint import CheckpointTimeline

        timeline = CheckpointTimeline()
        now = datetime.now().isoformat()
        events = timeline.get_before(now, limit=limit)

        if not events:
            return None

        # Group into sessions
        sessions = []
        current_session = [events[0]]

        for i in range(1, len(events)):
            try:
                prev_time = datetime.fromisoformat(events[i-1].get("timestamp", ""))
                curr_time = datetime.fromisoformat(events[i].get("timestamp", ""))
                gap_minutes = (curr_time - prev_time).total_seconds() / 60

                if gap_minutes > 10:
                    sessions.append(current_session)
                    current_session = [events[i]]
                else:
                    current_session.append(events[i])
            except:
                current_session.append(events[i])

        if current_session:
            sessions.append(current_session)

        # Build summary
        lines = ["## Recent Activity"]

        if not sessions:
            lines.append("No recent activity tracked.")
            return "\n".join(lines)

        lines.append(f"Showing {len(sessions)} session(s):")

        for i, session in enumerate(sessions[:3], 1):  # Max 3 sessions
            # Extract session info
            files = set()
            tools = {}
            has_errors = False
            test_results = []

            for event in session:
                tool = event.get("tool", "")
                tools[tool] = tools.get(tool, 0) + 1
                if event.get("file"):
                    files.add(event["file"])

                findings = event.get("findings", [])
                for f in findings:
                    if "Error" in str(f):
                        has_errors = True
                    if "passed" in str(f).lower():
                        test_results.append(f)

            # Format time range
            if len(session) == 1:
                time_str = session[0].get("timestamp", "")[:16]
                lines.append(f"\n### Session {i} at {time_str}")
            else:
                start_time = session[-1].get("timestamp", "")[:16]
                end_time = session[0].get("timestamp", "")[:16]
                lines.append(f"\n### Session {i} ({start_time} to {end_time})")

            # Files
            if files:
                file_list = list(files)[:5]
                files_str = ", ".join(file_list)
                if len(files) > 5:
                    files_str += f" +{len(files)-5} more"
                lines.append(f"   📁 {files_str}")

            # Activity
            activity = []
            if tools.get("Edit", 0):
                activity.append(f"{tools['Edit']} edits")
            if tools.get("Bash", 0):
                activity.append(f"{tools['Bash']} commands")
            if tools.get("Read", 0):
                activity.append(f"{tools['Read']} reads")
            if tools.get("Task", 0):
                activity.append(f"{tools['Task']} delegations")

            if activity:
                lines.append(f"   🔧 {', '.join(activity)}")

            # Tests
            if test_results:
                lines.append(f"   ✅ {test_results[0]}")

            # Errors
            if has_errors:
                lines.append("   ⚠️  errors occurred")

        lines.append(f"\n**Total:** {len(events)} events | Use /timeline for more")
        return "\n".join(lines)

    except Exception:
        return None


def get_last_checkpoint() -> str:
    """Get last checkpoint reference."""
    try:
        checkpoint_dir = Path.home() / ".claude" / "checkpoints"
        if not checkpoint_dir.exists():
            return None

        checkpoints = sorted(checkpoint_dir.glob("ckpt_*.json"), reverse=True)
        if not checkpoints:
            return None

        latest = checkpoints[0]
        import json
        with open(latest) as f:
            data = json.load(f)

        checkpoint_id = data.get("checkpoint_id", latest.stem)
        created_at = data.get("created_at", "")[:16]
        citation_id = data.get("citation_id", "")

        lines = [f"📌 Last checkpoint: {checkpoint_id}"]
        lines.append(f"   Created: {created_at}")
        if citation_id:
            lines.append(f"   Citation: {citation_id}")

        return "\n".join(lines)

    except Exception:
        return None


@hook_main
def main():
    """Hook entry point."""
    result = {
        "hookSpecificOutput": "",
        "additionalContext": "",
    }

    # Get timeline summary
    timeline_summary = get_timeline_summary(limit=10)

    # Get last checkpoint
    checkpoint_info = get_last_checkpoint()

    # Build context
    context_parts = []

    if checkpoint_info:
        context_parts.append(checkpoint_info)

    if timeline_summary:
        context_parts.append(timeline_summary)

    if context_parts:
        result["additionalContext"] = "\n\n".join(context_parts)
        result["hookSpecificOutput"] = context_parts[0].split("\n")[0]  # First line for visibility

    # Return JSON
    import json
    print(json.dumps(result))


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Walkthrough Generator for RCA Sessions

Auto-generates markdown walkthrough documents from RCA session data.
Captures problem, investigation, fix, and verification for evidence preservation.

Usage:
    from rca.walkthrough_generator import generate_walkthrough, save_walkthrough

    walkthrough = generate_walkthrough(session_id)
    filepath = save_walkthrough(session_id, output_dir)

Author: CSF Development Team
Version: 1.0.0
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .outcome_recorder import OutcomeRecorder

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

def get_session_data(session_id: str) -> dict:
    """
    Retrieve all session data from database.

    Args:
        session_id: The RCA session ID

    Returns:
        Dict with session data

    """
    db_path = PROJECT_ROOT / ".speckit" / "taskmaster" / "tasks.db"
    data = {
        "session_id": session_id,
        "problem_description": "",
        "problem_type": "",
        "started_at": "",
        "completed_at": "",
        "chs_results_count": 0,
        "fix_applied": "",
        "outcome": None,
        "outcome_notes": "",
        "verification_method": "",
    }

    with sqlite3.connect(db_path) as conn:
        # Get session info
        cursor = conn.execute(
            "SELECT problem_type, started_at FROM rca_sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if row:
            data["problem_type"] = row[0]
            data["started_at"] = row[1]

        # Get outcome info
        cursor = conn.execute(
            """SELECT outcome, notes, verification_method, recorded_at
               FROM rca_outcomes WHERE session_id = ?""",
            (session_id,)
        )
        row = cursor.fetchone()
        if row:
            data["outcome"] = row[0]
            data["outcome_notes"] = row[1]
            data["verification_method"] = row[2]
            data["completed_at"] = row[3]

    return data


def generate_walkthrough(
    session_id: str,
    problem_description: str = "",
    investigation_summary: str = "",
    fix_description: str = "",
) -> str:
    """
    Generate a markdown walkthrough from RCA session data.

    Args:
        session_id: The RCA session ID
        problem_description: Optional problem description (not stored in DB)
        investigation_summary: Optional summary of investigation steps
        fix_description: Optional detailed fix description

    Returns:
        Markdown walkthrough document

    """
    data = get_session_data(session_id)
    OutcomeRecorder()

    # Use provided problem_description if available, otherwise use placeholder
    if not problem_description:
        problem_description = data.get("problem_description", "Problem description not provided.")

    # Build the walkthrough
    lines = [
        f"# RCA Walkthrough: {session_id}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Problem Type:** {data.get('problem_type', 'Unknown')}",
        "",
    ]

    # Problem Section
    lines.extend([
        "## Problem",
        "",
        problem_description,
        "",
    ])

    # Investigation Section
    lines.extend([
        "## Investigation",
        "",
        investigation_summary or "*Investigation steps not recorded.*",
        "",
        "### Tools Used",
        "- `/search` - Unified multi-source search",
        "- CHS - Historical incident search",
        "- CKS - Pattern recognition",
        "- `/discover` - Codebase exploration",
        "",
    ])

    # Fix Section
    lines.extend([
        "## Fix",
        "",
        fix_description or data.get("fix_applied", "*Fix not yet recorded.*"),
        "",
    ])

    # Verification Section
    lines.extend([
        "## Verification",
        "",
    ])

    if data.get("outcome"):
        outcome = data["outcome"].upper()
        lines.extend([
            f"**Outcome:** {outcome}",
            "",
        ])

        if data.get("outcome_notes"):
            lines.extend([
                f"**Notes:** {data['outcome_notes']}",
                "",
            ])

        if data.get("verification_method"):
            lines.extend([
                f"**Verification Method:** {data['verification_method']}",
                "",
            ])
    else:
        lines.extend([
            "**Status:** Pending - outcome not yet recorded",
            "",
        ])

    # Outcome Section
    lines.extend([
        "## Outcome",
        "",
    ])

    outcome = data.get("outcome")
    if outcome == "resolved":
        lines.extend([
            "✅ **RESOLVED** - Fix verified to work",
            "",
            "**Next Steps:**",
            "- Extract learning to CKS for future reference",
            "- Consider adding regression test",
        ])
    elif outcome == "failed":
        lines.extend([
            "❌ **FAILED** - Fix applied but issue persists",
            "",
            "**Next Steps:**",
            "- Try alternative approach",
            "- Add to avoid list for future sessions",
        ])
    elif outcome == "partial":
        lines.extend([
            "⚠️ **PARTIAL** - Improvement but not fully resolved",
            "",
            "**Next Steps:**",
            "- Continue investigation",
            "- Consider as incremental progress",
        ])
    else:
        lines.extend([
            "❓ **UNKNOWN** - Outcome not yet verified",
            "",
            "**Next Steps:**",
            "- Run verification to confirm fix",
            "- Record outcome with `/debug --record-outcome`",
        ])

    lines.extend(["", ""])

    # Metadata Section
    lines.extend([
        "---",
        "",
        "## Session Metadata",
        "",
        f"- **Session ID:** {session_id}",
        f"- **Started:** {data.get('started_at', 'Unknown')}",
        f"- **Completed:** {data.get('completed_at', 'Pending')}",
        "",
    ])

    return "\n".join(lines)


def save_walkthrough(
    session_id: str,
    output_dir: str | Path = "P:/projects",
    problem_description: str = "",
    investigation_summary: str = "",
    fix_description: str = "",
) -> Path:
    """
    Generate and save walkthrough to file.

    Args:
        session_id: The RCA session ID
        output_dir: Base directory for walkthroughs (default: P:/projects)
        problem_description: Optional problem description (not stored in DB)
        investigation_summary: Optional investigation summary
        fix_description: Optional fix description

    Returns:
        Path to saved walkthrough file

    """
    output_dir = Path(output_dir)

    # Create walkthroughs subdirectory
    walkthroughs_dir = output_dir / "walkthroughs"
    walkthroughs_dir.mkdir(parents=True, exist_ok=True)

    # Generate walkthrough content
    content = generate_walkthrough(
        session_id,
        problem_description,
        investigation_summary,
        fix_description
    )

    # Save to file
    filename = f"walkthrough_{session_id}.md"
    filepath = walkthroughs_dir / filename

    filepath.write_text(content, encoding="utf-8")

    return filepath


def get_walkthrough_path(session_id: str) -> Path | None:
    """
    Get the path to an existing walkthrough file.

    Args:
        session_id: The RCA session ID

    Returns:
        Path to walkthrough file if it exists, None otherwise

    """
    walkthroughs_dir = PROJECT_ROOT / "projects" / "walkthroughs"

    if not walkthroughs_dir.exists():
        return None

    # Check for file with session_id
    for filepath in walkthroughs_dir.glob("walkthrough_*.md"):
        if session_id in filepath.name:
            return filepath

    return None


# Convenience function for quick generation
def create_walkthrough_for_session(
    session_id: str,
    investigation_summary: str = "",
    fix_description: str = "",
) -> str:
    """
    Create and save walkthrough for a session.

    Returns the walkthrough content.

    """
    content = generate_walkthrough(session_id, investigation_summary, fix_description)
    save_walkthrough(session_id, "P:/projects", investigation_summary, fix_description)
    return content


if __name__ == "__main__":
    # Self-test

    from rca.session import ProblemType, record_debug_start

    # Create test session
    session_id = record_debug_start(
        "Self-test walkthrough generation",
        ProblemType.ERROR
    )

    # Generate walkthrough
    walkthrough = generate_walkthrough(session_id)
    print(walkthrough)

    print("\n✅ Walkthrough generator self-test passed")

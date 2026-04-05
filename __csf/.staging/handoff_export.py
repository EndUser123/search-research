#!/usr/bin/env python3
"""
Generate LLM-ready handoff for pasting into another LLM chat.

Usage:
    python handoff_export.py                    # Output to terminal
    python handoff_export.py > handoff.txt      # Save to file
    python handoff_export.py --clipboard        # Copy to clipboard (Windows)
"""

import argparse
import json
import sys
from pathlib import Path

# Add handoff package to path
HANDOFF_PACKAGE = Path("P:/packages/handoff/src")
if str(HANDOFF_PACKAGE) not in sys.path:
    sys.path.insert(0, str(HANDOFF_PACKAGE))

from handoff.hooks.__lib.handoff_store import HandoffStore
from handoff.hooks.__lib.transcript import TranscriptParser
from handoff.hooks.__lib.handover import HandoverBuilder
from handoff.hooks.__lib.bridge_tokens import extract_bridge_tokens


def detect_terminal_id() -> str:
    import os
    if terminal_id := os.environ.get("CLAUDE_TERMINAL_ID"):
        return terminal_id
    if session_id := os.environ.get("CLAUDE_SESSION_ID"):
        return session_id
    return f"term_{os.getpid()}"


def find_transcript_path(project_root: Path) -> str | None:
    import glob
    import os
    project_conversations_dir = os.path.expanduser("~/.claude/projects/P--/")
    if not os.path.exists(project_conversations_dir):
        return None
    session_files = glob.glob(os.path.join(project_conversations_dir, "*.jsonl"))
    if not session_files:
        return None
    session_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    for f in session_files[:5]:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        if size_mb > 50 or "subagent" in f.lower():
            continue
        return f
    return None


def format_llm_prompt(handoff_data: dict) -> str:
    """Format handoff data as an LLM prompt."""

    bridge_tokens = extract_bridge_tokens(handoff_data)

    # Build the prompt
    lines = [
        "# Session Handoff from Claude Code",
        "",
        "You are receiving context from another LLM session. Below is the complete handoff data.",
        "",
        "## Quick Summary",
    ]

    # Basic info
    lines.append(f"- **Session**: {handoff_data.get('session_id', 'Unknown')}")
    lines.append(f"- **Timestamp**: {handoff_data.get('timestamp', 'Unknown')}")
    lines.append(f"- **Quality Score**: {handoff_data.get('quality_score', 0):.2f}/1.00 ({handoff_data.get('quality_rating', 'Unknown')})")

    # Blocker
    if blocker := handoff_data.get('blocker'):
        lines.append(f"- **Current Blocker**: {blocker.get('description', 'None')[:100]}...")

    # Bridge tokens
    if bridge_tokens:
        lines.append(f"- **Bridge Tokens**: {', '.join(bridge_tokens)}")

    lines.append("")

    # Last work
    if modifications := handoff_data.get('modifications'):
        lines.append("## Recent Work")
        for mod in modifications[-5:]:
            if file_path := mod.get('file'):
                lines.append(f"- Modified: `{file_path}`")
        lines.append("")

    # Next steps
    if next_steps := handoff_data.get('next_steps'):
        lines.append("## Next Steps")
        for i, step in enumerate(next_steps[:5], 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    # Key decisions with bridge tokens
    if handover := handoff_data.get('handover', {}):
        if decisions := handover.get('decisions', []):
            lines.append("## Key Decisions")
            for decision in decisions[:5]:
                topic = decision.get('topic', 'Unknown')
                bridge_token = decision.get('bridge_token', '')
                decision_text = decision.get('decision', '')[:150]
                lines.append(f"### {topic}")
                if bridge_token:
                    lines.append(f"**Bridge Token**: `{bridge_token}`")
                lines.append(f"{decision_text}...")
                lines.append("")

    # Full JSON data
    lines.append("---")
    lines.append("")
    lines.append("## Complete Handoff JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(handoff_data, indent=2, default=str))
    lines.append("```")
    lines.append("")

    # Instructions for receiving LLM
    lines.append("## Instructions for Continuing")
    lines.append("")
    lines.append("1. Review the quick summary above")
    lines.append("2. Check bridge tokens - respect decisions marked with them")
    lines.append("3. Note the quality score - if low, ask what needs documentation")
    lines.append("4. Continue based on next_steps or user's new request")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate LLM-ready handoff")
    parser.add_argument('--clipboard', action='store_true', help='Copy to clipboard (Windows only)')
    args = parser.parse_args()

    project_root = Path.cwd()

    # Generate handoff
    terminal_id = detect_terminal_id()
    transcript_path = find_transcript_path(project_root)

    parser_instance = TranscriptParser(transcript_path=transcript_path)
    handover_builder = HandoverBuilder(project_root=project_root, transcript_parser=parser_instance)
    handoff_store = HandoffStore(project_root=project_root, terminal_id=terminal_id)

    from datetime import UTC, datetime
    task_name = f"manual_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    blocker = parser_instance.extract_current_blocker()
    modifications = parser_instance.extract_modifications()

    next_steps_file = project_root / ".claude" / "next-steps.txt"
    if next_steps_file.exists():
        next_steps = [
            line.strip()
            for line in next_steps_file.read_text().split("\n")
            if line.strip() and not line.startswith("#")
        ][:5]
    else:
        next_steps = []

    handover = handover_builder.build(task_name)

    handoff_data = handoff_store.build_handoff_data(
        task_name=task_name,
        progress_pct=0,
        blocker=blocker,
        files_modified=[m.get("file", "") for m in modifications if m.get("file")],
        next_steps=next_steps,
        handover=handover,
        modifications=modifications,
        add_bridge_tokens=True,
        calculate_quality=True,
    )

    # Format for LLM
    prompt = format_llm_prompt(handoff_data)

    if args.clipboard:
        try:
            import subprocess
            subprocess.run(['clip'], input=prompt.encode(), check=True, shell=True)
            print("✅ Handoff copied to clipboard")
            print(f"   Quality Score: {handoff_data.get('quality_score', 0):.2f}")
            print(f"   Bridge Tokens: {extract_bridge_tokens(handoff_data)}")
        except (ImportError, OSError, subprocess.CalledProcessError):
            print("Failed to copy to clipboard. Output below:")
            print()
            print(prompt)
    else:
        print(prompt)


if __name__ == "__main__":
    main()

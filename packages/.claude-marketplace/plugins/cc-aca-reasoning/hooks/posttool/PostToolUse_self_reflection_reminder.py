

# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

#!/usr/bin/env python3
"""
Self-Reflection Reminder Hook (v3.1 - Count All History)
========================================================

Non-blocking advisory that reminds the agent to reflect on high-risk operations.

ZERO PERSISTENCE:
- Uses tool_use_history from hook input (already available)
- No state files
- No SessionStart hook needed
- No stale data possible
- Naturally multi-terminal safe (each terminal has its own history)

TRIGGERS:
- Multiple file modifications (>3 files) in this session
- Git push operations
- Destructive operations (rm, drop, delete, force push)
- Deployment operations

The actual self-reflection protocol is documented in CLAUDE.md under
"Self-Reflection for High-Risk Actions".

Author: CSF NIP
Version: 3.1.0
"""

import json
import re
import sys

# Risky operation patterns
RISKY_PATTERNS = {
    "git_push": r"git\s+(push.*--force|push\s+-f)",
    "destructive_write": r"(rm\s+-rf|rm\s+-r|drop\s+table|delete\s+from)",
    "deployment": r"(deploy|publish|release)",
    "database_write": r"(update\s+.*set\s+.*where|delete\s+from|drop\s+)",
}

MULTI_FILE_THRESHOLD = 3

def count_session_writes(tool_use_history: list) -> int:
    """Count ALL Write/Edit operations in this session."""
    if not tool_use_history:
        return 0

    seen_files = set()

    for entry in tool_use_history:  # ALL history, not just recent
        tool_name = entry.get("tool_name", "")
        if tool_name in ("Write", "Edit"):
            file_path = (
                entry.get("tool_input", {}).get("file_path") or
                entry.get("tool_input", {}).get("filePath", "")
            )
            # Count unique files
            if file_path and file_path not in seen_files:
                seen_files.add(file_path)

    return len(seen_files)

def check_risky_patterns(tool_name: str, tool_input: dict) -> list[str]:
    """Check if tool input matches risky operation patterns."""
    if tool_name != "Bash":
        return []

    command = tool_input.get("command", "")
    if not command:
        return []

    risks = []
    for risk_name, pattern in RISKY_PATTERNS.items():
        if re.search(pattern, command, re.IGNORECASE):
            risks.append(risk_name)

    return risks

def generate_advisor(risks: list[str], file_count: int = 0) -> str:
    """Generate advisory message based on detected risks."""
    lines = ["⚠️ Self-Reflection Reminder"]

    if file_count > MULTI_FILE_THRESHOLD:
        lines.append(f"• {file_count} files modified in this session")

    risk_messages = {
        "git_push": "• Force push operation detected",
        "destructive_write": "• Destructive operation (rm, drop, delete)",
        "deployment": "• Deployment/release operation",
        "database_write": "• Direct database write operation",
    }

    for risk in risks:
        if risk in risk_messages:
            lines.append(risk_messages[risk])

    lines.append("")
    lines.append("Consider the Self-Reflection Protocol in CLAUDE.md:")
    lines.append("1. Goal: What problem am I solving?")
    lines.append("2. Simplicity: What's the minimum viable change?")
    lines.append("3. Risk: What could go wrong? Is this reversible?")
    lines.append("4. Assumptions: What information do I lack?")
    lines.append("5. Alignment: Does this match the user's request?")

    return "\n".join(lines)

def main():
    """Main hook entry point."""
    # Read hook input from stdin
    input_data = json.load(sys.stdin)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_use_history = input_data.get("tool_use_history", [])

    # Check for risky conditions
    risks = check_risky_patterns(tool_name, tool_input)
    file_count = count_session_writes(tool_use_history)
    multi_file = file_count > MULTI_FILE_THRESHOLD

    # Generate advisory if risks detected
    if risks or multi_file:
        advisor = generate_advisor(risks, file_count)
        print("{}")
        sys.stderr.write(f"[advisory] {advisor}\n")
    else:
        # No risks, output empty JSON
        print(json.dumps({}))

if __name__ == "__main__":
    main()
"""
Post-response hook: blocks completion unless TDD validation passed.
v3.2: O(1) active session checks via .active_run pointer.
Multi-terminal isolated via run-id partitioned state files.
"""

import os
import sys
import json
from pathlib import Path

STATE_ROOT = Path(os.getcwd()) / ".claude-state" / "tdd"
ACTIVE_PTR = STATE_ROOT / ".active_run"


def main() -> None:
    # Consume stdin per hook contract
    _ = json.load(sys.stdin)

    if not ACTIVE_PTR.exists():
        print(json.dumps({"decision": "allow"}))
        return

    run_id = ACTIVE_PTR.read_text(encoding="utf-8").strip()
    run_dir = STATE_ROOT / run_id

    # Stale pointer: session directory no longer exists
    if not run_dir.exists():
        ACTIVE_PTR.unlink(missing_ok=True)
        print(json.dumps({"decision": "allow"}))
        return

    # If validated.json exists, validator just succeeded
    validated = run_dir / "validated.json"
    if validated.exists():
        ACTIVE_PTR.unlink(missing_ok=True)
        print(json.dumps({"decision": "allow"}))
        return

    # Also check session phase — must be "validated" to unlink pointer
    session_file = run_dir / "session.json"
    if session_file.exists():
        session_data = json.loads(session_file.read_text(encoding="utf-8"))
        if session_data.get("phase") == "validated":
            ACTIVE_PTR.unlink(missing_ok=True)
            print(json.dumps({"decision": "allow"}))
            return

    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    f"TDD session {run_id[:8]}… is still active.\n"
                    "You must:\n"
                    "1. Run RED via run_phase.py (failing tests).\n"
                    "2. Run GREEN via run_phase.py (passing tests).\n"
                    "3. (Optional) Run REFACTOR via run_phase.py.\n"
                    "4. Create evidence.json matching TddEvidence schema.\n"
                    f'5. Run: python .claude/skills/tdd/validate_tdd.py "{run_id}"'
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
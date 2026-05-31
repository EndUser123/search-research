

# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""
Pre-prompt hook: redirects TDD-like requests to /tdd skill.
v3.2: O(1) active session check via .active_run pointer.
Multi-terminal isolated via pointer file + run-id validation.
"""

import json
import os
import re
import sys
from pathlib import Path

STATE_ROOT = Path(os.getcwd()) / ".claude-state" / "tdd"
ACTIVE_PTR = STATE_ROOT / ".active_run"

_TDD_PATTERNS = re.compile(
    r"\b(?:write\s+tests?|test[- ]driven|tdd|add\s+test\s+coverage|"
    r"red[- ]green[- ]refactor|unit\s+tests?|integration\s+tests?|"
    r"test\s+first|failing\s+tests?\s+first)\b",
    re.IGNORECASE,
)

def main() -> None:
    payload = json.load(sys.stdin)
    prompt = payload.get("prompt") or ""

    # Already using /tdd or a session is active — allow
    if "/tdd" in prompt or ACTIVE_PTR.exists():
        print(json.dumps({"decision": "approve"}))
        return

    if _TDD_PATTERNS.search(prompt):
        escaped = prompt.replace('"', '\\"')
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "Detected a test-driven development request.\n"
                        "Re-run using the /tdd skill for strict "
                        "RED–GREEN–REFACTOR enforcement.\n"
                        f'/tdd feature "{escaped}"'
                    ),
                }
            )
        )
        return

    print(json.dumps({"decision": "approve"}))

if __name__ == "__main__":
    main()
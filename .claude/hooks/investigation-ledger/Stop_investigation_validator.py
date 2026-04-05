"""
Stop Hook: Investigation Validator
Blocks responses that make unsubstantiated claims or exceed confidence ceilings.

Integrates with Claude Code hook system via JSON stdin/stdout.
"""

import json
import os
import sys
from pathlib import Path

# Add ledger module to path
HOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR))

from validate_claims import validate_claims
from validate_confidence import validate_confidence


def main():
    """Main hook entry point."""
    # Check if investigation ledger is enabled
    if os.environ.get("INVESTIGATION_LEDGER_ENABLED", "true").lower() != "true":
        print(json.dumps({"continue": True}))
        return

    try:
        # Read hook input from stdin
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # No input - pass through
            print(json.dumps({"continue": True}))
            return

        hook_input = json.loads(raw_input)
        response_text = hook_input.get("response", "")

        if not response_text or len(response_text) < 50:
            # Empty or very short response - allow
            print(json.dumps({"continue": True}))
            return

        # Run validations
        claims_result = validate_claims(response_text)
        confidence_result = validate_confidence(response_text)

        # Check if either validation failed
        if not claims_result.get("valid", True):
            print(json.dumps({
                "decision": "block",
                "reason": claims_result.get("message", "Claims validation failed"),
                "details": claims_result.get("details", {})
            }))
            return

        if not confidence_result.get("valid", True):
            print(json.dumps({
                "decision": "block",
                "reason": confidence_result.get("message", "Confidence validation failed"),
                "details": confidence_result.get("details", {})
            }))
            return

        # All validations passed
        print(json.dumps({"continue": True}))

    except json.JSONDecodeError as e:
        # Invalid JSON input - log and continue
        print(json.dumps({
            "continue": True,
            "warning": f"Investigation validator: JSON parse error: {e}"
        }))
    except Exception as e:
        # Graceful degradation - don't block on validator errors
        print(json.dumps({
            "continue": True,
            "warning": f"Investigation validator error: {e}"
        }))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Bridge token expansion for external LLM handoffs.

Idea: Replace bridge tokens with full context when exporting to platforms
that don't have access to the local session history.

Example:
  Internal: BRIDGE_20260212-202702_HANDOFF
  External: "Decision made on 2026-02-12 at 20:27: Reconciled /hod skill with
            handoff package, adding quality scoring (30% completion, 25% outcomes,
            20% decisions, 15% issues, 10% knowledge), bridge tokens for
            cross-session continuity, and 90-day retention policy."
"""

from datetime import UTC, datetime
from typing import Any


def expand_bridge_token(decision: dict[str, Any]) -> str:
    """Expand a bridge token into a human-readable context string.

    Args:
        decision: Decision dict with bridge_token, timestamp, topic, decision

    Returns:
        Expanded context string replacing the token
    """
    token = decision.get("bridge_token", "")
    if not token:
        return decision.get("decision", "")

    # Parse token: BRIDGE_YYYYMMDD-HHMMSS_TOPIC
    parts = token.split("_")
    if len(parts) < 3:
        return decision.get("decision", "")

    try:
        # Extract timestamp from token
        dt = datetime.strptime(parts[1], "%Y%m%d-%H%M%S")
        dt = dt.replace(tzinfo=UTC)
        formatted_time = dt.strftime("%Y-%m-%d at %H:%M")

        # Extract topic
        topic = decision.get("topic", "Unknown")

        # Get decision summary (first 200 chars)
        decision_text = decision.get("decision", "")[:200]

        return f"""Decision made on {formatted_time} ({topic}):

{decision_text}...

[Reference: {token}]
"""
    except (ValueError, IndexError):
        return decision.get("decision", "")


def expand_all_bridge_tokens(handoff_data: dict[str, Any]) -> dict[str, Any]:
    """Replace bridge tokens with expanded context in handoff data.

    This creates a version suitable for external LLMs that don't have
    access to local session history or token lookup systems.

    Args:
        handoff_data: Original handoff data

    Returns:
        Handoff data with expanded bridge token context
    """
    # Create a copy to avoid mutating original
    expanded = handoff_data.copy()

    if "handover" not in expanded:
        return expanded

    handover = expanded["handover"].copy()
    if "decisions" not in handover:
        expanded["handover"] = handover
        return expanded

    # Expand each decision
    expanded_decisions = []
    for decision in handover["decisions"]:
        expanded_decision = decision.copy()

        if "bridge_token" in decision:
            # Add expanded context
            expanded_decision["expanded_context"] = expand_bridge_token(decision)
            # Keep original token for reference
            # expanded_decision.pop("bridge_token")  # Optional: remove original

        expanded_decisions.append(expanded_decision)

    handover["decisions"] = expanded_decisions
    expanded["handover"] = handover

    return expanded


# Example usage
if __name__ == "__main__":
    # Sample handoff data
    sample = {
        "session_id": "test_session",
        "handover": {
            "decisions": [
                {
                    "timestamp": "2026-02-12T20:27:02.507Z",
                    "topic": "handoff",
                    "bridge_token": "BRIDGE_20260212-202702_HANDOFF",
                    "decision": "Reconciled /hod skill with handoff package, adding quality scoring algorithm with 5 components (30% completion, 25% outcomes, 20% decisions, 15% issues, 10% knowledge), bridge tokens for cross-session continuity using format BRIDGE_YYYYMMDD-HHMMSS_TOPIC, and 90-day retention policy."
                }
            ]
        }
    }

    expanded = expand_all_bridge_tokens(sample)

    print("=== ORIGINAL ===")
    print(sample["handover"]["decisions"][0].get("bridge_token"))

    print("\n=== EXPANDED ===")
    print(expanded["handover"]["decisions"][0].get("expanded_context"))

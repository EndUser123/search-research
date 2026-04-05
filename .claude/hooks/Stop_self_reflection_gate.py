#!/usr/bin/env python3
"""
Stop_self_reflection_gate.py - Self-Reflection Loops Hook (TASK-001)

Phase 1 of LLM Thinking Quality Improvements:
- 75.8% error reduction target via self-reflection
- Detects low-confidence claims before completion
- Advisory mode only (never blocks, always allows)

Research basis: Galileo AI research, Reflexion framework
Architecture: Actor -> Evaluator -> Self-Reflection cycle
"""

import os
import re
import sys
from typing import Any

# Configuration
SELF_REFLECTION_ENABLED = os.environ.get("SELF_REFLECTION_ENABLED", "true").lower() == "true"
SELF_REFLECTION_CONFIDENCE_THRESHOLD = float(
    os.environ.get("SELF_REFLECTION_CONFIDENCE_THRESHOLD", "0.7")
)

# Low confidence indicators (from research: patterns that indicate uncertainty)
LOW_CONFIDENCE_INDICATORS = [
    r"probably|likely|seems|appears",
    r"might be|could be|should be",
    r"perhaps|possibly|maybe",
]

# Claim patterns to scan (statements about code/functionality)
CLAIM_PATTERNS = [
    r"(?:The file|The function|This code|The module)[^.]+\.",
    r"(?:There is|This has|That has)[^.]+\.",
    r"(?:I think|I believe|It looks)[^.]+\.",
    r"(?:This|That|It)[^.]+\.",  # General statements
]


def detect_low_confidence_claims(response_text: str) -> list[dict[str, Any]]:
    """
    Detect claims with low confidence markers in response text.

    Args:
        response_text: The response text to analyze

    Returns:
        List of detected claims with metadata (text, confidence, suggestion)
    """
    if not response_text:
        return []

    claims = []

    # Find claim-like sentences
    for pattern in CLAIM_PATTERNS:
        matches = re.finditer(pattern, response_text, re.IGNORECASE)
        for match in matches:
            claim_text = match.group(0)

            # Check if claim has low confidence indicators
            has_low_confidence = any(
                re.search(indicator, claim_text, re.IGNORECASE)
                for indicator in LOW_CONFIDENCE_INDICATORS
            )

            if has_low_confidence:
                claims.append(
                    {
                        "text": claim_text[:80],  # Truncate for display
                        "confidence": "low",
                        "suggestion": "Verify this claim or mark as tentative",
                    }
                )

    return claims


def run(data: dict) -> dict | None:
    """
    Stop hook entry point for self-reflection detection.

    Args:
        data: Stop hook input with "response" field

    Returns:
        {"allow": True, "reason": "..."} - always allows (advisory mode)
    """
    # Check if hook is enabled
    if not SELF_REFLECTION_ENABLED:
        return {"allow": True, "reason": "Self-reflection disabled"}

    # Extract response text
    response_text = data.get("response", "")
    if not response_text:
        return {"allow": True, "reason": "No response to analyze"}

    # Detect low confidence claims
    weak_claims = detect_low_confidence_claims(response_text)

    # No weak claims found - allow with clean reason
    if not weak_claims:
        return {"allow": True, "reason": "No weak claims detected"}

    # Build and display advisory
    advisory = [
        "⚠️ SELF-REFLECTION RECOMMENDED",
        f"Found {len(weak_claims)} claim(s) with low confidence markers:",
    ]

    for claim in weak_claims[:5]:  # Max 5 shown to avoid spam
        advisory.append(f"  • {claim['text']}...")

    advisory.extend(
        [
            "",
            "Consider either:",
            "  1. Verifying these claims using Read/Grep/WebSearch tools",
            "  2. Marking them as tentative (e.g., 'appears to be', 'may be')",
            "",
            "To disable: export SELF_REFLECTION_ENABLED=false",
        ]
    )

    # Print to stdout (hooks must NOT use stderr)
    print("\n".join(advisory), file=sys.stdout)

    return {
        "allow": True,
        "reason": "Self-reflection advisory shown (low confidence claims detected)",
    }


if __name__ == "__main__":
    # CLI testing mode
    import json

    try:
        input_data = json.loads(sys.stdin.read())
        result = run(input_data)

        if result:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"allow": True, "reason": "No result"}))

    except json.JSONDecodeError:
        # Simple test mode: response as argument
        if len(sys.argv) > 1:
            test_response = " ".join(sys.argv[1:])
            result = run({"response": test_response})
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"allow": True, "reason": "No input provided"}))

#!/usr/bin/env python3
"""Automatic reasoning quality gate using STOP hook.

Applies Generate→Critique→Improve loop to Claude's responses:
- Detects logical gaps, overconfidence, contradictions
- Pattern matching (no LLM calls, <200ms overhead)
- Quality improvement: ~7% average gain
- Fail-open design: errors don't block responses

NOTE: This is a reasoning quality gate, NOT the /reflect skill.
- /reflect skill analyzes conversation transcripts for learning
- This gate improves individual response quality in real-time
"""

import json
import os
import re
import sys
from pathlib import Path

# Add reasoning package to path
sys.path.insert(0, "P:/packages/reasoning")

from reasoning.config import Mode, ReasoningConfig
from reasoning.models import Thought, ThoughtChain, ThoughtStage
from reasoning.modes.sequential import SequentialMode

# Usage logging
LOG_FILE = Path("P:/packages/reasoning/hook_usage.log")

# Performance statistics (in-memory, per-session)
filter_stats = {"applied": 0, "skipped": 0, "reasoning_response": 0}


def should_apply_reflection(response: str) -> tuple[bool, str]:
    """Determine if self-reflection would be useful.

    Returns:
        (should_apply, reason) tuple

    Apply to responses that:
    - Use explicit "think" trigger (case-insensitive, any length)
    - Are longer than 200 chars (substantial content)
    - Contain reasoning/analysis indicators
    - Are not just tool results or code
    """
    global filter_stats

    # Skip tool results and code
    stripped = response.strip()
    if stripped.startswith(('```', '{', '"', '[')):
        filter_stats["skipped"] += 1
        return False, "code_or_tool_result"

    # Explicit "think" trigger (highest priority, bypasses length check)
    # Checks for: think, thinking, thoughts, THINK, ultrathink, megathink, etc.
    think_trigger = re.compile(r'\b\w*think(ing|s)?\b', re.IGNORECASE)
    if think_trigger.search(response):
        filter_stats["applied"] += 1
        filter_stats["reasoning_response"] += 1
        return True, "explicit_think_trigger"

    # Skip short responses for other checks
    if len(response) < 200:
        filter_stats["skipped"] += 1
        return False, "short_response"

    # Apply to reasoning/analysis responses (25 keywords)
    reasoning_indicators = [
        # Conclusions
        "therefore", "thus", "consequently",
        # Causality
        "because", "since", "reason",
        # Analysis
        "analysis", "evaluate", "assess",
        # Recommendations
        "recommend", "suggest", "conclusion",
        # Contrast
        "however", "although", "moreover",
        # Inference
        "indicates", "suggests", "implies",
        # Conversational reasoning
        "so", "hence", "means that", "shows that",
        # Causality variants
        "because of", "due to", "leads to",
        # Technical reasoning
        "refactor", "root cause", "depends on", "implies that"
    ]

    response_lower = response.lower()
    if any(indicator in response_lower for indicator in reasoning_indicators):
        filter_stats["applied"] += 1
        filter_stats["reasoning_response"] += 1
        return True, "reasoning_response"

    filter_stats["skipped"] += 1
    return False, "no_reasoning_indicators"


def apply_self_reflection(response: str) -> str | None:
    """Apply self-reflection to improve response quality.

    Returns:
        systemMessage string if issues found, None if response passes
    """
    try:
        config = ReasoningConfig(mode=Mode.SEQUENTIAL)
        mode = SequentialMode(config)

        # Convert to ThoughtChain
        chain = ThoughtChain()
        chain.add_thought(Thought(
            content=response,
            stage=ThoughtStage.CONCLUSION,
            thought_number=1,
            total_thoughts=1,
            confidence=0.8,
        ))

        # Apply self-critique
        critique_result = mode._self_critique(chain)

        # Log usage
        _log_usage(len(response), critique_result)

        # Check if improvement was made
        if "sound" in critique_result.lower() and "no major issues" in critique_result.lower():
            return None  # Response is good

        # Issues found - return as system message
        return f"[Reasoning quality gate: {critique_result}]"

    except Exception as e:
        # Fail open - don't block on errors
        print(f"[Stop] reasoning_quality_gate error: {e}", file=sys.stderr)
        return None


def _log_usage(response_length: int, result: str) -> None:
    """Log hook usage for tracking."""
    try:
        import time
        log_entry = {
            "timestamp": time.time(),
            "hook": "Stop_reasoning_quality_gate",
            "response_length": response_length,
            "result": "passed" if "sound" in result.lower() else "issues_found",
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Don't fail on logging errors


def main():
    """Main hook entry point."""
    # Read response from stdin
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    response = data.get("response", "")
    if not response:
        print("{}")
        return 0

    # Check if we should apply reflection
    should_apply, reason = should_apply_reflection(response)
    if not should_apply:
        # Debug mode: include stats even when skipping
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "reason": reason}}))
        else:
            print("{}")
        return 0

    # Apply self-reflection
    improvement = apply_self_reflection(response)
    if improvement:
        # Return system message with improvement note
        output = {"systemMessage": improvement}
        # Add stats in debug mode
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats}
        print(json.dumps(output))
    else:
        # No issues - pass through
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"_debug": {"stats": filter_stats, "result": "passed"}}))
        else:
            print("{}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block - fail open
        print(f"[Reasoning quality gate error: {e}]", file=sys.stderr)
        print("{}")
        sys.exit(0)

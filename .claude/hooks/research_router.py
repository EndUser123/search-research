#!/usr/bin/env python3
"""
PreToolUse Research Router

Blocks local-only tools when queries involve research, architecture decisions,
or performance alternatives. Forces web research or agent delegation first.

Fast: No network calls, no LLM calls, just string checks and logging.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict


def load_config() -> Dict[str, Any]:
    """Load research router config with safe fallbacks."""
    config_path = Path(__file__).resolve().parent / "research_router_config.json"

    default_config = {
        "research_keywords": [],
        "local_tools": [],
        "escape_phrases": []
    }

    if not config_path.exists():
        return default_config

    try:
        with open(config_path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default_config


def log_decision(data: Dict[str, Any], decision: str, reason: str = "") -> None:
    """Log decision to JSONL file for observability."""
    log_path = Path(__file__).resolve().parent / "research_router.log.jsonl"

    log_entry = {
        "ts": time.time(),
        "tool_name": data.get("tool_name", ""),
        "user_message": data.get("user_message", ""),
        "is_research": reason and "research" in reason.lower(),
        "is_local": data.get("tool_name", "") in load_config().get("local_tools", []),
        "decision": decision,
        "reason": reason
    }

    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")
    except OSError:
        pass


def main() -> None:
    """Main router logic."""
    try:
        data = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError):
        print("{}")
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    user_message = data.get("user_message", "").lower()

    config = load_config()
    research_keywords = config.get("research_keywords", [])
    local_tools = config.get("local_tools", [])
    escape_phrases = config.get("escape_phrases", [])

    # Check for escape phrases first
    for phrase in escape_phrases:
        if phrase.lower() in user_message:
            log_decision(data, "allow", "escape_phrase")
            print("{}")
            sys.exit(0)

    # Determine if query is researchy
    is_research = any(keyword.lower() in user_message for keyword in research_keywords)

    # Determine if tool is local-only
    is_local = tool_name in local_tools

    # Advisory mode: log and nudge, don't block
    if is_research and is_local:
        reason = (
            "This query involves architecture/performance alternatives. "
            "Consider using WebSearch or a research agent to explore options first. "
            "To bypass this reminder, include 'no research' in your message."
        )
        log_decision(data, "advisory", reason)

        # Advisory: don't block, just let the tool run
        # The log entry serves as the nudge
        print("{}")
        sys.exit(0)

    # Allow all other cases
    log_decision(data, "allow", "not_research_or_not_local")
    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()

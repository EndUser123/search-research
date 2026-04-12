#!/usr/bin/env python3
"""PreToolUse Domain Tool Router Hook.

Advisory hook that suggests domain-specific tools (/search, /chs, /cks) based on
query pattern detection. Non-blocking - provides suggestions to improve search
effectiveness.

GREENFIELD: New hook implementation for query classification and tool routing.
Existing pattern detectors (narrative_intent_detector.py) serve different purposes:
- Post-facto response analysis for design-intent claims (STOP hook)
- This module: Pre-execution query classification for tool routing (PRETOOLUSE hook)
"""

from __future__ import annotations

import json
import re
import sys

# Pattern definitions for query classification
# Chat history patterns: conversational, temporal, pronoun-based
CHAT_HISTORY_PATTERNS = [
    r"\bwe\s+(?:discussed|said|talked|decided|agreed|mentioned)\b",
    r"\bwhat\s+(?:did|do)\s+(?:we|you)\s+(?:discuss|say|talk|mean)\b",
    r"\byou\s+(?:mentioned|said|told|asked)\b",
    r"\b(?:earlier|yesterday|recent|today|last\s+week|before)\b",
    r"\b(?:our|my|the)\s+(?:conversation|discussion|chat)\b",
]

# Web source patterns: documentation, tutorials, procedural
WEB_SOURCE_PATTERNS = [
    r"\b(?:how\s+(?:to|does|do)|tutorial|guide|documentation|docs?|readme)\b",
    r"\b(?:explain|describe|overview)\s+(?:how|what|where|when)\b",
    r"\b(?:python|javascript|typescript|\w+)\s+(?:package|module|library|work)\b",
    r"\b(?:api|endpoint|route)\s+(?:documentation|reference)\b",
]

# Knowledge patterns: architectural decisions, patterns, lessons
# These patterns are more specific to avoid false positives on common words
KNOWLEDGE_PATTERNS = [
    r"\b(?:best\s+)?(?:practice|principle|convention)\s+(?:for|of|in)\b",
    r"\b(?:design|architectural)\s+(?:pattern|decision|choice)\b",
    r"\b(?:rationale|reasoning)\s+(?:behind|for|about)\b",
    r"\b(?:lesson|learning|insight)\s+(?:learned|from|gained)\b",
    r"\b(?:knowledge|cks|pattern)\s+(?:entry|base|memory)\b",
]

# Combined search patterns: cross-reference, evolution, validation
COMBINED_PATTERNS = [
    r"\b(?:compare|versus|vs|vs\.|against|versus)\b",
    r"\b(?:evolved|changed|updated)\s+(?:over|from|since)\b",
    r"\b(?:validation|verify|confirm)\s+(?:against|with)\b",
]

# Compiled regex patterns
_CHAT_RE = re.compile("|".join(f"(?:{p})" for p in CHAT_HISTORY_PATTERNS), re.IGNORECASE)
_WEB_RE = re.compile("|".join(f"(?:{p})" for p in WEB_SOURCE_PATTERNS), re.IGNORECASE)
_KNOWLEDGE_RE = re.compile("|".join(f"(?:{p})" for p in KNOWLEDGE_PATTERNS), re.IGNORECASE)
_COMBINED_RE = re.compile("|".join(f"(?:{p})" for p in COMBINED_PATTERNS), re.IGNORECASE)


def detect_chat_history(query: str) -> bool:
    """Check if query indicates chat history search intent."""
    return bool(_CHAT_RE.search(query))


def detect_web_source(query: str) -> bool:
    """Check if query indicates web source/documentation search intent."""
    return bool(_WEB_RE.search(query))


def detect_knowledge(query: str) -> bool:
    """Check if query indicates knowledge base search intent."""
    return bool(_KNOWLEDGE_RE.search(query))


def detect_combined_search(query: str) -> bool:
    """Check if query indicates combined multi-source search intent."""
    return bool(_COMBINED_RE.search(query))


def classify_query(query: str) -> str | None:
    """Classify query into domain tool recommendation.

    Returns:
        "chat" - Use /search with --source chat (or /chs directly)
        "web" - Use /search with --source web
        "knowledge" - Use /search with --source web (or /cks directly)
        "combined" - Use /search with --source all
        None - No specific recommendation
    """
    if detect_combined_search(query):
        return "combined"
    if detect_chat_history(query):
        return "chat"
    if detect_web_source(query):
        return "web"
    if detect_knowledge(query):
        return "knowledge"
    return None


def build_suggestion(classification: str, query: str) -> str:
    """Build advisory suggestion message based on query classification."""
    suggestions = {
        "chat": (
            '💡 Try: /search "{}" --source chat\n'
            "This query mentions conversation/history. "
            "Chat history search will find relevant discussions."
        ),
        "web": (
            '💡 Try: /search "{}" --source web\n'
            "This query asks for documentation/tutorials. "
            "Web source search will find relevant docs and guides."
        ),
        "knowledge": (
            '💡 Try: /search "{}" --source web\n'
            "This query relates to patterns/decisions. "
            "Knowledge base search will find relevant CKS entries."
        ),
        "combined": (
            '💡 Try: /search "{}" --source all\n'
            "This query crosses multiple domains. "
            "Combined search will check chat, docs, and knowledge."
        ),
    }
    return suggestions.get(classification, "").format(query[:50])


def extract_query(tool_name: str, tool_input: dict) -> str:
    """Extract query string from various tool inputs."""
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Use full command for pattern matching (context matters)
        return command[:200]  # First 200 chars for pattern matching

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return pattern

    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        return file_path

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return pattern

    elif tool_name == "Skill":
        # Skill tool invocation: extract skill name and args for routing suggestions
        skill = tool_input.get("skill", "")
        args = tool_input.get("args", "")
        # Combine skill name + args for search-relevant pattern detection
        combined = f"{skill} {args}".strip()
        return combined[:200]

    return ""


def main() -> None:
    """Main hook entry point."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Extract query from tool input
        query = extract_query(tool_name, tool_input)
        if not query or len(query) < 3:
            # No meaningful query, allow without suggestion
            print(json.dumps({"decision": "approve"}))
            return

        # Classify query and build suggestion
        classification = classify_query(query)
        if classification:
            advisory = build_suggestion(classification, query)
            print(json.dumps({"decision": "approve", "hookSpecificOutput": {"advisory": advisory}}))
        else:
            # No specific recommendation
            print(json.dumps({"decision": "approve"}))

    except Exception as e:
        # Fail open - don't block on errors
        print(json.dumps({"decision": "approve", "error": str(e)}), file=sys.stderr)


if __name__ == "__main__":
    main()

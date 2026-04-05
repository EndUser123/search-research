#!/usr/bin/env python3
"""Context Summary Injection Hook

Extracts key facts from last 5 conversation turns and injects at context top.
Makes invisible context visible to reduce context_reuse violations.

Principle: Extraction-only, no generation (prevents hallucination).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Configuration
NUM_TURNS = 5  # Number of recent turns to summarize
MAX_FACTS = 7  # Maximum key facts to extract
TOKEN_BUDGET = 800  # Max tokens for summary


def _should_trigger(context: HookContext) -> bool:
    """Check if context summary should be injected.

    Only trigger if:
    1. Enabled via environment
    2. Transcript path available
    3. Not a slash command (those have their own context)
    """
    # Check if enabled
    if os.environ.get("CONTEXT_SUMMARY_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return False

    # Check if transcript available
    transcript_path = context.data.get("transcript_path")
    if not transcript_path:
        return False

    # Skip slash commands (they have skill-specific context)
    prompt = context.prompt.strip()
    if re.match(r"^/\w+", prompt):
        return False

    # Skip very short prompts (likely continuations, not new questions)
    if len(prompt.split()) < 3:
        return False

    return True


def _read_transcript(transcript_path: str, max_turns: int = NUM_TURNS) -> list[dict]:
    """Read last N turns from transcript JSONL.

    Args:
        transcript_path: Path to transcript JSONL file
        max_turns: Maximum number of turns to extract

    Returns:
        List of turns in reverse chronological order (newest first)
    """
    try:
        path = Path(transcript_path)
        if not path.exists():
            return []

        # Read all lines
        lines = path.read_text(encoding="utf-8").strip().split("\n")

        # Parse JSONL (most recent at end)
        turns = []
        for line in reversed(lines):
            try:
                turn = json.loads(line.strip())
                if turn.get("role") in ("user", "assistant"):
                    turns.append(turn)
                    if len(turns) >= max_turns * 2:  # user + assistant = 1 turn
                        break
            except json.JSONDecodeError:
                continue

        return turns

    except Exception:
        # Fail silently - transcript issues shouldn't break hook
        return []


def _extract_key_facts(turns: list[dict]) -> list[str]:
    """Extract key facts from turns using keyword patterns.

    Uses extraction-only approach (no LLM generation) to prevent hallucination.
    Looks for factual statements: decisions, preferences, constraints, definitions.

    Args:
        turns: List of turn dictionaries from transcript

    Returns:
        List of key fact strings
    """
    if not turns:
        return []

    facts = []
    seen_patterns = set()

    # Pattern heuristics for factual statements
    factual_patterns = [
        # Decisions/choices
        (r"(?:we'll|we'll|i'll|i will|let's|going to)\s+(?:use|implement|choose|go with)\s+(\w.+)", "decision"),
        # Preferences
        (r"(?:i prefer|prefer|lets|let's)\s+(\w.+)", "preference"),
        # Constraints
        (r"(?:must|should|need to|required)\s+(?:not\s+)?(\w.+)", "constraint"),
        # Definitions
        (r"(\w+(?:\s+\w+)?)\s+(?:is|means?|refers to)\s+(\w.+)", "definition"),
        # File paths
        (r"[\w./]+/\w+(?:\.\w+)?", "file"),
        # API/endpoints
        (r"(?:POST|GET|PUT|DELETE|PATCH)\s+/\S+", "api"),
        # Configuration
        (r"(?:set|config|setting)\s+(\w+)\s*(?:to|=)\s*(\w+)", "config"),
    ]

    # Process turns (reversed = oldest to newest)
    for turn in reversed(turns):
        content = turn.get("content", "")
        if not content:
            continue

        # Extract sentences
        sentences = re.split(r"[.!?]+", content)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 200:
                continue

            # Check against patterns
            for pattern, fact_type in factual_patterns:
                try:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        fact = sentence.capitalize()

                        # Deduplicate
                        fact_key = fact.lower()[:50]
                        if fact_key in seen_patterns:
                            continue
                        seen_patterns.add(fact_key)

                        facts.append(f"• {fact}")

                        if len(facts) >= MAX_FACTS:
                            return facts

                        break  # Only count first match per sentence
                except re.error:
                    continue

    return facts


def _format_summary(facts: list[str]) -> str:
    """Format key facts as context injection.

    Args:
        facts: List of key fact strings

    Returns:
        Formatted context text
    """
    if not facts:
        return ""

    lines = [
        "## 📋 KEY FACTS FROM RECENT CONVERSATION",
        "",
        "Before asking questions, check if the information you need is already here:",
        "",
    ]

    lines.extend(facts[:MAX_FACTS])

    lines.extend([
        "",
        "---",
        "*Reusing context saves time and reduces repetition.*",
        "",
    ])

    return "\n".join(lines)


def context_summary_hook(context: HookContext) -> HookResult:
    """Inject context summary from recent conversation turns.

    This hook extracts key facts from the last 5 conversation turns and
    injects them at the top of context to reduce redundant questions.
    """
    # Fast path: check if should trigger
    if not _should_trigger(context):
        return HookResult.empty()

    # Read transcript
    transcript_path = context.data.get("transcript_path", "")
    turns = _read_transcript(str(transcript_path), max_turns=NUM_TURNS)

    if not turns:
        return HookResult.empty()

    # Extract key facts
    facts = _extract_key_facts(turns)

    if not facts:
        return HookResult.empty()

    # Format summary
    summary = _format_summary(facts)

    if not summary:
        return HookResult.empty()

    # Check token budget
    estimated_tokens = len(summary.split())
    if estimated_tokens > TOKEN_BUDGET:
        # Truncate if over budget
        summary = "\n".join(summary.split("\n")[:TOKEN_BUDGET // 10]) + "\n... [truncated]"

    return HookResult(
        context=summary,
        tokens=estimated_tokens,
        priority=4.0,  # Run early (before most other hooks)
    )


# Register hook
# Note: Priority 4.0 = run early to provide context before other hooks
register_hook("context_summary")(context_summary_hook)

"""Generate conversation summaries via LLM, stored in sessions.summary_short."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SUMMARIZER_PROMPT = """Given this Claude Code conversation, write a 1-sentence summary (max 80 chars) covering the main topic or goal. Focus on what was decided, built, or debugged.

Recent messages:
{preview}

Summary (1 sentence, max 80 chars):"""


async def generate_session_summary(
    messages: list[dict],
    max_preview_chars: int = 600,
) -> str:
    """Generate a short summary of a conversation session.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_preview_chars: Truncation limit for message preview

    Returns:
        1-sentence summary string (max 80 chars)
    """
    import core.llm.provider_manager as pm
    generate_with_fallback = pm.generate_with_fallback

    # Build preview from last 3 messages
    preview_parts = []
    for msg in messages[-3:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")[:200]
        preview_parts.append(f"{role}: {content}")
    preview = "\n".join(preview_parts)[:max_preview_chars]

    prompt = SUMMARIZER_PROMPT.format(preview=preview)
    summary, success = await generate_with_fallback(
        prompt=prompt,
        max_tokens=100,
        temperature=0.3,  # Low temp for consistent summarization
    )
    if not success:
        logger.warning("Summary generation failed, using placeholder")
        return "[summary unavailable]"
    return summary.strip()[:255]  # Match sessions.summary_short limit

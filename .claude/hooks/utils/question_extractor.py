"""Extract pending questions from transcript for S1.5 openquestions field."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PendingQuestion:
    question: str
    context: str
    timestamp: str
    turn_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "context": self.context,
            "timestamp": self.timestamp,
        }


def extract_text_from_message(msg: dict) -> str:
    """Extract text content from a message dict."""
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "")
    elif isinstance(content, str):
        return content
    return ""


def is_substantive_answer(text: str) -> bool:
    """Check if text is a substantive answer (>50 chars, not meta)."""
    if not text or len(text.strip()) < 50:
        return False
    # Meta responses that don't constitute an answer
    meta_phrases = [
        "let me", "i'll check", "i'll investigate", "i'll look",
        "i need to", "i'm not sure", "i don't know", "i'll get back",
        "i don't have", "i can't tell", "that's a good question",
        "let me think", "let me search", "checking", "investigating",
    ]
    lower = text.lower().strip()
    if any(lower.startswith(p) for p in meta_phrases):
        return False
    return True


def has_context_pronoun(text: str) -> bool:
    """Check if text contains pronouns requiring context.

    Rules:
    - "it", "that", "them", "those", "they" -> always requires context
    - "this" -> requires context only when standalone (no noun following)
    """
    pronoun_words = {"it", "that", "them", "those", "they"}
    determiner_words = {"this", "these"}
    lower = text.lower()
    words = re.split(r"\W+", lower)
    for word in words:
        if word in pronoun_words:
            return True
        if word in determiner_words:
            # Check if a noun immediately follows
            idx = words.index(word)
            if idx + 1 < len(words):
                next_word = words[idx + 1]
                # Nouns/verbs rarely follow "this" when it's a determiner
                # Skip detection if "this"/"these" is followed by a noun-like word
                noun_like = len(next_word) > 3 and not next_word.endswith("?")
                if noun_like:
                    continue
            return True
    return False


def extract_pending_questions(
    transcript_path: str | Path | None,
    max_questions: int = 3,
) -> list[dict[str, Any]]:
    """Extract unanswered user questions from transcript.

    Algorithm:
    1. Parse transcript entries in chronological order
    2. For each user message containing '?':
       - Mark as pending question
       - Extract context from preceding message if needed
    3. For each assistant message after a pending question:
       - If substantive response (>50 chars, not meta), mark question answered
       - If meta/clarification only, keep question pending
    4. Return top N most recent pending questions

    Args:
        transcript_path: Path to transcript JSONL
        max_questions: Maximum questions to return (default 3)

    Returns:
        List of dicts with keys: question, context, timestamp
    """
    if not transcript_path:
        return []

    path = Path(transcript_path)
    if not path.exists():
        return []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    entries: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return []

    # Build chronological list of (index, role, text, timestamp)
    message_log: list[tuple[int, str, str, str]] = []
    for i, entry in enumerate(entries):
        role = entry.get("type", "")
        if role not in ("user", "assistant"):
            continue
        text = extract_text_from_message(entry)
        if not text:
            continue
        timestamp = entry.get("timestamp", "")
        message_log.append((i, role, text, timestamp))

    # Find user questions (messages with '?' but not '...')
    pending: list[PendingQuestion] = []
    for idx, (orig_idx, role, text, timestamp) in enumerate(message_log):
        if role != "user":
            continue
        if "?" not in text:
            continue
        # Skip ellipsis-only questions
        if text.strip().endswith("..."):
            continue

        question_text = text.strip()
        context = ""

        # Extract context if question has pronouns
        if has_context_pronoun(question_text):
            # Look back up to 5 messages for substantive context
            for prev_orig_idx, prev_role, prev_text, _ in reversed(message_log[:idx]):
                if len(prev_text) > 20:  # Substantive
                    context = prev_text[:200]
                    if len(prev_text) > 200:
                        context = prev_text[:200] + "..."
                    break

        pending.append(PendingQuestion(
            question=question_text[:200],  # Cap at 200 chars
            context=context,
            timestamp=timestamp,
            turn_index=orig_idx,
        ))

    # Now check which questions were answered
    # For each pending question, look at subsequent assistant messages
    final_pending: list[PendingQuestion] = []
    for pq in pending:
        # Find position in message_log
        pq_pos = None
        for i, (orig_idx, _, _, _) in enumerate(message_log):
            if orig_idx == pq.turn_index:
                pq_pos = i
                break

        if pq_pos is None:
            continue

        # Check subsequent messages for substantive answer
        answered = False
        for i in range(pq_pos + 1, len(message_log)):
            _, role, text, _ = message_log[i]
            if role == "assistant" and is_substantive_answer(text):
                answered = True
                break

        if not answered:
            final_pending.append(pq)

    # Return top N most recent (already in chronological order from message_log)
    # Most recent = last in pending list
    result = [pq.to_dict() for pq in final_pending[-max_questions:]]
    return result
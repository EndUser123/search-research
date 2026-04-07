#!/usr/bin/env python3
"""
Context Follow-up Detector - UserPromptSubmit Hook
================================================

Detects follow-up vs standalone queries using fragment/pronoun patterns.
Loads prior context from terminal-scoped state file.

Per ADR-20260325: Self-Correcting Agent Loop.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# State directory - use hooks/state not UserPromptSubmit_modules/state
_HOOKS_DIR = Path(__file__).resolve().parent.parent
_STATE_DIR = _HOOKS_DIR / "state"

# Context window size
_CONTEXT_WINDOW = 10

# Keywords configuration path
_KEYWORDS_PATH = Path(__file__).resolve().parent.parent.parent / "skills" / "context_keywords.json"

# Fragment patterns indicating follow-up query
# NEGATIVE patterns indicate NEW topic (not a follow-up) - checked first
NEGATIVE_PATTERNS = [
    re.compile(
        r"^\s*What\s+about\s+[A-Z]", re.IGNORECASE
    ),  # "What about Paris..." (capital = specific entity)
    re.compile(
        r"^\s*How\s+about\s+", re.IGNORECASE
    ),  # "How about we..." = suggestion for new topic
    re.compile(r"^\s*I\s+want\s+to\s+", re.IGNORECASE),  # "I want to..." = new task
    re.compile(r"^\s*I\s+need\s+to\s+", re.IGNORECASE),  # "I need to..." = new task
    re.compile(r"^\s*Can\s+you\s+", re.IGNORECASE),  # "Can you..." = new request
]

FRAGMENT_PATTERNS = [
    re.compile(r"\bif\s+that[\'\"']?s?\b", re.IGNORECASE),
    # Narrow "what about": only follow-up if lowercase word/pronoun before, or sentence-internal
    # False positive: "What about Python?" (new topic) vs "what about it?" (follow-up)
    re.compile(r"(?<![A-Z])\bwhat\s+about\b(?!\s+[A-Z])", re.IGNORECASE),
    re.compile(r"\balso\b.*\b(and\s+)?the\s+other\b", re.IGNORECASE),
    re.compile(r"\b(what|which|how)\s+(else|about)\b", re.IGNORECASE),
]

# Pronoun patterns at sentence start (only these indicate follow-up)
# NOT mid-sentence pronouns like "Run it", "Fix that"
PRONOUN_START_PATTERNS = [
    re.compile(r'^"?(It|That|This|He|She|They|We|There)\b', re.IGNORECASE),
]

# Short recommendation/optimization queries that should inherit the active subject
# when substantive prior context exists. These are follow-up retrieval signals, not
# standalone vague prompts, as long as there is recent session context to attach to.
OPTIMIZATION_FOLLOWUP_PATTERNS = [
    re.compile(r"^\s*what(?:'s| is)\s+the\s+optimal\s+solution\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:'s| is)\s+the\s+best\s+approach\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:'s| is)\s+the\s+best\s+path\b", re.IGNORECASE),
    re.compile(r"^\s*what\s+should\s+we\s+do\b", re.IGNORECASE),
    re.compile(r"^\s*what\s+do\s+you\s+recommend\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:'s| is)\s+your\s+recommendation\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:'s| is)\s+the\s+recommended\s+path\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:'s| is)\s+the\s+optimal\s+long\s+term\s+fix\b", re.IGNORECASE),
]

_FOLLOWUP_CONTEXT_TTL_SECONDS = 4 * 60 * 60


def _get_terminal_id(data: dict) -> str:
    """Resolve terminal_id from data or environment."""
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or ""
    )
    return str(terminal_id).strip() if terminal_id else ""


def _normalize_terminal_id(terminal_id: str) -> str:
    """Normalize terminal_id for state file path, with cross-prefix fallback.

    If terminal_id starts with 'env_' and state file not found, retry with 'console_'.
    If starts with 'console_' and not found, retry with 'env_'.
    """
    if not terminal_id:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)


def _get_state_file_path(terminal_id: str) -> Path:
    """Get absolute state file path using __file__ resolution."""
    return _STATE_DIR / f"followup_context_{terminal_id}.json"


def _load_prior_context(terminal_id: str) -> dict | None:
    """Load prior context from state file with cross-prefix fallback.

    Returns None if file missing or corrupted (fail-open).
    """
    normalized = _normalize_terminal_id(terminal_id)
    state_file = _get_state_file_path(normalized)

    # Cross-prefix fallback: try alternate prefix if primary not found
    if not state_file.exists():
        if normalized.startswith("env_"):
            alt_normalized = "console_" + normalized[4:]
        elif normalized.startswith("console_"):
            alt_normalized = "env_" + normalized[7:]
        else:
            alt_normalized = None

        if alt_normalized:
            alt_path = _get_state_file_path(alt_normalized)
            if alt_path.exists():
                state_file = alt_path

    if not state_file.exists():
        return None

    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable - fail-open, proceed as standalone
        return None


def _save_prior_context(terminal_id: str, context: dict) -> None:
    """Save context to state file atomically via temp file + os.replace()."""
    normalized = _normalize_terminal_id(terminal_id)
    state_file = _get_state_file_path(normalized)

    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = state_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(context, f, separators=(",", ":"))
        os.replace(tmp_file, state_file)
    except OSError:
        # Atomic write failed - fail silently (non-critical)
        pass


def _is_followup_query(prompt: str, prior_context: dict | None = None) -> tuple[bool, str]:
    """Detect if prompt is a follow-up query.

    Returns (is_followup, matched_pattern).

    Args:
        prompt: The user's prompt text
        prior_context: Optional prior context dict for topic-change detection
    """
    prompt_stripped = prompt.strip()

    # Check NEGATIVE patterns first - these indicate NEW topic, not follow-up
    for pattern in NEGATIVE_PATTERNS:
        if pattern.match(prompt_stripped):
            return False, f"negative:{pattern.pattern}"

    # Check fragment patterns
    for pattern in FRAGMENT_PATTERNS:
        if pattern.search(prompt_stripped):
            return True, pattern.pattern

    # Short optimization/recommendation questions should inherit recent session
    # context rather than forcing the skill to ask for a subject the transcript
    # already makes obvious.
    if prior_context:
        topic = str(prior_context.get("topic", "")).strip()
        summary = str(prior_context.get("summary", "")).strip()
        timestamp = prior_context.get("timestamp")
        is_recent = True
        if isinstance(timestamp, int | float):
            is_recent = (time.time() - float(timestamp)) <= _FOLLOWUP_CONTEXT_TTL_SECONDS

        if is_recent and (topic or summary):
            for pattern in OPTIMIZATION_FOLLOWUP_PATTERNS:
                if pattern.match(prompt_stripped):
                    return True, f"optimization_followup:{pattern.pattern}"

    # Check sentence-start pronoun (NOT mid-sentence pronouns)
    # Split into sentences and check first word of each
    sentences = re.split(r"[.!?]+\s*", prompt_stripped)
    for sentence in sentences[:2]:  # Check first 2 sentences only
        sentence = sentence.strip()
        if not sentence:
            continue
        for pattern in PRONOUN_START_PATTERNS:
            if pattern.match(sentence):
                # Exclude obvious imperatives like "It's working" vs "Run it"
                # If first word is just the pronoun followed by verb, it's likely follow-up
                words = sentence.split()
                if len(words) >= 2:
                    second_word_lower = words[1].lower()
                    # Expanded exclusion list - common patterns that look like follow-ups but aren't
                    if second_word_lower not in (
                        "is",
                        "was",
                        "has",
                        "had",
                        "'s",
                        '"s',
                        # Stative verbs that don't indicate follow-up
                        "depends",
                        "requires",
                        "works",
                        "helps",
                        "means",
                        "seems",
                        "appears",
                        "needs",
                        "exists",
                        "contains",
                        # Other common patterns
                        "varies",
                        "differs",
                        "includes",
                        "provides",
                    ):
                        return True, f"pronoun_start:{pattern.pattern}"

    # Topic-change detection: if prior context exists, check keyword overlap
    # No overlap = likely new topic (false positive for follow-up detection)
    if prior_context:
        topic = prior_context.get("topic", "")
        summary = prior_context.get("summary", "")
        prior_text = f"{topic} {summary}".lower()

        # Extract keywords from current prompt (nouns/verbs, >3 chars)
        current_words = set(
            w.lower().strip(".,!?;:'\"")
            for w in prompt_stripped.split()
            if len(w) > 3 and w.isalpha()
        )

        # Extract keywords from prior context
        prior_words = set(
            w.lower().strip(".,!?;:'\"") for w in prior_text.split() if len(w) > 3 and w.isalpha()
        )

        # Calculate overlap
        if current_words and prior_words:
            overlap = current_words & prior_words
            # If <20% of current prompt words appear in prior context, it's likely new topic
            if len(overlap) / len(current_words) < 0.2:
                return False, "topic_change"

    return False, ""


def _load_keywords() -> dict:
    """Load context keywords from JSON config file."""
    try:
        if _KEYWORDS_PATH.exists():
            return json.loads(_KEYWORDS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {"topics": [], "skill_patterns": {}}


def get_conversational_context(transcript_path: Path | str | None) -> dict:
    """Extract conversational context from transcript.

    Args:
        transcript_path: Path to transcript JSONL file

    Returns:
        dict with keys: is_followup, detected_skills, detected_topics, confidence
    """
    if not transcript_path:
        return {
            "is_followup": False,
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }

    path = Path(transcript_path)
    if not path.exists():
        return {
            "is_followup": False,
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }

    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {
                "is_followup": False,
                "detected_skills": [],
                "detected_topics": [],
                "confidence": 0.0,
            }
        lines = text.split("\n")
    except OSError:
        return {
            "is_followup": False,
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }

    # Parse last N lines that are user messages
    keywords = _load_keywords()
    skill_patterns = keywords.get("skill_patterns", {})
    topic_keywords = keywords.get("topics", [])

    detected_skills: set[str] = set()
    detected_topics: set[str] = set()
    user_entries = 0

    # Scan from end, collect user messages
    for line in reversed(lines):
        try:
            entry = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        if entry.get("role") != "user":
            continue

        user_entries += 1
        if user_entries > _CONTEXT_WINDOW:
            break

        content = entry.get("content", "")

        # Detect skill names (slash at start of message, not in quoted text)
        # Pattern: /skillname at start or after whitespace, not inside quotes
        # Exclude: "I mentioned /arch" (narrative mention — word immediately before slash)
        # The preceding-word check catches narrative refs like "mentioned /arch", "said /arch"
        narrative_triggers = {"mentioned", "said", "told", "referenced", "called", "named"}
        skill_matches = re.findall(r'(?:^|[\s])/([' + ''.join(re.escape(k) for k in skill_patterns.keys()) + r']\w*)', content)
        for match in skill_matches:
            slash_pos = content.find(f"/{match}")
            if slash_pos > 1:
                # Check if a narrative trigger word precedes the slash
                # Extract word immediately before the slash (handles "mentioned /arch")
                prefix = content[:slash_pos]
                word_match = re.search(r'(\w+)\s*$', prefix)
                if word_match and word_match.group(1).lower() in narrative_triggers:
                    continue
            # Map back to skill name via patterns
            for skill_name, pattern in skill_patterns.items():
                if match == skill_name or match.startswith(skill_name + " ") or f"/{match}" == pattern:
                    detected_skills.add(skill_name)
                    break

        # Detect file paths
        # Pattern: P:/, C:\, ./, / (absolute paths)
        path_matches = re.findall(r'(?:P:/|C:\\|./|/(?![/\w]))[\w\\/.~-]+', content)
        _ = path_matches  # Future use

        # Detect topics via keyword matching
        content_lower = content.lower()
        for topic in topic_keywords:
            if topic.lower() in content_lower:
                detected_topics.add(topic)

    # Calculate confidence
    window_size = min(user_entries, _CONTEXT_WINDOW)
    if window_size == 0:
        confidence = 0.0
    else:
        skill_score = len(detected_skills) * 0.6
        topic_score = len(detected_topics) * 0.4
        confidence = (skill_score + topic_score) / max(window_size, 1)
        confidence = min(confidence, 1.0)

    return {
        "is_followup": user_entries > 1,
        "detected_skills": sorted(detected_skills),
        "detected_topics": sorted(detected_topics),
        "confidence": round(confidence, 2),
    }


def _inject_prior_context(prompt: str, prior_context: dict) -> str:
    """Inject prior context into prompt as system-bounded memory."""
    topic = prior_context.get("topic", "")
    summary = prior_context.get("summary", "")

    if not topic and not summary:
        return prompt

    context_block = f"""[Prior context from earlier in this session about "{topic}": {summary}]"""
    return f"{context_block}\n\n{prompt}"


def _inject_conversational_context(prompt: str, conv_context: dict) -> str:
    """Inject conversational context into prompt as structured block."""
    detected_skills = conv_context.get("detected_skills", [])
    detected_topics = conv_context.get("detected_topics", [])
    confidence = conv_context.get("confidence", 0.0)

    if not detected_skills and not detected_topics:
        return prompt

    skills_str = ", ".join(f"/{s}" for s in detected_skills) if detected_skills else "none"
    topics_str = ", ".join(detected_topics) if detected_topics else "none"

    context_block = f"""[CONVERSATIONAL CONTEXT]
Prior skills detected: {skills_str}
Prior topics: {topics_str}
Confidence: {confidence}
[/CONVERSATIONAL CONTEXT]
"""
    return f"{context_block}\n\n{prompt}"


@register_hook("context_followup_detector")
def process_prompt(context: HookContext) -> HookResult:
    """UserPromptSubmit hook entry point.

    Detects follow-up queries and injects prior context.
    """
    prompt = context.prompt
    if not prompt:
        return HookResult.empty()

    terminal_id = _get_terminal_id(context.data.get("raw_input", {}))
    if not terminal_id:
        return HookResult.empty()

    # Get transcript path from input_data
    transcript_path = context.data.get("transcript_path")

    # Extract conversational context from transcript
    conv_context = get_conversational_context(transcript_path)

    # Load prior context first (needed for topic-change detection)
    prior_context = _load_prior_context(terminal_id)

    # Detect follow-up query (pass prior_context for topic-change detection)
    is_followup, _ = _is_followup_query(prompt, prior_context)

    # Build enhanced prompt with conversational context
    enhanced_prompt = _inject_conversational_context(prompt, conv_context)

    if is_followup and prior_context:
        # Also inject prior terminal context
        enhanced_prompt = _inject_prior_context(enhanced_prompt, prior_context)

    # Save current prompt as context for future follow-ups
    # Only save meaningful context (not short prompts)
    if len(prompt.strip()) > 50:
        context_data = {
            "topic": prompt[:100],
            "summary": prompt[:200],
            "timestamp": time.time(),
        }
        _save_prior_context(terminal_id, context_data)

    # Return empty if no context was added (preserve original prompt)
    if enhanced_prompt == prompt:
        return HookResult.empty()

    return HookResult(context=enhanced_prompt, tokens=len(enhanced_prompt) // 4)

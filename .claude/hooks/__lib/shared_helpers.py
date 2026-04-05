#!/usr/bin/env python3
"""
shared_helpers.py - Common helper functions for hooks
"""

import re
from typing import Dict, List


def is_meta_conversation(transcript: List[Dict]) -> bool:
    """
    Check if user is asking meta-questions about LLM's behavior.

    Target ONLY user-side meta patterns:
    - "why did you make|do|say|use"
    - "what was your (reason|thinking|reasoning)"
    - "please explain your (reasoning|thinking|reason)"
    - "you're right|that was wrong" (agreement/correction)

    These patterns specifically catch:
    - Questions about LLM's past actions ("why did you...")
    - Questions about LLM's reasoning ("what was your thinking...")
    - User corrections/agreements (which prompt LLM self-explanation)

    Returns: True if meta-conversation detected, False otherwise
    """
    if not transcript:
        return False

    recent = transcript[-5:] if len(transcript) >= 5 else transcript

    for msg in recent:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                # Narrow meta-question patterns (user side)
                if re.search(r"why did you (make|do|say|use)", content, re.IGNORECASE):
                    return True
                if re.search(r"what was your (reason|thinking|reasoning)", content, re.IGNORECASE):
                    return True
                if re.search(r"please explain your (reasoning|thinking|reason)", content, re.IGNORECASE):
                    return True
                # Agreement/correction patterns
                if re.search(r"you.re right|your feedback (?:is )?correct|that was not what I asked|I didn't ask you to", content, re.IGNORECASE):
                    return True
    return False


def is_self_referential(response: str) -> bool:
    """
    Check if LLM's response is about its own reasoning/actions/process.

    Target ONLY LLM-side self-referential patterns:
    - "I did this because|my reasoning was|the reason I"
    - "apologize|sorry|incorrect"
    - "you're right|my mistake"
    - "I misread|misunderstood|remembered"
    - Process/self-report: "I did not use TDD", "I only ran py_compile", "I created X"

    CRITICAL: Does NOT filter external claims like:
    - "The file is at C:\\path"
    - "The bug is in line 42"
    - "This test passed"
    - "The fix works"

    Returns: True if self-referential, False otherwise
    """
    if not isinstance(response, str):
        return False

    response_lower = response.lower()

    # Self-referential patterns in LLM output
    self_ref_patterns = [
        # Existing: reasoning/explanation patterns
        r"i (?:did|made|said|used|wrote) this (?:because|as)",  # "I did this because"
        r"my (?:reasoning|thinking|mistake|intent|analysis) (?:was|has been)",  # "my reasoning was"
        r"the reason i (?:did|made|said|was)",  # "the reason i did"
        r"(?:apologize|sorry|regret),? i",  # Apologies
        r"you.re right|your feedback (?:is )?correct",  # Agreement with feedback
        r"i mis(?:read|understood|interpreted|remembered)",  # Admission of error
        # Process/self-report patterns (implementation descriptions)
        r"i (?:did not|didn't|didn't) use tdd",  # "I did not use TDD"
        r"i (?:only|just) ran (?:py_compile|python -c|a simple check)",  # "I only ran py_compile"
        r"i (?:didn't|haven't|did not) (?:write|create) (?:tests?|a test)",  # "I didn't write tests"
        r"i (?:haven't|didn't) (?:written|wrote) tests? (?:yet|first|before)",  # "I haven't written tests yet"
        r"i created (?:\w+\.py|shared_helpers|\w+\.md)",  # "I created shared_helpers.py"
        r"i modified (?:\d+ hooks?|\d+ files?|\w+\.py)",  # "I modified three hooks"
        r"i (?:added|edited|updated|changed) (?:the |a )?(?:hook|file|function)",  # "I added the function"
        r"no (?:tests?|pytest|verification) (?:yet|were run|have been run)",  # "no tests yet"
        r"(?:without|not) (?:running|using|executing) (?:pytest|tests?)",  # "without running pytest"
        r"tests? (?:not )?(?:written|created|implemented) (?:yet|before|first)",  # "tests not written yet"
    ]

    for pattern in self_ref_patterns:
        if re.search(pattern, response_lower):
            return True
    return False


def is_user_intent_statement(transcript_or_text) -> bool:
    """
    Detect user statements that set goals/preferences or configuration,
    not factual claims about the world.

    Examples:
    - "I want to LLM to push back when I'm wrong."
    - "We need to include these constraints in the system."
    - "My goal is to minimize unverified claims."
    - "Please make sure you respect my stated intent."

    These are CONFIGURATION, not claims to verify.
    Claim-coverage hooks should NOT block these.

    Returns: True if intent statement detected, False otherwise
    """
    # Accept either a transcript (list of messages) or a single text string
    if isinstance(transcript_or_text, list):
        texts = [
            msg.get("content", "")
            for msg in transcript_or_text
            if msg.get("role") == "user"
        ]
        combined = " ".join(t for t in texts if isinstance(t, str))
    else:
        combined = transcript_or_text or ""

    if not combined:
        return False

    lower = combined.lower()

    INTENT_PATTERNS = [
        r"\bi want (the )?llm to\b",
        r"\bwe need to\b",
        r"\bmy goal is\b",
        r"\bi prefer\b",
        r"\bplease make sure\b",
        r"\btreat .* as a hypothesis\b",
        r"\bwhen i say\b.*\bdon't\b",
        r"\brespect my\b",
    ]

    return any(re.search(p, lower) for p in INTENT_PATTERNS)


def strip_non_claim_lines(text: str) -> str:
    """Remove lines that are structural formatting, not factual claims.

    Strips: markdown headers, blockquotes quoting prior output, horizontal
    rules, table rows, and table separator lines. These are presentation,
    not assertions about code/files/state.
    """
    if not text:
        return ""
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        # Markdown headers (e.g. "### What IS Already Done")
        if stripped.startswith("#"):
            continue
        # Blockquotes that echo prior conversation (e.g. "> - ...")
        if stripped.startswith(">"):
            continue
        # Horizontal rules
        if re.match(r"^[-*_]{3,}\s*$", stripped):
            continue
        # Markdown table rows (e.g. "| Component | Status |")
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        # Table separator lines (e.g. "|---|---|")
        if re.match(r"^\|[\s:_-]+\|", stripped):
            continue
        out.append(line)
    return "\n".join(out)


def is_question(text: str) -> bool:
    """Check if a text block appears to be a question or clarification."""
    if not text:
        return False
    # Heuristic: ends with question mark or starts with question word
    lowered = text.lower().strip()
    if lowered.endswith("?"):
        return True
    question_starters = (
        "what", "which", "how", "where", "when", "why", "should", "would", "could",
        "can you", "would you", "should i", "is there", "are there", "do you",
    )
    return any(lowered.startswith(s) for s in question_starters)

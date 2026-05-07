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


_STOP_DIAGNOSTIC_PREFIXES: tuple[str, ...] = (
    "STATUS:",
    "UNVERIFIED CLAIMS:",
    "Evidence missing for:",
    "Stop hook error:",
    "Stop hook feedback:",
    "Ran ",
)


def strip_non_claim_lines(text: str) -> str:
    """Remove lines that are structural formatting, not factual claims.

    Strips: markdown headers, blockquotes quoting prior output, horizontal
    rules, table rows, table separator lines, and Stop-hook diagnostic
    scaffolding (STATUS:, UNVERIFIED CLAIMS:, etc.). These are presentation
    or transport artifacts, not assertions about code/files/state.
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
        # Stop-hook diagnostic lines (transport scaffolding, not claims)
        if any(stripped.startswith(p) for p in _STOP_DIAGNOSTIC_PREFIXES):
            continue
        # Ran N stop hooks summary
        if re.match(r"^Ran\s+\d+\s+stop\s+hooks?", stripped):
            continue
        # Tool/UI markers (⎿, ●, etc.)
        if stripped and stripped[0] in "⎿●":
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


def is_non_substantive_turn(text: str) -> bool:
    """
    Check if a response is phatic/meta with no substantive claims.

    Conservative: returns True only when ALL conditions are met.

    Conditions:
    1. Short length: Fewer than ~20 words
    2. No obvious factual/technical content (digits, technical terms)
    3. No strong epistemic or causal markers
    4. No recommendation or decision language
    5. Matches at least one phatic/meta pattern

    When in doubt, return False.
    """
    if not text or not isinstance(text, str):
        return False

    # Strip markdown formatting
    stripped = text.strip()
    # Remove blockquote markers
    if stripped.startswith(">"):
        return False

    # Condition 1: Length check
    words = stripped.split()
    if len(words) >= 20:
        return False

    # Condition 2: No digits (factual/technical content proxy)
    if any(c.isdigit() for c in text):
        return False

    # Condition 3: No epistemic/causal markers
    epistemic_causal = [
        "because", "caused by", "due to", "result of", "therefore",
        "as a result", "this means", "indicates that", "proves that",
        "confirms that", "shows that", "reveals that", "demonstrates",
        "i found", "tests passed", "the test", "verified that",
        "confirmed that", "discovered that", "concluded that",
        "in fact", "actually", "in reality", "the reality is",
    ]
    text_lower = stripped.lower()
    for marker in epistemic_causal:
        if marker in text_lower:
            return False

    # Condition 4: No recommendation/decision language
    recommendation = [
        "should", "i recommend", "you should", "we should",
        "choose", "option", "prefer", "recommend",
        "better to", "best to", "ideal", "optimal",
    ]
    for word in recommendation:
        if word in text_lower:
            return False

    # Condition 5: Matches at least one phatic/meta pattern
    phatic_patterns = [
        r"^\s*(hi|hello|hey|greetings|good morning|good afternoon|good evening|howdy)\b",
        r"\b(got it|understood|okay|ok|alright|sure|certainly)\b",
        r"\b(ready when you are|ready when you|ready to proceed|ready to start)\b",
        r"\b(no problem|you're welcome|my pleasure|happy to)\b",
        r"\b(let me know|feel free|just say|just ask|just tell)\b",
        r"\b(sounds good|looks good|great|perfect|excellent)\b",
        r"\b(what are we|what shall we|what should we)\b",
        r"\b(i'?m? (here|ready|available|open) (when|for|today|tomorrow))\b",
    ]
    for pattern in phatic_patterns:
        if re.search(pattern, stripped, re.IGNORECASE):
            return True

    # More lenient: check for common greeting endings (after content)
    greeting_enders = ["hi there", "hello!", "hey there", "hi!", "hello there"]
    for greeting in greeting_enders:
        if stripped.lower().endswith(greeting):
            return True

    return False

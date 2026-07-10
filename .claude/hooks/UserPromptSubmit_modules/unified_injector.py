"""Unified Prompt Injector Module.

Extracted from UserPromptSubmit_router.py.
Provides solo dev context, goal anchor, command directive, and
falsification injection.
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult

# Constants
SOLO_DEV_CONTEXT = """
## OPERATIONAL CONTEXT
Solo director + SOTA AI-coder. You are the implementation layer for a director who
sets direction and reviews output. Reliability target: 99% — production-grade without
enterprise bloat. Every output must be complete and correct on first delivery.
""".strip()

# Command detection patterns
COMMAND_WORDS = (
    "build",
    "code",
    "analyze",
    "research",
    "test",
    "debug",
    "investigate",
    "refactor",
    "optimize",
    "design",
    "plan",
    "arch",
    "change",
    "create",
    "implement",
    "add",
    "write",
    "develop",
    "make",
    "set up",
    "configure",
)
COMMAND_WORDS_RE = "|".join(COMMAND_WORDS)
IMPERATIVE_COMMAND_RE = re.compile(
    rf"^\s*(?:please\s+|can you\s+|go ahead and\s+)?(?P<command>{COMMAND_WORDS_RE})\b",
    re.IGNORECASE,
)
# Local quote-stripping regex retained for `detect_command` when called without
# the canonical envelope (defensive fallback). The canonical span removal lives
# in `request_envelope.strip_quoted_spans` and is used by `classify_intent`
# when an envelope is available. Kept here as a substring-only fallback so
# legacy callers that pass raw prompts still get the old behavior.
QUOTE_RE = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')
SLASH_COMMAND_RE = re.compile(r"^/([a-z0-9-]+)(?:\s+(.*))?$", re.IGNORECASE)

# Falsification indicators - these patterns suggest testing without implementation
FALSIFICATION_PATTERNS = [
    r"\bjust\s+?test\s+(?:this|that|it)\b",
    r"\b(?:this|that)\s+(?:is\s+)?a?\s*test\b",
    r"\b(?:verify|validate|check)\s+(?:that\s+)?(?:this|it|a)\s+(?:works?|is\s+correct|passes)\b",
    r"\b(?:confirm|ensure|make)\s+(?:sure\s+)?(?:this|it)\s+(?:works|is\s+correct|is\s+fixed)\b",
    r"\b(?:test|demo)\s+(?:only|mere(?:ly)?)?\s+(?:to\s+)?(?:show|prove|demonstrate)\s+(?:that\s+)?(?:this|it)\s+(?:works|is\s+correct|passes)\b",
    r"\b(?:without|no|(?:dont|not))\s+(?:implementing|writing|coding)\s+(?:any)?\s*(?:code|logic|implementation)\b",
    r"\b(?:minimal|minimum|smallest)\s+(?:possible\s+)?(?:example|change|fix|code)\b",
    r"\b(?:simple|easy|easiest)\s+(?:example|change|fix|code)\b",
    r"\bstub\b",
]


def _strip_quoted_text(text: str) -> str:
    """Remove simple quoted spans to avoid matching commands inside quotes.

    Defensive fallback used only when no canonical envelope is available.
    """
    return QUOTE_RE.sub(" ", text)


def detect_command(prompt: str, *, _outer_text: str | None = None) -> dict[str, str] | None:
    """Detect if prompt contains a command directive.

    Args:
        prompt: User prompt text
        _outer_text: Optional pre-computed outer text (from request_envelope).
            When provided, runs against outer text only — quoted/fenced commands
            do not trigger command injection. When None, falls back to the
            legacy `_strip_quoted_text` local stripper.

    Returns:
        Dict with 'command' and 'args' keys, or None if no command
    """
    stripped = prompt.strip()
    if not stripped:
        return None

    # Slash commands are handled by skill_enforcer to avoid duplicate injection.
    if SLASH_COMMAND_RE.match(stripped):
        return None

    # Avoid command detection in explicit questions.
    if "?" in stripped:
        return None

    if _outer_text is not None:
        text = _outer_text.strip() if _outer_text.strip() else _strip_quoted_text(stripped)
    else:
        text = _strip_quoted_text(stripped)
    sentences = [s.strip() for s in re.split(r"[.!;\n]+", text) if s.strip()]
    for sentence in sentences:
        match = IMPERATIVE_COMMAND_RE.match(sentence)
        if not match:
            continue
        command = match.group("command").lower()
        args = sentence[match.end() :].strip(" ,")
        return {
            "command": command,
            "args": args,
        }
    return None


def extract_command_name(prompt: str) -> str | None:
    """Extract command name from prompt.

    Args:
        prompt: User prompt text

    Returns:
        Command name string or None
    """
    match = SLASH_COMMAND_RE.match(prompt.strip())
    if match:
        return match.group(1)
    return None


def build_command_injection(cmd_info: dict, user_args: str) -> str:
    """Build context injection for command.

    Args:
        cmd_info: Command info dict with 'command' key
        user_args: Additional arguments after command

    Returns:
        Injection text for command context
    """
    command = cmd_info.get("command", "")
    if not command:
        return ""

    parts = [f"**Command**: /{command}"]
    if user_args:
        parts.append(f"**Args**: {user_args}")
    return "\n\n".join(parts)


def extract_goal(prompt: str) -> str | None:
    """Extract goal statement from prompt.

    Looks for patterns like "My goal is to..." or similar phrasing.
    """
    goal_patterns = [
        r"\b(?:my\s+)?goal\s+(?:is\s+to?(?:\s+(?:achieve|implement|build|create|fix|solve|add))?\s*)\b",
        r"\b(?:i\s+)?want\s+to(?:\s+(?:achieve|implement|build|create|fix|solve|add))?\s*\b",
        r"\b(?:trying\s+to|attempting)\s+(?:achieve|implement|build|create|fix)\s*\b",
    ]

    for pattern in goal_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            goal_text = re.sub(
                r"^\b(?:my\s+)?goal\s+(?:is\s+to|(?:i\s+)?want\s+to|(?:trying\s+to|attempting)\s+(?:achieve|implement|build|create|fix)\s*)\s*",
                "",
                prompt,
                flags=re.IGNORECASE,
            )
            return goal_text.strip() if goal_text.strip() else None

    return None


def build_goal_injection(goal: str | None) -> str:
    """Build context injection for goal anchor.

    Args:
        goal: Extracted goal statement or None

    Returns:
        Injection text with goal anchor
    """
    if not goal:
        return ""

    if len(goal) > 200:
        goal = goal[:197] + "..."

    return "**Goal**: " + goal


# Intent classification patterns
# NOTE: These are matched against lowercased text, so patterns must work with lowercase

# Meta-question patterns (checked before QUESTION - higher priority)
META_QUESTION_PATTERNS = [
    # User asking why AI missed/failed to identify something
    r"\bwhy\s+didn\'t\s+(?:you|the\s+ai)\s+(?:identify|notice|recognize|see|detect|find)\b",
    r"\bwhy\s+did\s+(?:you|the\s+ai)\s+(?:miss|fail\s+to|ignore|overlook)\b",
    r"\byou\s+(?:missed|failed\s+to\s+identify|didn\'t\s+identify|ignored)\b",
    r"\byou\s+didn\'t\s+(?:identify|notice|recognize|see|detect)\b",
    # User asking about question identification itself
    r"\bidentify\s+the\s+(?:actual|real|core|true)\s+question\b",
    r"\bwhat\s+(?:question|question\s+am|i)\s+(?:was\s+)?(?:i\s+)?asking\b",
    r"\bwhat\s+did\s+i\s+(?:actually\s+)?(?:mean|want|ask)\b",
    r"\byou\s+(?:answered|responded\s+to)\s+(?:the\s+)?wrong\s+(?:question|thing)\b",
]

QUESTION_PATTERNS = [
    # Must end with ?
    r"\?(?!.*\b(?:just|only|simply|mere(?:ly)?)\s+)",
    # Question words at start
    r"^(?:what|how|why|when|where|who|which|whose)\b",
    # Aux verbs with please/explain/tell/show/help
    r"\b(?:can you|could you|would you)\s+(?:please\s+)?(?:explain|tell|show|help|clarify)\b",
    # Explicit requests for explanation with ?
    r"\b(?:explain|describe|show me|tell me|clarify)\b.*\?$",
]

CORRECTION_PATTERNS = [
    # User re-stating instructions or pushing back (lowercase patterns)
    r"\b(?:did you|you didn\'t|you were|i asked|i told|i said)\b",
    r"\bthat\'s not|not what\b",
    r"\bno\s+(?:you|that\'s|this is)\b",
    r"\b(?:wrong|incorrect|missing|forgot|missed)\b.*\bit\b",
    r"\byou\s+(?:missed|overlooked|ignored|removed|deleted|changed)\b",
    r"\bdid\s+you\s+just\s+remove\b",
    r"\bwithout\s+(?:even\s+)?consider(?:ing|ation)\b",
    r"\bwhy\s+are\s+we\s+depending\s+so\s+much\s+on\s+pushback\s+prompts\b",
    # Escalation-level corrections (user asserting a fact the AI denied)
    r"\bi\s+(?:just\s+)?told\s+you\b",
    r"\bit\'?s\s+a\s+(?:bug|error|problem|issue|failure)\b",
    r"\bdo\s+i\s+need\s+to\s+(?:fire|replace|get\s+a\s+better)\b",
    r"\byou\'?re\s+(?:wrong|missing|not\s+listening|ignoring)\b",
    r"\bi\s+(?:already|just)\s+(?:said|told|explained|showed)\b",
    r"\bstop\s+(?:saying|claiming|telling\s+me)\b",
]

RESEARCH_PATTERNS = [
    # Explicit investigation verbs (higher specificity than problem words)
    r"\b(?:investigate|look into|explore|examine|research)\b",
    r"\b(?:check|analyze|study)\s+(?:why|how|what|whether|if)\b",
]

DEBUG_PATTERNS = [
    # Explicit fix/debug verbs
    r"\b(?:fix|debug|troubleshoot|resolve|repair|correct)\b",
    # "not working" variations
    r"\bnot\s+working\b",
    r"\bdoesn\'t\s+work\b",
    r"\bisn\'t\s+working\b",
    # Problem states with "the" (specific problem)
    r"\b(?:broken|failing|problem|bug)\b",
    # "error" alone is too ambiguous (could be adding error handling)
]


def classify_intent(prompt: str, *, _outer_text: str | None = None) -> str | None:
    """Classify user prompt intent.

    Categories:
    - META_QUESTION: User asking about question identification or meta-cognitive analysis
    - QUESTION: Genuine question expecting only an answer
    - CORRECTION: User pushing back or re-issuing instructions
    - RESEARCH: Investigation/exploration needed
    - DEBUG: Debugging/fixing needed
    - ACTION: Direct instruction (default, no injection)

    Priority order:
    1. CORRECTION (highest - user is re-directing)
    2. META_QUESTION (meta-cognitive question about question identification)
    3. QUESTION (with ?) - explicit questions take priority over keyword matches
    4. DEBUG, RESEARCH (keyword-based)

    Args:
        prompt: User prompt text
        _outer_text: Optional pre-computed outer text. When provided, runs
            against outer text only — quoted/fenced content cannot trigger
            intent classification.

    Returns:
        Intent category string or None for ACTION (no injection needed)
    """
    classification_text = _outer_text if _outer_text is not None else prompt
    prompt_lower = classification_text.lower().strip()
    prompt_clean = classification_text.strip()
    raw_prompt_clean = prompt.strip()

    # Skip slash commands - they're ACTION by definition
    if SLASH_COMMAND_RE.match(raw_prompt_clean):
        return None

    # Check for CORRECTION (highest priority - user is re-directing)
    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            return "CORRECTION"

    # Check for META_QUESTION (meta-cognitive questions about question identification)
    for pattern in META_QUESTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            return "META_QUESTION"

    # Check for QUESTION first (with ?) - explicit questions take priority
    # A sentence ending with ? is likely a question even if it has debug keywords
    if "?" in prompt_clean:
        # Check if it's actually a question (not imperative command like "Fix this?")
        is_imperative = bool(IMPERATIVE_COMMAND_RE.match(prompt_clean))
        if not is_imperative:
            for pattern in QUESTION_PATTERNS:
                if re.search(pattern, prompt_lower):
                    return "QUESTION"

    # Check for DEBUG (keyword-based, after QUESTION check)
    for pattern in DEBUG_PATTERNS:
        if re.search(pattern, prompt_lower):
            return "DEBUG"

    # Check for RESEARCH (keyword-based)
    for pattern in RESEARCH_PATTERNS:
        if re.search(pattern, prompt_lower):
            return "RESEARCH"

    # Default: ACTION - no injection needed
    return None


def build_intent_injection(intent: str | None) -> str:
    """Build context injection for classified intent.

    Args:
        intent: Classified intent category or None

    Returns:
        Injection text for intent guidance
    """
    if not intent:
        return ""

    injections = {
        "META_QUESTION": (
            "**Intent**: Meta-cognitive question about question identification. "
            "First, identify what the user is ACTUALLY asking (not the embedded questions). "
            "Restate the core question in one sentence, then answer ONLY that core question. "
            "Do NOT answer embedded questions or context - those are NOT the task."
        ),
        "QUESTION": (
            "**Intent**: The user is asking a question. "
            "Answer directly and concisely. "
            "Do not execute commands, create files, start workflows, or dispatch subagents unless explicitly asked."
        ),
        "CORRECTION": (
            "**Intent**: The user is correcting you or re-issuing a prior instruction. "
            "Follow their instruction now without defensiveness."
        ),
        "RESEARCH": (
            "**Intent**: Research mode - gather information before proposing solutions. "
            "Read relevant files, search codebase, and understand context before acting."
        ),
        "DEBUG": (
            "**Intent**: Debug mode - read files to identify the failure, "
            "propose a minimal fix, and test to verify."
        ),
    }

    return injections.get(intent, "")


def detect_falsification_risk(prompt: str) -> bool:
    """Detect if prompt indicates falsification testing.

    Checks for test-specific language that suggests falsification without
    actual implementation.

    Args:
        prompt: User prompt text

    Returns:
        True if falsification risk detected, False otherwise
    """
    prompt_lower = prompt.lower()
    for pattern in FALSIFICATION_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True

    return False


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Rough estimate: ~4 characters per token.
    """
    return len(text) // 4


def combine_sections(sections: list) -> tuple:
    """Combine sections and estimate tokens.

    Args:
        sections: List of section strings

    Returns:
        Tuple of (combined_text, estimated_tokens)
    """
    filtered = [s for s in sections if s]
    combined = "\n\n".join(filtered)
    return combined, estimate_tokens(combined)


from UserPromptSubmit_modules.registry import register_hook


@register_hook("unified_injector", priority=9.0)
def run_unified_injector(context: HookContext) -> HookResult:
    """Main entry point for unified injector.

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with context injection and token estimate
    """
    sections = []

    # Solo dev context (always)
    sections.append(SOLO_DEV_CONTEXT)

    # Read the canonical envelope so classification runs against outer text
    # (quoted/fenced proposal content cannot trigger DEBUG/IMPLEMENTATION
    # injection). The envelope is cached on context.data by the
    # unified_detection hook (priority 1.0) or computed lazily here.
    try:
        from UserPromptSubmit_modules.unified_detection import ensure_request_envelope
        envelope = ensure_request_envelope(context)
        outer = envelope.outer_text if envelope is not None else None
    except Exception:  # pragma: no cover - envelope is best-effort
        outer = None

    # Intent classification ( QUESTION, CORRECTION, RESEARCH, DEBUG, ACTION)
    # Must come before command detection so we don't double-classify
    intent = classify_intent(context.prompt, _outer_text=outer)
    if intent:
        sections.append(build_intent_injection(intent))

    # Command directive
    cmd_info = detect_command(context.prompt, _outer_text=outer)
    if cmd_info:
        user_args = cmd_info.get("args", "")
        sections.append(build_command_injection(cmd_info, user_args))

    # Goal anchor
    goal = extract_goal(context.prompt)
    sections.append(build_goal_injection(goal))

    # Library-First warning for build/create commands without a skill (#4)
    # Only injects when an imperative build/create/implement command is detected
    # and no slash-skill is active (skill system has its own Library-First Gate)
    if cmd_info and cmd_info.get("command", "") in (
        "build",
        "create",
        "implement",
        "add",
        "write",
        "develop",
        "make",
    ):
        prompt_stripped = context.prompt.strip()
        if not prompt_stripped.startswith("/"):
            sections.append(
                "**Library-First Gate**\n"
                "> Before proposing new code: (1) search first (`/search`, Grep, Glob), "
                "(2) check existing backends/skills/tools, (3) extend existing solutions "
                "when they cover ~70%+, and (4) if you still build new, state why existing "
                "options are insufficient. Greenfield proposals without a search pass are prohibited."
            )

    # Falsification reminder
    if len(context.prompt.strip()) >= 20:
        falsification = detect_falsification_risk(context.prompt)
        if falsification:
            sections.append(
                "**Note**: This appears to be a test. If implementing actual code, remember TDD requirements."
            )

    context_text, tokens = combine_sections(sections)
    return HookResult(context=context_text, tokens=tokens)

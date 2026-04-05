#!/usr/bin/env python3
"""
Prompt Enhancement Router Module

Layer 1 of three-layer prompt enhancement architecture:
- Detects ambiguous prompts via lightweight heuristics
- Injects clarification questions when needed
- Routes to appropriate enhancement level based on complexity

This module exports `process_prompt()` for router integration.
"""

from __future__ import annotations

import json
import os
import re
import sys

# Import base types for router integration (conditional for standalone execution)
try:
    from .base import HookContext, HookResult
    from .registry import register_hook
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False

# Import prompt choice state manager
try:
    from __lib.prompt_choice_state import (
        clear_prompt_choice,
        detect_choice_from_message,
        get_pending_choice,
        save_prompt_choice,
    )
    CHOICE_STATE_AVAILABLE = True
except ImportError:
    CHOICE_STATE_AVAILABLE = False

# Configuration from environment
ENABLED = os.environ.get("PROMPT_ENHANCEMENT_ENABLED", "false").lower() == "true"
DEBUG = os.environ.get("PROMPT_ENHANCEMENT_DEBUG", "false").lower() == "true"
PROMPT_CHOICE_ENABLED = os.environ.get("PROMPT_CHOICE_ENABLED", "true").lower() == "true"

# Domain detection patterns
DOMAIN_PATTERNS = {
    "security": {
        "paths": ["/security/", "security/", "auth/"],
        "keywords": ["vulnerability", "auth", "xss", "csrf", "injection", "exploit"],
    },
    "testing": {
        "paths": ["/test/", "tests/", "spec/"],
        "keywords": ["test", "pytest", "unittest", "mock", "fixture"],
    },
    "database": {
        "paths": ["/db/", "database/", "sql/"],
        "keywords": ["database", "sql", "query", "migration", "schema"],
    },
    "frontend": {
        "paths": ["/frontend/", "/web/", "client/"],
        "keywords": ["react", "vue", "angular", "css", "html", "component"],
    },
}

# Ambiguity patterns
AMBIGUITY_PATTERNS = [
    (r"^(fix|check|test|debug)\s+(it|this|that|them)(?!\s+(out|up|now))", "unclear_antecedent"),
    (r"^(implement|add|create|write|build)\s+(this|it|that)$", "missing_specifics"),
    (r"^(make|create|build|implement|optimize)\s+(it|this|them)\s+(better|faster|cleaner)$", "ambiguous_improvement"),
    (r"^(optimize|improve|enhance)\s+(this|it|that)$", "ambiguous_improvement"),
    (r"^(ok|okay|sure|do it|go|proceed)\s*$", "too_brief"),
    (r"^(help|fix|solve|handle)(?!\s+\w{3,})", "too_brief"),
]

# Complexity thresholds (word counts)
COMPLEXITY_THRESHOLDS = {
    "simple": (0, 10),
    "moderate": (10, 30),
    "complex": (30, 60),
    "expert": (60, float('inf')),
}


def detect_domain(prompt: str, cwd: str) -> str:
    """Detect domain from prompt and working directory."""
    prompt_lower = prompt.lower()

    # Check path hints from cwd
    for domain, patterns in DOMAIN_PATTERNS.items():
        for path_pattern in patterns.get("paths", []):
            if path_pattern.lower() in cwd.lower():
                if DEBUG:
                    print(f"[prompt_enhancement] Domain '{domain}' detected from path: {cwd}", file=sys.stderr)
                return domain

    # Check keywords in prompt
    for domain, patterns in DOMAIN_PATTERNS.items():
        for keyword in patterns.get("keywords", []):
            if keyword.lower() in prompt_lower:
                if DEBUG:
                    print(f"[prompt_enhancement] Domain '{domain}' detected from keyword: {keyword}", file=sys.stderr)
                return domain

    return "general"


def assess_complexity(prompt: str) -> str:
    """Assess prompt complexity based on word count and patterns.

    Word count is primary; patterns only apply when word count is ambiguous.
    """
    word_count = len(prompt.split())

    # Word count based (primary)
    for level, (min_words, max_words) in COMPLEXITY_THRESHOLDS.items():
        if min_words <= word_count < max_words:
            if DEBUG:
                print(f"[prompt_enhancement] Complexity '{level}' (words: {word_count})", file=sys.stderr)
            return level

    # Fallback for very long prompts
    return "expert"


def check_ambiguity(prompt: str) -> tuple[bool, str | None]:
    """Check if prompt has ambiguity issues.

    Returns:
        (is_ambiguous, reason) tuple
    """
    prompt_stripped = prompt.strip()

    # Check specific patterns first (before the generic "too_brief" check)
    for pattern, reason in AMBIGUITY_PATTERNS:
        if re.match(pattern, prompt_stripped, re.IGNORECASE):
            if DEBUG:
                print(f"[prompt_enhancement] Ambiguity detected: {reason}", file=sys.stderr)
            return True, reason

    # Very brief prompts (catches remaining cases) - only 1-2 words
    if len(prompt_stripped.split()) <= 2:
        return True, "too_brief"

    return False, None


def build_clarification_injection(prompt: str, ambiguity_reason: str, domain: str) -> dict:
    """Build clarification question injection.

    Returns:
        dict with 'additionalContext' and 'tokens' keys
    """
    questions = []

    if ambiguity_reason == "unclear_antecedent":
        questions.append("What specifically are you referring to?")
        questions.append("Which file, component, or area should I focus on?")
    elif ambiguity_reason == "missing_specifics":
        questions.append("What should be implemented or created?")
        questions.append("Can you describe the desired outcome or behavior?")
    elif ambiguity_reason == "ambiguous_improvement":
        questions.append("What aspects should be improved?")
        questions.append("Are there specific issues or problems to address?")
    elif ambiguity_reason in ("too_brief", "help", "fix"):
        questions.append("What would you like me to help you with?")
        questions.append(f"Can you provide more details about the {domain} task?")
    else:
        questions.append("Could you provide more context about what you need?")

    injection = "\n**Clarification Questions**\n\n"
    for i, q in enumerate(questions, 1):
        injection += f"{i}. {q}\n"

    injection += f"\nPlease clarify so I can best assist with your {domain} request."

    return {
        "additionalContext": injection,
        "tokens": len(injection.split())
    }


def build_lightweight_guidance(domain: str, complexity: str) -> dict:
    """Build lightweight domain-specific guidance injection.

    Returns:
        dict with 'additionalContext' and 'tokens' keys
    """
    guidance_by_domain = {
        "security": (
            "**Security Context**: Considering security implications including "
            "input validation, output encoding, authentication, authorization, "
            "and common vulnerabilities (OWASP Top 10)."
        ),
        "testing": (
            "**Testing Context**: Following test-driven development principles "
            "with clear arrange-act-assert structure, edge case coverage, and "
            "maintainable test fixtures."
        ),
        "database": (
            "**Database Context**: Considering data integrity, transaction safety, "
            "query performance, proper indexing, and migration safety."
        ),
        "frontend": (
            "**Frontend Context**: Considering component reusability, state management, "
            "accessibility, responsive design, and performance optimization."
        ),
        "general": (
            "**Context**: Please provide specific details about what you'd like "
            "to accomplish so I can give the most helpful response."
        ),
    }

    guidance = guidance_by_domain.get(domain, guidance_by_domain["general"])

    return {
        "additionalContext": guidance,
        "tokens": len(guidance.split())
    }


def build_enhanced_prompt(original: str, injection: str) -> str:
    """Build an enhanced prompt by adding the injection.

    Args:
        original: The user's original prompt
        injection: The clarification/guidance to add

    Returns:
        Enhanced prompt text
    """
    return f"{original}\n\n{injection.strip()}"


def build_choice_ui(
    original: str,
    enhanced: str,
    injection: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> dict:
    """Build a choice UI when prompt is enhanced.

    Args:
        original: The user's original prompt
        enhanced: The enhanced version
        injection: The injection that was added
        session_id: Session ID for state management
        terminal_id: Terminal ID for state management

    Returns:
        dict with 'additionalContext' containing the choice UI
    """
    choice_ui = f"""

---

**💡 Prompt Enhancement Available**

**Your original:**
{original[:200]}{"..." if len(original) > 200 else ""}

**Enhanced version:**
{enhanced[:300]}{"..." if len(enhanced) > 300 else ""}

**Action Required**

0 - Use enhanced prompt (recommended)
1 - Use your original prompt

---

"""

    # Save the choice state for the next turn
    if CHOICE_STATE_AVAILABLE:
        save_prompt_choice(original, enhanced, injection, session_id, terminal_id)

    return {
        "additionalContext": choice_ui,
        "tokens": len(choice_ui.split())
    }


def process_prompt(data: dict) -> dict:
    """Process prompt for enhancement.

    This is the main entry point for router integration.

    Args:
        data: Hook input data with 'prompt' and 'cwd' keys

    Returns:
        dict with 'additionalContext' and optionally 'tokens' keys.
        May also include 'replacePrompt' key for prompt replacement.
        Returns empty dict if no enhancement or disabled.
    """
    # Quick exit if disabled
    if not ENABLED:
        return {}

    prompt = data.get("prompt", "")
    cwd = data.get("cwd", "")

    # Extract session/terminal IDs for state management
    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
    )
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
    )

    if not prompt or not prompt.strip():
        return {}

    # Clean terminal noise from prompt - do this FIRST before any processing
    prompt = _clean_prompt_noise(prompt)

    # Check if there's a pending choice from a previous enhancement
    if CHOICE_STATE_AVAILABLE:
        pending = get_pending_choice(session_id, terminal_id)
        if pending:
            # Check if user is responding to the choice
            user_choice = detect_choice_from_message(prompt)
            if user_choice:
                # User made a choice - return the chosen prompt
                chosen_prompt = (
                    pending["original_prompt"] if user_choice == "original"
                    else pending["enhanced_prompt"]
                )
                clear_prompt_choice(session_id, terminal_id)

                # Return the chosen prompt as the new prompt
                return {
                    "replacePrompt": chosen_prompt,
                    "additionalContext": f"\n**✓ Using {'enhanced' if user_choice == 'enhanced' else 'original'} prompt.**\n"
                }
            else:
                # User said something else - clear the pending state and continue
                clear_prompt_choice(session_id, terminal_id)

    # Slash command handling: extract skill prefix and enhance only arguments.
    # e.g. "/p package skill, and files" → skill_prefix="/p", args_text="package skill, and files"
    # Enhancement operates on args_text only; skill_prefix is preserved in any replacement.
    # NOTE: Use re.search not re.match — terminal noise often precedes the slash command
    # in the raw prompt (e.g. "full pipeline review. /p package skill, and files").
    skill_prefix = ""
    slash_match = re.search(r'(?:^|\s)(/[\w-]+(?::[\w-]+)?)\s+(.*)', prompt.strip(), re.DOTALL)
    if slash_match:
        skill_prefix = slash_match.group(1)
        args_text = slash_match.group(2).strip()
        if not args_text:
            # Slash command with no arguments — nothing to enhance
            return {}
        # Use the arguments portion for analysis
        prompt = args_text

    # Perform analysis
    domain = detect_domain(prompt, cwd)
    complexity = assess_complexity(prompt)
    is_ambiguous, ambiguity_reason = check_ambiguity(prompt)

    result = {}

    # Helper: re-attach skill prefix to prompts for choice UI and replacePrompt
    def _with_prefix(text: str) -> str:
        return f"{skill_prefix} {text}" if skill_prefix else text

    # Route based on analysis
    if is_ambiguous:
        # Clarification questions - don't offer choice, just inject
        result = build_clarification_injection(prompt, ambiguity_reason, domain)
        if DEBUG:
            print("[prompt_enhancement] CLARIFICATION mode injected", file=sys.stderr)
    elif complexity == "simple":
        # Simple prompts pass through
        if DEBUG:
            print("[prompt_enhancement] PASS mode (simple prompt)", file=sys.stderr)
        result = {}
    elif complexity == "moderate":
        injection_obj = build_lightweight_guidance(domain, complexity)
        injection_text = injection_obj.get("additionalContext", "")

        if PROMPT_CHOICE_ENABLED and CHOICE_STATE_AVAILABLE and injection_text:
            # Build enhanced prompt and present choice (with skill prefix preserved)
            enhanced = build_enhanced_prompt(prompt, injection_text)
            result = build_choice_ui(
                _with_prefix(prompt), _with_prefix(enhanced),
                injection_text, session_id, terminal_id,
            )
        else:
            result = injection_obj

        if DEBUG:
            print("[prompt_enhancement] GUIDANCE mode injected", file=sys.stderr)
    else:
        # Complex/expert - could use framework in Phase 3
        injection_obj = build_lightweight_guidance(domain, complexity)
        injection_text = injection_obj.get("additionalContext", "")

        if PROMPT_CHOICE_ENABLED and CHOICE_STATE_AVAILABLE and injection_text:
            # Build enhanced prompt and present choice (with skill prefix preserved)
            enhanced = build_enhanced_prompt(prompt, injection_text)
            result = build_choice_ui(
                _with_prefix(prompt), _with_prefix(enhanced),
                injection_text, session_id, terminal_id,
            )
        else:
            result = injection_obj

        if DEBUG:
            print("[prompt_enhancement] GUIDANCE mode (framework available in Phase 3)", file=sys.stderr)

    return result


def _clean_prompt_noise(prompt: str) -> str:
    """Clean terminal noise and artifacts from prompt text.

    Removes common terminal output artifacts that shouldn't be part of
    the user's actual prompt for enhancement processing.

    Args:
        prompt: Raw prompt text that may contain terminal artifacts

    Returns:
        Cleaned prompt text with terminal noise removed
    """
    import re

    # Remove terminal symbols
    prompt = re.sub(r'[❯⎿⚙●ⓘ▸▹►▻✻]', ' ', prompt)

    # Remove hook messages (both success and error) - more aggressive
    prompt = re.sub(r'UserPromptSubmit hook [^\n]*', '', prompt)
    prompt = re.sub(r'PreToolUse hook [^\n]*', '', prompt)
    prompt = re.sub(r'SessionStart hook [^\n]*', '', prompt)
    prompt = re.sub(r'hook (success|error):[^\n]*', '', prompt)
    prompt = re.sub(r'⛔ BLOCKED:[^\n]*', '', prompt)

    # Remove command/args metadata blocks
    prompt = re.sub(r'\*\*Command:\*\*[^\n]*', '', prompt)
    prompt = re.sub(r'\*\*Args:\*\*[^\n]*', '', prompt)
    prompt = re.sub(r'Command: /[^\n]*', '', prompt)
    prompt = re.sub(r'Args: [^\n]*', '', prompt)
    prompt = re.sub(r'\*\*Command Name\*\*:[^\n]*', '', prompt)

    # Remove tool call artifacts
    prompt = re.sub(r'●?\s*(Read|Update|Bash|Edit|Write)\([^)]*\)\s*', '', prompt)
    prompt = re.sub(r'Added \d+ lines', '', prompt)
    prompt = re.sub(r'Removed \d+ lines', '', prompt)
    prompt = re.sub(r'Churned for \d+s', '', prompt)
    prompt = re.sub(r'Read \d+ files?', '', prompt)

    # Remove system reminder blocks
    prompt = re.sub(r'<system-reminder>.*?</system-reminder>', '', prompt, flags=re.DOTALL)
    prompt = re.sub(r'<local-command-caveat>.*?</local-command-caveat>', '', prompt, flags=re.DOTALL)

    # Remove file paths and code snippets (common in terminal output)
    prompt = re.sub(r'\.claude[\\\/][^\s]*', '', prompt)
    prompt = re.sub(r'P:\\\\[^\s]*', '', prompt)

    # Remove common shell prompt patterns
    prompt = re.sub(r'\s*~/[\$#]\s*', ' ', prompt)
    prompt = re.sub(r'\s*[\w\-]+@[\w\-]+:[^\$]*\$\s*', ' ', prompt)

    # Remove quoted conversation snippets with ❯
    prompt = re.sub(r'"\s*❯.*?"', '', prompt)
    prompt = re.sub(r'```\s*❯.*?```', '', prompt, flags=re.DOTALL)

    # Remove standalone numbers that look like choice responses mixed in
    prompt = re.sub(r'(?<=\s)\d+(?=\s|$)', '', prompt)

    # Clean up excessive whitespace and trim
    prompt = re.sub(r'\s+', ' ', prompt)
    prompt = re.sub(r'\n\s*\n\s*\n+', '\n\n', prompt)  # Max 2 consecutive newlines
    prompt = prompt.strip()

    return prompt


# Register hook only when router is available
if ROUTER_AVAILABLE:
    @register_hook("prompt_enhancement", priority=8.0)
    def prompt_enhancement_hook(context: HookContext) -> HookResult:
        """Hook function for router integration.

        Priority 8.0 runs after gates (conversation_gate, diagnostic_guard)
        but before most injectors and enforcers.

        Args:
            context: Hook execution context

        Returns:
            HookResult with additional context if enhancement applies
        """
        result = process_prompt(context.data)

        if result and "additionalContext" in result:
            return HookResult(
                context=result["additionalContext"],
                tokens=result.get("tokens", 0)
            )

        return HookResult.empty()


# For standalone execution (via settings.json)
def main() -> None:
    """Main hook entry point for standalone execution."""
    try:
        # Read stdin payload
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid JSON - fail open
        print(json.dumps({}))
        sys.exit(0)

    result = process_prompt(input_data)

    # Output result
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()

"""Plan Injector Module.

Extracted from UserPromptSubmit_router.py.
Provides plan context injection and disambiguation for "the plan" references.
"""

from __future__ import annotations

import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Plan context template for when a plan file is known
PLAN_CONTEXT_TEMPLATE = """
## PLAN CONTEXT
Active plan: {plan_name}
Plan file: {plan_path}

This plan defines the implementation approach. Follow the plan's phases
and tasks rather than improvising.
{content_block}""".strip()

# Maximum characters of plan file content to inline.
# ~3000 chars ≈ 750 tokens — enough for a full small plan without blowing the budget.
PLAN_INLINE_LIMIT = 3000

# All plan-related phrases (broad, for reference)
PLAN_PHRASES = [
    r"\bthe plan\b",
    r"\bthis plan\b",
    r"\bmy plan\b",
    r"\bour plan\b",
    r"\baccording to the plan\b",
    r"\bper the plan\b",
    r"\bfollowing the plan\b",
]

# Ambiguous "the plan" references that trigger disambiguation
AMBIGUOUS_REFS = [
    (r"\bthe plan\b", "which plan?"),
    (r"\bthis plan\b", "which plan?"),
]

# Implicit execution references ("implement the plan", "run the plan", etc.)
_IMPLICIT_EXECUTION_PATTERNS = [
    r"\bimplement(?:ing)?\s+the\s+plan\b",
    r"\bexecut(?:e|ing)\s+the\s+plan\b",
    r"\brun(?:ning)?\s+the\s+plan\b",
    r"\bfollow(?:ing)?\s+the\s+plan\b",
    r"\bdo(?:ing)?\s+the\s+plan\b",
    r"\bstart(?:ing)?\s+the\s+plan\b",
]

# Regex to find explicit file paths in prompts (Windows and Unix style)
_EXPLICIT_PLAN_PATH_RE = re.compile(
    r"[A-Za-z]:[/\x5c][\w/\x5c.-]+\.(?:md|txt|yaml|yml|json|toml)\b"
    r"|/[\w/\x5c.-]+\.(?:md|txt|yaml|yml|json|toml)\b"
    r"|\./[\w/\x5c.-]+\.(?:md|txt|yaml|yml|json|toml)\b",
    re.IGNORECASE,
)

# /plan command pattern
_PLAN_COMMAND_RE = re.compile(r"^\s*/plan\b", re.IGNORECASE)


def extract_explicit_plan_path(prompt: str) -> str | None:
    """Extract an explicit document file path from the prompt.

    Scans the entire prompt for a file path (Windows or Unix) pointing to
    a document file. If found, the user has already specified which file
    they mean — no disambiguation needed.

    Args:
        prompt: User prompt text

    Returns:
        First matched path string, or None if no path found
    """
    match = _EXPLICIT_PLAN_PATH_RE.search(prompt)
    return match.group(0) if match else None


def detect_plan_command(prompt: str) -> bool:
    """Detect if prompt is a /plan command invocation.

    Args:
        prompt: User prompt text

    Returns:
        True if prompt starts with /plan
    """
    return bool(_PLAN_COMMAND_RE.match(prompt))


def references_implicit_execution_plan(prompt: str) -> bool:
    """Detect prompts that reference executing a plan without specifying which.

    Covers phrases like "implement the plan", "execute the plan", "run the plan".

    Args:
        prompt: User prompt text

    Returns:
        True if an implicit execution reference is detected
    """
    prompt_lower = prompt.lower()
    return any(re.search(p, prompt_lower) for p in _IMPLICIT_EXECUTION_PATTERNS)


def detect_plan_reference(prompt: str) -> bool:
    """Detect if prompt references "the plan" ambiguously.

    Returns False immediately if the prompt already contains an explicit file
    path — the user has already specified which plan they mean.

    Args:
        prompt: User prompt text

    Returns:
        True only when an ambiguous reference is present AND no explicit path
    """
    if extract_explicit_plan_path(prompt):
        return False
    prompt_lower = prompt.lower()
    return any(re.search(pattern, prompt_lower) for pattern, _ in AMBIGUOUS_REFS)


def get_disambiguation_question(prompt: str) -> str | None:
    """Get disambiguation question for ambiguous reference.

    Args:
        prompt: User prompt text

    Returns:
        Disambiguation question or None
    """
    prompt_lower = prompt.lower()
    for pattern, question in AMBIGUOUS_REFS:
        if re.search(pattern, prompt_lower):
            return question
    return None


def extract_plan_name(plan_path: str) -> str:
    """Extract plan name from plan file path.

    Args:
        plan_path: Path to plan file

    Returns:
        Plan name or filename stem
    """
    name = Path(plan_path).stem
    for prefix in ["plan-", "opt_", "unified_"]:
        if name.startswith(prefix):
            name = name[len(prefix) :]
    return name


def build_plan_injection(plan_path: str) -> str:
    """Build plan context injection string, inlining file content when available.

    Inlines up to PLAN_INLINE_LIMIT chars of the plan file so the LLM can act
    on its contents without a separate file read. When the file does not exist,
    an explicit marker is injected so the LLM knows it lacks context and should
    state uncertainty rather than fabricate.

    Args:
        plan_path: Path to plan file (can be absolute or relative)

    Returns:
        Plan context injection text with inlined content or error message

    Error handling:
    - OSError/ValueError: Returns error message instead of crashing
    - Empty string: Returns explicit error message
    - Relative paths: Resolved against hooks directory or current working directory
    - Non-existent files: Returns explicit NOT FOUND marker
    """
    # Handle empty string explicitly (Path("") treats as current directory)
    if not plan_path or not plan_path.strip():
        return (
            "## PLAN CONTEXT\n\n"
            "[INVALID PLAN PATH: Empty path provided. "
            "State this uncertainty explicitly — do not infer or fabricate plan content.]"
        )

    # Risk 3: Exception handling for malformed paths
    try:
        path = Path(plan_path)
    except (OSError, ValueError) as e:
        # Handle malformed paths (null bytes, invalid characters, etc.)
        return (
            "## PLAN CONTEXT\n\n"
            f"[INVALID PLAN PATH: The path '{plan_path}' is malformed. "
            f"Error: {type(e).__name__}. "
            "State this uncertainty explicitly — do not infer or fabricate plan content.]"
        )

    # Risk 2: Resolve relative paths against hooks_dir or cwd
    if not path.is_absolute():
        # Try to resolve against hooks directory first
        try:
            hooks_dir = Path(__file__).resolve().parent.parent
            resolved_path = hooks_dir / path
            if resolved_path.exists():
                path = resolved_path.resolve()
            else:
                # Fall back to cwd resolution
                path = Path.cwd() / path
                if not path.exists():
                    return (
                        "## PLAN CONTEXT\n\n"
                        f"[PLAN FILE NOT FOUND: The plan file '{plan_path}' does not exist "
                        f"(relative path resolved to '{path}'). "
                        "State this uncertainty explicitly — do not infer or fabricate plan content.]"
                    )
        except Exception:
            # If resolution fails, try cwd as fallback
            path = Path.cwd() / path

    # Validate path exists and is a file (not directory) before injecting
    if not path.exists() or not path.is_file():
        return (
            "## PLAN CONTEXT\n\n"
            f"[PLAN FILE NOT FOUND: The plan file '{plan_path}' does not exist. "
            "State this uncertainty explicitly — do not infer or fabricate plan content.]"
        )

    plan_name = extract_plan_name(str(path))
    content_block = _read_plan_content(str(path))
    return PLAN_CONTEXT_TEMPLATE.format(
        plan_name=plan_name,
        plan_path=str(path),
        content_block=content_block,
    )


def _read_plan_content(plan_path: str) -> str:
    """Attempt to read and inline plan file content.

    Returns a formatted content block (with header) if the file exists and is
    readable, a [FILE NOT FOUND] marker if the path does not exist, or an empty
    string on unexpected read errors.

    Args:
        plan_path: Path to plan file

    Returns:
        Formatted content string to embed in the plan injection template
    """
    try:
        path = Path(plan_path)
        if not path.exists():
            return (
                "\n\n[PLAN FILE NOT FOUND: The file at the path above does not exist. "
                "State this uncertainty explicitly — do not infer or fabricate plan content.]"
            )
        raw = path.read_text(encoding="utf-8", errors="replace")
        if len(raw) <= PLAN_INLINE_LIMIT:
            content = raw
            truncated = False
        else:
            content = raw[:PLAN_INLINE_LIMIT]
            truncated = True
        block = f"\n\n### Plan Content\n\n{content}"
        if truncated:
            block += (
                f"\n\n... [truncated at {PLAN_INLINE_LIMIT} chars — read the full file for details]"
            )
        return block
    except OSError:
        return ""


def get_active_plan_path(data: dict) -> str | None:
    """Get active plan path from hook context data.

    Args:
        data: Hook context data dict

    Returns:
        Plan file path or None
    """
    plan_path = (
        data.get("plan_path")
        or data.get("planPath")
        or data.get("active_plan")
        or data.get("activePlan")
    )
    return plan_path if plan_path and isinstance(plan_path, str) else None


def inject_plan_context(_prompt: str) -> dict:
    """Build a structured plan template for /plan command invocations.

    Args:
        _prompt: User prompt (should start with /plan) - unused, reserved for future

    Returns:
        Dict with 'context' key containing a 7-section plan template
    """
    context = (
        "## 1. Problem Statement\n\n"
        "## 2. Context Analysis\n\n"
        "## 3. Proposed Solution\n\n"
        "## 4. Implementation Plan\n\n"
        "## 5. Risk Assessment\n\n"
        "## 6. Success Criteria\n\n"
        "## 7. Dependencies\n"
    )
    return {"context": context}


@register_hook("plan_injector", priority=10.1)
def run_plan_injector(context: HookContext) -> HookResult | None:
    """Main entry point for plan injector.

    Decision tree:
    1. Explicit file path in prompt + plan reference  ->  inject that plan's context
    2. Ambiguous "the/this plan" (no explicit path)   ->  ask for disambiguation
    3. Active plan path in session context            ->  inject active plan context
    4. Otherwise                                      ->  no-op

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with plan context or disambiguation, or None
    """
    # 1. Explicit path provided — user already specified the plan
    explicit_path = extract_explicit_plan_path(context.prompt)
    if explicit_path and re.search(r"\bplan\b", context.prompt, re.IGNORECASE):
        context_text = build_plan_injection(explicit_path)
        return HookResult(context=context_text, tokens=estimate_tokens(context_text))

    # 2. Ambiguous "the/this plan" without explicit path
    if detect_plan_reference(context.prompt):
        disambiguation = get_disambiguation_question(context.prompt)
        if disambiguation:
            return HookResult(
                context=f"**Plan Disambiguation**: {disambiguation}\n\nWhich plan are you referring to? Please specify the plan name or path.",
                tokens=50,
            )

    # 3. Active plan from session context
    plan_path = get_active_plan_path(context.data)
    if not plan_path:
        return None

    context_text = build_plan_injection(plan_path)
    return HookResult(context=context_text, tokens=estimate_tokens(context_text))


def estimate_tokens(text: str) -> int:
    """Estimate token count. Rough estimate: ~4 characters per token."""
    return len(text) // 4

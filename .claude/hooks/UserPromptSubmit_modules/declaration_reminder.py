"""
Declaration Reminder - UserPromptSubmit hook

Prevents "I'll update the template" declarations without execution by injecting
reminders when arch/ template update declarations are detected.

Problem: LLMs respond with intent ("I'll update the template") but stop at verbal
agreement without invoking Write/Edit tools (Declaration ≠ Execution).

Solution: Detect declaration patterns and inject reminder requiring Read → Edit → Diff.
Also stores declaration state for PreToolUse arch-first enforcer hook.
"""

import json
import os
import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# State directory for declaration tracking
STATE_DIR = Path(__file__).resolve().parent.parent / "state"

# Declaration patterns without execution - saying "I’ll do X" without follow-through
# Note: Use [‘’] with straight apostrophe (chr(39)) before curly (chr(8217)) to match both
STRAIGHT_APOS = chr(39)  # U+0027 APOSTROPHE
CURLY_APOS = chr(8217)  # U+2019 RIGHT SINGLE QUOTATION MARK

# Target keyword alternatives
_ARCH_KEYWORDS = r"(?:template|arch/|arch(?:\s+file)?|SKILL\.md)"

DECLARATION_PATTERNS = [
    rf"\bi[{STRAIGHT_APOS}{CURLY_APOS}]ll\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bi[{STRAIGHT_APOS}{CURLY_APOS}]d\s+(?:like to|love to|want to|going to)\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bi\s+(?:will|shall|going to)\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\blet\s+me\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bi[{STRAIGHT_APOS}{CURLY_APOS}]m\s+(?:going to|planning to|will)\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bi\s+should\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"[Nn]eed\s+to\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bhave\s+to\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
    rf"\bmust\s+(?:update|edit|modify|add to|fix)\s+(?:the\s+)?{_ARCH_KEYWORDS}",
]

# Compiled patterns for performance
_COMPILED_DECLARATIONS = [re.compile(p, re.IGNORECASE) for p in DECLARATION_PATTERNS]


def _get_terminal_id(context) -> str:
    """Extract terminal ID from hook context."""
    return (
        context.data.get("terminal_id")
        or context.data.get("terminalId")
        or context.data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or "default"
    )


def _get_state_file(terminal_id: str) -> Path:
    """Get path to declaration state file for terminal."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id))
    return STATE_DIR / f"arch_declaration_{safe_id}.json"


def _extract_arch_path(text: str) -> str | None:
    """Extract the arch path from a declaration text."""
    # First check for explicit SKILL.md mentions
    if re.search(r"SKILL\.md", text, re.IGNORECASE):
        return "SKILL.md"

    # Look for explicit path mentions
    # Common words that should NOT be treated as paths
    stop_words = {"the", "a", "an", "this", "that", "my", "our", "file", "doc"}

    path_patterns = [
        # "modify arch/something.md" - requires .md extension
        r"(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?(?:arch/|template/)?([^\s`']+?\.md)",
        # "template file at X" or "arch/ file at X" - capture path with slashes or .md
        r"(?:template|arch/)\s+(?:file|at|in)\s+[`']?([^\s`']+?)[`']?",
        # "modify X template" - X must look like a path (contains / or .md)
        r"(?:update|edit|modify)\s+[`']?([^\s`']+?(?:/|\.md))[`']?\s+(?:template|file)",
    ]

    for pattern in path_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            path = match.group(1)
            # Clean up common path patterns
            path = path.rstrip("'`\".")
            # Skip if it's a common stop word
            if path.lower() in stop_words:
                continue
            # Add arch/ prefix if path doesn't start with / or ~ or . or arch/
            if not path.startswith(("/", "~", ".", "arch/", "template/")):
                # Check if the original text had "arch/" before this path
                if re.search(r"arch/", text, re.IGNORECASE):
                    path = "arch/" + path
            return path

    # Default to common template location if no explicit path found
    return "arch/base.md"


def _store_declaration_state(terminal_id: str, path: str) -> None:
    """Store declaration state for PreToolUse hook to check."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = _get_state_file(terminal_id)

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"path": path, "timestamp": None}, f)
    except OSError:
        pass  # Fail silently if state storage fails


def _detect_template_declaration(text: str) -> bool:
    """Check if text contains a template update declaration without execution."""
    if not text:
        return False

    for pattern in _COMPILED_DECLARATIONS:
        if pattern.search(text):
            return True
    return False


@register_hook("declaration_reminder", priority=8.0)
def declaration_reminder_hook(context: HookContext) -> HookResult:
    """Hook function that injects reminder when template declarations are detected.

    Args:
        context: HookContext with prompt and session data

    Returns:
        HookResult with reminder context if declaration detected, empty otherwise
    """
    prompt = context.prompt

    # Check for template update declarations
    if not _detect_template_declaration(prompt):
        return HookResult.empty()

    # Extract arch path from declaration
    arch_path = _extract_arch_path(prompt)

    # Store declaration state for PreToolUse hook
    terminal_id = _get_terminal_id(context)
    _store_declaration_state(terminal_id, arch_path)

    # Inject reminder to prevent lazy declaration
    reminder = f"""
**⚠️ TEMPLATE UPDATE DECLARATION DETECTED**

You just declared you would update a template file. **Declaration ≠ Execution**.

To prevent repeating this mistake, you MUST:
1. **Read** the template file first: `{arch_path}`
2. **Edit/Write** the change with diff
3. **Show** the diff with explanation
4. **State:** "Template updated in {arch_path} so I won't repeat this mistake."

Do NOT respond with just "I'll update the template" - actually invoke the tools.

**Enforcement**: Other tools will be blocked until you update `{arch_path}`.
"""

    return HookResult(context=reminder)

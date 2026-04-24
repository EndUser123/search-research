"""Path Syntax Corrector - Detects and fixes Windows path syntax errors.

When user types bash commands with malformed Windows paths (missing backslashes),
this hook detects the error and applies a correction based on confidence:

High confidence (2+ known directory names): Auto-correct without prompting
Low confidence (0-1 known directory names): Show choice UI for user approval

Multi-terminal safe: Uses prompt_choice_state.py for session+terminal scoped state.
No TTL: State persists until replaced or explicitly cleared.
Stale-data immune: Every prompt overwrites prior state.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Add parent directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from __lib.prompt_choice_state import (  # noqa: E402
    clear_prompt_choice,
    get_pending_choice,
    save_prompt_choice,
)

# Windows path pattern with drive letter
# Matches: P:.claudehooksscanners... (missing backslashes after drive and separators)
WINDOWS_PATH_RE = re.compile(r"\b[A-Z]:[a-zA-Z0-9_./\\]+")

# Known directory names to detect (order matters: longer names first)
# Used for both path correction and confidence scoring
# NOTE: strawberry_validator entries removed during decommission (httpx policy violation)
KNOWN_DIRS = [
    "scanners",
    "StopHook",
    "hooks",
    ".claude",
    "docs/adrs",
]

# Confidence threshold for auto-correction
# Paths with >= this many known dirs get auto-corrected without prompting
AUTO_CORRECT_THRESHOLD = 2


def fix_windows_path(path: str) -> str:
    """
    Fix Windows path with missing backslashes by inserting separators
    at known directory boundaries.

    Examples:
        P:.claudehooksscannersMyScanner.py
            -> P:\\.claude\\hooks\\scanners\\MyScanner.py
        P:\\.claude\\hooks\\test.py (already correct, no change)

    Args:
        path: Raw path string (may have missing backslashes)

    Returns:
        Path with backslashes inserted at directory boundaries
    """
    if not path:
        return path

    # Check if path is already well-formed (has separators between components)
    # If path has backslashes beyond the drive letter separator, it's likely already correct
    # Example: P:\.claude\hooks has \ at positions 2 and 10 - skip processing
    if len(path) > 3 and path[1] == ":" and path[2] in ("\\", "/"):
        # Check for additional backslashes in the path (beyond position 2)
        if "\\" in path[3:]:
            return path  # Already well-formed, skip processing

    # Extract drive letter and rest of path
    if len(path) >= 2 and path[1] == ":":
        drive = path[:2]  # e.g., "P:"
        rest = path[2:]  # e.g., ".claudehooksscannersmy_scanner.py"
    else:
        # Not a Windows path, return as-is
        return path

    # Insert backslashes at directory boundaries
    result = rest
    for dirname in KNOWN_DIRS:
        # Only insert backslash BEFORE directory name, not after
        # This prevents adding \ after file extensions like .py
        result = result.replace(dirname, "\\" + dirname)

    # Remove leading backslash if present (from first directory)
    if result.startswith("\\"):
        result = result[1:]

    # Add backslash after drive letter
    return drive + "\\" + result


@register_hook("path_syntax_corrector", priority=0.5)
def path_syntax_corrector(context: HookContext) -> HookResult:
    """Detect and fix Windows path syntax errors in bash commands.

    High confidence (2+ known dirs): Auto-corrects immediately
    Low confidence (0-1 known dirs): Shows choice UI, requires user input
    """
    prompt = context.prompt or ""
    data = context.data

    # Turn 2: User responded with choice
    if prompt.strip() in ("0", "1"):
        return _handle_choice_response(prompt.strip(), data)

    # Turn 1: Detect path syntax errors
    return _detect_and_offer_correction(prompt, data)


def _calculate_confidence(path: str) -> int:
    """
    Calculate confidence score for path correction.

    Higher confidence = more likely to be a real path error that should be auto-corrected.

    Args:
        path: The malformed path string

    Returns:
        Number of known directory names found in the path
    """
    count = 0
    path_lower = path.lower()
    for dirname in KNOWN_DIRS:
        if dirname.lower() in path_lower:
            count += 1
    return count


def _detect_and_offer_correction(prompt: str, data: dict) -> HookResult:
    """Detect paths with missing backslashes and offer correction or auto-correct."""

    # Find all Windows path patterns
    matches = WINDOWS_PATH_RE.findall(prompt)
    if not matches:
        return HookResult.empty()

    # Check if any path has syntax errors (missing backslashes)
    original_paths = []
    corrected_paths = []

    for path in matches:
        # Detect missing backslashes after drive letter
        # Example: "P:.claude" should be "P:\.claude"
        if ":" in path:
            # Check if path has drive letter but no backslash after it
            # Corrected path should start with "X:\"
            try:
                corrected = fix_windows_path(path)
                if corrected != path:
                    original_paths.append(path)
                    corrected_paths.append(corrected)
            except Exception:
                # If correction fails, skip this path
                continue

    if not original_paths:
        return HookResult.empty()

    # Build corrected prompt
    corrected_prompt = prompt
    for orig, corr in zip(original_paths, corrected_paths, strict=True):
        corrected_prompt = corrected_prompt.replace(orig, corr)

    # Calculate confidence based on first path
    confidence = _calculate_confidence(original_paths[0])

    # High confidence: Auto-correct without prompting
    if confidence >= AUTO_CORRECT_THRESHOLD:
        original = original_paths[0]
        corrected = corrected_paths[0]
        path_count = len(original_paths)
        auto_note = f" ({path_count} paths)" if path_count > 1 else ""

        auto_ui = f"**✓ Auto-corrected path{auto_note}**\n  {original} → {corrected}\n"

        return HookResult(
            context={"replacePrompt": corrected_prompt, "additionalContext": auto_ui},
            tokens=len(auto_ui) // 4,
        )

    # Low confidence: Show choice UI for user approval
    original = original_paths[0]
    corrected = corrected_paths[0]

    # If multiple paths found, note it
    path_count = len(original_paths)
    path_note = f" ({path_count} paths detected)" if path_count > 1 else ""

    choice_ui = f"""**⚠️ Path Syntax Detected{path_note}**

Found path with missing backslashes:
  {original}

Corrected to:
  {corrected}

**Action Required**

0 - Use corrected path (recommended)
1 - Use your original path

---
"""

    # Save state for Turn 2
    session_id = data.get("session_id") or data.get("sessionId")
    terminal_id = data.get("terminal_id") or data.get("terminalId")
    save_prompt_choice(prompt, corrected_prompt, choice_ui, session_id, terminal_id)

    return HookResult(
        context={"replacePrompt": corrected_prompt, "additionalContext": choice_ui},
        tokens=len(choice_ui) // 4,
    )


def _handle_choice_response(choice: str, data: dict) -> HookResult:
    """Handle user's choice from Turn 1."""

    # Load pending state
    session_id = data.get("session_id") or data.get("sessionId")
    terminal_id = data.get("terminal_id") or data.get("terminalId")

    state = get_pending_choice(session_id, terminal_id)
    if not state:
        return HookResult.empty()

    # Get prompts from state
    original_prompt = state.get("original_prompt", "")
    enhanced_prompt = state.get("enhanced_prompt", "")

    # User chose corrected path (0) or original path (1)
    if choice == "0":
        result_prompt = enhanced_prompt
    else:  # choice == "1"
        result_prompt = original_prompt

    # Clear state
    clear_prompt_choice(session_id, terminal_id)

    return HookResult(
        context={"replacePrompt": result_prompt, "additionalContext": result_prompt},
        tokens=len(result_prompt) // 4,
    )

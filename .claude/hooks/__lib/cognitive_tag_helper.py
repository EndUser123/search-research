"""Cognitive tag helper - lightweight tag lookup for UserPromptSubmit hooks.

Reuses logic from tag_registry.py to get active tags for a prompt.
Fails open: returns empty list if any error.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

try:
    from UserPromptSubmit_modules.tag_registry import (
        FRAMEWORK_TAGS,
        get_framework_tags_for_enhancer,
        TAG_PATTERN,
    )
    from UserPromptSubmit_modules.cognitive_enhancers import (
        _detect_intent,
        _select_enhancers,
        _load_config,
        _ENHANCERS,
    )
    from UserPromptSubmit_modules.base import HookContext
except Exception:
    # Fail open - return empty on import error
    FRAMEWORK_TAGS = {}
    get_framework_tags_for_enhancer = lambda name: []
    _detect_intent = lambda prompt: {}
    _select_enhancers = lambda intent, config: []
    _load_config = lambda: {}
    _ENHANCERS = []
    HookContext = dict


def get_active_tags_for_prompt(prompt: str) -> list[str]:
    """Get active cognitive framework tags for a prompt.

    Args:
        prompt: User's prompt text

    Returns:
        List of active tag strings (e.g., ["CAL", "CYNE", "ASUM"])
        Empty list if no tags detected or on any error.
    """
    try:
        if not prompt or not prompt.strip():
            return []

        config = _load_config()
        if not config.get("enabled", True):
            return []

        intent = _detect_intent(prompt)
        selected = _select_enhancers(intent, config)

        tags: list[str] = []
        for enhancer in selected:
            enhancer_tags = get_framework_tags_for_enhancer(enhancer.name)
            for tag in enhancer_tags:
                if tag not in tags:
                    tags.append(tag)

        return tags

    except Exception:
        # Fail open - any error returns empty list
        return []


def format_tags_for_instruction(tags: list[str]) -> str:
    """Format tags into the compact instruction block.

    Args:
        tags: List of tag strings (e.g., ["CAL", "CYNE"])

    Returns:
        Formatted instruction block or empty string if no tags.
    """
    # Filter out empty strings
    valid_tags = [t for t in tags if t]
    if not valid_tags:
        return ""

    tag_str = " ".join(f"[{t}]" for t in valid_tags)
    return f'''<cognitive-tags active="{tag_str}">
Append this exact line at the end of your response:

Tags: {tag_str}

</cognitive-tags>'''


def get_cognitive_tag_instruction(prompt: str) -> str:
    """Get the full cognitive tag instruction for a prompt.

    Args:
        prompt: User's prompt text

    Returns:
        Instruction block to inject, or empty string if no tags active.
    """
    tags = get_active_tags_for_prompt(prompt)
    return format_tags_for_instruction(tags)


# Self-test when run directly
if __name__ == "__main__":
    import json

    test_prompts = [
        ("", []),
        ("fix the bug in auth.py", ["CAL", "ANCH"]),  # diagnostic + impl
        ("debug why the login fails", ["CAL"]),  # diagnostic
        ("build a new API endpoint", ["ANCH", "INV", "FENC"]),  # implementation
        ("analyze this complex problem", ["CYNE", "CAL"]),  # cynefin
    ]

    print("Testing cognitive_tag_helper...")
    for prompt, expected in test_prompts:
        tags = get_active_tags_for_prompt(prompt)
        instruction = format_tags_for_instruction(tags)
        print(f"\nPrompt: {prompt!r}")
        print(f"Tags: {tags}")
        if instruction:
            print(f"Instruction (first 100 chars): {instruction[:100]}...")

    print("\nAll tests completed.")

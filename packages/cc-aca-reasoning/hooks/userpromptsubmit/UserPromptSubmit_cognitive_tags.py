"""Cognitive Tags UserPromptSubmit hook - inject tag instruction for first reply.

This hook surfaces cognitive framework tags to the user by injecting a compact
instruction that tells Claude to append tags to its FIRST reply only.

Reuses logic from cognitive_enhancers.py and tag_registry.py.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


from pathlib import Path
import sys

# Add hooks directory to path
_HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

try:
    from __lib.cognitive_tag_helper import get_active_tags_for_prompt, format_tags_for_instruction
except Exception:
    # Fail open on import error
    def get_active_tags_for_prompt(prompt: str) -> list[str]:
        return []
    def format_tags_for_instruction(tags: list[str]) -> str:
        return ""


# Skip non-substantive turns (greetings, meta, control commands)
def _is_non_substantive_turn(prompt: str) -> bool:
    """Detect non-substantive prompts that shouldn't receive tag injection."""
    if not prompt or not prompt.strip():
        return True

    stripped = prompt.strip().lower()

    # Greetings
    greetings = {
        "hi", "hello", "hey", "yo", "sup", "hiya", "greetings",
        "good morning", "good afternoon", "good evening",
    }
    if stripped in greetings:
        return True

    # Single-word meta commands
    meta_commands = {
        "thanks", "thank you", "ok", "okay", "sure", "yes", "no",
        "done", "exit", "quit", "cancel", "nevermind", "never mind",
    }
    if stripped in meta_commands:
        return True

    # Slash commands that are meta (not content)
    if stripped.startswith("/") and len(stripped) < 20:
        meta_slashes = {
            "/model", "/help", "/clear", "/compact", "/config",
            "/think", "/plan", "/review", "/retry",
        }
        for cmd in meta_slashes:
            if stripped.startswith(cmd):
                return True

    return False


@register_hook("cognitive_tags", priority=15.0)
def cognitive_tags(context: HookContext) -> HookResult:
    """Inject cognitive tag instruction for first reply.

    Gets active tags from cognitive_enhancers detection and formats
    them into a compact instruction block. Tags appear on FIRST
    reply only - later replies for same prompt are clean.
    """
    prompt = context.prompt or ""

    # Skip non-substantive turns
    if _is_non_substantive_turn(prompt):
        return HookResult.empty()

    # Get active tags
    tags = get_active_tags_for_prompt(prompt)
    if not tags:
        return HookResult.empty()

    # Format instruction block
    instruction = format_tags_for_instruction(tags)
    if not instruction:
        return HookResult.empty()

    # Token estimate: ~4 chars per token
    tokens = len(instruction) // 4

    return HookResult(context=instruction, tokens=tokens, priority=15.0)

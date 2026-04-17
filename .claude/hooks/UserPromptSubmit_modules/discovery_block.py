"""Discovery-first enforcement hook.

Blocks implementation prompts until discovery tools are used.

Adversarial review fixes applied:
- LOGIC-001: Allow-list for discovery tools prevents deadlock
- IO-001: Defensive session_id validation
- STATE-001: Session-scoped state file prevents cross-terminal corruption
"""

import os
import re
import sys
from pathlib import Path

# Type hints for base classes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from UserPromptSubmit_modules.base import HookContext, HookResult

# Regex detection pattern for implementation intent
IMPL_PATTERNS = r'\b(?:create|write|implement|add|build|update|edit|modify|change|patch|fix|refactor|remove|delete)\b'

# Discovery tools allow-list (LOGIC-001 fix)
DISCOVERY_TOOLS = ['Glob', 'Grep', '/explore', '/search', '/research', '/discover']
DISCOVERY_PATTERNS = [
    r'\b(?:Glob|Grep)\s+',  # Tool invocations
    r'^/(?:explore|search|research|discover)\s+',  # Skill commands
]

# Escape hatch patterns
ESCAPE_HATCH_FLAG = '--skip-discovery'
ESCAPE_HATCH_ENV = 'DISCOVERY_OVERRIDE'


def get_session_id(data):
    """Extract session_id from hook input with validation (IO-001 fix).

    Args:
        data: Hook input dictionary (from HookContext.data)

    Returns:
        str: session_id if found, None otherwise
    """
    # Try multiple possible locations for session_id
    session_id = (
        data.get('session_id') or
        data.get('hook_input', {}).get('session_id') or
        data.get('data', {}).get('session_id')
    )

    if not session_id:
        return None

    # Type coercion for filename safety
    return str(session_id)


def is_discovery_tool(prompt):
    """Check if prompt invokes discovery tools (allow-list).

    Args:
        prompt: User prompt text

    Returns:
        bool: True if prompt matches discovery tool patterns
    """
    if not prompt:
        return False

    return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in DISCOVERY_PATTERNS)


def check_discovery_state(session_id):
    """Check if discovery completed for this session.

    Args:
        session_id: Current session identifier

    Returns:
        bool: True if discovery completed, False otherwise
    """
    if not session_id:
        return False  # Advisory mode: no session_id means no discovery tracking

    # Import json lazily
    import json

    # Session-scoped state file (STATE-001 fix)
    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(session_id))
    state_file = Path.home() / '.claude' / f'discovery_state_{safe_session}.json'

    if not state_file.exists():
        return False  # No discovery yet

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Session_id validation (STATE-002 fix)
        if state.get('session_id') != session_id:
            return False  # Session mismatch, treat as no discovery

        return state.get('discovery_done', False)
    except (json.JSONDecodeError, KeyError, IOError):
        return False  # Corrupted state, treat as no discovery


def extract_topic_from_prompt(prompt):
    """Extract topic from prompt for retry suggestion.

    Args:
        prompt: User prompt text

    Returns:
        str: Extracted topic or empty string
    """
    # Extract nouns/phrases after implementation verbs
    match = re.search(IMPL_PATTERNS, prompt, re.IGNORECASE)
    if match:
        # Get text after the verb
        after_verb = prompt[match.end():]
        # Extract first meaningful phrase (simple heuristic)
        topic_match = re.search(r'["\']?([a-zA-Z0-9_+\s]+?)["\']?', after_verb)
        if topic_match:
            return topic_match.group(1).strip()[:50]  # Limit length

    return ""


def process_prompt(context: 'HookContext') -> 'HookResult':
    """Main hook entry point.

    Args:
        context: HookContext with prompt, session_id, terminal_id

    Returns:
        HookResult with block decision or None (to allow)
    """
    from UserPromptSubmit_modules.base import HookResult

    prompt = context.prompt
    session_id = get_session_id(context.data)

    # Check escape hatch first
    if ESCAPE_HATCH_FLAG in prompt:
        return HookResult.empty()  # Allow with escape hatch

    if os.getenv(ESCAPE_HATCH_ENV, '').lower() == 'true':
        return HookResult.empty()  # Allow with escape hatch

    # Allow discovery tools unconditionally (LOGIC-001 fix)
    if is_discovery_tool(prompt):
        return HookResult.empty()  # Allow discovery tools to execute

    # Check for implementation intent
    if re.search(IMPL_PATTERNS, prompt, re.IGNORECASE):
        # Check discovery state
        if check_discovery_state(session_id):
            return HookResult.empty()  # Discovery done, allow

        # Block implementation without discovery
        topic = extract_topic_from_prompt(prompt)
        suggested_query = f'/explore "{topic}"' if topic else '/explore "your topic"'

        block_message = (
            f"**Discovery First**\n\n"
            f"Use discovery tools (`/explore`, `/search`, `/research`, `/discover`, `Glob`, `Grep`) before implementing.\n\n"
            f"Suggested: `{suggested_query}`\n\n"
            f"Escape hatch: Add `{ESCAPE_HATCH_FLAG}` to your prompt."
        )

        return HookResult(context=block_message, tokens=150)

    # Allow non-implementation prompts
    return HookResult.empty()


# Register the hook
from UserPromptSubmit_modules.registry import register_hook

@register_hook("discovery_block", priority=6.0)
def discovery_block_hook(context: 'HookContext') -> 'HookResult':
    """Wrapper function for registry compatibility."""
    return process_prompt(context)

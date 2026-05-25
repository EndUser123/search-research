# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""UserPromptSubmit hook to enforce discovery-first workflow.

Blocks implementation prompts until discovery tools (/search, /discover, Glob, Grep) are used.

Adversarial review fixes applied:
- LOGIC-001: Allow-list for discovery tools prevents deadlock
- IO-001: Defensive session_id validation
- FM-001: N/A (this hook reads state, doesn't write)
"""

import json
import os
import re
from pathlib import Path

# Regex detection pattern for implementation intent
IMPL_PATTERNS = r'\b(?:create|write|implement|add|build)\s+(?:file|function|class|code|script|test)'

# Discovery tools allow-list (LOGIC-001 fix)
DISCOVERY_TOOLS = ['Glob', 'Grep', '/search', '/discover']
DISCOVERY_PATTERNS = [
    r'\b(?:Glob|Grep)\s+',  # Tool invocations
    r'^/(?:search|discover)\s+',  # Skill commands
]

# Escape hatch patterns
ESCAPE_HATCH_FLAG = '--skip-discovery'
ESCAPE_HATCH_ENV = 'DISCOVERY_OVERRIDE'


def get_session_id(data):
    """Extract session_id from hook input with validation (IO-001 fix).

    Args:
        data: Hook input dictionary

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

    # Session-scoped state file (STATE-001 fix)
    state_file = Path.home() / '.claude' / f'discovery_state_{session_id}.json'

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


def main(hook_input):
    """Main hook entry point.

    Args:
        hook_input: Dictionary containing prompt and session data

    Returns:
        dict or None: Block decision if blocking, None to allow
    """
    prompt = hook_input.get('prompt', '')
    session_id = get_session_id(hook_input)

    # Check escape hatch first
    if ESCAPE_HATCH_FLAG in prompt:
        return None  # Allow with escape hatch

    if os.getenv(ESCAPE_HATCH_ENV, '').lower() == 'true':
        return None  # Allow with escape hatch

    # Allow discovery tools unconditionally (LOGIC-001 fix)
    if is_discovery_tool(prompt):
        return None  # Allow discovery tools to execute

    # Check for implementation intent
    if re.search(IMPL_PATTERNS, prompt, re.IGNORECASE):
        # Check discovery state
        if check_discovery_state(session_id):
            return None  # Discovery done, allow

        # Block implementation without discovery
        topic = extract_topic_from_prompt(prompt)
        suggested_query = f'/{topic}' if topic else '/search "your topic"'

        return {
            "decision": "block",
            "reason": "Discovery first: Use discovery tools (/search, /discover, Glob, Grep) before implementing",
            "suggested_query": suggested_query,
            "retry_hint": f"Run {suggested_query} first, then retry your prompt"
        }

    # Allow non-implementation prompts
    return None


if __name__ == '__main__':
    # For manual testing
    import sys

    test_input = {
        'prompt': ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'create test file',
        'session_id': 'test-session-123'
    }

    result = main(test_input)
    if result:
        print(f"BLOCKED: {result['reason']}")
        if result.get('suggested_query'):
            print(f"Suggestion: {result['suggested_query']}")
    else:
        print("ALLOWED")

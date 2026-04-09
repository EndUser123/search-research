"""PreToolUse hook to track discovery tool usage.

Tracks when discovery tools (Glob, Grep, /search, /discover) are used and sets
discovery_done flag in session-scoped state file.

Adversarial review fixes applied:
- LOGIC-001: PreToolUse timing ensures discovery executes before UserPromptSubmit check
- STATE-001: Session-scoped filename prevents cross-terminal corruption
- FM-001: Atomic write pattern prevents concurrent write corruption
- IO-001: Defensive session_id validation
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import time

# Discovery tools to track
DISCOVERY_TOOLS = ['Glob', 'Grep', '/search', '/discover']


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
        data.get('tool_input', {}).get('session_id') or
        data.get('data', {}).get('session_id')
    )

    if not session_id:
        return None

    # Type coercion for filename safety
    return str(session_id)


def write_state_atomic(session_id, discovery_done=True):
    """Write state file atomically using temp file + rename (FM-001 fix).

    Args:
        session_id: Current session identifier
        discovery_done: Whether discovery has been completed

    Returns:
        bool: True if write succeeded, False otherwise
    """
    state_file = Path.home() / '.claude' / f'discovery_state_{session_id}.json'

    # Create state data
    state = {
        "session_id": session_id,
        "discovery_done": discovery_done,
        "last_updated": time.time()
    }

    try:
        # Atomic write pattern: temp file + os.replace
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', dir=state_file.parent) as tmp:
            json.dump(state, tmp)
            tmp_path = tmp.name

        # Atomic replace (os.replace is atomic on POSIX and Windows)
        os.replace(tmp_path, state_file)
        return True

    except (IOError, OSError) as e:
        # Log error but don't fail hook
        print(f"[Discovery Tracker] Failed to write state: {e}", file=sys.stderr)
        return False


def main(hook_input):
    """Main hook entry point.

    Args:
        hook_input: Dictionary containing tool and session data

    Returns:
        None
    """
    tool_name = hook_input.get('tool', '')

    # Check if this is a discovery tool
    if tool_name not in DISCOVERY_TOOLS:
        return  # Not a discovery tool

    # Extract session_id
    session_id = get_session_id(hook_input)
    if not session_id:
        return  # Advisory mode: no session_id means no discovery tracking

    # Write state atomically
    write_state_atomic(session_id, discovery_done=True)


if __name__ == '__main__':
    # For manual testing
    import sys

    test_tool = sys.argv[1] if len(sys.argv) > 1 else 'Glob'
    test_input = {
        'tool': test_tool,
        'session_id': 'test-session-123'
    }

    print(f"Testing tool: {test_tool}")
    result = main(test_input)

    if result is None:
        print("Hook executed (no return value expected)")
    else:
        print(f"Unexpected result: {result}")

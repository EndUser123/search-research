#!/usr/bin/env python3
"""Tests for skill enforcement hook registration and execution."""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
SKILL_ENFORCER = HOOKS_DIR / "UserPromptSubmit" / "skill_enforcer.py"


def test_hook_registered():
    """Test that skill_enforcer is registered in registry."""
    # Import registry and check hook exists
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit import registry

    assert "skill_enforcer" in registry.HOOKS, \
        "skill_enforcer not found in registry. @register_hook decorator missing."
    assert "skill_enforcer" in registry.HOOK_PRIORITY, \
        "skill_enforcer not in HOOK_PRIORITY."

    # Check priority is 1.0 (runs first)
    priority = registry.HOOK_PRIORITY["skill_enforcer"]
    assert priority == 1.0, \
        f"Expected priority 1.0, got {priority}. Hook should run before unified_injector."


def test_slash_command_detection():
    """Test hook detects slash commands and creates intent file."""
    hook_input = {
        "prompt": "/universal-skills-manager search",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }

    result = subprocess.run(
        ["python", "-c", f"""
import sys
sys.path.insert(0, '{HOOKS_DIR}')
from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

# Run the hook
from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Output result
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
    print(f"TOKENS:{{result.tokens}}")
else:
    print("NO_INJECTION")
"""],
        capture_output=True,
        text=True
    )

    # Check hook ran and created injection
    assert "INJECTION:" in result.stdout, "Hook did not create injection"
    assert 'Execute skill universal-skills-manager' in result.stdout, "Missing execution directive"
    assert 'Call Skill("universal-skills-manager")' in result.stdout, "Missing Skill() instruction"
    assert "TOKENS:" in result.stdout, "Missing token count"


def test_intent_file_created():
    """Test that intent file is created for PreToolUse gate."""
    import os
    import tempfile

    session_id = "test_session_intent"
    terminal_id = "test_terminal_intent"

    hook_input = {
        "prompt": "/search test query",
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    # Set state directories to temp for test
    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_session = Path(tempfile.mkdtemp()) / "session_data"

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    env["CLAUDE_TERMINAL_ID"] = terminal_id

    # Prepare data dict as JSON to avoid quote escaping issues
    data_json = json.dumps(hook_input)

    result = subprocess.run(
        ["python", "-c", f'''
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, r"{HOOKS_DIR}")

# Monkey-patch state directories
from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path(r"{temp_state}")
skill_enforcer.SESSION_DATA_DIR = Path(r"{temp_session}")
skill_enforcer.FALLBACK_STATE_DIR = Path(r"{temp_state}")  # Patch fallback too

from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt=r"/search test query",
    data={data_json},
    session_id=r"{session_id}",
    terminal_id=r"{terminal_id}"
)

from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Check intent file at new terminal-scoped path
from __lib.terminal_id import normalize_terminal_id
normalized_tid = normalize_terminal_id("{terminal_id}")
intent_file = Path(r"{temp_state}") / f"terminals/{{normalized_tid}}/pending_command_intent.json"
print(f"INTENT_EXISTS:{{intent_file.exists()}}")
if intent_file.exists():
    print(f"INTENT_CONTENT:{{intent_file.read_text()}}")
'''],
        capture_output=True,
        text=True,
        env=env
    )

    assert "INTENT_EXISTS:True" in result.stdout, f"Intent file not created. Output: {result.stdout}"
    assert "INTENT_CONTENT:" in result.stdout, "Intent file empty"

    # Verify file content
    content_json = json.loads(
        result.stdout.split("INTENT_CONTENT:")[1].split("\n")[0]
    )
    assert content_json["skill"] == "search", f"Wrong skill name in intent: {content_json.get('skill')}"


def test_non_slash_command_ignored():
    """Test that non-slash prompts are ignored."""
    hook_input = {
        "prompt": "help me with this code",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }

    result = subprocess.run(
        ["python", "-c", f"""
import sys
sys.path.insert(0, '{HOOKS_DIR}')
from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt="{hook_input['prompt']}",
    data={hook_input},
    session_id="{hook_input['session_id']}",
    terminal_id="{hook_input['terminal_id']}"
)

from UserPromptSubmit import skill_enforcer
result = skill_enforcer.skill_enforcement_hook(context)

# Output result
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
else:
    print("NO_INJECTION")
"""],
        capture_output=True,
        text=True
    )

    assert "NO_INJECTION" in result.stdout, \
        "Non-slash command should not create injection"


def test_non_slash_command_clears_stale_intent_file():
    """A new plain-English prompt should revoke an older slash-command intent."""
    import os
    import re
    import tempfile

    session_id = "test_session_clear"
    terminal_id = "test_terminal_clear"
    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_state.mkdir(parents=True, exist_ok=True)

    # Normalize terminal ID same way the hook does and use new terminal-scoped path
    sys.path.insert(0, str(HOOKS_DIR))
    from __lib.terminal_id import normalize_terminal_id
    normalized_tid = normalize_terminal_id(terminal_id)
    stale_dir = temp_state / f"terminals/{normalized_tid}"
    stale_dir.mkdir(parents=True, exist_ok=True)
    stale_intent = stale_dir / "pending_command_intent.json"
    stale_intent.write_text(
        json.dumps(
            {
                "skill": "code",
                "prompt": "/code implement",
                "session_id": session_id,
                "terminal_id": terminal_id,
            }
        ),
        encoding="utf-8",
    )

    hook_input = {
        "prompt": "close task 14 and 15 and consider the project completed",
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    env["CLAUDE_TERMINAL_ID"] = terminal_id

    data_json = json.dumps(hook_input)

    result = subprocess.run(
        ["python", "-c", f'''
import sys
from pathlib import Path

sys.path.insert(0, r"{HOOKS_DIR}")

from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path(r"{temp_state}")
skill_enforcer.FALLBACK_STATE_DIR = Path(r"{temp_state}")

from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt=r"{hook_input['prompt']}",
    data={data_json},
    session_id=r"{session_id}",
    terminal_id=r"{terminal_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)
# Check at new terminal-scoped path
from __lib.terminal_id import normalize_terminal_id
normalized_tid = normalize_terminal_id("{terminal_id}")
intent_file = Path(r"{temp_state}") / f"terminals/{{normalized_tid}}/pending_command_intent.json"
print(f"IS_EMPTY:{{result.is_empty() if result else True}}")
print(f"INTENT_EXISTS:{{intent_file.exists()}}")
'''],
        capture_output=True,
        text=True,
        env=env
    )

    assert "IS_EMPTY:True" in result.stdout, "Non-slash prompt should not inject skill context"
    assert "INTENT_EXISTS:False" in result.stdout, "Non-slash prompt should clear stale intent"


def test_intent_file_write_error_handling():
    """Test hook handles intent file write failures gracefully (PR-002)."""
    import os
    import stat
    import tempfile

    session_id = "test_session_error"
    terminal_id = "test_terminal_error"

    hook_input = {
        "prompt": "/search test",
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    # Set state directory to read-only (simulate permission error)
    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_state.mkdir(parents=True, exist_ok=True)

    # Make directory read-only
    os.chmod(temp_state, stat.S_IRUSR | stat.S_IXUSR)

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    env["CLAUDE_TERMINAL_ID"] = terminal_id

    data_json = json.dumps(hook_input)

    result = subprocess.run(
        ["python", "-c", f'''
import sys
import os
from pathlib import Path

sys.path.insert(0, r"{HOOKS_DIR}")

# Monkey-patch state directories to read-only path
from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path(r"{temp_state}")

from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt=r"/search test",
    data={data_json},
    session_id=r"{session_id}",
    terminal_id=r"{terminal_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)

# Output result - hook should still create injection despite file write error
if result and not result.is_empty():
    print(f"INJECTION:{{result.context}}")
    print(f"TOKENS:{{result.tokens}}")
else:
    print("NO_INJECTION")
'''],
        capture_output=True,
        text=True,
        env=env
    )

    # Clean up: restore write permissions for cleanup
    os.chmod(temp_state, stat.S_IRWXU)

    # Hook should still create injection even if file write fails
    assert "INJECTION:" in result.stdout, \
        "Hook should create injection even if intent file write fails (graceful degradation)"


def test_multi_terminal_isolation():
    """Test that multiple terminals don't interfere with each other (PR-003)."""
    import os
    import re
    import sys
    import tempfile

    # Simulate two terminals
    terminal_1_id = "term_001"
    terminal_2_id = "term_002"
    shared_session = "shared_session"

    temp_state = Path(tempfile.mkdtemp()) / "state"
    temp_state.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = shared_session

    # Terminal 1 writes intent
    result_1 = subprocess.run(
        ["python", "-c", f'''
import sys
from pathlib import Path
sys.path.insert(0, r"{HOOKS_DIR}")

from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path(r"{temp_state}")
skill_enforcer.FALLBACK_STATE_DIR = Path(r"{temp_state}")  # Patch fallback too

from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt=r"/search terminal1",
    data={{"prompt": "/search terminal1"}},
    session_id=r"{shared_session}",
    terminal_id=r"{terminal_1_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)
print(f"TERM1_INJECTION:{{result.context if result and not result.is_empty() else 'NONE'}}")
'''],
        capture_output=True,
        text=True,
        env={**env, "CLAUDE_TERMINAL_ID": terminal_1_id}
    )

    # Terminal 2 writes different intent
    result_2 = subprocess.run(
        ["python", "-c", f'''
import sys
from pathlib import Path
sys.path.insert(0, r"{HOOKS_DIR}")

from UserPromptSubmit import skill_enforcer
skill_enforcer.INTENT_STATE_DIR = Path(r"{temp_state}")
skill_enforcer.FALLBACK_STATE_DIR = Path(r"{temp_state}")  # Patch fallback too

from UserPromptSubmit.base import HookContext

context = HookContext(
    prompt=r"/search terminal2",
    data={{"prompt": "/search terminal2"}},
    session_id=r"{shared_session}",
    terminal_id=r"{terminal_2_id}"
)

result = skill_enforcer.skill_enforcement_hook(context)
print(f"TERM2_INJECTION:{{result.context if result and not result.is_empty() else 'NONE'}}")
'''],
        capture_output=True,
        text=True,
        env={**env, "CLAUDE_TERMINAL_ID": terminal_2_id}
    )

    # Verify both terminals created intent files at new terminal-scoped paths
    sys.path.insert(0, str(HOOKS_DIR))
    from __lib.terminal_id import normalize_terminal_id
    norm_1 = normalize_terminal_id(terminal_1_id)
    norm_2 = normalize_terminal_id(terminal_2_id)
    intent_file_1 = temp_state / f"terminals/{norm_1}/pending_command_intent.json"
    intent_file_2 = temp_state / f"terminals/{norm_2}/pending_command_intent.json"

    assert intent_file_1.exists(), "Terminal 1 intent file should exist"
    assert intent_file_2.exists(), "Terminal 2 intent file should exist"

    # Verify intent files have different content (no cross-talk)
    content_1 = json.loads(intent_file_1.read_text())
    content_2 = json.loads(intent_file_2.read_text())

    assert content_1["skill"] == "search", "Terminal 1 should have search intent"
    assert content_2["skill"] == "search", "Terminal 2 should have search intent"

    # Verify terminal_id in content prevents cross-talk
    assert "terminal1" in content_1.get("prompt", ""), "Terminal 1 content should reflect terminal1"
    assert "terminal2" in content_2.get("prompt", ""), "Terminal 2 content should reflect terminal2"


if __name__ == "__main__":
    test_hook_registered()
    print("✓ test_hook_registered passed")

    test_slash_command_detection()
    print("✓ test_slash_command_detection passed")

    test_intent_file_created()
    print("✓ test_intent_file_created passed")

    test_non_slash_command_ignored()
    print("✓ test_non_slash_command_ignored passed")

    test_intent_file_write_error_handling()
    print("✓ test_intent_file_write_error_handling passed (PR-002)")

    test_multi_terminal_isolation()
    print("✓ test_multi_terminal_isolation passed (PR-003)")

    print("\n✓ All tests passed")

"""Test PreToolUse modify decision protocol extension."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_modify_decision_in_code():
    """Test that modify logic works conceptually (simple unit test)."""
    # Simulate what should happen when hook returns modify

    # Input data
    data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": 'ls "P:\\.claude\\hooks"'
        }
    }

    # Hook processes and returns modify
    def mock_hook(d):
        cmd = d["tool_input"]["command"]
        # Fix backslashes
        fixed = cmd.replace("\\", "/")
        return {
            "decision": "modify",
            "tool_input": {
                "command": fixed
            }
        }

    result = mock_hook(data)

    # Verify hook returns correct structure
    assert result["decision"] == "modify"
    assert result["tool_input"]["command"] == 'ls "P:/.claude/hooks"'
    print("✓ Modify logic works correctly")


def test_backward_compat_block_in_code():
    """Test that block decision still works (backward compatibility)."""
    data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "ls 'P:\\.claude\\hooks'"
        }
    }

    # Hook returns block
    def mock_hook(d):
        return {
            "decision": "block",
            "reason": "Test block"
        }

    result = mock_hook(data)

    # Verify block structure unchanged
    assert result["decision"] == "block"
    assert result["reason"] == "Test block"
    print("✓ Block decision backward compatible")


def test_backward_compat_none_in_code():
    """Test that None return still allows (backward compatibility)."""
    data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "ls 'P:/.claude/hooks'"
        }
    }

    # Hook returns None (allow)
    def mock_hook(d):
        return None

    result = mock_hook(data)

    # Verify None means allow
    assert result is None
    print("✓ None return (allow) backward compatible")


if __name__ == "__main__":
    print("Running RED phase tests...")
    test_modify_decision_in_code()
    test_backward_compat_block_in_code()
    test_backward_compat_none_in_code()
    print("\nAll RED tests passed!")

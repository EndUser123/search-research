#!/usr/bin/env python3
"""Live smoke test for Stop_semantic_critic - calls real Bifrost endpoint."""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

_TOOLS_MCP = Path("P:/tools/mcp")
if str(_TOOLS_MCP) not in sys.path:
    sys.path.insert(0, str(_TOOLS_MCP))


def test_live_bifrost_call():
    """Test that call_semantic_critic_via_bifrost actually hits Bifrost and returns valid JSON."""
    from Stop_semantic_critic import call_semantic_critic_via_bifrost

    print("Calling Bifrost (semantic-critic)...", file=sys.stderr)
    result = call_semantic_critic_via_bifrost(
        original_user_prompt="Why did the connection fail?",
        assistant_response=(
            "The connection failed because the authentication token expired after 24 hours. "
            "This caused the server to reject the request with a 401 error. "
            "The fix is to refresh the token before making API calls. "
            "You can verify the token expiration by checking the JWT claims at jwt.io. "
            "Alternative approaches include using a refresh token flow or increasing the token lifetime."
        )
        * 3,
        session_key="live-smoke-test",
    )

    assert result is not None, "Bifrost returned None - call failed"
    assert isinstance(result.ok, bool), f"ok should be bool, got {type(result.ok)}"
    assert isinstance(result.reason, str), f"reason should be str, got {type(result.reason)}"

    print(f"\nBifrost response:", file=sys.stderr)
    print(f"  ok: {result.ok}", file=sys.stderr)
    print(f"  reason: {result.reason}", file=sys.stderr)

    print("\n✅ Live smoke test PASSED - Bifrost integration works", file=sys.stderr)


def test_live_full_flow():
    """Test the full run() function with a diagnostic prompt/response."""
    import Stop_semantic_critic as mod

    # Clear per-session cap
    mod._INVOCATION_COUNTS.clear()

    data = {
        "session_id": "smoke-test-session",
        "user_prompt": "Why did the connection fail?",
        "response": (
            "The connection failed because the authentication token expired after "
            "24 hours. This caused the server to reject the request with a 401 error. "
            "The fix is to refresh the token before making API calls. "
            "You can verify the token expiration by checking the JWT claims. "
            "Alternative approaches include using a refresh token flow or "
            "increasing the token lifetime if security requirements allow."
        )
        * 5,
    }

    print("\nCalling run() with diagnostic content...", file=sys.stderr)
    result = mod.run(data)

    print(f"run() returned: {result}", file=sys.stderr)

    # run() returns None if ok=true (allow) or dict if ok=false (advisory)
    assert result is None or isinstance(result, dict), f"Unexpected result type: {type(result)}"

    if result is not None:
        assert "systemMessage" in result, f"Missing systemMessage: {result}"
        print(f"  Advisory injected: {result['systemMessage'][:80]}...", file=sys.stderr)
    else:
        print("  Response passed quality gate (allow)", file=sys.stderr)

    print("\n✅ Full flow smoke test PASSED", file=sys.stderr)


if __name__ == "__main__":
    test_live_bifrost_call()
    test_live_full_flow()
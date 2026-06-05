#!/usr/bin/env python3
"""Live smoke test for Stop_semantic_critic - calls real Bifrost endpoint."""

import sys
from pathlib import Path

import pytest

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


def test_second_backend_config_coherent():
    """Invariant: the second OR-veto backend (GLM, formerly M3) is wired to the
    Anthropic-protocol endpoint -- NOT z.ai's OpenAI coding endpoint -- with a key
    env name set and a model set. Catches the silent fail-open class (wrong endpoint
    / missing key) with no network call. Regression guard for the 2026-06-05 M3->GLM
    swap; mirrors the veridical-gate TestProductionWiring lesson (a fail-open gate can
    die silently when nothing asserts its wiring)."""
    import Stop_semantic_critic as mod

    assert "/anthropic" in mod.SEMANTIC_CRITIC_URL, mod.SEMANTIC_CRITIC_URL
    assert "/coding/paas" not in mod.SEMANTIC_CRITIC_URL, (
        "second backend must use z.ai Anthropic endpoint, not the OpenAI coding endpoint"
    )
    assert mod.SEMANTIC_CRITIC_MODEL.strip(), "second-backend model must be set"
    assert mod.SEMANTIC_CRITIC_KEY_ENV.strip(), "second-backend key env name must be set"


def test_second_backend_live_verdict():
    """Real smoke: the SECOND backend ALONE must return a parseable verdict.

    The combined live test (test_live_bifrost_call) stays green even if the second
    backend silently fail-opens, as long as Mistral works -- so it cannot detect the
    second backend dying. This isolates it. Skips when no key is configured (offline/CI).
    """
    import Stop_semantic_critic as mod

    if not mod._load_second_critic_key():
        pytest.skip("no second-backend key configured (Z_AI_API_KEY)")

    up = "Why does the API return 502 intermittently under load?"
    ar = "It is probably a temporary network blip, it should resolve itself."
    profile = mod._detect_critic_profile(up, ar)
    result = mod._call_minimax_critic(
        mod.CRITIC_PROMPTS[profile],
        mod._build_critic_user_message(up, ar),
        "live-second-backend-test",
        profile,
    )
    assert result is not None, (
        "second backend returned None -- wiring dead / fail-open (endpoint, key, or model)"
    )
    assert isinstance(result.ok, bool)


if __name__ == "__main__":
    test_live_bifrost_call()
    test_live_full_flow()
    test_second_backend_config_coherent()
    test_second_backend_live_verdict()
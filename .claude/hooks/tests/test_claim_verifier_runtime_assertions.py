from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop_router  # type: ignore
import unified_claim_verifier as ucv


def test_unified_claim_verifier_is_live_in_stop_router() -> None:
    hook_names = [hook_name for hook_name, *_ in Stop_router.HOOK_SEQUENCE]
    assert "unified_claim_verifier.py" in hook_names
    assert "unified_claim_verifier.py" in Stop_router.ACTIVE_RUNTIME_HOOKS


def test_unified_claim_verifier_is_enabled_in_settings() -> None:
    settings_path = HOOKS_DIR.parent / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    env = settings.get("env", {})
    assert env.get("UNIFIED_CLAIM_VERIFIER_ENABLED") == "true"


def test_stop_router_forwards_response_text_to_unified_claim_verifier(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        Stop_router,
        "_materialize_snapshot",
        lambda data: {
            "terminal_id": "term-1",
            "turn_id": "turn-1",
            "session_id": "session-1",
            "user_prompt": "Check whether P:/exists.py is present.",
            "assistant_response": "The file P:/exists.py exists.",
            "transcript_path": "",
            "tools_used": ["Read"],
            "tool_events": [
                {
                    "name": "Read",
                    "command": "P:/exists.py",
                    "output": "content of exists.py",
                    "cwd": "P:/repo",
                }
            ],
            "observations": [],
            "skill_state": {},
            "assistant_message_kind": "assistant",
            "governance": {},
            "status": "open",
            "outcome": {},
            "transcript_entries": [],
        },
    )
    monkeypatch.setattr(Stop_router, "_run_phase0_depends_on_skills_gate", lambda data: None)
    monkeypatch.setattr(Stop_router, "_supports_inprocess", lambda hook_name: True)
    monkeypatch.setattr(Stop_router, "_is_enabled", lambda env_var, default_enabled: True)
    monkeypatch.setattr(
        Stop_router,
        "ACTIVE_RUNTIME_HOOKS",
        frozenset({"unified_claim_verifier.py"}),
    )
    monkeypatch.setattr(
        Stop_router,
        "HOOK_SEQUENCE",
        [("unified_claim_verifier.py", "UNIFIED_CLAIM_VERIFIER_ENABLED", True, "inprocess")],
    )
    monkeypatch.setattr(
        Stop_router,
        "run_hook_inprocess",
        lambda hook_name, hook_data, timeout_seconds=5.0: captured.setdefault(
            "hook_data", dict(hook_data)
        )
        or {"decision": "allow", "reason": "CLAIMS_VERIFIED"},
    )
    monkeypatch.setattr(Stop_router, "_append_validator_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(Stop_router, "close_turn", lambda *args, **kwargs: None)

    Stop_router.route_stop({"hook_event_name": "Stop"})

    hook_data = captured["hook_data"]
    assert isinstance(hook_data, dict)
    assert hook_data["response"] == "The file P:/exists.py exists."
    assert hook_data["assistant_response"] == "The file P:/exists.py exists."
    assert hook_data["prompt"] == "Check whether P:/exists.py is present."


def test_unified_claim_verifier_warns_on_missing_response() -> None:
    result = ucv.run({"prompt": "Check P:/exists.py"})

    assert result["decision"] == "warn"
    assert result["reason"] == "MISSING_RESPONSE"


def test_user_prompt_mentions_do_not_disable_supported_claims() -> None:
    result = ucv.run(
        {
            "response": "The file P:/exists.py exists.",
            "prompt": "Please review P:/exists.py locally.",
            "session_id": "88888888-8888-8888-8888-888888888888",
            "terminal_id": "term-run",
            "tool_events": [
                {
                    "name": "Read",
                    "command": "P:/exists.py",
                    "output": "content of exists.py",
                    "cwd": "P:/repo",
                }
            ],
            "tools_used": ["Read"],
        }
    )

    assert result["decision"] == "allow"
    assert result["reason"] == "CLAIMS_VERIFIED"


def test_truth_validator_removed_from_posttooluse_registry() -> None:
    from posttooluse import create_registry

    registry = create_registry()
    hook_names = [name for name, _hook in getattr(registry, "_hooks", [])]
    assert "truth_validator" not in hook_names

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from __lib import unified_evidence_enforcer as ueea


def _long_claim_response() -> str:
    base = "Analysis references P:/__csf/src/daemons/unified_semantic_daemon.py and confirms behavior. "
    return base + ("x" * 240)


def test_dict_tool_entries_count_as_observation(monkeypatch):
    monkeypatch.setattr(ueea, "_record_observation", lambda *args, **kwargs: None)
    result = ueea.check_response(
        {
            "response": _long_claim_response(),
            "tools_used": [{"name": "Read"}],
            "terminal_id": "t-dict-obs",
        }
    )
    assert result["allowed"] is True


def test_structured_evidence_fields_bypass_observation_reblock(monkeypatch):
    monkeypatch.setattr(ueea, "_record_observation", lambda *args, **kwargs: None)
    response = (
        "observed_via: Read\n"
        "observed_at: 2026-02-09T15:52:00Z\n"
        "evidence_type: code\n\n"
        "The likely root cause is under investigation."
    )
    result = ueea.check_response(
        {
            "response": response,
            "tools_used": [],
            "terminal_id": "t-structured-bypass",
        }
    )
    assert result["allowed"] is True


def test_observation_is_recorded_even_when_response_blocks(monkeypatch):
    called = {"count": 0}

    def _capture(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setattr(ueea, "_record_observation", _capture)

    result = ueea.check_response(
        {
            "response": "assuming that the hook works without source evidence",
            "tools_used": [{"name": "Read"}],
            "terminal_id": "t-block-record",
        }
    )
    assert result["allowed"] is False
    assert called["count"] == 1


def test_speculation_allowed_when_labeled_unverified(monkeypatch):
    monkeypatch.setattr(ueea, "_record_observation", lambda *args, **kwargs: None)
    response = "This is likely [UNVERIFIED] until source-level tracing is completed."
    result = ueea.check_response(
        {
            "response": response,
            "tools_used": [],
            "terminal_id": "t-unverified-label",
        }
    )
    assert result["allowed"] is True


def test_speculation_allowed_with_required_to_verify_plan(monkeypatch):
    monkeypatch.setattr(ueea, "_record_observation", lambda *args, **kwargs: None)
    response = (
        "The likely cause is in hook routing.\n"
        "Required to verify: Read Stop_router.py and trace dispatch branch."
    )
    result = ueea.check_response(
        {
            "response": response,
            "tools_used": [],
            "terminal_id": "t-verify-plan",
        }
    )
    assert result["allowed"] is True

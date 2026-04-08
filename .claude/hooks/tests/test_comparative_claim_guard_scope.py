from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import Stop_comparative_claim_guard as guard


def test_fresh_session_scope_uses_historical_reads_even_when_current_turn_has_other_tools(
    monkeypatch,
) -> None:
    monkeypatch.setenv("COMPARATIVE_CLAIM_GUARD_SCOPE", "fresh_session")

    def fake_loader(
        session_id: str,
        terminal_id: str,
        scope: str,
        limit: int = 500,
        ttl_seconds: int | None = None,
        current_turn_events: list[dict] | None = None,
    ) -> list[dict]:
        return [
            {
                "id": 10,
                "name": "Read",
                "command": "P:/.claude/skills/p/SKILL.md",
            },
            {
                "id": 11,
                "name": "Read",
                "command": "P:/.claude/skills/sqa/SKILL.md",
            },
            *(current_turn_events or []),
        ]

    monkeypatch.setattr(
        guard,
        "load_scoped_tool_events",
        fake_loader,
    )

    result = guard.check(
        {
            "assistant_response": "/p vs /sqa",
            "tool_events": [{"id": 1, "name": "Bash", "command": "pytest"}],
            "session_id": "194b664d-0fc4-4032-a05b-ad4b56d9c955",
            "terminal_id": "term-1",
        }
    )

    assert result is None


def test_turn_scope_blocks_when_only_historical_reads_exist(monkeypatch) -> None:
    monkeypatch.setenv("COMPARATIVE_CLAIM_GUARD_SCOPE", "turn")

    def fake_loader(
        session_id: str,
        terminal_id: str,
        scope: str,
        limit: int = 500,
        ttl_seconds: int | None = None,
        current_turn_events: list[dict] | None = None,
    ) -> list[dict]:
        if scope == guard.SCOPE_TURN_STRICT:
            return current_turn_events or []
        return [
            {
                "id": 10,
                "name": "Read",
                "command": "P:/.claude/skills/p/SKILL.md",
            },
            {
                "id": 11,
                "name": "Read",
                "command": "P:/.claude/skills/sqa/SKILL.md",
            },
        ]

    monkeypatch.setattr(
        guard,
        "load_scoped_tool_events",
        fake_loader,
    )

    result = guard.check(
        {
            "assistant_response": "/p vs /sqa",
            "tool_events": [{"id": 1, "name": "Bash", "command": "pytest"}],
            "session_id": "194b664d-0fc4-4032-a05b-ad4b56d9c955",
            "terminal_id": "term-1",
        }
    )

    assert result is not None
    assert "verified in scope `turn_strict`" in result["reason"]


def test_skill_frontmatter_aliases_are_added_to_verified_set() -> None:
    verified = guard._build_verified_set(
        [{"name": "Read", "command": "P:/.claude/skills/p/SKILL.md"}]
    )

    assert "p" in verified
    assert "/p" in verified
